from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class FeeStatement(db.Model):
    __tablename__ = 'fee_statements'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Numeric(10, 2))

class Knowledge(db.Model):
    __bind_key__ = 'knowledge_db'
    __tablename__ = 'campus_knowledge'
    id = db.Column(db.Integer, primary_key=True)
    intent_tag = db.Column(db.String(50))
    content = db.Column(db.Text)

class Student(db.Model):
    __bind_key__ = 'campusai'
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class UserQuery(db.Model):
    __bind_key__ = 'knowledge_db'
    __tablename__ = 'user_queries'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=True) # Optional link to student
    query_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text)
    intent_tag = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    source = db.Column(db.String(20)) # 'local' or 'openai'
    is_reviewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class QAPair(db.Model):
    __bind_key__ = 'knowledge_db'
    __tablename__ = 'qa_pairs'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), unique=True)
    answer = db.Column(db.Text)
    source_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class NavigationItem(db.Model):
    __bind_key__ = 'campusai'
    __tablename__ = 'navigation_items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(50), nullable=False) # e.g. "fas fa-home"
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class NewsItem(db.Model):
    __bind_key__ = 'campusai'
    __tablename__ = 'news_items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.String(50), nullable=False) # e.g. "Today", "2 days ago", or actual date Let admin type string
    color = db.Column(db.String(20), default="#6366f1") # Default primary color for left border
    created_at = db.Column(db.DateTime, server_default=db.func.now())
