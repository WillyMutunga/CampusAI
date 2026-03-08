from app import app
from models import db, User, FeeStatement, Knowledge

def seed_data():
    with app.app_context():
        # Seed LoginApp (Free Statements)
        # Check if exists
        stmt = FeeStatement.query.filter_by(student_id="1").first()
        if not stmt:
            new_stmt = FeeStatement(student_id="1", balance=50000.00)
            db.session.add(new_stmt)
            print("Seeded FeeStatement.")
        
        # Seed KnowledgeDB
        # Check if exists
        know = Knowledge.query.filter_by(intent_tag="greeting").first()
        if not know:
            new_know = Knowledge(intent_tag="greeting", content="Hello! I am the CampusAI Assistant running on knowledge_db.")
            db.session.add(new_know)
            print("Seeded greeting.")
            
        db.session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    seed_data()
