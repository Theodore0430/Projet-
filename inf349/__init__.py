from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider

from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from config import config
import click

db = SqliteExtDatabase(config.DATABASE)
class UTF8JSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault("ensure_ascii", False)
        return super().dumps(obj, **kwargs)

    def loads(self, s, **kwargs):
        return super().loads(s, **kwargs)

def create_app():
    app = Flask(__name__)
    

    app.config.from_object("config.config")
    app.json = UTF8JSONProvider(app)



    @app.before_request
    def _db_connect():
        if db.is_closed():
            db.connect(reuse_if_open=True)

    @app.teardown_request
    def _db_close(exc):
        if not db.is_closed():
            db.close()

    from .routes import shop_bp
    app.register_blueprint(shop_bp)
    @app.errorhandler(404)
    def not_found(err):
        return jsonify({
            "errors": {
                "order": {
                    "code": "not-found",
                    "name": "La ressource demandée est introuvable"
                }
            }
        }), 404
    @app.errorhandler(500)
    def internal_error(err):
        return jsonify({
            "errors": {
                "server": {
                    "code": "internal-error",
                    "name": "Une erreur interne est survenue"
                }
            }
        }), 500





    @app.cli.command("init-db")
    def init_db():
        from .models import create_tables
        from .product_service import fetch_and_cache_products
        create_tables()
        fetch_and_cache_products()
        click.echo("Base initialisée et produits importés.")

    return app

app = create_app()
