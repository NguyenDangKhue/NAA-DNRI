from flask import Flask


def create_app() -> Flask:
	app = Flask(__name__)
	app.config["SECRET_KEY"] = "change-me-dev-key"

	from .routes import pages
	app.register_blueprint(pages)

	return app
