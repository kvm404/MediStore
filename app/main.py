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
    from app.models import Category, Medicine, Batch, Sale, SaleItem
    
    # Import Routes
    from app.routes.home import home
    from app.routes.medicines import medicines
    from app.routes.api import api

    # Register Routes
    app.register_blueprint(home, url_prefix='/')
    app.register_blueprint(medicines, url_prefix='/medicines')
    app.register_blueprint(api, url_prefix='/api')




    migrate = Migrate(app, db)
    
    return app