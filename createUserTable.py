import psycopg2
import os

def main():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    
    if not conn:
        print(f"Could not connect to database")
        return

    cur = conn.cursor()

    cur.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, username TEXT NOT NULL, password TEXT NOT NULL);")

    conn.commit()

    cur.close()
    conn.close()


if __name__=="__main__":
    main()