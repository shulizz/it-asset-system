import sqlite3
c = sqlite3.connect("it_assets.db")
# Check how many rows
n = c.execute("SELECT COUNT(*) FROM wechat_accounts").fetchone()[0]
print("Total rows:", n)
# Check distinct wx_account
n2 = c.execute("SELECT COUNT(*) FROM wechat_accounts WHERE wx_account IS NOT NULL AND wx_account != ''").fetchone()[0]
print("Rows with wx_account:", n2)
# Delete all rows where all main fields are empty
c.execute("DELETE FROM wechat_accounts WHERE (wx_account IS NULL OR wx_account = '') AND (wx_password IS NULL OR wx_password = '') AND (real_name IS NULL OR real_name = '') AND (user_name IS NULL OR user_name = '')")
print("Deleted:", c.total_changes)
c.commit()
c.close()
