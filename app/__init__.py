from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)

# Get the path of the current script
current_path = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')


# Use the path in your app
app.config['APP_PATH'] = current_path
app.config['STATIC_PATH'] = static_path

#Cargar las configuraciones 
app.config.from_object('config.DevelopmentConfig')


app.config['SECRET_KEY'] = 'secret'
 
#Importar aplicaciones
from app.views import running

app.register_blueprint(running)

