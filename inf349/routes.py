from __future__ import annotations
from flask import Blueprint, jsonify, request, url_for
from playhouse.shortcuts import model_to_dict
from .models import Product, Order, OrderLine, db
from .utils import calculate_shipping, calculate_tax, calculate_total, error



shop_bp = Blueprint("shop", __name__)



@shop_bp.route("/", methods=["GET"])
def list_products():
    """Retourne la liste complète des produits."""
    return jsonify({"products": [model_to_dict(p) for p in Product.select()]})

@shop_bp.route("/order", methods=["POST"])
def create_order():
    data = request.get_json(force=True)


    if list(data.keys()) != ["product"]:
        error("missing-fields", "Une commande ne peut contenir qu’un seul produit")

    product_info = data["product"]

    if {"id", "quantity"} - product_info.keys():
        error("missing-fields", "L'objet 'product' doit contenir 'id' et 'quantity'")

    try:
        qty = int(product_info["quantity"])
        assert qty >= 1
    except (ValueError, AssertionError):
        error("missing-fields", "La quantité doit être un entier ≥ 1")

    prod = Product.get_or_none(Product.id == product_info["id"]) # produit existant ou produit en stocks
    if not prod or not prod.in_stock:
        error("out-of-inventory", "Le produit demandé n'est pas en inventaire")

    
    total_dollars  = calculate_total(prod.price, qty)         
    shipping_cents = calculate_shipping(prod.weight * qty)   

    with db.atomic():
        order = Order.create(
            total_price=total_dollars,
            total_price_tax=0.0,             
            shipping_price=shipping_cents,
        )
        OrderLine.create(order=order, product=prod, quantity=qty)

    resp = jsonify()
    resp.status_code = 302
    resp.headers["Location"] = url_for("shop.get_order", order_id=order.id)
    return resp

@shop_bp.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id: int):
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Commande introuvable"}}}), 404
    return jsonify({"order": serialize_order(order)})




@shop_bp.route("/orders", methods=["GET"])
def list_orders():
    return jsonify({"orders": [serialize_order(o) for o in Order.select()]})

@shop_bp.route("/order/<int:order_id>", methods=["PUT"])
def update_order(order_id: int):
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Commande introuvable"}}}), 404

    data = request.get_json(force=True)

    if "order" in data and "credit_card" in data:
        error("invalid-fields", "Ne pas fournir 'credit_card' en même temps que 'order'")


    if "order" in data:
        info = data["order"]
        if not {"email", "shipping_information"}.issubset(info):
            error("missing-fields", "Il manque un ou plusieurs champs obligatoires")

        ship = info["shipping_information"]
        if {"country", "address", "postal_code", "city", "province"} - ship.keys():
            error("missing-fields", "Il manque un ou plusieurs champs obligatoires")

        tax_dollars = calculate_tax(order.total_price, ship["province"])  # taxe seule

        Order.update(
            email=info["email"],
            country=ship["country"],
            address=ship["address"],
            postal_code=ship["postal_code"],
            city=ship["city"],
            province=ship["province"],
            total_price_tax=tax_dollars,
        ).where(Order.id == order.id).execute()

        return jsonify({"order": serialize_order(Order.get_by_id(order.id))})

    if "credit_card" in data:
        if order.paid:
            error("already-paid", "La commande a déjà été payée.")
            
        if not order.email:
            error("missing-fields", "L’adresse courriel est obligatoire avant le paiement.")

        required_ship_fields = [order.country, order.address, order.postal_code, order.city, order.province]
        if not all(required_ship_fields):
            error("missing-fields", "Les informations d’expédition sont obligatoires avant le paiement.")

        if not (order.email and order.country):
            error("missing-fields", "Les informations client sont nécessaires avant le paiement")

        credit = data["credit_card"]
        amount_cents = int(round((order.total_price + order.total_price_tax) * 100)) + order.shipping_price

        from .payment_service import pay_credit_card, PaymentError
        try:
            payment_resp = pay_credit_card(credit, amount_cents)
        except PaymentError as err:
            return jsonify(err.args[0]), 422

        cc, tr = payment_resp["credit_card"], payment_resp["transaction"]

        Order.update(
            paid=True,
            credit_card_first=cc["first_digits"],
            credit_card_last=cc["last_digits"],
            credit_card_name=cc["name"],
            credit_exp_month=cc["expiration_month"],
            credit_exp_year=cc["expiration_year"],
            transaction_id=tr["id"],
            transaction_success=tr["success"],
            transaction_amount=tr["amount_charged"],
        ).where(Order.id == order.id).execute()

        return jsonify({"order": serialize_order(Order.get_by_id(order.id))})

    error("missing-fields", "Aucune donnée exploitable envoyée")





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
