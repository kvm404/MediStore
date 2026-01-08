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
    """Individual item in a sale. Supports both listed and unlisted items."""
    __tablename__ = 'sale_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    
    # For listed items (linked to inventory)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    
    # For unlisted/quick sale items (when medicine not in database yet)
    item_name = db.Column(db.String(100), nullable=True)  # Manual entry name
    
    quantity = db.Column(db.Integer, nullable=False)  # In base units (e.g. tablets)
    price_at_sale = db.Column(db.Float, nullable=False)  # Price per unit when sold
    
    # Relationship
    batch = db.relationship('Batch', backref='sale_items')
    
    @property
    def is_listed_item(self):
        """Check if this is a listed (inventory-tracked) item."""
        return self.batch_id is not None
    
    def __repr__(self):
        if self.batch_id:
            return f'<SaleItem Batch:{self.batch_id} x{self.quantity}>'
        return f'<SaleItem Unlisted:"{self.item_name}" x{self.quantity}>'
    
    @property
    def subtotal(self):
        """Calculate subtotal for this item."""
        return self.quantity * self.price_at_sale
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        if self.batch:
            # Listed item (from inventory)
            return {
                'id': self.id,
                'is_listed': True,
                'medicine_name': self.batch.medicine.name,
                'batch_number': self.batch.batch_number,
                'quantity': self.quantity,
                'price_at_sale': self.price_at_sale,
                'subtotal': self.subtotal
            }
        else:
            # Unlisted/Quick sale item
            return {
                'id': self.id,
                'is_listed': False,
                'medicine_name': self.item_name or 'Unlisted Item',
                'batch_number': None,
                'quantity': self.quantity,
                'price_at_sale': self.price_at_sale,
                'subtotal': self.subtotal
            }
