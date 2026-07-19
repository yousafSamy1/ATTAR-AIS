import sqlite3

c = sqlite3.connect('database/accounting.db')
c.row_factory = sqlite3.Row

r = c.execute("SELECT SUM(balance) as total_revenue FROM accounts WHERE type = 'revenue'").fetchone()['total_revenue'] or 0
cogs = c.execute("SELECT SUM(balance) as total_cogs FROM accounts WHERE code = '5000'").fetchone()['total_cogs'] or 0
e = c.execute("SELECT SUM(balance) as total_expenses FROM accounts WHERE type = 'expense' AND code != '5000'").fetchone()['total_expenses'] or 0

print(f'Revenue: {r}, COGS: {cogs}, Expenses: {e}')
gp = r - cogs
np = gp - e
print(f'Gross Profit: {gp}, Net Profit: {np}')
