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
#     (9999, datetime('now'));
# """)

# c.execute("""
# INSERT INTO reminders
# VALUES
#     (403198902, datetime('2022-07-29 15:11:00'));
# """)

db.commit()

c.execute("""
SELECT user_id, strftime('%H %M', datetime(reminder_date))
FROM reminders
WHERE DATE(reminder_date) <= DATE('now')
      AND strftime('%H %M', datetime(reminder_date)) <= strftime('%H %M', datetime('now', 'localtime'));
""")
# c.execute("""SELECT * FROM reminders""")
print(c.fetchall())

db.close()
