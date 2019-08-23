import psycopg2
import os

def main():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    
    if not conn:
        print(f"Could not connect to database")
        return

    cur = conn.cursor()

    # reviewer, isbn, review_head, review_body, rating
    cur.execute("CREATE TABLE reviews (id SERIAL PRIMARY KEY, reviewer TEXT NOT NULL, isbn char(10) NOT NULL, review_head TEXT, review_body TEXT NOT NULL, rating FLOAT NOT NULL);")

    conn.commit()

    cur.close()
    conn.close()


if __name__=="__main__":
    main()