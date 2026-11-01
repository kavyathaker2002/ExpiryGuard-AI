"""
Indian FMCG Barcode & Product Master Catalog
Provides instant lookup for common Indian retail grocery & chaat store products,
including standard shelf-life days and estimated prices in Indian Rupees (₹).
"""

# Catalog of common Indian Kirana & Chaat store items
FMCG_CATALOG = {
    # ── Dairy & Eggs ──────────────────────────────────────────────────────────
    "8901262010053": {"name": "Amul Taaza Homogenised Toned Milk 500ml", "brand": "Amul", "category": "Dairy", "package_size": "500 ml", "price": 27.0, "shelf_life_days": 3},
    "8901262010121": {"name": "Amul Pasteurised Butter 100g", "brand": "Amul", "category": "Dairy", "package_size": "100 g", "price": 58.0, "shelf_life_days": 180},
    "8901262020014": {"name": "Amul Pure Ghee 1 Litre", "brand": "Amul", "category": "Dairy", "package_size": "1 L", "price": 630.0, "shelf_life_days": 270},
    "8901262023015": {"name": "Amul Gold Full Cream Milk 500ml", "brand": "Amul", "category": "Dairy", "package_size": "500 ml", "price": 32.0, "shelf_life_days": 3},
    "8901262011067": {"name": "Amul Mozzarella Cheese 200g", "brand": "Amul", "category": "Dairy", "package_size": "200 g", "price": 130.0, "shelf_life_days": 60},
    "8901262000023": {"name": "Amul Mithai Mate Condensed Milk 400g", "brand": "Amul", "category": "Dairy", "package_size": "400 g", "price": 115.0, "shelf_life_days": 365},
    "8901648001019": {"name": "Mother Dairy Classic Paneer 200g", "brand": "Mother Dairy", "category": "Dairy", "package_size": "200 g", "price": 90.0, "shelf_life_days": 7},
    "8901648002009": {"name": "Mother Dairy Full Cream Milk 500ml", "brand": "Mother Dairy", "category": "Dairy", "package_size": "500 ml", "price": 30.0, "shelf_life_days": 3},
    "8908006371028": {"name": "Epigamia Greek Yogurt Natural 90g", "brand": "Epigamia", "category": "Dairy", "package_size": "90 g", "price": 50.0, "shelf_life_days": 14},
    "8906012430041": {"name": "Harvest Gold Soft Burger Buns 6pcs", "brand": "Harvest Gold", "category": "Bakery & Bread", "package_size": "6 pcs", "price": 35.0, "shelf_life_days": 6},

    # ── Milky Mist Dairy Products ──────────────────────────────────────────────
    "8904083307068": {"name": "Milky Mist Cheese Block 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 135.0, "shelf_life_days": 180, "mfg_date": "2026-04-10", "expiry_date": "2026-10-09"},
    "8904083310136": {"name": "Milky Mist Cheese Slices 100g", "brand": "Milky Mist", "category": "Dairy", "package_size": "100 g", "price": 85.0, "shelf_life_days": 180},
    "8904083310129": {"name": "Milky Mist Cheese Slices 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 160.0, "shelf_life_days": 180},
    "8904083310112": {"name": "Milky Mist Cheese Slice 400g", "brand": "Milky Mist", "category": "Dairy", "package_size": "400 g", "price": 280.0, "shelf_life_days": 180},
    "8904083307037": {"name": "Milky Mist Processed Cheese Cubes 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 140.0, "shelf_life_days": 180},
    "8904083307112": {"name": "Milky Mist Cheese Cubes 100g", "brand": "Milky Mist", "category": "Dairy", "package_size": "100 g", "price": 75.0, "shelf_life_days": 180},
    "8904083300021": {"name": "Milky Mist Fresh Paneer 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 90.0, "shelf_life_days": 15},
    "8904083300106": {"name": "Milky Mist Fresh Paneer 500g", "brand": "Milky Mist", "category": "Dairy", "package_size": "500 g", "price": 220.0, "shelf_life_days": 15},
    "8904083300045": {"name": "Milky Mist Paneer 1kg", "brand": "Milky Mist", "category": "Dairy", "package_size": "1 kg", "price": 420.0, "shelf_life_days": 15},
    "8904083301110": {"name": "Milky Mist Pizza Cheese 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 150.0, "shelf_life_days": 120},
    "8904083301097": {"name": "Milky Mist Pizza Cheese Mozzarella Diced 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 155.0, "shelf_life_days": 120},
    "8904083311010": {"name": "Milky Mist Shredded Mozzarella Cheese 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 165.0, "shelf_life_days": 120},
    "8904083310037": {"name": "Milky Mist Garlic Cheese Spread 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 120.0, "shelf_life_days": 180},
    "8904083310013": {"name": "Milky Mist Plain Cheese Spread 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 115.0, "shelf_life_days": 180},
    "8904083304036": {"name": "Milky Mist Natural Cheddar Cheese 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 190.0, "shelf_life_days": 180},
    "8904083309888": {"name": "Milky Mist Cream Cheese 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 140.0, "shelf_life_days": 120},
    "8906097370681": {"name": "Milky Mist Cheese Slice 200g", "brand": "Milky Mist", "category": "Dairy", "package_size": "200 g", "price": 130.0, "shelf_life_days": 120},

    # ── Snacks, Namkeen & Biscuits ─────────────────────────────────────────────
    "8901719101015": {"name": "Parle-G Gold Biscuits 1kg", "brand": "Parle", "category": "Biscuits & Confectionery", "package_size": "1 kg", "price": 120.0, "shelf_life_days": 180},
    "8901719140014": {"name": "Parle Krackjack Sweet & Salty Crackers 200g", "brand": "Parle", "category": "Biscuits & Confectionery", "package_size": "200 g", "price": 30.0, "shelf_life_days": 180},
    "8901063011128": {"name": "Britannia Good Day Butter Cookies 250g", "brand": "Britannia", "category": "Biscuits & Confectionery", "package_size": "250 g", "price": 40.0, "shelf_life_days": 180},
    "8901063102123": {"name": "Britannia 100% Whole Wheat Bread 400g", "brand": "Britannia", "category": "Bakery & Bread", "package_size": "400 g", "price": 45.0, "shelf_life_days": 5},
    "8901063020014": {"name": "Britannia Bourbon Cream Biscuits 150g", "brand": "Britannia", "category": "Biscuits & Confectionery", "package_size": "150 g", "price": 25.0, "shelf_life_days": 180},
    "8904004400124": {"name": "Haldiram Aloo Bhujia 400g", "brand": "Haldiram's", "category": "Snacks & Namkeen", "package_size": "400 g", "price": 95.0, "shelf_life_days": 150},
    "8904004400209": {"name": "Haldiram Pani Puri Kit 300g", "brand": "Haldiram's", "category": "Snacks & Namkeen", "package_size": "300 g", "price": 65.0, "shelf_life_days": 180},
    "8904004400315": {"name": "Haldiram Sev Murmura 200g", "brand": "Haldiram's", "category": "Snacks & Namkeen", "package_size": "200 g", "price": 35.0, "shelf_life_days": 120},
    "8904004400070": {"name": "Haldiram Mixture 400g", "brand": "Haldiram's", "category": "Snacks & Namkeen", "package_size": "400 g", "price": 90.0, "shelf_life_days": 180},
    "8901491100012": {"name": "Lay's Classic Salted Chips 50g", "brand": "Lay's", "category": "Snacks & Chips", "package_size": "50 g", "price": 20.0, "shelf_life_days": 120},
    "8901491101026": {"name": "Kurkure Masala Munch 85g", "brand": "Kurkure", "category": "Snacks & Chips", "package_size": "85 g", "price": 20.0, "shelf_life_days": 120},
    "8901491100166": {"name": "Lay's Magic Masala 50g", "brand": "Lay's", "category": "Snacks & Chips", "package_size": "50 g", "price": 20.0, "shelf_life_days": 120},
    "8902519100024": {"name": "Bikano Aloo Bhujia 400g", "brand": "Bikano", "category": "Snacks & Namkeen", "package_size": "400 g", "price": 75.0, "shelf_life_days": 150},
    "7622201443213": {"name": "Cadbury Dairy Milk Silk 60g", "brand": "Cadbury", "category": "Confectionery", "package_size": "60 g", "price": 85.0, "shelf_life_days": 270},
    "7622200404024": {"name": "Cadbury Dairy Milk 40g", "brand": "Cadbury", "category": "Confectionery", "package_size": "40 g", "price": 40.0, "shelf_life_days": 270},
    "8901259070016": {"name": "Kit Kat 4 Finger 41.5g", "brand": "Nestle", "category": "Confectionery", "package_size": "41.5 g", "price": 40.0, "shelf_life_days": 270},

    # ── Staples & Cooking Essentials ───────────────────────────────────────────
    "8901537007116": {"name": "Daawat Rozana Basmati Rice 5kg", "brand": "Daawat", "category": "Staples & Grocery", "package_size": "5 kg", "price": 489.0, "shelf_life_days": 730, "mfg_date": "2026-05-01", "expiry_date": "2028-04-30"},
    "8901537007109": {"name": "Daawat Rozana Basmati Rice 1kg", "brand": "Daawat", "category": "Staples & Grocery", "package_size": "1 kg", "price": 105.0, "shelf_life_days": 730, "mfg_date": "2026-05-01", "expiry_date": "2028-04-30"},
    "8901537005112": {"name": "Daawat Super Basmati Rice 5kg", "brand": "Daawat", "category": "Staples & Grocery", "package_size": "5 kg", "price": 675.0, "shelf_life_days": 730, "mfg_date": "2026-05-01", "expiry_date": "2028-04-30"},
    "8901537005105": {"name": "Daawat Super Basmati Rice 1kg", "brand": "Daawat", "category": "Staples & Grocery", "package_size": "1 kg", "price": 145.0, "shelf_life_days": 730, "mfg_date": "2026-05-01", "expiry_date": "2028-04-30"},
    "8901396001017": {"name": "India Gate Basmati Rice Classic 5kg", "brand": "India Gate", "category": "Staples & Grocery", "package_size": "5 kg", "price": 625.0, "shelf_life_days": 730, "mfg_date": "2026-04-15", "expiry_date": "2028-04-14"},
    "8901396001024": {"name": "India Gate Basmati Rice Classic 1kg", "brand": "India Gate", "category": "Staples & Grocery", "package_size": "1 kg", "price": 135.0, "shelf_life_days": 730, "mfg_date": "2026-04-15", "expiry_date": "2028-04-14"},
    "8901396002014": {"name": "India Gate Basmati Rice Dubar 5kg", "brand": "India Gate", "category": "Staples & Grocery", "package_size": "5 kg", "price": 465.0, "shelf_life_days": 730, "mfg_date": "2026-04-15", "expiry_date": "2028-04-14"},
    "8901595851218": {"name": "Ching's Secret Veg Hakka Noodles 140g", "brand": "Ching's Secret", "category": "Instant Food", "package_size": "140 g", "price": 45.0, "shelf_life_days": 270, "mfg_date": "2026-03-15", "expiry_date": "2026-12-14"},
    "8901058852415": {"name": "Maggi 2-Minute Masala Noodles 280g", "brand": "Maggi", "category": "Instant Food", "package_size": "280 g", "price": 48.0, "shelf_life_days": 240, "mfg_date": "2026-04-01", "expiry_date": "2026-11-30"},
    "8901058800019": {"name": "Maggi Masala Noodles 70g", "brand": "Maggi", "category": "Instant Food", "package_size": "70 g", "price": 14.0, "shelf_life_days": 240, "mfg_date": "2026-04-01", "expiry_date": "2026-11-30"},
    "8904043901006": {"name": "Tata Salt Iodized 1kg", "brand": "Tata", "category": "Staples & Grocery", "package_size": "1 kg", "price": 28.0, "shelf_life_days": 720, "mfg_date": "2026-01-15", "expiry_date": "2028-01-14"},
    "8901725131012": {"name": "Aashirvaad Whole Wheat Atta 5kg", "brand": "Aashirvaad", "category": "Staples & Grocery", "package_size": "5 kg", "price": 310.0, "shelf_life_days": 180, "mfg_date": "2026-06-10", "expiry_date": "2026-12-09"},
    "8906007280019": {"name": "Fortune Sunflower Oil 1L", "brand": "Fortune", "category": "Cooking Oil", "package_size": "1 L", "price": 145.0, "shelf_life_days": 270},
    "8906007280538": {"name": "Fortune Rice Bran Oil 1L", "brand": "Fortune", "category": "Cooking Oil", "package_size": "1 L", "price": 155.0, "shelf_life_days": 270},
    "8901058861127": {"name": "Knorr Mixed Vegetable Soup 43g", "brand": "Knorr", "category": "Instant Food", "package_size": "43 g", "price": 35.0, "shelf_life_days": 360},
    "8901052000015": {"name": "Tata Tea Gold 250g", "brand": "Tata Tea", "category": "Beverages", "package_size": "250 g", "price": 140.0, "shelf_life_days": 365},
    "8901262010459": {"name": "Everest Chaat Masala 100g", "brand": "Everest", "category": "Spices & Masala", "package_size": "100 g", "price": 72.0, "shelf_life_days": 365},
    "8901262010466": {"name": "Everest Pani Puri Masala 100g", "brand": "Everest", "category": "Spices & Masala", "package_size": "100 g", "price": 68.0, "shelf_life_days": 365},
    "8901774002028": {"name": "Badshah Biryani Masala 100g", "brand": "Badshah", "category": "Spices & Masala", "package_size": "100 g", "price": 175.0, "shelf_life_days": 540, "mfg_date": "2026-04-16", "expiry_date": "2027-10-15"},
    "8901725131050": {"name": "Aashirvaad Multigrain Atta 5kg", "brand": "Aashirvaad", "category": "Staples & Grocery", "package_size": "5 kg", "price": 340.0, "shelf_life_days": 180},
    "8901138500012": {"name": "Dabur Honey 500g", "brand": "Dabur", "category": "Health Foods", "package_size": "500 g", "price": 220.0, "shelf_life_days": 730},
    "8901012155021": {"name": "Catch Pani Puri Masala 100g", "brand": "Catch", "category": "Spices & Masala", "package_size": "100 g", "price": 35.0, "shelf_life_days": 365},
    "8901030840014": {"name": "Surf Excel Easy Wash 1kg", "brand": "Surf Excel", "category": "Household", "package_size": "1 kg", "price": 120.0, "shelf_life_days": 730},

    # ── Beverages ─────────────────────────────────────────────────────────────
    "8901058001015": {"name": "Nescafe Classic Instant Coffee 50g", "brand": "Nescafe", "category": "Beverages", "package_size": "50 g", "price": 135.0, "shelf_life_days": 730},
    "8901520001034": {"name": "Bru Instant Coffee 50g", "brand": "Bru", "category": "Beverages", "package_size": "50 g", "price": 120.0, "shelf_life_days": 730},
    "8901063720014": {"name": "Britannia Nutrichoice Digestive Biscuits 400g", "brand": "Britannia", "category": "Biscuits & Confectionery", "package_size": "400 g", "price": 75.0, "shelf_life_days": 180},
    "8901072001164": {"name": "Real Activ 100% Orange Juice 1L", "brand": "Real Activ", "category": "Beverages", "package_size": "1 L", "price": 120.0, "shelf_life_days": 180},
    "8901063101065": {"name": "Britannia Marie Gold Biscuits 250g", "brand": "Britannia", "category": "Biscuits & Confectionery", "package_size": "250 g", "price": 30.0, "shelf_life_days": 180},

    # ── Personal & Home Care ───────────────────────────────────────────────────
    "8901030010012": {"name": "Dettol Original Soap 75g", "brand": "Dettol", "category": "Personal Care", "package_size": "75 g", "price": 42.0, "shelf_life_days": 720},
    "8901314010118": {"name": "Colgate Strong Teeth Toothpaste 100g", "brand": "Colgate", "category": "Personal Care", "package_size": "100 g", "price": 62.0, "shelf_life_days": 720},
    "8901030852116": {"name": "Lifebuoy Total Soap 125g", "brand": "Lifebuoy", "category": "Personal Care", "package_size": "125 g", "price": 35.0, "shelf_life_days": 720},
    "8901207002052": {"name": "Parachute Coconut Oil 200ml", "brand": "Parachute", "category": "Personal Care", "package_size": "200 ml", "price": 90.0, "shelf_life_days": 730},

    # ── Regional & Kirana Snacks ───────────────────────────────────────────────
    "8902901251951": {
        "name": "Kamala Prakash Kurmura Bajra & Jowar 200g",
        "brand": "Kamala Prakash",
        "category": "Snacks & Namkeen",
        "package_size": "200 g",
        "price": 60.0,
        "shelf_life_days": 180,
        "mfg_date": "2026-05-01",
        "expiry_date": "2026-10-31"
    },
    "8902901252001": {"name": "Kamala Prakash Poha 500g", "brand": "Kamala Prakash", "category": "Staples & Grocery", "package_size": "500 g", "price": 45.0, "shelf_life_days": 180},

    # ── More Spices & Masala ──────────────────────────────────────────────────
    "8901774001014": {"name": "Badshah Chaat Masala 100g", "brand": "Badshah", "category": "Spices & Masala", "package_size": "100 g", "price": 80.0, "shelf_life_days": 540},
    "8901774001021": {"name": "Badshah Pav Bhaji Masala 100g", "brand": "Badshah", "category": "Spices & Masala", "package_size": "100 g", "price": 85.0, "shelf_life_days": 540},
    "8901774001038": {"name": "Badshah Rajwadi Garam Masala 100g", "brand": "Badshah", "category": "Spices & Masala", "package_size": "100 g", "price": 95.0, "shelf_life_days": 540},
    "8901774001052": {"name": "Badshah Chicken Masala 100g", "brand": "Badshah", "category": "Spices & Masala", "package_size": "100 g", "price": 90.0, "shelf_life_days": 540},
    "8901774001069": {"name": "Badshah Chole Masala 100g", "brand": "Badshah", "category": "Spices & Masala", "package_size": "100 g", "price": 85.0, "shelf_life_days": 540},
    "8901262010022": {"name": "Everest Kitchen King Masala 100g", "brand": "Everest", "category": "Spices & Masala", "package_size": "100 g", "price": 85.0, "shelf_life_days": 540},
    "8901262010039": {"name": "Everest Garam Masala 100g", "brand": "Everest", "category": "Spices & Masala", "package_size": "100 g", "price": 72.0, "shelf_life_days": 540},
    "8901262010046": {"name": "Everest Red Chilli Powder 100g", "brand": "Everest", "category": "Spices & Masala", "package_size": "100 g", "price": 60.0, "shelf_life_days": 540},
    "8901262010053": {"name": "Everest Turmeric Powder 100g", "brand": "Everest", "category": "Spices & Masala", "package_size": "100 g", "price": 55.0, "shelf_life_days": 540},
    "8901999000148": {"name": "MDH Chaat Masala 100g", "brand": "MDH", "category": "Spices & Masala", "package_size": "100 g", "price": 65.0, "shelf_life_days": 540},
    "8901999000155": {"name": "MDH Garam Masala 100g", "brand": "MDH", "category": "Spices & Masala", "package_size": "100 g", "price": 75.0, "shelf_life_days": 540},
    "8901999000162": {"name": "MDH Kitchen King Masala 100g", "brand": "MDH", "category": "Spices & Masala", "package_size": "100 g", "price": 85.0, "shelf_life_days": 540},
    "8901999000179": {"name": "MDH Chole Masala 100g", "brand": "MDH", "category": "Spices & Masala", "package_size": "100 g", "price": 70.0, "shelf_life_days": 540},
    "8901012155038": {"name": "Catch Chaat Masala 100g", "brand": "Catch", "category": "Spices & Masala", "package_size": "100 g", "price": 40.0, "shelf_life_days": 365},
    "8901012155045": {"name": "Catch Garam Masala 100g", "brand": "Catch", "category": "Spices & Masala", "package_size": "100 g", "price": 45.0, "shelf_life_days": 365},

    # ── More Rice & Staples ───────────────────────────────────────────────────
    "8901537003019": {"name": "Daawat Basmati Rice Traditional 5kg", "brand": "Daawat", "category": "Staples & Grocery", "package_size": "5 kg", "price": 735.0, "shelf_life_days": 730},
    "8901396003011": {"name": "India Gate Feast Rozzana Rice 5kg", "brand": "India Gate", "category": "Staples & Grocery", "package_size": "5 kg", "price": 395.0, "shelf_life_days": 730},
    "8901725133016": {"name": "Aashirvaad Select Sharbati Atta 5kg", "brand": "Aashirvaad", "category": "Staples & Grocery", "package_size": "5 kg", "price": 295.0, "shelf_life_days": 180},
    "8904004100012": {"name": "Tata Sampann Toor Dal 1kg", "brand": "Tata", "category": "Staples & Grocery", "package_size": "1 kg", "price": 145.0, "shelf_life_days": 365},
    "8904004100029": {"name": "Tata Sampann Chana Dal 1kg", "brand": "Tata", "category": "Staples & Grocery", "package_size": "1 kg", "price": 120.0, "shelf_life_days": 365},
    "8904004100036": {"name": "Tata Sampann Moong Dal 1kg", "brand": "Tata", "category": "Staples & Grocery", "package_size": "1 kg", "price": 135.0, "shelf_life_days": 365},
    "8904043901013": {"name": "Tata Salt Lite Low Sodium 1kg", "brand": "Tata", "category": "Staples & Grocery", "package_size": "1 kg", "price": 32.0, "shelf_life_days": 720},

    # ── More Oils ─────────────────────────────────────────────────────────────
    "8906007280026": {"name": "Fortune Mustard Oil 1L", "brand": "Fortune", "category": "Cooking Oil", "package_size": "1 L", "price": 150.0, "shelf_life_days": 270},
    "8906007280033": {"name": "Fortune Refined Soyabean Oil 1L", "brand": "Fortune", "category": "Cooking Oil", "package_size": "1 L", "price": 140.0, "shelf_life_days": 270},
    "8906007285015": {"name": "Fortune Sunflower Oil 5L", "brand": "Fortune", "category": "Cooking Oil", "package_size": "5 L", "price": 720.0, "shelf_life_days": 270},
    "8901058864104": {"name": "Saffola Gold Refined Oil 1L", "brand": "Saffola", "category": "Cooking Oil", "package_size": "1 L", "price": 175.0, "shelf_life_days": 270},
    "8901058864111": {"name": "Saffola Gold Refined Oil 5L", "brand": "Saffola", "category": "Cooking Oil", "package_size": "5 L", "price": 840.0, "shelf_life_days": 270},

    # ── More Dairy ────────────────────────────────────────────────────────────
    "8901262020021": {"name": "Amul Pure Ghee 500ml", "brand": "Amul", "category": "Dairy", "package_size": "500 ml", "price": 340.0, "shelf_life_days": 270},
    "8901262020038": {"name": "Amul Pure Ghee 200g", "brand": "Amul", "category": "Dairy", "package_size": "200 g", "price": 145.0, "shelf_life_days": 270},
    "8901262010077": {"name": "Amul Butter 500g", "brand": "Amul", "category": "Dairy", "package_size": "500 g", "price": 260.0, "shelf_life_days": 180},
    "8901648003006": {"name": "Mother Dairy Mishti Doi 400g", "brand": "Mother Dairy", "category": "Dairy", "package_size": "400 g", "price": 65.0, "shelf_life_days": 14},
    "8901648004003": {"name": "Mother Dairy Cheese Slice 200g", "brand": "Mother Dairy", "category": "Dairy", "package_size": "200 g", "price": 125.0, "shelf_life_days": 180},

    # ── More Snacks ───────────────────────────────────────────────────────────
    "8901719101022": {"name": "Parle-G Biscuits 500g", "brand": "Parle", "category": "Biscuits & Confectionery", "package_size": "500 g", "price": 65.0, "shelf_life_days": 180},
    "8901063021011": {"name": "Britannia Good Day Cashew Cookies 75g", "brand": "Britannia", "category": "Biscuits & Confectionery", "package_size": "75 g", "price": 20.0, "shelf_life_days": 180},
    "8904004400315": {"name": "Haldiram Sev 200g", "brand": "Haldiram's", "category": "Snacks & Namkeen", "package_size": "200 g", "price": 40.0, "shelf_life_days": 120},
    "8904004400391": {"name": "Haldiram Moong Dal 200g", "brand": "Haldiram's", "category": "Snacks & Namkeen", "package_size": "200 g", "price": 40.0, "shelf_life_days": 150},
    "8901491100173": {"name": "Lay's American Style Cream & Onion 50g", "brand": "Lay's", "category": "Snacks & Chips", "package_size": "50 g", "price": 20.0, "shelf_life_days": 120},
    "8901491101019": {"name": "Kurkure Naughty Tomatoes 58g", "brand": "Kurkure", "category": "Snacks & Chips", "package_size": "58 g", "price": 20.0, "shelf_life_days": 120},
    "7622201443220": {"name": "Cadbury Dairy Milk Silk Oreo 130g", "brand": "Cadbury", "category": "Confectionery", "package_size": "130 g", "price": 165.0, "shelf_life_days": 270},
    "8901259072010": {"name": "Kit Kat Minis 109g", "brand": "Nestle", "category": "Confectionery", "package_size": "109 g", "price": 170.0, "shelf_life_days": 270},

    # ── More Instant Food & Beverages ─────────────────────────────────────────
    "8901058800026": {"name": "Maggi Masala Noodles 140g (2-pack)", "brand": "Maggi", "category": "Instant Food", "package_size": "140 g", "price": 28.0, "shelf_life_days": 240},
    "8901595850013": {"name": "Ching's Secret Instant Chilli Chicken Noodles 60g", "brand": "Ching's Secret", "category": "Instant Food", "package_size": "60 g", "price": 25.0, "shelf_life_days": 270},
    "8901595855018": {"name": "Ching's Secret Manchow Soup 55g", "brand": "Ching's Secret", "category": "Instant Food", "package_size": "55 g", "price": 35.0, "shelf_life_days": 360},
    "8901058001022": {"name": "Nescafe Classic Instant Coffee 100g", "brand": "Nescafe", "category": "Beverages", "package_size": "100 g", "price": 255.0, "shelf_life_days": 730},
    "8901052000022": {"name": "Tata Tea Premium 500g", "brand": "Tata Tea", "category": "Beverages", "package_size": "500 g", "price": 260.0, "shelf_life_days": 365},
    "8901072001171": {"name": "Real Fruit Power Guava 1L", "brand": "Real Activ", "category": "Beverages", "package_size": "1 L", "price": 125.0, "shelf_life_days": 180},
    "8901072001188": {"name": "Real Fruit Power Mango 1L", "brand": "Real Activ", "category": "Beverages", "package_size": "1 L", "price": 125.0, "shelf_life_days": 180},

    # ── More Personal Care ─────────────────────────────────────────────────────
    "8901314023019": {"name": "Colgate MaxFresh Toothpaste 150g", "brand": "Colgate", "category": "Personal Care", "package_size": "150 g", "price": 95.0, "shelf_life_days": 730},
    "8901030852123": {"name": "Lifebuoy Lemon Fresh Soap 125g", "brand": "Lifebuoy", "category": "Personal Care", "package_size": "125 g", "price": 38.0, "shelf_life_days": 720},
    "8901030010029": {"name": "Dettol Sensitive Soap 75g", "brand": "Dettol", "category": "Personal Care", "package_size": "75 g", "price": 48.0, "shelf_life_days": 720},
    "8901207002069": {"name": "Parachute Coconut Oil 500ml", "brand": "Parachute", "category": "Personal Care", "package_size": "500 ml", "price": 200.0, "shelf_life_days": 730},
    "8901030040019": {"name": "Dettol Antiseptic Liquid 100ml", "brand": "Dettol", "category": "Personal Care", "package_size": "100 ml", "price": 90.0, "shelf_life_days": 1095},

    # ── Health Foods ───────────────────────────────────────────────────────────
    "8901138500029": {"name": "Dabur Honey 250g", "brand": "Dabur", "category": "Health Foods", "package_size": "250 g", "price": 115.0, "shelf_life_days": 730},
    "8901138500036": {"name": "Dabur Chyawanprash 500g", "brand": "Dabur", "category": "Health Foods", "package_size": "500 g", "price": 285.0, "shelf_life_days": 1095},
    "8901207000040": {"name": "Saffola Masala Oats Classic Masala 40g", "brand": "Saffola", "category": "Health Foods", "package_size": "40 g", "price": 25.0, "shelf_life_days": 180},
    "8901207000057": {"name": "Saffola Masala Oats Veggie Twist 40g", "brand": "Saffola", "category": "Health Foods", "package_size": "40 g", "price": 25.0, "shelf_life_days": 180},
}


def lookup_catalog_product(barcode):
    """Return known catalog identity with full auto-fill details."""
    clean_code = str(barcode).strip()
    item = FMCG_CATALOG.get(clean_code)
    if not item:
        return None

    import re
    from datetime import datetime, timedelta

    brand = item.get('brand') or item['name'].split()[0]
    category = item.get('category') or 'Grocery & Snacks'
    package_size = item.get('package_size') or ''
    if not package_size:
        size_match = re.search(r'(\d+(?:\.\d+)?\s*(?:g|gm|kg|ml|l|tin|pcs|pack))', item['name'], re.I)
        if size_match:
            package_size = size_match.group(1)
        else:
            package_size = '1 unit'

    from datetime import datetime, timedelta
    today = datetime.now().date()
    shelf_days = item.get('shelf_life_days', 180)

    # Use hardcoded batch dates if present (e.g. Kamala Prakash with real stamped dates)
    hardcoded_mfg = item.get('mfg_date', None)
    hardcoded_exp = item.get('expiry_date', None)

    if hardcoded_mfg and hardcoded_exp:
        mfg_date = hardcoded_mfg
        expiry_date = hardcoded_exp
        dates_are_estimated = False
    else:
        # If very short shelf life (<= 7 days, e.g. fresh bread/milk), batch is made fresh:
        if shelf_days <= 7:
            mfg_date = today.strftime('%Y-%m-%d')
            expiry_date = (today + timedelta(days=shelf_days)).strftime('%Y-%m-%d')
        else:
            # Packaged FMCG on store shelf was manufactured in a realistic prior batch (NEVER today)
            days_ago = min(90, max(30, int(shelf_days * 0.25)))
            mfg_date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            expiry_date = (today - timedelta(days=days_ago) + timedelta(days=shelf_days)).strftime('%Y-%m-%d')
        dates_are_estimated = True

    return {
        "barcode": clean_code,
        "product_name": item['name'],
        "brand": brand,
        "category": category,
        "package_size": package_size,
        "price": item['price'],
        "mfg_date": mfg_date,
        "expiry_date": expiry_date,
        "quantity": item.get('quantity', 1) or 1,
        "is_catalog_match": True,
        "price_is_catalog_estimate": True,
        "dates_are_estimated": dates_are_estimated
    }
