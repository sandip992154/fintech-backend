# Nginx Configuration & 502 Bad Gateway Troubleshooting

---

## WHAT NGINX DOES IN YOUR SETUP

```
┌─────────────────────────────────────────────────────────┐
│ User Browser                                             │
│ GET https://backend.bandarupay.pro/api/v1/demo-login    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Cloudflare CDN                                           │
│ (SSL termination)                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Nginx Reverse Proxy                                      │
│ (Forwards request to backend)                            │
└─────────────────────────────────────────────────────────┘
                          ↓
                          ❌ CANNOT REACH BACKEND
                          ↓
        502 Bad Gateway (returned to Cloudflare)
                          ↓
        502 Bad Gateway (returned to user)
```

---

## YOUR NGINX CONFIGURATION (Current)

### Location of Config Files

```bash
# Main config
/etc/nginx/nginx.conf

# Site-specific configs
/etc/nginx/sites-available/backend
/etc/nginx/sites-enabled/backend  # Symlink to above

# If using separate upstream file
/etc/nginx/conf.d/upstream-backend.conf
```

---

## CORRECT NGINX CONFIGURATION

### Configuration File Structure

```bash
# Step 1: Create upstream block
# /etc/nginx/conf.d/upstream-backend.conf
OR
# Inside /etc/nginx/sites-available/backend

# Step 2: Create server block that uses upstream
# /etc/nginx/sites-available/backend

# Step 3: Enable site
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/backend

# Step 4: Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

---

## CORRECT NGINX CONFIGURATION - COMPLETE

### File: `/etc/nginx/sites-available/backend`

```nginx
# ==========================================
# Upstream Block (Backend Server Address)
# ==========================================
upstream backend_app {
    # CRITICAL: Must match the port your backend is listening on
    server 127.0.0.1:8000;
    
    # If backend on different server:
    # server 192.168.1.100:8000;
    
    # If using multiple backends (load balancing):
    # server 127.0.0.1:8000;
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

# ==========================================
# HTTP Block (Redirect to HTTPS)
# ==========================================
server {
    listen 80;
    server_name backend.bandarupay.pro;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

# ==========================================
# HTTPS Block (Main Server Block)
# ==========================================
server {
    listen 443 ssl http2;
    server_name backend.bandarupay.pro;
    
    # ==========================================
    # SSL Configuration
    # ==========================================
    ssl_certificate /etc/letsencrypt/live/backend.bandarupay.pro/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/backend.bandarupay.pro/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # ==========================================
    # Logging
    # ==========================================
    access_log /var/log/nginx/backend-access.log;
    error_log /var/log/nginx/backend-error.log;
    
    # ==========================================
    # Proxy Settings (CRITICAL FOR 502)
    # ==========================================
    
    # Connection timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Buffering
    proxy_buffering on;
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    
    # Version
    proxy_http_version 1.1;
    
    # Keep-alive
    proxy_set_header Connection "";
    
    # ==========================================
    # Headers
    # ==========================================
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $server_name;
    proxy_set_header X-Forwarded-Port $server_port;
    
    # Pass cookies
    proxy_cookie_path / /;
    proxy_cookie_flags ~ secure httponly;
    
    # ==========================================
    # API Routes
    # ==========================================
    
    location /api/v1/ {
        # Forward to upstream
        proxy_pass http://backend_app;
        
        # Debug header (remove in production)
        # add_header X-Upstream-Addr $upstream_addr;
        # add_header X-Upstream-Status $upstream_status;
    }
    
    location /health {
        proxy_pass http://backend_app;
    }
    
    # ==========================================
    # Static Files (if any)
    # ==========================================
    location /static/ {
        alias /var/www/bandarupay/static/;
        expires 30d;
    }
    
    # ==========================================
    # Deny Access to Sensitive Files
    # ==========================================
    location ~ /\. {
        deny all;
    }
    
    location ~ ~$ {
        deny all;
    }
}
```

---

## HOW TO IMPLEMENT THIS CONFIG

### Step 1: Create the File

```bash
# Create/edit the file
sudo nano /etc/nginx/sites-available/backend

# Paste the configuration above (copy everything from "upstream backend_app" to the last closing brace)
```

### Step 2: Enable the Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/backend

# Verify symlink exists
ls -la /etc/nginx/sites-enabled/ | grep backend
```

### Step 3: Test Configuration Syntax

```bash
sudo nginx -t

# Expected output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration will be successful
```

### Step 4: Reload Nginx

```bash
sudo systemctl reload nginx

# Verify status
sudo systemctl status nginx
```

---

## COMMON NGINX MISCONFIGURATIONS CAUSING 502

### ❌ WRONG: Missing Upstream Block

```nginx
# WRONG - no upstream defined
server {
    listen 443 ssl;
    server_name backend.bandarupay.pro;
    
    location /api {
        proxy_pass http://backend_app;  # ❌ backend_app doesn't exist!
    }
}
```

**Fix:** Add upstream block at top:
```nginx
upstream backend_app {
    server 127.0.0.1:8000;
}
```

---

### ❌ WRONG: Wrong Port Number

```nginx
upstream backend_app {
    server 127.0.0.1:8001;  # ❌ Backend is on 8000, not 8001
}
```

**Fix:** Check what port backend is on:
```bash
sudo netstat -tlnp | grep python
# tcp 0 0 127.0.0.1:8000 ← Use this port
```

**Update config:**
```nginx
upstream backend_app {
    server 127.0.0.1:8000;  # ✅ Correct
}
```

---

### ❌ WRONG: Wrong IP Address

```nginx
upstream backend_app {
    server 192.168.1.100:8000;  # ❌ If backend is on localhost
}
```

**Fix:** If backend is on same server as Nginx:
```nginx
upstream backend_app {
    server 127.0.0.1:8000;  # ✅ Localhost
}
```

---

### ❌ WRONG: Missing Proxy Headers

```nginx
location /api {
    proxy_pass http://backend_app;  # ❌ No headers set
}
```

**Fix:** Add required headers:
```nginx
location /api {
    proxy_pass http://backend_app;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

### ❌ WRONG: Timeout Too Short

```nginx
location /api {
    proxy_connect_timeout 1s;  # ❌ Way too short
    proxy_read_timeout 1s;
    proxy_send_timeout 1s;
    proxy_pass http://backend_app;
}
```

**Fix:** Use reasonable timeouts:
```nginx
location /api {
    proxy_connect_timeout 60s;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
    proxy_pass http://backend_app;
}
```

---

### ❌ WRONG: No Buffer Configuration

```nginx
location /api {
    proxy_buffering off;  # ❌ Can cause 502 with large responses
    proxy_pass http://backend_app;
}
```

**Fix:** Enable buffering:
```nginx
location /api {
    proxy_buffering on;
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_pass http://backend_app;
}
```

---

### ❌ WRONG: Multiple Server Blocks Without Upstream

```nginx
# WRONG - Nginx treats them separately
server {
    listen 443 ssl;
    server_name backend.bandarupay.pro;
    location / { proxy_pass http://backend_app; }
}

server {
    listen 443 ssl;
    server_name api.bandarupay.pro;
    location / { proxy_pass http://backend_app; }
}
# upstream block is in different file - not loaded!
```

**Fix:** Make sure upstream block is in /etc/nginx/conf.d/ directory or in the same file before server blocks.

---

## HOW TO DEBUG NGINX CONFIGURATION

### Check If Nginx Loaded Config Correctly

```bash
# Verify Nginx can see the config
sudo nginx -T | grep -A 10 "upstream backend_app"

# Expected output shows your upstream block
```

### Check Nginx Error Logs

```bash
# Real-time error log
tail -f /var/log/nginx/error.log

# Full error log
cat /var/log/nginx/error.log | grep backend

# Look for messages like:
# - "no live upstreams while connecting to upstream"
# - "connect() failed"
# - "502 Bad Gateway"
```

### Check Access Logs

```bash
# See all requests
tail -f /var/log/nginx/backend-access.log

# Format: 
# 203.0.113.42 - - [05/Feb/2026 10:30:45 +0000] "POST /api/v1/demo-login HTTP/1.1" 502 0

# 502 in the status code means proxy couldn't reach backend
```

### Test Upstream Connectivity from Nginx

```bash
# From within the server running Nginx
curl -v http://127.0.0.1:8000/health

# Should work if backend is running
# If "Connection refused", backend is down
```

---

## NGINX CONFIGURATION VALIDATION CHECKLIST

Run through this checklist to validate your config:

```bash
# ✅ 1. Config syntax is valid
sudo nginx -t

# ✅ 2. View entire loaded configuration
sudo nginx -T | head -100

# ✅ 3. Find upstream block
sudo nginx -T | grep -A 5 "upstream"

# ✅ 4. Verify upstream server
sudo nginx -T | grep "server " | head -5

# ✅ 5. Check listening ports
sudo netstat -tlnp | grep nginx

# ✅ 6. Check error log
tail -20 /var/log/nginx/error.log

# ✅ 7. Test locally if backend is reachable
curl http://127.0.0.1:8000/health

# ✅ 8. Test through Nginx
curl http://127.0.0.1/api/v1/health

# ✅ 9. Test from local domain (if DNS works)
curl http://backend.bandarupay.pro/api/v1/health

# ✅ 10. Test from HTTPS (via Cloudflare)
curl https://backend.bandarupay.pro/api/v1/health
```

---

## IF YOU GET 502 EVEN AFTER CHECKING EVERYTHING

### Check Nginx Can Actually Connect

```bash
# Run a test from inside Nginx
sudo -u www-data curl -v http://127.0.0.1:8000/health

# If this fails, it's a network/firewall issue
# If this works, it's a header/configuration issue
```

### Check Backend is Binding to Correct Interface

```bash
# Backend must bind to 127.0.0.1 (localhost) OR 0.0.0.0
netstat -tlnp | grep 8000

# Example outputs:
# tcp 0 0 127.0.0.1:8000 0.0.0.0:* LISTEN 12345/python  ✅ OK
# tcp 0 0 0.0.0.0:8000 0.0.0.0:* LISTEN 12345/python    ✅ OK
# tcp 0 0 192.168.1.100:8000 0.0.0.0:* LISTEN          ✅ OK if Nginx on same subnet
```

If binding to `192.168.1.100` but Nginx can't reach it, it's a network routing issue.

---

## PRODUCTION CHECKLIST

Before going to production, verify:

```bash
# ☑ Backend is running
ps aux | grep main.py

# ☑ Port 8000 is listening
sudo netstat -tlnp | grep 8000

# ☑ Nginx config is valid
sudo nginx -t

# ☑ Upstream block exists
sudo nginx -T | grep -A 3 "upstream backend_app"

# ☑ Timeouts are reasonable (60+ seconds)
sudo nginx -T | grep timeout

# ☑ Buffering is enabled
sudo nginx -T | grep buffer

# ☑ Headers are set
sudo nginx -T | grep "X-Real-IP\|X-Forwarded"

# ☑ SSL is configured correctly
sudo nginx -T | grep ssl_certificate

# ☑ No syntax errors
sudo nginx -t

# ☑ Nginx is running
sudo systemctl status nginx

# ☑ Can connect locally
curl http://127.0.0.1:8000/health

# ☑ Can reach through Nginx
curl http://127.0.0.1/api/v1/health

# ☑ DNS resolves correctly
nslookup backend.bandarupay.pro

# ☑ Can reach from outside
curl https://backend.bandarupay.pro/api/v1/health
```

---

## QUICK FIXES

### Fix 1: Wrong Port in Upstream

```bash
# Check what port backend is on
sudo netstat -tlnp | grep python

# Update config (backup first!)
sudo cp /etc/nginx/sites-available/backend /etc/nginx/sites-available/backend.backup
sudo sed -i 's/server 127.0.0.1:8001/server 127.0.0.1:8000/g' /etc/nginx/sites-available/backend

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Fix 2: Upstream Block Not Loaded

```bash
# Make sure /etc/nginx/conf.d/ directory is included
grep "include /etc/nginx/conf.d/" /etc/nginx/nginx.conf

# If missing, add it to /etc/nginx/nginx.conf:
# http {
#     include /etc/nginx/conf.d/*.conf;
# }
```

### Fix 3: Proxy Headers Missing

```bash
# Add to location block:
sudo cat >> /etc/nginx/sites-available/backend << 'EOF'

# In location block, add:
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
EOF

# Test
sudo nginx -t
sudo systemctl reload nginx
```

---

## REFERENCE: Nginx Proxy Variables

| Variable | Meaning | Example |
|----------|---------|---------|
| `$http_host` | Host header from client | `backend.bandarupay.pro` |
| `$remote_addr` | Client IP | `203.0.113.42` |
| `$proxy_add_x_forwarded_for` | Client IP for proxies | `203.0.113.42, 10.0.0.5` |
| `$scheme` | Protocol (http/https) | `https` |
| `$server_name` | Server name | `backend.bandarupay.pro` |
| `$request_uri` | Full request path | `/api/v1/demo-login?param=value` |
| `$upstream_addr` | Backend server used | `127.0.0.1:8000` |
| `$upstream_status` | Backend response code | `200, 401, 500` |
