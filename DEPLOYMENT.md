# Deployment Guide for HRF Newsletter Generator

## Pre-Deployment Checklist ✅

### Security & Configuration
- [x] Removed hardcoded localhost references
- [x] Disabled debug mode for production
- [x] Implemented environment-based configuration
- [x] Secured secret key generation
- [x] Google Cloud credentials handled via environment variables
- [x] All sensitive files properly gitignored

### Environment Variables Required

Create a `.env` file in the project root and configure these variables:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
HOST=0.0.0.0
PORT=10000

# Mailchimp API
MAILCHIMP_API_KEY=your_mailchimp_api_key_here
MAILCHIMP_SERVER_PREFIX=your_server_prefix_here

# Google Cloud Translation
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}

# Security
SECRET_KEY=auto_generated_by_render
```

## Render Deployment Steps

### 1. Repository Setup
```bash
git add .
git commit -m "feat: prepare codebase for production deployment

- Configure environment-based Flask settings
- Implement secure secret key management  
- Add Google Cloud credentials via JSON environment variable
- Remove hardcoded localhost references
- Add deployment configuration files"
git push origin main
```

### 2. Create Render Service
1. Connect your GitHub repository to Render
2. Select "Web Service" 
3. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Environment**: Python 3.11

### 3. Configure Environment Variables
Set these in Render dashboard:
- `MAILCHIMP_API_KEY` - Your Mailchimp API key
- `MAILCHIMP_SERVER_PREFIX` - Your server prefix (e.g., us21)
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Full JSON content of service account file

### 4. Deploy
- Render will automatically deploy on git push
- Monitor logs for any deployment issues
- Test all functionality after deployment

## Production Features
- ✅ Automatic HTTPS
- ✅ Environment-based configuration
- ✅ Secure credential management
- ✅ Production-optimized Flask settings
- ✅ Persistent disk for generated newsletters
- ✅ Auto-scaling capabilities

## Post-Deployment Testing
1. Test newsletter generation workflow
2. Verify Mailchimp image uploads
3. Test translation functionality
4. Confirm template uploads work correctly
