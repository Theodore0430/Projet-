from __future__ import annotations
from flask import Blueprint, jsonify, request, url_for
from playhouse.shortcuts import model_to_dict
from .models import Product, Order, OrderLine, db
from .utils import calculate_shipping, calculate_tax, calculate_total, error, serialize_order
from rq import Queue
from .redis_client import redis_client
from inf349.tasks import process_payment
import json

payment_queue = Queue(connection=redis_client)
shop_bp = Blueprint("shop", __name__)


@shop_bp.route("/", methods=["GET"])
def list_products():
    return jsonify({"products": [model_to_dict(p) for p in Product.select()]})


@shop_bp.route("/order", methods=["POST"])
def create_order():
    data = request.get_json(force=True)

    if "product" in data:
        data["products"] = [data.pop("product")]

    if "products" not in data or not isinstance(data["products"], list):
        error("missing-fields", "Il faut fournir une liste de produits dans 'products'.")

    total_price = 0
    shipping_total = 0
    lines = []

    for product_info in data["products"]:
        if {"id", "quantity"} - product_info.keys():
            error("missing-fields", "Chaque produit doit contenir 'id' et 'quantity'.")

        try:
            qty = int(product_info["quantity"])
            assert qty >= 1
        except (ValueError, AssertionError):
            error("invalid-quantity", "La quantité doit être un entier ≥ 1.")

        prod = Product.get_or_none(Product.id == product_info["id"])
        if not prod or not prod.in_stock:
            error("out-of-inventory", f"Le produit {product_info['id']} n'est pas en inventaire.")

        total_price += prod.price * qty
        shipping_total += calculate_shipping(prod.weight * qty)
        lines.append((prod, qty))

    with db.atomic():
        order = Order.create(
            total_price=total_price,
            total_price_tax=0.0,
            shipping_price=shipping_total,
        )
        for prod, qty in lines:
            OrderLine.create(order=order, product=prod, quantity=qty)

    resp = jsonify()
    resp.status_code = 302
    resp.headers["Location"] = url_for("shop.get_order", order_id=order.id)
    return resp


@shop_bp.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id: int):
    cached = redis_client.get(f"order:{order_id}")
    if cached:
        return jsonify(json.loads(cached)), 200

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

        tax_dollars = calculate_tax(order.total_price, ship["province"])

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

        credit = data["credit_card"]

        # 🧠 Enqueue d'abord
        payment_queue.enqueue(process_payment, order.id, credit)

        # 🕒 Puis marquer comme "en attente"
        Order.update(transaction_success=None).where(Order.id == order.id).execute()

        return "", 202

    error("missing-fields", "Aucune donnée exploitable envoyée")
