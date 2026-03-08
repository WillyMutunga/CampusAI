import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "knowledge_db"
}

def check_qa_pairs():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM qa_pairs")
        count = cursor.fetchone()[0]
        print(f"Current Row Count in qa_pairs: {count}")
        
        cursor.execute("SELECT question, source_url FROM qa_pairs LIMIT 5")
        rows = cursor.fetchall()
        print("Sample Data:")
        for row in rows:
            print(row)
            
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    check_qa_pairs()
