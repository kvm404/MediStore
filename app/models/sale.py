from datetime import datetime
from app.main import db


class Sale(db.Model):
    """A sale transaction (bill)."""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Optional: Customer info (for future use)
    customer_name = db.Column(db.String(100))
    
    # Relationship
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Sale #{self.id} - ₹{self.total_amount}>'
    
    def calculate_total(self):
        """Calculate total from sale items."""
        return sum(item.quantity * item.price_at_sale for item in self.items)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'sale_date': self.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
            'total_amount': self.total_amount,
            'customer_name': self.customer_name,
            'items': [item.to_dict() for item in self.items]
        }


class SaleItem(db.Model):
    """Individual item in a sale."""
    __tablename__ = 'sale_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False) # In base units (e.g. tablets)
    price_at_sale = db.Column(db.Float, nullable=False)  # Price per unit when sold
    
    # Relationship
    batch = db.relationship('Batch', backref='sale_items')
    
    def __repr__(self):
        return f'<SaleItem Batch:{self.batch_id} x{self.quantity}>'
    
    @property
    def subtotal(self):
        """Calculate subtotal for this item."""
        return self.quantity * self.price_at_sale
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'medicine_name': self.batch.medicine.name if self.batch else 'Unknown',
            'batch_number': self.batch.batch_number if self.batch else 'Unknown',
            'quantity': self.quantity,
            'price_at_sale': self.price_at_sale,
            'subtotal': self.subtotal
        }
