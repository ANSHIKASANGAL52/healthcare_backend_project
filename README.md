# Healthcare Backend System

A robust, production-grade backend system for a healthcare application built using **Django**, **Django REST Framework (DRF)**, **SimpleJWT**, and **PostgreSQL**.

The system enables secure user registration and login with JWT authentication, along with full CRUD capabilities for managing patient records, doctor profiles, and assigning doctors to patients with strict authorization controls, data validation, and uniform error handling.

---

## 🌟 Key Features

- **JWT Authentication**: Secure stateless token authentication (`djangorestframework-simplejwt`) with Bearer tokens for access and refresh token lifecycle.
- **Custom User Model**: Dedicated user model with email-based authentication and name field.
- **Strict Patient Authorization (IDOR Protected)**: Patients are strictly scoped to the user who created them. Users cannot view, update, or delete other users' patient records by changing an ID in the URL.
- **Protected Doctor Management**: Any authenticated user can view the doctor directory, but only the creator of the doctor profile (or staff) can modify or delete doctor records.
- **Secure Patient-Doctor Mapping**: Assign doctors to patients with verification that the authenticated user owns the patient. Prevents duplicate assignments. Viewing assigned doctors (`GET /api/mappings/<patient_id>/`) and deleting mappings (`DELETE /api/mappings/<id>/`) enforce patient ownership.
- **Uniform Error Handling**: Centralized exception handler providing clean, standardized JSON response structures across all HTTP status codes (400, 401, 403, 404, 500).
- **PostgreSQL Database**: Built for PostgreSQL using the official modern `psycopg` driver, configurable via environment variables (`.env`). Includes fallback toggle for local standalone testing.
- **Interactive API Documentation**: Live Swagger UI (`/api/docs/`) and ReDoc (`/api/redoc/`) powered by `drf-spectacular`.
- **Docker Ready**: Pre-configured `docker-compose.yml` and `Dockerfile` for seamless deployment with containerized PostgreSQL 16.
- **Comprehensive Test Suite**: 41 automated unit and integration tests covering authentication, authorization, ownership violations, validation, and CRUD operations.
- **Ready-to-use Postman Collection**: `Healthcare_Backend.postman_collection.json` with pre-configured requests and token capture scripts.

---

## 🏗️ Project Architecture

```
peaceful-shannon/
│
├── apps/
│   ├── accounts/              # CustomUser, Registration, Login & JWT
│   ├── patients/              # Patient records & strict owner-scoped CRUD
│   ├── doctors/               # Doctor directory, owner-protected updates
│   ├── mappings/              # Patient-Doctor relationship mappings with ownership checks
│   └── common/                # Unified exception handler & standard responses
│
├── healthcare_backend/        # Core Django settings, URLs & WSGI
│   ├── settings.py            # Environment-driven configuration & security guards
│   ├── urls.py                # Root routing & Swagger documentation
│   └── ...
│
├── Dockerfile                 # Container specification
├── docker-compose.yml         # Multi-container orchestration (PostgreSQL 16 + Web)
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── .env                       # Local environment configurations (git-ignored)
├── Healthcare_Backend.postman_collection.json # Exported Postman collection
└── README.md                  # Project documentation
```

---

## ⚙️ Prerequisites & Tech Stack

- **Python**: 3.11+ / 3.12+ / 3.14+
- **Django**: 5.1+ / 6.1+
- **Django REST Framework**: 3.15+
- **Database**: PostgreSQL 14+ (or SQLite via `USE_SQLITE=True` for standalone testing)
- **Authentication**: `djangorestframework-simplejwt`
- **Documentation**: `drf-spectacular` (OpenAPI 3.0)

---

## 🚀 Quickstart Guide

### Option 1: Run with Docker Compose (Recommended for PostgreSQL)

Run the backend and PostgreSQL database with a single command:

```bash
docker compose up --build -d
```

- PostgreSQL 16 container initializes automatically with health checks.
- Django applies all migrations and starts on `http://localhost:8000`.
- Interactive Swagger docs: `http://localhost:8000/api/docs/`

To shut down:
```bash
docker compose down -v
```

---

### Option 2: Local Setup with Virtual Environment

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <repo-folder>
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   # On Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

   **PostgreSQL Configuration (`.env`):**
   ```ini
   SECRET_KEY=your-secure-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=healthcare_db
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   DB_HOST=localhost
   DB_PORT=5432
   USE_SQLITE=False
   ```

   *(Note: Set `USE_SQLITE=True` if you wish to run the app immediately without a local PostgreSQL server).*

5. **Apply Database Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser (Optional, for Django Admin)**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```
   Server will start at `http://127.0.0.1:8000/`.

---

## 🔒 Security & Authorization Architecture

### 1. Patient Authorization (IDOR Protection)
- `POST /api/patients/`: Automatically associates `created_by = request.user`.
- `GET /api/patients/`: Strictly filtered to only return patients created by the authenticated user (`created_by=request.user`).
- `GET /api/patients/<id>/`: If a user tries to access a patient ID created by another user, the query returns `404 Not Found`, completely preventing unauthorized reads and ID enumeration.
- `PUT /api/patients/<id>/` & `DELETE /api/patients/<id>/`: Strictly blocked for non-owners.

### 2. Doctor Management Permissions
- `GET /api/doctors/` & `GET /api/doctors/<id>/`: Any authenticated user can view doctors in the directory.
- `POST /api/doctors/`: Any authenticated user can register a doctor (saves `created_by = request.user`).
- `PUT /api/doctors/<id>/` & `DELETE /api/doctors/<id>/`: Only the user who registered that doctor (or staff) can modify or delete it. Attempts by other users return `403 Forbidden`.

### 3. Patient-Doctor Mapping Ownership Checks
- `GET /api/mappings/`: Scoped to mappings for patients created by the authenticated user.
- `POST /api/mappings/`: Verifies that the authenticated user owns the target patient before allowing doctor assignment (returns `403 Forbidden` if unowned). Prevents duplicate doctor assignments to the same patient (`400 Bad Request`).
- `GET /api/mappings/<patient_id>/`: Verifies that the authenticated user owns the patient before returning assigned doctors (returns `403 Forbidden` if unowned).
- `DELETE /api/mappings/<id>/`: Verifies that the authenticated user owns the patient in the mapping before deletion (returns `403 Forbidden` if unowned).

---

## 📚 API Endpoints Reference

### 1. Authentication APIs

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register a new user | No |
| `POST` | `/api/auth/login/` | Log in user & receive JWT tokens | No |

#### Example: Register User (`POST /api/auth/register/`)
**Request Body**:
```json
{
  "name": "Dr. Alice Smith",
  "email": "alice@healthcare.com",
  "password": "StrongPassword123!"
}
```
**Response (201 Created)**:
```json
{
  "success": true,
  "message": "User registered successfully.",
  "data": {
    "user": {
      "id": 1,
      "name": "Dr. Alice Smith",
      "email": "alice@healthcare.com",
      "date_joined": "2026-10-23T10:25:00Z"
    },
    "tokens": {
      "access": "eyJhbGciOiJIUzI1NiIs...",
      "refresh": "eyJhbGciOiJIUzI1NiIs..."
    }
  }
}
```

---

### 2. Patient Management APIs

| Method | Endpoint | Description | Authorization |
|---|---|---|---|
| `POST` | `/api/patients/` | Add a new patient | Authenticated User |
| `GET` | `/api/patients/` | List all patients created by the user | Authenticated User (Scoped) |
| `GET` | `/api/patients/<id>/` | Get details of a specific patient | Patient Owner / Staff |
| `PUT` | `/api/patients/<id>/` | Update patient details | Patient Owner / Staff |
| `DELETE` | `/api/patients/<id>/` | Delete a patient record | Patient Owner / Staff |

---

### 3. Doctor Management APIs

| Method | Endpoint | Description | Authorization |
|---|---|---|---|
| `POST` | `/api/doctors/` | Add a new doctor | Authenticated User |
| `GET` | `/api/doctors/` | Retrieve all doctors | Authenticated User |
| `GET` | `/api/doctors/<id>/` | Get details of a specific doctor | Authenticated User |
| `PUT` | `/api/doctors/<id>/` | Update doctor details | Doctor Creator / Staff |
| `DELETE` | `/api/doctors/<id>/` | Delete a doctor record | Doctor Creator / Staff |

---

### 4. Patient-Doctor Mapping APIs

| Method | Endpoint | Description | Authorization |
|---|---|---|---|
| `POST` | `/api/mappings/` | Assign a doctor to a patient | Patient Owner / Staff |
| `GET` | `/api/mappings/` | Retrieve patient-doctor mappings | Authenticated User (Scoped) |
| `GET` | `/api/mappings/<patient_id>/` | Get all doctors assigned to a patient | Patient Owner / Staff |
| `DELETE` | `/api/mappings/<id>/` | Remove a doctor from a patient | Patient Owner / Staff |

---

## 🧪 Automated Testing

The project includes **41 automated unit and integration tests** covering all positive and negative security/validation paths:

```bash
python manage.py test
```

### Test Coverage Highlights:
- **Authentication (7 tests)**: Registration with valid data, duplicate email rejection, short password validation, login success, invalid password rejection, nonexistent user rejection, inactive user rejection.
- **Patients (11 tests)**: Creation when authenticated, unauthenticated 401 check, validation rules, user-scoped list filtering, owner detail access, **IDOR read prevention (404/403)**, **IDOR update prevention (404/403)**, **IDOR delete prevention (404/403)**, staff access, updating, deleting.
- **Doctors (10 tests)**: Creation with `created_by`, unauthenticated 401 check, duplicate license/email validation, listing all doctors, retrieving details, creator update, **unauthorized user update blocked (403)**, creator delete, **unauthorized user delete blocked (403)**, staff modification and deletion.
- **Patient-Doctor Mappings (13 tests)**: Assigning doctor by owner, flexible key payloads, **assigning doctor to unowned patient blocked (403)**, duplicate assignment rejection (400), unauthenticated check (401), user-scoped list filtering, owner retrieval of assigned doctors, **unowned patient mapping retrieval blocked (403)**, 404 for nonexistent patient, owner mapping deletion, **unauthorized mapping deletion blocked (403)**, 404 for nonexistent mapping, staff management across all mappings.

---

## 📮 Postman Collection Usage

1. Open Postman.
2. Click **Import** and select [`Healthcare_Backend.postman_collection.json`](Healthcare_Backend.postman_collection.json).
3. Set the `base_url` variable (defaults to `http://127.0.0.1:8000`).
4. Execute **1. Register User** or **Login User**:
   - The test script will **automatically capture the `access_token`** and store it in the collection variables!
5. All subsequent requests in `Patients`, `Doctors`, and `Mappings` inherit the Bearer token automatically.
