print("Starting app.py...", flush=True)
try:
    from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
    from flask_login import LoginManager, login_user, login_required, logout_user, current_user
    from werkzeug.security import generate_password_hash, check_password_hash
    import json
    import subprocess
    import chatbot_engine
    print("Imported Flask & Flask-Login", flush=True)
    from models import db, User, FeeStatement, Student, Knowledge, UserQuery, NavigationItem, NewsItem # Import ORM models
    from chatbot_engine import predict_class, get_response # Logic
    from portal_handler import fetch_portal_data
    print("Imported chatbot_engine", flush=True)
except Exception as e:
    print(f"Import Error in app.py: {e}", flush=True)
    import sys
    sys.exit(1)

app = Flask(__name__)
app.secret_key = "secret_key_change_this_in_production"

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/loginapp'
app.config['SQLALCHEMY_BINDS'] = {
    'knowledge_db': 'mysql+mysqlconnector://root:@localhost/knowledge_db',
    'campusai': 'mysql+mysqlconnector://root:@localhost/CampusAI'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False # Update to True in production with HTTPS
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['UPLOAD_FOLDER_NEWS'] = 'static/uploads/news'
import os
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_NEWS'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    try:
        db.create_all() # Ensure tables exist in loginapp and knowledge_db
    except Exception as e:
        print(f"DB Setup Warning: {e}")
        
    try:
        import chatbot_engine
        chatbot_engine.init_qa_cache()
    except Exception as e:
        print(f"Cache Setup Warning: {e}")


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Check if user already exists
        existing_student = Student.query.filter_by(student_id=student_id).first()
        if existing_student:
             return render_template("register.html", error="Student ID already registered.")
        
        hashed_password = generate_password_hash(password)
        
        new_student = Student(
            student_id=student_id,
            full_name=full_name,
            email=email,
            password_hash=hashed_password
        )
        
        try:
            db.session.add(new_student)
            db.session.commit()
            # Auto-Login Logic: Sync to User table immediately
            new_user = User(student_id=student_id, full_name=full_name)
            db.session.add(new_user)
            db.session.commit()
            
            print(f"Registration: New student registered and synced to User: {student_id}")
            login_user(new_user)
            return redirect(url_for('chat')) # Redirect directly to chat
        except Exception as e:
            db.session.rollback()
            print(f"Registration Error: {e}")
            return render_template("register.html", error="An error occurred during registration.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        password = request.form.get("password")
        
        # 1. Check Local Registration (Student Table)
        student = Student.query.filter_by(student_id=student_id).first()
        if student and check_password_hash(student.password_hash, password):
            # Local Auth Successful
            print(f"Login: Local auth for {student_id}")
            
            # Sync to User table (for Flask-Login)
            user = User.query.filter_by(student_id=student_id).first()
            if not user:
                user = User(student_id=student_id, full_name=student.full_name)
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            return redirect(url_for('chat')) # Redirect directly to chat

        # 2. Fallback: Fetch Data from Portal (Auth + Scrape)
        print(f"Login: Attempting Portal match for {student_id}")
        success, result = fetch_portal_data(student_id, password)
        
        if success:
            data = result
            # session['student_id'] = data['student_id'] # Managed by Flask-Login
            # session['full_name'] = data['full_name']
            
            # 2. Data Sync: Update/Insert into Local DB via ORM
            user = User.query.filter_by(student_id=data['student_id']).first()
            
            if not user:
                new_user = User(student_id=data['student_id'], full_name=data['full_name'])
                db.session.add(new_user)
                print(f"Sync: New user registered: {data['student_id']}")
            else:
                user.full_name = data['full_name']
                # db.session.add(user) # Not strictly needed if object is attached, but good for clarity
            
            # Sync Fees Table
            # Remove old fee record or update
            fee_stmt = FeeStatement.query.filter_by(student_id=data['student_id']).first()
            if fee_stmt:
                fee_stmt.balance = data['fee_balance']
            else:
                new_fee = FeeStatement(student_id=data['student_id'], balance=data['fee_balance'])
                db.session.add(new_fee)
            
            print(f"Sync: Fee record processed for {data['student_id']}")
            
            db.session.commit()
            
            login_user(user)
            return redirect(url_for('chat')) # Redirect to chat
        else:
            # result contains the error message
            return render_template("login.html", error=result)
            
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    # Proactive Alert Logic
    fee = FeeStatement.query.filter_by(student_id=current_user.student_id).first()
    balance = float(fee.balance) if fee else 0.0
    return render_template("dashboard.html", name=current_user.full_name, fee_balance=balance)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        password = request.form.get("password")
        
        # Check Local Student Table
        student = Student.query.filter_by(student_id=student_id).first()
        if student and check_password_hash(student.password_hash, password):
            # Verify Admin Status in User Table
            user = User.query.filter_by(student_id=student_id).first()
            if user and user.is_admin:
                login_user(user)
                return redirect(url_for('admin_dashboard'))
            else:
                 return render_template("admin_login.html", error="Access Denied: You do not have admin privileges.")
        else:
             return render_template("admin_login.html", error="Invalid credentials.")

    return render_template("admin_login.html")

@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    total_students = Student.query.count()
    total_admins = User.query.filter_by(is_admin=True).count()
    # Estimate intents from knowledge table + hardcoded ones
    total_intents = Knowledge.query.count() + 3 # +3 for greeting, goodbye, fees
    unreviewed_queries = UserQuery.query.filter_by(is_reviewed=False).count()
    
    return render_template("admin_dashboard.html", 
                           name=current_user.full_name,
                           total_students=total_students,
                           total_admins=total_admins,
                           total_intents=total_intents,
                           unreviewed_queries=unreviewed_queries)

@app.route("/admin/students")
@login_required
@admin_required
def admin_students():
    # Join Student and User tables to get admin status
    # This is a bit complex because we have two tables. 
    # Let's iterate over Students and check User table for admin status.
    all_students = Student.query.all()
    student_data = []
    
    for s in all_students:
        user = User.query.filter_by(student_id=s.student_id).first()
        is_admin = user.is_admin if user else False
        student_data.append({
            'student_id': s.student_id,
            'full_name': s.full_name,
            'email': s.email,
            'is_admin': is_admin
        })
    
    return render_template("admin_students.html", students=student_data)

@app.route("/admin/promote/<path:student_id>")
@login_required
@admin_required
def promote_user(student_id):
    print(f"Promoting user: {student_id}", flush=True)
    user = User.query.filter_by(student_id=student_id).first()
    if user:
        user.is_admin = True
        db.session.commit()
        flash(f"User {student_id} promoted to Admin successfully!", "success")
    else:
        # If user exists in Student but not sync'd to User yet, we should create them?
        # For simplicity, assume they are sync'd on login. If not found, we can't promote easily without sync.
        # Let's try to find student and create user record if missing.
        student = Student.query.filter_by(student_id=student_id).first()
        if student:
            new_user = User(student_id=student_id, full_name=student.full_name, is_admin=True)
            db.session.add(new_user)
            db.session.commit()
            flash(f"User {student_id} created and promoted to Admin!", "success")
        else:
            flash(f"User {student_id} not found.", "error")
            
    return redirect(url_for('admin_students'))

@app.route("/admin/demote/<path:student_id>")
@login_required
@admin_required
def demote_user(student_id):
    if student_id == current_user.student_id:
        flash("You cannot demote yourself!", "error")
        return redirect(url_for('admin_students'))
        
    user = User.query.filter_by(student_id=student_id).first()
    if user:
        user.is_admin = False
        db.session.commit()
        flash(f"User {student_id} demoted to Student successfully!", "success")
    else:
        flash(f"User {student_id} not found.", "error")
            
    return redirect(url_for('admin_students'))

@app.route("/admin/knowledge", methods=["GET", "POST"])
@login_required
@admin_required
def admin_knowledge():
    if request.method == "POST":
        tag = request.form.get("tag")
        patterns_text = request.form.get("patterns")
        content = request.form.get("content")
        
        if tag and patterns_text and content:
            # 1. Update Database (Content)
            # Check if exists to update, or create new
            k_item = Knowledge.query.filter_by(intent_tag=tag).first()
            if not k_item:
                k_item = Knowledge(intent_tag=tag, content=content)
                db.session.add(k_item)
            else:
                k_item.content = content
            db.session.commit()
            
            # 2. Update Intents JSON (Training Data)
            patterns_list = [p.strip() for p in patterns_text.split('\n') if p.strip()]
            
            try:
                with open('intents.json', 'r') as f:
                    intents_data = json.load(f)
                
                # Check if intent exists
                intent_found = False
                for intent in intents_data['intents']:
                    if intent['tag'] == tag:
                        # Append new patterns, avoid duplicates
                        current_patterns = set(intent['patterns'])
                        current_patterns.update(patterns_list)
                        intent['patterns'] = list(current_patterns)
                        intent_found = True
                        break
                
                if not intent_found:
                    # Create new intent block
                    intents_data['intents'].append({
                        "tag": tag,
                        "patterns": patterns_list,
                        "responses": [] # We use DB for responses, but JSON structure is good to have.
                    })
                
                with open('intents.json', 'w') as f:
                    json.dump(intents_data, f, indent=2)
                    
            except Exception as e:
                flash(f"Error updating intents file: {e}", "error")
                return redirect(url_for('admin_knowledge'))

            # 3. Retrain Model
            try:
                # Run preprocessing first to update data.pickle with new words/classes
                print("Triggering data preprocessing...", flush=True)
                subprocess.run(["python", "preprocess_data.py"], check=True)
                
                # Run training script
                print("Triggering model training...", flush=True)
                subprocess.run(["python", "train_model.py"], check=True)
                
                # 4. Reload Model in Engine
                chatbot_engine.load_chatbot_model()
                
                flash(f"Topic '{tag}' saved and model retrained successfully!", "success")
            except Exception as e:
                flash(f"Saved to DB but Training Failed: {e}", "error")
                
        else:
            flash("All fields are required.", "error")
            
        return redirect(url_for('admin_knowledge'))

    # GET: List existing items
    knowledge_items = Knowledge.query.all()
    # Support pre-filling from queries
    prefill = {
        'tag': request.args.get('tag', ''),
        'patterns': request.args.get('patterns', ''),
        'content': request.args.get('content', '')
    }
    
    # If it's an "edit" request from the list, try to fetch patterns from JSON
    if request.args.get('edit') and prefill['tag']:
        try:
            with open('intents.json', 'r') as f:
                intents_data = json.load(f)
            for intent in intents_data['intents']:
                if intent['tag'] == prefill['tag']:
                    prefill['patterns'] = "\n".join(intent['patterns'])
                    break
        except:
            pass

    return render_template("admin_knowledge.html", 
                           knowledge_items=knowledge_items,
                           prefill=prefill)

@app.route("/admin/knowledge/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_knowledge(id):
    k_item = Knowledge.query.get_or_404(id)
    tag = k_item.intent_tag
    
    # 1. Delete from Database
    db.session.delete(k_item)
    db.session.commit()
    
    # 2. Delete from intents.json
    try:
        with open('intents.json', 'r') as f:
            intents_data = json.load(f)
        
        intents_data['intents'] = [i for i in intents_data['intents'] if i['tag'] != tag]
        
        with open('intents.json', 'w') as f:
            json.dump(intents_data, f, indent=2)
            
        flash(f"Topic '{tag}' deleted successfully.", "success")
    except Exception as e:
        flash(f"Error updating intents file: {e}", "error")
        
    return redirect(url_for('admin_knowledge'))

@app.route("/admin/queries")
@login_required
@admin_required
def admin_queries():
    # Show last 50 queries
    queries = UserQuery.query.order_by(UserQuery.created_at.desc()).limit(50).all()
    return render_template("admin_queries.html", queries=queries)

@app.route("/admin/upload", methods=["GET", "POST"])
@login_required
@admin_required
def upload_fee_structure():
    if request.method == "POST":
        if 'file' not in request.files:
            return render_template("admin_upload.html", error="No file part")
        file = request.files['file']
        if file.filename == '':
            return render_template("admin_upload.html", error="No selected file")
        if file and file.filename.endswith('.pdf'):
            filename = "fee_structure.pdf"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Just showing a simple success message for now, could be integrated into dashboard
            flash("Fee structure uploaded successfully!")
            return redirect(url_for('admin_dashboard'))
        else:
             return render_template("admin_upload.html", error="Invalid file type. Please upload a PDF.")
    return render_template("admin_upload.html")

@app.route("/admin/dynamic_content", methods=["GET", "POST"])
@login_required
@admin_required
def admin_dynamic_content():
    if request.method == "POST":
        action_type = request.form.get("action_type")
        
        if action_type == "add_nav":
            title = request.form.get("nav_title")
            url = request.form.get("nav_url")
            icon = request.form.get("nav_icon")
            order = request.form.get("nav_order", 0)
            if title and url and icon:
                new_nav = NavigationItem(title=title, url=url, icon=icon, order=int(order))
                db.session.add(new_nav)
                db.session.commit()
                flash("Navigation link added successfully!", "success")
            else:
                flash("Please fill all navigation fields.", "error")
                
        elif action_type == "add_news":
            title = request.form.get("news_title")
            content = request.form.get("news_content")
            date_posted = request.form.get("news_date")
            color = request.form.get("news_color", "#6366f1")
            
            image_paths = []
            if 'news_images' in request.files:
                images = request.files.getlist('news_images')
                from werkzeug.utils import secure_filename
                import time
                for img in images:
                    if img and img.filename != '':
                        filename = secure_filename(f"{int(time.time())}_{img.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER_NEWS'], filename)
                        img.save(filepath)
                        image_paths.append(filename)
            
            paths_string = ",".join(image_paths)

            if title and content and date_posted:
                new_news = NewsItem(title=title, content=content, date_posted=date_posted, color=color, image_paths=paths_string)
                db.session.add(new_news)
                db.session.commit()
                flash("News announcement added successfully!", "success")
            else:
                flash("Please fill all news fields.", "error")
                
        return redirect(url_for('admin_dynamic_content'))

    # GET requests fetch data for the templates
    nav_links = NavigationItem.query.order_by(NavigationItem.order).all()
    news_items = NewsItem.query.order_by(NewsItem.created_at.desc()).all()
    
    return render_template("admin_dynamic_content.html", nav_links=nav_links, news_items=news_items)

@app.route("/admin/dynamic_content/delete_nav/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_nav(id):
    item = NavigationItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Navigation link deleted successfully.", "success")
    return redirect(url_for('admin_dynamic_content'))

@app.route("/admin/dynamic_content/delete_news/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_news(id):
    item = NewsItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("News announcement deleted successfully.", "success")
    return redirect(url_for('admin_dynamic_content'))

@app.route("/chat")
@login_required
def chat():
    # Fetch navigation links and news items from database
    nav_links = NavigationItem.query.order_by(NavigationItem.order).all()
    news_items = NewsItem.query.order_by(NewsItem.created_at.desc()).all()
    return render_template("index.html", name=current_user.full_name, nav_links=nav_links, news_items=news_items)

@app.route("/get", methods=["POST"])
def chatbot_response():
    msg = request.json.get("message")
    if not msg:
        return jsonify({"response": "I didn't catch that. Could you try again?"})
    
    # Use your trained model to get the intent
    ints, ratio = predict_class(msg)
    # Use your MySQL logic to get the data
    # Pass current_user.student_id if authenticated
    student_id = current_user.student_id if current_user.is_authenticated else None
    res = get_response(ints, user_query_text=msg, student_id=student_id, ratio=ratio)
    
    return jsonify({"response": res})


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    student = Student.query.filter_by(student_id=current_user.student_id).first()
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        
        if student:
            student.full_name = full_name
            student.email = email
            # Also update the User model for current_user
            current_user.full_name = full_name
            db.session.commit()
            flash("Profile updated successfully!", "success")
        else:
            flash("Student record not found.", "error")
        return redirect(url_for('profile'))
        
    return render_template("profile.html", student=student)

@app.route("/admin/profile", methods=["GET", "POST"])
@login_required
@admin_required
def admin_profile():
    admin = User.query.filter_by(student_id=current_user.student_id).first()
    if request.method == "POST":
        full_name = request.form.get("full_name")
        
        if admin:
            admin.full_name = full_name
            # Also update student table if exists
            student = Student.query.filter_by(student_id=current_user.student_id).first()
            if student:
                student.full_name = full_name
            
            db.session.commit()
            flash("Admin profile updated successfully!", "success")
        return redirect(url_for('admin_profile'))
        
    return render_template("admin_profile.html", admin=admin)

@app.route("/autocomplete")
def autocomplete():
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify([])
    
    suggestions = []
    try:
        with open('intents.json', 'r') as f:
            data = json.load(f)
        
        # Simple search in patterns
        for intent in data['intents']:
            for pattern in intent['patterns']:
                if query in pattern.lower():
                    suggestions.append(pattern)
        
        # Sort by length or relevance? Just slice for now
        return jsonify(suggestions[:5])
    except Exception as e:
        print(f"Autocomplete Error: {e}")
        return jsonify([])

if __name__ == "__main__":
    app.run(debug=True, port=5000)
