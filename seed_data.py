"""
Attar AIS — Realistic Spice Store Seed Data
Clears old data and inserts fresh, realistic Egyptian spice store data.
"""
from database.db_config import DatabaseConnection, init_database
from datetime import datetime, timedelta
import random

def seed_data():
    init_database()
    with DatabaseConnection() as conn:
        cur = conn.cursor()

        # ── 1. CLEAN ALL DATA ─────────────────────────────────────
        tables = [
            'general_ledger', 'journal_entry_items', 'journal_entries',
            'sales_items', 'sales_invoices',
            'purchase_items', 'purchase_invoices',
            'expenses', 'products', 'customers', 'suppliers',
        ]
        for t in tables:
            try:
                cur.execute(f"DELETE FROM {t}")
            except Exception:
                pass

        # Reset account balances
        cur.execute("UPDATE accounts SET balance = 0")
        print("[OK] Old data cleared.")

        # ── 2. SUPPLIERS ──────────────────────────────────────────
        suppliers = [
            ("Al-Madina Spice Traders",    "Hassan Al-Rashidi",  "010-2345-6789", "hassan@almadina-spices.com",    "23 Al-Azhar St, Cairo"),
            ("Nile Valley Herbs Co.",      "Fatima Osman",       "011-3456-7890", "fatima@nilevalleyherbs.com",    "7 Corniche El-Nil, Giza"),
            ("Oriental Aroma Suppliers",   "Youssef Khalil",     "012-4567-8901", "youssef@orientalaroma.com",     "45 Port Said St, Alexandria"),
            ("Sinai Botanicals Ltd.",      "Mona Abdel-Aziz",    "010-5678-9012", "mona@sinaibotanicals.com",      "12 Suez Canal Rd, Ismailia"),
            ("Golden Saffron Imports",     "Kareem El-Masry",    "011-6789-0123", "kareem@goldensaffron.com",      "88 Ramsis St, Cairo"),
        ]
        cur.executemany("""
            INSERT INTO suppliers (name, contact_person, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        """, suppliers)
        cur.execute("SELECT id FROM suppliers ORDER BY id")
        sup_ids = [r['id'] for r in cur.fetchall()]
        print(f"[OK] {len(sup_ids)} suppliers inserted.")

        # ── 3. CUSTOMERS ─────────────────────────────────────────
        customers = [
            ("Al-Nour Pharmacy & Herbs",      "Dr. Amir Saad",       "010-1111-2222", "amir@alnour-pharmacy.com",    "15 Al-Haram St, Giza"),
            ("Badr Supermarket",              "Magdi Badr",          "011-2222-3333", "magdi@badrsupermarket.com",   "32 October 6 City, Giza"),
            ("Aromatic Kitchen Supplies",     "Nadia El-Gohary",     "012-3333-4444", "nadia@aromatickitchen.com",   "7 Nasr City, Cairo"),
            ("El-Safa Herbal Center",         "Ibrahim El-Safa",     "010-4444-5555", "ibrahim@elsafa-herbal.com",   "21 Zamalek St, Cairo"),
            ("Lotus Traditional Medicine",    "Dr. Sara Mahmoud",    "011-5555-6666", "sara@lotustrad.com",          "9 Heliopolis Ave, Cairo"),
            ("Star Restaurant Group",         "Ahmed Fathy",         "012-6666-7777", "ahmed@starrestaurants.com",   "55 Maadi Rd, Cairo"),
            ("Cleopatra Beauty Salon",        "Heba Mostafa",        "010-7777-8888", "heba@cleopatrabeauty.com",    "14 Mohandessin, Giza"),
            ("Pharaoh's Spice Shop",          "Walid Hassan",        "011-8888-9999", "walid@pharaohspice.com",      "3 Khan El-Khalili, Cairo"),
        ]
        cur.executemany("""
            INSERT INTO customers (name, contact_person, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        """, customers)
        cur.execute("SELECT id FROM customers ORDER BY id")
        cust_ids = [r['id'] for r in cur.fetchall()]
        print(f"[OK] {len(cust_ids)} customers inserted.")

        # ── 4. PRODUCTS ───────────────────────────────────────────
        products = [
            # (name, description, unit_price, quantity, min_qty)
            ("Premium Saffron",          "Iranian Saffron — Grade A",                125.00,  48,   10),
            ("Turmeric Powder",          "Pure ground turmeric root",                  8.50, 320,   50),
            ("Black Seed (Nigella)",     "Cold-pressed black cumin seeds",            22.00, 175,   30),
            ("Cumin Seeds",              "Whole roasted cumin seeds",                  6.00, 280,   40),
            ("Cinnamon Sticks",          "Ceylon true cinnamon, 3-inch sticks",       15.50, 140,   25),
            ("Cardamom Pods (Green)",    "Premium green cardamom pods",               38.00,  90,   15),
            ("Coriander Seeds",          "Whole coriander seeds, sun-dried",           5.50, 260,   45),
            ("Dried Rose Petals",        "Egyptian Damask rose petals",               32.00,  80,   15),
            ("Anise Seeds",              "Whole anise seeds",                          7.00, 200,   35),
            ("Fenugreek Seeds",          "Whole fenugreek seeds",                      5.00, 220,   40),
            ("Cloves (Whole)",           "Madagascar whole cloves",                   28.00,  65,   10),
            ("Black Pepper (Whole)",     "Malabar black pepper",                      18.00, 150,   25),
            ("Dried Chamomile Flowers",  "Pure chamomile flowers for tea",            24.00,  95,   20),
            ("Hibiscus Flowers (Karkade)","Dried hibiscus flowers — Premium grade",   12.00, 185,   30),
            ("Ginger Root (Dried)",      "Dried and sliced ginger root",              10.00, 210,   35),
            ("Star Anise",               "Whole star anise pods",                     20.00, 110,   20),
            ("Fennel Seeds",             "Whole fennel seeds",                         6.50, 195,   30),
            ("Dried Mint Leaves",        "Peppermint leaves — dried",                 14.00, 130,   25),
            ("Paprika (Sweet)",          "Sweet paprika powder — Spanish grade",       9.00, 245,   40),
            ("Mixed Spice Blend",        "Traditional Egyptian 7-spice blend",        16.00, 160,   30),
            ("Lavender Flowers",         "Dried lavender buds for tea & aroma",       28.00,  70,   12),
            ("Thyme (Dried)",            "Mediterranean dried thyme",                  9.50, 175,   25),
            ("Dried Lemon Peel",         "Sun-dried lemon peel strips",               11.00, 140,   20),
            ("Oud Incense Chips",        "Premium Cambodian oud wood chips",         195.00,  30,    5),
            ("Musk Seeds (Amber)",       "Natural ambrette musk seeds",               85.00,  22,    5),
        ]
        cur.executemany("""
            INSERT INTO products (name, description, unit_price, quantity, minimum_quantity)
            VALUES (?, ?, ?, ?, ?)
        """, products)
        cur.execute("SELECT id, unit_price FROM products ORDER BY id")
        prod_rows = cur.fetchall()
        prod_ids  = [r['id'] for r in prod_rows]
        prod_prices = {r['id']: r['unit_price'] for r in prod_rows}
        print(f"[OK] {len(prod_ids)} products inserted.")

        # ── 5. EXPENSES (last 60 days) ────────────────────────────
        expense_data = [
            # (days_ago, description, amount, category)
            ( 2,  "Monthly shop rent — April 2026",          4500.00,  "Rent"),
            ( 5,  "Electricity bill — March",                 680.00,  "Utilities"),
            ( 5,  "Water bill — March",                       120.00,  "Utilities"),
            ( 7,  "Part-time cashier salary",                2200.00,  "Salaries"),
            ( 7,  "Store assistant salary",                  1800.00,  "Salaries"),
            (10,  "Display stands & shelving",                950.00,  "Maintenance"),
            (14,  "Packaging bags & labels",                  380.00,  "Supplies"),
            (18,  "Internet & phone subscription",            220.00,  "Utilities"),
            (20,  "Shop cleaning supplies",                   145.00,  "Supplies"),
            (22,  "Scale calibration & repair",               300.00,  "Maintenance"),
            (28,  "Social media advertising — April",         600.00,  "Other"),
            (32,  "Monthly shop rent — March 2026",          4500.00,  "Rent"),
            (35,  "Electricity bill — February",              710.00,  "Utilities"),
            (38,  "Part-time cashier salary — March",        2200.00,  "Salaries"),
            (38,  "Store assistant salary — March",          1800.00,  "Salaries"),
            (42,  "Herbs drying equipment maintenance",       450.00,  "Maintenance"),
            (45,  "Glass jar packaging — bulk order",         870.00,  "Supplies"),
            (50,  "Market stall fee — weekend bazaar",        250.00,  "Other"),
            (55,  "Accounting software subscription",         180.00,  "Other"),
            (60,  "Fire extinguisher refill",                 200.00,  "Maintenance"),
        ]
        today = datetime.now()
        for days_ago, desc, amount, category in expense_data:
            date_str = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            cur.execute("""
                INSERT INTO expenses (date, description, amount, category)
                VALUES (?, ?, ?, ?)
            """, (date_str, desc, amount, category))
        print(f"[OK] {len(expense_data)} expenses inserted.")

        # ── 6. PURCHASE INVOICES (last 45 days) ──────────────────
        purchase_scenarios = [
            # (days_ago, supplier_idx, [(product_idx, qty, price)])
            ( 3, 0, [(0,10,115.00),(5,20,35.00),(10,15,25.00)]),   # Saffron, Cardamom, Cloves
            ( 7, 1, [(1,100,7.50),(6,80,5.00),(8,60,6.50)]),       # Turmeric, Coriander, Anise
            (10, 2, [(7,30,28.00),(12,40,21.00),(17,50,12.50)]),    # Rose, Chamomile, Mint
            (14, 3, [(2,50,18.00),(3,80,5.00),(9,60,4.50)]),        # Black Seed, Cumin, Fenugreek
            (18, 4, [(23,8,180.00),(24,6,75.00)]),                  # Oud, Musk
            (22, 0, [(4,40,13.50),(11,40,16.00),(15,30,18.00)]),    # Cinnamon, Pepper, Star Anise
            (28, 1, [(13,60,10.00),(14,60,9.00),(16,50,5.50)]),     # Hibiscus, Ginger, Fennel
            (35, 2, [(18,70,7.50),(19,50,14.00),(21,50,8.00)]),     # Paprika, Mixed, Thyme
            (42, 3, [(20,25,26.00),(22,40,9.50)]),                  # Lavender, Lemon peel
            (45, 4, [(0,12,115.00),(5,15,35.00)]),                  # Saffron, Cardamom restock
        ]

        for days_ago, sup_idx, items in purchase_scenarios:
            date_str = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            supplier_id = sup_ids[sup_idx]
            total = sum(qty * price for _, qty, price in items)

            cur.execute("""
                INSERT INTO purchase_invoices (supplier_id, date, total_amount)
                VALUES (?, ?, ?)
            """, (supplier_id, date_str, total))
            inv_id = cur.lastrowid

            for prod_idx, qty, price in items:
                pid = prod_ids[prod_idx]
                cur.execute("""
                    INSERT INTO purchase_items (invoice_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """, (inv_id, pid, qty, price))

            # Journal entry
            cur.execute("""
                INSERT INTO journal_entries (date, reference_no, description)
                VALUES (?, ?, ?)
            """, (date_str, f"PUR{inv_id}", f"Purchase Invoice #{inv_id} — {suppliers[sup_idx][0]}"))
            je_id = cur.lastrowid
            cur.execute("""
                INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                SELECT ?, id, ?, ?, 0 FROM accounts WHERE code='1200'
            """, (je_id, f"Purchase #{inv_id}", total))
            cur.execute("""
                INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                SELECT ?, id, ?, 0, ? FROM accounts WHERE code='2000'
            """, (je_id, f"Purchase #{inv_id}", total))

        print(f"[OK] {len(purchase_scenarios)} purchase invoices inserted.")

        # ── 7. SALES INVOICES (last 45 days) ─────────────────────
        sales_scenarios = [
            # (days_ago, cust_idx, [(prod_idx, qty, price)])
            ( 1, 7, [(0, 3, 125.00),(5, 5, 38.00),(23, 1, 195.00)]),    # Pharaoh's Spice Shop
            ( 1, 5, [(1,15,  8.50),(6,10,  6.00),(18, 8,  9.00)]),      # Star Restaurant
            ( 2, 3, [(12,10, 24.00),(7, 5, 32.00),(17, 8, 14.00)]),     # El-Safa Herbal
            ( 3, 0, [(2, 8, 22.00),(10, 5, 28.00),(24, 2, 85.00)]),     # Al-Nour Pharmacy
            ( 4, 6, [(20, 4, 28.00),(7, 3, 32.00),(17, 6, 14.00)]),     # Cleopatra Beauty
            ( 5, 4, [(12, 8, 24.00),(13,12, 12.00),(14, 8, 10.00)]),    # Lotus Traditional
            ( 6, 1, [(1,20,  8.50),(6,15,  6.00),(8,10,  7.00)]),       # Badr Supermarket
            ( 7, 2, [(3,12,  6.00),(16,10,  6.50),(21, 5,  9.50)]),     # Aromatic Kitchen
            ( 9, 7, [(0, 5, 125.00),(11, 6, 18.00),(4,  8, 15.50)]),    # Pharaoh's again
            (11, 5, [(18,10,  9.00),(19, 8, 16.00),(6, 12,  6.00)]),    # Star Restaurant
            (13, 0, [(2,10, 22.00),(13,15, 12.00),(15, 6, 20.00)]),     # Al-Nour Pharmacy
            (15, 3, [(12, 6, 24.00),(7,  4, 32.00),(20, 3, 28.00)]),    # El-Safa Herbal
            (17, 6, [(24, 2, 85.00),(23, 1, 195.00),(7, 3, 32.00)]),    # Cleopatra Beauty
            (20, 4, [(9,10,  7.00),(16, 8,  6.50),(17, 6, 14.00)]),     # Lotus Traditional
            (22, 1, [(1,25,  8.50),(6,20,  6.00),(3,15,  6.00)]),       # Badr Supermarket
            (25, 2, [(4,10, 15.50),(5, 8, 38.00),(10, 5, 28.00)]),      # Aromatic Kitchen
            (28, 7, [(0, 4, 125.00),(24, 2, 85.00),(11, 4, 18.00)]),    # Pharaoh's
            (30, 5, [(18,12,  9.00),(19,10, 16.00),(8, 8,  7.00)]),     # Star Restaurant
            (33, 0, [(13,20, 12.00),(14,15, 10.00),(12,10, 24.00)]),    # Al-Nour Pharmacy
            (36, 3, [(15, 5, 20.00),(16, 8,  6.50),(21, 6,  9.50)]),    # El-Safa Herbal
            (40, 6, [(7,  5, 32.00),(20, 4, 28.00),(17, 8, 14.00)]),    # Cleopatra Beauty
            (43, 4, [(9, 12,  7.00),(2,  8, 22.00),(1, 10,  8.50)]),    # Lotus Traditional
            (45, 1, [(3,20,  6.00),(6,25,  6.00),(18,15,  9.00)]),      # Badr Supermarket
        ]

        for days_ago, cust_idx, items in sales_scenarios:
            date_str = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            customer_id = cust_ids[cust_idx]
            total = sum(qty * price for _, qty, price in items)

            cur.execute("""
                INSERT INTO sales_invoices (customer_id, date, total_amount)
                VALUES (?, ?, ?)
            """, (customer_id, date_str, total))
            inv_id = cur.lastrowid

            cogs = 0.0
            for prod_idx, qty, price in items:
                pid = prod_ids[prod_idx]
                cost = prod_prices.get(pid, price * 0.65)
                cur.execute("""
                    INSERT INTO sales_items (invoice_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """, (inv_id, pid, qty, price))
                cogs += cost * qty

            # Journal entry
            cur.execute("""
                INSERT INTO journal_entries (date, reference_no, description)
                VALUES (?, ?, ?)
            """, (date_str, f"SALE{inv_id}", f"Sales Invoice #{inv_id} — {customers[cust_idx][0]}"))
            je_id = cur.lastrowid
            cur.execute("""
                INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                SELECT ?, id, ?, ?, 0 FROM accounts WHERE code='1100'
            """, (je_id, f"Sale #{inv_id}", total))
            cur.execute("""
                INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                SELECT ?, id, ?, 0, ? FROM accounts WHERE code='4000'
            """, (je_id, f"Sale #{inv_id}", total))

        print(f"[OK] {len(sales_scenarios)} sales invoices inserted.")

        conn.commit()
        print("\n[SUCCESS] Realistic spice store data seeded successfully!")
        print(f"   * {len(suppliers)} suppliers | {len(customers)} customers")
        print(f"   * {len(products)} products | {len(expense_data)} expenses")
        print(f"   * {len(purchase_scenarios)} purchases | {len(sales_scenarios)} sales")


if __name__ == "__main__":
    seed_data()
