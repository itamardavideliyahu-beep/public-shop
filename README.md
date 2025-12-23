# Public Shop

A social marketplace web application built with Flask.

## Features

- User authentication with email verification
- Social feed with posts and stories
- Marketplace listings with categories
- Private messaging system
- User profiles and following system
- Real-time chat with WebSockets

## Tech Stack

- **Backend**: Flask 3.1.2, Python 3.11+
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache**: Redis
- **Web Server**: Gunicorn
- **Frontend**: Bootstrap 5

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

## License

[Your License Here]


