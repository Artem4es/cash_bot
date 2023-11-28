import sqlite3

class BotDB:

    def __init__(self, db_file):
        """Создание соединения с БД"""
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('PRAGMA foreign_keys = ON')
        self.conn.commit()
        print('Соединился с базой, едем дальше')

    def user_exists(self, user_id):
        """Проверяем есть ли юзер в БД"""
        result = self.cursor.execute('SELECT username FROM users WHERE "user_id" = ?',(user_id,))
        return bool(len(result.fetchall()))
    
    def get_user_data(self, user_id):
        result = self.cursor.execute('SELECT user_id, username, pays_since FROM users WHERE "user_id" = ?', (user_id,))
        return result.fetchone()

    def get_users(self):
        """Вытаскиваем все user_id пользователей из БД"""
        result = self.cursor.execute('SELECT "user_id" FROM users ORDER BY "join_date"')    
        return result.fetchall()

    def get_usernames(self):
        """Вытаскиваем все username пользователей из БД"""
        result = self.cursor.execute('SELECT "username" FROM users')    
        return result.fetchall()
    def get_start_date(self, user_id):
        """Выясняем с какой даты считать должок"""
        result = self.cursor.execute('SELECT "join_date" FROM users WHERE "user_id" = ?', (user_id))    
        return result.fetchall() 

    def pays_from_start(self, user_id):
        """1 - считать сумму с начала, 0 - с даты вступления"""
        result = self.cursor.execute('SELECT "pays_from_start" FROM users WHERE "user_id" = ?', (user_id,))
        # result = self.cursor.execute('SELECT "pays_from_start" FROM users WHERE "user_id" = 291198651')
        
        return True if result.fetchone()[0] == 1 else False



    def add_user(self, user_id, username):
        """Добавляем пользователя в БД"""
        self.cursor.execute('INSERT INTO users ("user_id", "username") VALUES(?, ?);',(user_id, username))
        return self.conn.commit()

    def add_sum(self, user_id, amount):
        """Добавляем суммуи user_id в таблицу payments"""
        try:
            self.cursor.execute('INSERT INTO payments ("user_id", "amount") VALUES(?, ?);',(user_id, amount))
        except Exception as error:
            # logger.error(f'{error} Не удалось записать данные о платеже')
            raise error('Не удалось записать данные о платеже')
        return self.conn.commit()        


    def total(self, user_id=None, from_date=None):
        """Сколько всего заплатил один пользователь или все вместе"""
        if user_id is not None:
            self.cursor.execute('SELECT SUM(amount) FROM payments WHERE "user_id" = ?',(user_id,))
            sum = self.cursor.fetchone()[0]
            if sum is None:
                sum = 0
        else:        
            self.cursor.execute('SELECT SUM(amount) FROM payments')
            sum = self.cursor.fetchone()[0]
            if sum is None:
                sum = 0        
        return sum

    def reset_sum(self):
        """Обнуляем сумму у всех юзеров"""
        self.cursor.execute('UPDATE payments SET "amount"=0')  
        return self.conn.commit()  

    def set_complain(self,user_id):
        """Устанавливаем статус жалобы для пользователя"""
        self.cursor.execute('UPDATE users SET "is_complained"=1 WHERE "user_id"=?', (user_id,))
        return self.conn.commit()
    def set_payment_from_status(self,user_id):
        """Ставим 0 - юзер хочет платить с момента вступления в чат"""
        self.cursor.execute('UPDATE users SET "pays_from_start"=0 WHERE "user_id"=?', (user_id,))
        return self.conn.commit()        

    def remove_complain(self,user_id):
        """Удаляем статус жалобы для пользователя"""
        self.cursor.execute('UPDATE users SET "is_complained"=0 WHERE "user_id"=?', (user_id,))
        return self.conn.commit()  
    def public_message_status(self,user_id):
        """Узнаём статус публичного сообщения для пользователя"""
        result = self.cursor.execute('SELECT "public_message" FROM "users" WHERE "user_id"=?', (user_id,))
        return True if result.fetchone()[0] == 1 else False 
    def delete_user(self, username):
        """Удаляем пользователя из БД"""
        self.cursor.execute('DELETE FROM "users" WHERE "username"=?',(username,))
        return self.conn.commit()

    def set_public(self,user_id):
        """Устанавливаем что пользователь хочет написать публичное сообщение"""
        self.cursor.execute('UPDATE users SET "public_message"=1 WHERE "user_id"=?', (user_id,))
        return self.conn.commit()    

    def reset_public(self,user_id):
        """Удаляем что пользователь хочет написать публичное сообщение"""
        self.cursor.execute('UPDATE users SET "public_message"=0 WHERE "user_id"=?', (user_id,))
        return self.conn.commit() 

    def get_all_payments(self):
        """Все платежи в базе на текущий момент"""
        result = self.cursor.execute('SELECT users.username, payments.amount, payments.timestamp FROM "users" JOIN "payments" ON users.user_id=payments.user_id')
        return result.fetchall() 

    def get_period_payments(self, since, until, user_id=None):
        if user_id is None:
            result = self.cursor.execute('SELECT SUM(amount) FROM payments WHERE timestamp BETWEEN ? AND ?',(since, until))
            result = result.fetchall()[0][0]
            return result if result else 0
        result = self.cursor.execute('SELECT SUM(amount) FROM payments WHERE user_id=? AND timestamp BETWEEN ? AND ?',(user_id, since, until))
        result = result.fetchall()[0][0]
        return result if result else 0  


    def set_pays_since(self, user_id, pays_since=None):
        """Устанавливаем с какой даты платит юзер"""
        if pays_since is None: 
            result = self.cursor.execute('SELECT MIN("pays_since") FROM users')
            pays_since = result.fetchone()[0]
        self.cursor.execute('UPDATE users SET "pays_since"=? WHERE "user_id"=?', (pays_since, user_id)) # +
        return self.conn.commit()

    def get_pay_periods(self):
        result = self.cursor.execute('SELECT user_id, username, pays_since FROM users')
        return result.fetchall()
    def get_user_qty(self, until):
        result = self.cursor.execute('SELECT COUNT(user_id) FROM users WHERE "pays_since"<?',(until,))
        return result.fetchone()[0]

    def set_user_owes(self, user_id=None, user_owes=0):
        if user_id is None:
            self.cursor.execute('UPDATE "users" SET "user_owes"=0')
            return self.conn.commit()
        self.cursor.execute('UPDATE "users" SET "user_owes"=? WHERE "user_id"=?', (user_owes, user_id)) 
        return self.conn.commit()
    def get_user_owes(self, user_id):
        result = self.cursor.execute('SELECT "user_owes" FROM "users" WHERE "user_id"=?', (user_id,))
        return result.fetchone()[0]    



    