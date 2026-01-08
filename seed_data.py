"""
Seed script to add dummy data for testing.
Run with: FLASK_APP=run.py uv run python seed_data.py
"""
from datetime import datetime, timedelta
from app.main import create_app, db
from app.models import Category, Medicine, Batch, Sale, SaleItem

app = create_app()

def seed_categories():
    """Add medicine categories."""
    categories = [
        Category(name="Tablet", description="Solid oral dosage forms"),
        Category(name="Capsule", description="Gelatin-coated medicines"),
        Category(name="Syrup", description="Liquid oral medicines"),
        Category(name="Injection", description="Injectable medicines"),
        Category(name="Drops", description="Eye/Ear drops"),
        Category(name="Cream/Ointment", description="Topical applications"),
        Category(name="Inhaler", description="Respiratory medicines"),
        Category(name="Surgical", description="Surgical items and dressings"),
    ]
    db.session.add_all(categories)
    db.session.commit()
    print(f"✅ Added {len(categories)} categories")
    return categories

def seed_medicines(categories):
    """Add sample medicines."""
    # Get category references
    tablet = next(c for c in categories if c.name == "Tablet")
    capsule = next(c for c in categories if c.name == "Capsule")
    syrup = next(c for c in categories if c.name == "Syrup")
    injection = next(c for c in categories if c.name == "Injection")
    drops = next(c for c in categories if c.name == "Drops")
    cream = next(c for c in categories if c.name == "Cream/Ointment")
    
    medicines = [
        # Tablets (strip of 10)
        Medicine(name="Paracetamol 500mg", category=tablet, packing_type="Strip", 
                 units_per_pack=10, manufacturer="Cipla", generic_name="Paracetamol"),
        Medicine(name="Dolo 650", category=tablet, packing_type="Strip", 
                 units_per_pack=15, manufacturer="Micro Labs", generic_name="Paracetamol"),
        Medicine(name="Crocin Advance", category=tablet, packing_type="Strip", 
                 units_per_pack=15, manufacturer="GSK", generic_name="Paracetamol"),
        Medicine(name="Azithromycin 500mg", category=tablet, packing_type="Strip", 
                 units_per_pack=3, manufacturer="Cipla", generic_name="Azithromycin"),
        Medicine(name="Cetirizine 10mg", category=tablet, packing_type="Strip", 
                 units_per_pack=10, manufacturer="Dr Reddy's", generic_name="Cetirizine"),
        Medicine(name="Pantoprazole 40mg", category=tablet, packing_type="Strip", 
                 units_per_pack=10, manufacturer="Sun Pharma", generic_name="Pantoprazole"),
        Medicine(name="Metformin 500mg", category=tablet, packing_type="Strip", 
                 units_per_pack=10, manufacturer="USV", generic_name="Metformin"),
        Medicine(name="Amoxicillin 500mg", category=capsule, packing_type="Strip", 
                 units_per_pack=10, manufacturer="Cipla", generic_name="Amoxicillin"),
        
        # Syrups (single bottle)
        Medicine(name="Benadryl Cough Syrup", category=syrup, packing_type="Bottle", 
                 units_per_pack=1, manufacturer="J&J", generic_name="Diphenhydramine"),
        Medicine(name="Grilinctus Syrup", category=syrup, packing_type="Bottle", 
                 units_per_pack=1, manufacturer="Franco-Indian", generic_name="Dextromethorphan"),
        Medicine(name="Digene Syrup", category=syrup, packing_type="Bottle", 
                 units_per_pack=1, manufacturer="Abbott", generic_name="Antacid"),
        
        # Injections
        Medicine(name="Insulin Mixtard", category=injection, packing_type="Vial", 
                 units_per_pack=1, manufacturer="Novo Nordisk", generic_name="Insulin"),
        Medicine(name="Diclofenac Injection", category=injection, packing_type="Ampoule", 
                 units_per_pack=1, manufacturer="Cipla", generic_name="Diclofenac"),
        
        # Drops
        Medicine(name="Otrivin Nasal Drops", category=drops, packing_type="Bottle", 
                 units_per_pack=1, manufacturer="Novartis", generic_name="Xylometazoline"),
        Medicine(name="Tears Naturale Eye Drops", category=drops, packing_type="Bottle", 
                 units_per_pack=1, manufacturer="Alcon", generic_name="Artificial Tears"),
        
        # Creams
        Medicine(name="Betadine Ointment", category=cream, packing_type="Tube", 
                 units_per_pack=1, manufacturer="Win Medicare", generic_name="Povidone Iodine"),
        Medicine(name="Candid Cream", category=cream, packing_type="Tube", 
                 units_per_pack=1, manufacturer="Glenmark", generic_name="Clotrimazole"),
    ]
    db.session.add_all(medicines)
    db.session.commit()
    print(f"✅ Added {len(medicines)} medicines")
    return medicines

def seed_batches(medicines):
    """Add sample batches with varying expiry dates."""
    today = datetime.now().date()
    batches = []
    
    for med in medicines:
        # Add 1-3 batches per medicine
        batch_count = 2 if med.category.name in ["Tablet", "Capsule"] else 1
        
        for i in range(batch_count):
            # Varying expiry: some expired, some expiring soon, some fresh
            if i == 0:
                expiry = today + timedelta(days=365)  # 1 year ahead
                stock = 100 * med.units_per_pack  # 100 packs worth
            else:
                expiry = today + timedelta(days=45)  # Expiring soon
                stock = 20 * med.units_per_pack  # 20 packs worth
            
            batch = Batch(
                medicine=med,
                batch_number=f"B{med.id:02d}-{i+1:02d}",
                expiry_date=expiry,
                purchase_price=50.0 + (med.id * 5),  # Dummy purchase price
                mrp=80.0 + (med.id * 8),  # Dummy MRP
                stock_quantity=stock,
            )
            batches.append(batch)
    
    # Add one expired batch for testing
    expired_batch = Batch(
        medicine=medicines[0],  # Paracetamol
        batch_number="B01-EXPIRED",
        expiry_date=today - timedelta(days=30),  # Expired 30 days ago
        purchase_price=40.0,
        mrp=60.0,
        stock_quantity=50,
        is_active=False,
    )
    batches.append(expired_batch)
    
    db.session.add_all(batches)
    db.session.commit()
    print(f"✅ Added {len(batches)} batches")
    return batches

def seed_sales(batches):
    """Add sample sales with both listed and unlisted items."""
    today = datetime.now()
    sales = []
    
    # Sale 1: Listed items only
    sale1 = Sale(
        sale_date=today - timedelta(days=2),
        total_amount=0,
        customer_name="Rahul Sharma"
    )
    db.session.add(sale1)
    db.session.flush()  # Get ID
    
    # Add items to sale1
    item1 = SaleItem(sale=sale1, batch=batches[0], quantity=10, price_at_sale=batches[0].unit_price)
    item2 = SaleItem(sale=sale1, batch=batches[2], quantity=5, price_at_sale=batches[2].unit_price)
    sale1.total_amount = item1.subtotal + item2.subtotal
    
    # Sale 2: Mixed (listed + unlisted)
    sale2 = Sale(
        sale_date=today - timedelta(days=1),
        total_amount=0,
        customer_name="Priya Patel"
    )
    db.session.add(sale2)
    db.session.flush()
    
    item3 = SaleItem(sale=sale2, batch=batches[4], quantity=20, price_at_sale=batches[4].unit_price)
    item4 = SaleItem(sale=sale2, batch_id=None, item_name="Vicks VapoRub", quantity=2, price_at_sale=75.0)  # Unlisted
    item5 = SaleItem(sale=sale2, batch_id=None, item_name="Band-Aid", quantity=5, price_at_sale=10.0)  # Unlisted
    sale2.total_amount = item3.subtotal + item4.subtotal + item5.subtotal
    
    # Sale 3: Unlisted only (for testing quick sales)
    sale3 = Sale(
        sale_date=today,
        total_amount=0,
        customer_name=None  # Anonymous customer
    )
    db.session.add(sale3)
    db.session.flush()
    
    item6 = SaleItem(sale=sale3, batch_id=None, item_name="Strepsils", quantity=1, price_at_sale=50.0)
    item7 = SaleItem(sale=sale3, batch_id=None, item_name="Moov Spray", quantity=1, price_at_sale=180.0)
    sale3.total_amount = item6.subtotal + item7.subtotal
    
    db.session.add_all([item1, item2, item3, item4, item5, item6, item7])
    db.session.commit()
    
    print(f"✅ Added 3 sales with 7 sale items (4 listed, 3 unlisted)")

def seed_all():
    """Run all seed functions."""
    with app.app_context():
        # Clear existing data
        print("\n🗑️  Clearing existing data...")
        SaleItem.query.delete()
        Sale.query.delete()
        Batch.query.delete()
        Medicine.query.delete()
        Category.query.delete()
        db.session.commit()
        
        print("\n📦 Seeding database with dummy data...")
        print("─" * 50)
        
        categories = seed_categories()
        medicines = seed_medicines(categories)
        batches = seed_batches(medicines)
        seed_sales(batches)
        
        print("─" * 50)
        print("\n✅ Database seeded successfully!\n")
        
        # Summary
        print("📊 Summary:")
        print(f"   Categories: {Category.query.count()}")
        print(f"   Medicines:  {Medicine.query.count()}")
        print(f"   Batches:    {Batch.query.count()}")
        print(f"   Sales:      {Sale.query.count()}")
        print(f"   SaleItems:  {SaleItem.query.count()}")

if __name__ == "__main__":
    seed_all()
