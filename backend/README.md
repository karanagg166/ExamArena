# 🎓 ExamArena Backend API

Complete backend API for ExamArena exam platform built with **FastAPI**, **Prisma ORM**, and **PostgreSQL**.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Setup & Installation](#setup--installation)
5. [Environment Variables](#environment-variables)
6. [Running the Server](#running-the-server)
7. [API Endpoints](#api-endpoints)
8. [Authentication Flow](#authentication-flow)
9. [Adding New Features](#adding-new-features)
10. [Code Examples](#code-examples)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

ExamArena backend provides:
- 🔐 **Secure Authentication** - JWT tokens in HttpOnly cookies
- 👤 **User Management** - Signup, Login, Logout, Get Profile
- 🔒 **Password Security** - bcrypt hashing
- 📡 **RESTful API** - Clean endpoints with proper HTTP methods
- 🗄️ **Database Integration** - Prisma ORM with PostgreSQL
- 📝 **Type Safety** - Full TypeScript-like experience with Python type hints

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Web Framework** | FastAPI | 0.110.0 |
| **Server** | Uvicorn | 0.27.1 |
| **ORM** | Prisma | 0.13.1 |
| **Database** | PostgreSQL | 12+ |
| **Validation** | Pydantic | 2.6.4 |
| **Authentication** | python-jose | 3.3.0 |
| **Password Hashing** | passlib + bcrypt | 1.7.4 |
| **Environment** | python-dotenv | 1.0.1 |

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py                    # Package initialization
│   ├── main.py                        # FastAPI app & middleware setup
│   │
│   ├── core/                          # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py                  # Environment variables (validated)
│   │   └── security.py                # JWT & password hashing functions
│   │
│   ├── api/                           # API routes
│   │   ├── __init__.py
│   │   └── v1/                        # API version 1
│   │       ├── __init__.py
│   │       ├── dependencies.py        # Reusable dependencies (auth, DB)
│   │       └── endpoints/             # Route handlers
│   │           ├── __init__.py
│   │           └── auth.py            # Authentication endpoints
│   │
│   ├── schemas/                       # Pydantic request/response models
│   │   ├── __init__.py
│   │   └── user.py                    # User schemas
│   │
│   ├── crud/                          # Database operations
│   │   ├── __init__.py
│   │   └── user.py                    # User CRUD operations
│   │
│   ├── db/                            # Database models (reference only)
│   │   └── models/
│   │       └── user.py                # Prisma User model
│   │
│   └── utils/ (future)                # Utility functions
│
├── .env                               # Environment variables (never commit!)
├── .env.example                       # Example environment variables
├── .gitignore                         # Git ignore rules
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
└── Dockerfile (future)                # Docker configuration
```

### Folder Organization Explained

| Folder | Purpose | Example |
|--------|---------|---------|
| **core/** | Core app settings and logic | Config loading, JWT creation |
| **api/v1/endpoints/** | Route definitions | `/auth`, `/exams`, `/results` |
| **api/v1/dependencies.py** | Reusable dependency injection | Current user authentication |
| **schemas/** | Request/Response validation | LoginRequest, UserResponse |
| **crud/** | Database CRUD operations | Create user, Get user by ID |

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/karanagg166/ExamArena.git
cd ExamArena/backend
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env` with your actual values (see [Environment Variables](#environment-variables))

### Step 5: Setup Database

Ensure PostgreSQL is running, then:

```bash
# From root project directory
cd ..  # Go to ExamArena root
npx prisma migrate dev --name init
```

This creates the database schema defined in `prisma/schema.prisma`

---

## ⚙️ Environment Variables

### Critical Variables (Must be set, or app fails to start)

```bash
# SECRET_KEY - Used for JWT encryption
# Minimum 32 characters, use a strong random key
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-super-secret-key-min-32-chars-change-in-production

# DATABASE_URL - PostgreSQL connection string
# Format: postgresql://username:password@host:port/database
DATABASE_URL=postgresql://postgres:password@localhost:5432/examarena

# JWT Algorithm
ALGORITHM=HS256

# Token expiration time in minutes
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Optional Variables (Have defaults)

```bash
# Environment type (affects security features)
ENVIRONMENT=development  # Set to "production" for secure cookies

# Allowed frontend origins for CORS
ALLOWED_ORIGINS=http://localhost:3000
```

### Example `.env` File

```
# Authentication
SECRET_KEY=your-secret-key-here-32-chars-min
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/examarena

# Environment
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000
```

### Security Notes

⚠️ **Critical:**
- Never commit `.env` to Git
- Change `SECRET_KEY` in production to a strong random value
- Use environment-specific `.env` files (`.env.production`)
- `.env` is in `.gitignore` for safety

---

## ▶️ Running the Server

### Development Mode (with auto-reload)

```bash
cd backend
uvicorn app.main:app --reload
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Application startup complete
```

### Production Mode (without auto-reload)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Access the API

- **API Documentation (Swagger UI):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **Root Endpoint:** http://localhost:8000/
- **Health Check:** http://localhost:8000/health

---

## 📚 API Endpoints

### Base URL

```
http://localhost:8000/api/v1/auth
```

### 1. Signup (Register New User)

**Request:**
```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "student@example.com",
  "fullName": "John Doe",
  "password": "securePassword123!"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "student@example.com",
  "fullName": "John Doe",
  "role": "student"
}
```

**Sets Cookie:**
```
access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (HttpOnly, Secure, SameSite=Lax)
```

**Error Cases:**
- `400` - Email already registered
- `422` - Invalid data (email format, missing fields)

---

### 2. Login

**Request:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "securePassword123!"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "student@example.com",
  "fullName": "John Doe",
  "role": "student"
}
```

**Sets Cookie:**
```
access_token=<JWT_TOKEN> (HttpOnly, Secure in production)
```

**Error Cases:**
- `401` - Invalid email or password
- `422` - Invalid email format

---

### 3. Get Current User

**Request:**
```http
GET /api/v1/auth/me
Cookie: access_token=<JWT_TOKEN>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "student@example.com",
  "fullName": "John Doe",
  "role": "student"
}
```

**Error Cases:**
- `401` - Not authenticated (no token)
- `401` - Invalid/expired token
- `404` - User not found

---

### 4. Logout

**Request:**
```http
POST /api/v1/auth/logout
Cookie: access_token=<JWT_TOKEN>
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

**Clears Cookie:**
```
access_token= (empty, max_age=0)
```

---

## 🔐 Authentication Flow

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                      │
└─────────────────────────────────────────────────────────────┘

1. SIGNUP/LOGIN
   ┌──────────┐                    ┌────────────┐
   │ Frontend │ ──POST email/pass→ │  Backend   │
   │ (React)  │                    │ (FastAPI)  │
   └──────────┘                    └────────────┘
                                        ↓
                                  ┌─────────────┐
                                  │ Validate    │
                                  │ Hash        │
                                  │ Password    │
                                  └─────────────┘
                                        ↓
                                  ┌─────────────┐
                                  │ Create JWT  │
                                  │ Token:      │
                                  │ {           │
                                  │  sub: 1,    │
                                  │  exp: ...   │
                                  │ }           │
                                  └─────────────┘
                                        ↓
   ┌──────────┐ ← Set Cookie ─ ┌────────────┐
   │ Browser  │               │  Backend   │
   │ Storage  │               │ (response) │
   └──────────┘               └────────────┘
        ↓
   Cookie: access_token=<JWT>
   (HttpOnly - safe from XSS!)

2. AUTHENTICATED REQUESTS
   ┌──────────┐              ┌────────────┐
   │ Frontend │ ─GET /me─→   │  Backend   │
   │          │ (auto send)  │            │
   └──────────┘ ←token in──   └────────────┘
                   cookie         ↓
                              ┌─────────────┐
                              │ Verify JWT  │
                              │ Extract     │
                              │ user_id     │
                              └─────────────┘
                                   ↓
                              ┌─────────────┐
                              │ Get user    │
                              │ from DB     │
                              └─────────────┘
                                   ↓
                         ┌──────────────────┐
                         │ Return user data │
                         └──────────────────┘
```

### Key Points

1. **Token Storage** - JWT stored in HttpOnly cookie (secure, XSS-proof)
2. **Auto Sending** - Browser automatically sends cookie with each request
3. **Token Verification** - Backend verifies JWT signature on each request
4. **Token Expiry** - Token expires in 30 minutes (configurable)
5. **Security** - Cookie marked as Secure in production (HTTPS only)

---

## 🔧 Core Modules Explained

### `app/core/config.py`

Loads and validates environment variables:

```python
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
```

**What it does:**
- Loads `.env` file using `python-dotenv`
- Validates critical variables are set
- Provides sensible defaults for optional variables
- Raises errors early if required vars missing

### `app/core/security.py`

Handles authentication logic:

```python
from app.core.security import (
    hash_password,      # Hash plain passwords with bcrypt
    verify_password,    # Check password against hash
    create_access_token,# Generate JWT token
    verify_token        # Validate and decode JWT
)
```

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `hash_password(pwd)` | Converts plain password to bcrypt hash |
| `verify_password(plain, hashed)` | Checks if plain password matches |
| `create_access_token(user_id)` | Creates JWT token valid for 30 min |
| `verify_token(token)` | Extracts user_id from token |

### `app/schemas/user.py`

Defines request/response data structures:

```python
from app.schemas.user import LoginRequest, SignupRequest, UserResponse
```

**Models:**

```python
class LoginRequest:
    email: str      # Must be valid email
    password: str   # Any string

class SignupRequest:
    email: str      # Must be valid email
    fullName: str   # Any string
    password: str   # Any string

class UserResponse:
    id: int         # Auto from DB
    email: str
    fullName: str
    role: str       # "student", "teacher", "admin"
```

**Why Pydantic?**
- ✅ Auto validation (email format, type checking)
- ✅ Auto conversion (string → int)
- ✅ Clear error messages
- ✅ Auto API documentation

### `app/crud/user.py`

Database operations:

```python
from app.crud.user import (
    get_user_by_email,    # Find user by email
    get_user_by_id,       # Find user by ID
    create_user           # Create new user
)
```

**These functions abstract Prisma queries:**

```python
# Instead of:
user = await prisma.user.find_unique(where={"email": email})

# Use:
user = await get_user_by_email(email)  # Cleaner!
```

### `app/api/v1/dependencies.py`

Reusable authentication dependency:

```python
from app.api.v1.dependencies import get_current_user

@router.get("/me")
async def get_profile(current_user = Depends(get_current_user)):
    return current_user
```

**What it does:**
- Extracts token from cookie
- Verifies token validity
- Gets user from DB
- Returns user or raises 401 error

---

## ✨ Adding New Features

### Example: Add Exam Endpoints

#### Step 1: Create Schema

Create `app/schemas/exam.py`:

```python
from pydantic import BaseModel
from typing import Optional

class ExamCreate(BaseModel):
    title: str
    description: str
    duration_minutes: int

class ExamResponse(BaseModel):
    id: int
    title: str
    description: str
    duration_minutes: int
    
    class Config:
        from_attributes = True
```

#### Step 2: Create CRUD

Create `app/crud/exam.py`:

```python
from app.core.security import hash_password

async def create_exam(title: str, description: str, duration_minutes: int, created_by: int):
    return await prisma.exam.create(
        data={
            "title": title,
            "description": description,
            "duration_minutes": duration_minutes,
            "created_by": created_by
        }
    )

async def get_exam_by_id(exam_id: int):
    return await prisma.exam.find_unique(where={"id": exam_id})

async def get_all_exams():
    return await prisma.exam.find_many()
```

#### Step 3: Create Endpoints

Create `app/api/v1/endpoints/exam.py`:

```python
from fastapi import APIRouter, Depends
from app.schemas.exam import ExamCreate, ExamResponse
from app.crud.exam import create_exam, get_all_exams
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/exams", tags=["exams"])

@router.post("/", response_model=ExamResponse)
async def create_new_exam(
    exam: ExamCreate,
    current_user = Depends(get_current_user)
):
    return await create_exam(
        title=exam.title,
        description=exam.description,
        duration_minutes=exam.duration_minutes,
        created_by=current_user.id
    )

@router.get("/", response_model=list[ExamResponse])
async def list_exams(current_user = Depends(get_current_user)):
    return await get_all_exams()
```

#### Step 4: Include Router

Update `app/main.py`:

```python
from app.api.v1.endpoints import auth, exam

app.include_router(auth.router)
app.include_router(exam.router)  # Add this
```

#### Step 5: Update Prisma Schema

Update `prisma/schema.prisma`:

```prisma
model Exam {
  id                Int      @id @default(autoincrement())
  title             String
  description       String
  duration_minutes  Int
  created_by        Int
  user              User     @relation(fields: [created_by], references: [id])
  created_at        DateTime @default(now())
  updated_at        DateTime @updatedAt
}
```

Then migrate:

```bash
npx prisma migrate dev --name add_exam_model
```

Done! New exam endpoints ready to use! 🎉

---

## 💡 Code Examples

### Example 1: Call Protected Endpoint

**Frontend (TypeScript/React):**

```typescript
// Token automatically in cookie!
const response = await fetch('http://localhost:8000/api/v1/auth/me', {
  credentials: 'include'  // Send cookies
});
const user = await response.json();
console.log(user);
```

### Example 2: Login Flow

**Frontend:**

```typescript
const handleLogin = async (email: string, password: string) => {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify({ email, password })
  });
  
  if (response.ok) {
    const user = await response.json();
    // Token is already in cookie, no need to store!
    router.push('/dashboard');
  }
};
```

### Example 3: Test with cURL

```bash
# Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","fullName":"Test User","password":"pass123"}' \
  -c cookies.txt

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}' \
  -c cookies.txt

# Get current user (using same cookie jar)
curl -X GET http://localhost:8000/api/v1/auth/me \
  -b cookies.txt

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -b cookies.txt
```

---

## 🎯 Best Practices

### 1. Always Use Pydantic Schemas

```python
# ❌ DON'T
@router.post("/users")
async def create(data: dict):
    # No validation!
    return await prisma.user.create(data=data)

# ✅ DO
@router.post("/users", response_model=UserResponse)
async def create(user: UserCreate):
    # Auto validates, cleaner API docs
    return await crud_create_user(...)
```

### 2. Use Dependencies for Auth

```python
# ❌ DON'T
@router.get("/me")
async def get_user(request):
    # Repeated auth logic in every endpoint
    token = request.cookies.get("access_token")
    # ... validate token, get user, etc.

# ✅ DO
@router.get("/me")
async def get_user(current_user = Depends(get_current_user)):
    # Reusable & DRY
    return current_user
```

### 3. Separate Concerns

```
❌ BAD:
app/
  endpoints.py (2000 lines - routes, DB, validation, auth all mixed)

✅ GOOD:
app/
  api/v1/endpoints/
    auth.py (routes only)
  crud/
    user.py (DB operations)
  schemas/
    user.py (validation)
  core/
    security.py (auth logic)
```

### 4. Use Environment Variables

```python
# ❌ DON'T
SECRET_KEY = "hardcoded-key"  # Exposed in Git!

# ✅ DO
from app.core.config import SECRET_KEY  # From .env
```

### 5. Proper Error Handling

```python
# ❌ DON'T
try:
    user = await get_user_by_email(email)
except:
    pass  # Silently fail

# ✅ DO
try:
    user = await get_user_by_email(email)
except Exception as e:
    raise HTTPException(status_code=500, detail="Database error")
```

---

## 🐛 Troubleshooting

### Issue: "SECRET_KEY environment variable not set!"

**Solution:**
```bash
# Create .env file
cp .env.example .env

# Edit .env and add:
SECRET_KEY=your-secret-key-here
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
```

### Issue: "DATABASE_URL environment variable not set!"

**Solution:**
```bash
# Add to .env:
DATABASE_URL=postgresql://postgres:password@localhost:5432/examarena

# Make sure PostgreSQL is running
# Test connection: psql postgresql://postgres:password@localhost:5432/examarena
```

### Issue: Module not found errors

**Solution:**
```bash
# Reinstall requirements
pip install -r requirements.txt

# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Use different port
uvicorn app.main:app --port 8001

# Or find and kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: CORS errors from frontend

**Solution:**
Update `.env`:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

Restart server and check that frontend URL is in ALLOWED_ORIGINS.

---

## 📖 Quick Reference

### Start Development Server

```bash
cd backend
uvicorn app.main:app --reload
```

### Check API Documentation

```
http://localhost:8000/docs
```

### Add New Endpoint

1. Create schema in `schemas/`
2. Create CRUD in `crud/`
3. Create endpoint in `api/v1/endpoints/`
4. Include router in `main.py`

### Test Endpoint (Swagger)

1. Go to http://localhost:8000/docs
2. Expand endpoint
3. Click "Try it out"
4. Enter data
5. Click "Execute"

---

## 📞 Support

For issues or questions:
- Check error message in terminal
- See [Troubleshooting](#troubleshooting) section
- Check [Swagger Docs](http://localhost:8000/docs) for endpoint details
- Review code comments in relevant files

---

## 🔄 Development Workflow

```
1. Create feature branch
   git checkout -b feature/new-feature

2. Make changes following structure

3. Test with Swagger UI or cURL

4. Commit
   git add .
   git commit -m "Add new feature"

5. Push
   git push origin feature/new-feature

6. Create PR on GitHub
```

---

**Happy Coding! 🚀**

---

## ⚙️ Environment Variable Validation

### Critical Variables (Must be set)
- `SECRET_KEY` - JWT encryption key
- `ALGORITHM` - JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration
- `DATABASE_URL` - PostgreSQL connection string

If any critical variable is missing, the app will raise an error and refuse to start.

### Optional Variables (Have defaults)
- `ENVIRONMENT` - default: "development"
- `ALLOWED_ORIGINS` - default: "http://localhost:3000"

---

## 🔒 Security Features

✅ **HttpOnly Cookies** - JWT stored securely in cookies  
✅ **Password Hashing** - bcrypt for password encryption  
✅ **JWT Tokens** - Secure token-based authentication  
✅ **CORS Protection** - Configurable allowed origins  
✅ **Environment Validation** - Critical variables must be set  

---

## 🧪 Test Endpoints

### Using Swagger UI
Open: `http://localhost:8000/docs`

### Using cURL
```bash
# Login
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' \
  -c cookies.txt

# Get current user
curl -X GET "http://localhost:8000/api/v1/me" \
  -b cookies.txt

# Logout
curl -X POST "http://localhost:8000/api/v1/logout" \
  -b cookies.txt
```

---

## 🛠️ Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `prisma` | Database ORM |
| `pydantic` | Data validation |
| `python-jose` | JWT tokens |
| `passlib` | Password hashing |
| `python-dotenv` | Environment variables |

---

## ⚠️ Important Notes

1. **Never commit `.env` file** - It contains secrets!
2. **Change `SECRET_KEY` in production** - Use a strong, random key
3. **Use HTTPS in production** - Set `ENVIRONMENT=production`
4. **Database must be running** - Before starting the server
