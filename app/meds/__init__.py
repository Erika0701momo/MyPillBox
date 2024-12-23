from flask import Blueprint

bp = Blueprint("meds", __name__)

from app.meds import routes
