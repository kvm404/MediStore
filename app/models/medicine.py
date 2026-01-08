from datetime import datetime
from app.main import db


class Medicine(db.Model):
    """Medicine/Item sold in the store."""
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Category link
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # Unit Logic
    packing_type = db.Column(db.String(50), default="Strip")  # "Strip", "Bottle", "Box"
    units_per_pack = db.Column(db.Integer, default=1, nullable=False)  # 10 for strip, 1 for bottle
    
    # Basic Info
    manufacturer = db.Column(db.String(100))
    generic_name = db.Column(db.String(100))  # Composition
    
    # Status
    min_stock_level = db.Column(db.Integer, default=10) # Alert threshold
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Medicine {self.name}>'
    
    @property
    def total_stock(self):
        """Total stock across all active batches."""
        return sum(b.stock_quantity for b in self.batches if b.is_active)
    
    @property
    def is_low_stock(self):
        """Check if total stock is below minimum level."""
        return self.total_stock <= self.min_stock_level
    
    @property
    def is_out_of_stock(self):
        """Check if item is out of stock."""
        return self.total_stock == 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.name if self.category else None,
            'total_stock': self.total_stock,
            'packing_type': self.packing_type,
            'units_per_pack': self.units_per_pack,
            'is_low_stock': self.is_low_stock,
            'is_active': self.is_active
        }
