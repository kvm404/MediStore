from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = "MediStore Admin"
    
    
    # Initialize extensions
    db.init_app(app)
    
    # Import models (important for migrations)
    from app.models import Category, Medicine, Sale, SaleItem
    
    # Import Routes
    # eg: from .routes.home import home

    # Register Routes
    # eg: app.register_blueprint(home, url_prefix='/')




    migrate = Migrate(app, db)
    
    return app