from datetime import datetime
from flask import Blueprint, render_template
from app.main import db
from app.models import Category, Medicine, Batch, Sale, SaleItem

home = Blueprint('home', __name__)


@home.route('/')
def dashboard():
    """Dashboard with summary stats and alerts."""
    today = datetime.now().date()
    
    # Calculate stats
    stats = {
        'total_medicines': Medicine.query.filter_by(is_active=True).count(),
        'today_sales': db.session.query(db.func.sum(Sale.total_amount)).filter(
            db.func.date(Sale.sale_date) == today
        ).scalar() or 0,
        'low_stock_count': sum(1 for m in Medicine.query.filter_by(is_active=True).all() if m.is_low_stock),
        'expiring_soon_count': Batch.query.filter(
            Batch.is_active == True,
            Batch.expiry_date > today,
            Batch.expiry_date <= db.func.date(today, '+30 days')
        ).count(),
    }
    
    # Recent sales (last 5)
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(5).all()
    
    # Low stock medicines
    all_medicines = Medicine.query.filter_by(is_active=True).all()
    low_stock_medicines = [m for m in all_medicines if m.is_low_stock][:5]
    
    # Expiring soon batches (within 30 days)
    expiring_batches = Batch.query.filter(
        Batch.is_active == True,
        Batch.expiry_date > today,
        Batch.expiry_date <= db.func.date(today, '+30 days')
    ).order_by(Batch.expiry_date).limit(5).all()
    
    return render_template('home.html',
        stats=stats,
        recent_sales=recent_sales,
        low_stock_medicines=low_stock_medicines,
        expiring_batches=expiring_batches,
        now=datetime.now()
    )
