from flask import abort, jsonify


TAX_RATES = {"QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14} # calculs des taxes en fonction de la zone 

def calculate_shipping(weight_total):
    if weight_total < 500:
        return 500   # 5 $
    if weight_total < 2000:
        return 1000  # 10 $
    return 2500      # 25 $

def calculate_total(product_price, qty):
    return product_price * qty

def calculate_tax(total, province):
    return total * TAX_RATES.get(province, 0)



def error(code, name, http=422):
    resp = jsonify({"errors": { "order" if code in ("missing-fields","out-of-inventory",
                                                    "already-paid") else "product":
                                 {"code": code, "name": name}}})
    resp.status_code = http
    abort(resp)
