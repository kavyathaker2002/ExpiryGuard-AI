from ai.expiry_predictor import calculate_days_until_expiry

def get_restock_recommendations(products_with_stats):
    """
    Generate actionable restocking and waste-reduction advice for the shopkeeper.
    Categorizes products into:
    - Reorder Urgently (Low stock & safe expiry)
    - Halt Reordering (Excess stock or near expiry)
    - Front-Counter Placement (Urgent expiry liquidation)
    """
    reorder_list = []
    halt_list = []
    front_counter_list = []
    
    for item in products_with_stats:
        p = item['product']
        days_left = calculate_days_until_expiry(p['expiry_date'])
        qty = int(p['quantity'])
        sales_rate = item.get('sales_rate', 0.0)
        
        # 1. Front counter placement (Expiring in <= 7 days, stock > 0)
        if 0 <= days_left <= 7 and qty > 0:
            front_counter_list.append({
                "product_name": p['product_name'],
                "barcode": p['barcode'],
                "days_left": days_left,
                "quantity": qty,
                "advice_en": f"Move to billing counter or entrance display. Prioritize selling these {qty} units first.",
                "advice_hi": f"बिलिंग काउंटर या सामने रखें। इन {qty} पैकेटों को पहले बेचने पर ध्यान दें।",
                "advice_mr": f"बिलिंग काउंटर किंवा प्रवेशद्वारावर ठेवा. हे {qty} नग आधी विकण्यावर भर द्या.",
                "type": "front_counter"
            })
            
        # 2. Halt Reorder (If days_left <= 30 and qty > 10, or sales rate is slow)
        if 0 < days_left <= 30 and qty >= 8:
            halt_list.append({
                "product_name": p['product_name'],
                "barcode": p['barcode'],
                "days_left": days_left,
                "quantity": qty,
                "advice_en": f"Do NOT reorder new stock yet. You already have {qty} units expiring in {days_left} days.",
                "advice_hi": f"नया माल बिल्कुल न मंगाएं। दुकान में पहले से {qty} पैकेट हैं जो {days_left} दिनों में एक्सपायर होंगे।",
                "advice_mr": f"नवीन माल मागवू नका. दुकानात आधीच {qty} नग आहेत ज्यांची मुदत {days_left} दिवसांत संपत आहे.",
                "type": "halt_order"
            })
            
        # 3. Urgent Reorder (Low stock < 5, but expiry > 45 days or fresh)
        if 0 <= qty <= 4 and days_left > 30:
            reorder_list.append({
                "product_name": p['product_name'],
                "barcode": p['barcode'],
                "days_left": days_left,
                "quantity": qty,
                "advice_en": f"Low stock alert! Only {qty} units left. Place wholesale order to avoid stockout.",
                "advice_hi": f"स्टॉक कम है! केवल {qty} पैकेट बचे हैं। ग्राहकों की मांग पूरी करने के लिए नया माल मंगाएं।",
                "advice_mr": f"कमी स्टॉक! फक्त {qty} नग शिल्लक आहेत. ग्राहकांसाठी नवीन मालाची ऑर्डर द्या.",
                "type": "reorder_needed"
            })
            
    return {
        "front_counter": front_counter_list,
        "halt_orders": halt_list,
        "reorder_needed": reorder_list
    }
