
import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from Backend1 import Data_Manager, BankSystem

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "change-this-to-a-long-random-secret-before-deployment"
)

# Demonstration admin PIN. Change it before running.
ADMIN_PIN = os.environ.get("ATM_ADMIN_PIN", "9999")

data_manager = Data_Manager()
bank = BankSystem(data_manager)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def render_screen(screen, **kwargs):
    """Render every screen from the single HTML file."""
    return render_template(
        "atm_interface.html",
        screen=screen,
        **kwargs
    )


def get_account():
    """Return the logged-in user's account."""
    if not session.get("logged_in"):
        return None

    account_number = session.get("account_number")
    if not account_number:
        return None

    return bank.find_account(account_number)


def require_admin():
    return bool(session.get("admin_logged_in"))


def get_all_accounts():
    """Get account objects from BankSystem."""
    accounts = bank.list_all_accounts()
    if isinstance(accounts, dict):
        return [f"Account: {acc.acc_no} | Holder: {acc.holder_name} | Balance: ₹{acc.balance}" for acc in accounts.values()]
    return accounts if accounts is not None else []


def save_data_if_supported():
    """
    Persist data to Data_Manager in Backend1.py.
    """
    data = data_manager.load_data()
    if hasattr(bank, "accounts") and isinstance(bank.accounts, dict):
        for acc_no, acc in bank.accounts.items():
            if acc_no not in data:
                data[acc_no] = {}
            data[acc_no]["pin"] = str(acc.pin)
            data[acc_no]["balance"] = acc.balance
            data[acc_no]["holder_name"] = acc.holder_name
            txns = []
            for t in getattr(acc, "transactions", []):
                if hasattr(t, "make_dict"):
                    txns.append(t.make_dict())
                elif isinstance(t, dict):
                    txns.append(t)
                else:
                    txns.append({
                        "type": "Transaction",
                        "amount": 0,
                        "balance_after": acc.balance,
                        "note": str(t),
                        "time": ""
                    })
            data[acc_no]["transactions"] = txns
    data_manager.save_data(data)


def record_transaction(account, transaction_type, amount):
    """Append a transaction to the account's history."""
    if not hasattr(account, "transactions") or account.transactions is None:
        account.transactions = []

    from datetime import datetime
    account.transactions.append({
        "type": transaction_type,
        "amount": round(amount, 2),
        "balance_after": round(float(account.balance), 2),
        "note": f"{transaction_type} of ₹{round(amount, 2)}",
        "time": datetime.now().strftime("On %d-%m-%Y At %H:%M:%S")
    })


def get_account_details(account):
    """Prepare account information for the template."""
    return {
        "account_number": account.acc_no,
        "holder_name": account.holder_name,
        "balance": account.balance
    }


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return render_screen("home")


# --------------------------------------------------
# USER LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "GET":
        return render_screen("login")

    account_number = request.form.get("account_number", "").strip()
    pin = request.form.get("pin", "").strip()

    if not account_number or not pin:
        return render_screen(
            "login",
            error="Enter your account number and PIN."
        )

    account = bank.find_account(account_number)

    if account is None:
        return render_screen("login", error="Account not found.")

    if str(account.pin) != pin:
        return render_screen("login", error="Invalid PIN.")

    session.clear()
    session["account_number"] = account_number
    session["logged_in"] = True

    return redirect(url_for("user_dashboard"))


# --------------------------------------------------
# USER DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def user_dashboard():
    account = get_account()

    if account is None:
        return redirect(url_for("user_login"))

    return render_screen(
        "dashboard",
        **get_account_details(account)
    )


# --------------------------------------------------
# BALANCE ENQUIRY
# --------------------------------------------------

@app.route("/balance")
def balance_enquiry():
    account = get_account()

    if account is None:
        return redirect(url_for("user_login"))

    return render_screen(
        "balance",
        **get_account_details(account)
    )


# --------------------------------------------------
# DEPOSIT
# --------------------------------------------------

@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    account = get_account()

    if account is None:
        return redirect(url_for("user_login"))

    if request.method == "GET":
        return render_screen("deposit")

    try:
        amount = float(request.form.get("amount", "").strip())

        if not amount > 0:
            raise ValueError

    except (ValueError, AttributeError):
        return render_screen(
            "deposit",
            error="Enter a valid positive amount."
        )

    account.balance = round(float(account.balance) + amount, 2)
    record_transaction(account, "Deposit", amount)

    try:
        save_data_if_supported()
    except Exception:
        app.logger.exception("Could not persist deposit")

        return render_screen(
            "deposit",
            error="Deposit was processed in memory, but saving failed."
        )

    return render_screen(
        "deposit",
        message=f"₹{amount:.2f} deposited successfully.",
        balance=account.balance
    )


# --------------------------------------------------
# WITHDRAWAL
# --------------------------------------------------

@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    account = get_account()

    if account is None:
        return redirect(url_for("user_login"))

    if request.method == "GET":
        return render_screen("withdraw")

    try:
        amount = float(request.form.get("amount", "").strip())

        if not amount > 0:
            raise ValueError

    except (ValueError, AttributeError):
        return render_screen(
            "withdraw",
            error="Enter a valid positive amount."
        )

    if amount > float(account.balance):
        return render_screen(
            "withdraw",
            error="Insufficient balance."
        )

    account.balance = round(float(account.balance) - amount, 2)
    record_transaction(account, "Withdrawal", amount)

    try:
        save_data_if_supported()
    except Exception:
        app.logger.exception("Could not persist withdrawal")

        return render_screen(
            "withdraw",
            error="Withdrawal was processed in memory, but saving failed."
        )

    return render_screen(
        "withdraw",
        message=f"₹{amount:.2f} withdrawn successfully.",
        balance=account.balance
    )


# --------------------------------------------------
# CHANGE PIN
# --------------------------------------------------

@app.route("/change-pin", methods=["GET", "POST"])
def change_pin():
    account = get_account()

    if account is None:
        return redirect(url_for("user_login"))

    if request.method == "GET":
        return render_screen("change_pin")

    old_pin = request.form.get("old_pin", "").strip()
    new_pin = request.form.get("new_pin", "").strip()

    if str(account.pin) != old_pin:
        return render_screen(
            "change_pin",
            error="Current PIN is incorrect."
        )

    if not new_pin.isdigit() or len(new_pin) != 4:
        return render_screen(
            "change_pin",
            error="New PIN must contain exactly four digits."
        )

    account.pin = new_pin

    try:
        save_data_if_supported()
    except Exception:
        app.logger.exception("Could not persist PIN change")

        return render_screen(
            "change_pin",
            error="PIN changed in memory, but saving failed."
        )

    return render_screen(
        "change_pin",
        message="PIN changed successfully."
    )


# --------------------------------------------------
# MINI STATEMENT
# --------------------------------------------------

@app.route("/mini-statement")
def mini_statement():
    account = get_account()

    if account is None:
        return redirect(url_for("user_login"))

    history = getattr(account, "transactions", None) or []

    return render_screen(
        "mini_statement",
        transactions=history[-5:][::-1]
    )


# --------------------------------------------------
# ALL TRANSACTIONS
# --------------------------------------------------

@app.route("/transactions")
def transactions():
    account = get_account()

    if account is None:
        return redirect(url_for("user_login"))

    history = getattr(account, "transactions", None) or []

    return render_screen(
        "transactions",
        transactions=history[::-1]
    )
    @app.route("/logout")
    def logout():
         session.clear()
         return redirect(url_for("user_login"))


# --------------------------------------------------
# ADMIN LOGIN
# --------------------------------------------------

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_screen("admin_login")

    admin_pin = request.form.get("admin_pin", "").strip()

    if admin_pin != ADMIN_PIN:
        return render_screen(
            "admin_login",
            error="Invalid admin PIN. Please try again."
        )

    session.clear()
    session["admin_logged_in"] = True

    return redirect(url_for("admin_dashboard"))


# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------

@app.route("/admin-dashboard")
def admin_dashboard():
    if not require_admin():
        return redirect(url_for("admin_login"))

    return render_screen("admin_dashboard")


# --------------------------------------------------
# LIST ALL ACCOUNTS
# --------------------------------------------------

@app.route("/list-accounts")
def list_accounts():
    if not require_admin():
        return redirect(url_for("admin_login"))

    accounts = get_all_accounts()

    return render_screen(
        "list_accounts",
        accounts=accounts
    )


# --------------------------------------------------
# GENERATE / RESET USER PIN
# --------------------------------------------------

@app.route("/generate-pin", methods=["GET", "POST"])
def generate_pin():
    if not require_admin():
        return redirect(url_for("admin_login"))

    if request.method == "GET":
        return render_screen("generate_pin")

    account_number = request.form.get("account_number", "").strip()
    account = bank.find_account(account_number)

    if account is None:
        return render_screen(
            "generate_pin",
            error="Account not found."
        )

    # Generate a random four-digit PIN.
    import secrets
    new_pin = f"{secrets.randbelow(9000) + 1000:04d}"
    account.pin = new_pin

    try:
        save_data_if_supported()
    except Exception:
        app.logger.exception("Could not persist generated PIN")

        return render_screen(
            "generate_pin",
            error="PIN changed in memory, but saving failed."
        )

    return render_screen(
        "generate_pin",
        message=f"PIN generated successfully: {new_pin}"
    )


# --------------------------------------------------
# REMOVE ACCOUNT
# --------------------------------------------------

@app.route("/remove-account", methods=["GET", "POST"])
def remove_account():
    if not require_admin():
        return redirect(url_for("admin_login"))

    if request.method == "GET":
        return render_screen("remove_account")

    account_number = request.form.get("account_number", "").strip()
    account = bank.find_account(account_number)

    if account is None:
        return render_screen(
            "remove_account",
            error="Account not found."
        )

    try:
        bank.remove_account(account_number)
        save_data_if_supported()
    except Exception:
        app.logger.exception("Could not remove account")

        return render_screen(
            "remove_account",
            error="Could not remove the account. Check Backend1.py."
        )

    return render_screen(
        "remove_account",
        message="Account removed successfully."
    )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user_login"))


# --------------------------------------------------
# RUN APP
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)