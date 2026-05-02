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
    QTimer         # Timer class for periodic events
)

# Database Configuration
from database.db_config import DatabaseConnection  # Custom database connection handler

# Python Standard Libraries
from datetime import (
    datetime,      # Basic date and time types
    timedelta      # Duration/time difference calculations
)

class FinancialReportsModule(QWidget):
    """Financial Reports Module - Displays various types of financial reports"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Setup auto-refresh timer with faster refresh rate
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_current_view)
        self.refresh_timer.start(500)  # Refresh every 0.5 seconds for more responsive updates
        
    def init_ui(self):
        """Initialize the graphical user interface"""
        layout = QVBoxLayout(self)
        
        # Create button layout at the top
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)  # Space between buttons
        btn_layout.setContentsMargins(10, 10, 10, 10)  # Margins around button group
        
        # Create buttons for each report type
        self.journal_btn = QPushButton("Journal Entries")
        self.ledger_btn = QPushButton("General Ledger")
        self.income_btn = QPushButton("Income Statement")
        self.balance_btn = QPushButton("Balance Sheet")
        self.trial_btn = QPushButton("Trial Balance")
        
        # Normal button style (inactive)
        self.button_style = """
            QPushButton {
                background-color: #F0E8DC;
                color: #6B4C2A;
                border: 1px solid #E8DDD0;
                padding: 8px 15px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                min-width: 130px;
                margin: 0 5px;
            }
            QPushButton:hover {
                background-color: #E8DDD0;
                color: #1C1008;
            }
            QPushButton:pressed { background-color: #C8760A; color: white; }
        """
        
        # Active button style (currently selected)
        self.active_button_style = """
            QPushButton {
                background-color: #C8760A;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                min-width: 130px;
                margin: 0 5px;
                border-bottom: 3px solid #E8950A;
            }
        """
        
        # Apply basic style to all buttons
        for btn in [self.journal_btn, self.ledger_btn, self.income_btn, 
                   self.balance_btn, self.trial_btn]:
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
        self.instruction_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 16px;
                padding: 20px;
                qproperty-alignment: AlignCenter;
            }
        """)
        
        # Create table for displaying data
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only
        
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

    def _handle_button_click(self, clicked_button):
        """Handle button clicks and update active button state"""
        # Reset previous active button to normal style
        if hasattr(self, 'current_active_button') and self.current_active_button is not None:
            self.current_active_button.setStyleSheet(self.button_style)
        
        # Apply active style to clicked button
        clicked_button.setStyleSheet(self.active_button_style)
        self.current_active_button = clicked_button
        
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

    def show_journal_entries(self):
        """Show journal entries"""
        self.table.clear()
        self.table.setColumnCount(7)  # Added one more column for supplier/customer
        # Set column headers
        self.table.setHorizontalHeaderLabels([
            "Date",         # Date
            "Reference",    # Reference number
            "Account",      # Account
            "Description",  # Description
            "Debit",        # Debit
            "Credit",       # Credit
            "Entity"        # Supplier/Customer
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
                    debit_item = QTableWidgetItem(f"${entry['debit']:.2f}" if entry['debit'] > 0 else "")
                    debit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 4, debit_item)
                    
                    # Credit
                    credit_item = QTableWidgetItem(f"${entry['credit']:.2f}" if entry['credit'] > 0 else "")
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
            "Account",      # Account
            "Date",         # Date
            "Reference",    # Reference number
            "Description",  # Description
            "Debit",        # Debit
            "Credit",       # Credit
            "Balance",      # Balance
            "Entity"       # Supplier/Customer
        ])
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        a.name as account_name,
                        gl.date,
                        je.reference_no,
                        gl.description,
                        gl.debit,
                        gl.credit,
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
                    ORDER BY a.code, gl.date DESC, gl.id DESC
                """)
                entries = cursor.fetchall()
                
                self.table.setRowCount(len(entries))
                for row, entry in enumerate(entries):
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
                    debit_item = QTableWidgetItem(f"${entry['debit']:.2f}" if entry['debit'] > 0 else "")
                    debit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 4, debit_item)
                    
                    # Credit
                    credit_item = QTableWidgetItem(f"${entry['credit']:.2f}" if entry['credit'] > 0 else "")
                    credit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, 5, credit_item)
                    
                    # Balance
                    balance_item = QTableWidgetItem(f"${entry['account_balance']:.2f}")
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
                    amount_cell = QTableWidgetItem(f"${amount:.2f}")
                    amount_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.table.setItem(row, 0, item_cell)
                    self.table.setItem(row, 1, amount_cell)
                    
                    # Style the rows
                    if item in ["Gross Profit", "Net Profit"]:
                        for col in range(2):
                            cell = self.table.item(row, col)
                            if cell:
                                cell.setBackground(Qt.GlobalColor.lightGray)
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
                    amount_cell = QTableWidgetItem(f"${amount:.2f}" if amount != "" else "")
                    amount_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.table.setItem(row, 0, item_cell)
                    self.table.setItem(row, 1, amount_cell)
                    
                    # Style the rows
                    if not item.startswith("  ") and item != "":  # Headers and totals
                        for col in range(2):
                            cell = self.table.item(row, col)
                            if cell:
                                cell.setBackground(Qt.GlobalColor.lightGray)
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
            "Account",  # Account
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
                    debit_cell = QTableWidgetItem(f"${account['debit_balance']:.2f}" if account['debit_balance'] > 0 else "")
                    debit_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    credit_cell = QTableWidgetItem(f"${account['credit_balance']:.2f}" if account['credit_balance'] > 0 else "")
                    credit_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    
                    self.table.setItem(row, 0, name_cell)
                    self.table.setItem(row, 1, debit_cell)
                    self.table.setItem(row, 2, credit_cell)
                
                # Add total row
                total_row = len(accounts)
                total_label = QTableWidgetItem("Total")
                total_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                total_debit_cell = QTableWidgetItem(f"${total_debit:.2f}")
                total_debit_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                total_credit_cell = QTableWidgetItem(f"${total_credit:.2f}")
                total_credit_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                
                self.table.setItem(total_row, 0, total_label)
                self.table.setItem(total_row, 1, total_debit_cell)
                self.table.setItem(total_row, 2, total_credit_cell)
                
                # Style the total row
                for col in range(3):
                    cell = self.table.item(total_row, col)
                    if cell:
                        cell.setBackground(Qt.GlobalColor.lightGray)
                        font = cell.font()
                        font.setBold(True)
                        cell.setFont(font)
                
                # Style the table
                header = self.table.horizontalHeader()
                if header:
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating trial balance: {str(e)}")

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
