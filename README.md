# 🌿 Attar AIS Pro — Enterprise Accounting & ERP System for Spice Stores

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt&logoColor=white)
![Database](https://img.shields.io/badge/Database-SQLite3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-purple)

**Attar AIS Pro** is a comprehensive, desktop **Accounting & Information System (AIS / ERP)** specifically engineered for spice, herbal, and specialty retail enterprises. Built using **Python 3.13**, **PyQt6**, and **SQLite3**, it provides an intuitive, warm amber-themed interface for managing multi-module business operations, automated double-entry accounting ledgers, inventory tracking, and executive financial reporting.

---

## 🌟 Key Features & Modules

### 📊 1. Executive Dashboard & Real-Time KPIs
- **Live Business Metrics:** Real-time revenue, gross profit, total expenses, active inventory valuation, and net income counters.
- **Visual Analytics:** Interactive sales trends, top-selling spices/herbs, and expense breakdown charts powered by Matplotlib & PyQt.

### 🛒 2. Point of Sale (POS) & Sales Management
- Quick barcode/item search for bulk spices, herbal mixtures, and packaged goods.
- Customer invoice generation, discount application, tax calculation, and automated journal voucher posting.
- Multi-currency & transaction history tracking.

### 📦 3. Purchases & Supplier CRM
- Supplier profile management, purchase order logging, and payment status tracking (Paid, Partial, Credit).
- Automated inventory restocking and supplier balance ledger updates.

### 🌿 4. Inventory Control & Expiry Tracking
- Real-time stock levels, low-stock warnings, and unit conversions (Grams, Kilograms, Packages).
- Expiry date monitoring for organic herbal products with batch tracking.

### 🧪 5. Custom Spice Recipes & Blends
- Create custom herbal formulas and spice blends with automatic raw ingredient deduction from inventory.

### 💰 6. Automated Double-Entry Accounting & Financial Reports
- **Automatic Ledger Posting:** Every sale, purchase, and expense automatically updates General Ledger accounts.
- **Financial Statements:** Generates Income Statements (P&L), Balance Sheets, Trial Balances, and Account Statements.
- Export capabilities to **PDF** (ReportLab) and **Excel** (OpenPyXL).

### 👥 7. Multi-User RBAC & Audit Security Logs
- Role-based access control (Admin, Accountant, Sales Cashier).
- Timestamped audit logging of all sensitive transactions, deletions, and configuration edits.

---

## 🛠️ Technology Stack

* **Programming Language:** Python 3.13
* **GUI Framework:** PyQt6
* **Database Engine:** SQLite3 (WAL mode enabled)
* **Data & Analytics:** Pandas, OpenPyXL
* **PDF Report Generation:** ReportLab
* **Design & Theme:** Custom QSS Amber-Warm Theme System with Light/Dark switching

---

## 🚀 Getting Started

### Prerequisites
Ensure Python 3.10+ is installed on your operating system.

### 1. Clone the Repository
```bash
git clone https://github.com/yousafSamy1/ATTAR-AIS.git
cd ATTAR-AIS
```

### 2. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python main.py
```

---

## 📁 System Architecture

```
ATTAR/
├── main.py                   # Application Entry Point & Navigation Controller
├── AttarAIS.spec             # PyInstaller Executable Build Configuration
├── database/
│   └── db_config.py          # SQLite Schema, WAL Configuration & Connections
├── modules/                  # Specialized Business Logic Modules
│   ├── sales.py              # Sales & Invoicing Module
│   ├── purchases.py          # Purchase Orders & Supplier Ledger
│   ├── inventory.py          # Stock Control & Expiry Management
│   ├── accounting.py         # General Ledger & Double-Entry Accounting
│   ├── auto_accounting.py    # Automated Journal Entry Generator
│   ├── financial_reports.py  # P&L, Balance Sheet, Trial Balance Reports
│   ├── kpis.py               # Executive Analytics Dashboard
│   ├── recipes.py            # Herbal Recipe & Blend Compound Management
│   ├── users.py              # Authentication & User Management
│   ├── audit_log.py          # System Audit & Activity Logging
│   └── theme.py              # Theme Palette & QSS Styling Engine
├── resources/                # Visual Assets, Icons, and Images
├── requirements.txt          # Python Dependencies Manifest
└── README.md                 # System Documentation
```

---

## 👤 Author & Credits

**Yousef Samy** — *Back End & Full Stack Developer*  
[GitHub Profile](https://github.com/yousafSamy1)
