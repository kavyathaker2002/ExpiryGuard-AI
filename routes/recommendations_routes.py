from flask import Blueprint, render_template, request, jsonify, session
from database import get_db
from routes.auth_routes import login_required
from ai.expiry_predictor import predict_expiry_risk, get_product_sales_velocity, calculate_days_until_expiry
from ai.pricing_engine import get_pricing_recommendation
from ai.restock_engine import get_restock_recommendations

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/recommendations')
@login_required
def index():
    user_id = session['user_id']
    current_lang = session.get('lang', 'en')
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT id, product_name, mfg_date, expiry_date, barcode, quantity, price
        FROM products
        WHERE user_id = ?
        ORDER BY expiry_date ASC
    """, (user_id,))
    products = cursor.fetchall()
    
    ai_risk_cards = []
    pricing_cards = []
    products_with_stats = []
    
    for p in products:
        sales_rate = get_product_sales_velocity(cursor, p['id'], user_id, days=14)
        risk_info = predict_expiry_risk(p, sales_rate)
        pricing_info = get_pricing_recommendation(p, sales_rate)
        
        products_with_stats.append({
            "product": p,
            "sales_rate": sales_rate
        })
        
        ai_risk_cards.append({
            "product": p,
            "sales_rate": sales_rate,
            "risk": risk_info
        })
        
        # Only show discount suggestions if a discount is recommended and stock is > 0
        if pricing_info['has_discount'] and p['quantity'] > 0:
            pricing_cards.append({
                "product": p,
                "pricing": pricing_info
            })
            
    restock_advice = get_restock_recommendations(products_with_stats)
    
    return render_template(
        'recommendations/index.html',
        ai_risk_cards=ai_risk_cards,
        pricing_cards=pricing_cards,
        restock_advice=restock_advice,
        current_lang=current_lang
    )

@recommendations_bp.route('/api/pricing/apply-discount', methods=['POST'])
@login_required
def apply_discount():
    user_id = session['user_id']
    data = request.get_json() or {}
    
    product_id = data.get('product_id')
    new_price_raw = data.get('new_price')
    
    if not product_id or new_price_raw is None:
        return jsonify({"success": False, "message": "Missing product ID or price."}), 400
        
    try:
        new_price = float(new_price_raw)
        if new_price <= 0:
            return jsonify({"success": False, "message": "Price must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid price value."}), 400

    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT id, product_name, price FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    product = cursor.fetchone()
    if not product:
        return jsonify({"success": False, "message": "Product not found or unauthorized."}), 404
        
    cursor.execute("""
        UPDATE products
        SET price = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """, (new_price, product_id, user_id))
    db.commit()
    
    return jsonify({
        "success": True,
        "message": f"Discount applied! {product['product_name']} price updated to ₹{new_price:.2f}.",
        "new_price": new_price
    })
