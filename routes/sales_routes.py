from flask import Blueprint, render_template, request, jsonify, session
from database import get_db
from routes.auth_routes import login_required

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/quick-sales')
@login_required
def quick_sales():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Fetch recent sales for today
    cursor.execute("""
        SELECT s.id, s.quantity_sold, s.unit_price, s.total_amount, s.sale_timestamp,
               p.product_name, p.barcode, p.quantity as current_stock
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE s.user_id = ? AND date(s.sale_timestamp) = date('now')
        ORDER BY s.sale_timestamp DESC
        LIMIT 10
    """, (user_id,))
    recent_sales = cursor.fetchall()
    
    return render_template('sales/quick_sales.html', recent_sales=recent_sales)

@sales_bp.route('/api/sales/lookup/<barcode>')
@login_required
def lookup_for_sale(barcode):
    user_id = session['user_id']
    clean_barcode = barcode.strip()
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT id, product_name, barcode, quantity, price, expiry_date
        FROM products
        WHERE user_id = ? AND barcode = ?
    """, (user_id, clean_barcode))
    product = cursor.fetchone()
    
    if not product:
        return jsonify({
            "found": False,
            "message": f"Product with barcode '{clean_barcode}' not found in your inventory."
        }), 404
        
    return jsonify({
        "found": True,
        "product": {
            "id": product['id'],
            "product_name": product['product_name'],
            "barcode": product['barcode'],
            "available_quantity": product['quantity'],
            "price": product['price'],
            "expiry_date": product['expiry_date']
        }
    })

@sales_bp.route('/api/sales/record', methods=['POST'])
@login_required
def record_sale():
    user_id = session['user_id']
    data = request.get_json() or {}
    
    barcode = str(data.get('barcode', '')).strip()
    quantity_sold_raw = data.get('quantity_sold', 1)
    
    if not barcode:
        return jsonify({"success": False, "message": "Barcode is required."}), 400
        
    try:
        quantity_sold = int(quantity_sold_raw)
        if quantity_sold <= 0:
            return jsonify({"success": False, "message": "Quantity sold must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid quantity sold."}), 400

    db = get_db()
    cursor = db.cursor()
    
    try:
        # Atomic Transaction starts
        cursor.execute("BEGIN IMMEDIATE")
        
        # 1. Fetch current product and verify shop ownership
        cursor.execute("""
            SELECT id, product_name, quantity, price
            FROM products
            WHERE user_id = ? AND barcode = ?
        """, (user_id, barcode))
        product = cursor.fetchone()
        
        if not product:
            db.rollback()
            return jsonify({"success": False, "message": "Product not found in your inventory."}), 404
            
        current_stock = product['quantity']
        unit_price = product['price']
        product_name = product['product_name']
        product_id = product['id']
        
        # 2. Strict validation: cannot oversell
        if quantity_sold > current_stock:
            db.rollback()
            return jsonify({
                "success": False,
                "message": f"Cannot sell {quantity_sold} items. Only {current_stock} available in stock!"
            }), 400
            
        remaining_stock = current_stock - quantity_sold
        total_amount = round(quantity_sold * unit_price, 2)
        
        # 3. Deduct stock from products
        cursor.execute("""
            UPDATE products
            SET quantity = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (remaining_stock, product_id, user_id))
        
        # 4. Insert into sales table
        cursor.execute("""
            INSERT INTO sales (product_id, user_id, quantity_sold, unit_price, total_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, user_id, quantity_sold, unit_price, total_amount))
        
        # Commit transaction atomically
        db.commit()
        
        unit_text = "packets" if quantity_sold > 1 else "packet"
        success_msg = f"Sale complete! {quantity_sold} {unit_text} sold. {remaining_stock} remaining in stock."
        
        return jsonify({
            "success": True,
            "message": success_msg,
            "product_name": product_name,
            "sold_qty": quantity_sold,
            "remaining_stock": remaining_stock,
            "total_amount": total_amount
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"Transaction failed: {str(e)}"}), 500
