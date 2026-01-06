from datetime import datetime
from app.main import db


class Category(db.Model):
    """Medicine categories: Tablet, Syrup, Injection, etc."""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    medicines = db.relationship('Medicine', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    @property
    def medicine_count(self):
        """Count of medicines in this category."""
        return len(self.medicines)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'medicine_count': self.medicine_count
        }
