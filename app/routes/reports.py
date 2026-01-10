from flask import Blueprint, render_template, request
from app.main import db
from app.models import Medicine, Batch, Sale, SaleItem
from datetime import datetime, timedelta
from sqlalchemy import func

reports = Blueprint('reports', __name__, url_prefix='/reports')


@reports.route('/')
def index():
    """Reports dashboard."""
    return render_template('reports/index.html')


@reports.route('/sales')
def sales_report():
    """Daily/Weekly/Monthly sales report."""
    # Get date range
    period = request.args.get('period', 'today')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    today = datetime.now().date()
    
    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == 'month':
        start_date = today - timedelta(days=30)
        end_date = today
    elif period == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today
            end_date = today
    else:
        start_date = today
        end_date = today
    
    # Query sales in date range
    sales = Sale.query.filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).order_by(Sale.sale_date.desc()).all()
    
    # Calculate summary
    total_sales = sum(s.total_amount for s in sales)
    total_items = sum(len(s.items) for s in sales)
    
    # Daily breakdown
    daily_sales = {}
    for sale in sales:
        date_key = sale.sale_date.date()
        if date_key not in daily_sales:
            daily_sales[date_key] = {'count': 0, 'amount': 0}
        daily_sales[date_key]['count'] += 1
        daily_sales[date_key]['amount'] += sale.total_amount
    
    return render_template('reports/sales.html',
        sales=sales,
        total_sales=total_sales,
        total_items=total_items,
        sale_count=len(sales),
        daily_sales=daily_sales,
        period=period,
        start_date=start_date,
        end_date=end_date
    )


@reports.route('/expiry')
def expiry_report():
    """Expiring and expired batches report."""
    today = datetime.now().date()
    
    # Get expired batches
    expired_batches = Batch.query.filter(
        Batch.is_active == True,
        Batch.expiry_date < today,
        Batch.stock_quantity > 0
    ).order_by(Batch.expiry_date).all()
    
    # Get expiring within 30 days
    expiring_soon = Batch.query.filter(
        Batch.is_active == True,
        Batch.expiry_date >= today,
        Batch.expiry_date <= today + timedelta(days=30),
        Batch.stock_quantity > 0
    ).order_by(Batch.expiry_date).all()
    
    # Get expiring within 90 days (but not in 30)
    expiring_90 = Batch.query.filter(
        Batch.is_active == True,
        Batch.expiry_date > today + timedelta(days=30),
        Batch.expiry_date <= today + timedelta(days=90),
        Batch.stock_quantity > 0
    ).order_by(Batch.expiry_date).all()
    
    # Calculate total value at risk
    expired_value = sum(b.stock_quantity * b.unit_price for b in expired_batches)
    expiring_value = sum(b.stock_quantity * b.unit_price for b in expiring_soon)
    expiring_90_value = sum(b.stock_quantity * b.unit_price for b in expiring_90)
    
    return render_template('reports/expiry.html',
        expired_batches=expired_batches,
        expiring_soon=expiring_soon,
        expiring_90=expiring_90,
        expired_value=expired_value,
        expiring_value=expiring_value,
        expiring_90_value=expiring_90_value,
        today=today
    )


@reports.route('/stock')
def stock_report():
    """Low stock and out of stock report."""
    # Get all active medicines
    medicines = Medicine.query.filter_by(is_active=True).order_by(Medicine.name).all()
    
    # Categorize by stock status
    out_of_stock = []
    low_stock = []
    healthy_stock = []
    total_stock_value = 0
    
    for m in medicines:
        total_qty = m.total_stock
        
        # Calculate stock value
        stock_value = sum(b.stock_quantity * b.unit_price for b in m.batches if b.is_active)
        total_stock_value += stock_value
        
        if m.is_out_of_stock:
            out_of_stock.append(m)
        elif m.is_low_stock:
            low_stock.append((m, total_qty))
        else:
            healthy_stock.append((m, total_qty, stock_value))
    
    return render_template('reports/stock.html',
        out_of_stock=out_of_stock,
        low_stock=low_stock,
        healthy_stock=healthy_stock,
        total_medicines=len(medicines),
        total_stock_value=total_stock_value
    )
