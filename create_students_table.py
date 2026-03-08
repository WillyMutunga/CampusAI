import mysql.connector

def create_students_table():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="CampusAI"
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) UNIQUE,
                full_name VARCHAR(100),
                email VARCHAR(100),
                password_hash VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'students' checked/created in 'CampusAI'.")
        
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    create_students_table()
