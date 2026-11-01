from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Global pre-trained ML classifier for expiry risk assessment
_ml_model = None

def _get_or_train_model():
    global _ml_model
    if _ml_model is not None:
        return _ml_model
    
    # Train a baseline Random Forest on standard FMCG kirana inventory patterns
    # Features: [days_until_expiry, stock_quantity, daily_sales_rate, price, days_to_sellout_gap]
    # Label: 0 = Low Risk, 1 = Moderate Risk, 2 = High Risk of Expiry
    np.random.seed(42)
    X = []
    y = []
    
    # Generate representative retail grocery scenarios
    for _ in range(600):
        days_exp = np.random.randint(-5, 180)
        stock = np.random.randint(1, 100)
        sales_rate = np.random.uniform(0.1, 15.0)
        price = np.random.uniform(10, 500)
        
        days_to_sell = stock / sales_rate
        gap = days_exp - days_to_sell
        
        if days_exp <= 0:
            label = 2  # Expired
        elif gap < 0 or (days_exp <= 15 and days_to_sell > days_exp * 0.8):
            label = 2  # High risk of unsold waste
        elif days_exp <= 30 or gap < 7:
            label = 1  # Moderate risk
        else:
            label = 0  # Low risk
            
        X.append([days_exp, stock, sales_rate, price, gap])
        y.append(label)
        
    clf = RandomForestClassifier(n_estimators=30, random_state=42)
    clf.fit(X, y)
    _ml_model = clf
    return _ml_model

def calculate_days_until_expiry(expiry_date_str):
    """Calculate remaining days from today to expiry date (YYYY-MM-DD)."""
    try:
        exp_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        return (exp_date - today).days
    except Exception:
        return 0

def get_product_sales_velocity(cursor, product_id, user_id, days=14):
    """Compute average daily sales units over the last N days for this product."""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        SELECT COALESCE(SUM(quantity_sold), 0) as total_sold
        FROM sales
        WHERE product_id = ? AND user_id = ? AND sale_timestamp >= ?
    """, (product_id, user_id, start_date))
    row = cursor.fetchone()
    total_sold = row['total_sold'] if row else 0
    return round(total_sold / max(days, 1), 2)

def predict_expiry_risk(product, sales_rate):
    """
    Combines machine learning with transparent business logic
    Returns risk level ('high', 'medium', 'low', 'expired'),
    estimated days to sell out, waste probability, and reasoning.
    """
    days_left = calculate_days_until_expiry(product['expiry_date'])
    quantity = product['quantity']
    price = product['price']
    
    if days_left < 0:
        return {
            "risk_level": "expired",
            "days_left": days_left,
            "days_to_sellout": 0,
            "waste_probability": 100,
            "est_unsold_units": quantity,
            "reason_key": "status_expired",
            "recommendation_action": "dispose"
        }
    elif days_left == 0:
        return {
            "risk_level": "high",
            "days_left": 0,
            "days_to_sellout": 1,
            "waste_probability": 95,
            "est_unsold_units": max(0, quantity - int(sales_rate)),
            "reason_key": "status_today",
            "recommendation_action": "clearance"
        }
        
    effective_rate = max(sales_rate, 0.1)
    est_days_to_sell = round(quantity / effective_rate, 1)
    gap = days_left - est_days_to_sell
    
    # ML Model prediction
    try:
        model = _get_or_train_model()
        features = [[days_left, quantity, effective_rate, price, gap]]
        ml_probs = model.predict_proba(features)[0]
        # class 2 is high risk prob
        ml_high_risk_prob = round(float(ml_probs[min(2, len(ml_probs) - 1)]) * 100, 1)
    except Exception:
        ml_high_risk_prob = 50.0
        
    # Heuristic verification & explainability
    if est_days_to_sell > days_left:
        # Stock will not finish before expiry!
        risk_level = "high"
        unsold_estimate = max(1, int(quantity - (effective_rate * days_left)))
        waste_prob = max(ml_high_risk_prob, 75.0)
        reason_key = "ai_reason_high_risk"
    elif days_left <= 15:
        risk_level = "medium"
        unsold_estimate = 0
        waste_prob = max(ml_high_risk_prob, 45.0)
        reason_key = "status_urgent"
    else:
        risk_level = "low"
        unsold_estimate = 0
        waste_prob = min(ml_high_risk_prob, 25.0)
        reason_key = "ai_reason_safe"
        
    return {
        "risk_level": risk_level,
        "days_left": days_left,
        "days_to_sellout": est_days_to_sell,
        "waste_probability": round(waste_prob, 1),
        "est_unsold_units": unsold_estimate,
        "reason_key": reason_key,
        "recommendation_action": "discount" if risk_level == "high" else "monitor"
    }
