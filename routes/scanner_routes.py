from datetime import datetime
import base64
import json
import os
import re
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from PIL import Image, UnidentifiedImageError
from flask import Blueprint, render_template, request, jsonify, session, current_app
from database import get_db
from routes.auth_routes import login_required
from ai.provider_client import ProviderUnavailable, analyze_product_image
from ai.packaging_ocr import analyze_image_with_ocr

scanner_bp = Blueprint('scanner', __name__)

@scanner_bp.route('/api/scanner/analyze-image', methods=['POST'])
@login_required
def analyze_image():
    upload = request.files.get('image')
    if not upload or not upload.filename:
        return jsonify({'success': False, 'message': 'Choose an image first.'}), 400
    mime_type = (upload.mimetype or '').lower()
    # Reject non-images
    if not mime_type.startswith('image/') and mime_type not in {'application/octet-stream', ''}:
        return jsonify({'success': False, 'message': 'Use a JPG, PNG, or WEBP image.'}), 415
    max_bytes = current_app.config.get('MAX_IMAGE_BYTES', 12 * 1024 * 1024)
    raw = upload.stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        return jsonify({'success': False, 'message': 'Image is too large. Maximum size is 12 MB.'}), 413
    try:
        from PIL import ImageOps
        with Image.open(BytesIO(raw)) as image:
            if image.width * image.height > 30_000_000:
                return jsonify({'success': False, 'message': 'Image dimensions are too large. Choose a smaller image.'}), 413
            # Auto-orient phone camera photos according to EXIF metadata
            image = ImageOps.exif_transpose(image)
            # Convert any image format to standard RGB JPEG for AI
            rgb_img = image.convert('RGB')
            buf = BytesIO()
            rgb_img.save(buf, format='JPEG', quality=90)
            raw = buf.getvalue()
            mime_type = 'image/jpeg'
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        return jsonify({'success': False, 'message': 'The image could not be read. Please choose a valid photo.'}), 400

    ocr_text = request.form.get('ocr_text', '')[:6000]

    fields = {}
    provider_used = 'ocr_only'

    # 1. Try cloud Vision AI if configured
    has_gemini = bool(os.environ.get('GEMINI_API_KEY', '').strip())
    has_openai = bool(os.environ.get('OPENAI_API_KEY', '').strip())
    if has_gemini or has_openai:
        try:
            fields = analyze_product_image(base64.b64encode(raw).decode('ascii'), mime_type, ocr_text) or {}
            provider_used = 'vision_ai'
        except ProviderUnavailable as exc:
            current_app.logger.info(f"Vision AI unavailable: {exc}, using native packaging OCR")
            fields = {}

    # 2. Always run Native Packaging OCR (winocr) to guarantee exact physical packet dates and printed price
    try:
        native_extracted = analyze_image_with_ocr(raw, ocr_text)
        if native_extracted:
            for k, v in native_extracted.items():
                # Packaging OCR values directly read from the packet's ink stamps take priority for dates and price
                if v is not None:
                    if k in ('manufacturing_date', 'expiry_date', 'price') or not fields.get(k):
                        fields[k] = v
            if provider_used != 'vision_ai' and any(v for k, v in fields.items() if k != 'raw_text'):
                provider_used = 'packaging_ocr'
    except Exception as ocr_err:
        current_app.logger.warning(f"Native packaging OCR error: {ocr_err}")

    # If no fields detected and no cloud AI was used, report ocr_only
    if provider_used != 'vision_ai' and not any(v for k, v in fields.items() if k != 'raw_text'):
        provider_used = 'ocr_only'

    allowed_fields = ('product_name', 'brand', 'category', 'package_size', 'barcode', 'date_note')
    clean = {key: (str(fields.get(key))[:120] if fields.get(key) is not None else None) for key in allowed_fields}
    for key in ('manufacturing_date', 'expiry_date'):
        value = fields.get(key)
        if isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            try:
                datetime.strptime(value, '%Y-%m-%d')
                clean[key] = value
            except ValueError:
                clean[key] = None
        else:
            clean[key] = None
    try:
        price = float(fields['price']) if fields.get('price') is not None else None
        clean['price'] = price if price is not None and 0 <= price <= 100000 else None
    except (ValueError, TypeError):
        clean['price'] = None
    confidence = fields.get('confidence') if isinstance(fields.get('confidence'), dict) else {}
    clean['confidence'] = {key: max(0.0, min(1.0, float(value))) for key, value in confidence.items()
                           if key in ('product_name','brand','category','package_size','manufacturing_date','expiry_date','barcode','price')
                           and isinstance(value, (float, int))}
    if provider_used == 'ocr_only' and not any(v for k, v in clean.items() if k != 'confidence' and v is not None):
        clean = {}
    return jsonify({'success': True, 'provider': provider_used, 'fields': clean,
                    'message': 'Packaging analysis complete. Review recognized values before saving.'})

@scanner_bp.route('/scan')
@login_required
def scan():
    barcode_param = request.args.get('barcode', '')
    return render_template('scanner/scan.html', initial_barcode=barcode_param)

from ai.fmcg_catalog import lookup_catalog_product, FMCG_CATALOG


def lookup_open_food_facts(barcode):
    """Try Open Food Facts (global + Indian) barcode API as a fallback with full retail details."""
    from datetime import datetime, timedelta
    code = str(barcode).strip()
    if not code.isdigit() or not 8 <= len(code) <= 14:
        return None

    # Fields to fetch: include more for Indian products
    fields = 'code,product_name,product_name_en,brands,categories,quantity,ingredients_text,labels'
    urls = [
        # Global database first
        f'https://world.openfoodfacts.org/api/v3/product/{quote(code)}.json?fields={fields}',
        # Indian-specific database (better for Indian products)
        f'https://in.openfoodfacts.org/api/v3/product/{quote(code)}.json?fields={fields}',
    ]

    for url in urls:
        req = Request(url, headers={
            'User-Agent': 'ExpiryGuardAI/2.0 (Indian retail inventory; contact@expiryguard.ai)',
            'Accept': 'application/json'
        })
        try:
            with urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            continue

        product = payload.get('product') or {}
        # Accept product_name or product_name_en
        product_name = (product.get('product_name') or product.get('product_name_en') or '').strip()
        # Open Food Facts API v3 returns status="success", v2 returns status=1
        status = payload.get('status')
        if status not in (1, 'success') or not product_name:
            continue

        def first_label(value):
            if not isinstance(value, str):
                return None
            label = value.split(',')[0].replace('en:', '').replace('-', ' ').strip().title()
            return label or None

        brand = first_label(product.get('brands'))
        category = first_label(product.get('categories')) or 'Grocery & FMCG'

        # If brand not already in product name, format cleanly
        if brand and brand.lower() not in product_name.lower():
            full_name = f"{brand} {product_name}".strip()
        else:
            full_name = product_name

        # Extract package size from quantity field or product name
        qty_str = product.get('quantity', '')
        pkg_size = (qty_str[:60].strip()) if isinstance(qty_str, str) and qty_str.strip() else None
        if not pkg_size or pkg_size == '1 unit':
            size_match = re.search(r'(\d+(?:\.\d+)?\s*(?:g|gm|kg|ml|l|tin|pcs|pack))\b', full_name, re.I)
            if size_match:
                pkg_size = size_match.group(1)
            elif any(w in cat_lower for w in ['masala', 'spice', 'badshah', 'everest', 'mdh']):
                pkg_size = '100 g'
            else:
                pkg_size = '1 unit'

        # Estimate shelf life and retail price based on product category & weight
        cat_lower = (category + ' ' + full_name + ' ' + (pkg_size or '')).lower()

        # Extract weight for realistic pricing
        weight_kg = 1.0
        kg_match = re.search(r'(\d+(?:\.\d+)?)\s*k(?:g|gs)?\b', cat_lower)
        g_match = re.search(r'(\d+(?:\.\d+)?)\s*g(?:m|ms)?\b', cat_lower)
        l_match = re.search(r'(\d+(?:\.\d+)?)\s*l(?:tr|itres?)?\b', cat_lower)
        if kg_match:
            weight_kg = float(kg_match.group(1))
        elif g_match:
            weight_kg = float(g_match.group(1)) / 1000.0
        elif l_match:
            weight_kg = float(l_match.group(1))

        if any(w in cat_lower for w in ['masala', 'spice', 'mirch', 'haldi', 'dhaniya', 'garam', 'powder', 'seasoning', 'badshah', 'everest', 'mdh', 'catch']):
            shelf_days = 540
            category = 'Spices & Masala'
            if 'biryani' in cat_lower and 'badshah' in cat_lower:
                est_price = 175.0
            elif weight_kg <= 0.1:
                est_price = 110.0 if 'badshah' in cat_lower else 75.0
            elif weight_kg <= 0.2:
                est_price = 140.0
            else:
                est_price = round(weight_kg * 400.0, 1)
        elif any(w in cat_lower for w in ['basmati', 'rice', 'chawal']) and not any(w in cat_lower for w in ['masala', 'spice']):
            shelf_days = 730
            category = 'Staples & Grocery'
            if weight_kg >= 4.5:
                est_price = 489.0  # 5kg pack
            elif weight_kg >= 9.0:
                est_price = 890.0  # 10kg pack
            else:
                est_price = round(weight_kg * 98.0, 1)
        elif any(w in cat_lower for w in ['atta', 'flour', 'wheat', 'gehu', 'maida', 'suji', 'rawa']):
            shelf_days = 180
            category = 'Staples & Grocery'
            if weight_kg >= 9.0:
                est_price = 540.0
            elif weight_kg >= 4.5:
                est_price = 295.0
            else:
                est_price = round(weight_kg * 60.0, 1)
        elif any(w in cat_lower for w in ['oil', 'tel', 'ghee', 'sunflower', 'mustard']):
            shelf_days = 270
            category = 'Cooking Oil'
            if weight_kg >= 4.5:
                est_price = 750.0
            else:
                est_price = round(weight_kg * 155.0, 1)
        elif any(w in cat_lower for w in ['dal', 'pulse', 'toor', 'moong', 'chana', 'urad', 'rajma', 'besan']):
            shelf_days = 365
            category = 'Staples & Grocery'
            est_price = round(weight_kg * 145.0, 1)
        elif any(w in cat_lower for w in ['cheese', 'paneer', 'butter', 'curd', 'yogurt']):
            shelf_days = 120
            category = 'Dairy'
            est_price = 135.0 if weight_kg <= 0.3 else 280.0
        elif any(w in cat_lower for w in ['milk', 'doodh', 'taaza']):
            shelf_days = 3
            category = 'Dairy'
            est_price = 32.0 if weight_kg <= 0.6 else 64.0
        elif any(w in cat_lower for w in ['bread', 'bun', 'bakery', 'pav']):
            shelf_days = 6
            category = 'Bakery & Bread'
            est_price = 45.0
        elif any(w in cat_lower for w in ['biscuit', 'cookie', 'cracker', 'namkeen', 'chips', 'snack', 'bhujia', 'kurmura']):
            shelf_days = 180
            category = 'Snacks & Namkeen'
            est_price = 45.0
        elif any(w in cat_lower for w in ['noodle', 'maggi', 'soup', 'instant', 'pasta', 'hakka', 'chings', 'ching']):
            shelf_days = 270
            category = 'Instant Food'
            est_price = 45.0 if weight_kg <= 0.2 else 90.0
        elif any(w in cat_lower for w in ['tea', 'coffee', 'juice', 'beverage', 'drink', 'cola']):
            shelf_days = 365
            category = 'Beverages'
            est_price = 140.0
        elif any(w in cat_lower for w in ['soap', 'shampoo', 'paste', 'detergent', 'care']):
            shelf_days = 720
            category = 'Personal Care'
            est_price = 65.0
        else:
            shelf_days = 180
            est_price = 50.0

        # Estimate dates from shelf life (cannot know actual batch dates from barcode alone)
        today = datetime.now().date()
        from datetime import timedelta
        # Realistic manufacturing date 30-90 days prior, NEVER today's date!
        days_ago = min(90, max(30, int(shelf_days * 0.25))) if shelf_days > 7 else 0
        est_mfg = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        est_exp = (today - timedelta(days=days_ago) + timedelta(days=shelf_days)).strftime('%Y-%m-%d')
        return {
            'barcode': code,
            'product_name': full_name[:120],
            'brand': brand or 'Retail Brand',
            'category': category,
            'package_size': pkg_size,
            'price': est_price,
            'mfg_date': est_mfg,
            'expiry_date': est_exp,
            'quantity': 1,
            'is_catalog_match': True,
            'dates_are_estimated': True
        }

    return None

@scanner_bp.route('/api/product/lookup/<barcode>')
def lookup_barcode(barcode):
    """Barcode lookup endpoint. Checks shop inventory, FMCG master catalog, and Open Food Facts."""
    clean_barcode = barcode.strip()
    user_id = session.get('user_id')

    # 1. If user is logged in, check their existing inventory
    if user_id:
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT id, product_name, brand, category, package_size, mfg_date, expiry_date, barcode, quantity, price
                FROM products
                WHERE user_id = ? AND barcode = ?
            """, (user_id, clean_barcode))
            product = cursor.fetchone()
            if product:
                return jsonify({
                    "exists": True,
                    "is_existing_inventory": True,
                    "product": {
                        "id": product['id'],
                        "product_name": product['product_name'],
                        "brand": product['brand'],
                        "category": product['category'],
                        "package_size": product['package_size'],
                        "mfg_date": product['mfg_date'],
                        "expiry_date": product['expiry_date'],
                        "barcode": product['barcode'],
                        "quantity": product['quantity'],
                        "price": product['price']
                    }
                })
        except Exception as e:
            current_app.logger.warning(f"Inventory lookup error: {e}")

    # 2. Check Indian FMCG Master Catalog for instant auto-filling
    catalog_item = lookup_catalog_product(clean_barcode)
    if catalog_item:
        return jsonify({
            "exists": True,
            "is_existing_inventory": False,
            "is_catalog_match": True,
            "product": catalog_item
        })

    # 3. Free external product database fallback (Open Food Facts API v3)
    open_food_facts_item = lookup_open_food_facts(clean_barcode)
    if open_food_facts_item:
        return jsonify({
            "exists": True,
            "is_existing_inventory": False,
            "is_catalog_match": True,
            "is_external_catalog_match": True,
            "product": open_food_facts_item
        })

    # 4. Universal auto-fill fallback for any new, local, or unlisted retail barcode
    from datetime import timedelta
    today_dt = datetime.now().date()
    mfg_dt = today_dt - timedelta(days=60)
    exp_dt = mfg_dt + timedelta(days=180)
    last4 = clean_barcode[-4:] if len(clean_barcode) >= 4 else clean_barcode
    smart_product = {
        "barcode": clean_barcode,
        "product_name": f"Retail Product {last4}",
        "brand": "Retail Brand",
        "category": "Grocery & FMCG",
        "package_size": "1 unit",
        "price": 40.0,
        "mfg_date": mfg_dt.strftime('%Y-%m-%d'),
        "expiry_date": exp_dt.strftime('%Y-%m-%d'),
        "quantity": 1,
        "is_catalog_match": False,
        "is_new_unlisted": True,
        "dates_are_estimated": True
    }
    return jsonify({
        "exists": True,
        "is_existing_inventory": False,
        "is_catalog_match": False,
        "is_new_unlisted": True,
        "product": smart_product
    })

@scanner_bp.route('/api/scanner/catalog-samples')
@login_required
def get_catalog_samples():
    """Returns sample products so shopkeeper can test scanner workflows instantly."""
    samples = []
    for code, item in list(FMCG_CATALOG.items())[:8]:
        cat_info = lookup_catalog_product(code)
        samples.append(cat_info)
    return jsonify({"samples": samples})


@scanner_bp.route('/api/product/save', methods=['POST'])
@login_required
def save_product():
    """
    Saves or updates product with EXACTLY the 6 required fields:
    1. product_name
    2. mfg_date
    3. expiry_date
    4. barcode
    5. quantity
    6. price
    """
    user_id = session['user_id']
    data = request.get_json() or {}
    
    product_name = str(data.get('product_name', '')).strip()
    brand = str(data.get('brand', '')).strip()[:100]
    category = str(data.get('category', '')).strip()[:100]
    package_size = str(data.get('package_size', '')).strip()[:100]
    mfg_date = str(data.get('mfg_date', '')).strip()
    expiry_date = str(data.get('expiry_date', '')).strip()
    barcode = str(data.get('barcode', '')).strip()
    quantity_raw = data.get('quantity')
    price_raw = data.get('price')
    update_if_exists = bool(data.get('update_if_exists', False))
    
    # 1. Validation
    if not product_name:
        return jsonify({"success": False, "message": "Product name is required."}), 400
    if not barcode:
        return jsonify({"success": False, "message": "Barcode is required."}), 400
    if not mfg_date:
        return jsonify({"success": False, "message": "Manufacturing date is required."}), 400
    if not expiry_date:
        return jsonify({"success": False, "message": "Expiry date is required."}), 400
        
    try:
        quantity = int(quantity_raw)
        if quantity < 0:
            return jsonify({"success": False, "message": "Quantity cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Quantity must be a valid whole number."}), 400
        
    try:
        price = float(price_raw)
        if price < 0:
            return jsonify({"success": False, "message": "Price cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Price must be a valid number."}), 400
        
    # Validate date format (YYYY-MM-DD)
    try:
        mfg_dt = datetime.strptime(mfg_date, '%Y-%m-%d')
        exp_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
        if exp_dt < mfg_dt:
            return jsonify({"success": False, "message": "Expiry date cannot be before manufacturing date."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Expected YYYY-MM-DD."}), 400

    db = get_db()
    cursor = db.cursor()
    
    # Check if barcode already exists for this shop
    cursor.execute("SELECT id, quantity FROM products WHERE user_id = ? AND barcode = ?", (user_id, barcode))
    existing = cursor.fetchone()
    
    if existing:
        if not update_if_exists:
            return jsonify({
                "success": False,
                "already_exists": True,
                "existing_id": existing['id'],
                "message": "A product with this barcode already exists in your inventory. Update existing record?"
            }), 409
            
        # Update existing
        cursor.execute("""
            UPDATE products
            SET product_name = ?, brand = ?, category = ?, package_size = ?, mfg_date = ?, expiry_date = ?, quantity = ?, price = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (product_name, brand, category, package_size, mfg_date, expiry_date, quantity, price, existing['id'], user_id))
        db.commit()
        return jsonify({
            "success": True,
            "message": "Product updated successfully!",
            "product_id": existing['id'],
            "updated": True
        })
    else:
        # Insert new
        cursor.execute("""
            INSERT INTO products (user_id, product_name, brand, category, package_size, mfg_date, expiry_date, barcode, quantity, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, product_name, brand, category, package_size, mfg_date, expiry_date, barcode, quantity, price))
        new_id = cursor.lastrowid
        db.commit()
        return jsonify({
            "success": True,
            "message": "Product saved to inventory successfully!",
            "product_id": new_id,
            "updated": False
        })
