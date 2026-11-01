import os
import unittest
import tempfile
import json
from datetime import datetime, timedelta
from app import create_app
from database import get_db
from ai.expiry_predictor import calculate_days_until_expiry, predict_expiry_risk
from ai.pricing_engine import get_pricing_recommendation
from ai.fmcg_catalog import lookup_catalog_product
from translations import TRANSLATIONS, get_text

class ExpiryGuardAITestCase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp()
        os.close(fd) # Close immediately on Windows so SQLite can open it without sharing violation
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-secret-key'
        })
        self.client = self.app.test_client()

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        except OSError:
            pass

    # 1. Admin Credentials & Shop Name Tests
    def test_admin_credentials_and_shop_name(self):
        res = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin 123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Gupta Chaat &amp; Stores', res.data)

    def test_tenant_data_isolation(self):
        # Shop A
        self.client.post('/register', data={
            'shop_name': 'Shop A',
            'username': 'shop_a',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        # Add custom product to Shop A
        self.client.post('/api/product/save', json={
            'product_name': 'Secret Product A',
            'mfg_date': '2026-01-01',
            'expiry_date': '2026-12-31',
            'barcode': '1111111111111',
            'quantity': 10,
            'price': 50.0
        })

        # Logout Shop A and register Shop B
        self.client.get('/logout')
        self.client.post('/register', data={
            'shop_name': 'Shop B',
            'username': 'shop_b',
            'password': 'password123',
            'confirm_password': 'password123'
        })

        # Shop B searches for Shop A's barcode -> must NOT be found in inventory
        res = self.client.get('/api/product/lookup/1111111111111')
        data = res.get_json()
        self.assertFalse(data.get('is_existing_inventory', False))

        # Shop B attempts to sell Shop A's barcode -> must fail 404
        sale_res = self.client.post('/api/sales/record', json={
            'barcode': '1111111111111',
            'quantity_sold': 1
        })
        self.assertEqual(sale_res.status_code, 404)

    # 2. Exact 6-Field Product Management Tests
    def test_save_product_exact_six_fields(self):
        # Login admin user
        self.client.post('/login', data={'username': 'admin', 'password': 'admin 123'})

        # Save valid product with exact 6 fields
        res = self.client.post('/api/product/save', json={
            'product_name': 'Tata Tea Gold 250g',
            'mfg_date': '2026-02-01',
            'expiry_date': '2026-11-01',
            'barcode': '8901052000015',
            'quantity': 20,
            'price': 140.0
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        # Duplicate barcode detection
        dup_res = self.client.post('/api/product/save', json={
            'product_name': 'Tata Tea Gold 250g',
            'mfg_date': '2026-02-01',
            'expiry_date': '2026-11-01',
            'barcode': '8901052000015',
            'quantity': 25,
            'price': 140.0,
            'update_if_exists': False
        })
        self.assertEqual(dup_res.status_code, 409)

        # Invalid date order (expiry before mfg)
        invalid_date_res = self.client.post('/api/product/save', json={
            'product_name': 'Bad Product',
            'mfg_date': '2026-08-01',
            'expiry_date': '2026-02-01',
            'barcode': '8901052999999',
            'quantity': 5,
            'price': 20.0
        })
        self.assertEqual(invalid_date_res.status_code, 400)

        # Negative quantity rejection
        neg_qty_res = self.client.post('/api/product/save', json={
            'product_name': 'Bad Product',
            'mfg_date': '2026-01-01',
            'expiry_date': '2026-12-01',
            'barcode': '8901052888888',
            'quantity': -5,
            'price': 20.0
        })
        self.assertEqual(neg_qty_res.status_code, 400)

    # 3. Quick Sales & Overselling Prevention Tests
    def test_quick_sales_transaction_and_overselling_prevention(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin 123'})

        # Create a test item with quantity 5
        self.client.post('/api/product/save', json={
            'product_name': 'Lays Classic Salted',
            'mfg_date': '2026-01-01',
            'expiry_date': '2026-08-01',
            'barcode': '8901491100012',
            'quantity': 5,
            'price': 20.0
        })

        # Test lookup
        lookup_res = self.client.get('/api/sales/lookup/8901491100012')
        self.assertEqual(lookup_res.status_code, 200)
        self.assertEqual(lookup_res.get_json()['product']['available_quantity'], 5)

        # Successful sale: sell 2 units
        sale_res = self.client.post('/api/sales/record', json={
            'barcode': '8901491100012',
            'quantity_sold': 2
        })
        self.assertEqual(sale_res.status_code, 200)
        sale_data = sale_res.get_json()
        self.assertTrue(sale_data['success'])
        self.assertEqual(sale_data['sold_qty'], 2)
        self.assertEqual(sale_data['remaining_stock'], 3)
        self.assertEqual(sale_data['total_amount'], 40.0)

        # Overselling rejection: try to sell 4 when only 3 remain
        oversell_res = self.client.post('/api/sales/record', json={
            'barcode': '8901491100012',
            'quantity_sold': 4
        })
        self.assertEqual(oversell_res.status_code, 400)

        # Zero or negative sale rejection
        zero_res = self.client.post('/api/sales/record', json={
            'barcode': '8901491100012',
            'quantity_sold': 0
        })
        self.assertEqual(zero_res.status_code, 400)

    def test_inventory_decrement_and_increment(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin 123'})

        # Create a test item with quantity 2
        save_res = self.client.post('/api/product/save', json={
            'product_name': 'Test Inventory Decrement Item',
            'mfg_date': '2026-01-01',
            'expiry_date': '2026-10-01',
            'barcode': '8909999000011',
            'quantity': 2,
            'price': 55.0
        })
        self.assertEqual(save_res.status_code, 200)
        prod_id = save_res.get_json()['product_id']

        # Decrement by 1
        dec1 = self.client.post(f'/api/product/decrement/{prod_id}')
        self.assertEqual(dec1.status_code, 200)
        self.assertEqual(dec1.get_json()['new_quantity'], 1)

        # Decrement by 1 again -> 0
        dec2 = self.client.post(f'/api/product/decrement/{prod_id}')
        self.assertEqual(dec2.status_code, 200)
        self.assertEqual(dec2.get_json()['new_quantity'], 0)

        # Decrement when 0 -> reject with 400
        dec3 = self.client.post(f'/api/product/decrement/{prod_id}')
        self.assertEqual(dec3.status_code, 400)

        # Increment by 1 -> 1
        inc1 = self.client.post(f'/api/product/increment/{prod_id}')
        self.assertEqual(inc1.status_code, 200)
        self.assertEqual(inc1.get_json()['new_quantity'], 1)

    # 4. FMCG Catalog Lookup & Auto-fill Test
    def test_fmcg_catalog_lookup(self):
        from datetime import datetime, timedelta
        today = datetime.now().date()
        # Look up Britannia Bread (no hardcoded batch dates — estimated from shelf life)
        item = lookup_catalog_product("8901063102123")
        self.assertIsNotNone(item)
        self.assertIn("Britannia", item['product_name'])
        self.assertEqual(item['price'], 45.0)
        # Estimated dates must now be populated (today as mfg, today + shelf_life as expiry)
        self.assertIsNotNone(item['mfg_date'])
        self.assertIsNotNone(item['expiry_date'])
        self.assertTrue(item.get('dates_are_estimated'), "Britannia Bread should have dates_are_estimated=True")
        # mfg_date should be today
        self.assertEqual(item['mfg_date'], today.strftime('%Y-%m-%d'))
        # expiry_date should be today + 5 days (shelf_life_days=5 for bread)
        expected_exp = (today + timedelta(days=5)).strftime('%Y-%m-%d')
        self.assertEqual(item['expiry_date'], expected_exp)
        self.assertEqual(item['quantity'], 1)

        # Look up Kamala Prakash Kurmura (exact verified packet dates — NOT estimated)
        kp_item = lookup_catalog_product("8902901251951")
        self.assertIsNotNone(kp_item)
        self.assertEqual(kp_item['price'], 60.0)
        self.assertEqual(kp_item['mfg_date'], "2026-05-01")
        self.assertEqual(kp_item['expiry_date'], "2026-10-31")
        self.assertFalse(kp_item.get('dates_are_estimated'), "Kamala Prakash should have dates_are_estimated=False")

        # Look up Daawat Rozana Basmati Rice 5kg (exact verified packaging dates & MRP)
        daawat = lookup_catalog_product("8901537007116")
        self.assertIsNotNone(daawat)
        self.assertEqual(daawat['price'], 489.0)
        self.assertEqual(daawat['mfg_date'], "2026-05-01")
        self.assertEqual(daawat['expiry_date'], "2028-04-30")
        self.assertFalse(daawat.get('dates_are_estimated'))

        # Look up Ching's Secret Veg Hakka Noodles 140g (exact retail dates & MRP)
        chings = lookup_catalog_product("8901595851218")
        self.assertIsNotNone(chings)
        self.assertEqual(chings['price'], 45.0)
        self.assertEqual(chings['mfg_date'], "2026-03-15")
        self.assertEqual(chings['expiry_date'], "2026-12-14")
        self.assertFalse(chings.get('dates_are_estimated'))

        # Look up Badshah Biryani Masala 100g (exact retail dates & MRP)
        badshah = lookup_catalog_product("8901774002028")
        self.assertIsNotNone(badshah)
        self.assertEqual(badshah['price'], 175.0)
        self.assertEqual(badshah['mfg_date'], "2026-04-16")
        self.assertEqual(badshah['expiry_date'], "2027-10-15")
        self.assertFalse(badshah.get('dates_are_estimated'))

    # 5. Multilingual Chatbot Tests
    def test_multilingual_chatbot(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin 123'})

        # English query
        res_en = self.client.post('/api/chatbot/message', json={
            'message': 'Which products are expiring soon?',
            'lang': 'en'
        })
        self.assertEqual(res_en.status_code, 200)
        data_en = res_en.get_json()
        self.assertIn('reply', data_en)

        # Hindi query
        res_hi = self.client.post('/api/chatbot/message', json={
            'message': 'दुकान में कौन सा सामान कम है?',
            'lang': 'hi'
        })
        self.assertEqual(res_hi.status_code, 200)
        data_hi = res_hi.get_json()
        self.assertIn('reply', data_hi)

        # Marathi query
        res_mr = self.client.post('/api/chatbot/message', json={
            'message': 'आजची एकूण विक्री किती झाली?',
            'lang': 'mr'
        })
        self.assertEqual(res_mr.status_code, 200)
        data_mr = res_mr.get_json()
        self.assertIn('reply', data_mr)

    # 6. Expiry Calculation & Dynamic Pricing Tests
    def test_expiry_and_pricing_engine(self):
        today = datetime.now()
        
        # Test expired product
        exp_date_past = (today - timedelta(days=5)).strftime('%Y-%m-%d')
        days_past = calculate_days_until_expiry(exp_date_past)
        self.assertEqual(days_past, -5)
        
        expired_product = {
            'product_name': 'Old Milk',
            'expiry_date': exp_date_past,
            'quantity': 4,
            'price': 30.0
        }
        pricing = get_pricing_recommendation(expired_product, sales_rate=1.0)
        self.assertFalse(pricing['has_discount']) # Expired food cannot be sold

        # Test urgent product (expires in 2 days) -> 40% discount
        exp_date_soon = (today + timedelta(days=2)).strftime('%Y-%m-%d')
        urgent_product = {
            'product_name': 'Fresh Paneer',
            'expiry_date': exp_date_soon,
            'quantity': 10,
            'price': 100.0
        }
        pricing_urgent = get_pricing_recommendation(urgent_product, sales_rate=0.5)
        self.assertTrue(pricing_urgent['has_discount'])
        self.assertEqual(pricing_urgent['discount_percent'], 40)
        self.assertEqual(pricing_urgent['suggested_price'], 60.0)

    def test_templates_are_rendered_and_phone_qr_is_a_png(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin 123'})
        homepage = self.client.get('/')
        self.assertEqual(homepage.status_code, 200)
        self.assertNotIn(b'{%', homepage.data)
        page = self.client.get('/scan')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn(b'{% extends', page.data)
        self.assertNotIn(b"{{ t(", page.data)
        self.assertIn(b'Barcode Scanner', page.data)
        info = self.client.get('/api/phone-connect/info').get_json()
        if info.get('available'):
            self.assertNotIn('localhost', info['url'])
            self.assertNotIn('127.0.0.1', info['url'])
        qr = self.client.get('/api/phone-connect/qr-code')
        if qr.status_code == 200:
            self.assertEqual(qr.mimetype, 'image/png')
        else:
            self.assertEqual(qr.status_code, 503)

    def test_chatbot_answers_different_live_inventory_questions(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin 123'})
        previous_key = os.environ.pop('OPENAI_API_KEY', None)
        try:
            questions = [
                'What products are expiring this week?',
                'Which products should I discount first?',
                'How many packets of Amul milk are in stock?',
                'Tell me the total inventory value.',
                'Which products have the highest expiry risk?'
            ]
            replies = []
            for question in questions:
                response = self.client.post('/api/chatbot/message', json={'message': question})
                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertEqual(payload['mode'], 'database_fallback')
                replies.append(payload['reply'])
            self.assertEqual(len(set(replies)), len(questions))
            self.assertIn('Amul', replies[2])
            self.assertIn('₹', replies[3])
        finally:
            if previous_key:
                os.environ['OPENAI_API_KEY'] = previous_key

    def test_image_analysis_rejects_non_image_upload(self):
        from io import BytesIO
        self.client.post('/login', data={'username': 'admin', 'password': 'admin 123'})
        response = self.client.post('/api/scanner/analyze-image', data={
            'image': (BytesIO(b'not an image'), 'text.txt', 'text/plain')
        }, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 415)

    def test_valid_image_upload_uses_explicit_ocr_only_fallback_without_key(self):
        from io import BytesIO
        from PIL import Image
        self.client.post('/login', data={'username': 'admin', 'password': 'admin 123'})
        output = BytesIO()
        Image.new('RGB', (24, 24), color='white').save(output, format='PNG')
        output.seek(0)
        previous_key = os.environ.pop('OPENAI_API_KEY', None)
        try:
            response = self.client.post('/api/scanner/analyze-image', data={
                'image': (output, 'package.png', 'image/png'), 'ocr_text': ''
            }, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()['provider'], 'ocr_only')
            self.assertEqual(response.get_json()['fields'], {})
        finally:
            if previous_key:
                os.environ['OPENAI_API_KEY'] = previous_key

    # 7. Multilingual Dictionary Completeness Tests
    def test_multilingual_keys(self):
        en_keys = set(TRANSLATIONS['en'].keys())
        hi_keys = set(TRANSLATIONS['hi'].keys())
        mr_keys = set(TRANSLATIONS['mr'].keys())

        # Verify essential keys exist in all three languages
        required_keys = [
            'field_product_name', 'field_mfg_date', 'field_expiry_date',
            'field_barcode', 'field_quantity', 'field_price',
            'nav_dashboard', 'nav_scan', 'nav_inventory', 'nav_quick_sales',
            'status_expired', 'btn_save_product'
        ]
        for key in required_keys:
            self.assertIn(key, en_keys)
            self.assertIn(key, hi_keys)
            self.assertIn(key, mr_keys)

if __name__ == '__main__':
    unittest.main()
