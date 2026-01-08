from datetime import datetime
from app.main import db


class Batch(db.Model):
    """Specific batch of a medicine with expiry and stock."""
    __tablename__ = 'batches'
    __table_args__ = (
        db.UniqueConstraint('medicine_id', 'batch_number', name='unique_batch_per_medicine'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    
    batch_number = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    
    # Financials
    purchase_price = db.Column(db.Float)  # Buying price per pack
    mrp = db.Column(db.Float, nullable=False)  # Maximum Retail Price per pack
    
    # Stock tracking (Always in smallest unit, e.g., tablets)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)  # False when empty or expired
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship with Medicine
    medicine = db.relationship('Medicine', backref=db.backref('batches', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Batch {self.batch_number} - {self.medicine.name}>'
    
    @property
    def is_expired(self):
        """Check if batch is expired."""
        return self.expiry_date < datetime.now().date()
    
    @property
    def days_until_expiry(self):
        """Days remaining until expiry. Negative if expired."""
        delta = self.expiry_date - datetime.now().date()
        return delta.days
    
    @property
    def is_expiring_soon(self):
        """Check if expiring within 30 days."""
        return 0 < self.days_until_expiry <= 30
    
    @property
    def unit_price(self):
        """Calculate price per single unit (tablet/ml)."""
        if self.medicine and self.medicine.units_per_pack > 0:
            return self.mrp / self.medicine.units_per_pack
        return self.mrp

    def to_dict(self):
        return {
            'id': self.id,
            'batch_number': self.batch_number,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d'),
            'stock_quantity': self.stock_quantity,
            'mrp': self.mrp,
            'unit_price': self.unit_price,
            'is_expired': self.is_expired,
            'days_until_expiry': self.days_until_expiry,
            'is_expiring_soon': self.is_expiring_soon
        }
