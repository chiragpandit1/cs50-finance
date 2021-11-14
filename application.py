import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

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


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return render_template("home.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():


    if request.method == "GET":
        return render_template("quote.html")

    elif request.method == "POST":
        return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    # render page that has register form when request is GET
    if request.method == "GET":
        return render_template("register.html")

    # process and register the user if request is POST
    elif request.method == "POST":
        print("Registering user...")
        """Register user"""

        # get the value of username
        username = request.form.get("username")
        if not username:
            return apology("Unable to register, must provide username", 422)

        # get the value for password
        password = request.form.get("password")
        if not password:
            return apology("Unable to register, must provide password", 422)

        # Check whether either password does not matches
        password_again = request.form.get("password_again")
        if not password_again:
            return apology("Unable to register, please type password again", 422)

        # compare password
        if password_again != password:
            return apology("Unable to register, passwords do not match", 422)

        # generate password hash from generate_password_hash to store it in DB
        password_hash = generate_password_hash(password)

        # Check whether user exists in db with that username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        print(rows)

        if len(rows) != 0:  # if user exists, Show an error message on that form that user already exists
            return apology("Unable to register, User already registered, Please login to use CS50 finance", 422)

        else:  # if user does not exists then -> store the value for username and generated password hash in db
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, password_hash)

            # return success page
            flash("Registered!")
            return render_template("home.html")

        # return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
