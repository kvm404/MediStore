import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    
    # Initialize extensions
    db.init_app(app)
    
    # Context processor to make 'now' available in all templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    # Import models (important for migrations)
    from app.models import Category, Medicine, Batch, Sale, SaleItem
    
    # Import Routes
    from app.routes.home import home
    from app.routes.medicines import medicines
    from app.routes.api import api
    from app.routes.sales import bp as sales
    from app.routes.categories import categories
    from app.routes.reports import reports

    # Register Routes
    app.register_blueprint(home, url_prefix='/')
    app.register_blueprint(medicines, url_prefix='/medicines')
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(sales)
    app.register_blueprint(categories)
    app.register_blueprint(reports)




    migrate = Migrate(app, db)
    
    return app