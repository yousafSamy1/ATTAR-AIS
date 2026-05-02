from database.db_config import DatabaseConnection

def clean_database():
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            
            # قائمة الجداول التي نريد تنظيفها
            tables = [
                'sales_items',
                'sales_invoices',
                'purchase_items',
                'purchase_invoices', 
                'products',
                'customers',
                'suppliers',
                'expenses',
                'journal_entries',
                'accounts'
            ]
            
            print("⏳ جاري تنظيف قاعدة البيانات...")
            
            # تنظيف كل جدول
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                print(f"✓ تم تنظيف جدول {table}")
                
            # حفظ التغييرات
            conn.commit()
            print("\n✨ تم تنظيف قاعدة البيانات بنجاح!")
            
    except Exception as e:
        print(f"❌ حدث خطأ: {str(e)}")

if __name__ == "__main__":
    clean_database()
