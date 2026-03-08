import mysql.connector

def reset_students_table():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="CampusAI"
        )
        cursor = conn.cursor()

        print("Dropping existing 'students' table...")
        cursor.execute("DROP TABLE IF EXISTS students")
        
        print("Creating 'students' table with correct schema...")
        cursor.execute("""
            CREATE TABLE students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(100),
                email VARCHAR(100),
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'students' recreated successfully.")
        
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    reset_students_table()
