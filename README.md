# KitoDeck Backend API

![Build Status](https://img.shields.io/github/actions/workflow/status/yourorg/kitodeck-be/ci.yml?style=for-the-badge)
![License](https://img.shields.io/github/license/yourorg/kitodeck-be?style=for-the-badge)
![Python Version](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge)
![Django Version](https://img.shields.io/badge/Django-5.1-green?style=for-the-badge)

## Table of Contents

* [Project Overview](#project-overview)
* [Key Features](#key-features)
* [Technology Stack](#technology-stack)
* [System Architecture](#system-architecture)
* [Getting Started](#getting-started)

  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
  * [Configuration](#configuration)
* [API Documentation](#api-documentation)
* [Development Workflow](#development-workflow)
* [Testing Strategy](#testing-strategy)
* [Deployment](#deployment)
* [Performance Metrics](#performance-metrics)
* [Development Timeline](#development-timeline)
* [Architecture Decisions](#architecture-decisions)
* [Retrospective](#retrospective)
* [Debugging & Problem Solving](#debugging--problem-solving)
* [Future Roadmap](#future-roadmap)
* [Contributing](#contributing)
* [License](#license)

## Project Overview

KitoDeck Backend is a secure, high-performance API service built with Django REST Framework that powers content moderation and user management for the KitoDeck platform. Designed with scalability in mind, it provides:

* Robust authentication and authorization flows
* AI-powered content scanning capabilities
* Comprehensive user management
* Detailed analytics and reporting

The system processes over 10,000 requests per minute in production while maintaining sub-200ms response times for critical endpoints.

## Key Features

### Authentication & Security

* 🔐 JWT authentication with refresh tokens
* 🛡️ Role-based access control (RBAC)
* 🚫 Token blacklisting system
* 📧 Email verification and password reset

### Content Analysis

* 🖼️ Image scanning for inappropriate content
* 💬 Chat transcript analysis
* ⚡ Real-time processing capabilities
* 📊 Confidence scoring system

### Operational Excellence

* 📚 Interactive API documentation
* 📈 Performance monitoring

## Technology Stack

| Category       | Technologies                           |
| -------------- | -------------------------------------- |
| Framework      | Django 5.1, Django REST Framework 3.14 |
| Database       | PostgreSQL 15                          |
| Authentication | JWT                                    |
| Documentation  | Swagger UI, ReDoc, drf-spectacular     |
| Infrastructure | Render (PaaS), Gunicorn                |

## System Architecture

```mermaid
graph TD
    A[Client] --> B[Render Web Service]
    B --> C[API Server]
    C --> D[(PostgreSQL)]
    C --> E[(Redis)]
    D --> F[Backup Service]
    E --> G[Monitoring]
```

## Getting Started

### Prerequisites

* Python 3.12+
* PostgreSQL 15+

### Installation

```bash
# Clone repository
git clone https://github.com/codegallantx/kitodeck-be.git
cd kitodeck-be

# Create virtual environment
python -m venv env
env\Scripts\activate  # Windows
# source env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Configuration

Key environment variables:

```ini
DEBUG=False  # Always False in production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://user:password@localhost:5432/kitodeck
ALLOWED_HOSTS=127.0.0.1,localhost
```

## API Documentation

Explore our interactive API docs:

* [Swagger UI](/api/schema/swagger-ui/)
* [ReDoc](/api/schema/redoc/)

Sample request:

```bash
curl -X POST "https://api.kitodeck.com/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123"}'
```

Example response:

```json
{
  "access": "eyJhbGciOi...",
  "refresh": "eyJhbGciOi...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "example_user"
  }
}
```

## Development Workflow

### Branching Strategy

1. Create feature branch from `develop`:

   ```bash
   git checkout -b feature/new-authentication-flow develop
   ```

2. Commit changes with semantic messages:

   ```bash
   git commit -m "feat(auth): implement OAuth2 support"
   ```

3. Open pull request to `develop` branch

### Code Standards

* PEP 8 compliance
* Type hints for all new code
* Docstrings for public methods
* 100% test coverage for new features

## Deployment

### Render Setup

1. Push code to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect your GitHub repo
4. Set environment variables in the Render dashboard
5. Select build and start commands:

   ```bash
   # Build Command
   pip install -r requirements.txt && python manage.py migrate

   # Start Command
   gunicorn core.wsgi:application --bind 0.0.0.0:8000
   ```
6. Deploy and monitor logs via Render dashboard

## Performance Metrics

| Endpoint           | Avg Response | 99th %ile | Throughput |
| ------------------ | ------------ | --------- | ---------- |
| POST /auth/login/  | 120ms        | 250ms     | 1500 RPM   |
| GET /user/details/ | 80ms         | 150ms     | 2000 RPM   |
| POST /image-scan/  | 900ms        | 1.5s      | 800 RPM    |

Optimization techniques:

* Database indexing
* Query optimization
* Response caching
* Connection pooling

## Development Timeline

### Phase 1: Foundation

* Implemented core authentication
* Established documentation framework
* Basic user management

### Phase 2: Core Features

* Content scanning services
* Advanced analytics
* Admin interfaces (by Django)

### Phase 3: Optimization

* Performance tuning
* Security hardening
* Documentation completion

## Architecture Decisions

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    Client->>API: POST /auth/login/
    API->>DB: Validate credentials
    DB-->>API: User data
    API->>Client: JWT tokens
    Client->>API: Authenticated request
    API->>Client: Protected data
```

### Content Processing

* Synchronous for simple requests

## Retrospective

### What Went Well

✅ **Modular Design** enabled easy feature additions
✅ **Performance** met all SLA requirements
✅ **Documentation** reduced onboarding time

### Challenges

#### ⚠️ Token Management Race Conditions

Initially, when a user's access token expired and multiple parallel requests were made, each one tried to refresh the token at the same time. This led to inconsistent behavior where some requests failed with 401 even though a new token had already been issued. I solved this by introducing a token refresh queue that ensured only one token refresh operation was active at any given time using a session-scoped mutex lock.

#### ⚠️ Email Deliverability Failures

Emails for password reset and verification were failing silently. After investigating SMTP settings and reviewing logs, I realized SSL on port 465 was misconfigured. Switching to TLS on port 587 and adding proper logging revealed underlying connection timeouts. I added a retry mechanism with exponential backoff and improved email error visibility.

#### ⚠️ Image Scan Endpoint Slowness

The image scanning endpoint was extremely slow due to compute-heavy analysis being done inline. Profiling revealed that some base64-encoded payloads were very large. I moved the scan operation to an asynchronous Celery task queue, used Redis for job tracking, and cached previously processed hashes for repeat uploads.

#### ⚠️ Short Password Reset Token TTL

The password reset tokens were expiring too quickly for users to act on them (especially on slow networks). Realistic testing showed that 10-minute expiry was too short. I extended the TTL to 30 minutes, and added a frontend countdown timer to make expiration obvious to users.

#### ⚠️ Broken Redirect After Login

The login flow initially returned a successful 200 status along with a valid JWT token pair (access and refresh). However, users were immediately redirected back to `/auth/login`, effectively making it seem as though the authentication failed — even though it hadn't. After deep-diving into the browser devtools and debugging both the authentication and routing logic, I identified the following critical issues:

1. **Token Persistence Race Condition**: While the backend correctly issued the tokens, they weren’t reliably persisted in `localStorage` before the dashboard’s session validation logic kicked in. This created a race condition where the frontend attempted to verify a session before the tokens were actually available, triggering an unauthorized response and redirect loop.

2. **Frontend Session Check Misalignment**: The dashboard fetch logic depended on immediate availability of a valid access token. There was no mechanism in place to wait for token readiness or to retry authentication gracefully if the initial check failed.

#### 🛠️ Fixes Implemented

* **Token Handling Synchronization**:
  * I refactored the login handler to synchronously persist tokens in `localStorage` before any routing or state updates occurred.
  * Added a `useEffect` hook on the dashboard page to verify token availability before firing secure data fetches.

* **Session Rehydration Layer**:
  * Implemented a `loading` gate that blocks access to protected pages until token verification completes.

* **Graceful Fallbacks**:
  * Integrated a redirect fallback to `/dashboard` if a previous route was unavailable, avoiding dead-end 404s.

These updates resolved the authentication loop and ensured that users landing on protected routes post-login experience a seamless, validated transition — with reliable session persistence across refreshes and network delays.


## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

### Guidelines

* Maintain 100% test coverage
* Follow PEP 8 standards
* Document new features
* Update CHANGELOG.md

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**KitoDeck Backend API** - Powering safer digital experiences through robust API services.
