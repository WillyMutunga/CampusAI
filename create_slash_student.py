from app import app, db, Student, User
from werkzeug.security import generate_password_hash

def create_slash_student():
    with app.app_context():
        sid = "P01/9999/2026"
        
        # Cleanup
        s = Student.query.filter_by(student_id=sid).first()
        if s:
            db.session.delete(s)
        u = User.query.filter_by(student_id=sid).first()
        if u:
            db.session.delete(u)
        db.session.commit()
            
        # Create
        student = Student(
            student_id=sid,
            full_name="Slash Test Student",
            email="slash@test.com",
            password_hash=generate_password_hash("password")
        )
        db.session.add(student)
        db.session.commit()
        print(f"Created student {sid}")

if __name__ == "__main__":
    create_slash_student()
