import mysql.connector

def create_databases():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()

        # Create loginapp database
        cursor.execute("CREATE DATABASE IF NOT EXISTS loginapp")
        print("Database 'loginapp' checked/created.")

        # Create knowledge_db database
        cursor.execute("CREATE DATABASE IF NOT EXISTS knowledge_db")
        print("Database 'knowledge_db' checked/created.")
        
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    create_databases()
