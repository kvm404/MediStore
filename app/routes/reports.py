from flask import Blueprint, render_template, request
from app.models import db, Medicine, Batch, Sale, SaleItem, Category
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from calendar import monthrange

reports = Blueprint('reports', __name__, url_prefix='/reports')


# ============ HELPER FUNCTIONS ============

def get_date_range(period):
    """Get start and end dates based on period selection."""
    today = datetime.now().date()
    
    if period == 'this_month':
        start_date = today.replace(day=1)
        _, last_day = monthrange(today.year, today.month)
        end_date = today.replace(day=last_day)
    elif period == 'last_month':
        first_of_this = today.replace(day=1)
        last_month_end = first_of_this - timedelta(days=1)
        start_date = last_month_end.replace(day=1)
        end_date = last_month_end
    elif period == 'this_year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    elif period == 'last_year':
        start_date = today.replace(year=today.year-1, month=1, day=1)
        end_date = today.replace(year=today.year-1, month=12, day=31)
    else:
        start_date = today.replace(day=1)
        _, last_day = monthrange(today.year, today.month)
        end_date = today.replace(day=last_day)
    
    return start_date, end_date, period or 'this_month'


def get_month_date_range(month, year):
    """Get start and end dates for a specific month/year."""
    start_date = datetime(year, month, 1).date()
    _, last_day = monthrange(year, month)
    end_date = datetime(year, month, last_day).date()
    return start_date, end_date


def calculate_item_profit(sale_item):
    """
    Calculate profit for a single sale item.
    Returns (revenue, cost, profit) tuple.
    Unlisted items return (revenue, 0, 0) - unknown cost.
    """
    revenue = sale_item.subtotal
    
    if not sale_item.batch_id or not sale_item.batch:
        # Unlisted item - no cost data
        return revenue, 0, 0
    
    batch = sale_item.batch
    
    # Get cost per unit from batch
    if batch.purchase_price and batch.medicine and batch.medicine.units_per_pack > 0:
        cost_per_unit = batch.purchase_price / batch.medicine.units_per_pack
    else:
        # No purchase price recorded
        return revenue, 0, 0
    
    cost = cost_per_unit * sale_item.quantity
    profit = revenue - cost
    
    return revenue, cost, profit


def calculate_sale_profit(sale):
    """Calculate total profit for a sale."""
    total_revenue = 0
    total_cost = 0
    total_profit = 0
    
    for item in sale.items:
        revenue, cost, profit = calculate_item_profit(item)
        total_revenue += revenue
        total_cost += cost
        total_profit += profit
    
    return total_revenue, total_cost, total_profit


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


# ============ BUSINESS REPORTS ============

@reports.route('/profit')
def profit_report():
    """Profit & Loss report with charts."""
    period = request.args.get('period', 'this_month')
    start_date, end_date, period = get_date_range(period)
    
    # Get all sales in range
    sales = Sale.query.filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date
    ).order_by(Sale.sale_date).all()
    
    # Calculate totals
    total_revenue = 0
    total_cost = 0
    total_profit = 0
    daily_data = {}
    
    for sale in sales:
        revenue, cost, profit = calculate_sale_profit(sale)
        total_revenue += revenue
        total_cost += cost
        total_profit += profit
        
        # Daily breakdown for chart
        date_key = sale.sale_date.strftime('%Y-%m-%d')
        if date_key not in daily_data:
            daily_data[date_key] = {'revenue': 0, 'cost': 0, 'profit': 0}
        daily_data[date_key]['revenue'] += revenue
        daily_data[date_key]['cost'] += cost
        daily_data[date_key]['profit'] += profit
    
    # Calculate margin percentage
    margin_percent = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Prepare chart data (sorted by date)
    chart_labels = sorted(daily_data.keys())
    chart_revenue = [daily_data[d]['revenue'] for d in chart_labels]
    chart_profit = [daily_data[d]['profit'] for d in chart_labels]
    
    return render_template('reports/profit.html',
        period=period,
        start_date=start_date,
        end_date=end_date,
        total_revenue=total_revenue,
        total_cost=total_cost,
        total_profit=total_profit,
        margin_percent=margin_percent,
        sale_count=len(sales),
        chart_labels=chart_labels,
        chart_revenue=chart_revenue,
        chart_profit=chart_profit
    )


@reports.route('/top-sellers')
def top_sellers_report():
    """Top selling products by quantity and revenue."""
    period = request.args.get('period', 'this_month')
    start_date, end_date, period = get_date_range(period)
    
    # Get all sale items in range (excluding unlisted) with eager loading
    sale_items = db.session.query(SaleItem).join(Sale).options(
        joinedload(SaleItem.batch).joinedload(Batch.medicine)
    ).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date,
        SaleItem.batch_id.isnot(None)
    ).all()
    
    # Aggregate by medicine
    medicine_stats = {}
    for item in sale_items:
        med_id = item.batch.medicine_id
        med_name = item.batch.medicine.name
        
        if med_id not in medicine_stats:
            medicine_stats[med_id] = {
                'name': med_name,
                'quantity': 0,
                'revenue': 0,
                'transactions': 0
            }
        
        medicine_stats[med_id]['quantity'] += item.quantity
        medicine_stats[med_id]['revenue'] += item.subtotal
        medicine_stats[med_id]['transactions'] += 1
    
    # Sort by quantity (top sellers)
    top_by_qty = sorted(medicine_stats.values(), key=lambda x: x['quantity'], reverse=True)[:20]
    
    # Sort by revenue
    top_by_revenue = sorted(medicine_stats.values(), key=lambda x: x['revenue'], reverse=True)[:20]
    
    # Chart data (top 10 by quantity)
    chart_labels = [m['name'][:20] for m in top_by_qty[:10]]
    chart_quantities = [m['quantity'] for m in top_by_qty[:10]]
    chart_revenues = [m['revenue'] for m in top_by_revenue[:10]]
    
    return render_template('reports/top_sellers.html',
        period=period,
        start_date=start_date,
        end_date=end_date,
        top_by_qty=top_by_qty,
        top_by_revenue=top_by_revenue,
        chart_labels=chart_labels,
        chart_quantities=chart_quantities,
        chart_revenues=chart_revenues
    )


@reports.route('/profitable-products')
def profitable_products_report():
    """Products ranked by profit margin."""
    period = request.args.get('period', 'this_month')
    start_date, end_date, period = get_date_range(period)
    
    # Get all sale items in range (excluding unlisted) with eager loading
    sale_items = db.session.query(SaleItem).join(Sale).options(
        joinedload(SaleItem.batch).joinedload(Batch.medicine)
    ).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date,
        SaleItem.batch_id.isnot(None)
    ).all()
    
    # Aggregate by medicine with profit calculation
    medicine_profits = {}
    for item in sale_items:
        med_id = item.batch.medicine_id
        med_name = item.batch.medicine.name
        
        revenue, cost, profit = calculate_item_profit(item)
        
        if med_id not in medicine_profits:
            medicine_profits[med_id] = {
                'name': med_name,
                'revenue': 0,
                'cost': 0,
                'profit': 0,
                'quantity': 0
            }
        
        medicine_profits[med_id]['revenue'] += revenue
        medicine_profits[med_id]['cost'] += cost
        medicine_profits[med_id]['profit'] += profit
        medicine_profits[med_id]['quantity'] += item.quantity
    
    # Calculate margin % for each
    for med in medicine_profits.values():
        med['margin'] = (med['profit'] / med['revenue'] * 100) if med['revenue'] > 0 else 0
    
    # Sort by profit amount
    top_by_profit = sorted(medicine_profits.values(), key=lambda x: x['profit'], reverse=True)[:20]
    
    # Sort by margin %
    top_by_margin = sorted(medicine_profits.values(), key=lambda x: x['margin'], reverse=True)[:20]
    
    return render_template('reports/profitable_products.html',
        period=period,
        start_date=start_date,
        end_date=end_date,
        top_by_profit=top_by_profit,
        top_by_margin=top_by_margin
    )


@reports.route('/category-performance')
def category_performance_report():
    """Sales and profit breakdown by category."""
    period = request.args.get('period', 'this_month')
    start_date, end_date, period = get_date_range(period)
    
    # Get all sale items in range (excluding unlisted) with eager loading
    sale_items = db.session.query(SaleItem).join(Sale).options(
        joinedload(SaleItem.batch).joinedload(Batch.medicine).joinedload(Medicine.category)
    ).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date,
        SaleItem.batch_id.isnot(None)
    ).all()
    
    # Aggregate by category
    category_stats = {}
    for item in sale_items:
        cat = item.batch.medicine.category
        cat_id = cat.id if cat else 0
        cat_name = cat.name if cat else 'Uncategorized'
        
        revenue, cost, profit = calculate_item_profit(item)
        
        if cat_id not in category_stats:
            category_stats[cat_id] = {
                'name': cat_name,
                'revenue': 0,
                'cost': 0,
                'profit': 0,
                'items_sold': 0,
                'transactions': 0
            }
        
        category_stats[cat_id]['revenue'] += revenue
        category_stats[cat_id]['cost'] += cost
        category_stats[cat_id]['profit'] += profit
        category_stats[cat_id]['items_sold'] += item.quantity
        category_stats[cat_id]['transactions'] += 1
    
    # Sort by revenue
    categories = sorted(category_stats.values(), key=lambda x: x['revenue'], reverse=True)
    
    # Calculate percentages
    total_revenue = sum(c['revenue'] for c in categories)
    for cat in categories:
        cat['percentage'] = (cat['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
        cat['margin'] = (cat['profit'] / cat['revenue'] * 100) if cat['revenue'] > 0 else 0
    
    # Chart data
    chart_labels = [c['name'] for c in categories[:8]]
    chart_values = [c['revenue'] for c in categories[:8]]
    
    return render_template('reports/category_performance.html',
        period=period,
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        total_revenue=total_revenue,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


@reports.route('/dead-stock')
def dead_stock_report():
    """Products not sold in specified days."""
    days = request.args.get('days', 30, type=int)
    cutoff_date = datetime.now().date() - timedelta(days=days)
    
    # Get all medicines with stock
    medicines = Medicine.query.filter(
        Medicine.is_active == True
    ).all()
    
    dead_stock = []
    
    for med in medicines:
        if med.total_stock == 0:
            continue
        
        # Get last sale date for this medicine
        last_sale = db.session.query(func.max(Sale.sale_date)).join(SaleItem).join(Batch).filter(
            Batch.medicine_id == med.id
        ).scalar()
        
        if last_sale is None or last_sale.date() < cutoff_date:
            # Calculate stock value
            stock_value = sum(b.stock_quantity * b.unit_price for b in med.batches if b.is_active and b.stock_quantity > 0)
            
            dead_stock.append({
                'medicine': med,
                'stock': med.total_stock,
                'value': stock_value,
                'last_sale': last_sale.date() if last_sale else None,
                'days_since': (datetime.now().date() - last_sale.date()).days if last_sale else None
            })
    
    # Sort by value (highest first)
    dead_stock.sort(key=lambda x: x['value'], reverse=True)
    
    total_dead_value = sum(d['value'] for d in dead_stock)
    
    return render_template('reports/dead_stock.html',
        days=days,
        dead_stock=dead_stock,
        total_dead_value=total_dead_value,
        item_count=len(dead_stock)
    )


@reports.route('/trends')
def trends_report():
    """Sales trends comparison (this month vs last month)."""
    today = datetime.now().date()
    
    # This month
    this_month_start = today.replace(day=1)
    _, this_month_last = monthrange(today.year, today.month)
    this_month_end = today.replace(day=this_month_last)
    
    # Last month
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    
    # Get sales for both periods
    this_month_sales = Sale.query.filter(
        func.date(Sale.sale_date) >= this_month_start,
        func.date(Sale.sale_date) <= this_month_end
    ).all()
    
    last_month_sales = Sale.query.filter(
        func.date(Sale.sale_date) >= last_month_start,
        func.date(Sale.sale_date) <= last_month_end
    ).all()
    
    # Calculate metrics for this month
    this_revenue = sum(s.total_amount for s in this_month_sales)
    this_transactions = len(this_month_sales)
    this_profit = sum(calculate_sale_profit(s)[2] for s in this_month_sales)
    
    # Calculate metrics for last month
    last_revenue = sum(s.total_amount for s in last_month_sales)
    last_transactions = len(last_month_sales)
    last_profit = sum(calculate_sale_profit(s)[2] for s in last_month_sales)
    
    # Calculate growth percentages
    revenue_growth = ((this_revenue - last_revenue) / last_revenue * 100) if last_revenue > 0 else 0
    transaction_growth = ((this_transactions - last_transactions) / last_transactions * 100) if last_transactions > 0 else 0
    profit_growth = ((this_profit - last_profit) / last_profit * 100) if last_profit > 0 else 0
    
    # Daily breakdown for chart (both months aligned by day number)
    this_month_daily = {}
    last_month_daily = {}
    
    for sale in this_month_sales:
        day = sale.sale_date.day
        if day not in this_month_daily:
            this_month_daily[day] = 0
        this_month_daily[day] += sale.total_amount
    
    for sale in last_month_sales:
        day = sale.sale_date.day
        if day not in last_month_daily:
            last_month_daily[day] = 0
        last_month_daily[day] += sale.total_amount
    
    # Chart data
    max_day = max(this_month_last, last_month_end.day)
    chart_labels = list(range(1, max_day + 1))
    chart_this_month = [this_month_daily.get(d, 0) for d in chart_labels]
    chart_last_month = [last_month_daily.get(d, 0) for d in chart_labels]
    
    return render_template('reports/trends.html',
        this_month_start=this_month_start,
        last_month_start=last_month_start,
        this_revenue=this_revenue,
        last_revenue=last_revenue,
        this_transactions=this_transactions,
        last_transactions=last_transactions,
        this_profit=this_profit,
        last_profit=last_profit,
        revenue_growth=revenue_growth,
        transaction_growth=transaction_growth,
        profit_growth=profit_growth,
        chart_labels=chart_labels,
        chart_this_month=chart_this_month,
        chart_last_month=chart_last_month
    )


@reports.route('/margin-alerts')
def margin_alerts_report():
    """Items sold below cost (negative margin)."""
    period = request.args.get('period', 'this_month')
    start_date, end_date, period = get_date_range(period)
    
    # Get all sale items in range (excluding unlisted) with eager loading
    sale_items = db.session.query(SaleItem).join(Sale).options(
        joinedload(SaleItem.sale),
        joinedload(SaleItem.batch).joinedload(Batch.medicine)
    ).filter(
        func.date(Sale.sale_date) >= start_date,
        func.date(Sale.sale_date) <= end_date,
        SaleItem.batch_id.isnot(None)
    ).all()
    
    # Find items with negative margin
    alerts = []
    for item in sale_items:
        revenue, cost, profit = calculate_item_profit(item)
        
        if cost > 0 and profit < 0:  # Sold below cost
            alerts.append({
                'sale_id': item.sale_id,
                'sale_date': item.sale.sale_date,
                'medicine': item.batch.medicine.name,
                'batch': item.batch.batch_number,
                'quantity': item.quantity,
                'sold_price': item.price_at_sale,
                'cost_price': cost / item.quantity if item.quantity > 0 else 0,
                'loss': abs(profit)
            })
    
    # Sort by loss amount
    alerts.sort(key=lambda x: x['loss'], reverse=True)
    
    total_loss = sum(a['loss'] for a in alerts)
    
    return render_template('reports/margin_alerts.html',
        period=period,
        start_date=start_date,
        end_date=end_date,
        alerts=alerts,
        total_loss=total_loss,
        alert_count=len(alerts)
    )
