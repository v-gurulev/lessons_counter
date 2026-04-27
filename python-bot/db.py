import os
import json
import asyncio
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "bot.db")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS")


# ==================== ABSTRACT ====================

class Database:
    async def init(self):
        raise NotImplementedError

    async def get_config(self, key):
        raise NotImplementedError

    async def set_config(self, key, value):
        raise NotImplementedError

    async def find_student_by_chat(self, chat_id):
        raise NotImplementedError

    async def find_student_by_group(self, group_chat_id):
        raise NotImplementedError

    async def add_student(self, chat_id, name, group_chat_id=None):
        raise NotImplementedError

    async def update_counters(self, chat_id, field, delta):
        raise NotImplementedError

    async def update_last_lesson(self, chat_id):
        raise NotImplementedError

    async def log_transaction(self, chat_id, name, t_type, count, note):
        raise NotImplementedError

    async def get_all_students(self):
        raise NotImplementedError

    async def delete_student(self, chat_id):
        raise NotImplementedError


# ==================== SQLITE ====================

class SQLiteDB(Database):
    def __init__(self):
        import aiosqlite
        self.aiosqlite = aiosqlite

    async def init(self):
        async with self.aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT UNIQUE,
                    name TEXT,
                    group_chat_id TEXT,
                    bought INTEGER DEFAULT 0,
                    spent INTEGER DEFAULT 0,
                    last_lesson_date TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    chat_id TEXT,
                    name TEXT,
                    type TEXT,
                    count INTEGER,
                    note TEXT
                )
            """)
            await db.commit()

    async def get_config(self, key):
        async with self.aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT value FROM config WHERE key = ?", (key,)) as cur:
                row = await cur.fetchone()
                return row[0] if row else None

    async def set_config(self, key, value):
        async with self.aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
            await db.commit()

    async def find_student_by_chat(self, chat_id):
        async with self.aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT * FROM students WHERE chat_id = ?", (str(chat_id),)) as cur:
                row = await cur.fetchone()
                if row:
                    return {
                        "id": row[0], "chat_id": row[1], "name": row[2],
                        "group_chat_id": row[3], "bought": row[4] or 0,
                        "spent": row[5] or 0, "balance": (row[4] or 0) - (row[5] or 0),
                        "last_lesson_date": row[6]
                    }
                return None

    async def find_student_by_group(self, group_chat_id):
        async with self.aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT * FROM students WHERE group_chat_id = ?", (str(group_chat_id),)) as cur:
                row = await cur.fetchone()
                if row:
                    return {
                        "id": row[0], "chat_id": row[1], "name": row[2],
                        "group_chat_id": row[3], "bought": row[4] or 0,
                        "spent": row[5] or 0, "balance": (row[4] or 0) - (row[5] or 0),
                        "last_lesson_date": row[6]
                    }
                return None

    async def add_student(self, chat_id, name, group_chat_id=None):
        async with self.aiosqlite.connect(DB_PATH) as db:
            try:
                await db.execute(
                    "INSERT INTO students (chat_id, name, group_chat_id) VALUES (?, ?, ?)",
                    (str(chat_id), name, str(group_chat_id) if group_chat_id else None)
                )
                await db.commit()
                return True
            except Exception:
                return False

    async def update_counters(self, chat_id, field, delta):
        async with self.aiosqlite.connect(DB_PATH) as db:
            if field == "bought":
                await db.execute("UPDATE students SET bought = bought + ? WHERE chat_id = ?", (delta, str(chat_id)))
            else:
                await db.execute("UPDATE students SET spent = spent + ? WHERE chat_id = ?", (delta, str(chat_id)))
            await db.commit()

    async def update_last_lesson(self, chat_id):
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        async with self.aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE students SET last_lesson_date = ? WHERE chat_id = ?", (now, str(chat_id)))
            await db.commit()

    async def log_transaction(self, chat_id, name, t_type, count, note):
        now = datetime.now().isoformat()
        async with self.aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO transactions (date, chat_id, name, type, count, note) VALUES (?, ?, ?, ?, ?, ?)",
                (now, str(chat_id), name, t_type, count, note)
            )
            await db.commit()

    async def get_all_students(self):
        async with self.aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name, bought, spent, last_lesson_date FROM students") as cur:
                return await cur.fetchall()

    async def delete_student(self, chat_id):
        async with self.aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("DELETE FROM students WHERE chat_id = ?", (str(chat_id),))
            await db.commit()
            return cursor.rowcount > 0


# ==================== POSTGRESQL (Supabase) ====================

class PostgresDB(Database):
    def __init__(self):
        import asyncpg
        self.asyncpg = asyncpg
        self.pool = None
        self.dsn = os.getenv("DATABASE_URL")

    async def init(self):
        self.pool = await self.asyncpg.create_pool(self.dsn)
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    chat_id TEXT UNIQUE,
                    name TEXT,
                    group_chat_id TEXT,
                    bought INTEGER DEFAULT 0,
                    spent INTEGER DEFAULT 0,
                    last_lesson_date TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    date TEXT,
                    chat_id TEXT,
                    name TEXT,
                    type TEXT,
                    count INTEGER,
                    note TEXT
                )
            """)

    async def get_config(self, key):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM config WHERE key = $1", key)
            return row["value"] if row else None

    async def set_config(self, key, value):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO config (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2",
                key, value
            )

    async def find_student_by_chat(self, chat_id):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM students WHERE chat_id = $1", str(chat_id))
            if row:
                return {
                    "id": row["id"], "chat_id": row["chat_id"], "name": row["name"],
                    "group_chat_id": row["group_chat_id"], "bought": row["bought"] or 0,
                    "spent": row["spent"] or 0, "balance": (row["bought"] or 0) - (row["spent"] or 0),
                    "last_lesson_date": row["last_lesson_date"]
                }
            return None

    async def find_student_by_group(self, group_chat_id):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM students WHERE group_chat_id = $1", str(group_chat_id))
            if row:
                return {
                    "id": row["id"], "chat_id": row["chat_id"], "name": row["name"],
                    "group_chat_id": row["group_chat_id"], "bought": row["bought"] or 0,
                    "spent": row["spent"] or 0, "balance": (row["bought"] or 0) - (row["spent"] or 0),
                    "last_lesson_date": row["last_lesson_date"]
                }
            return None

    async def add_student(self, chat_id, name, group_chat_id=None):
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO students (chat_id, name, group_chat_id) VALUES ($1, $2, $3)",
                    str(chat_id), name, str(group_chat_id) if group_chat_id else None
                )
                return True
            except Exception:
                return False

    async def update_counters(self, chat_id, field, delta):
        async with self.pool.acquire() as conn:
            if field == "bought":
                await conn.execute("UPDATE students SET bought = bought + $1 WHERE chat_id = $2", delta, str(chat_id))
            else:
                await conn.execute("UPDATE students SET spent = spent + $1 WHERE chat_id = $2", delta, str(chat_id))

    async def update_last_lesson(self, chat_id):
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE students SET last_lesson_date = $1 WHERE chat_id = $2", now, str(chat_id))

    async def log_transaction(self, chat_id, name, t_type, count, note):
        now = datetime.now().isoformat()
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO transactions (date, chat_id, name, type, count, note) VALUES ($1, $2, $3, $4, $5, $6)",
                now, str(chat_id), name, t_type, count, note
            )

    async def get_all_students(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT name, bought, spent, last_lesson_date FROM students")
            return [(r["name"], r["bought"], r["spent"], r["last_lesson_date"]) for r in rows]

    async def delete_student(self, chat_id):
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM students WHERE chat_id = $1", str(chat_id))
            return int(result.split()[-1]) > 0


# ==================== GOOGLE SHEETS ====================

class SheetsDB(Database):
    def __init__(self):
        import gspread
        from google.oauth2.service_account import Credentials
        self.gspread = gspread
        self.Credentials = Credentials

    def _get_sheet(self):
        if CREDENTIALS_JSON:
            creds_dict = json.loads(CREDENTIALS_JSON)
        elif os.path.exists("credentials.json"):
            with open("credentials.json") as f:
                creds_dict = json.load(f)
        else:
            raise RuntimeError("Google credentials not found. Set GOOGLE_CREDENTIALS env var or create credentials.json")

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = self.Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = self.gspread.authorize(creds)
        return client.open_by_key(SHEET_ID)

    async def _ws(self, name, headers=None):
        sheet = await asyncio.to_thread(self._get_sheet)
        try:
            return await asyncio.to_thread(sheet.worksheet, name)
        except self.gspread.WorksheetNotFound:
            ws = await asyncio.to_thread(sheet.add_worksheet, name, rows=1000, cols=10)
            if headers:
                await asyncio.to_thread(ws.append_row, headers)
            return ws

    async def init(self):
        await self._ws("Config", ["key", "value"])
        await self._ws("Students", ["chat_id", "name", "group_chat_id", "bought", "spent", "last_lesson_date"])
        await self._ws("Transactions", ["id", "date", "chat_id", "name", "type", "count", "note"])

    async def get_config(self, key):
        ws = await self._ws("Config")
        records = await asyncio.to_thread(ws.get_all_records)
        for row in records:
            if str(row.get("key")) == str(key):
                return str(row.get("value"))
        return None

    async def set_config(self, key, value):
        ws = await self._ws("Config")
        records = await asyncio.to_thread(ws.get_all_records)
        for i, row in enumerate(records, start=2):
            if str(row.get("key")) == str(key):
                await asyncio.to_thread(ws.update_cell, i, 2, str(value))
                return
        await asyncio.to_thread(ws.append_row, [str(key), str(value)])

    async def find_student_by_chat(self, chat_id):
        ws = await self._ws("Students")
        records = await asyncio.to_thread(ws.get_all_records)
        for row in records:
            if str(row.get("chat_id")) == str(chat_id):
                return {
                    "id": None,
                    "chat_id": str(row.get("chat_id")),
                    "name": row.get("name"),
                    "group_chat_id": row.get("group_chat_id") or None,
                    "bought": int(row.get("bought") or 0),
                    "spent": int(row.get("spent") or 0),
                    "balance": int(row.get("bought") or 0) - int(row.get("spent") or 0),
                    "last_lesson_date": row.get("last_lesson_date") or None
                }
        return None

    async def find_student_by_group(self, group_chat_id):
        ws = await self._ws("Students")
        records = await asyncio.to_thread(ws.get_all_records)
        for row in records:
            if str(row.get("group_chat_id")) == str(group_chat_id):
                return {
                    "id": None,
                    "chat_id": str(row.get("chat_id")),
                    "name": row.get("name"),
                    "group_chat_id": row.get("group_chat_id") or None,
                    "bought": int(row.get("bought") or 0),
                    "spent": int(row.get("spent") or 0),
                    "balance": int(row.get("bought") or 0) - int(row.get("spent") or 0),
                    "last_lesson_date": row.get("last_lesson_date") or None
                }
        return None

    async def add_student(self, chat_id, name, group_chat_id=None):
        ws = await self._ws("Students")
        records = await asyncio.to_thread(ws.get_all_records)
        for row in records:
            if str(row.get("chat_id")) == str(chat_id):
                return False
        await asyncio.to_thread(ws.append_row, [
            str(chat_id), name, str(group_chat_id) if group_chat_id else "", "0", "0", ""
        ])
        return True

    async def update_counters(self, chat_id, field, delta):
        ws = await self._ws("Students")
        records = await asyncio.to_thread(ws.get_all_records)
        col_map = {"bought": 4, "spent": 5}
        for i, row in enumerate(records, start=2):
            if str(row.get("chat_id")) == str(chat_id):
                current = int(row.get(field) or 0)
                new_val = current + delta
                await asyncio.to_thread(ws.update_cell, i, col_map[field], str(new_val))
                return

    async def update_last_lesson(self, chat_id):
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        ws = await self._ws("Students")
        records = await asyncio.to_thread(ws.get_all_records)
        for i, row in enumerate(records, start=2):
            if str(row.get("chat_id")) == str(chat_id):
                await asyncio.to_thread(ws.update_cell, i, 6, now)
                return

    async def log_transaction(self, chat_id, name, t_type, count, note):
        now = datetime.now().isoformat()
        ws = await self._ws("Transactions")
        await asyncio.to_thread(ws.append_row, [
            "", now, str(chat_id), name, t_type, str(count), note
        ])

    async def get_all_students(self):
        ws = await self._ws("Students")
        records = await asyncio.to_thread(ws.get_all_records)
        result = []
        for row in records:
            result.append((
                row.get("name"),
                int(row.get("bought") or 0),
                int(row.get("spent") or 0),
                row.get("last_lesson_date") or None
            ))
        return result

    async def delete_student(self, chat_id):
        ws = await self._ws("Students")
        records = await asyncio.to_thread(ws.get_all_records)
        for i, row in enumerate(records, start=2):
            if str(row.get("chat_id")) == str(chat_id):
                await asyncio.to_thread(ws.delete_rows, i)
                return True
        return False


# ==================== FACTORY ====================

def get_db():
    if os.getenv("DATABASE_URL"):
        return PostgresDB()
    if SHEET_ID:
        return SheetsDB()
    return SQLiteDB()
