from app.main import db


class Medicine(db.Model):
    """Medicine/Item sold in the store."""
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Category link
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # Pricing
    price = db.Column(db.Float, nullable=False)  # Selling price per unit
    
    # Stock
    stock_quantity = db.Column(db.Integer, default=0)
    
    # Unit info (e.g., "strip of 10", "100ml bottle", "single vial")
    unit = db.Column(db.String(50))
    
    # Optional: Manufacturer/Brand
    manufacturer = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Medicine {self.name}>'
