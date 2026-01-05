from app.main import db


class Category(db.Model):
    """Medicine categories: Tablet, Syrup, Injection, etc."""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    
    # Relationship
    medicines = db.relationship('Medicine', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
