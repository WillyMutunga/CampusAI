import mysql.connector

def setup_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()

        # Create Database
        cursor.execute("CREATE DATABASE IF NOT EXISTS CampusAI")
        print("Database 'CampusAI' checked/created.")
        
        conn.database = "CampusAI"

        # Create Tables
        cursor.execute("DROP TABLE IF EXISTS fee_statements")
        cursor.execute("""
            CREATE TABLE fee_statements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50),
                balance DECIMAL(10, 2)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) UNIQUE,
                full_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campus_knowledge (
                id INT AUTO_INCREMENT PRIMARY KEY,
                intent_tag VARCHAR(50),
                content TEXT
            )
        """)
        print("Tables checked/created.")

        # Insert Dummy Data for Fee Statements
        cursor.execute("SELECT * FROM fee_statements WHERE student_id = 1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO fee_statements (student_id, balance) VALUES (1, 50000.00)")
            print("Inserted dummy fee record.")
        else:
            print("Dummy fee record already exists.")

        # Insert Dummy Data for Knowledge
        # Note: 'fee_inquiry' is handled by logic, but adding others can be good verification
        cursor.execute("SELECT * FROM campus_knowledge WHERE intent_tag = 'greeting'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO campus_knowledge (intent_tag, content) VALUES ('greeting', 'Hello! I am the CampusAI Assistant.')")
            print("Inserted dummy knowledge record.")

        conn.commit()
        conn.close()
        print("Database setup complete.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    setup_database()
