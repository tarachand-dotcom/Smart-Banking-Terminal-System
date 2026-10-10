# ATM Banking System

A Flask-based ATM and banking management web application that allows users to create or access accounts, deposit and withdraw funds, view transaction history, change PINs, and manage account access from an admin panel.

## Features

- User login and PIN authentication
- Account creation and PIN generation flow
- Deposit and withdrawal transactions
- Balance checking
- Mini statement / recent transaction history
- PIN change functionality
- Admin login and dashboard
- Add, remove, and list accounts
- Generate/reset user access credentials
- Data persistence through JSON storage

## Tech Stack

- Python
- Flask
- HTML
- CSS
- JSON for data storage

## Project Structure

```text
ATM/
├── app.py                  # Main Flask app entry point
├── main.py                 # Alternate Flask app version
├── Backend.py              # Core backend logic
├── Backend1.py             # Additional backend logic
├── Web_backend.py          # Web service/backend integration
├── bank_data.json          # Stored account data
├── static/
│   └── style.css
├── templates/
│   ├── admin_dashboard.html
│   ├── admin_generate_access.html
│   ├── admin_login.html
│   ├── atm_interface.html
│   ├── change_pin_page.html
│   ├── deposit_page.html
│   ├── enter_pin.html
│   ├── generate_pin.html
│   ├── home.html
│   ├── list_all_accounts.html
│   ├── mini_statement.html
│   ├── remove_account.html
│   ├── user_dashboard.html
│   ├── user_dashboard_full_transactions.html
│   ├── user_login.html
│   └── withdraw_page.html
└── README.md
```

## Getting Started

### 1. Clone or open the project

Navigate to the project folder:

```bash
cd ATM
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install flask
```

### 4. Run the app

Start the main application:

```bash
python app.py
```

The application will run locally at:

```text
http://127.0.0.1:5000
```

## Default Admin Access

The main app is configured with a default admin PIN:

```text
1212
```

You can change this in `app.py` if needed.

## Notes

- Account data is stored in `bank_data.json`.
- The project includes multiple backend files, but `app.py` is the primary app to run for the full web interface.
- If you want to use the alternate version, you can also run:

```bash
python main.py
```

## License

This project is intended for educational and learning purposes.
