# shopify-admin-app
=======

# Shopify COD Manager

A Flask-based MVP for managing Cash-on-Delivery (COD) orders from Shopify stores.

## Quickstart

1. Create and activate a virtual environment:
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
text2. Install dependencies:
pip install -r requirements.txt
text3. Set up environment variables:
cp .env.example .env
textEdit `.env` with your MySQL credentials and desired settings.

4. Initialize the database:
mysql -u root -p < sql/init.sql
text5. Create an admin user:
python tests/smoke.py
text6. Run the application:
flask --app app.py run
textAccess at `http://localhost:5000`.

## Production Deployment

- Use Gunicorn: `gunicorn -w 4 -b 0.0.0.0:8000 app:app`
- Set up Nginx as a reverse proxy.
- Override `FLASK_ENV=production` and `SECRET_KEY` in `.env`.
- Ensure MySQL is accessible and secure.

## Obtaining Shopify Private App Token

1. In Shopify admin, go to Apps > Develop Apps > Create App.
2. Enable required scopes: `read_orders`, `write_orders`, `read_fulfillments`, `write_fulfillments`.
3. Generate an access token and copy it.
4. Use this token in the `/connect` page along with your store URL.

## Syncing Orders

- Click "Sync Now" on the Dashboard or Orders page to fetch COD orders.
- Alternatively, send a POST request to `/orders/sync`.

## Exporting Orders

- On the Orders page, apply filters and click "Export CSV" to download filtered orders.

## Notes

- Shopify tokens are stored as-is in the database. To enable envelope encryption, use `cryptography.Fernet` to encrypt `access_token` before storing and decrypt on retrieval.