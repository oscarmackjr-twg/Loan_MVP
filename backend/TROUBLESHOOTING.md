# Troubleshooting Guide

## Common Startup Issues

### 1. Logs Directory Not Found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'logs/loan_engine.log'
```

**Solution:**
The logs directory is now automatically created on startup. If you still see this error:
- Ensure you have write permissions in the backend directory
- Manually create the directory: `mkdir logs` (or `mkdir logs` on Windows)

### 2. .env File Parsing Warning

**Warning:**
```
python-dotenv could not parse statement starting at line 1
```

**Causes:**
- `.env` file has syntax errors
- `.env` file has invalid characters
- `.env` file encoding issues

**Solution:**
1. Check your `.env` file format:
   ```env
   # Correct format (no spaces around =)
   DATABASE_URL=postgresql://user:password@host:port/database
   SECRET_KEY=your-secret-key
   
   # Wrong format (spaces around =)
   DATABASE_URL = postgresql://...
   ```

2. Ensure `.env` file uses UTF-8 encoding

3. Remove or fix problematic lines in `.env`

4. The application will still start using defaults and environment variables even if `.env` has issues

### 3. Database Connection Errors

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
1. Verify database is running:
   ```bash
   # PostgreSQL
   pg_isready
   ```

2. Check `DATABASE_URL` is correct:
   ```bash
   python -c "from config.settings import settings; print(settings.DATABASE_URL)"
   ```

3. Test connection:
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```

### 4. Port Already in Use

**Error:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**
```bash
# Use a different port
uvicorn api.main:app --reload --port 8001

# Or find and kill the process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill
```

### 5. Module Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'xxx'
```

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or if using virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 6. Bcrypt / Passlib: “password cannot be longer than 72 bytes” or “module 'bcrypt' has no attribute '__about__'”

**Causes:**
- `passlib` 1.7.4 is incompatible with `bcrypt` 4.1+.
- Bcrypt limits passwords to 72 bytes.

**Solution:**
1. Pin bcrypt to a compatible version:
   ```bash
   pip install "bcrypt>=4.0,<4.1"
   ```
   Or ensure `requirements.txt` contains `bcrypt>=4.0,<4.1` and run `pip install -r requirements.txt`.

2. Use a password of at most 72 bytes (72 ASCII characters, or fewer if using non-ASCII).

### 7. “Could not validate credentials” in Frontend

**Error:**
```
Failed to start pipeline: Could not validate credentials
```

**Causes:**
- JWT token expired (default: 30 minutes)
- Token not being sent with request
- User deleted or inactive
- SECRET_KEY changed between login and request

**Solution:**

1. **Check if you're logged in:**
   - Open browser DevTools → Application/Storage → Local Storage
   - Verify `token` exists
   - If missing, log in again

2. **Token expired:**
   - Tokens expire after 30 minutes by default
   - Log out and log in again to get a new token
   - Or increase `ACCESS_TOKEN_EXPIRE_MINUTES` in settings

3. **Verify token is being sent:**
   - Open DevTools → Network tab
   - Make the request that fails
   - Check Request Headers for `Authorization: Bearer <token>`
   - If missing, the axios interceptor should fix this automatically

4. **Check backend logs:**
   - Look for JWT validation errors
   - Check if user exists in database

5. **Manual fix:**
   ```javascript
   // In browser console
   localStorage.removeItem('token')
   // Then log in again
   ```

### 8. “invalid input value for enum userrole: 'ADMIN'”

**Error:**
```
psycopg2.errors.InvalidTextRepresentation: invalid input value for enum userrole: "ADMIN"
```

**Cause:** PostgreSQL enum values are lowercase (`admin`, `analyst`, `sales_team`). SQLAlchemy was persisting enum names (`ADMIN`, etc.) instead of values.

**Solution:** The models now use `values_callable` so enum **values** are stored. Ensure you have the updated `db/models.py`. If you created tables with a different enum definition, align the DB enum or recreate tables.

### 8. Permission Errors (Windows)

**Error:**
```
PermissionError: [WinError 5] Access is denied
```

**Solution:**
- Run terminal as Administrator
- Check file/folder permissions
- Ensure antivirus isn't blocking file access

## Verifying frontend–backend connectivity

To confirm the frontend is talking to the backend:

1. **Login page indicator**  
   Open the app and go to the login screen. Under “Sign in to your account” you should see either “Backend connected” or “Backend unreachable”. The former means the browser successfully called `GET /health` on the API.

2. **Browser DevTools → Network**  
   Open DevTools (F12) → Network. Submit login or load a page that calls the API. Check that requests go to the expected host (e.g. same origin like `https://your-alb-url/api/...` or `http://localhost:8000/api/...`) and return 200 (or 401 for unauthenticated), not failed/CORS/blocked.

3. **Call the health endpoint from the same origin**  
   In the browser console or a new tab (same URL as the app), run:
   ```javascript
   fetch('/health').then(r => r.json()).then(console.log)
   ```
   You should see `{ status: "healthy" }`. If the request fails or goes to the wrong host, the frontend’s API base URL (e.g. `VITE_API_URL`) or same-origin setup is wrong.

4. **Production (ALB)**  
   The frontend is built with `VITE_API_URL=` so API calls use the same origin. Ensure the browser is loading the app from the same base URL as the backend (e.g. `https://your-alb.amazonaws.com/`). If the app is on a different domain, set `VITE_API_URL` at build time to the backend base URL (e.g. `https://api.yourdomain.com`).

## Verification Steps

After fixing issues, verify the application:

1. **Check backend starts:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

2. **Check API docs:**
   - Visit: http://localhost:8000/docs
   - Should show Swagger UI

3. **Check logs:**
   ```bash
   # Logs should be created automatically
   ls logs/  # Linux/Mac
   dir logs  # Windows
   ```

## Getting Help

If issues persist:

1. Check logs in `logs/loan_engine.log`
2. Enable debug logging by setting `LOG_LEVEL=DEBUG` in `.env`
3. Check application logs in console output
4. Verify all prerequisites are met (database, Python version, etc.)
