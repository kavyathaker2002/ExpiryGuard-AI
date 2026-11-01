# ExpiryGuard AI — Smart Product Expiry Management and Waste Reduction System

**ExpiryGuard AI** is a modern, mobile-friendly web application designed primarily for small retail kirana shops, grocery stores, and supermarkets in India. It empowers shopkeepers to effortlessly track expiry dates, manage inventory, execute rapid sales, prevent food and product wastage, and make intelligent stocking decisions.

---

## 🌟 Key Features

1. **Light / Soft Pink Theme**:
   - Modern, friendly aesthetic crafted specifically with soft pastel pinks (`#FFF5F7`, `#FCE7F3`, `#EC4899`, `#9D174D`) and high-contrast dark charcoal text for clear readability under bright shop lights.
2. **Mobile-First & One-Handed Friendly**:
   - Sticky bottom navigation bar on mobile for instant thumb access (`Dashboard`, `Stock`, `Scan`, `Quick Sales`, `AI Advisor`, `Analytics`).
   - Touch-friendly 48px+ tap targets, stepper buttons, and responsive cards.
3. **Exact 6-Field Product Scanner**:
   - Strictly enforces the 6 essential fields:
     1. Product Name
     2. Manufacturing Date
     3. Expiry Date
     4. Barcode
     5. Quantity
     6. Price (₹)
   - Zero complicated categories or measurement unit configurations.
   - Barcode scanning via **ZXing Browser** (rear camera preferred).
   - Packaging text & date extraction via **Tesseract.js OCR** (supports `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`, and `MFG`/`EXP`/`Best Before` detection).
4. **Multilingual Localization (English, Hindi, Marathi)**:
   - Complete translations for 100% of the UI (menus, stats, forms, alerts, buttons, errors, receipts).
   - Natural vocabulary familiar to Indian shopkeepers (e.g., 'दुकान का स्टॉक', 'सामान स्कैन करें', 'सवलत सूचना').
   - Instant language switching persisted across sessions.
5. **Quick Sales Counter**:
   - Dedicated rapid POS interface separate from product creation.
   - Barcode auto-lookup, stock quantity check, large `+` / `-` steppers, automatic total calculation, and atomic stock deduction.
   - Prevents overselling and duplicate submissions.
   - Success message: `"Sale complete! 2 packets sold. 8 packets left."`
6. **Machine Learning Expiry Risk Prediction**:
   - Scikit-learn Random Forest model + moving average sales velocity calculation.
   - Categorizes stock into High Risk, Moderate Risk, Safe, and Expired.
   - Explains exactly why items are at risk of unsold waste.
7. **Dynamic Pricing Recommendations**:
   - Suggests clearance discounts (15% - 50%) based on remaining shelf life.
   - Displays clear rationale and one-click "Apply Discount" button (never alters price without shopkeeper's confirmation).
8. **Restocking & Waste-Reduction Advice**:
   - Highlights fast-movers needing reorder (< 5 units) vs. excess stock nearing expiry to halt ordering.
9. **Visual Analytics (Chart.js)**:
   - 7-day sales revenue & volume trend charts.
   - Expiry health breakdown doughnut chart.
   - Top-selling products bar chart.

---

## 🚀 How to Run

### Important: open the Flask app, not the template files
Files under `templates/` contain Jinja (`{% ... %}` and `{{ ... }}`) and are intentionally not standalone HTML. Do not open `templates/scanner/scan.html` from File Explorer or serve the project with a static file server. Start Flask with `python run.py`, then open the printed `http://localhost:5000` URL. Flask routes use `render_template()` and the project configures absolute `templates/` and `static/` paths. Raw Jinja syntax means the browser was given a source template instead of a Flask-rendered route.

### Prerequisite
- Python 3.10+ (Tested on Python 3.14 on Windows)

### Step 1: Clone or Open Project
Open the project directory in Visual Studio Code or Terminal:
```bash
cd "e:\PROJECT Vsem\expiryguard ai\final year prj"
```

### Step 2: Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```
*(Flask, scikit-learn, numpy, pandas, Pillow, Werkzeug, qrcode)*

### Step 3: Run the Application
```bash
python run.py
```

You will see:
```text
=================================================================
 🛡️  EXPIRYGUARD AI — SERVER STARTED SUCCESSFULLY!  🛡️
=================================================================
 ▶ Local Desktop Access: http://localhost:5000
 ▶ Mobile Phone Access:  http://192.168.x.x:5000
-----------------------------------------------------------------
 💡 Demo Login Credentials:
    Username: demo_shop
    Password: shop123
=================================================================
```

### Step 4: Access on Mobile Phone
1. Connect your smartphone and computer to the same Wi-Fi network.
2. Open the scanner page on the computer and scan its QR code. The QR uses the detected LAN address and opens the login page for the same Flask server and SQLite database.
3. If the QR says no LAN address is available, check that the PC is connected to Wi-Fi and that its firewall allows inbound connections on port 5000. For a remote deployment/tunnel, set `PUBLIC_APP_URL` to its reachable HTTPS origin.
4. Browser live-camera access requires a secure context: trusted HTTPS or localhost. `python run.py --ssl` uses a temporary self-signed certificate, which mobile browsers may reject; for reliable phone camera streaming, use trusted HTTPS via a reverse proxy. The native upload/capture picker remains available when live streaming is blocked.

### Optional AI services
The scanner supports browser OCR and barcode decoding without an API key. For image-based brand/category/product recognition beyond printed OCR, set `OPENAI_API_KEY` in the server environment. The key is read only by Flask and is never sent to browser JavaScript. `OPENAI_VISION_MODEL` and `OPENAI_CHAT_MODEL` can select models supported by the configured API. Without a key (or when the provider is unavailable), the scanner reports OCR-only results and the chatbot labels its answers as **Database fallback**. Supported inventory questions use SQLite-derived values directly even when AI is configured.

Example PowerShell setup for the current terminal:
```powershell
$env:SECRET_KEY = 'use-a-long-random-secret'
$env:OPENAI_API_KEY = 'your-server-side-api-key'
python run.py
```

For HTTPS behind a local trusted certificate, set `SSL_CERT_FILE` and `SSL_KEY_FILE` and run `python run.py --ssl`. For a trusted reverse-proxy or tunnel, set `PUBLIC_APP_URL` to the reachable HTTPS origin before starting Flask.

---

## 🧪 Running Automated Tests
Run the automated test suite covering authentication, multi-tenancy isolation, 6-field validation, atomic sales, overselling prevention, and multilingual dictionaries:
```bash
python test_app.py
```
Output:
```text
Ran 6 tests in 2.9s
OK
```

---

## 📁 Project Structure

```text
├── app.py                      # Flask Application Factory & Jinja filters
├── config.py                   # App Configuration & SQLite database path
├── database.py                 # SQLite Schema, Constraints & Indian Kirana Seed Data
├── run.py                      # Production / Local Launcher with Network IP display
├── test_app.py                 # Automated Unit & Integration Tests
├── translations.py             # Multilingual dictionary (English, Hindi, Marathi)
├── requirements.txt            # Python Dependencies
├── ai/
│   ├── __init__.py
│   ├── expiry_predictor.py     # Scikit-learn ML Risk Model & Velocity Calculator
│   ├── pricing_engine.py       # Dynamic Clearance Discount Engine
│   └── restock_engine.py       # Reorder & Waste-Reduction Advice
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py          # Register, Login, Logout, Profile, Language Switch
│   ├── dashboard_routes.py     # Dashboard KPIs & Urgent Alerts
│   ├── scanner_routes.py       # Exact 6-Field Product Scanner & Barcode Lookup
│   ├── inventory_routes.py     # Inventory Search, Status Filter Tabs, Edit/Delete
│   ├── sales_routes.py         # Quick Sales, Stepper, Atomic Stock Deduction
│   ├── recommendations_routes.py # AI Risk Cards & Dynamic Discount Apply API
│   └── analytics_routes.py     # Reporting Metrics & Chart.js JSON Endpoints
├── static/
│   ├── css/
│   │   ├── theme.css           # Soft Pink Color Palette, High Contrast Tokens
│   │   ├── main.css            # Responsive Layout, Bottom Nav, Modals, Cards
│   │   └── scanner.css         # Viewfinder Laser Animation, Stepper, Bill Preview
│   └── js/
│       ├── i18n.js             # Client-side Language Switcher & Persistence
│       ├── scanner.js          # ZXing Barcode + Tesseract OCR Date Parser
│       ├── sales.js            # Quick Sales Stepper & POS Logic
│       └── analytics.js        # Chart.js Visualizations
└── templates/
    ├── base.html               # Base layout, navbar, bottom nav, toast notifications
    ├── auth/                   # Login, Register, Profile templates
    ├── dashboard/              # Summary cards, urgent alerts, quick action tiles
    ├── scanner/                # Camera scanner & Exact 6-field form
    ├── inventory/              # Table & mobile cards with search and filters
    ├── sales/                  # Quick sales counter with live bill preview
    ├── recommendations/        # AI Risk, Dynamic Pricing & Restocking Advice
    └── analytics/              # Performance charts & waste metrics
```
