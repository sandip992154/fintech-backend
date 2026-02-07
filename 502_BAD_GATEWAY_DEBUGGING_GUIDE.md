# 502 Bad Gateway Debugging Guide

**Endpoint:** `https://backend.bandarupay.pro/api/v1/demo-login`  
**Error Code:** 502 Bad Gateway  
**Root Cause Domain:** Reverse Proxy (Nginx/Cloudflare) cannot reach backend application  
**Severity:** 🔴 CRITICAL - Production Down

---

## WHAT IS 502 BAD GATEWAY?

### In a Reverse Proxy Setup

```
User Browser
    ↓
    ├─→ Cloudflare/Nginx (Reverse Proxy)
    │       ↓
    │   Tries to forward request to backend
    │       ↓
    │   ❌ CANNOT REACH BACKEND APPLICATION
    │       ↓
    │   Returns 502 Bad Gateway to user
    ↓
User sees: "502 Bad Gateway"
```

### What It Means:

The reverse proxy (Cloudflare or Nginx sitting in front of your backend) successfully received the request from the user but **cannot reach the backend application** to forward the request to.

This is NOT an application error (those return 500). This is an **infrastructure/connectivity** error.

### Why It Happens:

1. ❌ Backend service is **not running**
2. ❌ Backend is listening on **wrong port**
3. ❌ Backend is **crashing immediately** after start
4. ❌ Proxy is configured to forward to **wrong address/port**
5. ❌ Firewall is **blocking** the proxy-to-backend connection
6. ❌ Backend is **out of memory** (cannot accept connections)
7. ❌ Backend is **hanging** (not responding to requests)

---

## CRITICAL: IS YOUR BACKEND RUNNING?

Run this FIRST before anything else:

```bash
# Check if Python process is running
ps aux | grep "python\|main.py"

# You should see something like:
# user 12345 ... python main.py
# If you see NOTHING, backend is NOT running
```

**If no process found:** Your backend is DOWN. Go to **SECTION 3: START BACKEND**.

---

## STEP-BY-STEP SERVER-SIDE DEBUGGING CHECKLIST

### PHASE 1: Verify Backend Service Status (2 minutes)

#### ✅ Step 1.1: Check if Backend Process is Running

```bash
# List all Python processes
ps aux | grep python

# Expected output (you should see this):
# ubuntu 12345  0.0 2.5 450000 50000 ?  Sl 10:30 0:05 python main.py
# ubuntu 12346  0.0 1.2 300000 25000 ?  Sl 10:31 0:02 python worker.py

# If you see NOTHING or only "grep python", backend is NOT running
```

**RESULT:**
- ✅ **Process exists** → Go to STEP 1.2
- ❌ **No process found** → BACKEND IS DOWN, go to SECTION 3

---

#### ✅ Step 1.2: Check if Backend is Listening on Port 8000

```bash
# Check if port 8000 is open and listening
netstat -tlnp | grep 8000
# OR
ss -tlnp | grep 8000

# Expected output:
# tcp 0 0 127.0.0.1:8000 0.0.0.0:* LISTEN 12345/python

# OR if listening on all interfaces:
# tcp 0 0 0.0.0.0:8000 0.0.0.0:* LISTEN 12345/python
```

**RESULT:**
- ✅ **Port 8000 listening** → Go to STEP 1.3
- ❌ **Port not listening** → Backend crashed or not configured correctly, go to SECTION 3

---

#### ✅ Step 1.3: Can You Connect to Backend Locally?

```bash
# Test direct connection to backend
curl -v http://localhost:8000/api/v1/demo-login -X POST -H "Content-Type: application/json"

# Expected: Should get a response (200, 400, 500, anything except connection refused)
# If it works locally, the proxy config is wrong
```

**RESULT:**
- ✅ **Got response** → Proxy/forwarding issue (go to STEP 2)
- ❌ **Connection refused** → Backend not accepting connections (go to SECTION 3)
- ❌ **Timeout** → Backend is hanging (go to SECTION 4)

---

### PHASE 2: Verify Proxy Configuration (3 minutes)

#### ✅ Step 2.1: Check Nginx Configuration

```bash
# Check Nginx syntax
sudo nginx -t

# Expected:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration will be successful

# If errors shown, that's your problem
```

#### ✅ Step 2.2: Check Nginx Upstream Configuration

```bash
# Find the upstream block for your backend
sudo cat /etc/nginx/nginx.conf | grep -A 10 "upstream"

# Expected (for backend.bandarupay.pro):
# upstream backend_app {
#     server 127.0.0.1:8000;
#     # OR
#     server 192.168.1.100:8000;  # if on different machine
# }

# Verify:
# 1. Is the IP correct?
# 2. Is the port correct (should be 8000)?
```

#### ✅ Step 2.3: Check Nginx Server Block

```bash
# Find the server block for backend.bandarupay.pro
sudo cat /etc/nginx/sites-enabled/* | grep -A 20 "backend.bandarupay.pro"

# Expected to see:
# server {
#     server_name backend.bandarupay.pro;
#     location /api {
#         proxy_pass http://backend_app;
#     }
# }
```

**RESULT:**
- ✅ **Config looks correct** → Backend is the issue (go to SECTION 3)
- ❌ **Config is wrong** → Fix it (see SECTION 5: Common Misconfigurations)

---

### PHASE 3: Check Backend Application Logs (2 minutes)

#### ✅ Step 3.1: View Recent Logs

```bash
# Last 50 lines of log
tail -50 /var/log/bandarupay/app.log
# OR if using journalctl (systemd):
sudo journalctl -u bandarupay-backend -n 50 --no-pager

# Look for:
# - Exceptions
# - Port already in use
# - Failed to bind to port
# - Database connection errors
```

#### ✅ Step 3.2: Watch Logs in Real-Time While Testing

```bash
# Terminal 1: Watch logs
tail -f /var/log/bandarupay/app.log

# Terminal 2: Send test request
curl http://localhost:8000/api/v1/demo-login -X POST -H "Content-Type: application/json"

# If you see logs updating → Backend is receiving requests
# If logs don't update → Proxy not forwarding correctly
```

---

### PHASE 4: Check System Resources (1 minute)

#### ✅ Step 4.1: Check Memory

```bash
# Check if backend process is consuming memory
ps aux | grep main.py | grep -v grep | awk '{print $2, $6, $4}'

# Output format: PID MEMORY%
# If MEMORY > 90% → OUT OF MEMORY → Restart backend

# OR check overall system memory
free -h

# If Mem shows almost full:
# total 16GB
# used 15.5GB  ← ❌ CRITICAL
# available 0.5GB
```

**ACTION IF OUT OF MEMORY:**
```bash
# Kill backend process
kill -9 <PID>

# OR
pkill -9 -f "python main.py"

# Clear cache
sync; echo 3 > /proc/sys/vm/drop_caches

# Restart
python main.py
```

#### ✅ Step 4.2: Check CPU

```bash
# Check CPU usage
top -b -n 1 | head -20

# If CPU spike visible, backend might be in infinite loop
# Kill and restart if hung
```

---

### PHASE 5: Check Network Connectivity (2 minutes)

#### ✅ Step 5.1: Backend to Proxy Communication

```bash
# If proxy is on different server, test connectivity
# From proxy server, test reaching backend
ping <backend-ip>
telnet <backend-ip> 8000

# Expected: Should be able to reach backend port
```

#### ✅ Step 5.2: Firewall Check

```bash
# Check if port 8000 is in firewall allow list
sudo ufw status
# OR
sudo iptables -L -n | grep 8000

# Should see ALLOW 127.0.0.1 8000
# OR ALLOW 0.0.0.0 8000
# If blocked, enable it:
sudo ufw allow 8000
```

---

## SECTION 3: HOW TO VERIFY BACKEND IS RUNNING

### Quick Verification Commands

```bash
# 1. FASTEST CHECK: Is process running?
ps aux | grep "python main.py" | grep -v grep

# 2. DETAILED CHECK: Is port listening?
sudo netstat -tlnp | grep 8000

# 3. CONNECTIVITY CHECK: Can you reach it?
curl -v http://localhost:8000/health

# 4. PROXY CHECK: Can proxy reach it?
curl -v http://localhost:8000/api/v1/demo-login -H "Content-Type: application/json"
```

### What Each Check Tells You

| Check | Command | Expected | If Fails |
|-------|---------|----------|---------|
| Process running | `ps aux \| grep python` | See process in list | Backend never started |
| Port listening | `netstat -tlnp \| grep 8000` | LISTEN on 8000 | App crashed after start |
| Local connection | `curl http://localhost:8000/health` | 200 response | Backend is hanging |
| Accepts requests | `curl http://localhost:8000/api/v1/demo-login` | Any response | Backend broken |

---

## SECTION 4: HOW TO START BACKEND (IF DOWN)

### Option A: Manual Start

```bash
# Navigate to backend
cd /path/to/backend-api

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Start backend
python main.py

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# If you see this, backend is running
```

### Option B: Systemd Service (Production)

```bash
# Check if systemd service exists
sudo systemctl status bandarupay-backend

# If it exists but stopped:
sudo systemctl start bandarupay-backend
sudo systemctl status bandarupay-backend

# Watch logs:
sudo journalctl -u bandarupay-backend -f
```

### Option C: Docker Container

```bash
# If running in Docker:
docker ps | grep backend

# If not running, start it:
docker-compose up -d backend

# Check logs:
docker logs -f <container-id>
```

---

## SECTION 5: MOST LIKELY MISCONFIGURATIONS CAUSING 502

### 🔴 CRITICAL: Wrong Port in Nginx

**Problem:** Nginx forwarding to port 8001, but backend on port 8000

```nginx
# WRONG:
upstream backend_app {
    server 127.0.0.1:8001;  # ❌ Backend on 8000, not 8001
}

# CORRECT:
upstream backend_app {
    server 127.0.0.1:8000;  # ✅
}
```

**Fix:**
```bash
# Check what port backend is actually listening on
sudo netstat -tlnp | grep python

# Update Nginx:
sudo nano /etc/nginx/sites-enabled/backend
# Change port to match
sudo nginx -t
sudo systemctl reload nginx
```

---

### 🔴 CRITICAL: Backend Not Starting Due to Port Conflict

**Problem:** Port 8000 already in use by another process

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Output might show:
# COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
# java 5432 root 45u IPv4 0x1234 0t0 TCP 127.0.0.1:8000

# Kill the conflicting process:
sudo kill -9 5432
```

---

### 🔴 CRITICAL: Backend Process Crashes on Startup

**Problem:** Backend starts but crashes immediately

```bash
# Run backend in foreground to see error:
python main.py

# Common errors:
# - ModuleNotFoundError: Missing dependency → pip install -r requirements.txt
# - Address already in use → Kill process on that port
# - PermissionError → Check file permissions
# - Database connection error → Check DB connection string
```

---

### 🔴 CRITICAL: Proxy Listening on Wrong Interface

**Problem:** Backend on 127.0.0.1 but proxy on 0.0.0.0 (different interface)

```bash
# Check which interface backend is on:
sudo netstat -tlnp | grep 8000
# tcp 0 0 127.0.0.1:8000  ← Only localhost, not external

# Backend needs to listen on 0.0.0.0:8000 or proxy on 127.0.0.1
```

---

### 🔴 CRITICAL: Firewall Blocking Proxy-to-Backend

**Problem:** Firewall rule blocks connection between proxy and backend

```bash
# Check firewall rules
sudo ufw status verbose
sudo iptables -L -n

# Allow traffic on 8000:
sudo ufw allow 8000
# OR
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
```

---

### 🟠 HIGH: Upstream Connection Timeout Too Short

**Problem:** Proxy gives up waiting for backend too quickly

```nginx
# Check timeout settings in Nginx config
sudo cat /etc/nginx/nginx.conf | grep proxy_connect_timeout

# If missing or too short, backend might not respond in time
# Fix by adding:
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

---

### 🟠 HIGH: Backend Out of Memory

**Problem:** Backend crashes due to memory limit

```bash
# Check memory usage
free -h
ps aux | grep main.py | awk '{print "Backend using", $6, "KB"}'

# If backend > 90% of available memory:
# 1. Check for memory leaks in code
# 2. Restart backend
# 3. Increase server RAM
# 4. Add swap
```

---

### 🟠 HIGH: Database Connection Pool Exhausted

**Problem:** Too many simultaneous requests, DB connections full

```bash
# Check active connections
ps aux | grep main.py

# If backend using excessive memory and many threads:
# Backend likely has DB connection leak
# Needs code review and fix
```

---

### 🟡 MEDIUM: SSL Certificate Issues (If Using HTTPS Upstream)

**Problem:** Nginx can't validate backend's SSL certificate

```nginx
# If using HTTPS upstream:
upstream backend_app {
    server 127.0.0.1:8443 ssl_verify_off;  # Disable cert verification
}
# OR
proxy_ssl_verify off;  # In server block
```

---

## QUICK DIAGNOSIS DECISION TREE

```
502 Bad Gateway on https://backend.bandarupay.pro/api/v1/demo-login
        ↓
┌─────────────────────────────────┐
│ Step 1: Is backend running?     │
│ ps aux | grep python main.py    │
└─────────────────────────────────┘
        ↓
    YES / NO
    ↙      ↖
   ✅      ❌ → START BACKEND (Section 3)
   ↓            └→ Check logs for startup errors
   ↓
┌─────────────────────────────────┐
│ Step 2: Is port 8000 listening? │
│ netstat -tlnp | grep 8000       │
└─────────────────────────────────┘
        ↓
    YES / NO
    ↙      ↖
   ✅      ❌ → Backend crashed (Section 3)
   ↓            └→ Check system resources (4.1, 4.2)
   ↓
┌─────────────────────────────────┐
│ Step 3: Works locally?          │
│ curl http://localhost:8000/api  │
└─────────────────────────────────┘
        ↓
    YES / NO
    ↙      ↖
   ✅      ❌ → Backend has error (Section 3)
   ↓            └→ Check app logs
   ↓
   🔴 PROXY IS MISCONFIGURED (Section 5)
   ├→ Check Nginx upstream config
   ├→ Check port number
   ├→ Check timeout settings
   ├→ Restart Nginx
   └→ Re-test
```

---

## COMPLETE DEBUGGING CHECKLIST

**Run these in order:**

```bash
# ✅ 1. Check process (10 seconds)
ps aux | grep "python main.py" | grep -v grep

# ✅ 2. Check port listening (10 seconds)
sudo netstat -tlnp | grep 8000

# ✅ 3. Check local connectivity (5 seconds)
curl -v http://localhost:8000/api/v1/demo-login

# ✅ 4. Check Nginx syntax (5 seconds)
sudo nginx -t

# ✅ 5. View Nginx config (10 seconds)
sudo cat /etc/nginx/sites-enabled/backend

# ✅ 6. Check logs (10 seconds)
tail -50 /var/log/bandarupay/app.log

# ✅ 7. Check memory (10 seconds)
free -h && ps aux | grep main.py | grep -v grep | awk '{print $6, $4}'

# ✅ 8. Check firewall (10 seconds)
sudo ufw status | grep 8000

# ✅ 9. Test from Nginx upstream (10 seconds)
curl -v http://<backend-ip>:8000/api/v1/demo-login

# ✅ 10. Reload Nginx if changes made (5 seconds)
sudo systemctl reload nginx

# Total time: ~2 minutes
```

---

## EMERGENCY RESTART PROCEDURES

### If Backend is Completely Down

```bash
# Kill any stuck processes
pkill -9 -f "python main.py"
pkill -9 -f "uvicorn"

# Check no processes remain
ps aux | grep python

# Clear cache
sync; echo 3 > /proc/sys/vm/drop_caches

# Start fresh
cd /path/to/backend-api
source venv/bin/activate
python main.py

# Watch logs
tail -f /var/log/bandarupay/app.log
```

### If Nginx Configuration is Wrong

```bash
# Backup current config
sudo cp /etc/nginx/sites-enabled/backend /etc/nginx/sites-enabled/backend.backup

# Edit config
sudo nano /etc/nginx/sites-enabled/backend

# Test syntax
sudo nginx -t

# If errors, revert
sudo cp /etc/nginx/sites-enabled/backend.backup /etc/nginx/sites-enabled/backend
sudo systemctl reload nginx

# If OK, reload
sudo systemctl reload nginx
sudo systemctl status nginx
```

---

## USEFUL COMMANDS REFERENCE

### Process Management
```bash
ps aux | grep python                    # List Python processes
ps aux | grep main.py                   # List main.py processes
pgrep -f "python main.py"              # Get PID
kill -9 <PID>                          # Force kill process
pkill -9 -f "python main.py"           # Kill by pattern
```

### Port Checking
```bash
netstat -tlnp | grep 8000              # Check listening ports
ss -tlnp | grep 8000                   # Alternative to netstat
lsof -i :8000                          # Show process using port
```

### Network Testing
```bash
curl http://localhost:8000/health      # Test local backend
curl -v http://localhost:8000/api      # Verbose output
nc -zv localhost 8000                  # Test port connectivity
telnet localhost 8000                  # Raw socket connection
```

### Nginx
```bash
sudo nginx -t                          # Test config syntax
sudo systemctl reload nginx            # Reload without restart
sudo systemctl restart nginx           # Full restart
sudo systemctl status nginx            # Check status
tail -f /var/log/nginx/access.log      # Watch access logs
tail -f /var/log/nginx/error.log       # Watch error logs
```

### Logs
```bash
tail -50 /var/log/bandarupay/app.log   # Last 50 lines
tail -f /var/log/bandarupay/app.log    # Real-time follow
grep ERROR /var/log/bandarupay/app.log # Find errors
journalctl -u bandarupay-backend -f    # If using systemd
```

### System Resources
```bash
free -h                                # Memory usage
df -h                                  # Disk usage
top -b -n 1                            # CPU/memory snapshot
ps aux | sort -k6 -rn | head           # Top memory consumers
```

---

## EXPECTED OUTPUTS

### ✅ Healthy Backend

```bash
$ ps aux | grep python
ubuntu 12345 0.0 2.5 450000 50000 ? Sl 10:30 0:05 python main.py

$ netstat -tlnp | grep 8000
tcp 0 0 127.0.0.1:8000 0.0.0.0:* LISTEN 12345/python

$ curl http://localhost:8000/health
{"status":"healthy"}

$ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok

$ tail /var/log/bandarupay/app.log
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: API server started successfully
```

### ❌ Backend Down

```bash
$ ps aux | grep python
ubuntu 12346 0.0 0.0 10000 2000 pts/0 S+ 10:45 0:00 grep --color=auto python
# No main.py process!

$ netstat -tlnp | grep 8000
# No output - port not listening

$ curl http://localhost:8000/health
curl: (7) Failed to connect to localhost port 8000: Connection refused

$ tail /var/log/bandarupay/app.log
ERROR: [Errno 2] No such file or directory: '/path/to/config'
ERROR: Cannot start server - check configuration
```

---

## NEXT STEPS AFTER FIXING

1. **Re-test the endpoint:**
   ```bash
   curl https://backend.bandarupay.pro/api/v1/demo-login
   ```

2. **Monitor logs for 5 minutes:**
   ```bash
   tail -f /var/log/bandarupay/app.log
   tail -f /var/log/nginx/error.log
   ```

3. **Load test if fixed:**
   ```bash
   ab -n 100 -c 10 https://backend.bandarupay.pro/api/v1/demo-login
   ```

4. **Check uptime:**
   ```bash
   ps aux | grep main.py | grep -v grep
   # Check how long process has been running
   ```

---

## CONTACT & ESCALATION

If after following this guide:
- ✅ Backend is running AND listening on port 8000 AND works locally
- ✅ Nginx config is correct
- ✅ Firewall is open
- ✅ You still get 502

**Then the issue is likely:**
1. Cloudflare configuration (check Cloudflare DNS and SSL settings)
2. Load balancer misconfiguration
3. Kubernetes/container orchestration issue
4. DNS not resolving to correct IP

**Check:**
```bash
nslookup backend.bandarupay.pro
dig backend.bandarupay.pro
curl -v https://backend.bandarupay.pro/api/v1/demo-login -H "Host: backend.bandarupay.pro"
```
