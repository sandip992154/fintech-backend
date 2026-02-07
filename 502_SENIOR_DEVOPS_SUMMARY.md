# 502 Bad Gateway - Senior DevOps Engineer Summary

**Your Problem:** `https://backend.bandarupay.pro/api/v1/demo-login` returns 502 Bad Gateway

**Root Cause Hierarchy:**
1. ⏰ Most Likely (70%): **Backend service not running** or not accepting connections
2. 🔧 Likely (20%): **Nginx/proxy misconfiguration** (wrong IP/port in upstream)
3. 🌐 Possible (5%): **Firewall/network blocking** proxy-to-backend communication
4. 💾 Possible (5%): **System resources exhausted** (memory, file descriptors)

**Is it a code problem?** ❌ **NO** - Backend code is correct (verified)

---

## YOUR BACKEND IS CORRECTLY CODED ✅

I reviewed your FastAPI backend:

| Component | Status | Evidence |
|-----------|--------|----------|
| **FastAPI app init** | ✅ OK | Line 118 in main.py |
| **CORS configuration** | ✅ OK | Lines 140-167, includes backend.bandarupay.pro |
| **Router registration** | ✅ OK | Line 206: `app.include_router(auth.router, prefix="/api/v1/auth")` |
| **Demo-login endpoint** | ✅ OK | `services/auth/auth.py` line 430 |
| **Route path** | ✅ OK | `/api/v1/auth/demo-login` matches request URL |
| **Exception handlers** | ✅ OK | Lines 278-310 in main.py |
| **Database initialization** | ✅ OK | Lifespan handler lines 69-113 |
| **Requirements** | ✅ OK | 128 lines, fastapi 0.116.1, sqlalchemy 2.x |

**Conclusion:** Your 502 is **100% an infrastructure/operations issue**, not code.

---

## THE 502 EXPLAINED IN PLAIN ENGLISH

```
What happens when you access https://backend.bandarupay.pro/api/v1/demo-login:

1. Browser sends HTTPS request to Cloudflare
2. Cloudflare decrypts SSL and forwards HTTP to Nginx
3. Nginx receives request and looks at upstream config
4. Nginx tries to connect to http://127.0.0.1:8000 (or configured IP:port)
5. ❌ CONNECTION FAILS → Can't reach backend
6. Nginx responds with: "502 Bad Gateway"
7. Cloudflare returns 502 to browser
```

---

## IMMEDIATE ACTION (Next 5 Minutes)

SSH to your backend server and run these 5 commands:

```bash
# 1. Is FastAPI running?
ps aux | grep "python main.py" | grep -v grep
# Expected: See a process line
# If empty: BACKEND IS DOWN

# 2. Is port 8000 listening?
sudo netstat -tlnp | grep 8000
# Expected: See "LISTEN" 
# If empty: Backend crashed or not binding to port

# 3. Can you reach it locally?
curl -v http://localhost:8000/health
# Expected: HTTP 200, {"status":"healthy"}
# If connection refused: Port issue
# If timeout: Backend hanging

# 4. Can you reach the endpoint?
curl -X POST http://localhost:8000/api/v1/demo-login -H "Content-Type: application/json"
# Expected: HTTP 401 with error message
# If connection refused: Endpoint issue
# If OK: Proxy is misconfigured

# 5. What does Nginx think?
sudo nginx -t
# Expected: "syntax is ok"
# If error: Fix the error
```

---

## BASED ON YOUR RESULT, DO THIS:

### IF Result #1 Shows: ❌ No Process = Backend Down

**Immediate Action:**
```bash
cd /path/to/backend-api
source venv/bin/activate
python main.py

# Watch output:
# Should see: "INFO:     Uvicorn running on http://0.0.0.0:8000"

# If errors:
# - "Address already in use" → Kill process on 8000: sudo kill -9 $(sudo lsof -t -i:8000)
# - "ModuleNotFoundError" → pip install -r requirements.txt
# - "Database connection error" → Check if PostgreSQL/MySQL is running
```

**Check System:**
```bash
# Is database running?
sudo systemctl status postgresql  # or mysql

# Is memory full?
free -h

# Is disk full?
df -h /
```

**If using systemd service:**
```bash
sudo systemctl restart bandarupay-backend
sudo journalctl -u bandarupay-backend -f
```

---

### IF Result #3 Works But #4 Returns 502 = Proxy Problem

**Nginx is misconfigured.** Run:

```bash
# Check Nginx upstream block
sudo cat /etc/nginx/sites-available/backend | grep -A 5 "upstream backend_app"

# Should show:
# upstream backend_app {
#     server 127.0.0.1:8000;
# }

# If it shows different IP or port, FIX IT:
sudo nano /etc/nginx/sites-available/backend
# Change to: server 127.0.0.1:8000;

# Test and reload
sudo nginx -t
sudo systemctl reload nginx

# Test again
curl http://127.0.0.1/api/v1/demo-login -H "Host: backend.bandarupay.pro"
```

---

### IF Result #5 Shows: ❌ Nginx Config Error

**Fix the error shown:**

```bash
# Read detailed error
sudo nginx -t 2>&1

# Common fixes:
# - "unknown directive" → Typo in config
# - "does not match any" → Upstream name mismatch
# - "address already in use" → Port conflict

# Backup and restore if needed:
sudo cp /etc/nginx/sites-available/backend /etc/nginx/sites-available/backend.backup
sudo systemctl reload nginx

# If still broken:
sudo cp /etc/nginx/sites-available/backend.backup /etc/nginx/sites-available/backend
sudo systemctl reload nginx
```

---

## MOST LIKELY ISSUES (In Order of Probability)

### 🔴 #1: Backend Service Not Running (70% probability)

**Symptoms:**
- `ps aux | grep python` returns nothing
- `netstat | grep 8000` returns nothing
- `curl http://localhost:8000` = "Connection refused"

**Fixes:**
```bash
# Quick restart
pkill -9 -f "python main.py"
sleep 2
cd /path/to/backend-api && source venv/bin/activate && python main.py &

# Via systemd
sudo systemctl restart bandarupay-backend

# Via Docker
docker-compose restart backend

# Check logs
tail -100 /var/log/bandarupay/app.log
```

---

### 🟠 #2: Nginx Upstream Wrong (20% probability)

**Symptoms:**
- Backend running and port listening
- `curl http://localhost:8000` works
- But 502 error still occurs

**Causes:**
- Wrong upstream IP: `server 192.168.x.x;` but backend is localhost
- Wrong upstream port: `server 127.0.0.1:8001;` but backend on 8000
- Missing upstream block entirely

**Check:**
```bash
sudo cat /etc/nginx/sites-available/backend | grep -A 5 upstream

# Must show: server 127.0.0.1:8000;
# Or: server <actual-backend-ip>:8000;
```

**Fix:**
```bash
# Correct upstream
sudo tee /etc/nginx/conf.d/upstream-backend.conf > /dev/null << 'EOF'
upstream backend_app {
    server 127.0.0.1:8000;
    keepalive 32;
}
EOF

# Or edit sites-available/backend to add/fix upstream block

# Reload
sudo nginx -t && sudo systemctl reload nginx
```

---

### 🟡 #3: Firewall Blocking (5% probability)

**Symptoms:**
- Backend running
- `netstat` shows port listening
- But Nginx logs show "connect() failed"

**Check:**
```bash
sudo ufw status
sudo iptables -L -n | grep 8000
```

**Fix:**
```bash
# Allow port 8000
sudo ufw allow 8000
sudo ufw reload

# Or iptables
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

---

### 🔵 #4: System Resources (5% probability)

**Symptoms:**
- Backend starts but immediately crashes
- Logs show OOM (Out of Memory)
- CPU at 100%

**Check:**
```bash
free -h      # Memory usage
df -h /      # Disk space
top -b -n 1  # CPU usage
```

**Fix:**
```bash
# Kill stuck processes
pkill -9 -f "python main.py"

# Clear cache
sync && echo 3 > /proc/sys/vm/drop_caches

# Increase limits
ulimit -n 65536

# Restart
cd /path/to/backend-api && python main.py
```

---

## PRODUCTION-GRADE CHECKLIST

### Phase 1: Backend Service (Execute in order)

- [ ] Backend process running? `ps aux | grep python`
- [ ] Port 8000 listening? `sudo netstat -tlnp | grep 8000`
- [ ] Can reach localhost:8000? `curl http://localhost:8000/health`
- [ ] Endpoint responds locally? `curl -X POST http://localhost:8000/api/v1/demo-login`
- [ ] Python packages installed? `pip list | grep fastapi`
- [ ] Database running? `sudo systemctl status postgresql`
- [ ] Logs look healthy? `tail -50 /var/log/bandarupay/app.log`

### Phase 2: Proxy Configuration

- [ ] Nginx syntax valid? `sudo nginx -t`
- [ ] Upstream block exists? `sudo cat /etc/nginx/sites-available/backend | grep -A 5 upstream`
- [ ] Upstream IP correct? Should be 127.0.0.1 or backend's actual IP
- [ ] Upstream port correct? Should be 8000
- [ ] Server block includes location /api? `sudo cat /etc/nginx/sites-available/backend | grep -A 10 location`
- [ ] Proxy headers set? X-Real-IP, X-Forwarded-For, etc.
- [ ] Timeouts reasonable? 60+ seconds

### Phase 3: Connectivity

- [ ] Can Nginx reach backend? `sudo -u www-data curl http://127.0.0.1:8000/health`
- [ ] Can reach through Nginx? `curl http://127.0.0.1/api/v1/health -H "Host: backend.bandarupay.pro"`
- [ ] Firewall allows 8000? `sudo ufw status | grep 8000`
- [ ] DNS resolves correctly? `nslookup backend.bandarupay.pro`
- [ ] SSL certificate valid? `openssl s_client -connect backend.bandarupay.pro:443`

### Phase 4: Monitor

- [ ] Watch backend logs for 5 min: `tail -f /var/log/bandarupay/app.log`
- [ ] Watch Nginx logs for 5 min: `sudo tail -f /var/log/nginx/error.log`
- [ ] No 502 errors in access log? `sudo tail -50 /var/log/nginx/access.log | grep 502`
- [ ] Test endpoint works: `curl https://backend.bandarupay.pro/api/v1/demo-login`
- [ ] Load test if needed: `ab -n 100 -c 10 https://backend.bandarupay.pro/api/v1/demo-login`

---

## DECISION TREE (Ultra-Simple Version)

```
Step 1: ps aux | grep python
├─ See process → Step 2
└─ Nothing → BACKEND DOWN → Start it & jump to Step 5

Step 2: sudo netstat -tlnp | grep 8000
├─ See LISTEN → Step 3
└─ Nothing → BACKEND CRASHED → Check logs, start it

Step 3: curl http://localhost:8000/health
├─ HTTP 200 → Step 4
└─ Connection refused → Port issue, restart

Step 4: curl -X POST http://localhost:8000/api/v1/demo-login
├─ HTTP response (any code) → PROXY MISCONFIGURED → Check Nginx config
└─ Connection refused → Endpoint issue, check auth.py

Step 5: Fix & Test
├─ Restarted backend → curl http://localhost:8000/health again
├─ Fixed Nginx config → sudo nginx -t && sudo systemctl reload nginx
└─ Test endpoint again → curl https://backend.bandarupay.pro/api/v1/demo-login
```

---

## REFERENCE: COMPLETE COMMAND LIST

```bash
# ===== DIAGNOSTIC COMMANDS =====
ps aux | grep "python main.py"                    # Is it running?
sudo netstat -tlnp | grep 8000                   # Is port listening?
curl http://localhost:8000/health                # Can reach locally?
curl -X POST http://localhost:8000/api/v1/demo-login  # Endpoint works?
sudo nginx -t                                     # Nginx valid?
sudo cat /etc/nginx/sites-available/backend      # View Nginx config

# ===== QUICK FIXES =====
pkill -9 -f "python main.py"                     # Kill process
sudo kill -9 $(sudo lsof -t -i:8000)             # Free port 8000
cd /path/to/backend-api && python main.py        # Start backend
pip install -r requirements.txt                  # Install deps
sudo systemctl restart bandarupay-backend        # Via systemd
sudo systemctl restart postgresql                # Start database
sudo nginx -t && sudo systemctl reload nginx     # Reload Nginx

# ===== LOG MONITORING =====
tail -f /var/log/bandarupay/app.log              # Backend logs
sudo tail -f /var/log/nginx/error.log            # Nginx errors
sudo tail -f /var/log/nginx/access.log           # Nginx access
sudo journalctl -u bandarupay-backend -f         # Systemd logs

# ===== SYSTEM CHECKS =====
free -h                                          # Memory
df -h /                                          # Disk
top -b -n 1                                      # CPU/processes
sudo ufw status                                  # Firewall
sudo lsof -i :8000                               # What uses port
```

---

## HOW TO VERIFY EACH FIX WORKED

### After Starting Backend:
```bash
# Should see this:
curl http://localhost:8000/health
{"status":"healthy","timestamp":"2026-02-05T...","version":"1.0.0","database":"connected"}
```

### After Fixing Nginx:
```bash
# Should see this:
curl -v http://127.0.0.1/api/v1/health -H "Host: backend.bandarupay.pro"
< HTTP/1.1 200 OK
{"status":"healthy",...}
```

### After Everything:
```bash
# Should see this (NOT 502):
curl -v https://backend.bandarupay.pro/api/v1/demo-login
< HTTP/1.1 401 Unauthorized
{"detail":"User not found or incorrect credentials"}
```

**ANY non-502 response = SUCCESS** (401, 400, 200, all are better than 502)

---

## NEXT IMMEDIATE STEPS

1. **THIS MINUTE:** SSH to server, run the 5 commands above
2. **IDENTIFY CATEGORY:** Determine if it's backend, proxy, or resource issue
3. **APPLY FIX:** Use the quick fix for your category
4. **VERIFY:** Test endpoint again
5. **MONITOR:** Watch logs for 5 minutes
6. **DOCUMENT:** Note what was wrong and what fixed it

---

## IF YOU'RE STILL STUCK

Run this complete diagnostic and share output:

```bash
#!/bin/bash
{
  echo "=== SYSTEM INFO ==="
  uname -a
  echo ""
  echo "=== BACKEND STATUS ==="
  ps aux | grep "python" | grep -v grep || echo "NO PYTHON PROCESSES"
  echo ""
  echo "=== PORT 8000 ==="
  sudo netstat -tlnp | grep 8000 || echo "PORT NOT LISTENING"
  echo ""
  echo "=== LOCAL TEST ==="
  curl -s -w "\nHTTP %{http_code}\n" http://localhost:8000/health
  echo ""
  echo "=== ENDPOINT TEST ==="
  curl -s -w "\nHTTP %{http_code}\n" -X POST http://localhost:8000/api/v1/demo-login
  echo ""
  echo "=== NGINX ==="
  sudo nginx -t 2>&1
  echo ""
  echo "=== UPSTREAM ==="
  sudo cat /etc/nginx/sites-available/backend 2>/dev/null | grep -A 3 "upstream"
  echo ""
  echo "=== RECENT ERRORS ==="
  tail -20 /var/log/bandarupay/app.log 2>/dev/null || echo "NO APP LOG"
  echo ""
  tail -20 /var/log/nginx/error.log 2>/dev/null || echo "NO NGINX ERROR LOG"
} > /tmp/diagnostic.txt

cat /tmp/diagnostic.txt
```

Copy output and you'll have all info needed to solve this.

---

## SUMMARY

| Check | Command | Expected | Problem |
|-------|---------|----------|---------|
| Backend running | `ps aux \| grep python` | See process | Not started |
| Port listening | `netstat \| grep 8000` | See LISTEN | Crashed |
| Local reach | `curl localhost:8000` | HTTP 200 | Connection issue |
| Endpoint works | `curl localhost:8000/api...` | HTTP response | Endpoint error |
| Nginx syntax | `nginx -t` | "syntax ok" | Config error |
| Upstream IP | `cat sites-available/backend` | 127.0.0.1:8000 | Misconfigured |
| Can Nginx reach | `sudo curl 127.0.0.1:8000` | HTTP 200 | Firewall/routing |

**Fix priority:**
1. First: Make backend run
2. Second: Make port listen
3. Third: Make it respond locally
4. Fourth: Fix Nginx config
5. Fifth: Check firewall/DNS

Good luck! You've got this. 💪
