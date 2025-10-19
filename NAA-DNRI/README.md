# Lab Sample Management (Prototype)

A small Flask web app prototype to manage lab samples. This initial step implements authentication and the home shell.

## Features (current)
- Login page with modern UI (Bootstrap 5)
- Hardcoded credentials: Admin / admin
- Session-based auth, logout
- Home page with placeholder sections

## Quickstart

```bash
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
set FLASK_APP=app
set FLASK_ENV=development
flask run
```

Then open `http://127.0.0.1:5000`.

## Default credentials
- Username: Admin
- Password: admin

## Structure
```
app/
  __init__.py
  routes.py
  auth.py
  templates/
    base.html
    login.html
    home.html
  static/
    styles.css
requirements.txt
README.md
```

## Next steps
- Replace hardcoded auth with a database
- Implement sections for samples, inventory, users, audit logs
# NAA-DNRI-test
