def test_get_root_returns_products(client, monkeypatch):
    monkeypatch.setattr("inf349.product_service.requests.get",
                        lambda *_a, **_k: type("R",(object,),
                                                {"json": lambda self: {"products":[{"id":1,"name":"X","description":"","price":100,"weight":100,"in_stock":True,"image":"0.jpg"}]},
                                                 "status_code":200,
                                                 "raise_for_status":lambda self:None})())
    from inf349.product_service import fetch_and_cache_products
    fetch_and_cache_products()

    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json["products"][0]["id"] == 1
