import csv
import io
import sys
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, Response, g, session, send_file
from services.shopify_sync import sync_orders
from services.fulfillment import fulfill_order
from services.cancellation import cancel_order
from services.pdfs import generate_money_order_pdf
from datetime import datetime, timedelta
from services.pdf_fill import fill_pdf_form, stamp_pdf
from services.company_profile import get_company_profile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from db import execute_insert, execute_query

from auth import require_login

blueprint = Blueprint('orders', __name__)


def _actor_email():
    u = getattr(g, "user", None)
    return (u.get("email") if isinstance(u, dict) else None) or session.get("user_email") or "system"


@blueprint.route('/orders')
@require_login
def list_orders():
    page = int(request.args.get('page', 1))
    per_page = 20
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    tag = request.args.get('tag')
    q = request.args.get('q')
    query = "SELECT * FROM cod_orders WHERE 1=1"
    params = []

    if start_date:
        query += " AND created_at_utc >= %s"
        params.append(start_date)
    if end_date:
        query += " AND created_at_utc <= %s"
        params.append(end_date)
    if status and status != 'all':
        query += " AND fulfillment_status = %s"
        params.append(status)
    if tag:
        query += " AND tags LIKE %s"
        params.append(f"%{tag}%")
    if q:
        query += " AND (name LIKE %s OR customer_name LIKE %s OR customer_email LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    query += " ORDER BY created_at_utc DESC LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])

    orders = execute_query(query, params, dictionary=True)
    total_orders = execute_query(
        "SELECT COUNT(*) AS count FROM cod_orders WHERE 1=1" + query.split("WHERE 1=1")[1].split("ORDER BY")[0],
        params[:-2]
    )[0][0]

    pagination = {
        'page': page,
        'has_prev': page > 1,
        'has_next': page * per_page < total_orders
    }
    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'tag': tag,
        'q': q
    }

    return render_template(
        'orders_list.html',
        orders=orders,
        pagination=pagination,
        filters=filters,
        active_page='orders'
    )

@blueprint.route('/orders/sync', methods=['POST'])
@require_login
def sync():
    stores = execute_query("SELECT * FROM shopify_stores", dictionary=True)
    for store in stores:
        success, error = sync_orders(
            store['id'], store['shop_url'], store['access_token'], store['api_version'], store['cod_tags']
        )
        if not success:
            flash(f"Sync failed for {store['shop_url']}: {error}", "danger")
            return redirect(url_for('orders.list_orders'))
    flash('Orders synced successfully.', 'success')
    return redirect(url_for('orders.list_orders'))


@blueprint.route('/orders/<int:order_id>/fulfill', methods=['POST'])
@require_login
def fulfill(order_id):
    order = execute_query(
        "SELECT shop_id, fulfillment_status FROM cod_orders WHERE id = %s",
        (order_id,), dictionary=True
    )[0]
    store = execute_query(
        "SELECT shop_url, access_token, api_version FROM shopify_stores WHERE id = %s",
        (order['shop_id'],), dictionary=True
    )[0]

    if order['fulfillment_status'] == 'fulfilled':
        flash('Order already fulfilled.', 'warning')
        return redirect(url_for('orders.list_orders'))

    success, message = fulfill_order(order_id, store['shop_url'], store['access_token'], store['api_version'])
    if success:
        flash('Order fulfilled successfully.', 'success')
        execute_query(
            "UPDATE cod_orders SET fulfillment_status = 'fulfilled' WHERE id = %s",
            (order_id,)
        )
        execute_insert("INSERT INTO audit_logs (actor, action, details) VALUES (%s, %s, %s)", (_actor_email(), "fulfill", f"Fulfilled order {order_id}"))

    else:
        flash(f'Fulfillment failed: {message}', 'danger')
    return redirect(url_for('orders.list_orders'))


@blueprint.route('/orders/<int:order_id>/cancel', methods=['POST'])
@require_login
def cancel(order_id):
    order = execute_query(
        "SELECT shop_id, fulfillment_status, financial_status FROM cod_orders WHERE id = %s",
        (order_id,), dictionary=True
    )
    if not order:
        flash(f'Order {order_id} not found.', 'danger')
        return redirect(url_for('orders.list_orders'))
    order = order[0]
    store = execute_query(
        "SELECT shop_url, access_token, api_version FROM shopify_stores WHERE id = %s",
        (order['shop_id'],), dictionary=True
    )
    if not store:
        flash(f'Store for order {order_id} not found.', 'danger')
        return redirect(url_for('orders.list_orders'))
    store = store[0]

    if order['financial_status'] == 'cancelled':
        flash('Order already cancelled.', 'warning')
        return redirect(url_for('orders.list_orders'))

    success, message = cancel_order(order_id, store['shop_url'], store['access_token'], store['api_version'])
    if success:
        flash('Order cancelled successfully.', 'success')
        execute_query(
            "UPDATE cod_orders SET financial_status = 'cancelled', fulfillment_status = 'cancelled' WHERE id = %s",
            (order_id,)
        )
        execute_insert("INSERT INTO audit_logs (actor, action, details) VALUES (%s, %s, %s)", (_actor_email(), "cancel", f"Cancelled order {order_id}"))

    else:
        flash(f'Cancellation failed: {message}', 'danger')
    return redirect(url_for('orders.list_orders'))


@blueprint.route('/orders/<int:order_id>/pdf')
@require_login
def generate_pdf(order_id):
    order = execute_query(
        """
        SELECT o.*, s.shop_url
        FROM cod_orders o
        JOIN shopify_stores s ON o.shop_id = s.id
        WHERE o.id = %s
        """,
        (order_id,), dictionary=True
    )[0]
    pdf_path = generate_money_order_pdf(order)
    execute_insert(
        "INSERT INTO money_order_pdfs (order_id, file_path) VALUES (%s, %s)",
        (order_id, pdf_path)
    )
    execute_insert("INSERT INTO audit_logs (actor, action, details) VALUES (%s, %s, %s)", (_actor_email(), "pdf", f"Generated PDF for order {order_id}"))

    return send_file(pdf_path, as_attachment=True, download_name=f"money_order_{order['name']}.pdf")

@blueprint.route('/orders/export')
@require_login
def export_csv():
    query = "SELECT * FROM cod_orders WHERE 1=1"
    params = []
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    tag = request.args.get('tag')
    q = request.args.get('q')

    if start_date:
        query += " AND created_at_utc >= %s"
        params.append(start_date)
    if end_date:
        query += " AND created_at_utc <= %s"
        params.append(end_date)
    if status and status != 'all':
        query += " AND fulfillment_status = %s"
        params.append(status)
    if tag:
        query += " AND tags LIKE %s"
        params.append(f"%{tag}%")
    if q:
        query += " AND (name LIKE %s OR customer_name LIKE %s OR customer_email LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    orders = execute_query(query, params, dictionary=True)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'id', 'name', 'customer_name', 'customer_email', 'phone', 'address1',
        'address2', 'city', 'province', 'country', 'postal_code', 'total_price',
        'currency', 'financial_status', 'fulfillment_status', 'tags', 'created_at_utc'
    ])
    writer.writeheader()
    for order in orders:
        writer.writerow(order)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=cod_orders.csv'}
    )


def _active_doc(doc_type):
    row = execute_query(
        "SELECT id, file_path, field_map_json, coordinate_map_json, fill_mode, font_name FROM shop_documents WHERE doc_type=%s AND is_active=1 ORDER BY uploaded_at DESC LIMIT 1",
        (doc_type,), dictionary=True
    )
    return row[0] if row else None


@blueprint.route('/orders/<int:order_id>/pdf/front')
@require_login
def pdf_front(order_id):
    order = execute_query("SELECT o.*, s.shop_url FROM cod_orders o JOIN shopify_stores s ON o.shop_id=s.id WHERE o.id=%s", (order_id,), dictionary=True)[0]
    profile = get_company_profile()
    data = {"order": order, "profile": profile}
    doc = _active_doc('money_order_front')
    if not doc:
        return ('Not configured', 404)
    if doc['fill_mode'] == 'stamp':
        buf = stamp_pdf(doc['file_path'], doc['coordinate_map_json'], data, doc['font_name'])
    else:
        merged = {**order, **{f"profile_{k}": v for k, v in profile.items()}}
        buf = fill_pdf_form(doc['file_path'], doc['field_map_json'], merged)
    return send_file(buf, as_attachment=True, download_name=f"money_order_front_{order['name']}.pdf", mimetype='application/pdf')


@blueprint.route('/orders/<int:order_id>/pdf/back')
@require_login
def pdf_back(order_id):
    doc = _active_doc('money_order_back')
    if not doc:
        return ('Not configured', 404)
    return send_file(doc['file_path'], as_attachment=True, download_name=f"money_order_back_{order_id}.pdf", mimetype='application/pdf')


@blueprint.route('/orders/<int:order_id>/pdf/label')
@require_login
def pdf_label(order_id):
    order = execute_query("SELECT o.*, s.shop_url FROM cod_orders o JOIN shopify_stores s ON o.shop_id=s.id WHERE o.id=%s", (order_id,), dictionary=True)[0]
    profile = get_company_profile()
    data = {"order": order, "profile": profile}
    doc = _active_doc('label')
    if not doc:
        return ('Not configured', 404)
    if doc['fill_mode'] == 'stamp':
        buf = stamp_pdf(doc['file_path'], doc['coordinate_map_json'], data, doc['font_name'])
    else:
        merged = {**order, **{f"profile_{k}": v for k, v in profile.items()}}
        buf = fill_pdf_form(doc['file_path'], doc['field_map_json'], merged)
    return send_file(buf, as_attachment=True, download_name=f"label_{order['name']}.pdf", mimetype='application/pdf')
