# مخطط الكيانات والعلاقات (ERD) لمشروع AttarAIS

بناءً على ملف إعداد قاعدة البيانات `db_config.py`، إليك مخطط الكيانات والعلاقات (ERD) الخاص بالمشروع والذي يوضح الجداول والحقول والعلاقات بينها.

```mermaid
erDiagram
    accounts {
        INTEGER id PK
        TEXT code "UNIQUE"
        TEXT name
        TEXT type "asset, liability, equity, revenue, expense"
        DECIMAL balance
        DATETIME created_at
    }

    journal_entries {
        INTEGER id PK
        DATE date
        TEXT reference_no "UNIQUE"
        TEXT description
        DATETIME created_at
    }

    journal_entry_items {
        INTEGER id PK
        INTEGER journal_entry_id FK
        INTEGER account_id FK
        TEXT description
        DECIMAL debit
        DECIMAL credit
    }

    general_ledger {
        INTEGER id PK
        INTEGER account_id FK
        INTEGER journal_entry_id FK
        DATE date
        TEXT description
        DECIMAL debit
        DECIMAL credit
        DECIMAL balance
    }

    customers {
        INTEGER id PK
        TEXT name
        TEXT contact_person
        TEXT phone
        TEXT email
        TEXT address
        REAL balance
    }

    suppliers {
        INTEGER id PK
        TEXT name
        TEXT contact_person
        TEXT phone
        TEXT email
        TEXT address
        REAL balance
    }

    products {
        INTEGER id PK
        TEXT name
        TEXT description
        REAL unit_price
        INTEGER quantity
        INTEGER minimum_quantity
    }

    sales_invoices {
        INTEGER id PK
        INTEGER customer_id FK
        TEXT date
        REAL total_amount
        REAL paid_amount
        TEXT status
    }

    sales_items {
        INTEGER id PK
        INTEGER invoice_id FK
        INTEGER product_id FK
        INTEGER quantity
        REAL unit_price
    }

    purchase_invoices {
        INTEGER id PK
        INTEGER supplier_id FK
        TEXT date
        REAL total_amount
        REAL paid_amount
        TEXT status
    }

    purchase_items {
        INTEGER id PK
        INTEGER invoice_id FK
        INTEGER product_id FK
        INTEGER quantity
        REAL unit_price
    }

    expenses {
        INTEGER id PK
        TEXT date
        TEXT category
        TEXT description
        REAL amount
    }

    revenues {
        INTEGER id PK
        TEXT date
        TEXT category
        TEXT description
        REAL amount
    }

    %% Relationships
    journal_entries ||--o{ journal_entry_items : "contains"
    accounts ||--o{ journal_entry_items : "is recorded in"
    
    accounts ||--o{ general_ledger : "has entries in"
    journal_entries ||--o{ general_ledger : "posts to"

    customers ||--o{ sales_invoices : "makes"
    sales_invoices ||--o{ sales_items : "contains"
    products ||--o{ sales_items : "sold as"

    suppliers ||--o{ purchase_invoices : "issues"
    purchase_invoices ||--o{ purchase_items : "contains"
    products ||--o{ purchase_items : "purchased as"
```

### تفاصيل العلاقات:

*   **القيود اليومية (Journal Entries):**
    *   كل قيد يومية (`journal_entries`) يمكن أن يحتوي على عدة عناصر (`journal_entry_items`).
    *   يتم ربط كل عنصر قيد بحساب معين من جدول الحسابات (`accounts`).
*   **دفتر الأستاذ العام (General Ledger):**
    *   يتم ترحيل الحركات من القيود اليومية إلى دفتر الأستاذ العام وتُربط برقم القيد (`journal_entry_id`) ورقم الحساب (`account_id`).
*   **المبيعات (Sales):**
    *   كل عميل (`customers`) يمكن أن يكون لديه عدة فواتير مبيعات (`sales_invoices`).
    *   كل فاتورة مبيعات تحتوي على عدة عناصر/أصناف (`sales_items`).
    *   عناصر الفاتورة مرتبطة بجدول المنتجات (`products`).
*   **المشتريات (Purchases):**
    *   كل مورد (`suppliers`) يمكن أن تصدر منه عدة فواتير مشتريات (`purchase_invoices`).
    *   كل فاتورة مشتريات تحتوي على عدة عناصر (`purchase_items`).
    *   عناصر فاتورة الشراء مرتبطة أيضاً بجدول المنتجات (`products`).
*   **المصروفات والإيرادات (Expenses & Revenues):**
    *   جداول مستقلة (مبدئياً في هذا الإعداد) لتسجيل الحركات المباشرة.
