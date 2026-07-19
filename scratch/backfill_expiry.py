import sqlite3
import random
from datetime import datetime, timedelta
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from database.db_config import DB_FILE

def backfill_expiry():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get all products
        cursor.execute("SELECT id, name FROM products")
        products = cursor.fetchall()

        print(f"Found {len(products)} products to backfill.")

        for p_id, p_name in products:
            # Generate a random number of days from -30 to 730
            random_days = random.randint(-30, 730)
            expiry_date = (datetime.now() + timedelta(days=random_days)).strftime("%Y-%m-%d")
            
            # Update product
            cursor.execute("UPDATE products SET expiry_date = ? WHERE id = ?", (expiry_date, p_id))
            
            # Update latest purchase item for this product if it exists
            cursor.execute("""
                UPDATE purchase_items 
                SET expiry_date = ? 
                WHERE id = (SELECT id FROM purchase_items WHERE product_id = ? ORDER BY id DESC LIMIT 1)
            """, (expiry_date, p_id))

        conn.commit()
        conn.close()
        print("Successfully backfilled random expiry dates.")

    except Exception as e:
        print(f"Error backfilling: {e}")

if __name__ == "__main__":
    backfill_expiry()
