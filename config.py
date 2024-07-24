
class Config:
    DEBUG = True
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False 

class DevelopmentConfig(Config):
    SECRET_KEY = 'dev'
    DEBUG = True
    TESTING = True