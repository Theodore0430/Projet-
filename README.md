Projet de session réaliser par LUCAS SANTIAGO et THÉODORE LEFEBVRE
# INF-349 – Application de commande en ligne (Première remise)


## 1. Installation rapide

```bash
git clone <repo> myshop
cd myshop
python -m venv venv
source venv/bin/activate   # (Windows : venv\Scripts\activate)
pip install -r requirements.txt
FLASK_APP=inf349:create_app flask init-db      # crée shop.db + récupère les produits


Pour lancer l'application 

FLASK_DEBUG=1 FLASK_APP=inf349:create_app flask run
L’API écoute sur http://127.0.0.1:5000


Arborescence du projet 

PROJET /
├── README.md
├── requirements.txt
├── config.py
├── run.py
├── inf349/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── utils.py
│   ├── product_service.py
│   └── payment_service.py
└── tests/
    ├── conftest.py
    └── test_api.py

Méthode	URL	Rôle
GET	/	Liste JSON de tous les produits
POST	/order	Création d’une commande (un seul produit)
GET	/order/<id>	Détails d’une commande
PUT	/order/<id>	• Ajoute e-mail & adresse ou • Effectue le paiement par carte


Codes d’erreur normalisés
HTTP	errors.*.code	Signification
404	not-found	Ressource inexistante
422	missing-fields	Champs obligatoires absents
422	out-of-inventory	Produit hors stock
422	already-paid	Paiement déjà effectué
422	card-declined / incorrect-number	Réponses du service de paiement




5. Exemples curl

Ajoute l’option -i pour afficher en-têtes + corps.
A. Créer une commande
curl -X POST http://127.0.0.1:5000/order \
  -H "Content-Type: application/json" \
  -d '{"product":{"id":1,"quantity":2}}' -i
# → HTTP 302 Found (Location : /order/1)


B. Ajouter e-mail + adresse
curl -X PUT http://127.0.0.1:5000/order/1 \
  -H "Content-Type: application/json" \
  -d '{
        "order":{
          "email":"test@example.com",
          "shipping_information":{
            "country":"Canada",
            "address":"123 Rue Principale",
            "postal_code":"G1X1X1",
            "city":"Québec",
            "province":"QC"
          }
        }
      }' -i

      C. Paiement (carte test valide)
curl -X PUT http://127.0.0.1:5000/order/1 \
  -H "Content-Type: application/json" \
  -d '{
        "credit_card":{
          "name":"John Doe",
          "number":"4242 4242 4242 4242",
          "expiration_year":2030,
          "expiration_month":12,
          "cvv":"123"
        }
      }' -i


      D. Exemple d’erreur : carte déclinée
curl -X PUT http://127.0.0.1:5000/order/1 \
  -H "Content-Type: application/json" \
  -d '{
        "credit_card":{
          "name":"John Doe",
          "number":"4000 0000 0000 0002",
          "expiration_year":2030,
          "expiration_month":12,
          "cvv":"123"
        }
      }'
# → HTTP 422 + {"errors":{"credit_card":{"code":"card-declined", ...}}}


. Lancer les tests

PYTHONPATH=. pytest -s -v



