
# Production-Ready SaaS Application (Software Engineering — Week 4 Major Project)

A full-stack, containerized SaaS Application featuring user authentication, database persistence, REST API endpoints, real-time analytics monitoring, Docker containerization, and automated GitHub Actions CI/CD pipeline.

---

## 📌 Architecture & Features

- **Backend Engine:** FastAPI with Python 3.11.
- **Security & Auth:** JWT authentication with bcrypt password hashing.
- **Database Layer:** SQLAlchemy with SQLite for transactional data.
- **Monitoring & Metrics:** Dedicated `/health` and `/analytics/dashboard` endpoints.
- **Containerization:** Docker container build specs (`Dockerfile`).
- **CI/CD Pipeline:** Automated GitHub Actions build and test suite (`.github/workflows/ci-cd.yml`).
- **Interactive Documentation:** Auto-generated Swagger UI at `/docs`.

---

## 🚀 How to Run Locally

1. **Start Server with Uvicorn:**
   ```bash
   python -m uvicorn main:app --reload
   ```
