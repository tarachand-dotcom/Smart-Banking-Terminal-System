import getpass as gp
import uuid
from datetime import datetime
from abc import ABC,abstractmethod
import sys
import time
import winsound
import os
import json 
from dotenv import load_dotenv


def dot_loader(task_name, duration=5):
    print(f"\n{task_name}", end='', flush=True)
    for _ in range(duration * 2):
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(0.5)





class Data_Manager:

    def __init__(self, filename="bank_data.json"):
        # Always use the file inside the ATM project folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filename = os.path.join(base_dir, filename)

        # Create file if it does not exist
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as file:
                json.dump({}, file, indent=4)

    def load_data(self):
        try:
            with open(self.filename, "r") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {}

            return data

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

        if acc_no not in data:
            return False

        if "transactions" not in data[acc_no]:
            data[acc_no]["transactions"] = []

        data[acc_no]["transactions"].append(t.make_dict())

        self.save_data(data)

        return True

    def add_account_to_json(self, account):

        data = self.load_data()

        data[account.acc_no] = account.make_dict()

        self.save_data(data)

        return True

    def remove_account_to_json(self, acc_no):

        data = self.load_data()

        if acc_no in data:
            del data[acc_no]
            self.save_data(data)
            return True

        return False

    def make_dict(self):
        return {
            "pin": self.pin,
            "balance": self.balance,
            "holder_name": self.holder_name,
            "transactions": [
                t.make_dict() if hasattr(t, "make_dict") else t
                for t in self.transactions
            ]
        }


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
    def add_transaction(self,t_type,note="",amount=0):
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



class Account(AccountBase):

    def __init__(self,acc_no,pin=None,balance=0,holder_name="Unknown",transactions=None):
        self.acc_no=acc_no
        self.pin=pin
        self.balance=balance
        self.holder_name=holder_name
        self.transactions=transactions if transactions is not None else []
        self.data=Data_Manager()

    def check_pin(self,entered_pin):
        return self.pin==entered_pin
    
    def deposit(self,e_amount):
        if e_amount<=0:
            raise ValueError("Deposit amount must be positive.")
        self.balance=self.balance+e_amount
        new_txn=Transaction("Deposit".title(),e_amount,self.balance,"You must check your account balance to confirm before leaving our ATM...!")
        self.transactions.append(new_txn)
        self.data.add_transaction_to_json(self.acc_no,new_txn)
        self.data.update_acc(self.acc_no,"balance",self.balance)
        return

    def withdraw(self,e_amount):
        if e_amount<=0:
            raise ValueError("Withdrawal amount must be positive.")
        if e_amount>self.balance:
            raise ValueError("Insufficient balance.")
        self.balance=self.balance-e_amount
        new_txn=Transaction("Withdraw".title(),e_amount,self.balance,"You must check your account balance to confirm before leaving our ATM...!")
        self.transactions.append(new_txn)
        self.data.add_transaction_to_json(self.acc_no,new_txn)
        self.data.update_acc(self.acc_no,"balance",self.balance)
        return

    def get_balance(self):
        print(f'Your current balance is : {self.balance}')

    def add_transaction(self,t_type,note="",amount=0):
        t=Transaction(t_type,amount,self.balance,note)
        self.transactions.append(t)
        self.data.add_transaction_to_json(self.acc_no,t)
        return 
    
    def make_dict(self):
        return {"acc_no": self.acc_no,
        "pin": self.pin,
        "balance": self.balance,
        "holder_name": self.holder_name,
        "failed_attempts": 0,
        "lock_until": None,
        "transactions": self.transactions,
        "new_acc":True}

    # def __str__(self):
    #     joiner="\n\n"
    #     return (f'Account no. : {self.acc_no}\nBalance : ₹{self.balance}\nAccount holder name : {self.holder_name}\nTransactions : \n{joiner.join("   "+str(i).replace("\n","\n   ") for i in self.transactions)}')
    # def __str__(self):
    #     return (f'Account no. : {self.acc_no}\nBalance : ₹{self.balance}\nAccount holder name : {self.holder_name}\nTransactions : \n{"\n\n".join("   "+str(i).replace("\n","\n   ") for i in self.transactions)}')
    
    # Here ("   "+str(i).replace("\n","\n   ") for i in self.transactions) is a "generator"...



class Transaction:

    def __init__(self,type,amount,balance_after,note="",t=datetime.now().strftime("On %d-%m-%Y At %H:%M:%S")):
        self.type=type
        self.amount=amount
        self.balance_after=balance_after
        self.note=note
        self.transaction_id=str(uuid.uuid4())[:8]
        self.timestamp=t
        # self.timestamp=datetime.now().strftime("On %d-%m-%Y At %H:%M:%S")
    
    def make_dict(self):
        return {"type":self.type,"amount":self.amount,"balance_after":self.balance_after,"note":self.note,"time":self.timestamp}

    def __str__(self):
        return (f'[{self.timestamp}]\nTransaction type : {self.type}\nAmount ₹{self.amount} → Balance : ₹{self.balance_after} | Transaction ID:{self.transaction_id}\nNote : {self.note}')



def convert_dict_to_strOFobj(l):
    k = []
    if not l:
        return k
    for item in l:
        if isinstance(item, dict):
            t_type = item.get("type", "Transaction")
            amount = item.get("amount", 0)
            balance = item.get("balance_after", item.get("balance", 0))
            note = item.get("note", "")
            time_val = item.get("time", item.get("timestamp", datetime.now().strftime("On %d-%m-%Y At %H:%M:%S")))
            new_txn = Transaction(t_type, amount, balance, note, time_val)
            k.append(str(new_txn))
        elif isinstance(item, str):
            k.append(item)
        else:
            k.append(str(item))
    return k


class BankSystem(BankBase):

    def __init__(self, d=None):

        if d is None:
            d = Data_Manager()

        self.d = d

        data = self.d.load_data()

        self.accounts = {}

        for acc_no, acc_data in data.items():

            if "pin" not in acc_data:
                print(f"Invalid account data: {acc_no}")
                continue

            account = Account(
                acc_no,
                acc_data["pin"],
                acc_data["balance"],
                acc_data["holder_name"],
                convert_dict_to_strOFobj(
                    acc_data.get("transactions", [])
                )
            )

            self.accounts[acc_no] = account

    def add_account(self, account):

        if account.acc_no in self.accounts:
            print("Account already exists...!")
            return False

        self.accounts[account.acc_no] = account

        dot_loader("Adding Account")

        self.d.add_account_to_json(account)

        print(f"\nAccount {account.acc_no} added successfully!")

        return True

    def find_account(self, acc_no):

        return self.accounts.get(acc_no)

    def remove_account(self, acc_no):

        if acc_no in self.accounts:

            del self.accounts[acc_no]

            dot_loader("Deleting Account")

            self.d.remove_account_to_json(acc_no)

            print(f"\nAccount {acc_no} deleted successfully...!")

            return True

        print("Account not found...!")
        return False

    def list_all_accounts(self):

        print("List of all accounts")

        for acc_no, acc_obj in self.accounts.items():

            print(
                f"{acc_no} - "
                f"{acc_obj.holder_name} - "
                f"Rs. {acc_obj.balance}"
            )
        return self.accounts
            
class ATM:
    
    def __init__(self,b_,d=Data_Manager()):
        self.BankSystem=b_
        self.current_account=None
        self.data=d

    def notes(self,w):
        notes=[2000,500,200,100,50]
        d={}
        r=w
        for i in notes:
            if r!=0:
                c=r//i
                r=r%i
                d[i]=int(c)
            else:
                d[i]=0
        print(f''' ₹2000 : {d[2000]}
 ₹500 : {d[500]}
 ₹200 : {d[200]}
 ₹100 : {d[100]}
 ₹50 : {d[50]}
 Other : ₹{r}''')
        

    def login_attempt(self,acc_no):
        k=self.data.load_data()
        f_a=0
        while f_a<3:
            if k[acc_no]["lock_until"]==None or k[acc_no]["lock_until"]<=time.time():
                e_pin=gp.getpass("\nEnter Your PIN:")
                if k[acc_no]["pin"]==e_pin:
                    self.data.update_acc(acc_no,"failed_attempts",0)
                    self.data.update_acc(acc_no,"lock_until",None)
                    return e_pin
                else:
                    print("\nIncorrect PIN...!")
                    print(f'\nYou have {3-f_a-1} attemts left...!')
                    f_a=f_a+1
                    self.data.update_acc(acc_no,"failed_attempts",f_a)
            else:
                print(f'\nYour account is locked. Try again after {float(k[acc_no]["lock_until"])-time.time()} seconds...!')
                return 1
        print(f'\nToo many attempts. Please try again after 10 seconds...!')
        self.data.update_acc(acc_no,"lock_until",time.time()+10)
        return 0
        

    def authentication(self,c):
        while True:
            _e=input("\nAre you an admin? (Y/N) : ")
            e=_e.upper()
            if e.isnumeric():
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\nInvalid input...!")
                continue
            elif e=="Y":
                print("\nAccesss granted...")
                winsound.Beep(800,200)
                return 26
            elif e=='N':
                print('---------------------------------------------!')
                print('---------------------------------------------!')
                print('\nWelcome to CLI ATM...🙏')
                
                try:
                    e_acc_no=input('\nEnter Your Account No.:')








                    if self.BankSystem.find_account(e_acc_no) and self.data.load_data().get(e_acc_no, {}).get("new_acc", False) is True:
                        self.current_account=self.BankSystem.find_account(e_acc_no)
                        print("\n   You have to generate PIN first...!  \n")
                        co=True
                        while co:
                            n_pin=gp.getpass("\nEnter your PIN:")
                            if len(n_pin)!=4 or not n_pin.isdigit():
                                print("\nPIN must be exactly 4 numeric digits...!")
                            else:
                                co=False
                        c_pin=gp.getpass("\nConfirm your PIN:")
                        dot_loader("\nProcessing")
                        if n_pin==c_pin:
                            self.BankSystem.accounts[self.current_account.acc_no].pin=n_pin
                            self.data.update_acc(self.current_account.acc_no,"pin",n_pin)
                            self.data.update_acc(self.current_account.acc_no,"new_acc",False)
                            print("\nYour PIN is successfully registered...")
                            print("\nPlease login again...")
                            winsound.Beep(800,200)
                            while True:
                                k=input("\n$_$ Next Page? (Y/N):").upper()
                                if k=="Y":
                                    os.system('cls' if os.name == 'nt' else 'clear')
                                    c=0
                                    False
                                    return c
                                elif k=="N":
                                    True
                                else:
                                    print("\nInvalid input...! Please try again...!")
                                    True
                        else:
                            print("\nYour PINs are not matching...!")
                            print('\nPlease try again...!')

                        
                    else:
                        e_pin=self.login_attempt(e_acc_no)
                except KeyError:
                    print("Account not found...!")
                    while True:
                        k=input("\n$_$ Next Page? (Y/N):").upper()
                        if k=="Y":
                            os.system('cls' if os.name == 'nt' else 'clear')
                            c=0
                            False
                            return c
                        elif k=="N":
                            True
                        else:
                            print("\nInvalid input...! Please try again...!")
                            True
                # e_pin=gp.getpass("Enter Your PIN:")
                if e_pin==1:
                    c=self.clss(c)
                elif e_pin==0:
                    c=self.clss(c)
                else:
                    account=self.BankSystem.find_account(e_acc_no)
                    dot_loader("\nLogging you in")
                    if account and account.check_pin(e_pin):
                        self.current_account=account
                        print('\nLogin Successful...')
                        print("\n✅ Done ✅")
                        winsound.Beep(800, 200)
                        if self.current_account.transactions==[] and len(self.current_account.transactions)==0:
                            print("\nNo transactions...!")
                            return 1
                        elif 1<=len(self.current_account.transactions)<3:
                            print(f'\nLast {len(self.current_account.transactions)} transactions:')
                            i=len(self.current_account.transactions)
                            for txn in self.current_account.transactions[-1::-1]:
                                print('\n',i,":",end=" ")
                                print(str(txn))
                                i=i-1
                            return 1
                        else:
                            print(f'\nLast 3 transactions:')
                            i=len(self.current_account.transactions)
                            for txn in self.current_account.transactions[-1:-4:-1]:
                                print('\n',i,":",end=" ")
                                print(str(txn))
                                i=i-1
                            c=1 
                            return c
                    else:
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print('\nInvalid account no. or PIN...!!!')
                        c=0
                        return c
            else:
                os.system('cls' if os.name == 'nt' else 'clear')
                print('\nYou must enter only Y or N...!')

    
    
    def show_balance(self):
        print(f'\nYour current balance is ₹{self.current_account.balance}')

    def withdraw_cash(self):
        co=True
        while co==True:
            try:
                amount=float(input(f'\nEnter the amount to withdraw : ₹'))
                _v=input("\nAre you sure? (Y/N):")
                v=_v.upper()
                if v.isnumeric():
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\nInvalid input...!")
                elif v=='Y':
                    if amount<=0:
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print("\nInvalid amount...! Please try again...!")
                        continue
                    elif self.current_account.balance>=amount and amount>0:
                        self.current_account.withdraw(amount)
                        dot_loader(f'\nwithdrawing ₹{amount}')
                        print("\n✅ Done ✅")
                        print("\nTransaction successful...")
                        winsound.Beep(800, 200)
                        print('\nPlease collect your cash 💵')
                        self.notes(amount)
                        print(f"\nNew Balance: ₹{self.current_account.balance}")
                    else:
                        print('\n❌ Not sufficient balance...! ❌')
                    co=False
                elif v=='N':
                    print("\nPlease try to read options carefully before you select them...!")
                    co=False
                else:
                    print('\nYou must enter only Y or N...!')
            except ValueError:
                print("\nInvalid input...!")
    
    def deposit_cash(self):
        co=True
        while co==True:
            try:
                amount=float(input("\nEnter amount to deposit: ₹"))
                _v=input("\nAre you sure? (Y/N):")
                v=_v.upper()
                if v.isnumeric():
                    print("\nInvalid input...!")
                elif v=='Y':
                    if amount<=0:
                        print("\nInvalid amount...! Please try again...!")
                        continue
                    self.current_account.deposit(amount)
                    dot_loader(f'\nDepositing ₹{amount}')
                    print("\n✅ Done ✅")
                    print("\nTransaction successful...")
                    winsound.Beep(800,200)
                    print(f"\nNew Balance: ₹{self.current_account.balance}")
                    co=False
                elif v=='N':
                    print("\nPlease try to read options carefully before you select them...!")
                    co=False
                else:
                    print('\nYou must enter only Y or N...!')
            except ValueError:
                print("\nInvalid input...!")
            

    def mini_statement(self):
        if self.current_account.transactions==[]:
            print("\nNo transactions...!")
        elif 1<=len(self.current_account.transactions)<5:
                print(f'\nLast {len(self.current_account.transactions)} transactions:')
                i=len(self.current_account.transactions)
                for txn in self.current_account.transactions[-1::-1]:
                    print('\n',i,":",end=" ")
                    print(str(txn))
                    i=i-1
        else:
            print("\nLast 5 transactions:")
            i=len(self.current_account.transactions)
            for txn in self.current_account.transactions[-1:-6:-1]:
                print('\n',i,":",end=" ")
                print(txn)
                i=i-1


    def pin_change(self,k):
        _v=input("\nAre you sure? (Y/N):")
        v=_v.upper()
        if v.isnumeric():
            print("\nInvalid input...!")
        elif v=='Y':
            o_pin=gp.getpass("\nEnter Your old PIN:")
            dot_loader(f'\nMatching PIN')
            if o_pin==self.current_account.pin:
                print("\nAccount found...")
                winsound.Beep(800,200)
                print("\n✅ Done ✅")
                co=True
                while co:
                    n_pin=gp.getpass("\nEnter your new PIN:")
                    if len(n_pin)!=4 or not n_pin.isdigit():
                        print("\nPIN must be exactly 4 numeric digits...!")
                    else:
                        co=False
                c_pin=gp.getpass("\nConfirm your new PIN:")
                dot_loader("\nProcessing")
                if n_pin==c_pin:
                    self.BankSystem.accounts[self.current_account.acc_no].pin=n_pin
                    self.data.update_acc(self.current_account.acc_no,"pin",n_pin)
                    print("\nYour PIN is successfully changed...")
                    winsound.Beep(800,200)
                    k=1
                    return k
                else:
                    print("\nYour PINs are not matching...!")
                    print('\nPlease try again...!')
                    k=11
                    return k
            else:
                print("\nInvalid input...!")
                k=11
                return k
        elif v=='N':
                print("\nPlease try to read options carefully before you select them...!")
                k=11
                return k
        else:
            print('\nYou must enter Y or N...!')
            k=11
            return k

    def fast_cash(self):
        co=True
        while co==True:
            l=[500,1000,2000,5000,10000]
            for i in range(len(l)):
                print(f'\n {i+1} : ₹ {l[i]} \n')
            try:
                c=int(input('\nSelect option:'))
                a=l[c-1]
                _v=input("\nAre you sure? (Y/N): ")
                v=_v.upper()
                if v.isnumeric():
                    print("\nInvalid Input...!")
                elif v=='Y':
                        if a<=0:
                            print("\nInvalid amount...! Please try again...!")
                            return
                        elif self.current_account.balance>=a and a>0:
                            self.current_account.withdraw(a)
                            dot_loader(f'\nwithdrawing ₹{a}')
                            print("\n✅ Done ✅")
                            print("\nTransaction successful...")
                            print('\nPlease collect your cash 💵')
                            self.notes(a)
                            winsound.Beep(800,200)
                            print(f"\nNew Balance: ₹{self.current_account.balance}")
                            co=False
                        else:
                            print('\n❌ Not sufficient balance...! ❌')
                            co=False
                elif v=='N':
                    print("\nPlease try to read options carefully before you select them...!")
                    co=False
                else:
                    print("\nYou must enter Y or N...!")
            except:
                print('\nInvalid input...!')

    def all_time_txn(self):
        if self.current_account.transactions==[]:
            print("\nNo transactions...!")
        else:
            print("\nAll time transactions:")
            i=1
            for txn in self.current_account.transactions[::]:
                print('\n',i,":",end=" ")
                print(txn)
                i=i+1

    def clss(self,c):
        while True:
            k=input("\n$_$ Next Page? (Y/N):").upper()
            if k=="Y":
                os.system('cls' if os.name == 'nt' else 'clear')
                c=1
                return c
            elif k=="N":
                continue
            else:
                print("\nInvalid input...! Please try again...!")
                continue

    def main_menu(self,c):
        while c==1:
            print("\nMain Menu:")
            print("1. Balance Enquiry")
            print("2. Withdraw Cash")
            print("3. Deposit Cash")
            print('4. Mini statement')
            print('5. Pin change')
            print('6. Fast cash')
            print('7. All-time Transactions')
            print("8. Exit")

            choice=input("\nSelect your option:").strip()

            if choice=='1':
                dot_loader("\nFinding info. about your balance")
                print("\n✅ Done ✅")
                self.show_balance()
                self.current_account.add_transaction("Balance enquiry".title(),"You are provided your current balance...")
                c=self.clss(c)
                return c
            elif choice=='2':
                self.withdraw_cash()
                c=self.clss(c)
                return c
            elif choice=='3':
                self.deposit_cash()
                c=self.clss(c)
                return c
            elif choice=='4':
                self.mini_statement()
                c=self.clss(c)
                return c
            elif choice=='5':
                k=self.pin_change(0)
                if k==1:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\nYour PIN is successfully changed...")
                    print('\nPlease login again...')
                    c=self.authentication(c)
                    return c
                if k==11:
                    return c
                c=self.clss(c)
                return c
            elif choice=='6':
                self.fast_cash()
                c=self.clss(c)
                return c
            elif choice=='7':
                self.all_time_txn()
                c=self.clss(c)
                return c
            elif choice=='8':
                while True:
                    _v=input("\nAre you sure? (Y/N):")
                    v=_v.upper()
                    if v.isnumeric():
                        print("\nInvalid input...!")
                        True
                    elif v=='Y':
                        dot_loader("\nLogging you out")
                        print("\nThank you for using our ATM...")
                        while True:
                            k=input("\n$_$ Next Page? (Y/N):").upper()
                            if k=="Y":
                                os.system('cls' if os.name == 'nt' else 'clear')
                                c=0
                                False
                                return c
                            elif k=="N":
                                True
                            else:
                                print("\nInvalid input...! Please try again...!")
                                True
                    elif v=='N':
                        os.system('cls' if os.name == 'nt' else 'clear')
                        c=self.main_menu(c)
                        return c
                    else:
                        print('\nYou must enter Y or N...!')
            else:
                print("\nInvalid option selected...!\nPlease try again...!")
                c=self.clss(c)
                return c
        return c



class Admin:
    def __init__(self,admin_pin,b=None):
        self.a_pin=admin_pin
        if b is None:
            b = BankSystem()

        self.bank = b;

    def clss(self,c):
        while True:
            k=input("\n$_$ Next Page? (Y/N):").upper()
            if k=="Y":
                os.system('cls' if os.name == 'nt' else 'clear')
                c=64
                return c
            elif k=="N":
                continue
            else:
                print("\nInvalid input...! Please try again...!")
                continue
    
    def menu(self,c):
        while c==64:
            print("\nMenu:")
            print("1. Add Account")
            print("2. Remove Account")
            print("3. List All Accounts")
            print("4. Exit")

            choice=input("\nSelect your option:").strip()

            if choice=='1':
                try:
                    a_n=input("\nEnter Account no. : ")
                    if a_n in self.b.accounts:
                        print(f'\nAccount already exists...!')
                        c=self.clss(c)
                    else:
                        a_h_n=input("\nEnter Account holder name : ")
                        acc=Account(a_n,holder_name=a_h_n)
                        temp=self.b.add_account(acc)
                        if temp==True:
                            print("\n✅ Done ✅")
                            winsound.Beep(800, 200)
                            c=self.clss(c)
                        else:
                            c=self.clss(c)
                except ValueError:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\nInvalid input...!")
                    continue
                    
            elif choice=='2':
                try:
                    a_n=input("\nEnter Account no. : ")
                    temp=self.b.remove_account(a_n)
                    if temp==True:
                        print("\n✅ Done ✅")
                        winsound.Beep(800, 200)
                        c=self.clss(c)
                    else:
                        c=self.clss(c)
                except:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\nInvalid input...!")
                    continue

            elif choice=='3':
                print("\nList of all Accounts : ")
                k=self.b.d.load_data()
                for acc_no in k:
                    # l=[]
                    # for i in range(len(k[acc_no]["transactions"])):
                    #     d={x:y for x,y in k[acc_no]["transactions"][i].items()}
                    #     l.append(d)

                    # Type : {self.b.d.load_data()[acc_no]["transactions"]["type"]}
                    # Amount : {self.b.d.load_data()[acc_no]["transactions"]["amount"]}
                    # Balance after : {self.b.d.load_data()[acc_no]["transactions"]["balance_after"]}
                    # Note : {self.b.d.load_data()[acc_no]["transactions"]["note"]}
                    # Time : {self.b.d.load_data()[acc_no]["transactions"]["time"]}
                    print(f'''~~~ Account no. : {acc_no} ~~~
        Balance : {self.b.d.load_data()[acc_no]["balance"]}
        Account holder name : {self.b.d.load_data()[acc_no]["holder_name"]}''')
                    print("        Transactions: ")
                    if len(k[acc_no]["transactions"])==0:
                           print("\n                        No Transactions...")
                    else:
                        for i in range(len(k[acc_no]["transactions"])):
                            print(f'''
                    {i+1} : 
                        Type : {k[acc_no]["transactions"][i]["type"]}
                        Amount : {k[acc_no]["transactions"][i]["amount"]}
                        Balance after : {k[acc_no]["transactions"][i]["balance_after"]}
                        Note : {k[acc_no]["transactions"][i]["note"]}
                        Time : {k[acc_no]["transactions"][i]["time"]}''')
                    print(f'        New_Account? : {self.b.d.load_data()[acc_no]["new_acc"]}')
                    print("\n\n\n")
                c=self.clss(c)
                del k
            elif choice=='4':
                while True:
                    _v=input("\nAre you sure? (Y/N):")
                    v=_v.upper()
                    if v.isnumeric():
                        print("\nInvalid input...!")
                        True
                    elif v=='Y':
                        dot_loader("\nLogging you out")
                        print("\nThank you for using our ATM...")
                        while True:
                            k=input("\n$_$ Next Page? (Y/N):").upper()
                            if k=="Y":
                                os.system('cls' if os.name == 'nt' else 'clear')
                                return 0
                            elif k=="N":
                                True
                            else:
                                print("\nInvalid input...! Please try again...!")
                                True
                    elif v=='N':
                        break
                    else:
                        print('\nYou must enter Y or N...!')
            else:
                print("\nInvalid option selected...!\nPlease try again...!")
                c=self.clss(c)
            

    def authantication(self,c):
        try:
            p=int(input("\nEnter your password : "))
            dot_loader("\nAuthanticating")
            if p==self.a_pin:
                print('\nAuthantication Successful...')
                print("\n✅ Done ✅")
                winsound.Beep(800, 200)
                c=self.menu(64)
                return c
            else:
                print("\nPassword is incorrect...!")
                return 26
        except ValueError:
            print("\nInvalid input...!")
            while True:
                k=input("\n$_$ Next Page? (Y/N):").upper()
                if k=="Y":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    c=0
                    False
                    return c
                elif k=="N":
                    True
                else:
                    print("\nInvalid input...! Please try again...!")
                    True
        


# Main :


load_dotenv()

admin_pin = os.getenv("ATM_ADMIN_PIN")



if __name__ == "__main__":

    c = 0

    while c == 0:
        d = Data_Manager()
        b = BankSystem(d)
        a = ATM(b)

        c = a.authentication(c)

        if c == 26:
            while c == 26:
                ad = Admin(admin_pin)
                c = ad.authantication(c)

        elif c == 1:
            while c == 1:
                c = a.main_menu(c)

        else:
            c = 0

            del d, b, a