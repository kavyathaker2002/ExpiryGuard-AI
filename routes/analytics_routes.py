from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, session
from database import get_db
from routes.auth_routes import login_required
from ai.expiry_predictor import calculate_days_until_expiry

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # 1. Product totals
    cursor.execute("""
        SELECT id, product_name, mfg_date, expiry_date, quantity, price
        FROM products
        WHERE user_id = ?
    """, (user_id,))
    products = cursor.fetchall()
    
    total_products = len(products)
    total_stock_qty = sum(p['quantity'] for p in products)
    total_inventory_value = sum(p['quantity'] * p['price'] for p in products)
    
    expired_count = 0
    expiring_soon_count = 0
    at_risk_value = 0.0
    
    for p in products:
        d = calculate_days_until_expiry(p['expiry_date'])
        if d < 0:
            expired_count += 1
            at_risk_value += (p['quantity'] * p['price'])
        elif d <= 15:
            expiring_soon_count += 1
            at_risk_value += (p['quantity'] * p['price'])
            
    # 2. Total Sales summary
    cursor.execute("""
        SELECT COALESCE(SUM(quantity_sold), 0) as total_units_sold,
               COALESCE(SUM(total_amount), 0) as total_revenue,
               COUNT(id) as total_transactions
        FROM sales
        WHERE user_id = ?
    """, (user_id,))
    sales_stats = cursor.fetchone()
    total_revenue = sales_stats['total_revenue'] if sales_stats else 0.0
    total_units_sold = sales_stats['total_units_sold'] if sales_stats else 0
    total_transactions = sales_stats['total_transactions'] if sales_stats else 0
    avg_sale_val = (total_revenue / total_transactions) if total_transactions > 0 else 0.0
    
    summary = {
        "total_products": total_products,
        "total_stock_qty": total_stock_qty,
        "total_inventory_value": round(total_inventory_value, 2),
        "expired_count": expired_count,
        "expiring_soon_count": expiring_soon_count,
        "at_risk_value": round(at_risk_value, 2),
        "total_revenue": round(total_revenue, 2),
        "total_units_sold": total_units_sold,
        "avg_sale_value": round(avg_sale_val, 2)
    }
    
    return render_template('analytics/index.html', summary=summary)

@analytics_bp.route('/api/analytics/data')
@login_required
def get_analytics_data():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # 1. Past 7 days sales trend
    today = datetime.now().date()
    days_labels = []
    daily_revenue = []
    daily_units = []
    
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        label_str = target_date.strftime('%d %b')
        days_labels.append(label_str)
        
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as rev,
                   COALESCE(SUM(quantity_sold), 0) as units
            FROM sales
            WHERE user_id = ? AND date(sale_timestamp) = ?
        """, (user_id, date_str))
        row = cursor.fetchone()
        daily_revenue.append(round(row['rev'], 2) if row else 0.0)
        daily_units.append(row['units'] if row else 0)
        
    # 2. Expiry status distribution
    cursor.execute("SELECT expiry_date, quantity FROM products WHERE user_id = ?", (user_id,))
    prods = cursor.fetchall()
    
    expired = 0
    urgent_7d = 0
    warning_15d = 0
    warning_30d = 0
    safe = 0
    
    for p in prods:
        d = calculate_days_until_expiry(p['expiry_date'])
        if d < 0:
            expired += 1
        elif d <= 7:
            urgent_7d += 1
        elif d <= 15:
            warning_15d += 1
        elif d <= 30:
            warning_30d += 1
        else:
            safe += 1
            
    # 3. Top 5 selling products
    cursor.execute("""
        SELECT p.product_name,
               SUM(s.quantity_sold) as total_sold,
               SUM(s.total_amount) as total_rev
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE s.user_id = ?
        GROUP BY p.id, p.product_name
        ORDER BY total_sold DESC
        LIMIT 5
    """, (user_id,))
    top_prods_rows = cursor.fetchall()
    top_products = [
        {"name": r['product_name'], "units": r['total_sold'], "revenue": round(r['total_rev'], 2)}
        for r in top_prods_rows
    ]
    
    return jsonify({
        "sales_trend": {
            "labels": days_labels,
            "revenue": daily_revenue,
            "units": daily_units
        },
        "expiry_distribution": {
            "labels": ["Expired", "≤ 7 Days", "8 - 15 Days", "16 - 30 Days", "Safe (> 30d)"],
            "data": [expired, urgent_7d, warning_15d, warning_30d, safe]
        },
        "top_products": top_products
    })
