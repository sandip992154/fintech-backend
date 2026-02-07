# 502 Bad Gateway - QUICK ACTION GUIDE (5 Minutes)

**Problem:** `https://backend.bandarupay.pro/api/v1/demo-login` returns 502 Bad Gateway

**Root Cause:** Reverse proxy (Nginx/Cloudflare) cannot reach your backend application

---

## STEP 1: Is Backend Running? (1 minute)

**SSH to your server and run:**

```bash
ps aux | grep "python main.py" | grep -v grep
```

### Expected Output:
```
ubuntu  12345  0.0  2.5  450000  50000  ?  Sl  10:30  0:05  python main.py
```

### What You See:
- ✅ **See the line above** → Backend is running, go to STEP 2
- ❌ **Nothing shown** → **BACKEND IS DOWN**, skip to STEP 4

---

## STEP 2: Is Port 8000 Listening? (1 minute)

**Run:**

```bash
sudo netstat -tlnp | grep 8000
```

### Expected Output:
```
tcp  0  0  127.0.0.1:8000  0.0.0.0:*  LISTEN  12345/python
```

### What You See:
- ✅ **See LISTEN on 8000** → Backend is accepting connections, go to STEP 3
- ❌ **Nothing shown** → **Backend is NOT listening** (crashed), go to STEP 4

---

## STEP 3: Can You Reach It Locally? (2 minutes)

**Run:**

```bash
curl -v http://localhost:8000/api/v1/demo-login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

### Expected Output:
```
Connected to localhost (127.0.0.1) port 8000 (#0)
< HTTP/1.1 401 Unauthorized
```

(Or any HTTP response - 200, 400, 500, etc. - just NOT "Connection refused")

### What You See:
- ✅ **HTTP response (any code)** → **PROXY IS MISCONFIGURED**, check Nginx settings
- ❌ **Connection refused** → **Backend is broken**, go to STEP 4
- ❌ **Timeout / no response** → **Backend is hanging**, go to STEP 4

---

## STEP 4: Backend is Down - Start It

### Option A: Manual Start (Linux/Mac)

```bash
cd /path/to/backend-api
source venv/bin/activate
python main.py
```

### Option B: Manual Start (Windows)

```powershell
cd C:\path\to\backend-api
.\venv\Scripts\Activate.ps1
python main.py
```

### Option C: Systemd Service

```bash
sudo systemctl start bandarupay-backend
sudo systemctl status bandarupay-backend
```

### Option D: Docker

```bash
docker-compose up -d backend
docker logs -f <container-name>
```

**Expected:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

If you see errors, read the error message. Common issues:
- `Address already in use` → Kill the process on that port
- `ModuleNotFoundError` → Run `pip install -r requirements.txt`
- `Database connection error` → Check DB is running

---

## STEP 5: Check Backend Logs

**Run:**

```bash
tail -50 /var/log/bandarupay/app.log
```

Or if using systemd:

```bash
sudo journalctl -u bandarupay-backend -n 50
```

**Look for errors** that explain why 502 occurs.

---

## STEP 6: Verify Nginx Configuration

**If Step 3 worked (curl localhost:8000 succeeds), the issue is Nginx.**

```bash
# Check syntax
sudo nginx -t

# View the config
sudo cat /etc/nginx/sites-enabled/backend

# Look for the upstream block - it should say:
# upstream backend_app {
#     server 127.0.0.1:8000;
# }
```

### Most Common Nginx Issues:

**Wrong Port:**
```nginx
upstream backend_app {
    server 127.0.0.1:8001;  # ❌ WRONG (backend is on 8000)
}
```

**Wrong IP:**
```nginx
upstream backend_app {
    server 192.168.1.100:8000;  # ❌ Backend might be on localhost
}
```

**Fix & Reload:**
```bash
sudo nano /etc/nginx/sites-enabled/backend
# Update the port/IP to 127.0.0.1:8000
sudo nginx -t
sudo systemctl reload nginx
```

---

## ONE-LINER DIAGNOSTIC CHECKLIST

Copy and run this command - it checks everything:

```bash
echo "=== BACKEND STATUS ===" && \
ps aux | grep "python main.py" | grep -v grep && echo "✅ Running" || echo "❌ NOT running" && \
echo -e "\n=== PORT LISTENING ===" && \
sudo netstat -tlnp | grep 8000 && echo "✅ Listening on 8000" || echo "❌ NOT listening on 8000" && \
echo -e "\n=== LOCAL CONNECTIVITY ===" && \
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health && echo " ✅ Backend responds" || echo " ❌ No response" && \
echo -e "\n=== NGINX ===" && \
sudo nginx -t 2>&1 | grep "ok"
```

---

## DECISION TREE

```
502 Bad Gateway
├─ Backend running? (ps aux | grep python)
│  ├─ YES → Port listening? (netstat | grep 8000)
│  │  ├─ YES → Works locally? (curl http://localhost:8000)
│  │  │  ├─ YES → ❌ NGINX IS MISCONFIGURED (check Section "STEP 6")
│  │  │  └─ NO → ❌ BACKEND ERROR (check app logs)
│  │  └─ NO → ❌ BACKEND CRASHED (restart it)
│  └─ NO → ❌ BACKEND NOT RUNNING (start it)
```

---

## EMERGENCY RESTART

If everything is broken:

```bash
# Kill any stuck processes
pkill -9 -f "python main.py"

# Wait 2 seconds
sleep 2

# Clear cache
sync; echo 3 > /proc/sys/vm/drop_caches

# Start fresh
cd /path/to/backend-api
source venv/bin/activate
python main.py

# In another terminal, watch logs
tail -f /var/log/bandarupay/app.log
```

---

## VERIFY FIX

Once you've fixed the issue:

```bash
# Test locally first
curl http://localhost:8000/api/v1/demo-login -X POST -H "Content-Type: application/json"

# Then test via proxy
curl https://backend.bandarupay.pro/api/v1/demo-login -X POST -H "Content-Type: application/json"

# Expected: No more 502 error
```

---

## HELP: COMMON FIXES

| Symptom | Fix |
|---------|-----|
| `ps aux` shows nothing | Start backend (STEP 4) |
| `netstat` shows nothing | Backend crashed - check logs |
| `curl localhost:8000` fails | App has error - read logs |
| `curl localhost:8000` works but HTTPS fails | Check Nginx config, reload, check Nginx logs |
| Port already in use | Kill process: `lsof -i :8000` then `kill -9 <PID>` |
| Module not found error | `pip install -r requirements.txt` |
| Permission denied | `sudo systemctl start bandarupay-backend` |

**For detailed help, see:** [502_BAD_GATEWAY_DEBUGGING_GUIDE.md](502_BAD_GATEWAY_DEBUGGING_GUIDE.md)
