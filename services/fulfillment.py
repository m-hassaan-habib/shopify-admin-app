from services.shopify_client import make_shopify_request
from db import execute_query

def fulfill_order(order_id, shop_url, access_token, api_version):
    r, e, _ = make_shopify_request(
        "GET", shop_url, access_token, api_version,
        f"orders/{order_id}/fulfillment_orders.json", return_headers=True
    )
    if e:
        return False, str(e)
    fos = r.get("fulfillment_orders", [])
    if not fos:
        return False, "No fulfillment orders"
    target = next((x for x in fos if x.get("status") in {"open", "in_progress", "scheduled"}), fos[0])
    payload = {
        "fulfillment": {
            "line_items_by_fulfillment_order": [
                {"fulfillment_order_id": target["id"]}
            ]
        }
    }
    r2, e2, _ = make_shopify_request(
        "POST", shop_url, access_token, api_version,
        "fulfillments.json", json=payload, return_headers=True
    )
    if e2:
        return False, str(e2)
    return True, None



def fulfill_order_legacy(order_id, shop_url, access_token, api_version):
    order = execute_query(
        "SELECT shop_id FROM cod_orders WHERE id = %s",
        (order_id,), dictionary=True
    )
    if not order:
        return False, f"Order {order_id} not found."
    order = order[0]
    store = execute_query(
        "SELECT shop_url FROM shopify_stores WHERE id = %s",
        (order['shop_id'],), dictionary=True
    )
    if not store:
        return False, f"Store for order {order_id} not found."
    store = store[0]

    location_id = get_default_location_id(shop_url, access_token, api_version)
    if not location_id:
        return False, "Failed to retrieve location ID for fulfillment."

    data = {
        'fulfillment': {
            'location_id': location_id,
            'notify_customer': False
        }
    }
    response, error = make_shopify_request(
        'POST', shop_url, access_token, api_version, f"orders/{order_id}/fulfillments.json", data
    )
    if error:
        if '401' in str(error):
            return False, "Unauthorized: Invalid or missing Shopify access token. Please reconnect the store."
        return False, f"Legacy fulfillment failed: {error}"
    return response is not None, None


def get_default_location_id(shop_url, access_token, api_version):
    response, error = make_shopify_request(
        'GET', shop_url, access_token, api_version, 'locations.json'
    )
    if error:
        if '401' in str(error):
            return None, "Unauthorized: Invalid or missing Shopify access token. Please reconnect the store."
        return None
    if response and response.get('locations'):
        return response['locations'][0]['id']
    return None