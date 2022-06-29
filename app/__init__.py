import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flaskext.markdown import Markdown

app = Flask(__name__)
bootstrap = Bootstrap(app)
markdown = Markdown(app)

SECRET_KEY = os.getenv("SECRET_KEY", default=os.urandom(32))
app.config["SECRET_KEY"] = SECRET_KEY

from app import routes
