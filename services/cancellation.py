from services.shopify_client import make_shopify_request

def cancel_order(order_id, shop_url, access_token, api_version):
    response, error = make_shopify_request(
        'POST', shop_url, access_token, api_version, f"orders/{order_id}/cancel.json"
    )
    return response is not None, error