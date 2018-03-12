import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    # Edit in .env file
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'NOT_so_SECR3T_kEY'

    # User Configurables
    #SQLALCHEMY_DATABASE_URI = "sqlite:////home/rotide/rpi.tv/monolith/app.db"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://rpitv:testpassword@172.17.0.2:3306/rpitv"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    VIDEO_BASE_DIR = "/mnt/media"
