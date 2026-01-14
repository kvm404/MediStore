from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.main import db
from app.models import Category, Medicine, Batch
from datetime import datetime

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
        # Escape LIKE special characters
        escaped_search = search.replace('%', r'\%').replace('_', r'\_')
        query = query.filter(Medicine.name.ilike(f'%{escaped_search}%', escape='\\'))
    
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


@medicines.route('/add', methods=['GET', 'POST'])
def add_medicine():
    """Add new medicine to catalog."""
    categories = Category.query.order_by(Category.name).all()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        generic_name = request.form.get('generic_name', '').strip()
        category_id = request.form.get('category_id', type=int)
        manufacturer = request.form.get('manufacturer', '').strip()
        units_per_pack = request.form.get('units_per_pack', 1, type=int)
        packing_type = request.form.get('packing_type', 'Strip')
        min_stock_level = request.form.get('min_stock_level', 10, type=int)
        description = request.form.get('description', '').strip()
        
        # Validation
        if not name:
            flash('Medicine name is required', 'danger')
            return render_template('medicines/add.html', categories=categories)
        
        if not category_id:
            flash('Category is required', 'danger')
            return render_template('medicines/add.html', categories=categories)
        
        # Check duplicate
        existing = Medicine.query.filter_by(name=name).first()
        if existing:
            flash(f'Medicine "{name}" already exists', 'warning')
            return render_template('medicines/add.html', categories=categories)
        
        # Create medicine
        medicine = Medicine(
            name=name,
            generic_name=generic_name or None,
            category_id=category_id,
            manufacturer=manufacturer or None,
            units_per_pack=units_per_pack,
            packing_type=packing_type,
            min_stock_level=min_stock_level,
            description=description or None
        )
        
        db.session.add(medicine)
        db.session.commit()
        
        flash(f'Medicine "{name}" added successfully!', 'success')
        return redirect(url_for('medicines.view_medicine', medicine_id=medicine.id))
    
    return render_template('medicines/add.html', categories=categories)


@medicines.route('/<int:medicine_id>/add-batch', methods=['GET', 'POST'])
def add_batch(medicine_id):
    """Add new batch to existing medicine."""
    medicine = Medicine.query.get_or_404(medicine_id)
    
    if request.method == 'POST':
        batch_number = request.form.get('batch_number', '').strip()
        expiry_date_str = request.form.get('expiry_date', '')
        mrp = request.form.get('mrp', type=float)
        purchase_price = request.form.get('purchase_price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        
        # Validation
        errors = []
        if not batch_number:
            errors.append('Batch number is required')
        if not expiry_date_str:
            errors.append('Expiry date is required')
        if not mrp or mrp <= 0:
            errors.append('Valid MRP is required')
        if stock_quantity is None or stock_quantity < 0:
            errors.append('Valid stock quantity is required')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('medicines/add_batch.html', medicine=medicine)
        
        # Parse expiry date
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid expiry date format', 'danger')
            return render_template('medicines/add_batch.html', medicine=medicine)
        
        # Check duplicate batch
        existing = Batch.query.filter_by(
            medicine_id=medicine_id, 
            batch_number=batch_number
        ).first()
        if existing:
            flash(f'Batch "{batch_number}" already exists for this medicine', 'warning')
            return render_template('medicines/add_batch.html', medicine=medicine)
        
        # Create batch
        batch = Batch(
            medicine_id=medicine_id,
            batch_number=batch_number,
            expiry_date=expiry_date,
            mrp=mrp,
            purchase_price=purchase_price or None,
            stock_quantity=stock_quantity
        )
        
        db.session.add(batch)
        db.session.commit()
        
        flash(f'Batch "{batch_number}" added with {stock_quantity} units!', 'success')
        return redirect(url_for('medicines.view_medicine', medicine_id=medicine_id))
    
    return render_template('medicines/add_batch.html', medicine=medicine)


@medicines.route('/<int:medicine_id>/edit', methods=['GET', 'POST'])
def edit_medicine(medicine_id):
    """Edit existing medicine."""
    medicine = Medicine.query.get_or_404(medicine_id)
    categories = Category.query.order_by(Category.name).all()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        generic_name = request.form.get('generic_name', '').strip()
        category_id = request.form.get('category_id', type=int)
        manufacturer = request.form.get('manufacturer', '').strip()
        units_per_pack = request.form.get('units_per_pack', 1, type=int)
        packing_type = request.form.get('packing_type', 'Strip')
        min_stock_level = request.form.get('min_stock_level', 10, type=int)
        description = request.form.get('description', '').strip()
        
        # Validation
        if not name:
            flash('Medicine name is required', 'danger')
            return render_template('medicines/edit.html', medicine=medicine, categories=categories)
        
        if not category_id:
            flash('Category is required', 'danger')
            return render_template('medicines/edit.html', medicine=medicine, categories=categories)
        
        # Check duplicate (excluding current)
        existing = Medicine.query.filter(
            Medicine.name == name,
            Medicine.id != medicine_id
        ).first()
        if existing:
            flash(f'Medicine "{name}" already exists', 'warning')
            return render_template('medicines/edit.html', medicine=medicine, categories=categories)
        
        # Update medicine
        medicine.name = name
        medicine.generic_name = generic_name or None
        medicine.category_id = category_id
        medicine.manufacturer = manufacturer or None
        medicine.units_per_pack = units_per_pack
        medicine.packing_type = packing_type
        medicine.min_stock_level = min_stock_level
        medicine.description = description or None
        
        db.session.commit()
        
        flash(f'Medicine "{name}" updated successfully!', 'success')
        return redirect(url_for('medicines.view_medicine', medicine_id=medicine.id))
    
    return render_template('medicines/edit.html', medicine=medicine, categories=categories)


@medicines.route('/<int:medicine_id>/delete', methods=['POST'])
def delete_medicine(medicine_id):
    """Soft delete a medicine (deactivate)."""
    medicine = Medicine.query.get_or_404(medicine_id)
    
    medicine.is_active = False
    db.session.commit()
    
    flash(f'Medicine "{medicine.name}" has been deleted.', 'success')
    return redirect(url_for('medicines.list_medicines'))


@medicines.route('/batch/<int:batch_id>/edit', methods=['GET', 'POST'])
def edit_batch(batch_id):
    """Edit existing batch (stock adjustment, price update)."""
    batch = Batch.query.get_or_404(batch_id)
    medicine = batch.medicine
    
    if request.method == 'POST':
        batch_number = request.form.get('batch_number', '').strip()
        expiry_date_str = request.form.get('expiry_date', '')
        mrp = request.form.get('mrp', type=float)
        purchase_price = request.form.get('purchase_price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        
        # Validation
        errors = []
        if not batch_number:
            errors.append('Batch number is required')
        if not expiry_date_str:
            errors.append('Expiry date is required')
        if not mrp or mrp <= 0:
            errors.append('Valid MRP is required')
        if stock_quantity is None or stock_quantity < 0:
            errors.append('Valid stock quantity is required')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('medicines/edit_batch.html', batch=batch, medicine=medicine)
        
        # Parse expiry date
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid expiry date format', 'danger')
            return render_template('medicines/edit_batch.html', batch=batch, medicine=medicine)
        
        # Check duplicate batch (excluding current)
        existing = Batch.query.filter(
            Batch.medicine_id == medicine.id,
            Batch.batch_number == batch_number,
            Batch.id != batch_id
        ).first()
        if existing:
            flash(f'Batch "{batch_number}" already exists for this medicine', 'warning')
            return render_template('medicines/edit_batch.html', batch=batch, medicine=medicine)
        
        # Update batch
        batch.batch_number = batch_number
        batch.expiry_date = expiry_date
        batch.mrp = mrp
        batch.purchase_price = purchase_price or None
        batch.stock_quantity = stock_quantity
        
        db.session.commit()
        
        flash(f'Batch "{batch_number}" updated successfully!', 'success')
        return redirect(url_for('medicines.view_medicine', medicine_id=medicine.id))
    
    return render_template('medicines/edit_batch.html', batch=batch, medicine=medicine)


@medicines.route('/batch/<int:batch_id>/delete', methods=['POST'])
def delete_batch(batch_id):
    """Soft delete a batch (deactivate)."""
    batch = Batch.query.get_or_404(batch_id)
    medicine_id = batch.medicine_id
    
    batch.is_active = False
    db.session.commit()
    
    flash(f'Batch "{batch.batch_number}" has been deleted.', 'success')
    return redirect(url_for('medicines.view_medicine', medicine_id=medicine_id))
