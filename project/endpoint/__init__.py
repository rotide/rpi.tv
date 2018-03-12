from flask import Blueprint

bp = Blueprint(
    'endpoint',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from project.endpoint import routes
