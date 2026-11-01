"""Inventory-grounded chat context and deterministic fallback replies."""
import re
from datetime import date

from ai.expiry_predictor import calculate_days_until_expiry


def inventory_snapshot(cursor, user_id):
    cursor.execute("""SELECT product_name, mfg_date, expiry_date, barcode, quantity, price
                      FROM products WHERE user_id = ? ORDER BY expiry_date""", (user_id,))
    products = [dict(row) for row in cursor.fetchall()]
    today = date.today()
    enriched = []
    for item in products:
        row = dict(item)
        row['days_to_expiry'] = calculate_days_until_expiry(row['expiry_date'])
        row['inventory_value'] = round(row['quantity'] * row['price'], 2)
        enriched.append(row)
    cursor.execute("""SELECT COALESCE(SUM(quantity_sold),0) AS units,
                            COALESCE(SUM(total_amount),0) AS revenue
                      FROM sales WHERE user_id = ? AND date(sale_timestamp) = date('now')""", (user_id,))
    sales = dict(cursor.fetchone())
    urgent = [p for p in enriched if 0 <= p['days_to_expiry'] <= 7 and p['quantity'] > 0]
    expired = [p for p in enriched if p['days_to_expiry'] < 0 and p['quantity'] > 0]
    low_stock = [p for p in enriched if p['quantity'] < 5 and p['days_to_expiry'] >= 0]
    risk = sorted(enriched, key=lambda p: (p['days_to_expiry'], -p['quantity']))
    return {
        'today': today.isoformat(),
        'products': enriched,
        'totals': {
            'product_count': len(enriched),
            'units': sum(p['quantity'] for p in enriched),
            'inventory_value': round(sum(p['inventory_value'] for p in enriched), 2),
            'units_sold_today': sales['units'],
            'revenue_today': round(sales['revenue'], 2)
        },
        'expiring_this_week': urgent,
        'expired_in_stock': expired,
        'low_stock': low_stock,
        'highest_expiry_risk': risk[:5]
    }


def _items(items):
    if not items:
        return 'None in the current inventory.'
    return '\n'.join(
        (f"• {p['product_name']} — {p['quantity']} units; expired {abs(p['days_to_expiry'])} days ago ({p['expiry_date']})"
         if p['days_to_expiry'] < 0 else
         f"• {p['product_name']} — {p['quantity']} units; expires {p['expiry_date']} (in {p['days_to_expiry']} days)")
        for p in items
    )


def fallback_answer(message, snapshot, history=()):
    """Return (reply, supported); replies only use values present in this snapshot."""
    q = message.lower().strip()
    products = snapshot['products']
    if not q:
        return 'Please enter a question about your stock, expiry dates, or sales.', True

    # Resolve common follow-ups such as "what about its price?" from the last
    # product mentioned in this browser session.
    last_product = None
    for turn in reversed(history):
        for p in products:
            if p['product_name'].lower() in turn.get('content', '').lower():
                last_product = p
                break
        if last_product:
            break

    if any(s in q for s in ('waste', 'reduce', 'fifo', 'food waste', 'नासाडी', 'कचरा', 'नुकसान', 'बचाव')):
        names = ', '.join(p['product_name'] for p in snapshot['expiring_this_week'][:4]) or 'none currently'
        return (f"Use FIFO (older stock at the front), check expiry dates daily, and discount eligible stock before it expires. "
                f"From your current data, prioritize: {names}. Remove expired stock from sale."), True
    if any(s in q for s in ('discount', 'clearance', 'offer', 'discount first', 'छूट', 'सवलत')):
        candidates = [p for p in products if 0 <= p['days_to_expiry'] <= 30 and p['quantity'] > 0]
        candidates.sort(key=lambda p: p['days_to_expiry'])
        if not candidates:
            return 'No non-expired stock with an expiry date within 30 days needs a clearance discount right now.', True
        return 'Discount priority based on nearest expiry:\n' + '\n'.join(
            f"• {p['product_name']} — {p['days_to_expiry']} days left, {p['quantity']} units. Review the suggested price before applying."
            for p in candidates[:6]), True
    if any(s in q for s in ('expired', 'already expired', 'खराब', 'मुदत संपली', 'एक्सपायर')):
        return 'Expired products currently in stock:\n' + _items(snapshot['expired_in_stock']), True
    if any(s in q for s in ('highest risk', 'expiry risk', 'risk first', 'at risk', 'जोखिम')):
        return 'Highest expiry risk in your inventory (nearest expiry first):\n' + _items(snapshot['highest_expiry_risk']), True
    if any(s in q for s in ('expir', 'expiry', 'week', '7 day', 'this week', 'जल्द', 'लवकर', 'आठवडा')):
        items = snapshot['expiring_this_week'] if ('week' in q or '7 day' in q or 'this week' in q or 'आठवडा' in q) else [p for p in products if 0 <= p['days_to_expiry'] <= 15]
        return 'Products expiring in the next ' + ('7 days' if ('week' in q or '7 day' in q or 'this week' in q or 'आठवडा' in q) else '15 days') + ':\n' + _items(items), True
    if any(s in q for s in ('low stock', 'reorder', 'कम स्टॉक', 'कम है', 'कमी', 'माल संपला')):
        return 'Products with low stock (under 5 units):\n' + _items(snapshot['low_stock']), True
    if any(s in q for s in ('inventory value', 'total value', 'stock value', 'कुल मूल्य')):
        return f"Your inventory has {snapshot['totals']['units']} units across {snapshot['totals']['product_count']} products, worth ₹{snapshot['totals']['inventory_value']:.2f} at listed selling prices.", True

    query_words = set(re.findall(r"[a-z0-9]+", q))
    matched = next((p for p in products if p['product_name'].lower() in q or p['barcode'] in q), None)
    if not matched:
        candidates = []
        for p in products:
            product_words = set(re.findall(r"[a-z0-9]+", p['product_name'].lower())) - {'the','and','with','for','g','ml','kg'}
            overlap = len(query_words & product_words)
            if overlap:
                candidates.append((overlap, p))
        if candidates:
            matched = max(candidates, key=lambda item: item[0])[1]
    if not matched and last_product and any(s in q for s in ('its', 'it ', 'that', 'price', 'quantity', 'stock', 'how many', 'barcode')):
        matched = last_product
    if matched:
        if any(s in q for s in ('price', 'cost', 'mrp')):
            return f"{matched['product_name']} is listed at ₹{matched['price']:.2f} per unit.", True
        if any(s in q for s in ('barcode', 'code')):
            return f"The barcode for {matched['product_name']} is {matched['barcode']}.", True
        if any(s in q for s in ('expir', 'fresh', 'date', 'when')):
            return f"{matched['product_name']} expires on {matched['expiry_date']} ({matched['days_to_expiry']} days from today).", True
        return f"{matched['product_name']}: {matched['quantity']} units in stock at ₹{matched['price']:.2f} each; expiry {matched['expiry_date']} ({matched['days_to_expiry']} days).", True
    if any(s in q for s in ('hello', 'hi', 'hey', 'नमस्ते', 'नमस्कार')):
        return (f"Hello! I can answer from your live inventory. You have {snapshot['totals']['product_count']} products "
                f"({snapshot['totals']['units']} units). Ask about expiry, discounts, low stock, or total value."), True
    return ('I can answer questions about expiring or expired products, discounts, stock, product price, and total inventory value. Try asking about a specific product, expiry dates, or low stock.', False)


def general_knowledge_answer(message, history=(), snapshot=None):
    """Answer general-knowledge questions that are NOT about the inventory database.
    Works without any API key. Returns a helpful string."""
    q = message.lower().strip()

    # ── Greetings ──────────────────────────────────────────────────────────────
    if any(s in q for s in ('hello', 'hi', 'hey', 'hii', 'good morning', 'good afternoon',
                             'good evening', 'sup', 'namaste', 'namaskar', 'नमस्ते',
                             'नमस्कार', 'नमस्कर', 'हाय', 'हेलो', 'कसे आहात', 'कैसे हो')):
        count = snapshot['totals']['product_count'] if snapshot else 0
        return (f"Namaste! 🙏 I'm ExpiryGuard AI, your smart store assistant. "
                f"I'm here to help with your inventory ({count} products), "
                f"expiry alerts, sales tips, food storage advice, and general store questions. "
                f"What would you like to know?")

    # ── About the app ──────────────────────────────────────────────────────────
    if any(s in q for s in ('what can you do', 'what do you do', 'who are you', 'your features',
                             'help me', 'your capabilities', 'tumhara kaam', 'तुम क्या कर सकते',
                             'तुम्ही काय करता', 'app kya hai', 'क्या करते')):
        return ("I'm ExpiryGuard AI — your intelligent store assistant! 🤖\n\n"
                "**I can help you with:**\n"
                "• 📦 Inventory management — check stock, expiry dates, low stock alerts\n"
                "• 💸 Discount recommendations — know when to apply clearance offers\n"
                "• 🍱 Food storage tips — how to store products properly\n"
                "• 🛒 General retail advice — FIFO, reordering, managing waste\n"
                "• 🌡️ Health & safety — food safety guidelines\n"
                "• 💬 General questions — ask me anything!\n\n"
                "Try asking: *'Which products expire this week?'* or *'How do I store rice properly?'*")

    # ── Food storage tips ──────────────────────────────────────────────────────
    if any(s in q for s in ('store rice', 'rice store', 'chawal', 'चावल रखना', 'तांदूळ')):
        return ("🍚 **Rice Storage Tips:**\n"
                "• Store in an airtight container in a cool, dry place\n"
                "• Ideal temperature: below 25°C\n"
                "• Uncooked rice lasts 1–2 years if stored properly\n"
                "• Keep away from moisture and direct sunlight\n"
                "• Add a few bay leaves to prevent insects\n"
                "• Once cooked, refrigerate within 2 hours and consume within 3 days.")

    if any(s in q for s in ('store oil', 'oil store', 'tel', 'तेल', 'तेल कसे')):
        return ("🫙 **Cooking Oil Storage Tips:**\n"
                "• Store in a cool, dark place away from the stove\n"
                "• Always keep the lid tightly closed to prevent oxidation\n"
                "• Avoid storing near heat sources — this speeds up rancidity\n"
                "• Most oils last 6–12 months after opening\n"
                "• Smell test: rancid oil smells sour or bitter — discard it immediately.")

    if any(s in q for s in ('store milk', 'milk store', 'dudh', 'दूध', 'दुध')):
        return ("🥛 **Milk Storage Tips:**\n"
                "• Always refrigerate between 1°C–4°C\n"
                "• Never store milk in the fridge door — it's the warmest spot\n"
                "• Keep milk in its original sealed container\n"
                "• Use within 3–5 days of opening\n"
                "• Don't mix old milk with new — it can curdle the fresh batch.")

    if any(s in q for s in ('store dal', 'store daal', 'dal store', 'दाल', 'डाळ')):
        return ("🫘 **Dal (Lentil) Storage Tips:**\n"
                "• Store in airtight containers in a cool, dry location\n"
                "• Whole dals last up to 1 year; split dals 6–8 months\n"
                "• Keep away from moisture to prevent mold\n"
                "• Add a piece of dried red chili to prevent insects naturally.")

    if any(s in q for s in ('store atta', 'wheat flour', 'atta store', 'आटा', 'पीठ')):
        return ("🌾 **Atta (Wheat Flour) Storage Tips:**\n"
                "• Store in a clean, airtight container\n"
                "• Keep in a cool, dry place away from moisture\n"
                "• Shelf life: 6–8 months at room temperature\n"
                "• Refrigerating atta extends shelf life to 12 months\n"
                "• Inspect regularly for insects or an off smell.")

    # ── Expiry / food safety general questions ─────────────────────────────────
    if any(s in q for s in ('how long', 'shelf life', 'how many days', 'kitne din',
                             'कितने दिन', 'किती दिवस', 'best before', 'use by')):
        return ("📅 **Understanding Expiry & Shelf Life:**\n\n"
                "**Best Before** — Product quality is best before this date. Often still safe to eat shortly after.\n"
                "**Use By / Expiry Date** — Safety date. Do NOT consume after this date (especially dairy, meat, medicine).\n\n"
                "**General guidelines (unopened, stored properly):**\n"
                "• Packaged snacks: 3–12 months\n"
                "• Dal/rice/atta: 6–18 months\n"
                "• Oils: 6–12 months after opening\n"
                "• Dairy products: 3–7 days\n"
                "• Canned goods: 1–3 years\n"
                "• Medicines: Follow the printed date strictly.\n\n"
                "Always check your specific product's label.")

    if any(s in q for s in ('food poisoning', 'khana kharab', 'खाना खराब', 'food spoil',
                             'spoiled', 'expired food', 'eat expired', 'खराब खाना')):
        return ("⚠️ **Food Safety — What to do with expired food:**\n\n"
                "• **Dairy, meat, fish** — Discard immediately when expired. Do NOT taste-test.\n"
                "• **Dry goods (dal, rice, atta)** — Inspect for insects, mold, or off smell. If fine, may still be usable.\n"
                "• **Packaged snacks** — A few days past Best Before is usually okay if sealed and stored properly.\n"
                "• **Medicines** — NEVER consume expired medicines. Dispose safely.\n\n"
                "When in doubt, throw it out! Your health is more important than saving money on expired stock.")

    # ── Retail / store management general tips ─────────────────────────────────
    if any(s in q for s in ('fifo', 'first in first out', 'stock rotation', 'stock management',
                             'manage stock', 'stocking', 'shelving tips')):
        return ("📦 **FIFO (First In, First Out) — The Golden Rule of Retail:**\n\n"
                "• Always place **older stock at the front**, newer stock behind\n"
                "• When restocking shelves, move existing items forward before adding new ones\n"
                "• Check expiry dates every time you receive a new delivery\n"
                "• Train your staff to follow FIFO strictly\n"
                "• Use ExpiryGuard AI's expiry alerts to know what to sell first!\n\n"
                "Following FIFO can reduce your food waste by up to **30%** in a typical kirana store.")

    if any(s in q for s in ('how to increase sales', 'boost sales', 'more customers', 'sales tips',
                             'bikri kaise', 'bikri badhaye', 'बिक्री', 'sales kaise')):
        return ("🛒 **Tips to Boost Sales in Your Store:**\n\n"
                "• **Discount near-expiry products** — Offer 10–40% off products expiring within 7 days\n"
                "• **Bundle offers** — Sell slow-moving items with fast sellers (e.g., atta + dal combo)\n"
                "• **End-cap displays** — Place promotional or expiring items at eye level near the counter\n"
                "• **Daily deals** — Pick one product per day for a small discount\n"
                "• **UPI payments** — Ensure you accept all payment methods (GPay, PhonePe, etc.)\n"
                "• **Loyalty** — Give a small reward or candy to regular customers\n"
                "• **Cleanliness** — A clean, well-organized store attracts more repeat customers.")

    if any(s in q for s in ('reduce waste', 'waste management', 'food waste kaise', 'waste kam karo',
                             'waste kaise', 'नासाडी', 'बर्बाद')):
        return ("♻️ **Reducing Waste in Your Store:**\n\n"
                "1. **Follow FIFO** — Always sell older stock first\n"
                "2. **Check expiry on delivery** — Reject or negotiate stock close to expiry\n"
                "3. **Set reorder quantities carefully** — Don't over-order perishables\n"
                "4. **Discount before discarding** — 20–40% off is better than zero\n"
                "5. **Donate to neighbors/food banks** — A day before expiry, donate rather than trash\n"
                "6. **Use ExpiryGuard alerts** — The weekly expiry report tells you what to act on NOW\n"
                "7. **Track what doesn't sell** — Slow movers may need smaller reorder quantities.")

    if any(s in q for s in ('gst', 'tax', 'टैक्स', 'कर', 'invoice', 'billing')):
        return ("🧾 **GST for Kirana/Retail Stores:**\n\n"
                "• Food items like rice, wheat, dal, vegetables are **0% GST** (exempt)\n"
                "• Packaged branded foods: **5% GST**\n"
                "• Biscuits, namkeen, soft drinks: **12–18% GST**\n"
                "• Medicines: **0% to 12% GST** depending on category\n\n"
                "**Tip:** Keep all purchase bills. File GSTR-1 monthly/quarterly based on your turnover.\n"
                "Consult a local CA or GST practitioner for your specific filing requirements.")

    # ── Health questions ───────────────────────────────────────────────────────
    if any(s in q for s in ('diabetes', 'sugar patient', 'diabetic', 'शुगर', 'मधुमेह',
                             'sugar kam', 'low sugar food')):
        return ("🩺 **Foods for Diabetic Customers:**\n\n"
                "**Good choices to stock/recommend:**\n"
                "• Whole grain atta (whole wheat, bajra, jowar)\n"
                "• Brown rice or millets (ragi, bajra)\n"
                "• Oats, daliya\n"
                "• Green leafy vegetables\n"
                "• Dals and legumes (high fiber, low glycemic)\n\n"
                "**Avoid or limit:**\n"
                "• White rice, maida products, sugary drinks\n"
                "• Processed snacks and namkeen\n\n"
                "*This is general information — always recommend customers consult their doctor.*")

    if any(s in q for s in ('protein', 'high protein', 'body banao', 'muscle', 'gym',
                             'fitness', 'प्रोटीन', 'शरीर बनाओ')):
        return ("💪 **High Protein Foods for Fitness:**\n\n"
                "• **Dal (lentils)** — 9g protein per 100g, very affordable\n"
                "• **Paneer** — 18g protein per 100g, great for vegetarians\n"
                "• **Eggs** — 13g protein per 100g, complete protein\n"
                "• **Chickpeas (Chana)** — 9g protein per 100g\n"
                "• **Peanuts** — 26g protein per 100g, budget-friendly\n"
                "• **Soy milk / soya chunks** — Good vegetarian alternative\n\n"
                "*Stock these in your store — they're popular with health-conscious customers!*")

    # ── Weather / general India / seasonal tips ────────────────────────────────
    if any(s in q for s in ('summer', 'garam', 'heat', 'garmi', 'गर्मी', 'उन्हाळा')):
        return ("☀️ **Summer Store Tips:**\n\n"
                "• Store dairy and cold drinks properly — demand is high in summer\n"
                "• Perishables expire faster in heat — check expiry dates more frequently\n"
                "• Keep cold storage below 4°C for dairy items\n"
                "• High-demand summer items: cold drinks, ice cream, nimbu sharbat, ORS sachets, sunscreen\n"
                "• Check your oils — heat accelerates rancidity. Rotate oil stock more frequently.")

    if any(s in q for s in ('monsoon', 'rainy', 'baarish', 'barish', 'पाऊस', 'बारिश')):
        return ("🌧️ **Monsoon Store Tips:**\n\n"
                "• Humidity causes dal, atta, and rice to absorb moisture — ensure airtight storage\n"
                "• Watch for mold on packaged items — check regularly\n"
                "• High demand: umbrellas, raincoats, ORS, cold & flu medicines\n"
                "• Ensure your store floor is dry to prevent slipping accidents\n"
                "• Electricity cuts are common — keep a backup for your refrigeration.")

    # ── Hindi/Marathi general questions ───────────────────────────────────────
    if any(s in q for s in ('तुम्ही कोण', 'आप कौन', 'तुम कौन', 'मला मदत', 'मुझे मदद')):
        return ("नमस्ते! 🙏 मी ExpiryGuard AI आहे — तुमचा स्मार्ट दुकान सहाय्यक!\n\n"
                "मी तुम्हाला मदत करू शकतो:\n"
                "• 📦 इन्व्हेंटरी आणि एक्सपायरी तपासणे\n"
                "• 💸 डिस्काउंट सुचवणे\n"
                "• 🍱 अन्न साठवणुकीच्या टिप्स\n"
                "• 🛒 दुकान व्यवस्थापन सल्ला\n\n"
                "काय जाणून घ्यायचे आहे?")

    if any(s in q for s in ('app kaise', 'app use kaise', 'app kesa', 'app chalao',
                             'कसे वापरावे', 'app kasa')):
        return ("📱 **ExpiryGuard AI कसे वापरावे:**\n\n"
                "1. **इन्व्हेंटरी** — Dashboard वर सर्व products, expiry dates आणि stock दिसतो\n"
                "2. **Scan** — Barcode scan करून नवीन product जोडा\n"
                "3. **Chatbot (मी!)** — इन्व्हेंटरी बद्दल किंवा सामान्य प्रश्न विचारा\n"
                "4. **Alerts** — Expiry आणि low stock alerts मिळवा\n"
                "5. **Sales** — Sales record करा आणि revenue track करा\n\n"
                "अधिक माहितीसाठी कोणताही प्रश्न विचारा!")

    # ── Cooking tips ───────────────────────────────────────────────────────────
    if any(s in q for s in ('recipe', 'cooking', 'how to make', 'kaise banaye', 'बनाने',
                             'कसे बनवायचे', 'khana', 'dish')):
        return ("🍳 **Quick Cooking Tips from ExpiryGuard AI:**\n\n"
                "I'm primarily an inventory assistant, but here are some helpful tips:\n\n"
                "• **Dal tadka:** Boil toor dal, temper with mustard seeds, cumin, garlic, and tomato\n"
                "• **Roti tip:** Use warm water to knead atta for softer rotis\n"
                "• **Rice:** 1 cup rice : 2 cups water, bring to boil then simmer 15 min covered\n"
                "• **Poha:** Rinse thick poha, temper with mustard, curry leaves, onion, green chili\n"
                "• **Upma:** Roast rava dry first, then add boiling water gradually while stirring\n\n"
                "For detailed recipes, try apps like Cookpad or YouTube!")

    # ── Thank you / farewell ───────────────────────────────────────────────────
    if any(s in q for s in ('thank', 'thanks', 'dhanyavad', 'shukriya', 'धन्यवाद',
                             'शुक्रिया', 'bye', 'goodbye', 'alvida', 'अलविदा')):
        return ("You're welcome! 😊 Happy to help. Come back anytime you have questions about your inventory, products, or anything else. Best of luck with your store! 🏪🙏")

    # ── Compliments ────────────────────────────────────────────────────────────
    if any(s in q for s in ('good', 'great', 'awesome', 'excellent', 'best', 'nice', 'wow',
                             'amazing', 'बढ़िया', 'शाबाश', 'छान', 'सुंदर')):
        return ("Thank you! 😊 I'm glad I could help. Feel free to ask more questions — I'm here for your inventory, product, food safety, and general store needs! 🏪")

    # ── Frustration / complaints ───────────────────────────────────────────────
    if any(s in q for s in ('not working', 'broken', 'error', 'problem', 'issue', 'bug',
                             'काम नाही', 'काम नहीं', 'खराब है', 'बंद है')):
        return ("😟 I'm sorry to hear that! Please try the following:\n\n"
                "1. **Refresh the page** and try again\n"
                "2. **Re-login** if the session has expired\n"
                "3. **Check your internet connection** — mobile data or Wi-Fi should both work\n"
                "4. If the issue persists, note the error message and contact your system administrator.\n\n"
                "I'm here whenever you're ready to continue! 🙏")

    # ── Generic intelligent fallback (catches everything else) ─────────────────
    topic = message.strip()[:60] if len(message.strip()) > 0 else 'that'
    return (f"Great question! 🤔 You asked about: *\"{topic}\"*\n\n"
            f"I'm ExpiryGuard AI — primarily built for inventory management, but I do my best to help with general questions too.\n\n"
            f"**For your query, here are some suggestions:**\n"
            f"• If this is about a **product in your store**, ask me by product name (e.g., 'Tell me about Amul Milk')\n"
            f"• If this is about **expiry dates**, ask 'Which products expire this week?'\n"
            f"• If this is a **general knowledge question**, try searching Google or asking a specific follow-up\n"
            f"• For **food storage or retail tips**, I can definitely help — just ask more specifically!\n\n"
            f"What else can I help you with today? 🏪")
