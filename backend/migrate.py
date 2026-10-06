import sqlite3
c = sqlite3.connect("it_assets.db")
# Add missing columns if not exist
for sql in [
    "ALTER TABLE transfer_records ADD COLUMN new_user VARCHAR(100)",
    "ALTER TABLE transfer_records ADD COLUMN new_dept VARCHAR(100)",
]:
    try:
        c.execute(sql)
    except Exception as e:
        print("skip:", e)
c.commit()
print("Migration done")
c.close()
