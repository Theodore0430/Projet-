from inf349.redis_client import redis_client
from rq import Queue
from inf349.tasks import process_payment

q = Queue(connection=redis_client)
q.enqueue(process_payment, 1, {
    "name": "Test User",
    "first_digits": "4242",
    "last_digits": "4242",
    "expiration_month": 12,
    "expiration_year": 2030
})
print("✅ Tâche de paiement mise en file pour la commande #1")
