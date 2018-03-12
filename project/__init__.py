import logging, os
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from celery import Celery
from config import Config

# Monolith design

# Video Player 		(On Raspberry Pi Video Device (Endpoint))
# - Plays videos as instructed

# Video Manager		(Celery Task)
# - When Video PLAYS, rPi POSTs to queue NEXT video

# Video Finder 		This App: videos
# - Searches for and records all videos

# Video Scanner		(Celery Task)
# - Scans for videos and adds them to database

# Controller 		This App: controller
# Frontend 		This App: frontend
# User Management 	This App: users
# Player Management 	This App: players
# Channel Management 	This App: channels

app = Flask(__name__)

app.config.from_object(Config)

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)
celery.conf.update(app.config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'auth.login'
bootstrap = Bootstrap(app)

from project.web import bp as web_bp
from project.auth import bp as auth_bp
from project.videos import bp as videos_bp
from project.channels import bp as channels_bp
from project.endpoint import bp as endpoints_bp
from project.errors import bp as errors_bp
app.register_blueprint(web_bp, url_prefix='/web')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(videos_bp, url_prefix='/api/videos')
app.register_blueprint(channels_bp, url_prefix='/api/channels')
app.register_blueprint(endpoints_bp, url_prefix='/api/endpoint')
app.register_blueprint(errors_bp)

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/video_finder.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Microblog startup')

from project import models