# Loan Engine – Demo Script (Working Functionality)

Use this to **start the app**, **verify connectivity**, and **confirm the database** for a demo.

---

## Prerequisites (once)

- **Python 3.10+** with venv and `pip install -r backend/requirements.txt`
- **Node.js 18+** and npm
- **PostgreSQL** running; database created (e.g. `loan_engine` or `cursor_db`)
- **Backend tables** created: `cd backend && python scripts/init_db.py`
- **Admin user** created: `cd backend && python scripts/seed_admin.py`  
  Default login: **admin** / **admin123**

---

## Option A: Step-by-step (good for first-time demo)

### 1. Start the backend

In **Terminal 1** (PowerShell, from project root):

```powershell
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine
.\scripts\start-backend.ps1
```

Wait until you see something like: `Uvicorn running on http://0.0.0.0:8000`

### 2. Start the frontend

In **Terminal 2** (new PowerShell, same project root):

```powershell
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine
.\scripts\start-frontend.ps1
```

Wait until you see something like: `Local: http://localhost:5173/`

### 3. Verify connectivity and database

In **Terminal 3** (new PowerShell, same project root):

```powershell
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine
.\scripts\verify-demo.ps1
```

You should see:

- **Backend API (health)** – OK  
- **Backend + Database (ready)** – OK (database connected)  
- **Frontend** – OK (if step 2 is running)  
- **API root** – OK  

If any step fails, see [Troubleshooting](#troubleshooting) below.

### 4. Use the app in the browser

1. Open **http://localhost:5173**
2. Log in: **admin** / **admin123**
3. You should see the dashboard (e.g. pipeline runs, option to start a run).

---

## Option B: One command (launch both servers + verify)

From project root:

```powershell
.\scripts\demo.ps1 -Launch
```

This opens **two new PowerShell windows** (backend and frontend) and, after a short wait, runs the same verification as in Option A. Then open http://localhost:5173 and log in as above.

---

## What the verification script checks

| Check              | Endpoint / Action              | Meaning                    |
|--------------------|--------------------------------|----------------------------|
| Backend API        | `GET http://localhost:8000/health`       | API process is up          |
| Backend + DB       | `GET http://localhost:8000/health/ready` | API can talk to PostgreSQL|
| Frontend           | `GET http://localhost:5173`             | Vite dev server is up      |
| API root           | `GET http://localhost:8000/`             | Root endpoint responds     |

---

## Quick reference

| What        | Command / URL |
|------------|----------------|
| Start backend  | `.\scripts\start-backend.ps1` |
| Start frontend | `.\scripts\start-frontend.ps1` |
| Verify all     | `.\scripts\verify-demo.ps1` |
| Full demo      | `.\scripts\demo.ps1 -Launch` |
| Backend URL    | http://localhost:8000 |
| API docs       | http://localhost:8000/docs |
| Frontend URL   | http://localhost:5173 |
| Login          | admin / admin123 |

---

## Windows (cmd vs PowerShell)

All demo scripts (`.ps1`) are for **PowerShell**. Run them from the **project root** in PowerShell:

```powershell
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine
.\scripts\start-backend.ps1
```

**If you use Command Prompt (cmd) instead:**

- The `.ps1` scripts won’t run in cmd. Use the same steps manually:
  1. **Backend:**  
     `cd backend` → `venv\Scripts\activate` → `uvicorn api.main:app --reload`
  2. **Frontend:**  
     Open a second cmd window → `cd frontend` → `npm run dev`
  3. **Verify:**  
     In a browser: http://localhost:8000/health/ready and http://localhost:5173

- Paths: use backslashes (`backend\scripts`) or forward slashes (`backend/scripts`); both work in Python and Node on Windows.

**Virtual environment (Windows):**

| Shell       | Activate backend venv                    |
|------------|-------------------------------------------|
| PowerShell | `cd backend; .\venv\Scripts\Activate.ps1` |
| cmd        | `cd backend` then `venv\Scripts\activate.bat` |

**Docker (Windows):**  
Same as elsewhere: from project root run `docker build -f deploy/Dockerfile .` in either PowerShell or cmd. If you use Docker Desktop, the daemon must be running.

---

## Troubleshooting

### Backend won’t start

- Activate venv if you use one:  
  `cd backend; .\venv\Scripts\Activate.ps1`
- Install deps:  
  `pip install -r backend/requirements.txt`
- Port 8000 free:  
  `netstat -ano | findstr :8000`

### “Database disconnected” or health/ready fails

- PostgreSQL is running (e.g. service or `pg_ctl`).
- Database exists:  
  `psql -U postgres -c "CREATE DATABASE loan_engine;"`  
  (or use your DB name.)
- Tables exist:  
  `cd backend && python scripts/init_db.py`
- `DATABASE_URL` in `backend/.env` (or env) matches your user/password/host/port/db.  
  Example:  
  `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/loan_engine`

### Frontend won’t start

- Install deps:  
  `cd frontend && npm install`
- Port 5173 free:  
  `netstat -ano | findstr :5173`

### Can’t log in

- Seed admin:  
  `cd backend && python scripts/seed_admin.py`
- Use **admin** / **admin123** (or the username/password you set with the seed script).

---

## Summary

1. Start backend: `.\scripts\start-backend.ps1`  
2. Start frontend: `.\scripts\start-frontend.ps1`  
3. Verify: `.\scripts\verify-demo.ps1`  
4. Open http://localhost:5173 and log in (admin / admin123).

For a one-shot demo: `.\scripts\demo.ps1 -Launch`, then run verify in the main window and open the app in the browser.
