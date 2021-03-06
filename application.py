import os
import csv
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required,apology

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///movies.db")
db2 = SQL("sqlite:///moviesclassification.db")

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    rows = db.execute("SELECT username, post, time FROM posts INNER JOIN users ON posts.user_id=users.id ORDER BY time DESC")
    return render_template("index.html", rows = rows)
    

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    rows = db.execute(
        "SELECT movie,rating,watched_time FROM history WHERE user_id = ? ORDER BY watched_time DESC", session["user_id"])
    return render_template("history.html", rows=rows)

@app.route("/add", methods=["GET", "POST"] )
@login_required
def add():
    if request.method == "POST":
        movie = request.form.get("movie")

                
        rating = int(request.form.get("rating"))
        
        if rating <= 0:
            return apology("Invalid Number", 403) 
        
        if rating > 10:
            return apology("Invalid Number", 403)
        
        db.execute("INSERT INTO history (user_id,movie,rating) VALUES(?,?,?)", session["user_id"], movie, rating)
        flash("Watched!")
        return redirect("/history")
    else:
        return render_template("add.html")


@app.route("/top", methods=["GET", "POST"])
@login_required
def top():
    if request.method == "POST":
        number = int(request.form.get("number"))
        
        if number <= 0:
            return apology("Invalid Number", 403)

        rows = db2.execute("SELECT title, release_date, vote_count, vote_average,overview FROM movies WHERE vote_count > 500 ORDER BY vote_average DESC LIMIT ?", number)
        return render_template("toped.html", rows = rows, number = number)
    else:
         return render_template("top.html")



@app.route("/connect", methods=["GET", "POST"])
@login_required
def connect():
    if request.method == "POST":
        post = request.form.get("connect")
        db.execute("INSERT INTO posts (user_id,post) VALUES(?,?)", session["user_id"], post)
        flash("Posted!")
        return redirect("/")
    else:
        return render_template("connect.html")
        
        
    

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Password needs to be the same", 400)

        else:
            username = request.form.get("username")
            password = request.form.get("password")
            try:
                db.execute("INSERT INTO users (username,hash) VALUES(?,?)", username,
                           generate_password_hash(password, method='pbkdf2:sha256', salt_length=8))
            except:
                return apology("Username already used.", 400)
            return redirect("/")
    else:
        return render_template("register.html")
        
@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        if not request.form.get("new_password"):
            return apology("must provide password", 400)
        if request.form.get("new_password") != request.form.get("repeat_password"):
            return apology("Password needs to be the same", 400)
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        if check_password_hash(rows[0]["hash"], request.form.get("new_password")):
            return apology("New Password needs to be keyed", 400)
        new_password = request.form.get("new_password")
        db.execute("UPDATE users SET hash=? WHERE id=?", generate_password_hash(
            new_password, method='pbkdf2:sha256', salt_length=8), session["user_id"])
        flash("Changed password!")
        return redirect("/")
        
    else:
        return render_template("change_password.html")



