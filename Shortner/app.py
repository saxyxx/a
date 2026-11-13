from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import string
import random
from datetime import datetime

app = Flask(__name__)

# ডাটাবেস কানেকশন তৈরি
def get_db_connection():
    conn = sqlite3.connect('shortener.db')
    conn.row_factory = sqlite3.Row
    return conn

# ডাটাবেস টেবিল তৈরি
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            views INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# র‍্যান্ডম শর্ট কোড জেনারেট করার ফাংশন
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM links WHERE short_code = ?', (code,)).fetchone()
        conn.close()
        if not existing:
            return code

# হোম পেজ (লিংক ম্যানেজমেন্ট)
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    if request.method == 'POST':
        original_url = request.form['original_url']
        # ইউজার http:// বা https:// না দিলে অটো যোগ হবে
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'https://' + original_url
            
        short_code = generate_short_code()
        
        conn.execute('INSERT INTO links (original_url, short_code) VALUES (?, ?)', 
                     (original_url, short_code))
        conn.commit()
        return redirect(url_for('index'))

    # সব লিংক নিয়ে আসা (নতুনগুলো আগে)
    links = conn.execute('SELECT * FROM links ORDER BY id DESC').fetchall()
    conn.close()
    
    # বর্তমান ডোমেইন নেওয়া শর্ট লিংক দেখানোর জন্য
    host_url = request.host_url 
    return render_template('index.html', links=links, host_url=host_url)

# শর্ট লিংকে ক্লিক করলে রিডাইরেক্ট হবে এবং ভিউ কাউন্ট বাড়বে
@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = get_db_connection()
    link = conn.execute('SELECT * FROM links WHERE short_code = ?', (short_code,)).fetchone()
    
    if link:
        # ভিউ কাউন্ট ১ বাড়ানো
        conn.execute('UPDATE links SET views = views + 1 WHERE short_code = ?', (short_code,))
        conn.commit()
        conn.close()
        return redirect(link['original_url'])
    else:
        conn.close()
        return "লিংকটি খুঁজে পাওয়া যায়নি!", 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)