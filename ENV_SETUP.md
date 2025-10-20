# Environment Configuration

This project uses **python-decouple** to manage environment variables through a `.env` file.

## How it works

The `settings.py` file uses `from decouple import config` which automatically:
1. Reads from `.env` file in the backend directory
2. Falls back to environment variables if `.env` doesn't exist
3. Uses default values if neither is found

## Setup Instructions

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Generate a secure SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   
3. **Update `.env` file with your values:**
   - Replace `SECRET_KEY` with the generated key
   - Configure your database settings
   - Add API keys for payment gateways (Iyzico/Stripe)
   - Configure email/SMS settings
   - Add Firebase credentials for push notifications

## Configuration Variables

### Django Core
- `SECRET_KEY` - Django secret key (REQUIRED - must be unique and secret)
- `DEBUG` - Debug mode (default: True)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

### Database
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

### JWT Authentication
- `JWT_ACCESS_TOKEN_LIFETIME` - Access token lifetime in minutes (default: 60)
- `JWT_REFRESH_TOKEN_LIFETIME` - Refresh token lifetime in minutes (default: 1440)

### CORS
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed origins

### Redis & Celery
- `REDIS_URL` - Redis connection URL
- `CELERY_BROKER_URL` - Celery broker URL
- `CELERY_RESULT_BACKEND` - Celery result backend URL

### Email
- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`

### SMS (Twilio)
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

### Payment Gateways
#### Iyzico
- `IYZICO_API_KEY`, `IYZICO_SECRET_KEY`, `IYZICO_BASE_URL`

#### Stripe
- `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

### Firebase (Push Notifications)
- `FIREBASE_PROJECT_ID`
- `FIREBASE_PRIVATE_KEY` - Private key from Firebase service account
- `FIREBASE_CLIENT_EMAIL`

### Frontend
- `FRONTEND_URL` - Frontend application URL

## Security Notes

⚠️ **NEVER commit `.env` file to version control**

The `.env` file contains sensitive information and is already listed in `.gitignore`.

✅ **DO commit `.env.example`** 

This serves as a template for other developers.

## Why python-decouple?

- **Separation of config from code** - 12-factor app principle
- **Type casting** - Automatic conversion (e.g., `cast=bool`, `cast=int`)
- **Default values** - Fallback values for development
- **No need to modify settings.py** - All config in one place

## Current Setup Status

✅ `.env` file exists and is being used
✅ `python-decouple` is installed
✅ All settings are loaded from environment variables
✅ Secure SECRET_KEY has been generated
