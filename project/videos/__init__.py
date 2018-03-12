from flask import Blueprint

bp = Blueprint(
    'videos',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from project.videos import routes
