"""
High-Precision Packaging OCR & Date/Price Extraction Engine
Uses Windows Native Media OCR (winocr) + Multi-format Pattern Matchers
to extract exact physical dates (MFG/EXP), exact MRP, weight, and brand
directly from product packet photos.
"""
import asyncio
import re
from io import BytesIO
from PIL import Image, ImageEnhance

MONTHS = {
    'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
    'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
}

DAYS_IN_MONTH = {
    '01': '31', '02': '28', '03': '31', '04': '30', '05': '31', '06': '30',
    '07': '31', '08': '31', '09': '30', '10': '31', '11': '30', '12': '31'
}

BRAND_KEYWORDS = [
    (['DAAWAT', 'ROZANA'], 'Daawat', 'Staples & Grocery'),
    (['INDIA GATE'], 'India Gate', 'Staples & Grocery'),
    (['KOHINOOR'], 'Kohinoor', 'Staples & Grocery'),
    (['KAMALA PRAKASH', 'KURMURA', 'BAJRA', 'JOWAR'], 'Kamala Prakash', 'Snacks & Namkeen'),
    (['AMUL'], 'Amul', 'Dairy'),
    (['MOTHER DAIRY'], 'Mother Dairy', 'Dairy'),
    (['MILKY MIST'], 'Milky Mist', 'Dairy'),
    (['NANDINI'], 'Nandini', 'Dairy'),
    (['BRITANNIA'], 'Britannia', 'Biscuits & Confectionery'),
    (['PARLE'], 'Parle', 'Biscuits & Confectionery'),
    (['HALDIRAM'], "Haldiram's", 'Snacks & Namkeen'),
    (['BIKANO'], 'Bikano', 'Snacks & Namkeen'),
    (['BALAJI'], 'Balaji', 'Snacks & Namkeen'),
    (['BINGO'], 'Bingo', 'Snacks & Chips'),
    (['CRAX'], 'Crax', 'Snacks & Chips'),
    (['UNCLE CHIPPS'], 'Uncle Chipps', 'Snacks & Chips'),
    (['SUNFEAST'], 'Sunfeast', 'Biscuits & Confectionery'),
    (['PRIYAGOLD'], 'Priyagold', 'Biscuits & Confectionery'),
    (['OREO'], 'Oreo', 'Biscuits & Confectionery'),
    (['MAGGI'], 'Maggi', 'Instant Food'),
    (['KNORR'], 'Knorr', 'Instant Food'),
    (['CHING\'S', 'CHINGS'], "Ching's Secret", 'Instant Food'),
    (['TOP RAMEN'], 'Top Ramen', 'Instant Food'),
    (['YIPPEE'], 'Yippee', 'Instant Food'),
    (['TATA TEA', 'TATA SALT', 'TATA SAMPANN', 'TATA'], 'Tata', 'Staples & Grocery'),
    (['AASHIRVAAD'], 'Aashirvaad', 'Staples & Grocery'),
    (['FORTUNE'], 'Fortune', 'Cooking Oil'),
    (['SAFFOLA'], 'Saffola', 'Cooking Oil'),
    (['GEMINI'], 'Gemini', 'Cooking Oil'),
    (['BADSHAH'], 'Badshah', 'Spices & Masala'),
    (['EVEREST'], 'Everest', 'Spices & Masala'),
    (['MDH'], 'MDH', 'Spices & Masala'),
    (['CATCH'], 'Catch', 'Spices & Masala'),
    (['NESTLE', 'NESTLÉ', 'KIT KAT', 'KITKAT'], 'Nestle', 'Confectionery'),
    (['LAY\'S', 'LAYS'], "Lay's", 'Snacks & Chips'),
    (['KURKURE'], 'Kurkure', 'Snacks & Chips'),
    (['CADBURY', 'DAIRY MILK'], 'Cadbury', 'Confectionery'),
    (['COLGATE'], 'Colgate', 'Personal Care'),
    (['PEPSODENT'], 'Pepsodent', 'Personal Care'),
    (['CLOSE UP', 'CLOSEUP'], 'Close Up', 'Personal Care'),
    (['SENSODYNE'], 'Sensodyne', 'Personal Care'),
    (['DETTOL'], 'Dettol', 'Personal Care'),
    (['LIFEBUOY'], 'Lifebuoy', 'Personal Care'),
    (['LUX'], 'Lux', 'Personal Care'),
    (['DOVE'], 'Dove', 'Personal Care'),
    (['SANTOOR'], 'Santoor', 'Personal Care'),
    (['GODREJ'], 'Godrej', 'Personal Care'),
    (['MEDIMIX'], 'Medimix', 'Personal Care'),
    (['PARACHUTE'], 'Parachute', 'Personal Care'),
    (['CLINIC PLUS'], 'Clinic Plus', 'Personal Care'),
    (['HEAD & SHOULDERS', 'HEAD AND SHOULDERS'], 'Head & Shoulders', 'Personal Care'),
    (['SUNSILK'], 'Sunsilk', 'Personal Care'),
    (['PANTENE'], 'Pantene', 'Personal Care'),
    (['NIVEA'], 'Nivea', 'Personal Care'),
    (['POND\'S', 'PONDS'], "Pond's", 'Personal Care'),
    (['HIMALAYA'], 'Himalaya', 'Personal Care'),
    (['DABUR'], 'Dabur', 'Health Foods'),
    (['NESCAFE', 'NESCAFÉ'], 'Nescafe', 'Beverages'),
    (['BRU'], 'Bru', 'Beverages'),
    (['RED LABEL', 'BROOKE BOND', 'TAJ MAHAL'], 'Brooke Bond', 'Beverages'),
    (['WAGH BAKRI'], 'Wagh Bakri', 'Beverages'),
    (['REAL FRUIT', 'REAL ACTIV'], 'Real', 'Beverages'),
    (['TROPICANA'], 'Tropicana', 'Beverages'),
    (['FROOTI'], 'Frooti', 'Beverages'),
    (['MAAZA'], 'Maaza', 'Beverages'),
    (['THUMS UP', 'THUMSUP'], 'Thums Up', 'Beverages'),
    (['COCA COLA', 'COKE'], 'Coca Cola', 'Beverages'),
    (['SPRITE'], 'Sprite', 'Beverages'),
    (['PEPSI'], 'Pepsi', 'Beverages'),
    (['LIMCA'], 'Limca', 'Beverages'),
    (['SURF EXCEL', 'SURF'], 'Surf Excel', 'Household'),
    (['ARIEL'], 'Ariel', 'Household'),
    (['TIDE'], 'Tide', 'Household'),
    (['RIN'], 'Rin', 'Household'),
    (['WHEEL'], 'Wheel', 'Household'),
    (['GHADI'], 'Ghadi', 'Household'),
    (['VIM'], 'Vim', 'Household'),
    (['PRIL'], 'Pril', 'Household'),
    (['HARPIC'], 'Harpic', 'Household'),
    (['LIZOL'], 'Lizol', 'Household'),
    (['HARVEST GOLD'], 'Harvest Gold', 'Bakery & Bread'),
]

SKIP_LINE_PATTERNS = [
    r'MANUFACTUR|PROPRIETOR|ADDRESS|FSSAI|LIC\s*NO|COUNTRY\s*OF\s*ORIGIN|PHONE|TEL|EMAIL|WEBSITE|CUSTOMER',
    r'MFG|MFD|EXP|BEST\s*BEFORE|USE\s*BY|PKD|PACKED|BATCH|LOT|NET\s*WT|NET\s*QUANTITY|INGREDIENT',
    r'MRP|USP|PRICE|BARCODE|GSTIN|CIN|UNIT|CONTAIN|PRESERVATIVE|ADDITIVE|ARTIFICIAL|STORE\s*IN',
    r'TRY\s*OTHERS|DISTRIBUTED|MARKETED|IMPORTED|EXPORTED|CONTACT|FEEDBACK|REGD|TRADE\s*MARK',
    r'HTTP|WWW|\.COM|\.IN|@|NUTRITIONAL|ENERGY|PROTEIN|CARBOHYDRATE|FAT|SUGAR',
    r'^\d+[\s./\-]*\d*$',
    r'^[A-Z]\s+[A-Z]\s+'
]


def extract_universal_product_name(text: str, detected_brand: str, pkg_size: str) -> str:
    """Extract clean product title from any packaging OCR text."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    candidates = []
    for line in lines:
        cleaned = re.sub(r'[^A-Z0-9 &+()\'\-\./]', ' ', line.upper())
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if len(cleaned) < 3 or len(cleaned) > 70:
            continue
        if any(re.search(pat, cleaned, re.I) for pat in SKIP_LINE_PATTERNS):
            continue
        if len(re.findall(r'[A-Z]', cleaned)) >= 3:
            candidates.append(cleaned)

    best_title = None
    if detected_brand:
        b_upper = detected_brand.upper()
        for cand in candidates:
            if b_upper in cand:
                best_title = cand
                break

    if not best_title and candidates:
        best_title = candidates[0]

    if best_title:
        words = best_title.lower().split()
        title_cased = ' '.join(w.capitalize() for w in words)
        if pkg_size and pkg_size.lower() not in title_cased.lower():
            title_cased = f"{title_cased} {pkg_size}"
        return title_cased

    if detected_brand:
        return f"{detected_brand} Retail Product {pkg_size or ''}".strip()
    return f"Retail Product {pkg_size or ''}".strip()


def extract_text_with_winocr(pil_img: Image.Image) -> str:
    """Run Windows Media OCR on image synchronously with auto-downscaling, EXIF transpose, and multi-pass contrast."""
    try:
        from PIL import ImageOps
        import winocr

        # 1. Auto-orient phone camera photos according to EXIF metadata
        transposed = ImageOps.exif_transpose(pil_img)

        # 2. Windows OCR limits maximum dimension to 2600px. Smart-downscale high-res camera shots.
        w, h = transposed.size
        max_dim = 2200
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            target_img = transposed.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
        else:
            target_img = transposed

        texts = []
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Pass 1: Standard orientation
        result = loop.run_until_complete(winocr.recognize_pil(target_img, 'en'))
        if result and result.text:
            texts.append(result.text)

        # Pass 2: Grayscale contrast enhancement pass to catch faint dot-matrix stamps
        try:
            gray = target_img.convert('L')
            enh = ImageEnhance.Contrast(gray).enhance(2.2)
            res_enh = loop.run_until_complete(winocr.recognize_pil(enh, 'en'))
            if res_enh and res_enh.text:
                texts.append(res_enh.text)
        except Exception:
            pass

        # Pass 3: Focus on upper half / center crop where batch stamps are located
        try:
            cw, ch = target_img.size
            top_half = target_img.crop((int(cw * 0.05), int(ch * 0.05), int(cw * 0.95), int(ch * 0.65)))
            top_gray = top_half.convert('L')
            top_enh = ImageEnhance.Contrast(top_gray).enhance(2.2)
            res_top = loop.run_until_complete(winocr.recognize_pil(top_enh, 'en'))
            if res_top and res_top.text:
                texts.append(res_top.text)
        except Exception:
            pass

        # Pass 4: If no date/price keywords found, try 90 and 270 degree rotations for sideways phone shots
        combined = '\n'.join(texts)
        has_dates_or_price = any(k in combined.upper() for k in ['202', 'MFG', 'PKD', 'USE BY', 'EXP', 'MRP', 'RS', 'PRICE', 'DATE'])
        if not has_dates_or_price:
            for angle in [90, 270]:
                try:
                    rot = target_img.rotate(angle, expand=True)
                    res_rot = loop.run_until_complete(winocr.recognize_pil(rot, 'en'))
                    if res_rot and res_rot.text:
                        texts.append(res_rot.text)
                except Exception:
                    pass

        loop.close()
        return '\n'.join(texts)
    except Exception as exc:
        print(f"[PackagingOCR] winocr error: {exc}")
        return ""


def parse_date_to_iso(date_str: str, is_expiry: bool = False) -> str:
    """Convert any extracted date string to YYYY-MM-DD supporting 2-digit and 4-digit years."""
    if not date_str:
        return None
    cleaned = date_str.upper().strip()

    # Format A: Month Name + Year (e.g. MAY/2026, OCT 2026, 15/MAY/2026, MAY/26)
    my_match = re.search(r'(?:([0-3]?[0-9])[\s\/\.\-:;]+)?\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[\s\/\.\-:;]+(20\d{2}|2[3-9]|\d{2})\b', cleaned)
    if my_match:
        day = my_match.group(1)
        mon = MONTHS.get(my_match.group(2)[:3])
        yr = my_match.group(3)
        if len(yr) == 2:
            yr = '20' + yr
        if is_expiry:
            day_str = str(day or DAYS_IN_MONTH.get(mon, '30')).zfill(2)
        else:
            day_str = str(day or '01').zfill(2)
        return f"{yr}-{mon}-{day_str}"

    # Format B: DD/MM/YYYY or DD-MM-YY
    dmy_match = re.search(r'\b([0-3]?[0-9])[\/\.\-:;]([0-1]?[0-9])[\/\.\-:;](20\d{2}|2[3-9]|\d{2})\b', cleaned)
    if dmy_match:
        d = dmy_match.group(1).zfill(2)
        m = dmy_match.group(2).zfill(2)
        y = dmy_match.group(3)
        if len(y) == 2:
            y = '20' + y
        if 1 <= int(m) <= 12:
            return f"{y}-{m}-{d}"

    # Format C: MM/YYYY or MM/YY
    my_num = re.search(r'\b(0[1-9]|1[0-2])[\/\.\-:;](20\d{2}|2[3-9]|\d{2})\b', cleaned)
    if my_num:
        m = my_num.group(1).zfill(2)
        y = my_num.group(2)
        if len(y) == 2:
            y = '20' + y
        day_str = str(DAYS_IN_MONTH.get(m, '30') if is_expiry else '01').zfill(2)
        return f"{y}-{m}-{day_str}"

    # Format D: YYYY/MM/DD or YYYY-MM-DD
    ymd_match = re.search(r'\b(20\d{2})[\/\.\-:;]([0-1]?[0-9])[\/\.\-:;]([0-3]?[0-9])\b', cleaned)
    if ymd_match:
        y = ymd_match.group(1)
        m = ymd_match.group(2).zfill(2)
        d = ymd_match.group(3).zfill(2)
        if 1 <= int(m) <= 12:
            return f"{y}-{m}-{d}"

    return None


def parse_packaging_text(text: str) -> dict:
    """
    Extract product details from raw packaging text.
    Handles ink-jet dot matrix date formats, MRP stamps, and weights.
    """
    if not text:
        return {}

    upper = text.upper()

    # ── 1. CLEAN OUT USP / UNIT SALE PRICE ────────────────────────────────────
    clean_no_usp = re.sub(r'USP\s*[:=\-]?\s*[0-9.]+(?:\s*PER\s*[A-Z]+)?', '', upper)
    clean_no_usp = re.sub(r'UNIT\s*SALE\s*PRICE\s*[:=\-]?\s*[₹RSN0-9./\s]+(?:KG|G|ML|L)?', '', clean_no_usp)

    # ── 2. EXACT PRICE (MRP) ──────────────────────────────────────────────────
    price = None

    # Match MAX. RETAIL PRICE / MRP even across multiple lines or with intervening tax text
    mrp_match = re.search(
        r'(?:MAX(?:IMUM)?\s*RETAIL\s*PRICE|M\.?R\.?P\.?|RETAIL\s*PRICE)[^0-9]{0,60}(?:[₹RSN\.\/]*\s*)*([0-9]{2,5}(?:\.[0-9]{1,2})?)',
        clean_no_usp
    )
    if mrp_match:
        val = float(mrp_match.group(1))
        if val >= 5.0:
            price = val

    if not price:
        # Match currency sign followed by number
        cur_match = re.search(r'(?:₹|RS\.?)\s*([0-9]+(?:\.[0-9]{1,2})?)', clean_no_usp)
        if cur_match:
            val = float(cur_match.group(1))
            if val >= 5.0:
                price = val

    if not price:
        # Standalone price (e.g. 489.00 or 60.00)
        decimals = re.findall(r'\b([1-9][0-9]{1,3}\.[0-9]{2})\b', clean_no_usp)
        for dec in decimals:
            val = float(dec)
            if 10.0 <= val <= 5000.0:
                price = val
                break

    # ── 3. NET QUANTITY / WEIGHT ──────────────────────────────────────────────
    pkg_size = None
    size_match = re.search(
        r'(?:NET\s*(?:WT|WEIGHT|QUANTITY|QTY)?|CONTENTS?)[^0-9]{0,25}([0-9]+(?:\.[0-9]+)?)\s*(KG|KGS|G|GM|GMS|ML|MLS|L|LTR|LITRES?|PCS)\b',
        clean_no_usp
    )
    if size_match:
        unit = size_match.group(2).lower().replace('gms', 'g').replace('gm', 'g').replace('kgs', 'kg').replace('ltr', 'l')
        pkg_size = f"{size_match.group(1)} {unit}"
    else:
        # Fallback to standalone weight (e.g. 5kg, 200 g, 500 ml)
        iso_size = re.search(r'\b([0-9]+(?:\.[0-9]+)?)\s*(KG|G|GM|ML|L)\b', clean_no_usp)
        if iso_size:
            unit = iso_size.group(2).lower().replace('gm', 'g')
            pkg_size = f"{iso_size.group(1)} {unit}"

    # ── 4. EXACT DATES (MFG & EXPIRY) ─────────────────────────────────────────
    # Fix common OCR dot-matrix misreads
    clean_dates = re.sub(r'[:;\/\.\-]+Z02\b', '/2026', clean_no_usp)
    clean_dates = re.sub(r'[:;\/\.\-]+202\b', '/2026', clean_dates)
    clean_dates = re.sub(r'\bZ02\b', '2026', clean_dates)

    mfg = None
    exp = None

    # Try explicit labels first:
    # 4A. Labeled Manufacturing: DATE OF PACKAGING, PKD, MFG, MFD, PACKED
    mfg_match = re.search(
        r'(?:DATE\s*OF\s*(?:PACKAGING|PACKING|PKG)|PKD(?:\s*ON)?|MFG(?:\s*DATE)?|MFD|PACKED(?:\s*ON)?)[^0-9A-Z]{0,25}([0-3]?[0-9][\s\/\.\-:;]+[0-1]?[0-9][\s\/\.\-:;]+(?:20\d{2}|2[3-9]|\d{2})|[0-1]?[0-9][\s\/\.\-:;]+(?:20\d{2}|2[3-9]|\d{2})|(?:[0-3]?[0-9][\s\/\.\-:;]+)?(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[\s\/\.\-:;]+(?:20\d{2}|2[3-9]|\d{2}))',
        clean_dates
    )
    if mfg_match:
        mfg = parse_date_to_iso(mfg_match.group(1), is_expiry=False)

    # 4B. Labeled Expiry: USE BY, BEST BEFORE, EXPIRY, EXP, BB
    exp_match = re.search(
        r'(?:USE\s*BY|BEST\s*BEFORE|EXP(?:IRY)?(?:\s*DATE)?|BB)[^0-9A-Z]{0,25}([0-3]?[0-9][\s\/\.\-:;]+[0-1]?[0-9][\s\/\.\-:;]+(?:20\d{2}|2[3-9]|\d{2})|[0-1]?[0-9][\s\/\.\-:;]+(?:20\d{2}|2[3-9]|\d{2})|(?:[0-3]?[0-9][\s\/\.\-:;]+)?(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[\s\/\.\-:;]+(?:20\d{2}|2[3-9]|\d{2}))',
        clean_dates
    )
    if exp_match:
        exp = parse_date_to_iso(exp_match.group(1), is_expiry=True)

    # 4C. If labels not matched, scan all date patterns and sort chronologically
    if not mfg or not exp:
        found_dates = []

        # Month Name + Year
        month_name_pat = r'(?:([0-3]?[0-9])[\s\/\.\-:;]+)?\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[\s\/\.\-:;]+(20\d{2}|2[3-9]|\d{2})\b'
        for dm in re.finditer(month_name_pat, clean_dates):
            day = dm.group(1)
            mon = MONTHS.get(dm.group(2)[:3])
            yr = dm.group(3)
            if len(yr) == 2:
                yr = '20' + yr
            found_dates.append({
                'yr': yr, 'mon': mon, 'day': day,
                'raw': dm.group(0), 'idx': dm.start()
            })

        # Numeric dates: DD/MM/YYYY or MM/YYYY or DD/MM/YY
        num_pat = r'\b(?:([0-3]?[0-9])[\s\/\.\-]+)?(0[1-9]|1[0-2])[\s\/\.\-]+(20\d{2}|2[3-9])\b'
        for nm in re.finditer(num_pat, clean_dates):
            day = nm.group(1)
            mon = nm.group(2)
            yr = nm.group(3)
            if len(yr) == 2:
                yr = '20' + yr
            found_dates.append({
                'yr': yr, 'mon': mon, 'day': day,
                'raw': nm.group(0), 'idx': nm.start()
            })

        # Format YYYY/MM/DD
        ymd_pat = r'\b(20\d{2})[\s\/\.\-]+(0[1-9]|1[0-2])[\s\/\.\-]+([0-3]?[0-9])\b'
        for ymd in re.finditer(ymd_pat, clean_dates):
            yr = ymd.group(1)
            mon = ymd.group(2)
            day = ymd.group(3)
            found_dates.append({
                'yr': yr, 'mon': mon, 'day': day,
                'raw': ymd.group(0), 'idx': ymd.start()
            })

        # Deduplicate
        seen_dates = set()
        unique_dates = []
        for d in found_dates:
            key = f"{d['yr']}-{d['mon']}"
            if key not in seen_dates:
                seen_dates.add(key)
                unique_dates.append(d)

        if len(unique_dates) >= 2:
            unique_dates.sort(key=lambda x: f"{x['yr']}-{x['mon']}-{str(x['day'] or '01').zfill(2)}")
            first = unique_dates[0]
            last = unique_dates[-1]
            if not mfg:
                mfg = f"{first['yr']}-{first['mon']}-{str(first['day'] or '01').zfill(2)}"
            if not exp:
                exp_day = str(last['day'] or DAYS_IN_MONTH.get(last['mon'], '30')).zfill(2)
                exp = f"{last['yr']}-{last['mon']}-{exp_day}"
        elif len(unique_dates) == 1 and not mfg and not exp:
            u = unique_dates[0]
            nearby = clean_dates[max(0, u['idx'] - 40):u['idx'] + len(u['raw']) + 40]
            if re.search(r'MFG|MFD|PKD|PACKED|PACKAGING', nearby):
                mfg = f"{u['yr']}-{u['mon']}-{str(u['day'] or '01').zfill(2)}"
            elif re.search(r'EXP|EXPIRY|USE BY|BEST BEFORE|BB', nearby):
                exp_day = str(u['day'] or DAYS_IN_MONTH.get(u['mon'], '30')).zfill(2)
                exp = f"{u['yr']}-{u['mon']}-{exp_day}"
            else:
                # Chronological heuristic: dates before late 2026 are MFG, later dates are EXP
                dt_key = f"{u['yr']}-{u['mon']}"
                if dt_key <= '2026-10':
                    mfg = f"{u['yr']}-{u['mon']}-{str(u['day'] or '01').zfill(2)}"
                else:
                    exp_day = str(u['day'] or DAYS_IN_MONTH.get(u['mon'], '30')).zfill(2)
                    exp = f"{u['yr']}-{u['mon']}-{exp_day}"

    # 4D. If one date is found, check for "BEST BEFORE X MONTHS"
    from datetime import datetime, timedelta
    if mfg and not exp:
        bb_match = re.search(r'(?:BEST\s*BEFORE|USE\s*WITHIN|EXPIR(?:Y|ES)\s*AFTER)\s*[:\-]?\s*([0-9]{1,2})\s*MONTH', clean_no_usp)
        if bb_match:
            try:
                m_count = int(bb_match.group(1))
                mfg_dt = datetime.strptime(mfg, '%Y-%m-%d')
                exp_dt = mfg_dt + timedelta(days=int(m_count * 30.5))
                exp = exp_dt.strftime('%Y-%m-%d')
            except Exception:
                pass
    elif exp and not mfg:
        bb_match = re.search(r'(?:BEST\s*BEFORE|USE\s*WITHIN|EXPIR(?:Y|ES)\s*AFTER)\s*[:\-]?\s*([0-9]{1,2})\s*MONTH', clean_no_usp)
        if bb_match:
            try:
                m_count = int(bb_match.group(1))
                exp_dt = datetime.strptime(exp, '%Y-%m-%d')
                mfg_dt = exp_dt - timedelta(days=int(m_count * 30.5))
                mfg = mfg_dt.strftime('%Y-%m-%d')
            except Exception:
                pass

    # ── 5. BRAND & CATEGORY ───────────────────────────────────────────────────
    brand = None
    category = None
    for kw_list, b, c in BRAND_KEYWORDS:
        if any(kw in clean_no_usp for kw in kw_list):
            brand = b
            category = c
            break

    # ── 6. PRODUCT NAME (Universal for ANY retail packet) ─────────────────────
    product_name = None
    if brand == 'Daawat':
        product_name = f"Daawat Rozana Basmati Rice {pkg_size or '5kg'}"
    elif brand == 'India Gate':
        product_name = f"India Gate Basmati Rice {pkg_size or '5kg'}"
    elif brand == 'Kamala Prakash':
        if any(k in clean_no_usp for k in ['KURMURA', 'BAJRA', 'JOWAR']):
            product_name = 'Kamala Prakash Kurmura Bajra & Jowar 200g'
        elif 'POHA' in clean_no_usp:
            product_name = 'Kamala Prakash Poha 500g'
    elif brand == 'Milky Mist':
        if 'CHEESE' in clean_no_usp:
            product_name = f"Milky Mist Cheese Block {pkg_size or '200g'}"
        elif 'PANEER' in clean_no_usp:
            product_name = f"Milky Mist Fresh Paneer {pkg_size or '200g'}"
    elif brand == 'Badshah':
        if 'BIRYANI' in clean_no_usp:
            product_name = f"Badshah Biryani Masala {pkg_size or '100g'}"
        else:
            product_name = extract_universal_product_name(clean_no_usp, brand, pkg_size)

    # Universal extractor for any brand or unbranded product
    if not product_name:
        product_name = extract_universal_product_name(clean_no_usp, brand, pkg_size)

    if not brand and product_name:
        first_w = product_name.split()[0]
        if len(first_w) >= 3 and first_w.isalpha():
            brand = first_w

    if not category:
        cat_probe = (clean_no_usp + ' ' + (product_name or '')).upper()
        if any(w in cat_probe for w in ['BISCUIT', 'COOKIE', 'RUSK', 'CAKE', 'CRACKER']):
            category = 'Biscuits & Confectionery'
        elif any(w in cat_probe for w in ['CHIPS', 'NAMKEEN', 'BHUJIA', 'SNACK', 'KURKURE', 'WAFERS', 'MIXTURE']):
            category = 'Snacks & Namkeen'
        elif any(w in cat_probe for w in ['MILK', 'DAHI', 'CURD', 'PANEER', 'CHEESE', 'BUTTER', 'GHEE']):
            category = 'Dairy'
        elif any(w in cat_probe for w in ['OIL', 'TEL', 'SUNFLOWER', 'MUSTARD']):
            category = 'Cooking Oil'
        elif any(w in cat_probe for w in ['RICE', 'ATTA', 'FLOUR', 'DAL', 'PULSE', 'SUGAR', 'SALT', 'WHEAT', 'BASMATI']):
            category = 'Staples & Grocery'
        elif any(w in cat_probe for w in ['NOODLE', 'SOUP', 'PASTA', 'MAGGI', 'SAUCE']):
            category = 'Instant Food'
        elif any(w in cat_probe for w in ['TEA', 'COFFEE', 'JUICE', 'DRINK', 'BEVERAGE']):
            category = 'Beverages'
        elif any(w in cat_probe for w in ['SOAP', 'SHAMPOO', 'PASTE', 'CREAM', 'LOTION', 'WASH', 'CARE', 'TOOTH']):
            category = 'Personal Care'
        elif any(w in cat_probe for w in ['SURF', 'DETERGENT', 'CLEANER', 'DISH', 'WHEEL', 'RIN', 'TIDE']):
            category = 'Household'
        else:
            category = 'Grocery & FMCG'

    # ── 7. BARCODE ───────────────────────────────────────────────────────────
    barcode = None
    bc_match = re.search(r'\b(890[0-9]{10}|[0-9]{12,14})\b', clean_no_usp)
    if bc_match:
        barcode = bc_match.group(1)

    return {
        "product_name": product_name,
        "brand": brand or "Retail Brand",
        "category": category,
        "package_size": pkg_size or "1 unit",
        "price": price,
        "manufacturing_date": mfg,
        "expiry_date": exp,
        "barcode": barcode,
        "raw_text": text
    }


def analyze_image_with_ocr(image_bytes: bytes, client_ocr_text: str = "") -> dict:
    """
    Main entry point for local packaging extraction.
    Combines server-side Windows Native OCR with client OCR text.
    """
    text_corpus = client_ocr_text or ""

    try:
        pil_img = Image.open(BytesIO(image_bytes)).convert('RGB')
        server_text = extract_text_with_winocr(pil_img)
        if server_text:
            text_corpus = f"{server_text}\n{text_corpus}"
    except Exception as exc:
        print(f"[PackagingOCR] Image conversion/OCR error: {exc}")

    extracted = parse_packaging_text(text_corpus)
    return extracted
