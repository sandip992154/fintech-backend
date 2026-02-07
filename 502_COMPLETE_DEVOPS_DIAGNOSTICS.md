# 502 Bad Gateway - Complete DevOps Diagnostics

**Error:** `502 Bad Gateway` on `https://backend.bandarupay.pro/api/v1/demo-login`

**What This Means:** The reverse proxy (Nginx/Cloudflare) received your request but could not reach your backend Python application to process it.

---

## IMMEDIATE ACTION (First 5 Minutes)

### Step 1: SSH to Backend Server

```bash
ssh user@your-backend-server

# Navigate to project
cd /path/to/backend-api

# Check if backend is running
ps aux | grep "python main.py" | grep -v grep
```

**If you see a process line** → Go to Step 2  
**If you see nothing** → Backend is DOWN, jump to SECTION: "START BACKEND"

---

### Step 2: Verify Port is Listening

```bash
sudo netstat -tlnp | grep 8000

# Expected: tcp 0 0 127.0.0.1:8000 0.0.0.0:* LISTEN <PID>/python
```

**If you see LISTEN** → Go to Step 3  
**If you see nothing** → Backend crashed, jump to SECTION: "START BACKEND"

---

### Step 3: Test Local Connectivity

```bash
curl -v http://localhost:8000/api/v1/demo-login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

**Expected:** Any HTTP response (200, 401, 500, etc.) with response body

**If you get response** → Nginx is misconfigured, go to SECTION: "VERIFY NGINX"  
**If Connection refused** → Backend has a critical issue, go to SECTION: "DEBUG BACKEND"  
**If Timeout** → Backend is hanging, go to SECTION: "BACKEND HANGING"

---

## SECTION A: VERIFY NGINX CONFIGURATION

This section assumes backend IS running locally and works when you curl it directly.

### Check 1: Nginx Syntax

```bash
sudo nginx -t

# Expected:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration will be successful
```

**If OK** → Go to Check 2  
**If errors** → Fix the errors shown and re-test

---

### Check 2: View Nginx Upstream Configuration

```bash
# Find the upstream block
sudo nginx -T | grep -A 10 "upstream backend"

# OR view the config file directly
sudo cat /etc/nginx/sites-enabled/backend | grep -A 10 "upstream"
```

**Expected Output:**
```nginx
upstream backend_app {
    server 127.0.0.1:8000;
}
```

**CRITICAL CHECKS:**
- Is the IP correct? (Should be 127.0.0.1 if on same server, or your server IP if remote)
- Is the port correct? (Should match what `netstat` showed - usually 8000)
- Does the upstream block exist?

**If incorrect** → Fix the config (see NGINX_CONFIGURATION_502_GUIDE.md), then:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

**If correct** → Go to Check 3

---

### Check 3: Test Through Nginx Locally

```bash
# Test going through Nginx instead of directly to backend
curl -v http://127.0.0.1/api/v1/demo-login \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Host: backend.bandarupay.pro" \
  -d '{"username":"test","password":"test"}'
```

**If works** → The issue is HTTPS/SSL (Cloudflare), go to Check 4  
**If fails** → Something wrong with Nginx config, review Check 2

---

### Check 4: View Nginx Error Logs

```bash
# See last 50 lines of errors
sudo tail -50 /var/log/nginx/error.log

# Watch in real-time
sudo tail -f /var/log/nginx/error.log

# In another terminal, trigger error
curl http://127.0.0.1/api/v1/demo-login -X POST

# Watch for error messages
```

**Look for errors like:**
- `connect() failed` → Backend not reachable
- `upstream timed out` → Backend hanging
- `no live upstreams` → Wrong upstream config
- `DNS resolution failed` → DNS issue

---

### Check 5: View Access Logs

```bash
# See all requests to backend
sudo tail -50 /var/log/nginx/backend-access.log

# Or if in main access log:
sudo tail -50 /var/log/nginx/access.log | grep "api/v1"

# Watch for 502s:
sudo tail -f /var/log/nginx/access.log | grep " 502 "
```

**Log Format:**
```
203.0.113.42 - - [05/Feb/2026 10:30:45 +0000] "POST /api/v1/demo-login HTTP/2.0" 502 173
```

If you see 502s here, trace back to NGINX errors from Check 4.

---

## SECTION B: DEBUG BACKEND APPLICATION

If backend is running but curl http://localhost:8000 fails:

### Check 1: View Application Logs

```bash
# Last 100 lines
tail -100 /var/log/bandarupay/app.log

# Real-time
tail -f /var/log/bandarupay/app.log

# If using systemd:
sudo journalctl -u bandarupay-backend -n 100
sudo journalctl -u bandarupay-backend -f
```

**Look for:**
- Exceptions in the logs
- Port conflict messages
- Database connection errors
- Import errors

---

### Check 2: Backend Binding Interface

```bash
# Check EXACTLY what interface backend is bound to
sudo netstat -tlnp | grep 8000

# Output analysis:
# tcp 0 0 127.0.0.1:8000 0.0.0.0:* LISTEN      ✅ OK (localhost only)
# tcp 0 0 0.0.0.0:8000 0.0.0.0:* LISTEN        ✅ OK (all interfaces)
# tcp 0 0 192.168.1.100:8000 0.0.0.0:* LISTEN  ❓ Only if on that subnet
```

**If bound to 192.168.x.x or similar:**
- Nginx on same subnet → Verify IP is correct in upstream
- Nginx on different server → Use that IP in upstream

---

### Check 3: Try Direct Requests with Strace

```bash
# Run backend in foreground to see startup messages
cd /path/to/backend-api
source venv/bin/activate

# Run with debug output
python main.py

# Watch for:
# INFO: Uvicorn running on http://127.0.0.1:8000
# Any error messages before that
```

**Common startup errors:**
- `Address already in use` → Kill process on port 8000
- `ModuleNotFoundError` → Run `pip install -r requirements.txt`
- `FileNotFoundError` → Config file missing
- `Database connection error` → Database not running

---

### Check 4: Check Port Conflicts

```bash
# See what's using port 8000
sudo lsof -i :8000

# Output:
# COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
# python 12345 user 5u IPv4 0x1234 0t0 TCP 127.0.0.1:8000 (LISTEN)
#
# OR maybe another process:
# java 54321 root 45u IPv4 0x5678 0t0 TCP 127.0.0.1:8000 (LISTEN)

# If wrong process, kill it
sudo kill -9 54321
```

---

### Check 5: Verify Database Connectivity

```bash
# Check if database is running
# For PostgreSQL:
pg_isready -h localhost -p 5432

# For MySQL:
mysqladmin ping -u root -p

# If DB not running, start it
sudo systemctl start postgresql
sudo systemctl start mysql
```

If app logs show DB errors, this is likely your issue.

---

## SECTION C: BACKEND HANGING OR SLOW RESPONSE

If curl http://localhost:8000 times out:

### Check 1: Is Process CPU Bound?

```bash
# See process status
ps aux | grep main.py | grep -v grep

# Output format:
# USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
# user 123  0.0  2.5  450000 50000 ? Sl 10:30 0:05 python main.py

# If %CPU is high (>50%), backend is busy computing
# If %MEM is high (>90%), might be memory pressure
```

**If high CPU:**
- Normal if processing lots of data
- Check if there's an infinite loop in code
- Check if database query is slow
- Run profiler: `python -m cProfile main.py`

**If high memory:**
- Memory leak likely
- Check app logs for error messages
- Restart backend: `kill -9 <PID>`, then start again

---

### Check 2: Check Database Query Performance

```bash
# If using PostgreSQL, check slow queries:
sudo -u postgres psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# For MySQL:
mysql> SET GLOBAL slow_query_log = 'ON';
mysql> SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;
```

If a query is taking seconds, that's your issue. Optimize the query.

---

### Check 3: Check Connection Pool

```bash
# Count database connections from backend
# For PostgreSQL:
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='bandarupay';"

# If many connections, could be connection pool leak
# Check app code for proper connection closing
```

---

## SECTION D: START BACKEND (If Not Running)

### Method 1: Direct Start (Development)

```bash
# Navigate to backend
cd /path/to/backend-api

# Activate environment
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\Activate.ps1  # Windows

# Run backend
python main.py

# Expected:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# If you see errors, read them carefully
```

**Keep terminal open** to see logs while testing.

---

### Method 2: Systemd Service (Production)

```bash
# Check service status
sudo systemctl status bandarupay-backend

# If not running:
sudo systemctl start bandarupay-backend

# Watch status
sudo systemctl status bandarupay-backend

# Watch logs
sudo journalctl -u bandarupay-backend -f
```

**If service fails to start:**
```bash
# Check for errors
sudo journalctl -u bandarupay-backend -n 50 --no-pager

# Check service file
sudo cat /etc/systemd/system/bandarupay-backend.service

# Common issues:
# - ExecStart path wrong
# - User doesn't have permission
# - WorkingDirectory wrong
# - Environment variables missing
```

---

### Method 3: Docker Container

```bash
# List containers
docker ps -a

# Check if backend container exists
docker ps -a | grep backend

# If not running, start it
docker-compose up -d backend

# Watch logs
docker logs -f <container-name>

# If fails to start:
docker logs <container-name> | tail -50
```

---

## SECTION E: CHECK SYSTEM RESOURCES

### Memory Issues

```bash
# Check overall memory
free -h

# Output:
#               total        used        free      shared  buff/cache   available
# Mem:           16Gi        14Gi       500Mi       100Mi        1.5Gi       1.2Gi
#                         ↑ If used is 90%+, you're out of memory

# Check what's using memory
ps aux --sort=-%mem | head -10

# If backend process using >5GB, it has a memory leak
```

**Fix:**
```bash
# Restart backend
pkill -9 -f "python main.py"

# Clear cache
sync; echo 3 > /proc/sys/vm/drop_caches

# Start again
python main.py
```

### Disk Issues

```bash
# Check disk space
df -h

# If /var is >90% full, logs might be filling disk
df -h /var

# Clear old logs
sudo journalctl --vacuum=10d

# Check what's using space
du -sh /var/log/*
```

### CPU Issues

```bash
# Real-time CPU usage
top -b -n 1 | head -20

# If high CPU from backend:
# 1. Check if query is slow
# 2. Check if infinite loop in code
# 3. Profile the app
```

---

## SECTION F: FIREWALL AND NETWORK

### Check Firewall Rules

```bash
# UFW (Ubuntu)
sudo ufw status
sudo ufw status verbose | grep 8000

# IPTables
sudo iptables -L -n | grep 8000

# If port 8000 is blocked:
sudo ufw allow 8000
# OR
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
```

### Check Port is Actually Open

```bash
# From backend server
nc -zv localhost 8000

# From another server (if checking remote backend)
nc -zv <backend-ip> 8000

# If connection refused, backend not listening
```

---

## SECTION G: CLOUDFLARE / HTTPS ISSUES

If local tests work (curl http://localhost works, curl through nginx works) but HTTPS fails:

### Check Cloudflare Configuration

```bash
# Verify DNS points to your server
nslookup backend.bandarupay.pro
dig backend.bandarupay.pro

# Should show your server's IP
```

### Check SSL Certificate

```bash
# View certificate
openssl s_client -connect backend.bandarupay.pro:443

# Check expiration
openssl x509 -dates -noout -in /etc/letsencrypt/live/backend.bandarupay.pro/cert.pem

# If expired, renew
sudo certbot renew --quiet
```

### Check Cloudflare SSL Settings

In Cloudflare dashboard:
1. Go to SSL/TLS settings
2. Ensure SSL/TLS encryption mode is "Full" or "Full (Strict)"
3. Not "Flexible" (that causes issues)

---

## MASTER CHECKLIST: Run Everything in Order

Copy and run each command, verify success before moving to next:

```bash
# ===============================
# PHASE 1: Backend Status (1 min)
# ===============================
echo "=== 1. Is backend running? ==="
ps aux | grep "python main.py" | grep -v grep || echo "❌ NOT RUNNING"

echo "=== 2. Is port listening? ==="
sudo netstat -tlnp | grep 8000 || echo "❌ NOT LISTENING"

echo "=== 3. Can curl localhost:8000? ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/health || echo "❌ FAILED"

# ===============================
# PHASE 2: Nginx Config (2 min)
# ===============================
echo "=== 4. Nginx syntax OK? ==="
sudo nginx -t 2>&1 | grep "ok" || echo "❌ CONFIG ERROR"

echo "=== 5. Upstream block present? ==="
sudo nginx -T | grep -A 3 "upstream backend" || echo "❌ MISSING"

echo "=== 6. Can curl through Nginx? ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1/api/v1/health || echo "❌ FAILED"

# ===============================
# PHASE 3: Logs (1 min)
# ===============================
echo "=== 7. Recent Nginx errors? ==="
sudo tail -20 /var/log/nginx/error.log

echo "=== 8. Recent app errors? ==="
tail -20 /var/log/bandarupay/app.log

echo "=== 9. Recent 502 responses? ==="
sudo grep " 502 " /var/log/nginx/access.log | tail -5 || echo "No 502s found"

# ===============================
# PHASE 4: Resources (1 min)
# ===============================
echo "=== 10. Memory OK? ==="
free -h

echo "=== 11. Disk OK? ==="
df -h /

# ===============================
# All Complete
# ===============================
echo "✅ Diagnostic complete. Review output above."
```

---

## DECISION TREE: Where Is My Problem?

```
502 Bad Gateway
├─ Process running?
│  ├─ NO → START BACKEND (Section D)
│  └─ YES ↓
├─ Port listening?
│  ├─ NO → Backend crashed (Section B)
│  └─ YES ↓
├─ Works locally (curl localhost:8000)?
│  ├─ NO → Debug backend (Section B)
│  └─ YES ↓
├─ Nginx config valid?
│  ├─ NO → Fix config (NGINX_CONFIGURATION_502_GUIDE.md)
│  └─ YES ↓
├─ Works through Nginx (curl 127.0.0.1)?
│  ├─ NO → Nginx misconfiguration (Section A, Check 2)
│  └─ YES ↓
└─ HTTPS/Cloudflare issue (Section G)
   ├─ Check DNS
   ├─ Check SSL cert
   ├─ Check Cloudflare SSL settings
```

---

## QUICK COMMAND REFERENCE

| Task | Command |
|------|---------|
| Check backend running | `ps aux \| grep main.py` |
| Check port listening | `sudo netstat -tlnp \| grep 8000` |
| Test local connection | `curl http://localhost:8000/health` |
| Nginx syntax check | `sudo nginx -t` |
| View Nginx config | `sudo cat /etc/nginx/sites-enabled/backend` |
| Test through Nginx | `curl http://127.0.0.1/api/v1/health` |
| Nginx error logs | `sudo tail -f /var/log/nginx/error.log` |
| App logs | `tail -f /var/log/bandarupay/app.log` |
| See what uses port 8000 | `sudo lsof -i :8000` |
| Kill process on 8000 | `sudo kill -9 <PID>` |
| Restart backend manually | `python main.py` |
| Restart backend service | `sudo systemctl restart bandarupay-backend` |
| View memory | `free -h` |
| View disk | `df -h` |
| View CPU | `top -b -n 1` |

---

## COMMON FIXES AT A GLANCE

| Problem | Command to Fix |
|---------|---|
| Backend not running | `cd backend-api && source venv/bin/activate && python main.py` |
| Port already in use | `sudo kill -9 $(sudo lsof -t -i:8000)` |
| Config not reloaded | `sudo systemctl reload nginx` |
| Wrong upstream IP | `sudo sed -i 's/server .*/server 127.0.0.1:8000;/' /etc/nginx/sites-enabled/backend` |
| Wrong upstream port | `sudo sed -i 's/:8001/:8000/g' /etc/nginx/sites-enabled/backend` |
| Out of memory | `pkill -9 -f main.py && sync && echo 3 > /proc/sys/vm/drop_caches && python main.py` |
| Stuck process | `pkill -9 -f "python main.py"` |
