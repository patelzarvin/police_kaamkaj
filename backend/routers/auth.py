from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
import datetime

from backend.database import get_db
from backend.models import User
from backend.schemas import Token, UserLogin, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = "super_secret_jwt_key_change_in_production_gujarat_police_2026"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: datetime.timedelta = datetime.timedelta(hours=8)):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Allow default fallback admin login if DB is freshly created
    if not user and form_data.username == "admin" and form_data.password == "police123":
        user_info = {
            "username": "admin",
            "full_name": "Commandant S. K. Sharma",
            "role": "COMMANDER",
            "department": "Gujarat Police SCRB"
        }
        token = create_access_token(user_info)
        return {"access_token": token, "token_type": "bearer", "user_info": user_info}

    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_info = {
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "department": user.department
    }
    token = create_access_token({"sub": user.username, **user_info})
    return {"access_token": token, "token_type": "bearer", "user_info": user_info}

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub") or payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token claims")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT signature")

    stmt = select(User).where(User.username == username)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        # Fallback admin response for dev
        return UserResponse(
            id=1,
            email="admin@sentinel.police.gujarat.gov.in",
            username="admin",
            full_name="Commandant S. K. Sharma",
            department="Gujarat Police SCRB",
            role="COMMANDER",
            is_active=True
        )
    return user
