import os
import csv
import psycopg2


def main():
    """import books.csv to Heroku"""

    # connect to database
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))

    if not conn:
        print(f"Could not connect to database")
        return

    # get cursor
    cur = conn.cursor()

    # creat table
    cur.execute("CREATE TABLE books (isbn char(10) NOT NULL UNIQUE PRIMARY KEY, title TEXT NOT NULL, author varchar(100) NOT NULL, year SMALLINT NOT NULL);")

    # creat index
    cur.execute("CREATE INDEX index_isbn ON books (isbn);")


    with open("books.csv") as file:
        # read csv file
        books = csv.reader(file)

        # add csv file to database row by row
        counter = 0

        for row in books:
            if counter != 0:
                cur.execute("INSERT INTO books (isbn, title, author, year) VALUES (%s, %s, %s, %s);", (row[0], row[1], row[2], row[3]))
                print(f"Inserted {row[0]}, {row[1]}, {row[2]}, {row[3]} into table")

            counter = counter + 1

        print(f"Total added = {counter - 1}")

    # Make the changes to the database persistent
    conn.commit()

    # close connection
    cur.close()
    conn.close()


if __name__=="__main__":
    main()
