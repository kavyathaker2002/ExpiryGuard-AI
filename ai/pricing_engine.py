from ai.expiry_predictor import calculate_days_until_expiry

def get_pricing_recommendation(product, sales_rate):
    """
    Computes dynamic discount recommendations based on shelf life and stock movement.
    Provides suggested discount %, suggested new price in ₹, and clear rationale.
    """
    days_left = calculate_days_until_expiry(product['expiry_date'])
    current_price = float(product['price'])
    quantity = int(product['quantity'])
    
    if days_left < 0:
        return {
            "has_discount": False,
            "discount_percent": 0,
            "current_price": current_price,
            "suggested_price": current_price,
            "reason_en": "Product has expired. Do not sell for consumption. Return to supplier or safely discard.",
            "reason_hi": "उत्पाद एक्सपायर हो चुका है। इसे न बेचें, सप्लायर को वापस करें या नष्ट करें।",
            "reason_mr": "वस्तूची मुदत संपली आहे. ती विकू नका, पुरवठादाराला परत करा किंवा नष्ट करा.",
            "urgency": "expired"
        }
    elif days_left == 0:
        discount = 50
        suggested = max(1.0, round(current_price * 0.5, 0))
        return {
            "has_discount": True,
            "discount_percent": discount,
            "current_price": current_price,
            "suggested_price": suggested,
            "reason_en": "Expires TODAY! Offer 50% clearance discount to avoid 100% loss.",
            "reason_hi": "आज ही एक्सपायर हो रहा है! १००% नुकसान से बचने के लिए ५०% छूट पर बेचें।",
            "reason_mr": "आजच मुदत संपत आहे! पूर्ण नुकसान टाळण्यासाठी ५०% सवलत देऊन विका.",
            "urgency": "critical"
        }
    elif days_left <= 4:
        discount = 40
        suggested = max(1.0, round(current_price * 0.6, 0))
        return {
            "has_discount": True,
            "discount_percent": discount,
            "current_price": current_price,
            "suggested_price": suggested,
            "reason_en": f"Only {days_left} days left! 40% discount will attract quick buyers at shop counter.",
            "reason_hi": f"केवल {days_left} दिन शेष हैं! काउंटर पर ४०% छूट रखकर जल्दी बेचें।",
            "reason_mr": f"फक्त {days_left} दिवस शिल्लक आहेत! काउंटरवर ४०% सवलत देऊन लगेच विका.",
            "urgency": "critical"
        }
    elif days_left <= 10:
        discount = 25
        suggested = max(1.0, round(current_price * 0.75, 0))
        return {
            "has_discount": True,
            "discount_percent": discount,
            "current_price": current_price,
            "suggested_price": suggested,
            "reason_en": f"Expires in {days_left} days. 25% discount helps liquidate {quantity} units smoothly.",
            "reason_hi": f"{days_left} दिनों में एक्सपायर होगा। २५% छूट से {quantity} पैकेट आसानी से बिक जाएंगे।",
            "reason_mr": f"{days_left} दिवसांत मुदत संपेल. २५% सवलत दिल्यास {quantity} नग सहज विकले जातील.",
            "urgency": "urgent"
        }
    elif days_left <= 25:
        # Check if sales rate is slow
        days_to_sell = quantity / max(sales_rate, 0.1)
        if days_to_sell > days_left * 0.7:
            discount = 15
            suggested = max(1.0, round(current_price * 0.85, 0))
            return {
                "has_discount": True,
                "discount_percent": discount,
                "current_price": current_price,
                "suggested_price": suggested,
                "reason_en": f"Slow sales rate detected. 15% discount will accelerate sales before {days_left} days.",
                "reason_hi": f"बिक्री धीमी है। १५% छूट देने से {days_left} दिन से पहले माल निकल जाएगा।",
                "reason_mr": f"विक्रीचा वेग कमी आहे. १५% सवलत दिल्यास {days_left} दिवसांपूर्वी माल संपेल.",
                "urgency": "warning"
            }
            
    return {
        "has_discount": False,
        "discount_percent": 0,
        "current_price": current_price,
        "suggested_price": current_price,
        "reason_en": "Normal pricing. Stock is moving satisfactorily with healthy expiry.",
        "reason_hi": "सामान्य कीमत। स्टॉक सुरक्षित है और समय पर बिक रहा है।",
        "reason_mr": "सामान्य किंमत. स्टॉक सुरक्षित आहे आणि योग्य वेगाने विकला जात आहे.",
        "urgency": "safe"
    }
