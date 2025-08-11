from db import execute_upsert
from services.shopify_client import make_shopify_request
from datetime import datetime, timedelta, timezone
import re
from urllib.parse import urlencode

IGNORE_TAGS = {"⚠ subscription required"}

def _as_utc(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts or ""

def _tags_csv(raw):
    if isinstance(raw, str):
        tags = [t.strip() for t in raw.split(",") if t.strip()]
    else:
        tags = [str(t).strip() for t in (raw or []) if str(t).strip()]
    tags = [t for t in tags if t.lower() not in IGNORE_TAGS]
    return ",".join(tags)

def _is_cod(order, cod_tags_set):
    pg = {x.strip().lower() for x in order.get("payment_gateway_names", [])}
    if any(("cash on delivery" in x) or (x == "cod") for x in pg):
        return True
    tags = {t.strip().lower() for t in (order.get("tags", "") or "").split(",") if t.strip()}
    return bool(tags & cod_tags_set)

def _fetch(shop_url, access_token, api_version, params):
    qs = urlencode(params)
    url = f"orders.json?{qs}"
    return make_shopify_request("GET", shop_url, access_token, api_version, url, return_headers=True)

def sync_orders(store_id, shop_url, access_token, api_version, cod_tags):
    cod_tag_set = {t.strip().lower() for t in (cod_tags or "").split(",") if t.strip()} - IGNORE_TAGS
    days = 30
    since_iso = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[SYNC] Starting sync for store {store_id}, COD tags: {sorted(cod_tag_set) or ['<gateway only>']}")

    base_params = {"limit": 50}
    trial_params = [
        {"updated_at_min": since_iso},
        {"created_at_min": since_iso},
        {}
    ]
    headers = {}
    response = None
    error = None

    for extra in trial_params:
        params = {**base_params, **extra}
        response, error, headers = _fetch(shop_url, access_token, api_version, params)
        if not error:
            break
        if "status" in params:
            params.pop("status", None)
    if error:
        print(f"[SYNC] API error: {error}")
        return False, error

    processed_count = 0
    skipped_count = 0
    orders = response.get("orders", [])
    while True:
        if not orders:
            print("[SYNC] No more orders found.")
            break

        for order in orders:
            if not _is_cod(order, cod_tag_set):
                skipped_count += 1
                continue

            customer = order.get("customer", {}) or {}
            shipping_address = order.get("shipping_address", {}) or {}

            execute_upsert(
                """
                INSERT INTO cod_orders (
                    id, shop_id, name, customer_name, customer_email, phone,
                    address1, address2, city, province, country, postal_code,
                    total_price, currency, financial_status, fulfillment_status,
                    tags, created_at_utc, updated_at_utc
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    customer_name = VALUES(customer_name),
                    customer_email = VALUES(customer_email),
                    phone = VALUES(phone),
                    address1 = VALUES(address1),
                    address2 = VALUES(address2),
                    city = VALUES(city),
                    province = VALUES(province),
                    country = VALUES(country),
                    postal_code = VALUES(postal_code),
                    total_price = VALUES(total_price),
                    currency = VALUES(currency),
                    financial_status = VALUES(financial_status),
                    fulfillment_status = VALUES(fulfillment_status),
                    tags = VALUES(tags),
                    updated_at_utc = VALUES(updated_at_utc)
                """,
                (
                    int(order["id"]),
                    int(store_id),
                    order.get("name"),
                    f"{customer.get('first_name','') or ''} {customer.get('last_name','') or ''}".strip(),
                    customer.get("email"),
                    shipping_address.get("phone"),
                    shipping_address.get("address1"),
                    shipping_address.get("address2"),
                    shipping_address.get("city"),
                    shipping_address.get("province"),
                    shipping_address.get("country"),
                    shipping_address.get("zip"),
                    float(order.get("total_price") or 0),
                    order.get("currency"),
                    order.get("financial_status"),
                    order.get("fulfillment_status") or "unfulfilled",
                    _tags_csv(order.get("tags", "")),
                    _as_utc(order.get("created_at") or ""),
                    _as_utc(order.get("updated_at") or "")
                )
            )
            processed_count += 1

        link_header = headers.get("Link", "")
        match = re.search(r'<[^>]*page_info=([^&>]+)[^>]*>; rel="next"', link_header)
        if not match:
            break
        page_info = match.group(1)
        response, error, headers = _fetch(shop_url, access_token, api_version, {"limit": 50, "page_info": page_info})
        if error:
            print(f"[SYNC] API error: {error}")
            return False, error
        orders = response.get("orders", [])

    print(f"[SYNC] Finished. Processed: {processed_count}, Skipped: {skipped_count}")
    return True, None
