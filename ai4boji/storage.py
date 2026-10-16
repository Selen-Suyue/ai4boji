"""Transactional records, explicit revisions, and permanent memory deletion."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class Store:
    def __init__(self, directory):
        self.directory = Path(directory).expanduser().resolve()
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.directory / "ai4boji.sqlite3"
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS entries (
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, date TEXT NOT NULL,
                    payload TEXT NOT NULL, source TEXT NOT NULL,
                    revision INTEGER NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS revisions (
                    id TEXT NOT NULL, revision INTEGER NOT NULL, snapshot TEXT NOT NULL,
                    PRIMARY KEY (id, revision));
                CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
                INSERT OR IGNORE INTO meta VALUES ('schema_version', '1');
            ''')
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA secure_delete=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def decode(row):
        if row is None:
            return None
        item = dict(row)
        item['payload'] = json.loads(item['payload'])
        return item

    def get(self, key):
        with self.connect() as db:
            return self.decode(db.execute("SELECT * FROM entries WHERE id=?", (key,)).fetchone())

    def list(self, kind=None):
        with self.connect() as db:
            if kind:
                rows = db.execute("SELECT * FROM entries WHERE kind=? ORDER BY date,id", (kind,))
            else:
                rows = db.execute("SELECT * FROM entries ORDER BY date,id")
            return [self.decode(row) for row in rows]

    def put(self, key, kind, day, payload, source='user', expected_revision=None):
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = self.decode(db.execute('SELECT * FROM entries WHERE id=?', (key,)).fetchone())
            if old and old['kind'] != kind:
                raise ValueError('ID 已被其他记录占用 / ID belongs to another record type')
            if old and old['payload'] == payload and old['source'] == source and old['date'] == day:
                return old
            if expected_revision is not None and expected_revision != (old['revision'] if old else 0):
                raise ValueError('记录已更新，请重新读取 / Record changed; reload before editing')
            revision = old['revision'] + 1 if old else 1
            if old:
                db.execute('INSERT INTO revisions VALUES (?,?,?)',
                           (key, old['revision'], json.dumps(old, ensure_ascii=False)))
            db.execute('INSERT OR REPLACE INTO entries VALUES (?,?,?,?,?,?,?)',
                       (key, kind, day, body, source, revision, datetime.now(timezone.utc).isoformat()))
        return self.get(key)

    def history(self, key):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute(
                'SELECT snapshot FROM revisions WHERE id=? ORDER BY revision', (key,))]

    def forget(self, key):
        if not isinstance(key, str) or not key.startswith('memory:'):
            raise ValueError('仅支持删除记忆 / Only memory records can be forgotten here')
        with self.connect() as db:
            db.execute('DELETE FROM revisions WHERE id=?', (key,))
            count = db.execute('DELETE FROM entries WHERE id=?', (key,)).rowcount
        return {'forgotten': key, 'deleted': bool(count)}

    def export(self):
        return {'title': 'AI4薄肌', 'schema_version': 1, 'entries': self.list()}
