import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from Web_backend import (
    BankSystem,
    ATM,
    Data_Manager,
    Admin,
    MIN_DEPOSIT_LIMIT,
    MAX_DEPOSIT_LIMIT,
    MIN_WITHDRAWAL_LIMIT,
    MAX_WITHDRAWAL_LIMIT
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

# Initialize backend systems
data_manager = Data_Manager()
bank_system = BankSystem(data_manager)
atm = ATM(bank_system, data_manager)
admin_system = Admin(admin_pin="1212", b=bank_system)


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('home.html')


# ---------------- USER LOGIN (STEP 1) ----------------
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        acc_no = request.form.get('acc_no', '').strip()

        data = data_manager.load_data()

        if acc_no not in data:
            flash("Account not found!", "error")
            return redirect(url_for('user_login'))

        acc_data = data[acc_no]

        # If user is new and needs to set PIN first
        if acc_data.get("new_acc", False):
            flash("You need to generate your PIN first.", "info")
            return redirect(url_for('generate_pin', acc_no=acc_no))
        else:
            # Existing user → enter PIN
            return redirect(url_for('enter_pin', acc_no=acc_no))

    return render_template('user_login.html')


# ---------------- ENTER PIN (STEP 2 for existing user) ----------------
@app.route('/enter_pin/<acc_no>', methods=['GET', 'POST'])
def enter_pin(acc_no):
    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        result = atm.authenticate(acc_no, pin)

        if isinstance(result, tuple):
            success, msg = result
            if success:
                session['acc_no'] = acc_no
                atm.set_current_account(acc_no)
                flash(msg, 'success')
                return redirect(url_for('user_dashboard'))
            else:
                flash(msg, 'error')
                return redirect(url_for('enter_pin', acc_no=acc_no))
        else:
            flash(str(result), 'error')
            return redirect(url_for('enter_pin', acc_no=acc_no))

    return render_template('enter_pin.html', acc_no=acc_no)


# ---------------- GENERATE PIN (STEP 2 for new user) ----------------
@app.route('/generate_pin/<acc_no>', methods=['GET', 'POST'])
def generate_pin(acc_no):
    if request.method == 'POST':
        new_pin1 = request.form.get('new_pin1', '').strip()
        new_pin2 = request.form.get('new_pin2', '').strip()

        result = atm.authenticate(acc_no, None, new_pin1, new_pin2)

        if isinstance(result, tuple):
            success, msg = result
            if success:
                flash("Your PIN has been generated successfully. Please login again.", "success")
                return redirect(url_for('user_login'))
            else:
                flash(msg, 'error')
                return redirect(url_for('generate_pin', acc_no=acc_no))
        else:
            flash(str(result), 'error')
            return redirect(url_for('generate_pin', acc_no=acc_no))

    return render_template('generate_pin.html', acc_no=acc_no)


# ---------------- USER DASHBOARD ----------------
@app.route('/user_dashboard')
def user_dashboard():
    acc_no = session.get('acc_no')
    if not acc_no:
        return redirect(url_for('user_login'))

    account = bank_system.find_account(acc_no)
    if not account:
        session.pop('acc_no', None)
        flash("Account not found. Please log in again.", "error")
        return redirect(url_for('user_login'))

    atm.set_current_account(acc_no)
    transactions = []
    if hasattr(account, 'transactions') and account.transactions:
        transactions = account.transactions[-5:][::-1]

    return render_template('user_dashboard.html', account=account, transactions=transactions)


# ---------------- LOGOUT ----------------
@app.route('/user_logout')
def user_logout():
    session.pop('acc_no', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))


# ---------------- BALANCE ----------------
@app.route('/balance')
def balance():
    acc_no = session.get('acc_no')
    if not acc_no:
        return redirect(url_for('user_login'))

    msg = atm.show_balance(acc_no=acc_no)
    flash(msg, 'info')
    return redirect(url_for('user_dashboard'))


# ---------------- DEPOSIT ----------------
@app.route('/deposit_page', methods=['GET', 'POST'])
def deposit_page():
    acc_no = session.get('acc_no')
    if not acc_no:
        return redirect(url_for('user_login'))

    account = bank_system.find_account(acc_no)
    if not account:
        session.pop('acc_no', None)
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
        except (ValueError, TypeError):
            flash("Invalid amount entered!", "error")
            return redirect(url_for('deposit_page'))

        msg = atm.deposit_cash(amount, acc_no=acc_no)
        if "successfully" in msg.lower():
            flash(msg, 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash(msg, 'error')
            return redirect(url_for('deposit_page'))

    return render_template(
        'deposit_page.html',
        account=account,
        min_limit=MIN_DEPOSIT_LIMIT,
        max_limit=MAX_DEPOSIT_LIMIT
    )


# ---------------- WITHDRAW ----------------
@app.route('/withdraw_page', methods=['GET', 'POST'])
def withdraw_page():
    acc_no = session.get('acc_no')
    if not acc_no:
        return redirect(url_for('user_login'))

    account = bank_system.find_account(acc_no)
    if not account:
        session.pop('acc_no', None)
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
        except (ValueError, TypeError):
            flash("Invalid amount entered!", "error")
            return redirect(url_for('withdraw_page'))

        msg = atm.withdraw_cash(amount, acc_no=acc_no)
        if "successfully" in msg.lower():
            flash(msg, 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash(msg, 'error')
            return redirect(url_for('withdraw_page'))

    return render_template(
        'withdraw_page.html',
        account=account,
        min_limit=MIN_WITHDRAWAL_LIMIT,
        max_limit=MAX_WITHDRAWAL_LIMIT
    )


# ---------------- CHANGE PIN ----------------
@app.route('/change_pin_page', methods=['GET', 'POST'])
def change_pin_page():
    acc_no = session.get('acc_no')
    if not acc_no:
        flash("Please log in again.", "error")
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        old_pin = request.form.get('old_pin', '').strip()
        new_pin1 = request.form.get('new_pin1', '').strip()
        new_pin2 = request.form.get('new_pin2', '').strip()
        result = atm.pin_change(old_pin, new_pin1, new_pin2, acc_no=acc_no)

        if "successfully" in result.lower():
            flash(result, "success")
            return redirect(url_for('user_dashboard'))
        else:
            flash(result, "error")
            return redirect(url_for('change_pin_page'))

    return render_template('change_pin_page.html')


# ---------------- MINI STATEMENT ----------------
@app.route('/mini_statement')
def mini_statement():
    acc_no = session.get('acc_no')
    if not acc_no:
        return redirect(url_for('user_login'))

    account = bank_system.find_account(acc_no)
    if not account:
        return redirect(url_for('user_login'))

    transactions = []
    if hasattr(account, 'transactions') and account.transactions:
        transactions = account.transactions[-5:][::-1]

    return render_template('mini_statement.html', account=account, transactions=transactions)


# ---------------- FULL TRANSACTIONS ----------------
@app.route('/user_dashboard_full_transactions')
def user_dashboard_full_transactions():
    acc_no = session.get('acc_no')
    if not acc_no:
        return redirect(url_for('user_login'))

    account = bank_system.find_account(acc_no)
    if not account:
        return redirect(url_for('user_login'))

    transactions = []
    if hasattr(account, 'transactions') and account.transactions:
        transactions = account.transactions[::-1]

    return render_template('user_dashboard_full_transactions.html', account=account, transactions=transactions)


# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_pin = request.form.get('admin_pin', '').strip()
        success, msg = admin_system.authenticate(admin_pin)

        if success:
            session['admin_logged_in'] = True
            flash("Admin login successful.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid Admin PIN!", "error")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        flash("Please log in as admin.", "error")
        return redirect(url_for('admin_login'))

    all_accounts = bank_system.list_all_accounts()
    total_accounts = len(all_accounts)
    total_balance = sum(acc.get("balance", 0) for acc in all_accounts.values())

    return render_template(
        'admin_dashboard.html',
        total_accounts=total_accounts,
        total_balance=total_balance,
        accounts=all_accounts
    )


# ---------------- ADMIN LOGOUT ----------------
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Admin logged out successfully.", "success")
    return redirect(url_for('home'))


# ---------------- GENERATE / ADD ACCOUNT (ADMIN) ----------------
@app.route('/add_account', methods=['GET', 'POST'])
def add_account():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    suggested_acc_no = bank_system.generate_next_account_number()

    if request.method == 'POST':
        custom_acc_no = request.form.get('acc_no', '').strip()
        holder_name = request.form.get('holder_name', '').strip()
        initial_deposit = request.form.get('initial_deposit', '0').strip()
        pin_option = request.form.get('pin_option', 'require_setup')
        auto_pin = request.form.get('auto_pin', '').strip()

        if not holder_name:
            flash("Please enter the account holder name.", "error")
            return redirect(url_for('add_account'))

        final_pin = auto_pin if pin_option == 'direct_pin' and auto_pin else None

        success, msg, acc_no, generated_pin = admin_system.generate_account(
            holder_name=holder_name,
            initial_balance=initial_deposit,
            custom_acc_no=custom_acc_no,
            auto_pin=final_pin
        )

        if success:
            if generated_pin:
                flash(f"{msg} Set Temporary PIN: {generated_pin}", 'success')
            else:
                flash(f"{msg} User will create PIN on first login.", 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash(msg, 'error')
            return redirect(url_for('add_account'))

    return render_template('add_account.html', suggested_acc_no=suggested_acc_no)


# ---------------- GENERATE / RESET USER ACCESS (ADMIN) ----------------
@app.route('/admin_generate_access', methods=['GET', 'POST'])
def admin_generate_access():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    accounts_data = bank_system.list_all_accounts()

    if request.method == 'POST':
        acc_no = request.form.get('acc_no', '').strip()
        action = request.form.get('action', 'new_pin')
        custom_pin = request.form.get('custom_pin', '').strip()

        if not acc_no:
            flash("Please select or enter an account number.", "error")
            return redirect(url_for('admin_generate_access'))

        success, msg = admin_system.generate_or_reset_access(
            acc_no=acc_no,
            action=action,
            custom_pin=custom_pin
        )
        if success:
            flash(msg, 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash(msg, 'error')
            return redirect(url_for('admin_generate_access'))

    return render_template('admin_generate_access.html', accounts=accounts_data)


# ---------------- API: GET NEXT ACCOUNT NUMBER ----------------
@app.route('/api/next_account_number')
def next_account_number():
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"next_acc_no": bank_system.generate_next_account_number()})


# ---------------- REMOVE ACCOUNT ----------------
@app.route('/remove_account', methods=['GET', 'POST'])
def remove_account():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        acc_no = request.form.get('acc_no', '').strip()
        if not acc_no:
            flash("Please enter an account number.", "error")
            return redirect(url_for('remove_account'))

        msg = admin_system.remove_account(acc_no)
        if "successfully" in msg.lower():
            flash(msg, 'success')
        else:
            flash(msg, 'error')
        return redirect(url_for('admin_dashboard'))

    return render_template('remove_account.html')


# ---------------- LIST ALL ACCOUNTS ----------------
@app.route('/list_accounts')
def list_accounts():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    accounts_data = bank_system.list_all_accounts()
    return render_template('list_all_accounts.html', accounts=accounts_data)


if __name__ == "__main__":
    app.run(debug=True)
