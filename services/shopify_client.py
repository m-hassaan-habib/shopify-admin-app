import requests
import time
from urllib.parse import urljoin
import json as _json


def make_shopify_request(method, shop_url, access_token, api_version, path_or_query, return_headers=False, json=None, data=None, headers=None):
    base = f"https://{shop_url}/admin/api/{api_version}/"
    url = base + path_or_query
    h = {"X-Shopify-Access-Token": access_token}
    if headers:
        h.update(headers)
    kwargs = {"headers": h}
    if json is not None:
        h.setdefault("Content-Type", "application/json")
        kwargs["data"] = json if isinstance(json, str) else _json.dumps(json)
    elif data is not None:
        kwargs["data"] = data
    resp = requests.request(method, url, **kwargs)
    try:
        payload = resp.json()
    except Exception:
        payload = {}
    if not resp.ok:
        err_detail = payload.get("errors") if isinstance(payload, dict) else None
        err = f"{resp.status_code} {resp.reason}" + (f": {err_detail}" if err_detail else "")
        return None, err, resp.headers if return_headers else None
    return payload, None, resp.headers if return_headers else None




def test_shopify_connection(shop_url, access_token, api_version):
    response, error = make_shopify_request('GET', shop_url, access_token, api_version, 'shop.json')
    return response is not None