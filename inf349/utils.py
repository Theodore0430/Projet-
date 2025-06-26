from flask import abort, jsonify
from .models import Order, Product


TAX_RATES = {"QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14} # calculs des taxes en fonction de la zone 

def calculate_shipping(weight_total):
    if weight_total < 500:
        return 500   # 5 $
    if weight_total < 2000:
        return 1000  # 10 $
    return 2500      # 25 $

def calculate_total(product_price, qty):
    return product_price * qty

def calculate_tax(total, province):
    return total * TAX_RATES.get(province, 0)



def error(code, name, http=422):
    resp = jsonify({"errors": { "order" if code in ("missing-fields","out-of-inventory",
                                                    "already-paid") else "product":
                                 {"code": code, "name": name}}})
    resp.status_code = http
    abort(resp)


def _cents_to_dollars(cents: int | None) -> float:
    return round(cents / 100, 2) if cents is not None else 0.0

def serialize_order(order: Order) -> dict:
    return {
        "id": order.id,
        "total_price": float(order.total_price),
        "total_price_tax": float(order.total_price_tax),
        "email": order.email,
        "shipping_information": (
            {
                "country": order.country,
                "address": order.address,
                "postal_code": order.postal_code,
                "city": order.city,
                "province": order.province,
            }
            if order.country else {}
        ),
        "credit_card": (
            {
                "name": order.credit_card_name,
                "first_digits": order.credit_card_first,
                "last_digits": order.credit_card_last,
                "expiration_year": order.credit_exp_year,
                "expiration_month": order.credit_exp_month,
            } if order.credit_card_first else {}
        ),
        "paid": order.paid,
        "transaction": (
            {
                "id": order.transaction_id,
                "success": order.transaction_success,
                "amount_charged": _cents_to_dollars(order.transaction_amount),
            } if order.transaction_id else {}
        ),
        "product": {
            "id": order.lines[0].product.id,
            "quantity": order.lines[0].quantity,
        },
        "shipping_price": _cents_to_dollars(order.shipping_price),
    }
