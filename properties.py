__author__ = 'Luis Geronimo'

import logging

class Config(object):
    # properties Admin
    LINK='/admin'
    TEM='bootstrap3'
    NAMEAPP= 'DNS'
    # properties for Email
    #PMAIL = 587  # For starttls
    #SMTP = ''
    #SEMAIL = ''
    #EPASS = ''
    #REMAIL = ''
    LOG_LEVEL = logging.DEBUG
    SECRETKEY='desDNS'

class ProductionConfig(Config):
    DEBUG=False
    # properties host
    SERVER='0.0.0.0'
    # properties SQlite
    DB_DIR = 'sqlite:////etc/dnsweb/db/data.db'
    # Log
    LOG_DIR='/var/log/dnsweb/dns_web_%d_%m_%Y.log'
    # Port
    PRTO = 4000
    #Service
    _SER=str('http://'+SERVER+':'+str(PRTO))
    # Api hosted zones
    APIHOSETD=_SER+'/core/v1.0/hostedzone'
    # Api User
    APIUSER=_SER+'/core/v1.0/apiuser'
    # Api domain
    APIDOMAIN=_SER+'/core/v1.0/domain/'

class DevelopmentConfig(Config):
    DEBUG=True
    # properties host
    SERVER='127.0.0.1'
    # properties SQlite
    DB_DIR = 'sqlite:////mnt/c/Users/LP-0220/Documents/Desarrollos/flask/dnsWEB/db/des-data.db'
    # Log
    LOG_DIR='logs/dns_web_%d_%m_%Y.log'
    # Port
    PRTO = 8292
    #service
    _SER=str('http://'+SERVER+':'+str(PRTO))
    # Api hosted zones
    APIHOSETD=_SER+'/core/v1.0/hostedzone'
    # Api User
    APIUSER=_SER+'/core/v1.0/apiuser' 
    # Api domain
    APIDOMAIN=_SER+'/core/v1.0/domain/'