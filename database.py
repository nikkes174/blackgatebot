import datetime
import sqlite3



con = sqlite3.connect('tren_table.db')
cur = con.cursor()

tables = '''
CREATE TABLE IF NOT EXISTS payments_table (
    user_id INTEGER PRIMARY KEY,
    end_payment_date TEXT NOT NULL
);    

CREATE TABLE IF NOT EXISTS date_tranning (
    user_id INTEGER PRIMARY KEY,
    end_tranning_date TEXT NOT NULL
);
'''
cur.executescript(tables)


# Функция для добавления или обновления информации о платеже
def add_payment(user_id):
    end_payment_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')

    cur.execute('''
    INSERT INTO payments_table (user_id, end_payment_date)
    VALUES (?, ?)
    ON CONFLICT (user_id) DO UPDATE SET end_payment_date = ?
    ''', (user_id, end_payment_date, end_payment_date))

    con.commit()


# Функция для проверки, активен ли платеж
def check_payment(user_id):
    cur.execute('''
    SELECT end_payment_date 
    FROM payments_table
    WHERE user_id = ?''', (user_id,))

    result = cur.fetchone()
    if result:
        try:
            end_payment_date = datetime.datetime.strptime(result[0], '%Y-%m-%d')
            return end_payment_date > datetime.datetime.now()
        except ValueError:
            return False
    return False


# Функция для добавления или обновления даты тренировки
def add_date_tranning(user_id):
    end_tranning_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')

    cur.execute('''
    INSERT INTO date_tranning (user_id, end_tranning_date)
    VALUES (?, ?)
    ON CONFLICT (user_id) DO UPDATE SET end_tranning_date = ?
    ''', (user_id, end_tranning_date, end_tranning_date))

    con.commit()


# Функция для проверки, прошла ли тренировка более 30 дней назад
def check_date_tranning(user_id):
    cur.execute('''
    SELECT end_tranning_date 
    FROM date_tranning
    WHERE user_id = ?''', (user_id,))

    result = cur.fetchone()
    if result:
        try:
            end_tranning_date = datetime.datetime.strptime(result[0], '%Y-%m-%d')
            now = datetime.datetime.now()
            if (now - end_tranning_date).days < 30:
                return False
        except ValueError:
            return False
    return True


# Закрыть соединение в конце работы с базой данных
def close_db():
    con.close()

