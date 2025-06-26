# inf349/database.py

import os
from peewee import PostgresqlDatabase

db = PostgresqlDatabase(
    os.getenv("DB_NAME", "api8inf349"),
    user=os.getenv("DB_USER", "user"),
    password=os.getenv("DB_PASSWORD", "pass"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 5432)),
)
