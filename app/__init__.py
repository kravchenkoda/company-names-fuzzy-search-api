from flask import Flask
from extensions import api
from companies_routes import ns


def create_app():
    app = Flask(__name__)

    api.init_app(app)
    api.add_namespace(ns)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
