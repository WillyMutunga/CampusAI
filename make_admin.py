import mysql.connector

def make_admin(student_id):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="loginapp"
        )
        cursor = conn.cursor()

        print(f"Promoting user '{student_id}' to admin...")
        cursor.execute("UPDATE users SET is_admin = TRUE WHERE student_id = %s", (student_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Success: User '{student_id}' is now an admin.")
        else:
            print(f"Warning: User '{student_id}' not found in 'users' table.")
        
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    # Promote our test user for verification
    make_admin("test_student_01")
