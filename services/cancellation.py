from services.shopify_client import make_shopify_request

def cancel_order(order_id, shop_url, access_token, api_version):
    payload = {"reason": "customer", "email": False, "restock": False, "refund": False}
    r, e, _ = make_shopify_request(
        "POST", shop_url, access_token, api_version,
        f"orders/{order_id}/cancel.json",
        json=payload,
        return_headers=True
    )
    if e:
        return False, str(e)
    return True, None
