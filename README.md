# Healthcare Backend System

A robust, production-grade backend system for a healthcare application built using **Django**, **Django REST Framework (DRF)**, **SimpleJWT**, and **PostgreSQL**.

The system enables secure user registration and login with JWT authentication, along with full CRUD capabilities for managing patient records, doctor profiles, and assigning doctors to patients with validation and security controls.

---

## 🌟 Key Features

- **JWT Authentication**: Secure stateless token authentication (`djangorestframework-simplejwt`) with Bearer tokens for access and refresh rotation.
- **Custom User Model**: Dedicated user model with email-based authentication and full name fields.
- **Patient Management**: User-scoped patient records ensuring authenticated users only manage their own patients.
- **Doctor Management**: Complete cataloging of medical specialists with unique license verification and contact tracking.
- **Patient-Doctor Mapping**: Assign doctors to patients with duplicate-assignment prevention, retrieval of all doctors assigned to a patient, and mapping deletion.
- **Uniform Error Handling**: Centralized exception handler providing clean, standardized JSON response structures across all HTTP status codes.
- **PostgreSQL Database**: Configured for PostgreSQL 16+ using the official modern `psycopg` driver, with environment variable overrides.
- **Interactive API Documentation**: Live Swagger UI (`/api/docs/`) and ReDoc (`/api/redoc/`) powered by `drf-spectacular`.
- **Docker Ready**: Pre-configured `docker-compose.yml` and `Dockerfile` for seamless deployment with containerized PostgreSQL.
- **Comprehensive Test Suite**: 29 automated unit and integration tests covering authentication, authorization, validation, and CRUD operations.
- **Ready-to-use Postman Collection**: `Healthcare_Backend.postman_collection.json` with pre-configured requests and token capture scripts.

---

## 🏗️ Project Architecture

```
peaceful-shannon/
│
├── apps/
│   ├── accounts/              # CustomUser, Registration, Login & JWT
│   ├── patients/              # Patient records & user-isolated CRUD
│   ├── doctors/               # Doctor directory & validation
│   ├── mappings/              # Patient-Doctor relationship mappings
│   └── common/                # Unified exception handler & helpers
│
├── healthcare_backend/        # Core Django settings, URLs & WSGI
│   ├── settings.py            # Environment-driven configuration
│   ├── urls.py                # Root routing & Swagger documentation
│   └── ...
│
├── Dockerfile                 # Container specification
├── docker-compose.yml         # Multi-container orchestration (PostgreSQL + Web)
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── .env                       # Local environment configurations
├── Healthcare_Backend.postman_collection.json # Exported Postman collection
└── README.md                  # Project documentation
```

---

## ⚙️ Prerequisites & Tech Stack

- **Python**: 3.11+ / 3.12+ / 3.14+
- **Django**: 5.1+ / 6.1+
- **Django REST Framework**: 3.15+
- **Database**: PostgreSQL 14+ (or SQLite for standalone evaluation)
- **Authentication**: `djangorestframework-simplejwt`
- **Documentation**: `drf-spectacular` (OpenAPI 3.0)

---

## 🚀 Quickstart Guide

### Option 1: Run with Docker Compose (Recommended for PostgreSQL)

Run the backend and PostgreSQL database with a single command:

```bash
docker compose up --build -d
```

- PostgreSQL container initializes automatically with health checks.
- Django runs migrations and starts on `http://localhost:8000`.
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
   ```bash
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

#### Example: Login User (`POST /api/auth/login/`)
**Request Body**:
```json
{
  "email": "alice@healthcare.com",
  "password": "StrongPassword123!"
}
```
**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "user": {
      "id": 1,
      "name": "Dr. Alice Smith",
      "email": "alice@healthcare.com"
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

> [!NOTE]
> All patient endpoints require header: `Authorization: Bearer <access_token>`.
> `GET /api/patients/` automatically filters and returns only patients created by the authenticated user.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/patients/` | Add a new patient | Yes |
| `GET` | `/api/patients/` | List all patients created by the user | Yes |
| `GET` | `/api/patients/<id>/` | Get details of a specific patient | Yes |
| `PUT` | `/api/patients/<id>/` | Update patient details | Yes |
| `DELETE` | `/api/patients/<id>/` | Delete a patient record | Yes |

#### Example: Add Patient (`POST /api/patients/`)
**Request Body**:
```json
{
  "name": "John Doe",
  "age": 38,
  "gender": "Male",
  "contact_number": "+1-555-0199",
  "email": "john.doe@example.com",
  "address": "742 Evergreen Terrace",
  "medical_history": "Mild hypertension, seasonal allergies"
}
```
**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Patient created successfully.",
  "data": {
    "id": 1,
    "name": "John Doe",
    "age": 38,
    "gender": "Male",
    "contact_number": "+1-555-0199",
    "email": "john.doe@example.com",
    "address": "742 Evergreen Terrace",
    "medical_history": "Mild hypertension, seasonal allergies",
    "created_by": 1,
    "created_by_name": "Dr. Alice Smith",
    "created_by_email": "alice@healthcare.com",
    "created_at": "2026-10-23T10:30:00Z",
    "updated_at": "2026-10-23T10:30:00Z"
  }
}
```

---

### 3. Doctor Management APIs

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/doctors/` | Add a new doctor | Yes |
| `GET` | `/api/doctors/` | Retrieve all doctors | Yes |
| `GET` | `/api/doctors/<id>/` | Get details of a specific doctor | Yes |
| `PUT` | `/api/doctors/<id>/` | Update doctor details | Yes |
| `DELETE` | `/api/doctors/<id>/` | Delete a doctor record | Yes |

#### Example: Add Doctor (`POST /api/doctors/`)
**Request Body**:
```json
{
  "name": "Gregory House",
  "specialization": "Diagnostic Medicine",
  "license_number": "MED-NY-84920",
  "phone": "+1-555-0100",
  "email": "house@princetonplainsboro.org",
  "experience_years": 20
}
```
**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Doctor registered successfully.",
  "data": {
    "id": 1,
    "name": "Gregory House",
    "specialization": "Diagnostic Medicine",
    "license_number": "MED-NY-84920",
    "phone": "+1-555-0100",
    "email": "house@princetonplainsboro.org",
    "experience_years": 20,
    "created_at": "2026-10-23T10:32:00Z",
    "updated_at": "2026-10-23T10:32:00Z"
  }
}
```

---

### 4. Patient-Doctor Mapping APIs

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/mappings/` | Assign a doctor to a patient | Yes |
| `GET` | `/api/mappings/` | Retrieve all patient-doctor mappings | Yes |
| `GET` | `/api/mappings/<patient_id>/` | Get all doctors assigned to a patient | Yes |
| `DELETE` | `/api/mappings/<id>/` | Remove a doctor from a patient (by mapping ID) | Yes |

#### Example: Assign Doctor (`POST /api/mappings/`)
**Request Body**:
```json
{
  "patient_id": 1,
  "doctor_id": 1,
  "notes": "Assigned for diagnostic evaluation and treatment protocol."
}
```
*(Accepts either `patient_id` / `doctor_id` or `patient` / `doctor`).*

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Doctor assigned to patient successfully.",
  "data": {
    "id": 1,
    "patient": {
      "id": 1,
      "name": "John Doe",
      "age": 38,
      "gender": "Male"
    },
    "doctor": {
      "id": 1,
      "name": "Gregory House",
      "specialization": "Diagnostic Medicine"
    },
    "assigned_date": "2026-10-23T10:35:00Z",
    "notes": "Assigned for diagnostic evaluation and treatment protocol."
  }
}
```

#### Example: Get Doctors for Patient (`GET /api/mappings/1/`)
**Response (200 OK)**:
```json
{
  "success": true,
  "patient_id": 1,
  "patient_name": "John Doe",
  "count": 1,
  "data": [
    {
      "id": 1,
      "patient": { ... },
      "doctor": {
        "id": 1,
        "name": "Gregory House",
        "specialization": "Diagnostic Medicine",
        "email": "house@princetonplainsboro.org"
      },
      "assigned_date": "2026-10-23T10:35:00Z",
      "notes": "Assigned for diagnostic evaluation and treatment protocol."
    }
  ]
}
```

#### Example: Remove Mapping (`DELETE /api/mappings/1/`)
**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Doctor removed from patient successfully."
}
```

---

## 🧪 Automated Testing

The project includes 29 unit and integration tests covering all critical paths:

```bash
python manage.py test
```

### Test Coverage Highlights:
- **Authentication**: Registration with valid/invalid data, email normalization, uniqueness validation, password length checks, login token issuance, incorrect password rejection.
- **Patients**: Creation with JWT token, unauthenticated 401 blocking, input validations (age range, phone), user-level isolation in list endpoint, detail retrieval, updating, deleting.
- **Doctors**: Creation, duplicate license/email rejection, listing all doctors, retrieving details, update, delete.
- **Patient-Doctor Mappings**: Assigning doctors, preventing duplicate assignments to the same patient, unauthenticated access blocking, listing all mappings, querying assigned doctors by patient ID, 404 on missing patient, mapping deletion by ID.

---

## 📮 Postman Collection Usage

1. Open Postman.
2. Click **Import** and select the file `Healthcare_Backend.postman_collection.json`.
3. Set the `base_url` variable (defaults to `http://127.0.0.1:8000`).
4. Execute **1. Register User** or **Login User**:
   - The test script will **automatically capture the `access_token`** and store it in the collection variables!
5. All subsequent requests in the `Patients`, `Doctors`, and `Mappings` folders inherit the token automatically.

---

## 🔒 Security Best Practices Implemented

- Passwords securely hashed with Django's PBKDF2 algorithm.
- Environment variables for `SECRET_KEY`, database credentials, and token lifetimes.
- `IsAuthenticated` default permission class with explicit `AllowAny` only on auth endpoints.
- Object-level ownership validation for patient records.
- SQL injection protection via Django ORM parameterized queries.
- Database constraints (`UniqueConstraint`) preventing duplicate doctor-patient assignments.
