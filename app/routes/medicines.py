from flask import Blueprint, render_template, request
from app.main import db
from app.models import Category, Medicine, Batch

medicines = Blueprint('medicines', __name__)


@medicines.route('/')
def list_medicines():
    """List all medicines with filters."""
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '').strip()
    stock_filter = request.args.get('stock', '')  # 'low', 'out', 'ok'
    
    # Base query
    query = Medicine.query.filter_by(is_active=True)
    
    # Apply category filter
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Apply search filter
    if search:
        query = query.filter(Medicine.name.ilike(f'%{search}%'))
    
    # Get all medicines (we'll filter stock in Python due to computed property)
    medicines_list = query.order_by(Medicine.name).all()
    
    # Apply stock filter (computed property, can't filter in SQL)
    if stock_filter == 'low':
        medicines_list = [m for m in medicines_list if m.is_low_stock and not m.is_out_of_stock]
    elif stock_filter == 'out':
        medicines_list = [m for m in medicines_list if m.is_out_of_stock]
    elif stock_filter == 'ok':
        medicines_list = [m for m in medicines_list if not m.is_low_stock]
    
    # Get categories for filter dropdown
    categories = Category.query.order_by(Category.name).all()
    
    return render_template('medicines/list.html',
        medicines=medicines_list,
        categories=categories,
        selected_category=category_id,
        search=search,
        stock_filter=stock_filter
    )


@medicines.route('/<int:medicine_id>')
def view_medicine(medicine_id):
    """View medicine details with batches."""
    medicine = Medicine.query.get_or_404(medicine_id)
    
    # Get batches sorted by expiry date
    batches = Batch.query.filter_by(
        medicine_id=medicine_id,
        is_active=True
    ).order_by(Batch.expiry_date).all()
    
    return render_template('medicines/view.html',
        medicine=medicine,
        batches=batches
    )
