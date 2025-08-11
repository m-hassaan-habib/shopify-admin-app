import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import execute_query, execute_insert
from services.shopify_client import test_shopify_connection
from auth import require_login
from services.shopify_test import test_store


blueprint = Blueprint('connect', __name__)

@require_login
@blueprint.route('/connect', methods=['GET', 'POST'])
def manage_store():
    connected = False
    connected_shop_url = None
    current_cod_tags = None

    if request.method == 'POST':
        shop_url = request.form.get('shop_url')
        access_token = request.form.get('access_token')
        cod_tags = request.form.get('cod_tags', 'post office')
        api_version = request.form.get('api_version', '2023-10')

        if test_shopify_connection(shop_url, access_token, api_version):
            execute_insert(
                """
                INSERT INTO shopify_stores (shop_url, access_token, api_version, cod_tags)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    access_token = VALUES(access_token),
                    api_version = VALUES(api_version),
                    cod_tags = VALUES(cod_tags)
                """,
                (shop_url, access_token, api_version, cod_tags)
            )
            flash('Store connected successfully.', 'success')
            return redirect(url_for('connect.manage_store'))
        flash('Failed to connect to Shopify store. Check credentials.', 'danger')

    if request.args.get('test'):
        stores = execute_query("SELECT * FROM shopify_stores", dictionary=True)
        if stores:
            store = stores[0]
            if test_shopify_connection(store['shop_url'], store['access_token'], store['api_version']):
                flash('Connection test passed.', 'success')
            else:
                flash('Connection test failed.', 'danger')

    stores = execute_query("SELECT * FROM shopify_stores LIMIT 1", dictionary=True)
    if stores:
        connected = True
        connected_shop_url = stores[0]['shop_url']
        current_cod_tags = stores[0]['cod_tags']

    return render_template(
        'connect.html',
        connected=connected,
        connected_shop_url=connected_shop_url,
        current_cod_tags=current_cod_tags
    )


@blueprint.route("/connect/retest", methods=["POST"])
@require_login
def retest_connection():
    row = execute_query(
        "SELECT shop_url, access_token, api_version FROM shopify_stores ORDER BY id DESC LIMIT 1",
        dictionary=True
    )
    if not row:
        flash("No store configured.", "danger")
        return redirect(url_for("connect.manage_store"))

    store = row[0]
    ok, msg = test_store(store["shop_url"], store["access_token"], store["api_version"])
    if ok:
        flash("Connection verified.", "success")
    else:
        flash(f"Connection failed: {msg}", "danger")
    return redirect(url_for("connect.manage_store"))


