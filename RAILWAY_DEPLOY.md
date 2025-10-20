# Railway Deployment Guide

Quick guide to deploy the backend to Railway.

## Files Created

- `Procfile` - Tells Railway how to run the app
- `railway.json` - Railway configuration
- `nixpacks.toml` - Build configuration
- `runtime.txt` - Python version
- `apps/core/health.py` - Health check endpoint

## Environment Variables

Add these in Railway dashboard under Variables:

```
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,your-domain.com
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=from-railway-postgres-plugin
DB_HOST=from-railway-postgres-plugin
DB_PORT=from-railway-postgres-plugin
DB_OPTIONS=sslmode=require
USE_S3=True
AWS_ACCESS_KEY_ID=your-digitalocean-key
AWS_SECRET_ACCESS_KEY=your-digitalocean-secret
AWS_STORAGE_BUCKET_NAME=cekfisi
AWS_S3_REGION_NAME=fra1
AWS_S3_ENDPOINT_URL=https://fra1.digitaloceanspaces.com
AWS_LOCATION=haliyikama
AWS_DEFAULT_ACL=public-read
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
FRONTEND_URL=https://your-frontend.vercel.app
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@haliyikama.com
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
FIREBASE_PROJECT_ID=haliyikama-16cd0
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=your-firebase-email
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=your-number
IYZICO_API_KEY=your-key
IYZICO_SECRET_KEY=your-secret
IYZICO_BASE_URL=https://api.iyzipay.com
STRIPE_PUBLIC_KEY=your-key
STRIPE_SECRET_KEY=your-secret
STRIPE_WEBHOOK_SECRET=your-webhook-secret
```

## Deployment Steps

1. Push code to GitHub
2. Go to Railway dashboard
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Add PostgreSQL plugin
7. Add environment variables from above
8. Railway will auto-deploy

## Post-Deployment

After first deployment:

1. Run migrations (Railway runs this automatically via Procfile)
2. Create superuser:
   ```bash
   railway run python manage.py createsuperuser
   ```
3. Test the health endpoint:
   ```
   https://your-app.railway.app/api/health/
   ```

## Database

Railway provides PostgreSQL. Connection details are automatically injected as environment variables when you add the PostgreSQL plugin.

## Static Files

Static files are collected during build and served via WhiteNoise.

## Monitoring

Check logs in Railway dashboard under "Deployments" → "View Logs"

Health check runs every 30 seconds at `/api/health/`
