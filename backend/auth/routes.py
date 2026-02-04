"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from db.connection import get_db
from db.models import User, UserRole, SalesTeam
from auth.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_role
)
from auth.validators import (
    validate_sales_team_assignment,
    validate_user_update,
    get_user_sales_team_id
)
from auth.audit import log_user_action
from config.settings import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    user: dict


class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    username: str
    password: str
    full_name: str
    role: UserRole = UserRole.ANALYST
    sales_team_id: int | None = None


class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    username: str
    full_name: str | None
    role: UserRole
    sales_team_id: int | None
    is_active: bool
    
    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token."""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    # Log successful login
    log_user_action('login', user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "sales_team_id": user.sales_team_id
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Register a new user (admin only)."""
    # Check if user already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Validate sales team assignment
    validate_sales_team_assignment(user_data.role, user_data.sales_team_id, db)
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        sales_team_id=user_data.sales_team_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log user creation
    log_user_action('create_user', current_user, target_user_id=db_user.id, details={
        'new_user_role': db_user.role.value,
        'new_user_sales_team_id': db_user.sales_team_id
    })
    
    return db_user


class UserUpdate(BaseModel):
    """User update model."""
    email: EmailStr | None = None
    username: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    sales_team_id: int | None = None
    is_active: bool | None = None
    password: str | None = None


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update a user (admin only)."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate update
    validate_user_update(
        user_id,
        user_data.role,
        user_data.sales_team_id,
        current_user,
        db
    )
    
    # Validate sales team assignment if role is being changed
    if user_data.role is not None:
        validate_sales_team_assignment(user_data.role, user_data.sales_team_id, db)
    
    # Update fields
    if user_data.email is not None:
        # Check if email is already taken by another user
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = user_data.email
    
    if user_data.username is not None:
        # Check if username is already taken by another user
        existing = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        db_user.username = user_data.username
    
    if user_data.full_name is not None:
        db_user.full_name = user_data.full_name
    
    if user_data.role is not None:
        db_user.role = user_data.role
    
    if user_data.sales_team_id is not None:
        db_user.sales_team_id = user_data.sales_team_id
    
    if user_data.is_active is not None:
        db_user.is_active = user_data.is_active
    
    if user_data.password is not None:
        db_user.hashed_password = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(db_user)
    
    # Log user update
    log_user_action('update_user', current_user, target_user_id=user_id, details={
        'updated_fields': {k: v for k, v in user_data.dict(exclude_unset=True).items() if k != 'password'}
    })
    
    return db_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: UserRole | None = None,
    sales_team_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """List all users (admin only)."""
    query = db.query(User)
    
    if role is not None:
        query = query.filter(User.role == role)
    
    if sales_team_id is not None:
        query = query.filter(User.sales_team_id == sales_team_id)
    
    users = query.offset(skip).limit(limit).all()
    return users
