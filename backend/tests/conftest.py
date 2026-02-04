"""Pytest configuration and shared fixtures."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.connection import Base, get_db
from db.models import User, SalesTeam, PipelineRun, UserRole, RunStatus
from config.settings import settings
from auth.security import get_password_hash


# Test database setup
@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override get_db dependency for testing."""
    def _get_db():
        try:
            yield test_db_session
        finally:
            pass
    return _get_db


# Sample data fixtures
@pytest.fixture
def sample_loans_df():
    """Sample loans dataframe."""
    return pd.DataFrame({
        'Account Number': [1001, 1002, 1003, 1004, 1005],
        'Loan Group': ['FX3_GROUP', 'PRIME_GROUP', 'FX1_GROUP', 'PRIME_GROUP', 'FX3_GROUP'],
        'Status Codes': ['', 'REPURCHASE', '', 'ACTIVE', ''],
        'Open Date': pd.to_datetime(['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2024-05-12']),
        'maturityDate': pd.to_datetime(['2029-01-15', '2029-02-20', '2029-03-10', '2029-04-05', '2029-05-12']),
    })


@pytest.fixture
def sample_sfy_df():
    """Sample SFY dataframe (after normalization)."""
    return pd.DataFrame({
        'SELLER Loan #': ['SFC_1001', 'SFC_1003', 'SFC_1005'],
        'Loan Program': ['Unsec Std - 999 - 120', 'Unsec Std - 999 - 144', 'Unsec Std - 999 - 120'],
        'Application Type': ['STANDARD', 'STANDARD', 'HD NOTE'],
        'Platform': ['SFY', 'SFY', 'SFY'],
        'Orig. Balance': [15000.0, 25000.0, 18000.0],
        'Purchase Price': [14850.0, 24750.0, 17820.0],
        'Lender Price(%)': [99.0, 99.0, 99.0],
        'modeled_purchase_price': [0.99, 0.99, 0.99],
        'FICO Borrower': [720, 750, 680],
        'DTI': [0.35, 0.40, 0.38],
        'PTI': [0.15, 0.18, 0.16],
        'Income': [60000, 80000, 55000],
        'Term': [120, 144, 120],
        'APR': [7.5, 8.0, 7.8],
        'Property State': ['CA', 'TX', 'FL'],
        'Dealer Fee': [0.05, 0.05, 0.05],
        'Submit Date': pd.to_datetime(['2024-10-15', '2024-10-20', '2024-10-25']),
        'TU144': [0, 0, 1],
    })


@pytest.fixture
def sample_prime_df():
    """Sample Prime dataframe (after normalization)."""
    return pd.DataFrame({
        'SELLER Loan #': ['SFC_1002', 'SFC_1004'],
        'Loan Program': ['Prime Std - 999 - 120', 'Prime Std - 999 - 144'],
        'Application Type': ['STANDARD', 'STANDARD'],
        'Platform': ['PRIME', 'PRIME'],
        'Orig. Balance': [20000.0, 30000.0],
        'Purchase Price': [19800.0, 29700.0],
        'Lender Price(%)': [99.0, 99.0],
        'modeled_purchase_price': [0.99, 0.99],
        'FICO Borrower': [680, 700],
        'DTI': [0.36, 0.42],
        'PTI': [0.16, 0.19],
        'Income': [70000, 90000],
        'Term': [120, 144],
        'APR': [8.5, 9.0],
        'Property State': ['NY', 'IL'],
        'Dealer Fee': [0.05, 0.05],
        'Submit Date': pd.to_datetime(['2024-10-18', '2024-10-22']),
    })


@pytest.fixture
def sample_buy_df(sample_sfy_df, sample_prime_df):
    """Combined buy dataframe."""
    return pd.concat([sample_sfy_df, sample_prime_df], ignore_index=True)


@pytest.fixture
def sample_loans_types_df():
    """Sample loan types master sheet."""
    return pd.DataFrame({
        'loan program': [
            'Unsec Std - 999 - 120',
            'Unsec Std - 999 - 144',
            'Prime Std - 999 - 120',
            'Prime Std - 999 - 144',
            'Unsec Std - 999 - 120notes',
        ],
        'Platform': ['SFY', 'SFY', 'PRIME', 'PRIME', 'SFY'],
        'platform': ['sfy', 'sfy', 'prime', 'prime', 'sfy'],
        'type': ['standard', 'standard', 'standard', 'standard', 'standard'],
    })


@pytest.fixture
def sample_underwriting_df():
    """Sample underwriting grid."""
    return pd.DataFrame({
        'finance_type_name_nls': [
            'Unsec Std - 999 - 120',
            'Unsec Std - 999 - 120',
            'Prime Std - 999 - 120',
            'Prime Std - 999 - 120',
        ],
        'monthly_income_min': [3000, 4000, 3500, 4500],
        'fico_min': [660, 700, 660, 700],
        'approval_high': [20000, 30000, 25000, 35000],
        'approval_low': [5000, 10000, 5000, 10000],
        'dti_max': [45, 50, 45, 50],
        'pti_ratio': [20, 25, 20, 25],
    })


@pytest.fixture
def sample_comap_df():
    """Sample CoMAP grid."""
    return pd.DataFrame({
        '660-699': ['Unsec Std - 999 - 120', 'Prime Std - 999 - 120', None, None],
        '700-739': ['Unsec Std - 999 - 144', 'Prime Std - 999 - 144', None, None],
        '740-749': [None, None, None, None],
        '750-769': [None, None, None, None],
        '770+': [None, None, None, None],
    })


@pytest.fixture
def sample_existing_file():
    """Sample existing assets file."""
    return pd.DataFrame({
        'SELLER Loan #': ['SFC_9999', 'SFC_9998'],
        'Submit Date': pd.to_datetime(['2024-09-15', '2024-09-20']),
        'Purchase_Date': pd.to_datetime(['2024-09-15', '2024-09-20']),
        'Monthly Payment Date': pd.to_datetime(['2024-10-15', '2024-10-20']),
        'Orig. Balance': [15000.0, 20000.0],
        'Purchase Price': [14850.0, 19800.0],
        'Lender Price(%)': [99.0, 99.0],
        'modeled_purchase_price': [0.99, 0.99],
        'platform': ['sfy', 'prime'],
        'Repurchase': [False, False],
    })


# User and sales team fixtures
@pytest.fixture
def sample_sales_team(test_db_session):
    """Create sample sales team."""
    team = SalesTeam(
        name="Test Sales Team",
        description="Test team for unit tests",
        is_active=True
    )
    test_db_session.add(team)
    test_db_session.commit()
    test_db_session.refresh(team)
    return team


@pytest.fixture
def sample_admin_user(test_db_session):
    """Create sample admin user."""
    user = User(
        email="admin@test.com",
        username="admin",
        hashed_password=get_password_hash("testpass"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def sample_sales_user(test_db_session, sample_sales_team):
    """Create sample sales team user."""
    user = User(
        email="sales@test.com",
        username="sales",
        hashed_password=get_password_hash("testpass"),
        full_name="Sales User",
        role=UserRole.SALES_TEAM,
        sales_team_id=sample_sales_team.id,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


# Temporary directory fixture
@pytest.fixture
def temp_dir():
    """Create temporary directory for file operations."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_input_dir(temp_dir):
    """Create sample input directory structure."""
    files_required = temp_dir / "files_required"
    files_required.mkdir(parents=True)
    
    # Create sample files
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%m-%d-%Y')
    
    # Tape loans file
    loans_df = pd.DataFrame({
        'Account Number': [1001, 1002, 1003],
        'Loan Group': ['FX3_GROUP', 'PRIME_GROUP', 'FX1_GROUP'],
        'Status Codes': ['', 'REPURCHASE', ''],
    })
    loans_file = files_required / f"Tape20Loans_{yesterday}.csv"
    loans_df.to_csv(loans_file, index=False)
    
    # SFY file
    sfy_df = pd.DataFrame({
        'Header1': ['', '', '', '', 'SELLER Loan #'],
        'Header2': ['', '', '', '', 'Loan Program'],
        'Data1': ['', '', '', '', 'SFC_1001'],
        'Data2': ['', '', '', '', 'Unsec Std - 999 - 120'],
    })
    sfy_file = files_required / f"SFY_{yesterday}_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx"
    sfy_df.to_excel(sfy_file, index=False)
    
    # Prime file
    prime_df = pd.DataFrame({
        'Header1': ['', '', '', '', 'SELLER Loan #'],
        'Header2': ['', '', '', '', 'Loan Program'],
        'Data1': ['', '', '', '', 'SFC_1002'],
        'Data2': ['', '', '', '', 'Prime Std - 999 - 120'],
    })
    prime_file = files_required / f"PRIME_{yesterday}_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx"
    prime_df.to_excel(prime_file, index=False)
    
    return temp_dir
