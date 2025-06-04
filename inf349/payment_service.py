from __future__ import annotations
import requests
from typing import Any, Dict



PAY_ENDPOINT = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"

class PaymentError(Exception): #  Exception si probleme carte de crédit
    """Erreur levée si l’API distante refuse la carte ou répond 4xx/5xx."""
    

def pay_credit_card(card: Dict[str, Any], amount_cents: int) -> Dict[str, Any]:
    payload = {
        "credit_card": card,
        "amount_charged": amount_cents,
    }
    try:
        resp = requests.post(PAY_ENDPOINT, json=payload, timeout=10)
    except requests.RequestException as exc:
        raise PaymentError(
            {"errors": {"network": str(exc)}}
        ) from exc
    if resp.status_code == 200:
        return resp.json()
    try:
        error_json = resp.json()
    except ValueError:
        error_json = {
            "errors": {
                "payment": {
                    "code": "invalid-response",
                    "name": "Réponse inattendue du service de paiement",
                }
            }
        }
    raise PaymentError(error_json)
