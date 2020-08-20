__author__ = 'Luis Geronimo'

from flask import Flask
#Entorno
from flask_environments import Environments

#QLAlchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker

#Login manager
from flask_login import LoginManager

app = Flask(__name__)

if app.config["ENV"] == "production":
    app.config.from_object("properties.ProductionConfig")
elif app.config["ENV"] == "development":
    app.config.from_object("properties.DevelopmentConfig")
else:
    app.config.from_object("properties.TestingConfig")

class cf():
    SERVER=app.config["SERVER"]
    PRTO=app.config["PRTO"]
    SECRETKEY=app.config["SECRETKEY"]
    #PMAIL=app.config["PMAIL"]
    #SMTP=app.config["SMTP"]
    #SEMAIL=app.config["SEMAIL"]
    #REMAIL=app.config["REMAIL"]
    #EPASS=app.config["EPASS"]
    DB_DIR=app.config["DB_DIR"]
    LINK=app.config["LINK"]
    TEM=app.config["TEM"]
    NAMEAPP=app.config["NAMEAPP"]
    APIUSER=app.config["APIUSER"]
    APIHOSETD=app.config["APIHOSETD"]
    APIDOMAIN=app.config["APIDOMAIN"]
    LOG_DIR=app.config["LOG_DIR"]
    LOG_LEVEL=app.config["LOG_LEVEL"]
    DEBUG=app.config["DEBUG"]

app.config['SECRET_KEY'] = cf.SECRETKEY
app.config['SQLALCHEMY_DATABASE_URI'] = cf.DB_DIR
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)

from app.view import dashboard
from app.view import domain
from app.view import named
from app.view import masterslave
from app.view import users