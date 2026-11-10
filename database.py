import os
import sqlite3
import re
from datetime import datetime


def update_html_font_sizes(html_text, base_size=12, example_size=12):
    if not html_text:
        return ""

    pattern_raw = re.compile(r'\[([^\]\n<]+)\]')
    span_template = f'<span style="background-color: #1e293b; font-size: {example_size}pt; color: #e2e8f0; border-radius: 4px; padding: 2px 5px;"> \\1 </span>'

    # If it is HTML
    if "<html" in html_text.lower() or "<body" in html_text.lower():
        # 1. Update block spans with background-color: #1e293b
        def repl_block(m):
            style = m.group(1)
            style = re.sub(r'font-size:\s*[^;]+;', f'font-size: {example_size}pt;', style)
            if 'font-size' not in style:
                style += f' font-size: {example_size}pt;'
            return f'<span style="{style}">'

        res = re.sub(r'<span style="([^"]*1e293b[^"]*)">', repl_block, html_text)

        # 2. Update normal spans
        def repl_normal(m):
            style = m.group(1)
            if '1e293b' in style:
                return m.group(0)
            style = re.sub(r'font-size:\s*[^;]+;', f'font-size: {base_size}pt;', style)
            return f'<span style="{style}">'

        res = re.sub(r'<span style="([^"]*)">', repl_normal, res)

        # 3. Update body font-size if present
        res = re.sub(r'(<body[^>]*font-size:)\s*[^;]+;', f'\\1{base_size}pt;', res)

        # 4. Any raw brackets
        res = pattern_raw.sub(span_template, res)
        return res
    else:
        # Plain text
        lines = html_text.split("\n")
        out = [f'<div style="color: #e4e4e7; font-size: {base_size}pt; line-height: 1.7; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;">']
        for line in lines:
            if not line.strip():
                out.append("<div style='height: 10px;'></div>")
                continue
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            transformed = pattern_raw.sub(span_template, escaped)
            out.append(f"<div style='margin-bottom: 4px;'>{transformed}</div>")
        out.append("</div>")
        return "".join(out)


class DiaryDB:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "diary.db")
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Default categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            defaults = ["Мысли", "Личное", "Работа", "Идеи", "Планы"]
            for d in defaults:
                cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (d,))

        # Entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                duration_seconds INTEGER DEFAULT 0,
                word_count INTEGER DEFAULT 0,
                char_count INTEGER DEFAULT 0
            )
        """)

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('base_font_size', '13')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('example_font_size', '12')")

        conn.commit()
        conn.close()

    def get_setting(self, key, default=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        row = cursor.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else default

    def set_setting(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()
        conn.close()

    def update_all_entries_font_sizes(self, base_size, example_size):
        conn = self.get_connection()
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id, content FROM entries").fetchall()
        for r in rows:
            updated = update_html_font_sizes(r["content"], base_size, example_size)
            cursor.execute("UPDATE entries SET content = ? WHERE id = ?", (updated, r["id"]))
        conn.commit()
        conn.close()

    def get_categories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT c.name, COUNT(e.id) as count
            FROM categories c
            LEFT JOIN entries e ON e.topic = c.name
            GROUP BY c.name
            ORDER BY c.name ASC
        """).fetchall()
        
        extra = cursor.execute("""
            SELECT DISTINCT topic FROM entries
            WHERE topic NOT IN (SELECT name FROM categories)
        """).fetchall()
        for ex in extra:
            cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (ex["topic"],))
        conn.commit()

        if extra:
            rows = cursor.execute("""
                SELECT c.name, COUNT(e.id) as count
                FROM categories c
                LEFT JOIN entries e ON e.topic = c.name
                GROUP BY c.name
                ORDER BY c.name ASC
            """).fetchall()

        cats = [{"name": r["name"], "count": r["count"]} for r in rows]
        conn.close()
        return cats

    def add_category(self, name):
        name = name.strip()
        if not name:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        conn.close()
        return success

    def rename_category(self, old_name, new_name):
        old_name = old_name.strip()
        new_name = new_name.strip()
        if not old_name or not new_name or old_name == new_name:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE categories SET name = ? WHERE name = ?", (new_name, old_name))
            cursor.execute("UPDATE entries SET topic = ? WHERE topic = ?", (new_name, old_name))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        conn.close()
        return success

    def delete_category(self, name):
        name = name.strip()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE name = ?", (name,))
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES ('Общее')")
        cursor.execute("UPDATE entries SET topic = 'Общее' WHERE topic = ?", (name,))
        conn.commit()
        conn.close()

    def get_entries(self, topic=None, date=None, search=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        sql = """
            SELECT id, title, topic, content, date, created_at, duration_seconds, word_count, char_count
            FROM entries
            WHERE 1=1
        """
        params = []
        if topic and topic.strip() and topic.strip() != "Все темы":
            sql += " AND topic = ?"
            params.append(topic.strip())
        if date and date.strip() and date.strip() != "Все дни":
            sql += " AND date = ?"
            params.append(date.strip())
        if search and search.strip():
            sql += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term])

        sql += " ORDER BY id DESC"
        rows = cursor.execute(sql, params).fetchall()
        entries = [dict(r) for r in rows]
        conn.close()
        return entries

    def get_entry_by_id(self, entry_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT id, title, topic, content, date, created_at, duration_seconds, word_count, char_count FROM entries WHERE id = ?",
            (entry_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_dates(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT date, COUNT(*) as count
            FROM entries
            GROUP BY date
            ORDER BY date DESC
        """).fetchall()
        conn.close()
        return [{"date": r["date"], "count": r["count"]} for r in rows]

    def get_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        row = cursor.execute("""
            SELECT
                COUNT(*) as total_entries,
                COALESCE(SUM(duration_seconds), 0) as total_duration,
                COALESCE(SUM(word_count), 0) as total_words
            FROM entries
        """).fetchone()
        conn.close()
        return {
            "total_entries": row["total_entries"],
            "total_duration": row["total_duration"],
            "total_words": row["total_words"]
        }

    def add_entry(self, title, topic, content, duration_seconds):
        title = title.strip() or "Запись без названия"
        topic = topic.strip() or "Общее"
        content = content.strip()
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        created_at_str = now.strftime("%Y-%m-%d %H:%M")
        
        # Calculate clean text word and char counts
        clean_text = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<style[^>]*>.*?</style>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        words = len(clean_text.split()) if clean_text else 0
        chars = len(clean_text)

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (topic,))
        cursor.execute("""
            INSERT INTO entries (title, topic, content, date, created_at, duration_seconds, word_count, char_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, topic, content, date_str, created_at_str, duration_seconds, words, chars))
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return entry_id

    def update_entry(self, entry_id, title, topic, content, added_duration_seconds):
        title = title.strip() or "Запись без названия"
        topic = topic.strip() or "Общее"
        content = content.strip()
        
        clean_text = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<style[^>]*>.*?</style>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        words = len(clean_text.split()) if clean_text else 0
        chars = len(clean_text)

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (topic,))
        cursor.execute("SELECT duration_seconds FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        current_duration = row["duration_seconds"] if row else 0
        total_duration = current_duration + added_duration_seconds

        cursor.execute("""
            UPDATE entries
            SET title = ?, topic = ?, content = ?, duration_seconds = ?, word_count = ?, char_count = ?
            WHERE id = ?
        """, (title, topic, content, total_duration, words, chars, entry_id))
        conn.commit()
        conn.close()

    def delete_entry(self, entry_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()
