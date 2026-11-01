"""
ExpiryGuard AI — True AI Conversational Assistant Engine
Understands natural language questions in English, Hindi (हिन्दी), and Marathi (मराठी).
Maintains conversation memory, queries live inventory & sales, and generates varied, context-aware responses.
"""
import re
import random
from datetime import datetime, timedelta
from ai.expiry_predictor import calculate_days_until_expiry, get_product_sales_velocity
from ai.pricing_engine import get_pricing_recommendation

# Conversation history storage (per user session)
_conversation_history = {}

def get_history(user_id):
    if user_id not in _conversation_history:
        _conversation_history[user_id] = []
    return _conversation_history[user_id]

def append_history(user_id, role, text):
    hist = get_history(user_id)
    hist.append({"role": role, "text": text, "time": datetime.now()})
    # Keep last 10 messages for context
    if len(hist) > 10:
        _conversation_history[user_id] = hist[-10:]

def process_ai_chat(user_msg, user_id, shop_name, lang, cursor):
    """
    Main True AI reasoning pipeline.
    1. Analyzes intent & parameters (product name, timeframe, query type).
    2. Gathers dynamic store metrics from SQLite database.
    3. Synthesizes a unique, helpful, conversational answer in the requested language.
    """
    clean_msg = user_msg.strip()
    msg_lower = clean_msg.lower()
    
    # Store user message in history
    append_history(user_id, "user", clean_msg)
    
    # Fetch live store inventory
    cursor.execute("""
        SELECT id, product_name, mfg_date, expiry_date, barcode, quantity, price
        FROM products
        WHERE user_id = ?
        ORDER BY expiry_date ASC
    """, (user_id,))
    products = cursor.fetchall()
    
    # Calculate live inventory aggregates
    total_products = len(products)
    total_units = sum(p['quantity'] for p in products)
    total_val = sum(p['quantity'] * p['price'] for p in products)
    
    expired_list = [p for p in products if calculate_days_until_expiry(p['expiry_date']) < 0]
    urgent_7d_list = [p for p in products if 0 <= calculate_days_until_expiry(p['expiry_date']) <= 7]
    urgent_15d_list = [p for p in products if 0 <= calculate_days_until_expiry(p['expiry_date']) <= 15]
    low_stock_list = [p for p in products if p['quantity'] < 5 and calculate_days_until_expiry(p['expiry_date']) >= 0]

    # Fetch sales today
    cursor.execute("""
        SELECT COALESCE(SUM(quantity_sold), 0) as units_sold,
               COALESCE(SUM(total_amount), 0) as revenue
        FROM sales
        WHERE user_id = ? AND date(sale_timestamp) = date('now')
    """, (user_id,))
    today_sales = cursor.fetchone()
    sales_units_today = today_sales['units_sold'] if today_sales else 0
    sales_rev_today = today_sales['revenue'] if today_sales else 0.0

    # Fetch top selling item
    cursor.execute("""
        SELECT p.product_name, SUM(s.quantity_sold) as sold_qty
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE s.user_id = ?
        GROUP BY p.id, p.product_name
        ORDER BY sold_qty DESC
        LIMIT 1
    """, (user_id,))
    top_item = cursor.fetchone()
    top_seller_name = top_item['product_name'] if top_item else "No sales yet"

    # -------------------------------------------------------------
    # INTENT 1: Specific Product Check
    # (Matches any specific product name in store inventory)
    # -------------------------------------------------------------
    for p in products:
        p_name = p['product_name'].lower()
        # Extract meaningful keywords from product name (e.g., 'milk', 'bread', 'paneer', 'maggi')
        keywords = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', p_name) if w not in ['gold', 'pack', 'pure', 'with', 'plus', 'gram', 'litre']]
        hindi_keywords = {
            'milk': ['दूध', 'मिल्क'], 'bread': ['ब्रेड', 'पाव'], 'paneer': ['पनीर'],
            'atta': ['आटा'], 'oil': ['तेल'], 'salt': ['नमक'], 'tea': ['चाय'],
            'biscuit': ['बिस्कुट', 'बिस्किट'], 'noodle': ['मैगी', 'नूडल'], 'yogurt': ['दही', 'योगर्ट']
        }
        marathi_keywords = {
            'milk': ['दूध'], 'bread': ['ब्रेड', 'पाव'], 'paneer': ['पनीर'],
            'atta': ['पीठ', 'आटा'], 'oil': ['तेल'], 'salt': ['मीठ'], 'tea': ['चहा'],
            'biscuit': ['बिस्किट'], 'noodle': ['मॅगी'], 'yogurt': ['दही']
        }

        matched = any(k in msg_lower for k in keywords) or (p['barcode'] in msg_lower)
        # Check translated words
        for en_key, trans_list in (hindi_keywords if lang == 'hi' else marathi_keywords).items():
            if en_key in p_name and any(tk in msg_lower for tk in trans_list):
                matched = True

        # Let explicit store-wide requests reach their own handlers even when
        # the wording also includes a product name.
        if any(k in msg_lower for k in ['sold', 'sales', 'revenue', 'discount', 'offer', 'scan', 'qr', 'phone', 'waste', 'tips']):
            matched = False

        if matched:
            days_left = calculate_days_until_expiry(p['expiry_date'])
            status_badge = "EXPIRED" if days_left < 0 else (f"Expiring in {days_left} days" if days_left <= 15 else "Fresh & Safe")

            # Answer the attribute the user asked for instead of repeating the
            # same full stock card for every question about this product.
            if lang == 'en':
                if any(k in msg_lower for k in ['how many', 'quantity', 'stock', 'units', 'packets', 'left', 'available']):
                    reply = f"📦 <strong>{p['product_name']}</strong>: {p['quantity']} units are in stock."
                elif any(k in msg_lower for k in ['price', 'cost', 'mrp', 'sell for', 'selling']):
                    reply = f"💰 <strong>{p['product_name']}</strong> is priced at ₹{p['price']:.2f} per unit."
                elif any(k in msg_lower for k in ['expiry', 'expire', 'fresh', 'safe', 'when']):
                    state = f"expired {abs(days_left)} days ago" if days_left < 0 else f"expires on {p['expiry_date']} ({days_left} days left)"
                    reply = f"⏳ <strong>{p['product_name']}</strong> {state}." + (" Do not sell it for consumption." if days_left < 0 else "")
                elif any(k in msg_lower for k in ['barcode', 'code']):
                    reply = f"🏷️ The barcode for <strong>{p['product_name']}</strong> is <code>{p['barcode']}</code>."
                else:
                    reply = (f"📦 <strong>{p['product_name']}</strong>: {p['quantity']} units in stock at ₹{p['price']:.2f} each.<br>"
                             f"Expiry: {p['expiry_date']} ({'expired' if days_left < 0 else str(days_left) + ' days remaining'}).<br>Barcode: <code>{p['barcode']}</code>")
                actions = [{"label": "Open Quick Sales", "url": "/quick-sales"}, {"label": "View Inventory", "url": "/inventory"}]
                append_history(user_id, "assistant", reply)
                return reply, actions
            
            if lang == 'hi':
                reply = (
                    f"📦 <strong>{p['product_name']}</strong> का स्टॉक विवरण:<br><br>"
                    f"• <strong>दुकान में मौजूद:</strong> {p['quantity']} पैकेट<br>"
                    f"• <strong>बिक्री कीमत:</strong> ₹{p['price']:.2f}<br>"
                    f"• <strong>एक्सपायरी तारीख:</strong> {p['expiry_date']} ("
                )
                if days_left < 0:
                    reply += f"<span style='color:#dc2626;'>{abs(days_left)} दिन पहले एक्सपायर हो चुका है!</span>)<br>"
                    reply += "⚠️ <em>सलाह: इसे ग्राहकों को न बेचें, सप्लायर को वापस करें।</em>"
                elif days_left <= 7:
                    reply += f"<span style='color:#ea580c;'>केवल {days_left} दिन बचे हैं!</span>)<br>"
                    reply += "💡 <em>सलाह: काउंटर पर सबसे आगे रखकर जल्दी बेचें।</em>"
                else:
                    reply += f"<span style='color:#059669;'>सुरक्षित, {days_left} दिन शेष</span>)"
            elif lang == 'mr':
                reply = (
                    f"📦 <strong>{p['product_name']}</strong> चा स्टॉक तपशील:<br><br>"
                    f"• <strong>दुकानात उपलब्ध:</strong> {p['quantity']} नग<br>"
                    f"• <strong>विक्री किंमत:</strong> ₹{p['price']:.2f}<br>"
                    f"• <strong>मुदत संपण्याची तारीख:</strong> {p['expiry_date']} ("
                )
                if days_left < 0:
                    reply += f"<span style='color:#dc2626;'>{abs(days_left)} दिवसांपूर्वी मुदत संपली आहे!</span>)<br>"
                elif days_left <= 7:
                    reply += f"<span style='color:#ea580c;'>फक्त {days_left} दिवस शिल्लक आहेत!</span>)<br>"
                else:
                    reply += f"<span style='color:#059669;'>सुरक्षित, {days_left} दिवस शिल्लक</span>)"
            else:
                reply = (
                    f"📦 Live Stock Details for <strong>{p['product_name']}</strong>:<br><br>"
                    f"• <strong>Current In-Store Quantity:</strong> {p['quantity']} units<br>"
                    f"• <strong>Selling Price:</strong> ₹{p['price']:.2f} per unit<br>"
                    f"• <strong>Barcode:</strong> <code>{p['barcode']}</code><br>"
                    f"• <strong>Expiry Date:</strong> {p['expiry_date']} ("
                )
                if days_left < 0:
                    reply += f"<span style='color:#dc2626; font-weight:700;'>EXPIRED {abs(days_left)}d ago!</span>)<br>"
                    reply += "⚠️ <em>Recommendation: Do not sell for consumption. Safely return to distributor.</em>"
                elif days_left <= 7:
                    reply += f"<span style='color:#ea580c; font-weight:700;'>Only {days_left}d remaining!</span>)<br>"
                    reply += "💡 <em>Recommendation: Offer a quick discount or place near checkout counter.</em>"
                else:
                    reply += f"<span style='color:#059669;'>Fresh & Safe with {days_left} days shelf life</span>)"

            actions = [{"label": f"Sell {p['product_name'][:14]}...", "url": f"/quick-sales"}]
            append_history(user_id, "assistant", reply)
            return reply, actions

    # -------------------------------------------------------------
    # INTENT 2: What is Expired?
    # -------------------------------------------------------------
    if any(k in msg_lower for k in ['expired', 'खराब', 'मुदत संपली', 'एक्सपायर']):
        if expired_list:
            if lang == 'hi':
                reply = f"🚨 <strong>Gupta Chaat & Stores</strong> में <strong>{len(expired_list)} उत्पाद एक्सपायर</strong> हो चुके हैं:<br><br>"
                for p in expired_list:
                    days_ago = abs(calculate_days_until_expiry(p['expiry_date']))
                    reply += f"• <strong>{p['product_name']}</strong> — {p['quantity']} पैकेट (एक्सपायरी: {p['expiry_date']}, {days_ago} दिन पहले)<br>"
                reply += "<br>🛑 <em>सलाह: फूड सेफ्टी के नियमों के अनुसार इन्हें तुरंत अलमारियों से हटा दें।</em>"
            elif lang == 'mr':
                reply = f"🚨 <strong>Gupta Chaat & Stores</strong> मध्ये <strong>{len(expired_list)} वस्तूंची मुदत संपलेली</strong> आहे:<br><br>"
                for p in expired_list:
                    days_ago = abs(calculate_days_until_expiry(p['expiry_date']))
                    reply += f"• <strong>{p['product_name']}</strong> — {p['quantity']} नग ({days_ago} दिवसांपूर्वी मुदत संपली)<br>"
                reply += "<br>🛑 <em>सल्ला: या वस्तू त्वरित शेल्फवरून काढून टाका.</em>"
            else:
                reply = f"🚨 There are currently <strong>{len(expired_list)} expired products</strong> in your inventory:<br><br>"
                for p in expired_list:
                    days_ago = abs(calculate_days_until_expiry(p['expiry_date']))
                    reply += f"• <strong>{p['product_name']}</strong> — {p['quantity']} units (Expired {days_ago}d ago on {p['expiry_date']})<br>"
                reply += "<br>🛑 <em>Action: Segregate these items immediately for wholesale distributor credit or safe disposal.</em>"
            actions = [{"label": "Open Expired List", "url": "/inventory?filter=expired"}]
        else:
            if lang == 'hi':
                reply = "🎉 <strong>शानदार!</strong> आपकी दुकान में इस समय कोई भी सामान एक्सपायर नहीं है। सारा स्टॉक सुरक्षित है।"
            elif lang == 'mr':
                reply = "🎉 <strong>छान!</strong> आपल्या दुकानात सध्या कोणतीही वस्तू मुदत संपलेली नाही. सर्व माल सुरक्षित आहे."
            else:
                reply = "🎉 <strong>Zero Waste Alert!</strong> You have no expired products in your store right now. Great inventory control!"
            actions = [{"label": "View Inventory", "url": "/inventory"}]
        append_history(user_id, "assistant", reply)
        return reply, actions

    # -------------------------------------------------------------
    # INTENT 3: Expiring Soon (Within 7 or 15 days)
    # -------------------------------------------------------------
    if any(k in msg_lower for k in ['soon', 'week', 'days', 'नजदीक', 'जल्द', 'लवकर', 'संपणार', 'आठवडा']):
        target_list = urgent_7d_list if ('7' in msg_lower or 'week' in msg_lower or 'आठव' in msg_lower) else urgent_15d_list
        if target_list:
            if lang == 'hi':
                reply = f"⏳ <strong>अगले कुछ दिनों में एक्सपायर होने वाले {len(target_list)} उत्पाद:</strong><br><br>"
                for p in target_list:
                    d_left = calculate_days_until_expiry(p['expiry_date'])
                    reply += f"• <strong>{p['product_name']}</strong> — {p['quantity']} पैकेट (<strong>{d_left} दिन</strong> बाकी, ₹{p['price']})<br>"
                reply += "<br>💡 <em>स्मार्ट टिप: इन सामानों पर २५% से ४०% छूट रखकर काउंटर के सामने रखें ताकि ये एक्सपायर होने से पहले बिक जाएं!</em>"
            elif lang == 'mr':
                reply = f"⏳ <strong>लवकरच मुदत संपणाऱ्या {len(target_list)} वस्तू:</strong><br><br>"
                for p in target_list:
                    d_left = calculate_days_until_expiry(p['expiry_date'])
                    reply += f"• <strong>{p['product_name']}</strong> — {p['quantity']} नग (<strong>{d_left} दिवस</strong> शिल्लक)<br>"
                reply += "<br>💡 <em>स्मार्ट सल्ला: या वस्तू काऊंटरवर पुढे ठेवा किंवा सवलत देऊन लगेच विका.</em>"
            else:
                reply = f"⏳ <strong>Urgent Expiry Watch ({len(target_list)} products needing attention):</strong><br><br>"
                for p in target_list:
                    d_left = calculate_days_until_expiry(p['expiry_date'])
                    reply += f"• <strong>{p['product_name']}</strong> — {p['quantity']} units left (<strong>{d_left} days</strong> until expiry)<br>"
                reply += "<br>💡 <em>Smart AI Advice: Move these items to the front billing counter or apply a 25%–40% dynamic clearance discount to recover your capital before they expire!</em>"
            actions = [{"label": "Apply Dynamic Discounts", "url": "/recommendations"}, {"label": "Quick Sell", "url": "/quick-sales"}]
        else:
            reply = "No items are expiring within this timeframe. Your stock is fresh!" if lang == 'en' else "इस अवधि में कोई भी सामान एक्सपायर नहीं हो रहा। आपका स्टॉक सुरक्षित है!"
            actions = [{"label": "Full Stock List", "url": "/inventory"}]
        append_history(user_id, "assistant", reply)
        return reply, actions

    # -------------------------------------------------------------
    # INTENT 4: Low Stock / Reorder Needed
    # -------------------------------------------------------------
    if any(k in msg_lower for k in ['low', 'short', 'reorder', 'कम स्टॉक', 'कमी', 'माल संपला', 'ऑर्डर']):
        if low_stock_list:
            if lang == 'hi':
                reply = f"📉 <strong>कम स्टॉक अलर्ट! इन {len(low_stock_list)} उत्पादों का माल खत्म होने वाला है:</strong><br><br>"
                for p in low_stock_list:
                    reply += f"• <strong>{p['product_name']}</strong>: केवल <strong>{p['quantity']} पैकेट</strong> बचे हैं (कीमत ₹{p['price']})<br>"
                reply += "<br>📦 <em>ग्राहकों की मांग बनी रहे, इसलिए होलसेलर से नया स्टॉक मंगाने का आर्डर दें।</em>"
            elif lang == 'mr':
                reply = f"📉 <strong>कमी स्टॉक सूचना! या {len(low_stock_list)} वस्तू संपत आल्या आहेत:</strong><br><br>"
                for p in low_stock_list:
                    reply += f"• <strong>{p['product_name']}</strong>: फक्त <strong>{p['quantity']} नग</strong> शिल्लक आहेत<br>"
                reply += "<br>📦 <em>होलसेलरकडून नवीन मालाची ऑर्डर द्या.</em>"
            else:
                reply = f"📉 <strong>Restock Alert! {len(low_stock_list)} products are running critically low (&lt; 5 units):</strong><br><br>"
                for p in low_stock_list:
                    reply += f"• <strong>{p['product_name']}</strong> — Only <strong>{p['quantity']} units</strong> left in shop<br>"
                reply += "<br>📦 <em>Advice: Place an order with your wholesale distributor today to avoid customer stockouts.</em>"
            actions = [{"label": "View Low Stock", "url": "/inventory?filter=low_stock"}]
        else:
            reply = "All products currently have plenty of stock!" if lang == 'en' else "दुकान में सभी सामान पर्याप्त मात्रा में उपलब्ध हैं!"
            actions = []
        append_history(user_id, "assistant", reply)
        return reply, actions

    # -------------------------------------------------------------
    # INTENT 5: Sales, Revenue, Earnings & Performance
    # -------------------------------------------------------------
    if any(k in msg_lower for k in ['sale', 'revenue', 'earning', 'profit', 'today', 'बिक्री', 'कमाई', 'विक्री', 'आज', 'नफा']):
        if lang == 'hi':
            reply = (
                f"💰 <strong>Gupta Chaat & Stores — आज का बिक्री और कमाई का हिसाब:</strong><br><br>"
                f"• <strong>आज बिके पैकेट:</strong> {sales_units_today} पैकेट<br>"
                f"• <strong>आज की कुल कमाई:</strong> ₹{sales_rev_today:.2f}<br>"
                f"• <strong>दुकान में कुल इन्वेंटरी मूल्य:</strong> ₹{total_val:.2f}<br>"
                f"• <strong>सबसे ज्यादा बिकने वाला सामान:</strong> {top_seller_name}<br><br>"
                f"📈 <em>आप एनालिटिक्स पेज पर जाकर पिछले ७ दिनों के ग्राफ़ और ट्रेंड देख सकते हैं।</em>"
            )
        elif lang == 'mr':
            reply = (
                f"💰 <strong>Gupta Chaat & Stores — आजचा विक्री व उत्पन्न अहवाल:</strong><br><br>"
                f"• <strong>आज विकलेले नग:</strong> {sales_units_today} नग<br>"
                f"• <strong>आजची कमाई:</strong> ₹{sales_rev_today:.2f}<br>"
                f"• <strong>एकूण साठ्याचे मूल्य:</strong> ₹{total_val:.2f}<br>"
                f"• <strong>सर्वाधिक विकली जाणारी वस्तू:</strong> {top_seller_name}<br><br>"
                f"📈 <em>अहवाल पेजवर जाऊन विक्रीचे विश्लेषण पाहू शकता.</em>"
            )
        else:
            reply = (
                f"💰 <strong>Today's Store Performance for Gupta Chaat & Stores:</strong><br><br>"
                f"• <strong>Items Sold Today:</strong> {sales_units_today} units<br>"
                f"• <strong>Gross Revenue Today:</strong> ₹{sales_rev_today:.2f}<br>"
                f"• <strong>Total On-Shelf Inventory Valuation:</strong> ₹{total_val:.2f}<br>"
                f"• <strong>Top Moving Product:</strong> {top_seller_name}<br><br>"
                f"📈 <em>Open Analytics to view daily trend charts and product performance breakdown.</em>"
            )
        actions = [{"label": "Open Quick Sales", "url": "/quick-sales"}, {"label": "Analytics Charts", "url": "/analytics"}]
        append_history(user_id, "assistant", reply)
        return reply, actions

    # -------------------------------------------------------------
    # INTENT 6: Dynamic Pricing & Discount Recommendations
    # -------------------------------------------------------------
    if any(k in msg_lower for k in ['discount', 'offer', 'clearance', 'price', 'छूट', 'सवलत', 'सस्ता', 'ऑफर']):
        discount_cards = []
        for p in products:
            rate = get_product_sales_velocity(cursor, p['id'], user_id)
            rec = get_pricing_recommendation(p, rate)
            if rec['has_discount'] and p['quantity'] > 0:
                discount_cards.append((p, rec))

        if discount_cards:
            if lang == 'hi':
                reply = f"🏷️ <strong>एआई डायनामिक छूट के सुझाव (नुकसान रोकने के लिए):</strong><br><br>"
                for p, rec in discount_cards[:4]:
                    reply += f"• <strong>{p['product_name']}</strong>: ₹{rec['current_price']} ➔ <strong>₹{rec['suggested_price']}</strong> ({rec['discount_percent']}% छूट)<br>"
                reply += "<br>✅ <em>फायदा: छूट देने से ग्राहक जल्दी खरीदेंगे और एक्सपायरी के कारण होने वाले १००% नुकसान से आप बच जाएंगे!</em>"
            elif lang == 'mr':
                reply = f"🏷️ <strong>एआय सवलत सूचना (नासाडी टाळण्यासाठी):</strong><br><br>"
                for p, rec in discount_cards[:4]:
                    reply += f"• <strong>{p['product_name']}</strong>: ₹{rec['current_price']} ➔ <strong>₹{rec['suggested_price']}</strong> ({rec['discount_percent']}% सवलत)<br>"
                reply += "<br>✅ <em>फायदा: १००% नुकसान होण्यापेक्षा योग्य सवलत देऊन माल लगेच विकला जाईल.</em>"
            else:
                reply = f"🏷️ <strong>AI Dynamic Clearance Discount Recommendations:</strong><br><br>"
                for p, rec in discount_cards[:4]:
                    reply += f"• <strong>{p['product_name']}</strong>: ₹{rec['current_price']} ➔ <strong>₹{rec['suggested_price']}</strong> ({rec['discount_percent']}% OFF)<br>"
                reply += "<br>✅ <em>Why this works: Offering a targeted discount now attracts impulse buyers and avoids losing 100% of the wholesale cost once expired.</em>"
            actions = [{"label": "Review & Apply Discounts", "url": "/recommendations"}]
        else:
            reply = "No items need discounts right now. All products are moving normally!" if lang == 'en' else "फिलहाल किसी भी सामान पर डिस्काउंट देने की आवश्यकता नहीं है।"
            actions = []
        append_history(user_id, "assistant", reply)
        return reply, actions

    # -------------------------------------------------------------
    # INTENT 7: How to Use / Scanner / QR Code Guidance
    # -------------------------------------------------------------
    if any(k in msg_lower for k in ['how', 'guide', 'scan', 'qr', 'phone', 'कैसे', 'कसे', 'फोन', 'स्कैन']):
        if lang == 'hi':
            reply = (
                "📱 <strong>स्मार्ट स्कैनर और मोबाइल इस्तेमाल गाइड:</strong><br><br>"
                "१. <strong>फोन पर खोलने के लिए:</strong> स्कैनर पेज पर दिए गए <strong>QR कोड</strong> को अपने मोबाइल कैमरे से स्कैन करें। ऐप तुरंत फोन पर खुल जाएगा बिना कोई IP टाइप किए!<br>"
                "२. <strong>सामान स्कैन करने के लिए:</strong> 'Take Photo / Upload' पर टैप करें। पैकेट की फोटो लेते ही बारकोड, नाम, तारीखें और कीमत अपने-आप भर जाएंगी!<br>"
                "३. <strong>तेज़ बिक्री के लिए:</strong> 'Quick Sales' पेज पर बारकोड स्कैन करें और १-टैप में बिक्री दर्ज करें।"
            )
        elif lang == 'mr':
            reply = (
                "📱 <strong>स्कॅनर व मोबाईल वापर मार्गदर्शक:</strong><br><br>"
                "१. <strong>मोबाईलवर सुरू करण्यासाठी:</strong> स्कॅनर पेजवरील <strong>QR कोड</strong> मोबाईल कॅमेऱ्याने स्कॅन करा. कोणत्याही IP शिवाय थेट ॲप उघडेल!<br>"
                "२. <strong>वस्तू स्कॅन करण्यासाठी:</strong> 'Take Photo / Upload' वर टॅप करा. फोटो काढताच सर्व माहिती आपोआप भरेल!<br>"
                "३. <strong>जलद विक्री:</strong> 'Quick Sales' पेजवर जाऊन थेट विक्री करा."
            )
        else:
            reply = (
                "📱 <strong>ExpiryGuard AI Quick Usage Guide:</strong><br><br>"
                "1. <strong>Connect Your Phone:</strong> Simply point your phone camera at the <strong>QR Code</strong> shown on your laptop screen. It opens ExpiryGuard AI on your phone instantly — no IP address typing needed!<br>"
                "2. <strong>Product Scanning:</strong> Tap <strong>'Take Photo / Upload'</strong>. Take a photo of the packaging, and our AI engine auto-detects the barcode, product name, MFG date, EXP date, and price automatically!<br>"
                "3. <strong>Fast POS Sales:</strong> Go to <strong>Quick Sales</strong> to ring up items with automatic stock deduction and overselling protection."
            )
        actions = [{"label": "Go to Scanner", "url": "/scan"}, {"label": "Quick Sales Counter", "url": "/quick-sales"}]
        append_history(user_id, "assistant", reply)
        return reply, actions

    # -------------------------------------------------------------
    # INTENT 8: Waste Reduction Tips for Kirana & Chaat Shops
    # -------------------------------------------------------------
    if any(k in msg_lower for k in ['waste', 'reduce', 'tip', 'advice', 'नुकसान', 'बचाव', 'कचरा', 'नासाडी']):
        if lang == 'hi':
            reply = (
                f"🛡️ <strong>Gupta Chaat & Stores के लिए कचरा और नुकसान कम करने के ५ आसान नियम:</strong><br><br>"
                f"१. <strong>FIFO नियम (पहले आया, पहले बिका):</strong> नए माल को पीछे और पुराने माल को शेल्फ पर आगे रखें।<br>"
                f"२. <strong>डेयरी उत्पादों पर कड़ी नज़र:</strong> दूध, पनीर, और ब्रेड को ३-५ दिनों के अंदर बेचने के लिए काउंटर पर आगे रखें।<br>"
                f"३. <strong>अति-स्टॉकिंग से बचें:</strong> जिस सामान की बिक्री धीमी है, उसका नया माल तब तक न मंगाएं जब तक पुराना न बिक जाए।<br>"
                f"४. <strong>समय रहते छूट दें:</strong> एक्सपायरी से ३-७ दिन पहले २५% छूट देकर पूंजी वापस निकाल लें।<br>"
                f"५. <strong>रोज़ क्विक सेल्स दर्ज करें:</strong> इससे आपको हमेशा पता रहेगा कि दुकान में क्या बचा है।"
            )
        elif lang == 'mr':
            reply = (
                f"🛡️ <strong>किराणा व चाट दुकानातील नासाडी रोखण्यासाठी ५ स्मार्ट उपाय:</strong><br><br>"
                f"१. <strong>FIFO पद्धत:</strong> आधी आलेला माल पुढे आणि नवीन माल मागे ठेवा.<br>"
                f"२. <strong>डेअरी वस्तू:</strong> दूध, पनीर, ब्रेड यांसारख्या वस्तू लवकर संपवण्यासाठी पुढे ठेवा.<br>"
                f"३. <strong>जादा माल साठवू नका:</strong> आधीचा साठा संपल्याशिवाय नवीन ऑर्डर देऊ नका.<br>"
                f"४. <strong>वेळेत सवलत द्या:</strong> मुदत संपण्यापूर्वी सवलत देऊन विक्री करा.<br>"
                f"५. <strong>दैनिक विक्री नोंद:</strong> रोजच्या रोज विक्री नोंदवून अचूक साठा ठेवा."
            )
        else:
            reply = (
                f"🛡️ <strong>5 Practical Waste Reduction Rules for Gupta Chaat & Stores:</strong><br><br>"
                f"1. <strong>First-In, First-Out (FIFO):</strong> Always place newer stock behind older batches on shelves.<br>"
                f"2. <strong>Daily Perishables Priority:</strong> Dairy items like milk, bread, and paneer should be placed right at the front counter.<br>"
                f"3. <strong>Halt Over-Ordering:</strong> Use our AI Restock engine so you never order slow-moving goods when you already have expiring batches.<br>"
                f"4. <strong>Strategic Dynamic Clearance:</strong> Offering 25%–40% discount 3 to 7 days before expiry recovers wholesale capital rather than suffering a 100% loss.<br>"
                f"5. <strong>Record Every Sale:</strong> Log transactions on the Quick Sales page so you always have real-time visibility."
            )
        actions = [{"label": "View AI Advisor", "url": "/recommendations"}]
        append_history(user_id, "assistant", reply)
        return reply, actions

    # -------------------------------------------------------------
    # INTENT 9: Natural Conversational Greeting / General AI Assistant
    # -------------------------------------------------------------
    greeting_variations_en = [
        f"Hello! I am your AI Store Assistant for <strong>{shop_name}</strong>. Currently, you have <strong>{total_products} items ({total_units} units)</strong> in stock. What can I check for you today?",
        f"Hi there! How can I help you manage <strong>{shop_name}</strong> today? I can check expiring stock, search product quantities, review today's sales, or suggest clearance discounts.",
        f"Welcome! I am analyzing your live inventory for <strong>{shop_name}</strong>. We currently have {len(urgent_15d_list)} items nearing expiry. What would you like to inspect?"
    ]
    greeting_variations_hi = [
        f"नमस्ते! मैं <strong>{shop_name}</strong> का स्मार्ट एआई सहायक हूँ। आपकी दुकान में इस समय कुल <strong>{total_products} उत्पाद ({total_units} पैकेट)</strong> मौजूद हैं। आज मैं आपकी क्या मदद कर सकता हूँ?",
        f"नमस्ते! आप मुझसे दुकान के स्टॉक, एक्सपायरी अलर्ट, आज की कमाई (₹{sales_rev_today:.2f}), या छूट के सुझावों के बारे में कुछ भी पूछ सकते हैं।"
    ]
    greeting_variations_mr = [
        f"नमस्कार! मी <strong>{shop_name}</strong> चा स्मार्ट एआय सहाय्यक आहे. आपल्या दुकानात सध्या एकूण <strong>{total_products} वस्तू ({total_units} नग)</strong> आहेत. मी आपल्याला कशी मदत करू?",
        f"नमस्कार! आपण मला दुकानातील साठा, मुदत संपणारे माल, आजची विक्री (₹{sales_rev_today:.2f}) किंवा सवलतींविषयी विचारू शकता."
    ]

    if lang == 'hi':
        reply = random.choice(greeting_variations_hi)
        reply += "<br><br>💡 <em>उदाहरण के लिए पूछें:</em><br>• 'दूध का कितना पैकेट बचा है?'<br>• 'कौन से सामान जल्द एक्सपायर हो रहे हैं?'<br>• 'आज की कुल बिक्री कितनी हुई?'"
    elif lang == 'mr':
        reply = random.choice(greeting_variations_mr)
        reply += "<br><br>💡 <em>उदा. विचारा:</em><br>• 'ब्रेडचा किती साठा शिल्लक आहे?'<br>• 'कोणत्या वस्तू लवकर संपणार आहेत?'<br>• 'आजची एकूण कमाई किती झाली?'"
    else:
        reply = (f"I don't have a specific store action for <strong>{clean_msg[:120]}</strong> yet. "
                 "I can look up a product's stock, price or expiry; list expired or low-stock items; "
                 "summarize sales; or suggest discounts. Try asking one of those directly.")

    actions = [
        {"label": "⏳ Expiring Soon", "query": "Which products are expiring soon?"},
        {"label": "📦 Low Stock", "query": "Show low stock products"},
        {"label": "💰 Today's Sales", "query": "What are today sales?"}
    ]
    append_history(user_id, "assistant", reply)
    return reply, actions
