# chabrovy_perly

Simple Flask + Jinja2 website for storing and browsing funny quotes.

## Features

- Main page with quotes ordered by date (newest first)
- Filtering quotes by exact date and by text substring
- Admin area for authorized users:
  - Login/logout
  - Add quote
  - Edit quote

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Admin credentials

Default admin login is configured via environment variables:

- `ADMIN_USERNAME` (default: `admin`)
- `ADMIN_PASSWORD` (default: `change-me`)
- `SECRET_KEY` (default: `dev-secret-key`)

Example:

```bash
export ADMIN_USERNAME=your_name
export ADMIN_PASSWORD='strong-password'
export SECRET_KEY='strong-secret'
python app.py
```
