import sqlite3


db = sqlite3.connect('myassistant.db')
c = db.cursor()

# c.execute("""
# CREATE TABLE reminders (
#     user_id INT,
#     reminder_date text DEFAULT (datetime('now','localtime'))
# );
# """)

# c.execute("""
# INSERT INTO reminders
# VALUES
#     (403198902, datetime('2022-08-05 15:11:00'), "lalala");
# """)
db.commit()

c.execute("""SELECT * FROM reminders""")
print(c.fetchall())

db.close()
