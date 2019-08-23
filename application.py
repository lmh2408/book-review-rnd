import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, error, get_book_data


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login and register"""
    if request.method == "POST":
        # get input
        username = str(request.form.get("username"))
        password = str(request.form.get("password"))

        # check login info
        check_query = "SELECT * FROM users WHERE username = :username;"
        check = db.execute(check_query, {"username":username})

        if check.rowcount != 1:
            return error("Incorrect username")

        if not check_password_hash(check.fetchone()["password"], password):
            return error("Incorrect password")

        # log user in
        session["id"] = username

        return redirect(url_for('index'))
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Received register request """
    if request.method == "POST":
        # get input
        username = str(request.form.get("username"))
        password = str(request.form.get("password"))
        confirm = str(request.form.get("confirm"))

        # check if password confirm is correct
        if password != confirm:
            return error("Password confirmation not match")

        # check if username already exist
        check_query = "SELECT username FROM users WHERE username = :username;"
        check = db.execute(check_query, {"username": username}).rowcount
        if check != 0:
            return error("Username already exists")

        # hash password
        hash = generate_password_hash(password)

        # add user to table users
        insert_query = "INSERT INTO users (username, password) VALUES (:username, :password);"
        insert = db.execute(insert_query, {"username":username, "password":hash}).rowcount
        db.commit()

        # log user in
        session["id"] = username

        # redirect user to search page
        return redirect(url_for('index'))

    else:
        return render_template("register.html")


@app.route("/search")
@login_required
def search():
    """ Search result page """

    # get input
    isbn = request.args.get("isbn")
    title = request.args.get("title")
    author = request.args.get("author")
    year = request.args.get("year")
    display_count = request.args.get("display_count")

    # process input
    try:
        year = int(year)
    except:
        year = 0
    try:
        display_count = int(display_count)
    except:
        display_count = 10

    i_isbn = isbn
    if isbn:
        i_isbn = i_isbn + "%"

    i_title = title
    if title:
        i_title = i_title + "%"

    i_author = author
    if author:
        i_author = i_author + "%"

    # search through table
    search_query = "SELECT * FROM books WHERE isbn LIKE :isbn OR title ILIKE :title OR author ILIKE :author OR year = :year LIMIT :limit;"
    search = db.execute(search_query, {"isbn": i_isbn, "title": i_title, "author": i_author, "year": year, "limit": display_count})

    # get result then send to template
    if search.rowcount == 0:
        return render_template("search.html", result_count = search.rowcount, def_isbn=isbn, def_title=title, def_author=author, def_year=request.args.get("year"), display_count=display_count)

    result = search.fetchall()
    return render_template("search.html", result=result, def_isbn=isbn, def_title=title, def_author=author, def_year=request.args.get("year"), display_count=display_count)


@app.route("/book/<isbn>")
@login_required
def book(isbn):
    """ Display book page """

    # get book's rating
    rating = get_book_data("bBypFUkpDHox5Z5fjzJqg", isbn)

    # get book info
    try:
        query = "SELECT * FROM books WHERE isbn = :isbn;"
        book = db.execute(query, {"isbn":isbn})
    except:
        error("Book not found", 404)

    # get review data
    q_reviews = "SELECT * FROM reviews WHERE isbn = :isbn LIMIT 10;"
    reviews = db.execute(q_reviews, {"isbn":isbn})

    # check if book have any review
    if reviews.rowcount == 0:
        return render_template("book.html", book=book.fetchone(), rating=rating, display_review=False, reviews=reviews.fetchall())

    return render_template("book.html", book=book.fetchone(), rating=rating, display_review=True, reviews=reviews.fetchall())


@app.route("/send_review/<isbn>", methods=["POST"])
@login_required
def send_review(isbn):
    """ Received and insert review into table """

    # check if user already submit review
    check_user_query = "SELECT * FROM reviews WHERE isbn = :isbn AND reviewer = :reviewer;"
    check_user = db.execute(check_user_query, {"isbn":isbn, "reviewer":session["id"]})

    if check_user.rowcount != 0:
        return error("User already submit a review")

    # get input
    review_head = request.form.get("review_head")
    review_body = request.form.get("review_body")
    review_rating = request.form.get("review_rating")

    # process input
    try:
        review_rating = float(review_rating)
    except:
        return error("Invalid rating")

    if not review_body:
        return error("Review body is empty")

    # insert review into table
    try:
        review_submit_query = "INSERT INTO reviews (reviewer, isbn, review_head, review_body, rating) VALUES (:reviewer, :isbn, :review_head, :review_body, :rating);"
        review_submit = db.execute(review_submit_query, {"reviewer":session["id"], "isbn":isbn, "review_head":review_head, "review_body":review_body, "rating":review_rating})
        db.commit()
    except:
        return error("Error when submitting review")

    return redirect(url_for("book", isbn=isbn))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/api/<isbn>")
def api(isbn):
    # get book data
    try:
        book_query = "SELECT * FROM books WHERE isbn = :isbn;"
        book = db.execute(book_query, {"isbn":isbn})
    except:
        return error("Error when fetching book data", 404)

    # book not found
    if book.rowcount != 1:
        return error("Book not found", 404)

    # get book's rating
    rating = get_book_data("bBypFUkpDHox5Z5fjzJqg", isbn)

    # prepare api
    book_api = book.fetchone()

    return jsonify(
        title= book_api["title"],
        author= book_api["author"],
        year= book_api["year"],
        isbn= book_api["isbn"],
        review_count= rating["work_reviews_count"],
        average_score= rating["average_rating"]
        )
