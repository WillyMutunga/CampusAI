from app import app, db
from models import UserQuery

with app.app_context():
    print("Updating database schema...")
    try:
        db.create_all()
        print("Database schema updated successfully (user_queries table created if it didn't exist).")
    except Exception as e:
        print(f"Error updating database schema: {e}")
