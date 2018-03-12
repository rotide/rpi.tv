from flask import Blueprint

bp = Blueprint('channels', __name__, template_folder='templates', static_folder='static')

from project.channels import routes
