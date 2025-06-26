import requests
from .models import Product, db
from config import config

def strip_null_bytes(s):
    """Supprime les caractères NUL (\x00) interdits par PostgreSQL."""
    if isinstance(s, str):
        return s.replace('\x00', '')
    return s

def fetch_and_cache_products():
    """Télécharge les produits distants et les insère dans la base (1 fois au lancement)."""
    r = requests.get(config.REMOTE_PRODUCTS_URL)
    r.raise_for_status()
    products = r.json()["products"]

    allowed_fields = {field.name for field in Product._meta.sorted_fields}

    with db.atomic():
        for p in products:
            clean_p = {k: strip_null_bytes(v) for k, v in p.items() if k in allowed_fields}

            Product.insert(**clean_p).on_conflict(
                conflict_target=[Product.id],
                update={
                    Product.name: clean_p["name"],
                    Product.description: clean_p["description"],
                    Product.price: clean_p["price"],
                    Product.weight: clean_p["weight"],
                    Product.in_stock: clean_p["in_stock"],
                    Product.image: clean_p["image"],
                }
            ).execute()

