# Vercel Environment Variables Setup Guide

Complete step-by-step guide to configure your PostgreSQL database connection in Vercel.

---

## Step 1: Choose a PostgreSQL Provider

Select one of these providers based on your needs:

### Option A: **Vercel PostgreSQL** (Recommended - Built-in)
- **Easiest**: Integrated directly with Vercel
- **Link**: https://vercel.com/docs/storage/vercel-postgres
- **Free tier**: Yes (limited)
- **Setup time**: 5 minutes

### Option B: **Supabase** (Popular)
- **Why**: Free tier is generous, simple UI
- **Link**: https://supabase.com
- **Free tier**: 500MB database, 2GB bandwidth
- **Setup time**: 10 minutes

### Option C: **Railway** (Developer-Friendly)
- **Why**: Affordable, good documentation
- **Link**: https://railway.app
- **Free tier**: $5 credit monthly
- **Setup time**: 10 minutes

### Option D: **Neon** (Serverless PostgreSQL)
- **Why**: Optimized for serverless, auto-scaling
- **Link**: https://neon.tech
- **Free tier**: Yes
- **Setup time**: 10 minutes

---

## Step 2: Create a PostgreSQL Database

### For Vercel PostgreSQL:
1. Go to: https://vercel.com/dashboard
2. Click on your project
3. Go to **Storage** tab
4. Click **Create Database**
5. Select **Postgres**
6. Choose a region
7. Click **Create**
8. **Connection string will be automatically added to environment variables** ✅

### For Supabase:
1. Go to: https://app.supabase.com
2. Click **New Project**
3. Fill in project details (choose a region close to Vercel)
4. Click **Create new project**
5. Wait for database to initialize (~30 seconds)
6. Go to **Settings** → **Database** → **Connection Pooling**
7. Copy the connection string with mode `Session` or `Transaction`

### For Railway:
1. Go to: https://railway.app/dashboard
2. Click **New Project**
3. Select **Provision PostgreSQL**
4. Database will be created automatically
5. Click on the PostgreSQL plugin
6. Go to **Variables** tab
7. Find `DATABASE_URL` variable

### For Neon:
1. Go to: https://console.neon.tech
2. Click **Create a project**
3. Choose PostgreSQL version (keep default)
4. Click **Create project**
5. Copy the **Connection string** from the dashboard

---

## Step 3: Add DATABASE_URL to Vercel

### Method 1: Using Vercel Dashboard (Easiest)

1. **Go to Vercel Project**
   - Open: https://vercel.com/dashboard
   - Select your **Vivaha-muhurtham** project

2. **Navigate to Settings**
   - Click **Settings** tab at the top
   - Select **Environment Variables** from left sidebar

3. **Add the Variable**
   - Click **Add New** button
   - In the **Name** field, enter: `DATABASE_URL`
   - In the **Value** field, paste your PostgreSQL connection string
   - Example: `postgresql://user:password@host:port/dbname`

4. **Select Environments**
   - Check **Production** ✓
   - Check **Preview** ✓
   - Check **Development** ✓

5. **Save**
   - Click **Save** button

6. **Redeploy Your Project**
   - Go to **Deployments** tab
   - Click the three dots (...) on the latest deployment
   - Select **Redeploy**
   - Wait for deployment to complete (~2 minutes)

### Method 2: Using Vercel CLI (Terminal)

```powershell
# Install Vercel CLI (if not already installed)
npm install -g vercel

# Login to Vercel
vercel login

# Navigate to your project directory
cd "c:\Users\Walmart\Documents\Vivaha-muhurutham\Vivaha-muhurtham"

# Add environment variable
vercel env add DATABASE_URL

# Paste your PostgreSQL connection string when prompted

# Redeploy
vercel --prod
```

---

## Step 4: Connection String Format

Your connection string should look like one of these:

### PostgreSQL Standard Format:
```
postgresql://username:password@hostname:5432/database_name
```

### PostgreSQL URI Format:
```
postgres://username:password@hostname:5432/database_name
```

### With SSL (Recommended):
```
postgresql://username:password@hostname:5432/database_name?sslmode=require
```

### Example from Supabase:
```
postgresql://postgres.abcdefghij:password@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require
```

---

## Step 5: Verify the Connection

### Check Vercel Logs
1. Go to your Vercel project dashboard
2. Click **Deployments** tab
3. Click on the latest deployment
4. Click **Logs** button
5. Look for one of these messages:

✅ **Success:**
```
✓ Connected to PostgreSQL
✓ Database initialized successfully
```

❌ **Failure:**
```
✗ PostgreSQL connection failed
✗ Database initialization error
```

### Test Signup
1. Open your deployed app
2. Try creating a new account
3. You should **not** see "no such table: users" error anymore

---

## Step 6: Troubleshooting

### Problem: "Connection refused" or "Network timeout"

**Solution:**
- Verify the connection string is correct
- Check that PostgreSQL server is running
- Ensure Vercel's IP addresses are whitelisted (if your provider has a firewall)
- Test the connection string locally first

### Problem: "Role does not exist"

**Solution:**
- Verify the username in your connection string
- For Supabase, ensure you're using the `postgres` user or your created user

### Problem: "Database does not exist"

**Solution:**
- The database name must exist
- Verify the database name matches the connection string
- For new databases, create it first in your provider's dashboard

### Problem: "SSL certificate problem"

**Solution:**
- Add `?sslmode=require` to your connection string
- Or try `?sslmode=disable` for local testing (NOT recommended for production)

### Problem: Still getting "no such table: users"

**Solution:**
1. Verify `DATABASE_URL` is set in Vercel environment variables
2. Redeploy your project
3. Check Vercel deployment logs for initialization messages
4. Clear browser cookies/session cache
5. Try signup again in an incognito window

---

## Step 7: Database Initialization (What Happens)

When you deploy with `DATABASE_URL` set:

```
Vercel deploys your app
    ↓
First user request arrives
    ↓
before_request() hook runs (new code we added)
    ↓
_ensure_db_initialized() called
    ↓
init_db() creates tables:
  - users table (for login credentials)
  - profiles table (for matrimonial profiles)
    ↓
Tables ready for use
    ↓
Signup/login operations work ✅
```

---

## Step 8: Verify Database Persistence

To confirm your database is working:

1. **Signup** with test credentials
2. **Logout**
3. **Login** with the same credentials
4. **You should see your profile** - this proves data persisted in PostgreSQL ✅

---

## Security Best Practices

### ✅ DO:
- Keep your connection string secret
- Use strong passwords for your database user
- Enable SSL for production (`?sslmode=require`)
- Restrict database access to only necessary IPs
- Rotate credentials periodically

### ❌ DON'T:
- Commit `DATABASE_URL` to GitHub
- Share connection strings in public
- Use `sslmode=disable` in production
- Use default/simple passwords
- Store credentials in source code

---

## Summary of Changes Made

### 1. **Enhanced Database Initialization** (db.py)
- Added better error recovery in `_ensure_tables_exist()`
- Auto-initializes database if table check fails

### 2. **Added Before-Request Hook** (app.py)
- New `before_request()` function ensures database is initialized on first request
- Critical for serverless environments like Vercel

### 3. **Environment Variable Configuration** (This guide)
- Step-by-step instructions for setting `DATABASE_URL`
- Multiple PostgreSQL provider options
- Troubleshooting guide

---

## Quick Reference

| Task | Link |
|------|------|
| Vercel Project Dashboard | https://vercel.com/dashboard |
| Vercel PostgreSQL Docs | https://vercel.com/docs/storage/vercel-postgres |
| Supabase Console | https://app.supabase.com |
| Railway Dashboard | https://railway.app/dashboard |
| Neon Console | https://console.neon.tech |

---

## Next Steps

1. ✅ Choose a PostgreSQL provider
2. ✅ Create a database
3. ✅ Copy the connection string
4. ✅ Add `DATABASE_URL` to Vercel
5. ✅ Redeploy your project
6. ✅ Test signup/login
7. ✅ Monitor logs for any errors

**Done!** Your app should now work without the "no such table" error.
