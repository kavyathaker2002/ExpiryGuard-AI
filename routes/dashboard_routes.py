from datetime import datetime, date
from flask import Blueprint, render_template, session
from database import get_db
from routes.auth_routes import login_required
from ai.expiry_predictor import calculate_days_until_expiry

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Fetch all products belonging to this shop
    cursor.execute("""
        SELECT id, product_name, mfg_date, expiry_date, barcode, quantity, price
        FROM products
        WHERE user_id = ?
        ORDER BY expiry_date ASC
    """, (user_id,))
    products = cursor.fetchall()
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_date = datetime.now().date()
    
    total_products = len(products)
    total_stock_qty = sum(p['quantity'] for p in products)
    total_inventory_value = sum(p['quantity'] * p['price'] for p in products)
    
    expired_count = 0
    nearing_expiry_count = 0  # <= 30 days and >= 0
    low_stock_count = 0       # < 5 units
    urgent_alerts = []
    
    for p in products:
        days_left = calculate_days_until_expiry(p['expiry_date'])
        qty = p['quantity']
        
        if days_left < 0:
            expired_count += 1
            urgent_alerts.append({
                "product": p,
                "days_left": days_left,
                "urgency": "expired",
                "label_key": "status_expired"
            })
        elif days_left <= 30:
            nearing_expiry_count += 1
            if days_left <= 7:
                urgent_alerts.append({
                    "product": p,
                    "days_left": days_left,
                    "urgency": "critical" if days_left <= 3 else "urgent",
                    "label_key": "status_today" if days_left == 0 else "status_critical"
                })
                
        if qty < 5 and days_left >= 0:
            low_stock_count += 1
            
    # Fetch Today's sales
    cursor.execute("""
        SELECT COALESCE(SUM(quantity_sold), 0) as units_sold,
               COALESCE(SUM(total_amount), 0) as revenue
        FROM sales
        WHERE user_id = ? AND date(sale_timestamp) = date('now')
    """, (user_id,))
    sales_today = cursor.fetchone()
    units_sold_today = sales_today['units_sold'] if sales_today else 0
    revenue_today = sales_today['revenue'] if sales_today else 0.0
    
    stats = {
        "total_products": total_products,
        "total_stock_qty": total_stock_qty,
        "total_inventory_value": round(total_inventory_value, 2),
        "nearing_expiry_count": nearing_expiry_count,
        "expired_count": expired_count,
        "low_stock_count": low_stock_count,
        "units_sold_today": units_sold_today,
        "revenue_today": round(revenue_today, 2)
    }
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        urgent_alerts=urgent_alerts[:6]  # show top 6 urgent alerts
    )
