from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.main import db
from app.models import Category

categories = Blueprint('categories', __name__, url_prefix='/categories')


@categories.route('/')
def list_categories():
    """List all categories."""
    all_categories = Category.query.order_by(Category.name).all()
    return render_template('categories/list.html', categories=all_categories)


@categories.route('/add', methods=['GET', 'POST'])
def add_category():
    """Add new category."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Category name is required', 'danger')
            return render_template('categories/add.html')
        
        # Check duplicate
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash(f'Category "{name}" already exists', 'warning')
            return render_template('categories/add.html')
        
        category = Category(
            name=name,
            description=description or None
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Category "{name}" added successfully!', 'success')
        return redirect(url_for('categories.list_categories'))
    
    return render_template('categories/add.html')


@categories.route('/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    """Edit existing category."""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Category name is required', 'danger')
            return render_template('categories/edit.html', category=category)
        
        # Check duplicate (excluding current)
        existing = Category.query.filter(
            Category.name == name,
            Category.id != category_id
        ).first()
        if existing:
            flash(f'Category "{name}" already exists', 'warning')
            return render_template('categories/edit.html', category=category)
        
        category.name = name
        category.description = description or None
        
        db.session.commit()
        
        flash(f'Category "{name}" updated successfully!', 'success')
        return redirect(url_for('categories.list_categories'))
    
    return render_template('categories/edit.html', category=category)


@categories.route('/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    """Delete a category (only if no medicines use it)."""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has medicines
    if category.medicines:
        flash(f'Cannot delete "{category.name}" - it has {len(category.medicines)} medicine(s) assigned.', 'danger')
        return redirect(url_for('categories.list_categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{category.name}" has been deleted.', 'success')
    return redirect(url_for('categories.list_categories'))
