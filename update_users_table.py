import mysql.connector

def add_is_admin_column():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="loginapp"
        )
        cursor = conn.cursor()

        print("Checking if 'is_admin' column exists...")
        cursor.execute("DESCRIBE users")
        columns = [row[0] for row in cursor.fetchall()]

        if "is_admin" not in columns:
            print("Adding 'is_admin' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
            print("Column 'is_admin' added successfully.")
        else:
            print("Column 'is_admin' already exists.")
        
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    add_is_admin_column()
