Here's the updated comprehensive README.md with the Django secret key generation tutorial integrated:

```markdown
# KitoDeck Backend API

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![DRF](https://img.shields.io/badge/Django_REST-ff1709?style=for-the-badge&logo=django&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=JSON%20web%20tokens&logoColor=white)

KitoDeck is a Django REST Framework backend API with JWT authentication, providing user management and data processing capabilities.

## Table of Contents
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Generating a Django Secret Key](#generating-a-django-secret-key)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [License](#license)

## Tech Stack

### Core Technologies
- **Python 3.12**
- **Django 5.1**
- **Django REST Framework**
- **SQLite** (Development)
- **PostgreSQL** (Production)

### Authentication
- **JWT Authentication** using `djangorestframework-simplejwt`
- Custom email/username authentication backend

### Documentation
- **OpenAPI 3.0** via `drf-spectacular`
- Interactive Swagger UI and ReDoc documentation

### Security & Middleware
- **CORS** headers for cross-origin requests
- **CSRF** protection
- **WhiteNoise** for static files

### Email Service
- **SMTP** (Gmail) for email services

## Project Structure

```
kitodeck/
├── api/                      # Main app directory
│   ├── backends.py           # Custom authentication backend
│   ├── urls.py               # App URL routes
│   ├── views.py              # API view functions
│   ├── models.py             # Database models
│   ├── tests.py              # Test cases
│   └── ...
├── kitodeck/                 # Project configuration
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL routes
│   └── ...
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── Procfile                  # Production process file
└── render.yaml               # Render deployment config
```

## Installation

### Prerequisites
- Python 3.12+
- pip
- Virtualenv (recommended)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/codegallantx/kitodeck-be.git
   cd kitodeck-be
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv env
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with the following variables:
   ```
   DJANGO_SECRET_KEY=your-generated-secret-key
   DEBUG=True
   SENDER_EMAIL_HOST_USER=your-email@gmail.com
   SENDER_EMAIL_HOST_PASSWORD=your-app-password
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

## Generating a Django Secret Key

For security reasons, you should never use the default secret key in production. Here's how to generate your own:

### Method 1: Using Python Interactive Shell

1. Open a Python shell:
   ```bash
   python
   ```

2. Run the following code:
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```

3. This will output a random secret key like:
   ```
   'django-insecure-!lbz2veaxjmx#8rihn6q%_i(&m_m78_#b=vv4f7*i%evaz#4el' # Fake
   ```

4. Copy this key and set it as your `DJANGO_SECRET_KEY` in `.env` file.

### Method 2: Using Command Line

Run this command in your terminal:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Method 3: Using Django Management Command

If you already have Django installed:
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Important Security Notes:
1. **Never commit your secret key** to version control
2. **Keep it secret** - treat it like a password
3. **Regenerate it** if you suspect it's been compromised
4. **Use environment variables** (as shown in this project) rather than hardcoding

## Running the Project

### Development Server
```bash
python manage.py runserver
```
The API will be available at `http://localhost:8000/api/`

### Production Server (Gunicorn)
```bash
gunicorn kitodeck.wsgi:application
```

### Accessing Documentation
- Swagger UI: `http://localhost:8000/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/schema/redoc/`

## API Documentation

### Authentication

#### `POST /api/auth/signup/`
Register a new user.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "username": "newuser",
    "email": "user@example.com"
  }
}
```

#### `POST /api/auth/login/`
Authenticate and get JWT tokens.

**Request Body:**
```json
{
  "username": "newuser",  # or email
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### `POST /api/token/refresh/`
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh": "your-refresh-token"
}
```

### User Data

#### `GET /api/user/details/`
Get authenticated user details (requires JWT).

**Headers:**
```
Authorization: Bearer your-access-token
```

**Response:**
```json
{
  "id": 1,
  "username": "newuser",
  "email": "user@example.com"
}
```

### Data Processing

#### `POST /api/process-data/`
Process data (protected endpoint).

**Headers:**
```
Authorization: Bearer your-access-token
```

**Request Body:**
```json
{
  "data": "your-data-to-process"
}
```

**Response:**
```json
{
  "result": "processed-data",
  "status": "success"
}
```

## Deployment

The project includes configuration for deployment to Render:

1. **Database Setup**
   - PostgreSQL database configured in `render.yaml`

2. **Web Service**
   - Gunicorn as application server
   - Automatic static file collection
   - Environment variables configuration

To deploy:
1. Push to your connected repository
2. Render will automatically build and deploy using the `render.yaml` config

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DJANGO_SECRET_KEY` | Secret key for Django | Yes | - |
| `DEBUG` | Debug mode | No | False |
| `SENDER_EMAIL_HOST_USER` | Email for SMTP | Yes | - |
| `SENDER_EMAIL_HOST_PASSWORD` | Email app password | Yes | - |
| `DATABASE_URL` | Database connection URL | Production only | - |

## License

This project is licensed under the MIT License.
```

Key improvements made:
1. Added "Generating a Django Secret Key" as a dedicated section in the table of contents
2. Placed the secret key generation tutorial right after installation and before running the project
3. Maintained all existing content while adding the new section
4. Kept the security warnings prominent
5. Ensured the flow makes logical sense (install → setup secrets → run)
6. Maintained consistent formatting throughout the document

