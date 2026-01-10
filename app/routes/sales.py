from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db
from app.models.sale import Sale, SaleItem
from app.models.batch import Batch
from app.models.medicine import Medicine
from datetime import datetime

bp = Blueprint('sales', __name__, url_prefix='/sales')


@bp.route('/')
def list_sales():
    """List all sales with filters."""
    page = request.args.get('page', 1, type=int)
    date_filter = request.args.get('date', '')
    
    query = Sale.query.order_by(Sale.sale_date.desc())
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Sale.sale_date) == filter_date)
        except ValueError:
            pass
    
    sales = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('sales/list.html', sales=sales, date_filter=date_filter)


@bp.route('/new')
def new_sale():
    """New sale page with search and cart."""
    return render_template('sales/new.html')


@bp.route('/create', methods=['POST'])
def create_sale():
    """Create a new sale from cart items."""
    data = request.get_json()
    
    if not data or 'items' not in data or not data['items']:
        return jsonify({'success': False, 'error': 'No items in cart'}), 400
    
    try:
        # Create the sale
        sale = Sale(
            customer_name=data.get('customer_name', ''),
            customer_phone=data.get('customer_phone', '')
        )
        db.session.add(sale)
        db.session.flush()  # Get the sale ID
        
        total_amount = 0
        
        for item in data['items']:
            # Validate quantity and price
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Invalid quantity. Must be a positive number.'}), 400
            
            if not isinstance(unit_price, (int, float)) or unit_price < 0:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Invalid price. Must be a non-negative number.'}), 400
            
            quantity = int(quantity)
            unit_price = float(unit_price)
            
            if item.get('is_unlisted'):
                # Unlisted item
                sale_item = SaleItem(
                    sale_id=sale.id,
                    batch_id=None,
                    item_name=item.get('name', 'Unlisted Item')[:100],
                    quantity=quantity,
                    price_at_sale=unit_price
                )
            else:
                # Listed item with batch
                batch = Batch.query.get(item['batch_id'])
                if not batch:
                    db.session.rollback()
                    return jsonify({'success': False, 'error': f'Batch not found: {item["batch_id"]}'}), 400
                
                if batch.stock_quantity < quantity:
                    db.session.rollback()
                    return jsonify({
                        'success': False, 
                        'error': f'Insufficient stock for {batch.medicine.name}. Available: {batch.stock_quantity}'
                    }), 400
                
                # Deduct stock
                batch.stock_quantity -= quantity
                
                sale_item = SaleItem(
                    sale_id=sale.id,
                    batch_id=batch.id,
                    quantity=quantity,
                    price_at_sale=unit_price
                )
            
            total_amount += sale_item.subtotal
            db.session.add(sale_item)
        
        sale.total_amount = total_amount
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'sale_id': sale.id,
            'message': f'Sale #{sale.id} created successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<int:sale_id>')
def view_sale(sale_id):
    """View sale details."""
    sale = Sale.query.get_or_404(sale_id)
    return render_template('sales/view.html', sale=sale)
