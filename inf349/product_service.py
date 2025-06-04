import requests
from .models import Product, db
from config import config



def fetch_and_cache_products():
    """Télécharge les produits distants et les insère dans la base (1 fois au lancement)."""
    r = requests.get(config.REMOTE_PRODUCTS_URL)
    r.raise_for_status()
    products = r.json()["products"]

    allowed_fields = {field.name for field in Product._meta.sorted_fields}

    with db.atomic():
        for p in products:
            clean_p = {k: v for k, v in p.items() if k in allowed_fields}
            Product.insert(**clean_p).on_conflict_replace().execute()
