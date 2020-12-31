import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
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

# Create table for user balance
db.execute("""
CREATE TABLE IF NOT EXISTS 'balances' (
    'id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    'user_id' INTEGER NOT NULL,
    'symbol' TEXT NOT NULL,
    'shares' INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
db.execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_balances_user_id_symbol ON balances (user_id, symbol)")    

# Create table of user history
db.execute("""
CREATE TABLE IF NOT EXISTS 'history' (
    'id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    'user_id' INTEGER, 'symbol' TEXT,
    'shares' INTEGER NOT NULL,
    'price' NUMERIC NOT NULL,
    'created_at' DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)    
    )
    """)
db.execute("CREATE UNIQUE INDEX IF NOT EXISTS index_history_user_id ON balances (user_id, symbol)")    

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if shares < 1:
            return apology("must provide a positive shares quantity", 400)
            

        if not symbol:
            return apology("must provide a stock symbol", 400)  

        symbol = symbol.upper()
        stock = lookup(symbol)

        if not stock:
            return apology(f"invalid stock '{symbol}'", 400)

        total = stock["price"] * shares

        users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        user = users[0]
        if user["cash"] < total:
            return apology(f"insufficiente balance", 400)      

        rows = db.execute("SELECT * FROM balances WHERE user_id = ? AND symbol = ?", user["id"], symbol)
        if len(rows) < 1:
            db.execute("INSERT INTO balances (user_id, symbol, shares) VALUES (?, ?, ?)", user["id"], symbol, shares)
        else:
            balance = rows[0]
            balance["shares"] += shares
            db.execute("UPDATE balances SET shares = ? WHERE id = ?", balance["shares"], balance["id"])


        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)", user["id"], symbol, shares, stock["price"])

        updated_cash = user["cash"] - total
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, user["id"])
           
        flash(f"bought'{shares}' shares of '{symbol}' successfully", "success")        
        return redirect("/")

    else:     
        return render_template("buy.html")   


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            flash("You must provide a stock symbol", "danger")
            return render_template("quote.html")  

        stock = lookup(symbol)

        if not stock:
            flash(f"invalid stock'{symbol}'", "danger")
            return render_template("quote.html")  

        return render_template("quoted.html", stock=stock)

    else:     
        return render_template("quote.html")   

    


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

         # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)
        
        elif confirmation != password:
            return apology("passwords didn't match", 403)    

        hashed_password = generate_password_hash(password)

        new_user_id = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)

        # Remember which user has logged in
        session["user_id"] = new_user_id

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("register.html")


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
