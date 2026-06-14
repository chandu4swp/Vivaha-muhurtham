"""
Database Layer - Handles all database operations
Supports both PostgreSQL (production) and SQLite (development)
"""

import datetime
import os
import sqlite3

try:
    import psycopg2
    import psycopg2.extras
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

from werkzeug.security import generate_password_hash


# ── Configuration ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "matrimonial.db")

# Database configuration
USE_POSTGRES = bool(os.getenv("DATABASE_URL"))
DATABASE_URL = os.getenv("DATABASE_URL")

# Use the Neon table in PostgreSQL, but keep SQLite local profiles for development.
PROFILE_TABLE = "vivahusers" if USE_POSTGRES and HAS_POSTGRES else "profiles"
IMAGE_TABLE = "vivahimages"

PROFILE_FIELDS = [
    ("id", "ProfileId"),
    ("name", "Name"),
    ("caste", "Caste"),
    ("religion", "Religion"),
    ("religion_alt", "Religupaion"),
    ("city", "City"),
    ("qualification", "Qualification"),
    ("education", "Education"),
    ("state", "State"),
    ("country", "Country"),
    ("created_at", "ProfileCreationDate"),
    ("dob", "Birthday"),
    ("birth_time", "BirthTime"),
    ("phone", "mobile"),
    ("alt_phone", "altmobile"),
    ("income", "Annual Income"),
    ("occupation", "Occupation"),
    ("bio", "Bio"),
    ("height", "Height"),
    ("photo", "image"),
]

APP_TO_DB_PROFILE = {app: db for app, db in PROFILE_FIELDS}
DB_TO_APP_PROFILE = {db: app for app, db in PROFILE_FIELDS}
PROFILE_INSERT_COLUMNS = [db for app, db in PROFILE_FIELDS if app != "created_at"]

# Track if we're using in-memory database
_use_memory_db = False
_memory_db_connection = None  # Keep persistent connection for in-memory DB


# ── Connection Management ──────────────────────────────────────────────────────

def get_db_connection():
    """
    Get database connection (PostgreSQL for production, SQLite for local development)
    Returns: Connection object with cursor available
    """
    global _use_memory_db
    
    # Try PostgreSQL first if DATABASE_URL is set
    if USE_POSTGRES and HAS_POSTGRES:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.cursor_factory = psycopg2.extras.DictCursor
            print("✓ Connected to PostgreSQL")
            return conn
        except Exception as e:
            print(f"✗ PostgreSQL connection failed: {e}")
    
    # Try SQLite file database
    if not _use_memory_db:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH, timeout=5)
            conn.row_factory = sqlite3.Row
            print(f"✓ Connected to SQLite: {SQLITE_DB_PATH}")
            return conn
        except (OSError, PermissionError, sqlite3.Error) as e:
            print(f"✗ Cannot access SQLite file ({SQLITE_DB_PATH}): {e}")
            print("→ Switching to in-memory database")
            _use_memory_db = True
    
    # Use shared in-memory database (allows multiple connections to same DB)
    if _use_memory_db:
        try:
            conn = sqlite3.connect('file::memory:?cache=shared', uri=True)
            conn.row_factory = sqlite3.Row
            print("⚠ Using shared in-memory SQLite database (data persists for this session)")
            return conn
        except Exception as e:
            print(f"✗ Failed to connect to shared memory DB: {e}")
            # Fallback to regular in-memory (will create separate DB per connection)
            conn = sqlite3.connect(':memory:')
            conn.row_factory = sqlite3.Row
            print("⚠ Using non-shared in-memory database (data may not persist)")
            return conn


def close_db_connection(conn):
    """Close database connection"""
    if conn:
        conn.close()


# ── Database Initialization ────────────────────────────────────────────────────

def init_db():
    """Initialize database schema (create tables if they don't exist)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        profile_table_name = PROFILE_TABLE
        quoted_profile = f'"{profile_table_name}"'

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {quoted_profile} (
                "ProfileId" VARCHAR(50) PRIMARY KEY,
                "Name" VARCHAR(255) NOT NULL,
                "Caste" VARCHAR(100),
                "Religion" VARCHAR(100),
                "Religupaion" VARCHAR(100),
                "City" VARCHAR(100),
                "Qualification" VARCHAR(100),
                "Education" VARCHAR(100),
                "State" VARCHAR(100),
                "Country" VARCHAR(100) DEFAULT 'India',
                "ProfileCreationDate" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "Birthday" DATE,
                "BirthTime" VARCHAR(50),
                "mobile" VARCHAR(20),
                "altmobile" VARCHAR(20),
                "Annual Income" VARCHAR(100),
                "Occupation" VARCHAR(100),
                "Bio" TEXT,
                "Height" VARCHAR(50),
                "image" VARCHAR(255)
            )
        """)
        if USE_POSTGRES and HAS_POSTGRES:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usersauth (
                    "Username" VARCHAR(50) UNIQUE NOT NULL,
                    "Emailaddress" TEXT UNIQUE NOT NULL,
                    "Password" TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vivahimages (
                    "id" SERIAL PRIMARY KEY,
                    "name" TEXT UNIQUE NOT NULL,
                    "photo" BYTEA
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usersauth (
                    "Username" TEXT UNIQUE NOT NULL,
                    "Emailaddress" TEXT UNIQUE NOT NULL,
                    "Password" TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vivahimages (
                    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                    "name" TEXT UNIQUE NOT NULL,
                    "photo" BLOB
                )
            """)

        conn.commit()
        cursor.close()
        close_db_connection(conn)
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization error: {e}")
        print("→ Attempting to re-initialize with in-memory database")

        global _use_memory_db
        _use_memory_db = True
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {quoted_profile} (
                    "ProfileId" TEXT PRIMARY KEY,
                    "Name" TEXT NOT NULL,
                    "Caste" TEXT,
                    "Religion" TEXT,
                    "Religupaion" TEXT,
                    "City" TEXT,
                    "Qualification" TEXT,
                    "Education" TEXT,
                    "State" TEXT,
                    "Country" TEXT DEFAULT 'India',
                    "ProfileCreationDate" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    "Birthday" TEXT,
                    "BirthTime" TEXT,
                    "mobile" TEXT,
                    "altmobile" TEXT,
                    "Annual Income" TEXT,
                    "Occupation" TEXT,
                    "Bio" TEXT,
                    "Height" TEXT,
                    "image" TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usersauth (
                    "Username" TEXT UNIQUE NOT NULL,
                    "Emailaddress" TEXT UNIQUE NOT NULL,
                    "Password" TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vivahimages (
                    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                    "name" TEXT UNIQUE NOT NULL,
                    "photo" BLOB
                )
            """)
            conn.commit()
            cursor.close()
            close_db_connection(conn)
            print("✓ Database re-initialized with in-memory storage")
        except Exception as e2:
            print(f"✗ Failed to initialize in-memory database: {e2}")
            raise


def _ensure_tables_exist():
    """Ensure database tables exist (called before operations)"""
    profile_exists = False
    users_exist = False
    images_exist = False

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if USE_POSTGRES and HAS_POSTGRES:
            cursor.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
                (PROFILE_TABLE,)
            )
            profile_exists = cursor.fetchone() is not None
            cursor.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
                ("usersauth",)
            )
            users_exist = cursor.fetchone() is not None
            cursor.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
                (IMAGE_TABLE,)
            )
            images_exist = cursor.fetchone() is not None
        else:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (PROFILE_TABLE,)
            )
            profile_exists = cursor.fetchone() is not None
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                ("usersauth",)
            )
            users_exist = cursor.fetchone() is not None
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (IMAGE_TABLE,)
            )
            images_exist = cursor.fetchone() is not None

        cursor.close()
        close_db_connection(conn)

        if not profile_exists or not users_exist or not images_exist:
            print("⚠ Tables don't exist, initializing database...")
            init_db()
    except Exception as e:
        print(f"⚠ Could not verify tables exist: {e}")
        try:
            print("→ Attempting automatic database initialization...")
            init_db()
        except Exception as init_error:
            print(f"✗ Critical: Database initialization failed: {init_error}")


def get_db_info():
    """Return diagnostic info about the database connection and existing tables."""
    info = {
        "use_postgres": USE_POSTGRES,
        "has_psycopg2": HAS_POSTGRES,
        "database_url": bool(DATABASE_URL),
        "server": None,
        "tables": [],
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if USE_POSTGRES and HAS_POSTGRES:
            try:
                cursor.execute("SELECT version()")
                info["server"] = cursor.fetchone()[0]
            except Exception:
                pass
            try:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                info["tables"] = [r[0] for r in cursor.fetchall()]
            except Exception:
                pass
        else:
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                info["tables"] = [r[0] for r in cursor.fetchall()]
            except Exception:
                pass

        cursor.close()
        close_db_connection(conn)
    except Exception as e:
        info["error"] = str(e)

    return info


def create_profile_image(name, photo_bytes):
    """
    Store or update a profile image in the vivahimages table.
    Args: name (str), photo_bytes (bytes)
    """
    if not name or photo_bytes is None:
        return

    try:
        _ensure_tables_exist()
        conn = get_db_connection()
        cursor = conn.cursor()

        if USE_POSTGRES and HAS_POSTGRES:
            cursor.execute(
                'INSERT INTO vivahimages ("name", "photo") VALUES (%s, %s) '
                'ON CONFLICT ("name") DO UPDATE SET "photo" = EXCLUDED."photo"',
                (name, photo_bytes)
            )
        else:
            cursor.execute(
                'INSERT OR REPLACE INTO vivahimages ("name", "photo") VALUES (?, ?)',
                (name, photo_bytes)
            )

        conn.commit()
        cursor.close()
        close_db_connection(conn)
    except Exception as e:
        print(f"Error storing profile image: {e}")
        raise


def get_profile_image_by_name(name):
    """
    Fetch raw profile image bytes by profile name.
    Args: name (str)
    Returns: bytes or None
    """
    if not name:
        return None

    try:
        _ensure_tables_exist()
        conn = get_db_connection()
        cursor = conn.cursor()

        if USE_POSTGRES and HAS_POSTGRES:
            cursor.execute('SELECT "photo" FROM vivahimages WHERE "name" = %s', (name,))
        else:
            cursor.execute('SELECT "photo" FROM vivahimages WHERE "name" = ?', (name,))

        row = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)

        if row:
            if isinstance(row, dict) or hasattr(row, "keys"):
                return row.get("photo")
            return row[0]
        return None
    except Exception as e:
        print(f"Error fetching profile image: {e}")
        raise

# ── User Operations ────────────────────────────────────────────────────────────

def get_user_by_email(email):
    """
    Fetch user by email address
    Args: email (str) - User email
    Returns: User row or None
    """
    try:
        _ensure_tables_exist()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if USE_POSTGRES and HAS_POSTGRES:
            cursor.execute('SELECT * FROM usersauth WHERE "Emailaddress" = %s', (email,))
        else:
            cursor.execute('SELECT * FROM usersauth WHERE "Emailaddress" = ?', (email,))

        row = cursor.fetchone()
        if row is None:
            # fallback for legacy auth data stored in the old users table
            if USE_POSTGRES and HAS_POSTGRES:
                cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            else:
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            legacy_row = cursor.fetchone()
            if legacy_row:
                # migrate legacy auth entry to usersauth for future use
                try:
                    legacy_data = row_to_dict(legacy_row)
                    username = email if len(email) <= 50 else email[:50]
                    password_hash = legacy_data.get("password_hash")
                    if password_hash:
                        if USE_POSTGRES and HAS_POSTGRES:
                            cursor.execute(
                                'INSERT INTO usersauth ("Username", "Emailaddress", "Password") VALUES (%s, %s, %s)',
                                (username, email, password_hash)
                            )
                        else:
                            cursor.execute(
                                'INSERT INTO usersauth ("Username", "Emailaddress", "Password") VALUES (?, ?, ?)',
                                (username, email, password_hash)
                            )
                        conn.commit()
                except Exception:
                    pass
                row = legacy_row

        cursor.close()
        close_db_connection(conn)
        return row
    except Exception as e:
        print(f"Error fetching user: {e}")
        raise


def create_user(email, password):
    """
    Create a new user account
    Args: email (str), password (str)
    Returns: None
    Raises: Exception on database error
    """
    try:
        _ensure_tables_exist()
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        username = email if len(email) <= 50 else email[:50]
        if USE_POSTGRES and HAS_POSTGRES:
            cursor.execute(
                "INSERT INTO usersauth (\"Username\", \"Emailaddress\", \"Password\") VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
        else:
            cursor.execute(
                "INSERT INTO usersauth (\"Username\", \"Emailaddress\", \"Password\") VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
        
        conn.commit()
        cursor.close()
        close_db_connection(conn)
    except Exception as e:
        print(f"Error creating user: {e}")
        raise


# ── Profile Operations ─────────────────────────────────────────────────────────

def create_profile(profile_id, data, photo_bytes=None):
    """
    Create a new profile and optionally store the uploaded image.
    Args: profile_id (str), data (dict with profile fields), photo_bytes (bytes or None)
    Returns: None
    Raises: Exception on database error
    """
    try:
        _ensure_tables_exist()
        conn = get_db_connection()
        cursor = conn.cursor()

        columns = PROFILE_INSERT_COLUMNS
        quoted_columns = ", ".join([f'"{col}"' for col in columns])
        placeholders = ", ".join(["%s"] * len(columns)) if USE_POSTGRES and HAS_POSTGRES else ", ".join(["?"] * len(columns))
        values = [
            profile_id,
            data.get("name"),
            data.get("caste"),
            data.get("religion"),
            data.get("religion_alt"),
            data.get("city"),
            data.get("qualification") or data.get("education"),
            data.get("education"),
            data.get("state"),
            data.get("country", "India"),
            data.get("dob"),
            data.get("birth_time"),
            data.get("phone"),
            data.get("alt_phone"),
            data.get("income"),
            data.get("occupation"),
            data.get("bio"),
            data.get("height"),
            None,
        ]

        query = f"INSERT INTO \"{PROFILE_TABLE}\" ({quoted_columns}) VALUES ({placeholders})"
        cursor.execute(query, tuple(values))

        conn.commit()
        cursor.close()
        close_db_connection(conn)

        if photo_bytes:
            create_profile_image(data.get("name"), photo_bytes)
    except Exception as e:
        print(f"Error creating profile: {e}")
        raise


def get_profile_by_id(profile_id):
    """
    Fetch profile by ID
    Args: profile_id (str)
    Returns: Profile row or None
    """
    try:
        _ensure_tables_exist()
        conn = get_db_connection()
        cursor = conn.cursor()

        query = f'SELECT * FROM "{PROFILE_TABLE}" WHERE "ProfileId" = %s' if USE_POSTGRES and HAS_POSTGRES else f'SELECT * FROM "{PROFILE_TABLE}" WHERE "ProfileId" = ?'
        cursor.execute(query, (profile_id,))

        row = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        return row
    except Exception as e:
        print(f"Error fetching profile: {e}")
        raise


def search_profiles(query, limit=20):
    """
    Search profiles by name, ID, phone, caste, or religion
    Args: query (str), limit (int)
    Returns: List of profile rows
    """
    try:
        _ensure_tables_exist()
        conn = get_db_connection()
        cursor = conn.cursor()

        like_query = f"%{query}%"
        if USE_POSTGRES and HAS_POSTGRES:
            cursor.execute(f"""
                SELECT * FROM "{PROFILE_TABLE}"
                WHERE "ProfileId" ILIKE %s
                   OR "Name" ILIKE %s
                   OR "mobile" ILIKE %s
                   OR "altmobile" ILIKE %s
                   OR "Caste" ILIKE %s
                   OR "Religion" ILIKE %s
                ORDER BY "ProfileCreationDate" DESC
                LIMIT %s
            """, (like_query, like_query, like_query, like_query, like_query, like_query, limit))
        else:
            cursor.execute(f"""
                SELECT * FROM "{PROFILE_TABLE}"
                WHERE "ProfileId" LIKE ?
                   OR "Name" LIKE ?
                   OR "mobile" LIKE ?
                   OR "altmobile" LIKE ?
                   OR "Caste" LIKE ?
                   OR "Religion" LIKE ?
                ORDER BY "ProfileCreationDate" DESC
                LIMIT ?
            """, (like_query, like_query, like_query, like_query, like_query, like_query, limit))

        rows = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)
        return rows
    except Exception as e:
        print(f"Error searching profiles: {e}")
        raise


def get_all_profiles(limit=None):
    """
    Get all profiles ordered by creation date
    Args: limit (int or None)
    Returns: List of profile rows
    """
    try:
        _ensure_tables_exist()
        conn = get_db_connection()
        cursor = conn.cursor()

        if limit:
            if USE_POSTGRES and HAS_POSTGRES:
                cursor.execute(f'SELECT * FROM "{PROFILE_TABLE}" ORDER BY "ProfileCreationDate" DESC LIMIT %s', (limit,))
            else:
                cursor.execute(f'SELECT * FROM "{PROFILE_TABLE}" ORDER BY "ProfileCreationDate" DESC LIMIT ?', (limit,))
        else:
            cursor.execute(f'SELECT * FROM "{PROFILE_TABLE}" ORDER BY "ProfileCreationDate" DESC')

        rows = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)
        return rows
    except Exception as e:
        print(f"Error fetching all profiles: {e}")
        raise


def row_to_dict(row):
    """
    Convert database row to dictionary
    Works with both SQLite Row and PostgreSQL DictRow
    """
    if row is None:
        return None

    auth_map = {
        "Username": "username",
        "Emailaddress": "email",
        "Password": "password_hash",
    }

    data = dict(row)
    mapped = {}
    for key, value in data.items():
        if isinstance(value, (datetime.date, datetime.datetime)):
            value = value.isoformat()
        if key in DB_TO_APP_PROFILE:
            mapped[DB_TO_APP_PROFILE[key]] = value
        elif key in auth_map:
            mapped[auth_map[key]] = value
        else:
            mapped[key] = value
    return mapped
