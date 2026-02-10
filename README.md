# Loan Engine Pipeline

A comprehensive loan processing pipeline application that replicates notebook functionality for structured finance products. The application processes loans, applies configurable business rules, generates exception reports, and produces analytic outputs.

## Features

- **Automated Pipeline Processing**: Daily scheduled runs with manual trigger capability
- **User Authentication & Authorization**: Multi-tenant system with role-based access control (Admin, Analyst, Sales Team)
- **Data Isolation**: Sales teams can only view their own data
- **Comprehensive Validation**: 
  - Purchase price validation
  - Underwriting checks
  - CoMAP validation
  - Eligibility checks (Prime and SFY platforms)
- **Exception Reporting**: Detailed exception reports exported to Excel
- **Eligibility Reports**: Portfolio compliance reporting

## Tech Stack

### Backend
- **FastAPI**: Python web framework
- **PostgreSQL**: Database
- **SQLAlchemy**: ORM
- **Alembic**: Database migrations
- **Pandas/NumPy**: Data processing
- **APScheduler**: Task scheduling
- **JWT**: Authentication

### Frontend
- **React**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Axios**: HTTP client
- **React Router**: Navigation

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up database (see backend/scripts/README.md)
python scripts/init_db.py
python scripts/seed_admin.py

# Start server
uvicorn api.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Default Login Credentials

- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@example.com`

⚠️ **Important**: Change the password immediately after first login!

### Demo: Verify connectivity and database

To **start backend and frontend** and **verify connectivity (including the database)** for a demo:

1. **Start backend** (Terminal 1): `.\scripts\start-backend.ps1`
2. **Start frontend** (Terminal 2): `.\scripts\start-frontend.ps1`
3. **Verify** (Terminal 3): `.\scripts\verify-demo.ps1`
4. Open **http://localhost:5173** and log in (admin / admin123).

Or run `.\scripts\demo.ps1 -Launch` to start both servers in new windows and then run verification.

See **[DEMO.md](DEMO.md)** for the full demo script and troubleshooting.

## Project Structure

```
cursor_loan_engine/
├── backend/
│   ├── api/              # FastAPI routes and main app
│   ├── auth/             # Authentication & authorization
│   ├── config/           # Configuration and settings
│   ├── db/               # Database models and migrations
│   ├── orchestration/    # Pipeline execution logic
│   ├── outputs/          # Excel export functionality
│   ├── rules/            # Business rule validations
│   ├── scheduler/        # Automated task scheduling
│   ├── scripts/          # Setup and utility scripts
│   ├── tests/            # Test suite
│   ├── transforms/       # Data transformation logic
│   └── utils/            # Utility functions
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── contexts/     # React contexts (Auth)
│   │   ├── pages/        # Page components
│   │   └── services/     # API services
│   └── public/           # Static assets
└── README.md
```

## Documentation

- **[Backend Setup Guide](backend/scripts/README.md)**: Database initialization and setup
- **[Database Setup](backend/scripts/DATABASE_SETUP.md)**: Detailed database configuration
- **[File Structure Guide](backend/docs/FILE_STRUCTURE.md)**: Input file requirements
- **[Troubleshooting](backend/TROUBLESHOOTING.md)**: Common issues and solutions

## Development

### Running Tests

```bash
cd backend
pytest
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]
