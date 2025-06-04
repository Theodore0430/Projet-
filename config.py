import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))



class Config:
    DEBUG = True
    DATABASE = os.path.join(BASE_DIR, "shop.db")
    REMOTE_PRODUCTS_URL = "http://dimensweb.uqac.ca/~jgnault/shops/products/"
    PAYMENT_URL = "http://dimensweb.uqac.ca/~jgnault/shops/pay/"

config = Config()
