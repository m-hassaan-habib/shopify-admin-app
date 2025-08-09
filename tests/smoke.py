import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import execute_insert, execute_query
from blueprints.admin import create_admin_user

def run_smoke_tests():
    existing_user = execute_query(
        "SELECT id FROM users WHERE email = %s",
        ('admin@example.com',),
        dictionary=True
    )
    if not existing_user:
        create_admin_user('admin@example.com', 'securepassword123')

    existing_store = execute_query(
        "SELECT id FROM shopify_stores WHERE shop_url = %s",
        ('test.myshopify.com',),
        dictionary=True
    )
    if existing_store:
        store_id = existing_store[0]['id']
    else:
        store_id = execute_insert(
            """
            INSERT INTO shopify_stores (shop_url, access_token, api_version, cod_tags)
            VALUES (%s, %s, %s, %s)
            """,
            ('test.myshopify.com', 'dummy_token', '2023-10', 'post office')
        )

    existing_order_1001 = execute_query(
        "SELECT id FROM cod_orders WHERE id = %s",
        (1001,),
        dictionary=True
    )
    if not existing_order_1001:
        execute_insert(
            """
            INSERT INTO cod_orders (
                id, shop_id, name, customer_name, customer_email, phone, address1, city, province, country,
                postal_code, total_price, currency, financial_status, fulfillment_status, tags,
                created_at_utc, updated_at_utc
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                1001, store_id, '#1001', 'John Doe', 'john@example.com', '1234567890', '123 Main St',
                'New York', 'NY', 'USA', '10001', 99.99, 'USD', 'pending', 'unfulfilled',
                'post office', '2023-10-01 12:00:00', '2023-10-01 12:00:00'
            )
        )

    existing_order_1002 = execute_query(
        "SELECT id FROM cod_orders WHERE id = %s",
        (1002,),
        dictionary=True
    )
    if not existing_order_1002:
        execute_insert(
            """
            INSERT INTO cod_orders (
                id, shop_id, name, customer_name, customer_email, phone, address1, city, province, country,
                postal_code, total_price, currency, financial_status, fulfillment_status, tags,
                created_at_utc, updated_at_utc
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                1002, store_id, '#1002', 'Jane Smith', 'jane@example.com', '0987654321', '456 Elm St',
                'Los Angeles', 'CA', 'USA', '90001', 149.99, 'USD', 'pending', 'unfulfilled',
                'post office', '2023-10-02 12:00:00', '2023-10-02 12:00:00'
            )
        )

    print("Smoke tests completed: admin user, store, and mock orders created or verified.")

if __name__ == '__main__':
    run_smoke_tests()