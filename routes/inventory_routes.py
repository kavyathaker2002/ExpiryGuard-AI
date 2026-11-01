from flask import Blueprint, render_template, request, jsonify, session
from database import get_db
from routes.auth_routes import login_required
from ai.expiry_predictor import calculate_days_until_expiry

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def index():
    user_id = session['user_id']
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('q', '').strip().lower()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, product_name, brand, category, package_size, mfg_date, expiry_date, barcode, quantity, price
        FROM products
        WHERE user_id = ?
        ORDER BY expiry_date ASC
    """, (user_id,))
    rows = cursor.fetchall()
    
    products_list = []
    for r in rows:
        days_left = calculate_days_until_expiry(r['expiry_date'])
        qty = r['quantity']
        
        # Determine status classification
        if days_left < 0:
            status = 'expired'
            badge_class = 'badge-danger'
            status_text = f"Expired ({abs(days_left)}d ago)"
        elif days_left == 0:
            status = 'today'
            badge_class = 'badge-danger'
            status_text = "Expires Today!"
        elif days_left <= 7:
            status = '7days'
            badge_class = 'badge-orange'
            status_text = f"Expiring in {days_left}d"
        elif days_left <= 15:
            status = '15days'
            badge_class = 'badge-amber'
            status_text = f"Expiring in {days_left}d"
        elif days_left <= 30:
            status = '30days'
            badge_class = 'badge-yellow'
            status_text = f"Expiring in {days_left}d"
        else:
            status = 'safe'
            badge_class = 'badge-success'
            status_text = f"Safe ({days_left}d left)"
            
        is_low_stock = (qty < 5)
        
        # Search filter
        if search_query:
            searchable = ' '.join((r['product_name'], r['brand'], r['category'], r['package_size'], r['barcode'])).lower()
            if search_query not in searchable:
                continue
                
        # Status tab filter
        if filter_type == 'expired' and status != 'expired':
            continue
        elif filter_type == '7days' and (days_left < 0 or days_left > 7):
            continue
        elif filter_type == '15days' and (days_left < 0 or days_left > 15):
            continue
        elif filter_type == '30days' and (days_left < 0 or days_left > 30):
            continue
        elif filter_type == 'low_stock' and not is_low_stock:
            continue
        elif filter_type == 'normal' and (days_left <= 30):
            continue
            
        products_list.append({
            "id": r['id'],
            "product_name": r['product_name'],
            "brand": r['brand'],
            "category": r['category'],
            "package_size": r['package_size'],
            "mfg_date": r['mfg_date'],
            "expiry_date": r['expiry_date'],
            "barcode": r['barcode'],
            "quantity": qty,
            "price": r['price'],
            "days_left": days_left,
            "status": status,
            "badge_class": badge_class,
            "status_text": status_text,
            "is_low_stock": is_low_stock
        })
        
    return render_template(
        'inventory/index.html',
        products=products_list,
        current_filter=filter_type,
        search_query=search_query,
        total_count=len(products_list)
    )

@inventory_bp.route('/api/product/update/<int:product_id>', methods=['POST'])
@login_required
def update_product(product_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    
    product_name = str(data.get('product_name', '')).strip()
    mfg_date = str(data.get('mfg_date', '')).strip()
    expiry_date = str(data.get('expiry_date', '')).strip()
    barcode = str(data.get('barcode', '')).strip()
    brand = str(data['brand']).strip()[:100] if 'brand' in data else None
    category = str(data['category']).strip()[:100] if 'category' in data else None
    package_size = str(data['package_size']).strip()[:100] if 'package_size' in data else None
    quantity_raw = data.get('quantity')
    price_raw = data.get('price')
    
    if not product_name or not barcode or not mfg_date or not expiry_date:
        return jsonify({"success": False, "message": "All fields are required."}), 400
        
    try:
        quantity = int(quantity_raw)
        price = float(price_raw)
        if quantity < 0 or price < 0:
            return jsonify({"success": False, "message": "Values cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid numeric values."}), 400

    db = get_db()
    cursor = db.cursor()
    
    # Check ownership
    cursor.execute("SELECT id FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    if not cursor.fetchone():
        return jsonify({"success": False, "message": "Product not found or unauthorized."}), 404
        
    # Check barcode conflict with another product
    cursor.execute("SELECT id FROM products WHERE user_id = ? AND barcode = ? AND id != ?", (user_id, barcode, product_id))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "Another product already uses this barcode."}), 400
        
    cursor.execute("""
        UPDATE products
        SET product_name = ?, brand = COALESCE(?, brand), category = COALESCE(?, category), package_size = COALESCE(?, package_size), mfg_date = ?, expiry_date = ?, barcode = ?, quantity = ?, price = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """, (product_name, brand, category, package_size, mfg_date, expiry_date, barcode, quantity, price, product_id, user_id))
    db.commit()
    
    return jsonify({"success": True, "message": "Product updated successfully!"})

@inventory_bp.route('/api/product/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT id, product_name FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    prod = cursor.fetchone()
    if not prod:
        return jsonify({"success": False, "message": "Product not found or unauthorized."}), 404
        
    cursor.execute("DELETE FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    db.commit()
    
    return jsonify({"success": True, "message": f"'{prod['product_name']}' deleted from inventory."})

@inventory_bp.route('/api/product/decrement/<int:product_id>', methods=['POST'])
@login_required
def decrement_product(product_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT id, product_name, quantity, price FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    prod = cursor.fetchone()
    if not prod:
        return jsonify({"success": False, "message": "Product not found or unauthorized."}), 404
        
    current_qty = prod['quantity']
    if current_qty <= 0:
        return jsonify({"success": False, "message": f"'{prod['product_name']}' is already at 0 stock."}), 400
        
    new_qty = current_qty - 1
    cursor.execute("""
        UPDATE products
        SET quantity = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """, (new_qty, product_id, user_id))
    
    # Also record 1 unit in sales table so analytics and sales logs stay consistent
    try:
        cursor.execute("""
            INSERT INTO sales (product_id, user_id, quantity_sold, unit_price, total_amount)
            VALUES (?, ?, 1, ?, ?)
        """, (product_id, user_id, prod['price'], prod['price']))
    except Exception:
        pass
        
    db.commit()
    return jsonify({
        "success": True,
        "product_id": product_id,
        "new_quantity": new_qty,
        "message": f"'{prod['product_name']}' quantity decreased to {new_qty}."
    })

@inventory_bp.route('/api/product/increment/<int:product_id>', methods=['POST'])
@login_required
def increment_product(product_id):
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT id, product_name, quantity FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    prod = cursor.fetchone()
    if not prod:
        return jsonify({"success": False, "message": "Product not found or unauthorized."}), 404
        
    new_qty = prod['quantity'] + 1
    cursor.execute("""
        UPDATE products
        SET quantity = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """, (new_qty, product_id, user_id))
    db.commit()
    return jsonify({
        "success": True,
        "product_id": product_id,
        "new_quantity": new_qty,
        "message": f"'{prod['product_name']}' quantity increased to {new_qty}."
    })
