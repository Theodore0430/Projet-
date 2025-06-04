from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from config import config

db = SqliteExtDatabase(config.DATABASE)

class BaseModel(Model):
    class Meta:
        database = db
class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = TextField()
    price = IntegerField()
    weight = IntegerField()
    in_stock = BooleanField()
    image = CharField()
class Order(BaseModel):
    email = CharField(null=True)
    country = CharField(null=True)
    address = CharField(null=True)
    postal_code = CharField(null=True)
    city = CharField(null=True)
    province = CharField(null=True)
    paid = BooleanField(default=False)
    total_price = IntegerField()
    total_price_tax = FloatField()
    shipping_price = IntegerField()
    credit_card_first = CharField(null=True)
    credit_card_last = CharField(null=True)
    credit_card_name = CharField(null=True)
    credit_exp_month = IntegerField(null=True)
    credit_exp_year = IntegerField(null=True)
    transaction_id = CharField(null=True)
    transaction_success = BooleanField(null=True)
    transaction_amount = IntegerField(null=True)
class OrderLine(BaseModel):
    order = ForeignKeyField(Order, backref="lines", on_delete="CASCADE")
    product = ForeignKeyField(Product, backref="order_lines")
    quantity = IntegerField()


def create_tables():
    db.create_tables([Product, Order, OrderLine])
