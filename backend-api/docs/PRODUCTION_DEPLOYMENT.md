# 🚀 Bandru API Production Deployment Guide

## 📋 Prerequisites

### System Requirements

- Docker & Docker Compose
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Python 3.11+ (for local development)

### Environment Setup

1. **Copy environment template:**

   ```bash
   cp .env .env.production
   ```

2. **Update `.env.production` with production values:**

   ```bash
   # Database
   DATABASE_URL=postgresql+psycopg2://username:password@prod-db-host:5432/bandaru_pay_prod

   # Security
   SECRET_KEY=your-super-secure-random-key-here

   # Email
   SMTP_USERNAME=your-production-email@bandarupay.com
   SMTP_PASSWORD=your-app-specific-password

   # Cloudinary
   CLOUDINARY_CLOUD_NAME=your-prod-cloud
   CLOUDINARY_API_KEY=your-prod-key
   CLOUDINARY_API_SECRET=your-prod-secret
   ```

## 🐳 Docker Deployment (Recommended)

### Quick Start

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Manual Docker Steps

```bash
# Build image
docker build -t bandru-api:latest .

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Check health
curl http://localhost:8000/health
```

## 🖥️ Manual Deployment

### 1. Database Setup

```sql
-- Create production database
CREATE DATABASE bandaru_pay_prod;
CREATE USER bandaru_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE bandaru_pay_prod TO bandaru_user;
```

### 2. Application Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start application
uvicorn main_production:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔧 Configuration Details

### Environment Variables

| Variable        | Description                     | Required |
| --------------- | ------------------------------- | -------- |
| `DATABASE_URL`  | PostgreSQL connection string    | ✅       |
| `SECRET_KEY`    | JWT signing key                 | ✅       |
| `SMTP_USERNAME` | Email service username          | ✅       |
| `SMTP_PASSWORD` | Email service password          | ✅       |
| `CLOUDINARY_*`  | File upload service credentials | ✅       |
| `REDIS_HOST`    | Redis server host               | ❌       |
| `SENTRY_DSN`    | Error monitoring URL            | ❌       |

### Security Checklist

- [ ] Strong `SECRET_KEY` (64+ random characters)
- [ ] Database credentials secured
- [ ] Email credentials secured
- [ ] Cloudinary credentials secured
- [ ] Redis password set
- [ ] Debug mode disabled (`DEBUG=False`)
- [ ] HTTPS configured (reverse proxy)
- [ ] Firewall configured

## 🌐 Production Services

### Health Check

```bash
curl http://your-domain.com/health
```

### API Documentation

- Available at `/docs` (only if `DEBUG=True`)
- Use API testing tools like Postman for production

### Monitoring

- Health endpoint: `/health`
- Logs: `docker-compose logs api`
- Metrics: Prometheus endpoint (if configured)

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Failed**

   ```bash
   # Check database connectivity
   docker-compose exec db psql -U bandaru_user -d bandaru_pay_prod -c "SELECT 1;"
   ```

2. **Email Service Issues**

   ```bash
   # Test SMTP settings
   python -c "
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email', 'your-password')
   print('SMTP connection successful')
   "
   ```

3. **Container Issues**

   ```bash
   # Restart services
   docker-compose restart

   # Check container logs
   docker-compose logs api

   # Check resource usage
   docker stats
   ```

### Performance Tuning

1. **Database Optimization**

   - Increase connection pool size
   - Enable query optimization
   - Add database indexes

2. **Application Scaling**

   - Increase worker count
   - Use load balancer
   - Enable Redis caching

3. **Resource Limits**
   ```yaml
   # In docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: "1.0"
   ```

## 🔐 Security Best Practices

1. **Use Environment Variables** for all secrets
2. **Enable HTTPS** with SSL certificates
3. **Configure CORS** for specific domains only
4. **Use Strong Passwords** for all services
5. **Regular Security Updates** for dependencies
6. **Monitor Logs** for suspicious activity
7. **Backup Database** regularly

## 📊 Monitoring & Logging

### Application Logs

```bash
# Follow application logs
docker-compose logs -f api

# Check specific time range
docker-compose logs --since="2025-01-01T00:00:00Z" api
```

### Database Monitoring

```bash
# PostgreSQL stats
docker-compose exec db psql -U bandaru_user -d bandaru_pay_prod -c "
SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del
FROM pg_stat_user_tables;
"
```

### Health Monitoring

Set up automated health checks:

```bash
# Add to cron job
*/5 * * * * curl -f http://your-domain.com/health || echo "API Down" | mail -s "Alert" admin@bandarupay.com
```

## 🚨 Backup & Recovery

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U bandaru_user bandaru_pay_prod > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T db psql -U bandaru_user bandaru_pay_prod < backup_20250923.sql
```

### Application Data

```bash
# Backup logs and uploads
tar -czf app_backup_$(date +%Y%m%d).tar.gz logs/ static/
```

## 📞 Support

For deployment issues:

1. Check logs: `docker-compose logs api`
2. Verify environment variables
3. Test database connectivity
4. Check health endpoint
5. Review this documentation

## 🔄 Updates & Maintenance

### Application Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build api
docker-compose up -d api

# Check health
curl http://localhost:8000/health
```

### Database Migrations

```bash
# Run pending migrations
docker-compose exec api alembic upgrade head
```

---

**🎉 Your Bandru API is now production-ready!**

Access your API at: `http://your-domain.com:8000`
