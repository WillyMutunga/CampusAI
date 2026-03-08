from app import app, db
import sys

try:
    with app.app_context():
        # Try to query the Knowledge table as a check
        from models import Knowledge
        count = Knowledge.query.count()
        print(f"DB Connection Successful! Knowledge items count: {count}")
except Exception as e:
    print(f"DB Connection Failed: {e}")
    sys.exit(1)
