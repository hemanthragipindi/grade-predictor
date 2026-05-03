# Nexora: Scalable Academic API & Platform

Nexora is a production-level, API-first academic platform designed for both web and mobile clients. It provides data-driven insights, grade predictions, and secure file management through a robust RESTful architecture.

## 🚀 Key Features

* **API-First Architecture**: RESTful endpoints for all core features (Dashboard, Subjects, Predictions, Files).
* **Hybrid Authentication**: Support for both Session-based (Web) and JWT-based (Mobile) security.
* **Performance Analytics**: Visualized GPA trends and data-driven insights via AcademicBrain.
* **Grade Prediction**: Accuracy-focused grading projections based on continuous assessments.
* **Cloud Drive**: Scalable file storage via Cloudinary with paginated API access.
* **Security Hardened**: Rate limiting, JWT tokens, and strict data isolation for production stability.

## 🛠️ Tech Stack

* **Backend**: Python Flask (Stateless API Design)
* **Auth**: Google OAuth 2.0 / JWT (JSON Web Tokens)
* **Database**: PostgreSQL (Production) / SQLite (Development)
* **Storage**: Cloudinary API
* **Security**: Flask-Limiter, Werkzeug Password Hashing

## 📡 API Reference (JSON)

* `POST /auth/api/login`: Authenticate and receive JWT.
* `GET /api/dashboard`: Retrieve academic overview and insights.
* `GET /api/subjects`: List all tracked subjects.
* `POST /api/upload`: Upload academic documents to Cloud Drive.
* `GET /api/predictions`: Get data-driven grade estimations.

## ▶️ Getting Started

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` with `DATABASE_URL` and API keys.
4. Run: `python backend/app.py`
5. Visit `/auth/` for the web landing page or connect your mobile client to `/api/`.

## 📈 Deployment

Optimized for **Render**. Automatically detects production environment and switches to `ProductionConfig` with PostgreSQL support.
