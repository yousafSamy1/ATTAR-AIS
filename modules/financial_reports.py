# PyQt6 Widgets: Core GUI components
from PyQt6.QtWidgets import (
    QWidget,        # Base class for all UI objects
    QVBoxLayout,    # Vertical box layout manager
    QHBoxLayout,    # Horizontal box layout manager
    QPushButton,    # Standard push button widget
    QLabel,         # Text or image display widget
    QTableWidget,   # Table/grid widget for displaying data
    QTableWidgetItem,  # Individual cell item for QTableWidget
    QHeaderView,    # Header view for tables and tree views
    QComboBox,      # Drop-down selection widget
    QDateEdit,      # Date editing widget with calendar
    QDialog,        # Base class for dialog windows
    QMessageBox,    # Modal dialog for showing messages
    QLineEdit       # Line edit widget for input
)

# PyQt6 Core: Fundamental classes and functions
from PyQt6.QtCore import (
    Qt,            # Contains core non-widget functionality
    QDate,         # Date handling class
    QTimer,        # Timer class for periodic events
    pyqtSignal     # Signal/slot communication
)
from PyQt6.QtGui import QColor

# Database Configuration
from database.db_config import DatabaseConnection  # Custom database connection handler
from modules.theme import COLORS, get_button_style

# Python Standard Libraries
from datetime import (
    datetime,      # Basic date and time types
    timedelta      # Duration/time difference calculations
)

class FinancialReportsModule(QWidget):
    """Financial Reports Module - Displays various types of financial reports"""
    transaction_clicked = pyqtSignal(str)
    
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.init_ui()
        
        # Setup auto-refresh timer with a reasonable refresh rate
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_current_view)
        self.refresh_timer.start(1000)  # Real-time refresh every 1 second
        
    def init_ui(self):
        """Initialize the graphical user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Financial Reports")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        layout.addWidget(header)
        
        # Create button layout at the top
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)  # Space between buttons
        btn_layout.setContentsMargins(10, 10, 10, 10)  # Margins around button group
        
        # Create buttons for each report type
        self.journal_btn = QPushButton("📋 Journal Entries")
        self.ledger_btn = QPushButton("📖 General Ledger")
        self.income_btn = QPushButton("💰 Income Statement")
        self.balance_btn = QPushButton("⚖️ Balance Sheet")
        self.trial_btn = QPushButton("📊 Trial Balance")
        self.adj_trial_btn = QPushButton("📑 Adj. Trial Balance")
        self.cash_flow_btn = QPushButton("💵 Cash Flow")
        self.equity_btn = QPushButton("📈 Owner Equity")
        
        # Normal button style (inactive)
        self.button_style = get_button_style('bg_mid', font_size=13, padding="10px 15px") + f"QPushButton {{ min-width: 140px; margin: 0 5px; color: {COLORS['text_main']}; }}"
        
        # Active button style (currently selected)
        self.active_button_style = get_button_style('accent', font_size=13, padding="10px 15px") + f"QPushButton {{ min-width: 140px; margin: 0 5px; border-bottom: 3px solid {COLORS['accent2']}; }}"
        
        # Apply basic style to all buttons
        for btn in [self.journal_btn, self.ledger_btn, self.income_btn, 
                   self.balance_btn, self.trial_btn, self.adj_trial_btn,
                   self.cash_flow_btn, self.equity_btn]:
            btn.setStyleSheet(self.button_style)
            btn_layout.addWidget(btn)
        
        # Add flexible space at start and end to center buttons
        btn_layout.insertStretch(0)
        btn_layout.addStretch()
        
        # Add search box for filtering
        search_layout = QHBoxLayout()
        entity_label = QLabel("Filter by Supplier/Customer:")
        self.entity_search = QLineEdit()
        self.entity_search.setPlaceholderText("Enter supplier/customer name...")
        self.entity_search.textChanged.connect(self.filter_entries)
        
        search_layout.addWidget(entity_label)
        search_layout.addWidget(self.entity_search)
        layout.addLayout(search_layout)
        
        # Add instruction label for user to select report type
        self.instruction_label = QLabel("Please select a report type from the buttons above")
        self.instruction_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_dim']};
                font-size: 16px;
                padding: 20px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        
        # Create table for displaying data
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only
        self.table.itemDoubleClicked.connect(self._on_table_double_clicked)
        
        # Add elements to main layout
        layout.addLayout(btn_layout)
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.table)
        
        # Hide table initially
        self.table.hide()
        
        # Connect buttons to their respective functions
        self.journal_btn.clicked.connect(lambda: self._handle_button_click(self.journal_btn))
        self.ledger_btn.clicked.connect(lambda: self._handle_button_click(self.ledger_btn))
        self.income_btn.clicked.connect(lambda: self._handle_button_click(self.income_btn))
        self.balance_btn.clicked.connect(lambda: self._handle_button_click(self.balance_btn))
        self.trial_btn.clicked.connect(lambda: self._handle_button_click(self.trial_btn))
        self.adj_trial_btn.clicked.connect(lambda: self._handle_button_click(self.adj_trial_btn))
        self.cash_flow_btn.clicked.connect(lambda: self._handle_button_click(self.cash_flow_btn))
        self.equity_btn.clicked.connect(lambda: self._handle_button_click(self.equity_btn))

    def _handle_button_click(self, clicked_button):
        """Handle button clicks and update active button state"""
        self.set_active_button(clicked_button)
        
        # Hide instruction label and show table
        self.instruction_label.hide()
        self.table.show()
        
        # Call appropriate function based on clicked button
        if clicked_button == self.journal_btn:
            self.show_journal_entries()
        elif clicked_button == self.ledger_btn:
            self.show_general_ledger()
        elif clicked_button == self.income_btn:
            self.show_income_statement()
        elif clicked_button == self.balance_btn:
            self.show_balance_sheet()
        elif clicked_button == self.trial_btn:
            self.show_trial_balance()
        elif clicked_button == self.adj_trial_btn:
            self.show_adjusted_trial_balance()
        elif clicked_button == self.cash_flow_btn:
            self.show_cash_flow_statement()
        elif clicked_button == self.equity_btn:
            self.show_statement_of_owner_equity()

    def set_active_button(self, active_btn):
        """Update button styles to show which report is active"""
        self.current_active_button = active_btn
        for btn in [self.journal_btn, self.ledger_btn, self.income_btn, 
                   self.balance_btn, self.trial_btn, self.adj_trial_btn,
                   self.cash_flow_btn, self.equity_btn]:
            btn.setStyleSheet(self.active_button_style if btn == active_btn else self.button_style)

    def filter_entries(self):
        """Filter table entries based on entity name"""
        entity_text = self.entity_search.text().lower()
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            if self.current_active_button == self.journal_btn:
                entity_item = self.table.item(row, 6)   # Entity column
                
                if entity_item and entity_text:
                    entity_name = entity_item.text().lower()
                    if entity_text not in entity_name:
                        show_row = False
                        
            elif self.current_active_button == self.ledger_btn:
                entity_item = self.table.item(row, 7)   # Entity column
                
                if entity_item and entity_text:
                    entity_name = entity_item.text().lower()
                    if entity_text not in entity_name:
                        show_row = False
            
            self.table.setRowHidden(row, not show_row)

    def _on_table_double_clicked(self, item):
        """Handle double click on table items to navigate to original transaction"""
        row = item.row()
        ref_col = -1
        for col in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(col)
            if header_item and header_item.text() == "Reference":
                ref_col = col
                break
        
        if ref_col != -1:
            ref_item = self.table.item(row, ref_col)
            if ref_item:
                ref = ref_item.text()
                self.transaction_clicked.emit(ref)

    def show_journal_entries(self):
        """Show journal entries"""
        self.table.clear()
        self.table.setColumnCount(7)  # Added one more column for supplier/customer
        # Set column headers
        self.table.setHorizontalHeaderLabels([
            "Date",         # Date
            "Reference",    # Reference number
            "Type",         # Account type
            "Description",  # Description
            "Debit",        # Debit
            "Credit",       # Credit
            "Supplier/Customer" # Supplier/Customer
        ])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        je.date,
                        je.reference_no,
                        a.name as account_name,
                        jei.description,
                        jei.debit,
                        jei.credit,
                        CASE
                            WHEN je.reference_no LIKE 'SALE%' THEN (
                                SELECT c.name 
                                FROM sales_invoices si 
                                JOIN customers c ON si.customer_id = c.id 
                                WHERE CAST(si.id AS TEXT) = SUBSTR(je.reference_no, 6)
                                LIMIT 1
                            )
                            WHEN je.reference_no LIKE 'PUR%' THEN (
                                SELECT s.name 
                                FROM purchase_invoices pi 
                                JOIN suppliers s ON pi.supplier_id = s.id 
                                WHERE CAST(pi.id AS TEXT) = SUBSTR(je.reference_no, 5)
                                LIMIT 1
                            )
                            ELSE NULL
                        END as entity_name
                    FROM journal_entries je
                    JOIN journal_entry_items jei ON je.id = jei.journal_entry_id
                    JOIN accounts a ON jei.account_id = a.id
                    ORDER BY je.date DESC, je.id DESC, jei.id ASC
                """)
                entries = cursor.fetchall()
                
                self.table.setRowCount(len(entries))
                for row, entry in enumerate(entries):
                    # Date
                    date_item = QTableWidgetItem(entry['date'])
                    date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 0, date_item)
                    
                    # Reference
                    ref_item = QTableWidgetItem(entry['reference_no'])
                    ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 1, ref_item)
                    
                    # Account
                    acc_item = QTableWidgetItem(entry['account_name'])
                    acc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 2, acc_item)
                    
                    # Description
                    desc_item = QTableWidgetItem(entry['description'])
                    desc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 3, desc_item)
                    
                    # Debit
                    debit_item = QTableWidgetItem(f"EGP {entry['debit']:.2f}" if entry['debit'] > 0 else "")
                    debit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 4, debit_item)
                    
                    # Credit
                    credit_item = QTableWidgetItem(f"EGP {entry['credit']:.2f}" if entry['credit'] > 0 else "")
                    credit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 5, credit_item)
                    
                    # Entity (Supplier/Customer)
                    entity_item = QTableWidgetItem(entry['entity_name'] if entry['entity_name'] else "")
                    entity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 6, entity_item)
                
                # Style the table
                header = self.table.horizontalHeader()
                if header:
                    # Set specific column widths
                    self.table.setColumnWidth(0, 100)  # Date
                    self.table.setColumnWidth(1, 120)  # Reference
                    self.table.setColumnWidth(2, 200)  # Account
                    self.table.setColumnWidth(3, 250)  # Description
                    self.table.setColumnWidth(4, 100)  # Debit
                    self.table.setColumnWidth(5, 100)  # Credit
                    self.table.setColumnWidth(6, 150)  # Entity
                    header.setStretchLastSection(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading journal entries: {str(e)}")
    
    def show_general_ledger(self):
        """Show general ledger"""
        self.table.clear()
        self.table.setColumnCount(8)  # Added one more column for supplier/customer
        # Set column headers
        self.table.setHorizontalHeaderLabels([
            "Type",         # Account type
            "Date",         # Date
            "Reference",    # Reference number
            "Description",  # Description
            "Debit",        # Debit
            "Credit",       # Credit
            "Balance",      # Balance
            "Supplier/Customer" # Supplier/Customer
        ])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        gl.id,
                        a.code as account_code,
                        a.name as account_name,
                        gl.date,
                        je.reference_no,
                        gl.description,
                        gl.debit,
                        gl.credit,
                        gl.account_id,
                        a.type as account_type,
                        a.balance as account_balance,
                        CASE
                            WHEN je.reference_no LIKE 'SALE%' THEN (
                                SELECT c.name 
                                FROM sales_invoices si 
                                JOIN customers c ON si.customer_id = c.id 
                                WHERE CAST(si.id AS TEXT) = SUBSTR(je.reference_no, 6)
                                LIMIT 1
                            )
                            WHEN je.reference_no LIKE 'PUR%' THEN (
                                SELECT s.name 
                                FROM purchase_invoices pi 
                                JOIN suppliers s ON pi.supplier_id = s.id 
                                WHERE CAST(pi.id AS TEXT) = SUBSTR(je.reference_no, 5)
                                LIMIT 1
                            )
                            ELSE NULL
                        END as entity_name
                    FROM general_ledger gl
                    JOIN accounts a ON gl.account_id = a.id
                    JOIN journal_entries je ON gl.journal_entry_id = je.id
                    ORDER BY a.code, gl.date ASC, gl.id ASC
                """)
                all_entries = cursor.fetchall()
                
                # Group by account and calculate running balances
                account_balances = {} # Account ID -> Running Balance
                processed_entries = []
                
                for entry in all_entries:
                    acc_id = entry['account_id']
                    acc_type = entry['account_type']
                    
                    if acc_id not in account_balances:
                        account_balances[acc_id] = 0.0
                    
                    # Update running balance based on account type
                    if acc_type in ('asset', 'expense'):
                        account_balances[acc_id] += (entry['debit'] - entry['credit'])
                    else:
                        account_balances[acc_id] += (entry['credit'] - entry['debit'])
                    
                    # Store the running balance with the entry
                    entry_dict = dict(entry)
                    entry_dict['running_balance'] = account_balances[acc_id]
                    processed_entries.append(entry_dict)
                
                # Sort by account code ASC, then date DESC, then id DESC
                processed_entries.sort(key=lambda x: x['id'], reverse=True)
                processed_entries.sort(key=lambda x: x['date'], reverse=True)
                processed_entries.sort(key=lambda x: x['account_code'])
                self.table.setRowCount(len(processed_entries))
                for row, entry in enumerate(processed_entries):
                    # Account
                    acc_item = QTableWidgetItem(entry['account_name'])
                    acc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 0, acc_item)
                    
                    # Date
                    date_item = QTableWidgetItem(entry['date'])
                    date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 1, date_item)
                    
                    # Reference
                    ref_item = QTableWidgetItem(entry['reference_no'])
                    ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 2, ref_item)
                    
                    # Description
                    desc_item = QTableWidgetItem(entry['description'])
                    desc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 3, desc_item)
                    
                    # Debit
                    debit_item = QTableWidgetItem(f"EGP {entry['debit']:.2f}" if entry['debit'] > 0 else "")
                    debit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 4, debit_item)
                    
                    # Credit
                    credit_item = QTableWidgetItem(f"EGP {entry['credit']:.2f}" if entry['credit'] > 0 else "")
                    credit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 5, credit_item)
                    
                    # Balance (Now using the calculated running balance)
                    balance_item = QTableWidgetItem(f"EGP {entry['running_balance']:.2f}")
                    balance_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 6, balance_item)
                    
                    # Entity (Supplier/Customer)
                    entity_item = QTableWidgetItem(entry['entity_name'] if entry['entity_name'] else "")
                    entity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 7, entity_item)
                
                # Style the table
                header = self.table.horizontalHeader()
                if header:
                    # Set specific column widths
                    self.table.setColumnWidth(0, 200)  # Account
                    self.table.setColumnWidth(1, 100)  # Date
                    self.table.setColumnWidth(2, 120)  # Reference
                    self.table.setColumnWidth(3, 250)  # Description
                    self.table.setColumnWidth(4, 100)  # Debit
                    self.table.setColumnWidth(5, 100)  # Credit
                    self.table.setColumnWidth(6, 100)  # Balance
                    self.table.setColumnWidth(7, 150)  # Entity
                    header.setStretchLastSection(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading general ledger: {str(e)}")
    
    def show_income_statement(self):
        """Show income statement"""
        self.table.clear()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([
            "Item",    # Item
            "Amount"  # Amount
        ])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # Get revenue accounts
                cursor.execute("""
                    SELECT SUM(balance) as total_revenue
                    FROM accounts
                    WHERE type = 'revenue'
                """)
                revenue = cursor.fetchone()['total_revenue'] or 0
                
                # Get cost of goods sold
                cursor.execute("""
                    SELECT SUM(balance) as total_cogs
                    FROM accounts
                    WHERE code = '5000'  -- Cost of Goods Sold account
                """)
                cogs = cursor.fetchone()['total_cogs'] or 0
                
                # Get operating expenses
                cursor.execute("""
                    SELECT SUM(balance) as total_expenses
                    FROM accounts
                    WHERE type = 'expense' AND code != '5000'
                """)
                expenses = cursor.fetchone()['total_expenses'] or 0
                
                # Calculate gross and net profit
                gross_profit = revenue - cogs
                net_profit = gross_profit - expenses
                
                # Display the income statement
                rows = [
                    ("Revenue", revenue),
                    ("Cost of Goods Sold", cogs),
                    ("Gross Profit", gross_profit),
                    ("Operating Expenses", expenses),
                    ("Net Profit", net_profit)
                ]
                
                self.table.setRowCount(len(rows))
                for row, (item, amount) in enumerate(rows):
                    item_cell = QTableWidgetItem(item)
                    item_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    amount_cell = QTableWidgetItem(f"EGP {amount:.2f}")
                    amount_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.table.setItem(row, 0, item_cell)
                    self.table.setItem(row, 1, amount_cell)
                    
                    # Style the rows
                    if item in ["Gross Profit", "Net Profit"]:
                        for col in range(2):
                            cell = self.table.item(row, col)
                            if cell:
                                cell.setBackground(QColor(COLORS['sidebar_mid']))
                                font = cell.font()
                                font.setBold(True)
                                cell.setFont(font)
                
                # Style the table
                header = self.table.horizontalHeader()
                if header:
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating income statement: {str(e)}")
    
    def show_balance_sheet(self):
        """Show balance sheet"""
        self.table.clear()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([
            "Item",    # Item
            "Amount"  # Amount
        ])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # Get assets
                cursor.execute("""
                    SELECT name, balance
                    FROM accounts
                    WHERE type = 'asset'
                    ORDER BY code
                """)
                assets = cursor.fetchall()
                total_assets = sum(asset['balance'] for asset in assets)
                
                # Get liabilities
                cursor.execute("""
                    SELECT name, balance
                    FROM accounts
                    WHERE type = 'liability'
                    ORDER BY code
                """)
                liabilities = cursor.fetchall()
                total_liabilities = sum(liability['balance'] for liability in liabilities)
                
                # Get equity accounts
                cursor.execute("""
                    SELECT name, balance
                    FROM accounts
                    WHERE type = 'equity'
                    ORDER BY code
                """)
                equity_accounts = cursor.fetchall()
                
                # Calculate retained earnings (net income)
                cursor.execute("""
                    SELECT 
                        (SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE type = 'revenue') -
                        (SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE type = 'expense')
                    as retained_earnings
                """)
                retained_earnings = cursor.fetchone()['retained_earnings']
                
                total_equity = sum(equity['balance'] for equity in equity_accounts) + retained_earnings
                
                # Prepare rows for display
                rows = []
                
                # Assets section
                rows.append(("ASSETS", ""))
                for asset in assets:
                    rows.append(("  " + asset['name'], asset['balance']))
                rows.append(("Total Assets", total_assets))
                rows.append(("", ""))  # Blank row
                
                # Liabilities section
                rows.append(("LIABILITIES", ""))
                for liability in liabilities:
                    rows.append(("  " + liability['name'], liability['balance']))
                rows.append(("Total Liabilities", total_liabilities))
                rows.append(("", ""))  # Blank row
                
                # Equity section
                rows.append(("EQUITY", ""))
                for equity in equity_accounts:
                    rows.append(("  " + equity['name'], equity['balance']))
                rows.append(("  Retained Earnings", retained_earnings))
                rows.append(("Total Equity", total_equity))
                rows.append(("", ""))  # Blank row
                rows.append(("Total Liabilities and Equity", total_liabilities + total_equity))
                
                # Display the balance sheet
                self.table.setRowCount(len(rows))
                for row, (item, amount) in enumerate(rows):
                    item_cell = QTableWidgetItem(item)
                    item_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    amount_cell = QTableWidgetItem(f"EGP {amount:.2f}" if amount != "" else "")
                    amount_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.table.setItem(row, 0, item_cell)
                    self.table.setItem(row, 1, amount_cell)
                    
                    # Style the rows
                    if not item.startswith("  ") and item != "":  # Headers and totals
                        for col in range(2):
                            cell = self.table.item(row, col)
                            if cell:
                                cell.setBackground(QColor(COLORS['sidebar_mid']))
                                font = cell.font()
                                font.setBold(True)
                                cell.setFont(font)
                
                # Style the table
                header = self.table.horizontalHeader()
                if header:
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating balance sheet: {str(e)}")
    
    def show_trial_balance(self):
        """Show trial balance"""
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Type",    # Account type
            "Debit",   # Debit
            "Credit"   # Credit
        ])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        name,
                        CASE 
                            WHEN type IN ('asset', 'expense') THEN 
                                CASE WHEN balance > 0 THEN balance ELSE 0 END
                            ELSE 
                                CASE WHEN balance < 0 THEN -balance ELSE 0 END
                        END as debit_balance,
                        CASE 
                            WHEN type IN ('asset', 'expense') THEN 
                                CASE WHEN balance < 0 THEN -balance ELSE 0 END
                            ELSE 
                                CASE WHEN balance > 0 THEN balance ELSE 0 END
                        END as credit_balance
                    FROM accounts
                    WHERE balance != 0
                    ORDER BY code
                """)
                accounts = cursor.fetchall()
                
                total_debit = sum(account['debit_balance'] for account in accounts)
                total_credit = sum(account['credit_balance'] for account in accounts)
                
                # Display accounts
                self.table.setRowCount(len(accounts) + 2)  # +2 for total row and header
                for row, account in enumerate(accounts):
                    name_cell = QTableWidgetItem(account['name'])
                    name_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    debit_cell = QTableWidgetItem(f"EGP {account['debit_balance']:.2f}" if account['debit_balance'] > 0 else "")
                    debit_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    credit_cell = QTableWidgetItem(f"EGP {account['credit_balance']:.2f}" if account['credit_balance'] > 0 else "")
                    credit_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.table.setItem(row, 0, name_cell)
                    self.table.setItem(row, 1, debit_cell)
                    self.table.setItem(row, 2, credit_cell)
                
                # Add total row
                total_row = len(accounts)
                total_label = QTableWidgetItem("Total")
                total_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                total_debit_cell = QTableWidgetItem(f"EGP {total_debit:.2f}")
                total_debit_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                total_credit_cell = QTableWidgetItem(f"EGP {total_credit:.2f}")
                total_credit_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                
                self.table.setItem(total_row, 0, total_label)
                self.table.setItem(total_row, 1, total_debit_cell)
                self.table.setItem(total_row, 2, total_credit_cell)
                
                # Style the total row
                for col in range(3):
                    cell = self.table.item(total_row, col)
                    if cell:
                        cell.setBackground(QColor(COLORS['sidebar_mid']))
                        font = cell.font()
                        font.setBold(True)
                        cell.setFont(font)
                
                # Style the table
                header = self.table.horizontalHeader()
                if header:
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating trial balance: {str(e)}")

    def show_adjusted_trial_balance(self):
        """Show 6-column adjusted trial balance"""
        self.set_active_button(self.adj_trial_btn)
        self.table.clear()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Account Name",
            "Unadjusted Balance",
            "Adjustments (Dr/Cr)",
            "Adjusted Debit",
            "Adjusted Credit"
        ])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # We'll treat entries from the current month as "Adjustments" 
                # and everything before as "Unadjusted"
                start_of_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
                
                cursor.execute("""
                    SELECT 
                        a.name,
                        a.type,
                        a.balance as current_balance,
                        COALESCE((
                            SELECT SUM(gl.debit - gl.credit)
                            FROM general_ledger gl
                            WHERE gl.account_id = a.id AND gl.date < ?
                        ), 0) as unadjusted_balance,
                        COALESCE((
                            SELECT SUM(gl.debit - gl.credit)
                            FROM general_ledger gl
                            WHERE gl.account_id = a.id AND gl.date >= ?
                        ), 0) as adjustments
                    FROM accounts a
                    WHERE a.balance != 0 OR EXISTS (SELECT 1 FROM general_ledger WHERE account_id = a.id)
                    ORDER BY a.code
                """, (start_of_month, start_of_month))
                
                accounts = cursor.fetchall()
                
                self.table.setRowCount(len(accounts) + 1)
                
                total_adj_dr = 0
                total_adj_cr = 0
                
                for row, acc in enumerate(accounts):
                    self.table.setItem(row, 0, QTableWidgetItem(acc['name']))
                    
                    # Unadjusted
                    unadj = acc['unadjusted_balance']
                    self.table.setItem(row, 1, QTableWidgetItem(f"EGP {unadj:,.2f}"))
                    
                    # Adjustments
                    adj = acc['adjustments']
                    adj_item = QTableWidgetItem(f"EGP {adj:,.2f}" if adj != 0 else "-")
                    if adj > 0: adj_item.setForeground(QColor("#10b981"))
                    elif adj < 0: adj_item.setForeground(QColor("#ef4444"))
                    self.table.setItem(row, 2, adj_item)
                    
                    # Adjusted Dr/Cr
                    curr = acc['current_balance']
                    dr = curr if curr > 0 else 0
                    cr = -curr if curr < 0 else 0
                    
                    dr_item = QTableWidgetItem(f"EGP {dr:,.2f}" if dr > 0 else "")
                    cr_item = QTableWidgetItem(f"EGP {cr:,.2f}" if cr > 0 else "")
                    
                    self.table.setItem(row, 3, dr_item)
                    self.table.setItem(row, 4, cr_item)
                    
                    total_adj_dr += dr
                    total_adj_cr += cr

                # Total row
                total_row = len(accounts)
                self.table.setItem(total_row, 0, QTableWidgetItem("TOTALS"))
                self.table.setItem(total_row, 3, QTableWidgetItem(f"EGP {total_adj_dr:,.2f}"))
                self.table.setItem(total_row, 4, QTableWidgetItem(f"EGP {total_adj_cr:,.2f}"))
                
                for col in range(5):
                    item = self.table.item(total_row, col)
                    if item:
                        item.setBackground(QColor(COLORS['sidebar_mid']))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

                self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate adjusted trial balance: {e}")

    def show_cash_flow_statement(self):
        """Show cash flow statement (simplified indirect/direct method)"""
        self.table.clear()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Cash Flow Activity", "Amount"])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # Operating Activities
                cursor.execute("""
                    SELECT SUM(gl.debit - gl.credit) 
                    FROM general_ledger gl 
                    JOIN journal_entries je ON gl.journal_entry_id = je.id 
                    WHERE gl.account_id = (SELECT id FROM accounts WHERE code = '1000')
                    AND je.reference_no LIKE 'SALE-%'
                """)
                cash_from_sales = cursor.fetchone()[0] or 0
                
                cursor.execute("""
                    SELECT SUM(gl.credit - gl.debit) 
                    FROM general_ledger gl 
                    JOIN journal_entries je ON gl.journal_entry_id = je.id 
                    WHERE gl.account_id = (SELECT id FROM accounts WHERE code = '1000')
                    AND je.reference_no LIKE 'EXP-%'
                """)
                cash_for_expenses = cursor.fetchone()[0] or 0
                
                cursor.execute("""
                    SELECT SUM(gl.credit - gl.debit) 
                    FROM general_ledger gl 
                    JOIN journal_entries je ON gl.journal_entry_id = je.id 
                    WHERE gl.account_id = (SELECT id FROM accounts WHERE code = '1000')
                    AND je.reference_no LIKE 'PUR-%'
                """)
                cash_for_purchases = cursor.fetchone()[0] or 0
                
                operating_cash = cash_from_sales - cash_for_expenses - cash_for_purchases
                
                # Display
                rows = [
                    ("Operating Activities", ""),
                    ("  Cash Received from Customers", cash_from_sales),
                    ("  Cash Paid for Expenses", -cash_for_expenses),
                    ("  Cash Paid for Inventory", -cash_for_purchases),
                    ("Net Cash from Operating Activities", operating_cash),
                    ("Investing Activities", ""),
                    ("  (No Data Yet)", 0),
                    ("Financing Activities", ""),
                    ("  (No Data Yet)", 0),
                    ("Net Increase (Decrease) in Cash", operating_cash)
                ]
                
                self.table.setRowCount(len(rows))
                for row, (item, amount) in enumerate(rows):
                    item_cell = QTableWidgetItem(item)
                    
                    if amount == "":
                        amount_cell = QTableWidgetItem("")
                        font = item_cell.font()
                        font.setBold(True)
                        item_cell.setFont(font)
                    else:
                        amount_cell = QTableWidgetItem(f"EGP {amount:,.2f}")
                        amount_cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.table.setItem(row, 0, item_cell)
                    self.table.setItem(row, 1, amount_cell)
                    
                self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate cash flow statement: {e}")

    def show_statement_of_owner_equity(self):
        """Show statement of owner equity"""
        self.table.clear()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Item", "Amount"])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # Get Owner Capital
                cursor.execute("SELECT balance FROM accounts WHERE code = '3000'")
                capital = cursor.fetchone()
                capital = capital['balance'] if capital else 0
                
                # Calculate Net Income
                cursor.execute("SELECT SUM(balance) FROM accounts WHERE type = 'revenue'")
                revenue = cursor.fetchone()[0] or 0
                cursor.execute("SELECT SUM(balance) FROM accounts WHERE type = 'expense'")
                expenses = cursor.fetchone()[0] or 0
                net_income = revenue - expenses
                
                # Get Drawings
                cursor.execute("SELECT balance FROM accounts WHERE code = '3200'")
                drawings = cursor.fetchone()
                drawings = drawings['balance'] if drawings else 0
                
                ending_capital = capital + net_income - drawings
                
                rows = [
                    ("Beginning Capital", capital),
                    ("Add: Net Income", net_income),
                    ("Less: Drawings", -drawings),
                    ("Ending Capital", ending_capital)
                ]
                
                self.table.setRowCount(len(rows))
                for row, (item, amount) in enumerate(rows):
                    item_cell = QTableWidgetItem(item)
                    amount_cell = QTableWidgetItem(f"EGP {amount:,.2f}")
                    amount_cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.table.setItem(row, 0, item_cell)
                    self.table.setItem(row, 1, amount_cell)
                    
                    if item == "Ending Capital":
                        font = item_cell.font()
                        font.setBold(True)
                        item_cell.setFont(font)
                        amount_font = amount_cell.font()
                        amount_font.setBold(True)
                        amount_cell.setFont(amount_font)
                        
                self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate equity statement: {e}")

    def refresh_current_view(self):
        """Refresh the current view based on which button is active"""
        if not self.isVisible():
            return
            
        if hasattr(self, 'current_active_button') and self.current_active_button is not None:
            # Store current scroll position
            scrollbar = self.table.verticalScrollBar()
            current_scroll = scrollbar.value() if scrollbar else 0
            
            # Store current filter text
            current_filter = self.entity_search.text()
            
            # Refresh the view
            if self.current_active_button == self.journal_btn:
                self.show_journal_entries()
            elif self.current_active_button == self.ledger_btn:
                self.show_general_ledger()
            elif self.current_active_button == self.income_btn:
                self.show_income_statement()
            elif self.current_active_button == self.balance_btn:
                self.show_balance_sheet()
            elif self.current_active_button == self.trial_btn:
                self.show_trial_balance()
            elif self.current_active_button == self.adj_trial_btn:
                self.show_adjusted_trial_balance()
            elif self.current_active_button == self.cash_flow_btn:
                self.show_cash_flow_statement()
            elif self.current_active_button == self.equity_btn:
                self.show_statement_of_owner_equity()
            
            # Restore scroll position
            scrollbar = self.table.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(current_scroll)
            
            # Reapply filter if there was one
            if current_filter:
                self.entity_search.setText(current_filter)
                self.filter_entries()
    
    def showEvent(self, a0):
        """Called when the window is shown"""
        super().showEvent(a0)
        self.refresh_timer.start()  # Start auto-refresh
        
    def hideEvent(self, a0):
        """Called when the window is hidden"""
        super().hideEvent(a0)
        self.refresh_timer.stop()  # Stop auto-refresh
        
        # Reset all buttons to normal style
        if hasattr(self, 'current_active_button') and self.current_active_button is not None:
            self.current_active_button.setStyleSheet(self.button_style)
            self.current_active_button = None
        
        # Hide table and show instruction label
        self.table.hide()
        self.instruction_label.show()
        
        # Clear table contents
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
