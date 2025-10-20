# Database & Storage Migration Guide

## What Changed

### 1. Database: SQLite → PostgreSQL
- Switched from local SQLite to Railway PostgreSQL
- All data is now stored in a production-grade database
- Database connection uses SSL for security

### 2. Media Storage: Local → DigitalOcean Spaces (S3-compatible)
- All uploaded files (images, documents) now stored on DigitalOcean Spaces
- Files are stored in the `haliyikama` folder within the `cekfisi` bucket
- Files are publicly accessible via CDN URL
- Automatic caching with 24-hour cache control

## Configuration

All configuration is done via the `.env` file:

### PostgreSQL Settings
```
DB_NAME=haliyikama
DB_USER=postgres
DB_PASSWORD=bvFjwEEBLCsEYPWWRYWEpwMnvnCyWYKD
DB_HOST=turntable.proxy.rlwy.net
DB_PORT=13557
DB_OPTIONS=sslmode=require
```

### S3/DigitalOcean Spaces Settings
```
USE_S3=True
AWS_ACCESS_KEY_ID=DO00QY49VAUHRE4FMF4Y
AWS_SECRET_ACCESS_KEY=0U1OEdDC/EL2GgM5bgydlG00B68SR71RvSS4Rf1Kado
AWS_STORAGE_BUCKET_NAME=cekfisi
AWS_S3_REGION_NAME=fra1
AWS_S3_ENDPOINT_URL=https://fra1.digitaloceanspaces.com
AWS_LOCATION=haliyikama
AWS_DEFAULT_ACL=public-read
```

## New Dependencies Installed

- `boto3==1.34.51` - AWS SDK for Python
- `django-storages==1.14.2` - Django storage backends for S3

## File Structure on DigitalOcean Spaces

All media files are stored at:
```
https://cekfisi.fra1.digitaloceanspaces.com/haliyikama/[file-path]
```

Example:
- Profile images: `haliyikama/profiles/user_123.jpg`
- Service images: `haliyikama/services/carpet_cleaning.jpg`
- Booking documents: `haliyikama/bookings/invoice_456.pdf`

## Custom Storage Backend

Created `config/storage_backends.py` with `MediaStorage` class that:
- Automatically prefixes all files with `haliyikama/`
- Sets files to public-read by default
- Prevents file overwriting (keeps unique filenames)
- Applies caching headers for better performance

## Database Migration

All migrations have been applied to the PostgreSQL database:
- ✅ User accounts and authentication
- ✅ Services, categories, and pricing
- ✅ Bookings and time slots
- ✅ Payments and transactions
- ✅ Notifications and FCM devices
- ✅ Core settings

Admin user created:
- Email: `admin@haliyikama.com`
- Password: `Admin123`

## Testing Media Upload

To test if S3 upload works:

1. Start the Django server:
   ```bash
   python manage.py runserver
   ```

2. Access admin panel at `http://localhost:8000/admin`

3. Upload an image in any model (e.g., Category icon)

4. Check that the file URL starts with:
   ```
   https://cekfisi.fra1.digitaloceanspaces.com/haliyikama/...
   ```

## Switching Between S3 and Local Storage

To temporarily use local storage (for development):

1. Edit `.env`:
   ```
   USE_S3=False
   ```

2. Restart Django server

Files will now be stored in `backend/media/` locally.

## Security Notes

⚠️ **Production Checklist:**
- Database credentials are secure and use SSL
- S3 access keys are properly configured
- Files are publicly readable (required for web display)
- SECRET_KEY has been regenerated
- `.env` file is in `.gitignore`

## Troubleshooting

### Database Connection Issues
- Verify Railway PostgreSQL is running
- Check firewall/network settings
- Ensure SSL is enabled

### S3 Upload Issues
- Verify DigitalOcean Spaces credentials
- Check bucket permissions
- Ensure CORS is configured if accessing from frontend

### Migration Issues
- Run `python manage.py migrate` to apply any pending migrations
- Check database connection with `python manage.py dbshell`
