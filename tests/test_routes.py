import pytest
from inf349.models import Product, Order, OrderLine


def insert_product():
    return Product.create(
        id=1,
        name="Test Product",
        description="Juste un test",
        price=1000,         
        weight=500,         
        in_stock=True,
        image="test.jpg"
    )

def test_get_products_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json() == {"products": []}

def test_post_order_missing_fields(client):
    response = client.post("/order", json={})
    print(response.get_json())  
    assert response.status_code == 422
    assert response.get_json()["errors"]["order"]["code"] == "missing-fields"

def test_post_order_invalid_id(client):
    response = client.post("/order", json={"product": {"id": 999, "quantity": 1}})
    print(response.get_json())   
    assert response.status_code == 422
    assert response.get_json()["errors"]["order"]["code"] == "out-of-inventory"

def test_post_order_success(client):
    insert_product()
    response = client.post("/order", json={"product": {"id": 1, "quantity": 2}})
    assert response.status_code == 302
    assert "Location" in response.headers

def insert_test_order():
    product = Product.create(
        id=42,
        name="Produit Test",
        description="Description test",
        price=1500,
        weight=300,
        in_stock=True,
        image="test.jpg"
    )
    order = Order.create(
        total_price=1500,
        total_price_tax=0,
        shipping_price=500,
        paid=False
    )
    OrderLine.create(order=order, product=product, quantity=1)
    return order.id

def test_get_order_found(client):
    order_id = insert_test_order()
    response = client.get(f"/order/{order_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert "order" in data
    assert data["order"]["id"] == order_id
    assert data["order"]["total_price"] == 1500

def test_get_order_not_found(client):
    response = client.get("/order/99999")
    assert response.status_code == 404
    data = response.get_json()
    assert "errors" in data
    assert data["errors"]["order"]["code"] == "not-found"

def insert_order_for_update():
    product = Product.create(
        id=999,
        name="Produit test PUT",
        description="Produit de test",
        price=1200,
        weight=500,
        in_stock=True,
        image="img.jpg"
    )
    order = Order.create(
        total_price=1200,
        total_price_tax=0,
        shipping_price=500,
        paid=False
    )
    OrderLine.create(order=order, product=product, quantity=1)
    return order.id

def test_put_order_add_address_success(client):
    order_id = insert_order_for_update()

    data = {
        "order": {
            "email": "toto@mail.com",
            "shipping_information": {
                "country": "Canada",
                "address": "12 rue des tests",
                "postal_code": "G0X1Y0",
                "city": "Testville",
                "province": "QC"
            }
        }
    }

    response = client.put(f"/order/{order_id}", json=data)
    print(response.get_json()) 
    assert response.status_code in (200, 204)

#Test de paiements
def insert_order_for_payment():
    product = Product.create(
        id=777,
        name="Produit Payable",
        description="Paiement test",
        price=2000,
        weight=500,
        in_stock=True,
        image="img.jpg"
    )
    order = Order.create(
        total_price=2000,
        total_price_tax=300,
        shipping_price=500,
        paid=False
    )
    OrderLine.create(order=order, product=product, quantity=1)
    return order.id

def test_put_order_payment_success(client):
    order_id = insert_order_for_payment()

    r1 = client.put(f"/order/{order_id}", json={
        "order": {
            "email": "client@test.com",
            "shipping_information": {
                "country": "Canada",
                "address": "123 rue de la Paix",
                "postal_code": "H0H0H0",
                "city": "Montréal",
                "province": "QC"
            }
        }
    })
    print("Response for adding email and address:", r1.status_code, r1.get_json())

    data = {
        "credit_card": {
            "number": "4242 4242 4242 4242",
            "expiration_month": 12,
            "expiration_year": 2028,
            "cvv": "123",
            "name": "Toto Test"
        }
    }

    response = client.put(f"/order/{order_id}", json=data)
    print("Réponse du paiement:", response.status_code, response.get_json())

    assert response.status_code in (200, 204)




def test_put_order_payment_failure(client):
    order_id = insert_order_for_payment()

    client.put(f"/order/{order_id}", json={
        "email": "client@test.com",
        "country": "Canada",
        "address": "123 rue de la Paix",
        "postal_code": "H0H0H0",
        "city": "Montréal",
        "province": "QC"
    })

    bad_card = {
        "credit_card": {
            "number": "1234567890123456",  # Faux numéro
            "expiry_month": 1,
            "expiry_year": 2020,           # Expirée
            "cvc": "123",
            "name": "Jean Bidon"
        }
    }

    response = client.put(f"/order/{order_id}", json=bad_card)
    print(response.get_json())
    assert response.status_code in (402, 422)
