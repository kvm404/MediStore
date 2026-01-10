"""API routes for AJAX/JSON endpoints."""
from flask import Blueprint, jsonify, request
from app.models import Medicine, Batch

api = Blueprint('api', __name__)


@api.route('/medicines/search')
def search_medicines():
    """
    Search medicines by name for autocomplete.
    Query params:
        q: search query (min 2 chars)
        limit: max results (default 10)
    Returns JSON list of matching medicines with batch info.
    """
    query = request.args.get('q', '').strip()
    limit = min(request.args.get('limit', 10, type=int), 50)  # Cap at 50
    
    if len(query) < 2:
        return jsonify([])
    
    # Search medicines by name (case-insensitive)
    medicines = Medicine.query.filter(
        Medicine.is_active == True,
        Medicine.name.ilike(f'%{query}%')
    ).order_by(Medicine.name).limit(limit).all()
    
    results = []
    for med in medicines:
        # Get available batches (in stock, not expired, sorted by expiry)
        available_batches = [b for b in med.batches 
                           if b.is_active and b.stock_quantity > 0 and not b.is_expired]
        available_batches.sort(key=lambda x: x.expiry_date)
        
        results.append({
            'id': med.id,
            'name': med.name,
            'generic_name': med.generic_name or '',
            'category': med.category.name if med.category else 'Uncategorized',
            'packing_type': med.packing_type,
            'units_per_pack': med.units_per_pack,
            'total_stock': med.total_stock,
            'batches': [{
                'id': b.id,
                'batch_number': b.batch_number,
                'expiry_date': b.expiry_date.strftime('%Y-%m-%d'),
                'days_until_expiry': b.days_until_expiry,
                'stock_quantity': b.stock_quantity,
                'mrp': b.mrp,
                'unit_price': round(b.unit_price, 2)
            } for b in available_batches]
        })
    
    return jsonify(results)


@api.route('/batches/<int:medicine_id>')
def get_batches(medicine_id):
    """
    Get all available batches for a medicine.
    Used when user selects a medicine in sales form.
    """
    medicine = Medicine.query.get_or_404(medicine_id)
    
    # Get available batches (in stock, not expired)
    batches = Batch.query.filter(
        Batch.medicine_id == medicine_id,
        Batch.is_active == True,
        Batch.stock_quantity > 0
    ).order_by(Batch.expiry_date).all()
    
    # Filter out expired in Python (for accurate date comparison)
    available_batches = [b for b in batches if not b.is_expired]
    
    return jsonify({
        'medicine': {
            'id': medicine.id,
            'name': medicine.name,
            'units_per_pack': medicine.units_per_pack,
            'packing_type': medicine.packing_type
        },
        'batches': [{
            'id': b.id,
            'batch_number': b.batch_number,
            'expiry_date': b.expiry_date.strftime('%Y-%m-%d'),
            'days_until_expiry': b.days_until_expiry,
            'stock_quantity': b.stock_quantity,
            'mrp': b.mrp,
            'unit_price': round(b.unit_price, 2)
        } for b in available_batches]
    })
