from __future__ import annotations

import datetime
import hashlib
import hmac
import json

from app.infra.clients.http_client import HttpClient
from app.infra.config import load_config
from app.infra.logger import setup_logging
from app.infra.secrets import get_secret


def search_offers(keyword: str) -> list[dict]:
    access_key = _get_secret_safe("amazon_access_key")
    secret_key = _get_secret_safe("amazon_secret_key")
    partner_tag = _get_secret_safe("amazon_partner_tag")
    if not access_key or not secret_key or not partner_tag or not keyword:
        return []

    config = load_config()
    host, region = _amazon_host_region(config.amazon_locale)
    service = "ProductAdvertisingAPI"
    endpoint = f"https://{host}/paapi5/searchitems"

    payload = {
        "Keywords": keyword,
        "PartnerTag": partner_tag,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.co.jp",
        "Resources": [
            "ItemInfo.Title",
            "Offers.Listings.Price",
        ],
        "SearchIndex": "All",
        "ItemCount": 10,
    }

    headers = _sign(
        access_key=access_key,
        secret_key=secret_key,
        host=host,
        region=region,
        service=service,
        amz_target="com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        payload=payload,
    )

    client = HttpClient(min_interval=1.0)
    try:
        response = client.post(endpoint, json=payload, headers=headers)
        data = response.json()
        items = data.get("SearchResult", {}).get("Items", []) or []
        offers = []
        for item in items:
            title = (
                item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue")
            )
            listing = (
                item.get("Offers", {})
                .get("Listings", [{}])[0]
                .get("Price", {})
            )
            price = listing.get("Amount")
            offers.append(
                {
                    "title": title,
                    "price": price,
                    "shipping": None,
                    "stock_status": None,
                    "url": item.get("DetailPageURL"),
                    "confidence": None,
                    "raw_text": None,
                }
            )
        return offers
    finally:
        client.close()


def _sign(
    *,
    access_key: str,
    secret_key: str,
    host: str,
    region: str,
    service: str,
    amz_target: str,
    payload: dict,
) -> dict[str, str]:
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    canonical_uri = "/paapi5/searchitems"
    canonical_querystring = ""
    canonical_headers = (
        f"content-encoding:amz-1.0\n"
        f"content-type:application/json; charset=utf-8\n"
        f"host:{host}\n"
        f"x-amz-date:{amz_date}\n"
        f"x-amz-target:{amz_target}\n"
    )
    signed_headers = "content-encoding;content-type;host;x-amz-date;x-amz-target"
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    canonical_request = (
        "POST\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    signing_key = _get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    authorization_header = (
        f"{algorithm} "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    return {
        "Content-Encoding": "amz-1.0",
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-Amz-Date": amz_date,
        "X-Amz-Target": amz_target,
        "Authorization": authorization_header,
    }


def _get_signature_key(
    key: str, date_stamp: str, region_name: str, service_name: str
) -> bytes:
    k_date = _sign_hmac(("AWS4" + key).encode("utf-8"), date_stamp)
    k_region = _sign_hmac(k_date, region_name)
    k_service = _sign_hmac(k_region, service_name)
    k_signing = _sign_hmac(k_service, "aws4_request")
    return k_signing


def _sign_hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _amazon_host_region(locale: str) -> tuple[str, str]:
    locale = (locale or "JP").upper()
    if locale == "JP":
        return "webservices.amazon.co.jp", "us-west-2"
    if locale == "US":
        return "webservices.amazon.com", "us-east-1"
    return "webservices.amazon.co.jp", "us-west-2"


def _get_secret_safe(key: str) -> str | None:
    try:
        return get_secret(key)
    except RuntimeError:
        setup_logging().warning("keyring unavailable for %s", key)
        return None
