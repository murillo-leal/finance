import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from helpers import apology, login_required, lookup, usd

from models import balances, history as history_db, users, database
db = database.db

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

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user = users.get_user_by_id(session["user_id"])

    rows = balances.get_balences_by_user_id(user["id"])
    
    stocks = []    
    for row in rows:
        balance = row
        stock = lookup(balance["symbol"])
        balance["price"] = stock["price"]
        balance["total"] = stock["price"] * balance["shares"]
        balance["name"] = stock["name"]
        stocks.append(balance)

    return render_template("index.html", cash=user["cash"], stocks=stocks, user=user)


   


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = history_db.get_history_by_user_id(session["user_id"])  
    return render_template("history.html", history=history)


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

        user = users.get_user_by_username_and_password(request.form.get("username"), request.form.get("password"))
        if not user:
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user["id"]

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

        new_user_id = users.register(username, password)

        # Remember which user has logged in
        flash("Registered", "success")
        session["user_id"] = new_user_id

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Change password"""
    if request.method == "POST":
        current_password = request.form.get("current_password")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

         # Ensure username was submitted
        if not current_password:
            return apology("must provide current password", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)
        
        elif confirmation != password:
            return apology("passwords didn't match", 403)    

        update_successfully = users.update_password(session["user_id"], current_password, password)

        if not update_successfully:
            #Error
            flash("Invalid current password!", "warning")
            return render_template("settings.html")
        else:
            #Redirect
            flash("Password updated successfully!", "success")
            return redirect("/")


        # Remember which user has logged in
        flash("Password Updated successfully", "warning")

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("settings.html")        

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

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if shares < 1:
           return apology("must provide a positive shares quantity", 400)            

        if not symbol:
            return apology("must provide a stock symbol", 400)  

        stock = lookup(symbol)
        if not stock:
            return apology(f"error retrieving stock '{symbol}'", 400)  
   
        symbol = symbol.upper()

        sucess, message = balances.get_balances_for_user_shares(session["user_id"], symbol, shares)
        if not sucess:
            return apology(message, 400)

        history_db.insert_new_entry(session["user_id"], symbol, shares * -1, stock["price"])

        users.add_cash(session["user_id"], stock["price"] * shares)       
           
        flash(f"sold'{shares}' shares of '{symbol}' successfully", "success")        
        return redirect("/")

    else:     
        stocks = balances.get_positive_stocks(session["user_id"])
        return render_template("sell.html", stocks=stocks)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
