import sqlite3

class Database:
    def __init__(self, db_name="cashflow.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Tabel Users
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Tabel Transactions
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                type TEXT NOT NULL, -- 'in' untuk pemasukan, 'out' untuk pengeluaran
                amount REAL NOT NULL,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users (email)
            )
        ''')
        self.conn.commit()

        # Otomatis konversi kolom fullname ke name jika memakai database lama
        self.cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'fullname' in columns and 'name' not in columns:
            self.cursor.execute("ALTER TABLE users RENAME COLUMN fullname TO name")
            self.conn.commit()

    def register_user(self, name, email, password):
        try:
            self.cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            self.conn.commit()
            return True, "Pendaftaran berhasil!"
        except sqlite3.IntegrityError:
            return False, "Email sudah terdaftar!"
        except Exception as e:
            return False, str(e)

    def login_user(self, email, password):
        self.cursor.execute(
            "SELECT name FROM users WHERE email = ? AND password = ?",
            (email, password)
        )
        user = self.cursor.fetchone()
        if user:
            return True, user[0]
        return False, "Email atau password salah!"

    def get_first_user(self):
        self.cursor.execute("SELECT name, email FROM users ORDER BY id LIMIT 1")
        return self.cursor.fetchone()

    def add_transaction(self, email, tx_type, amount, description="", transaction_date=None):
        try:
            if transaction_date:
                self.cursor.execute(
                    "INSERT INTO transactions "
                    "(user_email, type, amount, description, date) VALUES (?, ?, ?, ?, ?)",
                    (email, tx_type, amount, description, transaction_date),
                )
            else:
                self.cursor.execute(
                    "INSERT INTO transactions (user_email, type, amount, description) VALUES (?, ?, ?, ?)",
                    (email, tx_type, amount, description),
                )
            self.conn.commit()
            return True, "Transaksi berhasil disimpan!"
        except Exception as e:
            return False, str(e)

    def get_summary(self, email=None, year=None, month=None):
        if not email:
            return 0.0, 0.0, 0.0

        if year is not None and month is not None:
            total_in, total_out = self.get_monthly_summary(email, year, month)
            return total_in - total_out, total_in, total_out

        # Hitung total pemasukan
        self.cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_email = ? AND type = 'in'", (email,)
        )
        total_in = self.cursor.fetchone()[0] or 0.0

        # Hitung total pengeluaran
        self.cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_email = ? AND type = 'out'", (email,)
        )
        total_out = self.cursor.fetchone()[0] or 0.0

        balance = total_in - total_out
        return balance, total_in, total_out

    def get_monthly_summary(self, email, year, month):
        if not email:
            return 0.0, 0.0

        month_key = f"{year:04d}-{month:02d}%"
        self.cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions "
            "WHERE user_email = ? AND type = 'in' AND date LIKE ?",
            (email, month_key),
        )
        total_in = self.cursor.fetchone()[0]

        self.cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions "
            "WHERE user_email = ? AND type = 'out' AND date LIKE ?",
            (email, month_key),
        )
        total_out = self.cursor.fetchone()[0]
        return total_in, total_out

    def get_transactions(self, email, year, month):
        if not email:
            return []

        month_key = f"{year:04d}-{month:02d}%"
        self.cursor.execute(
            "SELECT type, description, amount, date FROM transactions "
            "WHERE user_email = ? AND date LIKE ? ORDER BY date DESC, id DESC",
            (email, month_key),
        )
        return [
            {
                "type": "income" if row[0] == "in" else "expense",
                "desc": row[1] or "Tanpa keterangan",
                "amount": row[2],
                "date": row[3][:10],
            }
            for row in self.cursor.fetchall()
        ]

    def close(self):
        self.conn.close()