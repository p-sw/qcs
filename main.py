from flask import Flask, render_template, request
from random import randint
import sqlite3
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

DATABASE_NAME = "db.sqlite3"

class Database:
    def __init__(self, name):
        self.db = sqlite3.connect(name)
        cursor = self.db.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS items (key TEXT, data TEXT, encrypted BOOLEAN, created_at INTEGER)")
        self.db.commit()
    
    def __del__(self):
        self.db.close()
    
    def execute(self, sql, params=()):
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        self.db.commit()
        return cursor

    def fetchall(self, sql, params=()):
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

class Item:
    def __init__(self, data: str = None, encrypted: bool = None, key: str = None):
        self.data = data
        self.encrypted = encrypted
        self.key = key
        self.created_at = time.time()
        self.control = self._Control(self)
    
    def to_json(self):
        return {
            'data': self.data,
            'encrypted': self.encrypted,
            'key': self.key,
            'created_at': self.created_at
        }

    class _Control:
        def __init__(self, obj):
            self.db = Database(DATABASE_NAME)
            self.obj = obj
        
        def exists(self):
            return self.db.execute('SELECT EXISTS(SELECT * FROM items WHERE key = ?)', (self.obj.key,)).fetchone()[0] == 1

        def save(self):
            if not self.exists():
                self.db.execute('INSERT INTO items (key, data, encrypted, created_at) VALUES (?, ?, ?, ?)', (self.obj.key, self.obj.data, self.obj.encrypted, self.obj.created_at))
                return self.obj
            else:
                return False

        def get(self):
            if self.exists():
                return Item(*self.db.execute('SELECT data, encrypted FROM items WHERE key = ?', (self.obj.key,)).fetchone(), key=self.obj.key)
            else:
                return None


def clear_db():
    print("Clearing..")
    db = Database(DATABASE_NAME)
    length = len(db.fetchall("SELECT * FROM items WHERE created_at < ?", (time.time() - 60,)))
    db.execute('DELETE FROM items WHERE created_at < ?', (time.time() - 60,))
    print(f"Cleared {length} items.")


scheduler = BackgroundScheduler()
scheduler.add_job(func=clear_db, trigger="interval", seconds=60)
scheduler.start()

app = Flask(__name__)

atexit.register(scheduler.shutdown)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/putclip', methods=['POST'])
def put_copy():
    data = str(request.json['putdata'])
    encrypted = request.json['encrypt']

    key_decided = False
    while not key_decided:
        key = randint(0, 999999)
        if Item(key=key).control.exists():
            continue
        key_decided = True

    result = Item(key='0'*(6-len(str(key)))+str(key), data=data, encrypted=encrypted).control.save()
    return result.to_json()

@app.route('/api/getclip', methods=['POST'])
def get_copy():
    key = str(request.json['key'])
    result = Item(key=key).control.get()
    if not result:
        return {'error': "True"}
    return result.to_json()

if __name__ == "__main__":
    app.run()
