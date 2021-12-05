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
    return render_homepage()


def render_homepage():
    user_record = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

    user_holdings = db.execute("SELECT DISTINCT (asset_ticker),"
                               " SUM(quantity) as quantity,"
                               " SUM(price) AS price"
                               " FROM transaction_details"
                               " WHERE user_id=?"
                               " GROUP BY asset_ticker", session["user_id"])

    # TODO - Add details in user_holdings about current price of that stock and its company name

    # Add details in user_holdings about current price of that stock and its company name
    homepage_records = [];
    user_margin = float(user_record[0]["cash"])
    asset_total = user_margin
    for holding in user_holdings:
        ticker_details = lookup(holding['asset_ticker'])
        current_share_price = float(ticker_details['price'])
        print(f"Current share price of {holding['asset_ticker']} is {current_share_price}")

        # Fetch share's current prices.
        print(f"Adding {holding['price']} with {asset_total}")
        asset_total += float(holding['price'])
        homepage_record = {
            "asset_ticker": holding["asset_ticker"],
            "ticker_current_price": usd(current_share_price),
            "ticker_detail_name": ticker_details['name'],
            "total_quantity": holding['quantity'],
            "total_price": usd(holding['price'])
        }
        homepage_records.append(homepage_record)

    return render_template("home.html",
                           cash=usd(float(user_record[0]["cash"])),
                           asset_total=usd(asset_total),
                           user_holdings=homepage_records)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")

    elif request.method == "POST":

        symbol = request.form.get("symbol")
        quantity = float(request.form.get("shares"))

        # TODO - :(buy handles fractional, negative, and non-numeric shares - # expected status code 400, but got 200

        # Query the IEX Stocks API - # Send the response back to the page
        response = lookup(symbol)

        if not response:
            print(response)
            return apology("Unable to buy now, Ticket invalid!", 400);
        else:
            # Response - {{response.name}} ({{response.symbol}}) costs ${{response.price}}
            print(response)

            name = response['name']
            print(name)

            symbol = response['symbol']
            print(symbol)

            price = response['price']
            print(price)
            price = float(price)
            print(price)

            rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

            # Retrieve the total margin / cash user has on their account
            user_margin = float(rows[0]["cash"])

            # Buy Shares of that stock multiplied by quantity
            total_price = price * quantity
            if user_margin < total_price:
                return apology("Unable to buy now, Not sufficient cash!", 400);
            else:
                # Reduce user margin
                user_margin = user_margin - total_price

                # Update user_margin / cash on backend for that user -
                # TODO - UPDATE TABLE user SET cash = user_margin WHERE id = session["user_id"]
                db.execute("UPDATE users SET cash = ? WHERE id = ?", user_margin, session["user_id"])

                # TODO - Add the record in transactions_details, and holdings TABLES where userID = session
                db.execute("  INSERT INTO transaction_details "
                           "   (user_id, asset_ticker, transaction_type, quantity, price, transaction_date) "
                           "  VALUES (?, ?, 'BUY', ?, ?, datetime('now'))",
                           session["user_id"], symbol, quantity, total_price)

                success_message = f"Bought {quantity} shares for {name}({symbol}) at {price}"
                print(f"{success_message}, \nNew User Margin Available = {usd(user_margin)}")

                # return success page
                flash(f"{success_message}")
                return render_homepage()

            # Redirect user back to quote details_page - # {'name': 'Apple Inc', 'price': 149.99, 'symbol': 'AAPL'}
            # return render_template("buy.html", response=response)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT * FROM transaction_details WHERE user_id=?", session["user_id"])
    return render_template("history.html", rows=rows)


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

        symbol = request.form.get("symbol")

        # handle blank Symbol - 400

        # Query the IEX Stocks API - # Send the response back to the page
        response = lookup(symbol)  # print(response)

        # handle invalid Symbol - 400
        if not response:
            print(response)
            return apology("Unable to buy now, Ticket invalid!", 400);

        # Redirect user back to quote details_page - # {'name': 'Apple Inc', 'price': 149.99, 'symbol': 'AAPL'}
        # print(f"{usd(response['price'])}")
        return render_template("quote.html", response=response, price=usd(response['price']))


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
            return apology("Unable to register, must provide username", 400)

        # get the value for password
        password = request.form.get("password")
        if not password:
            return apology("Unable to register, must provide password", 400)

        # Check whether either password does not matches
        password_again = request.form.get("confirmation")
        if not password_again:
            return apology("Unable to register, please type password again", 400)

        # compare password
        if password_again != password:
            return apology("Unable to register, passwords do not match", 400)

        # generate password hash from generate_password_hash to store it in DB
        password_hash = generate_password_hash(password)

        # Check whether user exists in db with that username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        print(rows)

        if len(rows) != 0:  # if user exists, Show an error message on that form that user already exists
            return apology("Unable to register, User already registered, Please login to use CS50 finance", 400)

        else:  # if user does not exists then -> store the value for username and generated password hash in db
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, password_hash)
            user_details = db.execute("SELECT * FROM users WHERE username=? ", username)
            session["user_id"] = user_details[0]["id"]

            # return success page
            flash("Registered!")

            user_record = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

            user_holdings = db.execute("SELECT DISTINCT (asset_ticker),"
                                       " SUM(quantity) AS quantity,"
                                       " SUM(price) AS price"
                                       " FROM transaction_details"
                                       " WHERE user_id=?"
                                       " GROUP BY asset_ticker", session["user_id"])

            return render_template("home.html",
                                   cash=usd(float(user_record[0]["cash"])),
                                   user_holdings=user_holdings)


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
