from models.database import db

def get_balences_by_user_id(user_id):
        rows = db.execute("SELECT * FROM balances WHERE user_id = ?", user_id)
        return rows

def get_positive_stocks(user_id):
    rows = db.execute("SELECT * FROM balances WHERE user_id = ? AND shares > 0", user_id)
    return rows


def get_balances_for_user_shares(user_id, symbol, shares ):    
    balances = db.execute("SELECT * FROM balances WHERE user_id = ? AND symbol = ?", user_id, symbol)

    if len(balances) < 1:        
        return apology, "Insufficiente shares"
    balance = balances[0]
    if shares > balance["shares"]:
        return False, "Insufficiente shares"

    balance["shares"] -= shares
    db.execute("UPDATE balances SET shares = ? WHERE id = ?", balance["shares"],balance["id"])
    return True, None

