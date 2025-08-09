from services.shopify_client import make_shopify_request

REQUIRED_SCOPES = {"read_orders", "write_orders", "read_fulfillments", "write_fulfillments"}

def test_store(shop_url, access_token, api_version):
    # Try to hit the basic shop info endpoint
    shop_resp, err = make_shopify_request(
        "GET", shop_url, access_token, api_version, "shop.json"
    )
    if err:
        if "401" in str(err):
            return False, "Unauthorized: Invalid or missing token."
        if "403" in str(err):
            return False, "Forbidden: Token does not have required permissions."
        return False, f"API error: {err}"

    if not shop_resp.get("shop"):
        return False, "Invalid response from Shopify."
    return True, None

