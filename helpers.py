import requests

from functools import wraps
from flask import g, request, redirect, url_for, render_template, session

def login_required(f):
    """
    Flask login_required decorator
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def error(message, code=400):
    return render_template("error.html", message=message, code=code), code


def get_book_data(key, isbn):
    try:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    except:
        return None
    return res.json()["books"][0]
