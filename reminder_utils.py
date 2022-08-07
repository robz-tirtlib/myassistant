import sqlite3


def add_to_db(user_id, date_time, reminder_text) -> None:
    """Adds reminder from user to DB"""

    db = sqlite3.connect('myassistant.db')
    c = db.cursor()

    query = f"""
    INSERT INTO reminders
    VALUES
        ({user_id}, datetime('{date_time}'), "{reminder_text}");
    """
    c.execute(query)

    db.commit()

    db.close()


def get_reminders(bot):
    """Check if there is someone to remind and remind if there is"""

    db = sqlite3.connect('myassistant.db')
    c = db.cursor()

    query_select = """
SELECT user_id, reminder_text
FROM reminders
WHERE DATE(reminder_date) <= DATE('now')
      AND strftime('%H %M', datetime(reminder_date)) <= strftime('%H %M', datetime('now', 'localtime'));
"""

    c.execute(query_select)

    reminders = c.fetchall()

    query_delete = """
DELETE FROM reminders
WHERE DATE(reminder_date) <= DATE('now')
      AND strftime('%H %M', datetime(reminder_date)) <= strftime('%H %M', datetime('now', 'localtime'));
"""
    c.execute(query_delete)

    db.commit()
    db.close()

    remind_users(reminders, bot)


def remind_users(reminders, bot):
    """Send reminder messages to users"""

    for reminder in reminders:
        user_id, reminder_text = reminder
        bot.send_message(user_id, reminder_text)
