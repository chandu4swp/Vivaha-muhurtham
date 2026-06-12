# Database Connectivity Analysis - Vivaha Muhurtham

## Problem Summary
**Error**: "Error: no such table: users" when signing up in Vercel

## Root Causes

### 1. **Missing DATABASE_URL Environment Variable** (PRIMARY ISSUE)
- Your `db.py` checks: `USE_POSTGRES = bool(os.getenv("DATABASE_URL"))`
- If `DATABASE_URL` is not set in Vercel's environment, the app **falls back to SQLite**
- The code then tries to use: `SQLITE_DB_PATH = os.path.join(BASE_DIR, "matrimonial.db")`

**Problem**: Vercel's serverless environment has **ephemeral storage** - the filesystem is read-only and gets wiped after each function execution. This means:
- The `matrimonial.db` file cannot be persisted
- Each request runs in isolation
- Database tables are never created or lost between requests

### 2. **Database Initialization Timing Issue**
Current flow in `app.py` (line 280):
```python
try:
    init_db()
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")
```

This only runs in local development (`if __name__ == "__main__"`), NOT in Vercel's serverless environment. In Vercel, the code is imported as a module, so `init_db()` may not be called at all during the first request.

### 3. **In-Memory Database Fallback**
If the SQLite file cannot be created, the code falls back to in-memory SQLite:
```python
# From db.py line 68
conn = sqlite3.connect('file::memory:?cache=shared', uri=True)
```

**Problem**: With in-memory databases, data is lost between requests and the `users` table doesn't exist when signup is attempted.

### 4. **Signup Flow Error**
When you try to signup:
```python
# app.py line 231
create_user(email, password)
    ↓
# db.py line 279
cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)")
    ↓
ERROR: "no such table: users"
```

The `_ensure_tables_exist()` function is called before each operation (db.py line 231):
```python
def _ensure_tables_exist():
    # This checks if tables exist, but in Vercel it fails silently
    # because init_db() can't persist the database
```

---

## Current Database Configuration

### Code Detection Logic
```python
USE_POSTGRES = bool(os.getenv("DATABASE_URL"))

if USE_POSTGRES and HAS_POSTGRES:
    # Use PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
else:
    # Fall back to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH, timeout=5)
```

### What's Installed
From `requirements.txt`:
- ✅ `psycopg2-binary>=2.9.0` (PostgreSQL driver is installed)
- ❌ `DATABASE_URL` environment variable is NOT set in Vercel

---

## Database Schema

Both PostgreSQL and SQLite create the same tables:

### **users** table
- Stores login credentials
- Fields: `id`, `email`, `password_hash`, `created_at`

### **profiles** table  
- Stores matrimonial profile information
- Fields: name, email, phone, DOB, gender, religion, caste, education, occupation, income, height, city, state, country, bio, photo, created_at

---

## Solutions

### ✅ **SOLUTION 1: Set DATABASE_URL in Vercel (RECOMMENDED)**

1. **Get your PostgreSQL Connection String**
   - If using Vercel PostgreSQL: Copy the connection string from Vercel dashboard
   - If using external provider (Supabase, AWS RDS, Railway, etc.): Get the connection string from their dashboard
   
   Format: `postgresql://user:password@host:port/dbname`

2. **Add to Vercel Environment Variables**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add new variable:
     - Name: `DATABASE_URL`
     - Value: `postgresql://user:password@host:port/dbname`
   - Redeploy your project

3. **Verify PostgreSQL is being used**
   - The code will detect `DATABASE_URL` and use PostgreSQL instead of SQLite
   - Check Vercel function logs for: `✓ Connected to PostgreSQL`

### ✅ **SOLUTION 2: Fix Database Initialization in Serverless Environment**

The current `init_db()` is not guaranteed to run in serverless. Here's a fix:

**File: db.py**

Replace the current `_ensure_tables_exist()` function (around line 225) with this more robust version:

```python
def _ensure_tables_exist():
    """Ensure database tables exist (called before operations)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if users table exists
        if USE_POSTGRES and HAS_POSTGRES:
            cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name='users'")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        
        table_exists = cursor.fetchone() is not None
        cursor.close()
        close_db_connection(conn)
        
        if not table_exists:
            print("⚠ Tables don't exist, initializing database...")
            init_db()
    except Exception as e:
        print(f"Warning: Could not check tables: {e}")
        # If check fails, try to initialize
        try:
            init_db()
        except Exception as e2:
            print(f"Error initializing database: {e2}")
```

### ✅ **SOLUTION 3: Add Startup Database Initialization**

**File: app.py**

Add this after line 36 (after app configuration):

```python
# Ensure database is initialized on first request
def _init_db_once():
    """Initialize database on first request"""
    if not hasattr(app, '_db_initialized'):
        try:
            init_db()
            app._db_initialized = True
            print("✓ Database initialized on first request")
        except Exception as e:
            print(f"⚠ Database initialization on first request failed: {e}")

@app.before_request
def before_request():
    _init_db_once()
```

---

## Step-by-Step Fix for Your Vercel Deployment

### Step 1: Configure PostgreSQL Connection
- [ ] Obtain PostgreSQL connection string
- [ ] Add `DATABASE_URL` to Vercel environment variables
- [ ] Redeploy project

### Step 2: Verify Logs
- [ ] Check Vercel deployment logs for `✓ Connected to PostgreSQL`
- [ ] Confirm `CREATE TABLE` statements executed

### Step 3: Test Signup
- [ ] Try creating a new account
- [ ] Should no longer see "no such table: users" error

### Step 4: If Issues Persist
- [ ] Check Vercel environment variables are set correctly
- [ ] Verify PostgreSQL database is accessible from Vercel
- [ ] Test connection string locally with psycopg2

---

## Database Connection Flow

```
User Signs Up
    ↓
/signup route (app.py:211)
    ↓
create_user(email, password) called (db.py:271)
    ↓
_ensure_tables_exist() (db.py:225)
    ↓
get_db_connection() (db.py:31)
    ↓
Check: Is DATABASE_URL set?
    ├─ YES → Connect to PostgreSQL ✅
    └─ NO  → Fall back to SQLite ❌ (FAILS IN VERCEL)
    ↓
INSERT INTO users...
```

---

## Current Environment Status

| Component | Status | Details |
|-----------|--------|---------|
| PostgreSQL Driver | ✅ Installed | `psycopg2-binary` in requirements.txt |
| DATABASE_URL | ❌ **NOT SET** | **MAIN ISSUE** |
| SQLite Fallback | ⚠️ Non-functional in Vercel | Serverless has ephemeral storage |
| Database Init | ⚠️ Unreliable | Only runs in `if __name__ == "__main__"` |
| Tables Persistence | ❌ FAILING | Can't persist in Vercel without PostgreSQL |

---

## Recommended PostgreSQL Providers for Vercel

1. **Vercel PostgreSQL** (built-in) - Free tier available
2. **Supabase** - Free tier, easy integration
3. **Railway** - Developer-friendly, affordable
4. **AWS RDS** - Reliable, scalable
5. **Neon** - Serverless PostgreSQL, perfect for Vercel

Choose one, create a database, and add the connection string to Vercel environment variables.
