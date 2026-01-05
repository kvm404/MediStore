from datetime import datetime
from app.main import db


class Sale(db.Model):
    """A sale transaction (bill)."""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, default=datetime.now)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Relationship
    items = db.relationship('SaleItem', backref='sale', lazy=True)
    
    def __repr__(self):
        return f'<Sale #{self.id} - ₹{self.total_amount}>'


class SaleItem(db.Model):
    """Individual item in a sale."""
    __tablename__ = 'sale_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    price_at_sale = db.Column(db.Float, nullable=False)  # Price when sold (in case price changes later)
    
    # Relationship to get medicine details
    medicine = db.relationship('Medicine', backref='sale_items')
    
    def __repr__(self):
        return f'<SaleItem {self.medicine_id} x{self.quantity}>'
