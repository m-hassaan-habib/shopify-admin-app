import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Blueprint, render_template
from db import execute_query
from datetime import datetime, timedelta
from auth import require_login

blueprint = Blueprint('dashboard', __name__)

@blueprint.route('/dashboard')
@require_login
def index():
    now = datetime.utcnow()
    today = now.date()
    week_ago = now - timedelta(days=7)

    connected_store_count = execute_query("SELECT COUNT(*) FROM shopify_stores")[0][0]
    cod_today_count = execute_query(
        "SELECT COUNT(*) FROM cod_orders WHERE DATE(created_at_utc) = %s",
        (today,)
    )[0][0]

    row = execute_query(
        """
        SELECT currency, SUM(total_price) AS amount
        FROM cod_orders
        WHERE created_at_utc >= %s
        GROUP BY currency
        ORDER BY amount DESC
        LIMIT 1
        """,
        (week_ago,)
    )
    if row:
        store_currency, cod_last_7_amount = row[0][0], float(row[0][1] or 0)
    else:
        store_currency, cod_last_7_amount = 'USD', 0.0

    unfulfilled_count = execute_query(
        "SELECT COUNT(*) FROM cod_orders WHERE fulfillment_status = 'unfulfilled'"
    )[0][0]

    last_sync_at = execute_query(
        "SELECT MAX(synced_at) FROM cod_orders"
    )[0][0]

    recent_orders = execute_query(
        """
        SELECT id, name, customer_name, total_price, currency, fulfillment_status, created_at_utc
        FROM cod_orders
        ORDER BY created_at_utc DESC
        LIMIT 10
        """,
        dictionary=True
    )

    return render_template(
        'dashboard.html',
        connected_store_count=connected_store_count,
        cod_today_count=cod_today_count,
        cod_last_7_amount=cod_last_7_amount,
        store_currency=store_currency,
        unfulfilled_count=unfulfilled_count,
        last_sync_at=last_sync_at,
        recent_orders=recent_orders,
        active_page='dashboard'
    )
