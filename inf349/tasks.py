# inf349/tasks.py

from .models import Order
from .payment_service import pay_credit_card, PaymentError
from .utils import serialize_order
from .redis_client import redis_client

import json

def process_payment(order_id: int, credit_card: dict):
    print("🔥🔥🔥 process_payment appelé avec order_id =", order_id)

    try:
        order = Order.get_or_none(Order.id == order_id)
        if not order:
            print(f"[worker] ❌ Commande {order_id} introuvable.")
            return

        print(f"[worker] 💡 Commande récupérée : id={order.id}, paid={order.paid}")

        if order.paid:
            print(f"[worker] ✅ Commande {order_id} déjà payée.")
            return

        if not (order.email and order.country):
            print(f"[worker] ❌ Informations client incomplètes pour la commande {order_id}.")
            return

        amount_cents = int(round((order.total_price + order.total_price_tax) * 100)) + order.shipping_price
        print(f"[worker] 💳 Montant à facturer : {amount_cents} cents")

        try:
            payment_resp = pay_credit_card(credit_card, amount_cents)
        except PaymentError as err:
            print(f"[worker] ❌ Erreur de paiement pour la commande {order_id} : {err}")
            Order.update(
                transaction_success=False,
                transaction_amount=amount_cents,
            ).where(Order.id == order.id).execute()
            redis_client.set(f"order:{order.id}", json.dumps(serialize_order(Order.get_by_id(order.id))))
            return

        cc, tr = payment_resp["credit_card"], payment_resp["transaction"]
        print(f"[worker] ✅ Paiement accepté, transaction ID : {tr['id']}")

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

        updated = Order.get_by_id(order.id)
        print(f"[worker] 🔄 Commande mise à jour : paid={updated.paid}")
        redis_client.set(f"order:{order.id}", json.dumps(serialize_order(updated)))
        print(f"[worker] ✅ Cache Redis synchronisé pour la commande #{order.id}")

    except Exception as e:
        print("🔥🔥🔥 Une exception NON GÉRÉE est survenue dans process_payment :", e)
