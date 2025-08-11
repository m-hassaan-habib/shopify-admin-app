from flask import Blueprint, render_template, request
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import execute_query
from datetime import datetime, timedelta
from auth import require_login

blueprint = Blueprint('analytics', __name__)

@blueprint.route('/analytics')
@require_login
def index():
    range_days = int(request.args.get('range', 30))
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=range_days)

    earnings = execute_query(
        """
        SELECT DATE(created_at_utc) AS date, SUM(total_price) AS total, currency
        FROM cod_orders
        WHERE created_at_utc >= %s AND created_at_utc <= %s
        GROUP BY DATE(created_at_utc), currency
        ORDER BY date
        """,
        (start_date, end_date),
        dictionary=True
    )

    labels = []
    values = []
    current_date = start_date
    while current_date <= end_date:
        labels.append(current_date.strftime('%Y-%m-%d'))
        total = sum(e['total'] for e in earnings if e['date'] == current_date)
        values.append(float(total))
        current_date += timedelta(days=1)

    top_tags = execute_query(
        """
        SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(tags, ',', n.digit+1), ',', -1) AS tag,
               COUNT(*) AS count,
               SUM(total_price) AS total
        FROM cod_orders
        CROSS JOIN (SELECT a.N + b.N * 10 + 1 AS digit
                    FROM (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
                          UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                         (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
                          UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b
                    ORDER BY digit) n
        WHERE created_at_utc >= %s AND created_at_utc <= %s
        AND n.digit < (LENGTH(tags) - LENGTH(REPLACE(tags, ',', '')) + 1)
        GROUP BY tag
        ORDER BY total DESC
        LIMIT 5
        """,
        (start_date, end_date),
        dictionary=True
    )

    return render_template(
        'analytics.html',
        labels=labels,
        values=values,
        range=range_days,
        top_tags=top_tags,
        active_page='analytics'
    )