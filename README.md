# Public Shop 🛍️

[![CI Pipeline](https://github.com/YOUR_USERNAME/public-shop/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/public-shop/actions/workflows/ci.yml)
[![Security Scan](https://github.com/YOUR_USERNAME/public-shop/actions/workflows/security-scan.yml/badge.svg)](https://github.com/YOUR_USERNAME/public-shop/actions/workflows/security-scan.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A modern, secure, and scalable social marketplace web application built with Flask and deployed on Azure.

## ✨ Features

### Core Functionality
- 🔐 **User Authentication** - Secure registration with email verification
- 📝 **Social Feed** - Share posts and stories with the community
- 🏪 **Marketplace** - Create and browse listings with categories
- 💬 **Real-time Messaging** - WebSocket-powered chat system
- 👥 **Social Features** - Follow users, view profiles
- 🔍 **Advanced Search** - Find users and listings easily
- 🎁 **Free Listings** - Support for giveaways and free items

### Technical Features
- ⚡ **High Performance** - Redis caching and optimized queries
- 🔒 **Security First** - CSRF protection, rate limiting, security headers
- 📊 **Monitoring** - Application Insights integration
- 🐳 **Containerized** - Docker support for easy deployment
- 🚀 **CI/CD** - Automated testing and deployment
- 🏗️ **Infrastructure as Code** - Terraform for Azure resources

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask 3.1.2
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15 (SQLite for development)
- **Cache**: Redis 7
- **WSGI Server**: Gunicorn with Eventlet workers
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic (Flask-Migrate)

### Frontend
- **UI Framework**: Bootstrap 5
- **Template Engine**: Jinja2
- **Real-time**: Socket.IO

### Infrastructure
- **Cloud Provider**: Microsoft Azure
- **Container Platform**: Azure Container Instances
- **Container Registry**: Azure Container Registry
- **Monitoring**: Application Insights
- **Secrets Management**: Azure Key Vault
- **Storage**: Azure Blob Storage
- **IaC**: Terraform

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- Redis (for caching and rate limiting)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd public-shop
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
flask db upgrade
```

6. Run development server:
```bash
python run.py
```

### Docker

```bash
docker-compose up -d
```

## Environment Variables

Required environment variables (see `.env.example`):

- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - PostgreSQL connection string
- `MAIL_USERNAME` / `MAIL_PASSWORD` - Email configuration
- `RATELIMIT_STORAGE_URL` - Redis URL for rate limiting
- `CACHE_REDIS_URL` - Redis URL for caching

## Production Deployment

הפרויקט כולל תשתית מלאה לפריסה ב-Azure עם Terraform ו-CI/CD pipeline.

### 📚 תיעוד פריסה

**כל התיעוד נמצא בתיקייה [`docs/`](docs/)**

- **[מדריך התיעוד המלא](docs/INDEX.md)** - נקודת התחלה לכל התיעוד
- **[התחלה מהירה](docs/terraform/START-HERE.md)** - קרא את זה קודם!
- **[הגדרת Azure](docs/AZURE-SETUP.md)** - הגדרת Azure CLI ו-Service Principal
- **[פריסה עם Terraform](docs/DEPLOYMENT.md)** - הוראות מפורטות לפריסת התשתית
- **[שלבי פריסה](docs/DEPLOYMENT-STEPS.md)** - מדריך שלב אחר שלב
- **[פתרון בעיות](docs/TROUBLESHOOTING.md)** - פתרון בעיות נפוצות

### 🚀 התחלה מהירה

1. קרא את [START-HERE](docs/terraform/START-HERE.md) - נקודת ההתחלה
2. הגדר [Azure](docs/AZURE-SETUP.md) עם Service Principal
3. פרוס עם [Terraform](docs/terraform/QUICK-START.md)
4. הגדר [CI/CD](docs/CI-CD.md) ל-GitHub Actions

### 🏗️ משאבי Azure

לאחר הפריסה, המשאבים הבאים ייווצרו:
- **Azure Container Instances (ACI)** - Application, PostgreSQL, Redis
- **Azure Container Registry (ACR)** - Docker images
- **Azure Key Vault** - Secrets management
- **Application Insights** - Monitoring
- **Storage Account** - File storage

לפרטים נוספים, ראה [תיעוד התשתית](docs/INFRASTRUCTURE.md)

## 📊 Project Structure

```
public-shop/
├── app/                    # Application code
│   ├── routes/            # Route blueprints
│   ├── templates/         # Jinja2 templates
│   ├── static/            # Static files
│   ├── models.py          # Database models
│   ├── config.py          # Configuration
│   └── utils.py           # Utility functions
├── infrastructure/        # Infrastructure as Code
│   ├── terraform/         # Terraform configurations
│   └── scripts/           # Deployment scripts
├── tests/                 # Test suite
├── migrations/            # Database migrations
├── docs/                  # Documentation
└── .github/workflows/     # CI/CD pipelines
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📖 Documentation

- **[Architecture](ARCHITECTURE.md)** - System architecture and design
- **[Contributing](CONTRIBUTING.md)** - Contribution guidelines
- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[Changelog](CHANGELOG.md)** - Version history
- **[Docs Folder](docs/)** - Complete documentation

## 🔒 Security

- Security headers (CSP, HSTS, X-Frame-Options)
- CSRF protection
- Rate limiting
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (Jinja2 auto-escaping)
- Secure password hashing (PBKDF2)
- Regular security scanning (Trivy, Bandit, Gitleaks)

For security issues, please see [SECURITY.md](SECURITY.md) or contact security@example.com

## 📈 Monitoring & Observability

- Application Insights for performance monitoring
- Automated alerts for critical metrics
- Centralized logging with Log Analytics
- Health check endpoints
- Error tracking and reporting

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run linting
flake8 app/
black --check app/
isort --check-only app/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- Flask and its amazing ecosystem
- Azure for cloud infrastructure
- All contributors and maintainers

## 📞 Support

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/public-shop/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/YOUR_USERNAME/public-shop/discussions)

---

Made with ❤️ by the Public Shop team


