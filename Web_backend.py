import json, time
import uuid
from datetime import datetime
from abc import ABC, abstractmethod
import os

# Transaction limits
MIN_DEPOSIT_LIMIT = 100.0
MAX_DEPOSIT_LIMIT = 50000.0

MIN_WITHDRAWAL_LIMIT = 100.0
MAX_WITHDRAWAL_LIMIT = 20000.0


class Data_Manager:
    def __init__(self, filename="bank_data.json"):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as file:
                json.dump({}, file)

    def load_data(self):
        try:
            with open(self.filename, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            self.save_data({})
            return {}

    def save_data(self, data):
        with open(self.filename, "w") as file:
            json.dump(data, file, indent=4)

    def update_acc(self, acc_no, field, value):
        data = self.load_data()
        if acc_no in data:
            data[acc_no][field] = value
            self.save_data(data)

    def add_transaction_to_json(self, acc_no, t):
        data = self.load_data()
        if acc_no in data:
            data[acc_no]["transactions"].append(t.make_dict())
            self.save_data(data)

    def add_account_to_json(self, account):
        data = self.load_data()
        data[account.acc_no] = account.make_dict()
        self.save_data(data)

    def remove_account_to_json(self, acc_no):
        data = self.load_data()
        if acc_no in data:
            del data[acc_no]
            self.save_data(data)


class AccountBase(ABC):
    @abstractmethod
    def check_pin(self, entered_pin):
        pass

    @abstractmethod
    def deposit(self, e_amount):
        pass

    @abstractmethod
    def withdraw(self, e_amount):
        pass

    @abstractmethod
    def get_balance(self):
        pass

    @abstractmethod
    def add_transaction(self, t_type, note="", amount=0):
        pass


class BankBase(ABC):
    @abstractmethod
    def add_account(self, account):
        pass

    @abstractmethod
    def find_account(self, acc_no):
        pass

    @abstractmethod
    def remove_account(self, acc_no):
        pass

    @abstractmethod
    def list_all_accounts(self):
        pass


class Transaction:
    def __init__(self, type, amount, balance_after, note="", t=None):
        self.type = type
        self.amount = amount
        self.balance_after = balance_after
        self.note = note
        self.transaction_id = str(uuid.uuid4())[:8]
        if t is None:
            t = datetime.now().strftime("On %d-%m-%Y At %H:%M:%S")
        self.timestamp = t
        self.time = t

    def make_dict(self):
        return {
            "type": self.type,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "note": self.note,
            "time": self.timestamp
        }

    def __str__(self):
        return f"[{self.timestamp}] Transaction type : {self.type} | Amount ₹{self.amount} → Balance : ₹{self.balance_after} | Note : {self.note}"


def convert_dict_to_strOFobj(l):
    k = []
    if not l:
        return k
    for item in l:
        if isinstance(item, dict):
            time_val = item.get("time") or item.get("timestamp")
            new_txn = Transaction(
                item.get("type", ""),
                item.get("amount", 0),
                item.get("balance_after", 0),
                item.get("note", ""),
                time_val
            )
            k.append(new_txn)
        elif isinstance(item, Transaction):
            k.append(item)
    return k


class Account(AccountBase):
    def __init__(self, acc_no, pin=None, balance=0, holder_name="Unknown", transactions=None, new_acc=False):
        self.acc_no = acc_no
        self.pin = pin
        self.balance = balance
        self.holder_name = holder_name
        self.transactions = transactions if transactions is not None else []
        self.new_acc = new_acc
        self.data = Data_Manager()

    def check_pin(self, entered_pin):
        return str(self.pin) == str(entered_pin)

    def deposit(self, e_amount):
        try:
            e_amount = float(e_amount)
        except (ValueError, TypeError):
            return "Invalid deposit amount."

        if e_amount < MIN_DEPOSIT_LIMIT:
            return f"Deposit rejected! Minimum deposit amount is ₹{MIN_DEPOSIT_LIMIT:,.2f}."
        if e_amount > MAX_DEPOSIT_LIMIT:
            return f"Deposit limit exceeded! Maximum allowed deposit is ₹{MAX_DEPOSIT_LIMIT:,.2f} per transaction."

        old_balance = self.balance
        self.balance = round(self.balance + e_amount, 2)
        new_txn = Transaction(
            "Deposit",
            e_amount,
            self.balance,
            f"Inserted ₹{e_amount:,.2f} | Balance: ₹{old_balance:,.2f} → ₹{self.balance:,.2f}"
        )
        self.transactions.append(new_txn)
        self.data.add_transaction_to_json(self.acc_no, new_txn)
        self.data.update_acc(self.acc_no, "balance", self.balance)
        return f"Inserted Amount: ₹{e_amount:,.2f} deposited successfully! Previous Balance: ₹{old_balance:,.2f} | New Balance: ₹{self.balance:,.2f}"

    def withdraw(self, e_amount):
        try:
            e_amount = float(e_amount)
        except (ValueError, TypeError):
            return "Invalid withdrawal amount."

        if e_amount < MIN_WITHDRAWAL_LIMIT:
            return f"Withdrawal rejected! Minimum withdrawal amount is ₹{MIN_WITHDRAWAL_LIMIT:,.2f}."
        if e_amount > MAX_WITHDRAWAL_LIMIT:
            return f"Withdrawal limit exceeded! Maximum allowed withdrawal is ₹{MAX_WITHDRAWAL_LIMIT:,.2f} per transaction."
        if e_amount > self.balance:
            return f"Insufficient balance! Requested withdrawal: ₹{e_amount:,.2f}, but available balance is only ₹{self.balance:,.2f}."

        old_balance = self.balance
        self.balance = round(self.balance - e_amount, 2)
        new_txn = Transaction(
            "Withdraw",
            e_amount,
            self.balance,
            f"Dispensed ₹{e_amount:,.2f} | Balance: ₹{old_balance:,.2f} → ₹{self.balance:,.2f}"
        )
        self.transactions.append(new_txn)
        self.data.add_transaction_to_json(self.acc_no, new_txn)
        self.data.update_acc(self.acc_no, "balance", self.balance)
        return f"Dispensed Amount: ₹{e_amount:,.2f} withdrawn successfully! Previous Balance: ₹{old_balance:,.2f} | Remaining Balance: ₹{self.balance:,.2f}"

    def get_balance(self):
        return self.balance

    def add_transaction(self, t_type, note="", amount=0):
        t = Transaction(t_type, amount, self.balance, note)
        self.transactions.append(t)
        self.data.add_transaction_to_json(self.acc_no, t)

    def make_dict(self):
        return {
            "acc_no": self.acc_no,
            "pin": self.pin,
            "balance": self.balance,
            "holder_name": self.holder_name,
            "failed_attempts": 0,
            "lock_until": None,
            "new_acc": self.new_acc,
            "transactions": [t.make_dict() if isinstance(t, Transaction) else t for t in self.transactions]
        }


class BankSystem(BankBase):
    def __init__(self, d=None):
        if d is None:
            d = Data_Manager()
        self.d = d
        self.accounts = {}
        self.sync_accounts()

    def sync_accounts(self):
        data = self.d.load_data()
        self.accounts = {
            acc_no: Account(
                acc_no,
                acc_data.get("pin"),
                acc_data.get("balance", 0),
                acc_data.get("holder_name", "Unknown"),
                convert_dict_to_strOFobj(acc_data.get("transactions", [])),
                acc_data.get("new_acc", False)
            ) for acc_no, acc_data in data.items()
        }

    def add_account(self, account):
        data = self.d.load_data()
        if account.acc_no in data:
            return "Account already exists."
        self.d.add_account_to_json(account)
        self.accounts[account.acc_no] = account
        return "Account added successfully."

    def find_account(self, acc_no):
        data = self.d.load_data()
        if acc_no not in data:
            return None

        acc_data = data[acc_no]
        acc = Account(
            acc_no,
            acc_data.get("pin"),
            acc_data.get("balance", 0),
            acc_data.get("holder_name", "Unknown"),
            convert_dict_to_strOFobj(acc_data.get("transactions", [])),
            acc_data.get("new_acc", False)
        )
        self.accounts[acc_no] = acc
        return acc

    def remove_account(self, acc_no):
        data = self.d.load_data()
        if acc_no in data or acc_no in self.accounts:
            if acc_no in self.accounts:
                del self.accounts[acc_no]
            self.d.remove_account_to_json(acc_no)
            return "Account deleted successfully."
        return "Account not found."

    def list_all_accounts(self):
        return self.d.load_data()

    def generate_next_account_number(self):
        data = self.d.load_data()
        max_num = 1000
        for acc in data.keys():
            if acc.startswith("ACC"):
                digits = acc[3:]
                if digits.isdigit():
                    max_num = max(max_num, int(digits))
        return f"ACC{max_num + 1}"


class ATM:
    def __init__(self, b_, d=None):
        self.BankSystem = b_
        self.current_account = None
        self.data = d if d is not None else Data_Manager()

    def set_current_account(self, acc_no):
        acc = self.BankSystem.find_account(acc_no)
        self.current_account = acc
        return acc

    def login_attempt(self, acc_no, entered_pin):
        data = self.data.load_data()

        if acc_no not in data:
            return False, "Account not found."

        acc_info = data[acc_no]

        if acc_info.get("lock_until") and acc_info["lock_until"] > time.time():
            remaining = int(acc_info["lock_until"] - time.time())
            return False, f"Account locked. Try again after {remaining} seconds."

        f_a = acc_info.get("failed_attempts", 0)

        if str(acc_info.get("pin")) == str(entered_pin):
            self.data.update_acc(acc_no, "failed_attempts", 0)
            self.data.update_acc(acc_no, "lock_until", None)
            acc = self.BankSystem.find_account(acc_no)
            self.current_account = acc
            return True, "Authentication successful."

        f_a += 1
        self.data.update_acc(acc_no, "failed_attempts", f_a)

        if f_a >= 3:
            self.data.update_acc(acc_no, "lock_until", time.time() + 30)
            return False, "Too many incorrect attempts. Account locked for 30 seconds."

        remaining = 3 - f_a
        return False, f"Incorrect PIN. {remaining} attempts left."

    def authenticate(self, acc_no, pin=None, new_pin1=None, new_pin2=None):
        data = self.data.load_data()
        if acc_no not in data:
            return False, "Account not found."

        acc_data = data[acc_no]

        if acc_data.get("new_acc", False):
            if new_pin1 is None or new_pin2 is None:
                return False, "PIN setup required."
            if new_pin1 != new_pin2:
                return False, "PINs do not match."
            if len(new_pin1) != 4 or not new_pin1.isdigit():
                return False, "PIN must be exactly 4 digits."
            self.data.update_acc(acc_no, "pin", new_pin1)
            self.data.update_acc(acc_no, "new_acc", False)
            self.set_current_account(acc_no)
            return True, "New PIN created successfully."

        result = self.login_attempt(acc_no, pin)
        return result

    def show_balance(self, acc_no=None):
        if acc_no:
            self.set_current_account(acc_no)
        if self.current_account:
            return f"Current Balance: ₹{self.current_account.balance}"
        return "No active account."

    def withdraw_cash(self, amount, acc_no=None):
        if acc_no:
            self.set_current_account(acc_no)
        if self.current_account:
            return self.current_account.withdraw(amount)
        return "No active account."

    def deposit_cash(self, amount, acc_no=None):
        if acc_no:
            self.set_current_account(acc_no)
        if self.current_account:
            return self.current_account.deposit(amount)
        return "No active account."

    def pin_change(self, old_pin, new_pin1, new_pin2, acc_no=None):
        if acc_no:
            self.set_current_account(acc_no)
        if not self.current_account:
            return "No active account."
        if not self.current_account.check_pin(old_pin):
            return "Invalid current PIN."
        if new_pin1 != new_pin2:
            return "PINs do not match."
        if len(new_pin1) != 4 or not new_pin1.isdigit():
            return "PIN must be exactly 4 digits."
        self.current_account.pin = new_pin1
        self.data.update_acc(self.current_account.acc_no, "pin", new_pin1)
        return "PIN changed successfully."


class Admin:
    def __init__(self, admin_pin=1212, b=None):
        self.a_pin = admin_pin
        self.b = b if b is not None else BankSystem()

    def authenticate(self, entered_pin):
        if str(entered_pin).strip() == str(self.a_pin).strip():
            return True, "Authentication successful."
        return False, "Invalid admin PIN."

    def generate_account(self, holder_name, initial_balance=0.0, custom_acc_no=None, auto_pin=None):
        acc_no = custom_acc_no.strip() if custom_acc_no and custom_acc_no.strip() else self.b.generate_next_account_number()
        data = self.b.d.load_data()
        if acc_no in data:
            return False, f"Account {acc_no} already exists.", None, None

        try:
            initial_balance = max(0.0, float(initial_balance))
        except (ValueError, TypeError):
            initial_balance = 0.0

        if auto_pin and str(auto_pin).strip().isdigit() and len(str(auto_pin).strip()) == 4:
            pin = str(auto_pin).strip()
            new_acc = False
        else:
            pin = None
            new_acc = True

        acc = Account(
            acc_no,
            pin=pin,
            balance=initial_balance,
            holder_name=holder_name.strip(),
            transactions=[],
            new_acc=new_acc
        )
        if initial_balance > 0:
            init_txn = Transaction(
                "Deposit",
                initial_balance,
                initial_balance,
                "Account opening initial deposit"
            )
            acc.transactions.append(init_txn)

        self.b.add_account(acc)
        return True, f"Account {acc_no} generated successfully for {holder_name}!", acc_no, pin

    def add_account(self, acc_no, h_n, initial_balance=0.0):
        success, msg, _, _ = self.generate_account(h_n, initial_balance=initial_balance, custom_acc_no=acc_no)
        return msg

    def generate_or_reset_access(self, acc_no, action="new_pin", custom_pin=None):
        data = self.b.d.load_data()
        if acc_no not in data:
            return False, f"Account {acc_no} not found."

        # Clear any lockouts and failed attempts
        self.b.d.update_acc(acc_no, "failed_attempts", 0)
        self.b.d.update_acc(acc_no, "lock_until", None)

        if action == "new_pin":
            import secrets
            pin = str(custom_pin).strip() if custom_pin and str(custom_pin).strip().isdigit() and len(str(custom_pin).strip()) == 4 else f"{secrets.randbelow(9000) + 1000:04d}"
            self.b.d.update_acc(acc_no, "pin", pin)
            self.b.d.update_acc(acc_no, "new_acc", False)
            if acc_no in self.b.accounts:
                self.b.accounts[acc_no].pin = pin
                self.b.accounts[acc_no].new_acc = False
            return True, f"Access generated! New 4-digit PIN for {acc_no} is: {pin}"

        elif action == "require_setup":
            self.b.d.update_acc(acc_no, "pin", None)
            self.b.d.update_acc(acc_no, "new_acc", True)
            if acc_no in self.b.accounts:
                self.b.accounts[acc_no].pin = None
                self.b.accounts[acc_no].new_acc = True
            return True, f"Access reset for {acc_no}. The user will be required to create their PIN upon next login."

        elif action == "unlock":
            return True, f"Account {acc_no} has been unlocked successfully."

        return False, "Unknown access action."

    def remove_account(self, acc_no):
        return self.b.remove_account(acc_no)

    def list_all_accounts(self):
        return self.b.list_all_accounts()


# ----------------- CLI Loop commented out -----------------
# if __name__ == "__main__":
#     # Original interactive CLI code commented for Flask integration
#     pass
