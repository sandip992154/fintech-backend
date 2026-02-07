# 🎯 COMPREHENSIVE API DEBUGGING GUIDE - START HERE

**Your Issue:** Network Error on `https://backend.bandarupay.pro/api/v1/demo-login`

**Goal:** Identify root cause without refactoring frontend

---

## 📚 Two Documents Created For You

### 1. **API_QUICK_TEST_REFERENCE.md** ⚡ (Read This First - 3 min)
- Quick copy-paste test commands
- Expected results for each test
- CORS quick fix
- Decision tree

### 2. **API_NETWORK_ERROR_DEBUGGING_GUIDE.md** 🔧 (Detailed Reference - 20 min)
- 25 possible causes listed
- 7-phase systematic debugging checklist
- 3 complete testing procedures (browser, curl, Postman)
- Expected results for each test type
- CORS configuration details
- How to confirm it's NOT a frontend bug
- Server log analysis
- Decision tree with all options

---

## 🚀 Quick Start (Do This First)

### Step 1: Test Basic Connectivity (30 seconds)
```bash
# Test if server is reachable
curl -I https://backend.bandarupay.pro

# Expected: HTTP response (any code like 200, 404, 500 is OK)
# Problem: Connection error, timeout, or DNS error
```

### Step 2: Test the Endpoint (30 seconds)
```bash
# Test actual endpoint
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'

# Expected: 200 with tokens OR 401/400 with error message
# Problem: 404, 500, timeout, connection refused
```

### Step 3: If You Got an Error
- Got **curl error (not HTTP status)** → Go to "Network Issues" section
- Got **HTTP 404** → Go to "Routing Issues" section  
- Got **HTTP 500** → Go to "Server Issues" section
- Got **browser "Failed to fetch"** → Go to "CORS Issues" section

---

## 🔍 25 Possible Causes (Organized by Category)

### 🌐 Network Layer (Test First)
1. DNS Resolution Failure - Can't reach domain
2. Firewall Blocking - Port blocked by firewall
3. SSL/TLS Certificate Error - Certificate expired/invalid
4. Network Timeout - Request too slow
5. Connection Refused - Port closed/not listening

### 🖥️ Server Configuration
6. Server Down/Not Running - Process not active
7. Wrong Port - Service on different port
8. Reverse Proxy Misconfigured - nginx/apache wrong
9. Load Balancer Issue - LB routing wrong
10. Server Out of Memory - Not enough resources

### 🛣️ API Routing
11. Route Not Registered - @app.post("/demo-login") missing
12. Wrong URL Path - /auth/login vs /api/v1/auth/login
13. API Prefix Missing - Missing /api/v1 prefix
14. Method Not Allowed - Using GET instead of POST

### 🔐 CORS & Headers
15. CORS Not Enabled - No CORSMiddleware
16. CORS Wrong Origin - Origin not in allowed_origins
17. CORS Missing Headers - Content-Type not allowed
18. Missing Auth Headers - Authorization header required
19. Invalid Content-Type - Wrong Content-Type header

### 💻 Client-Side
20. Wrong URL - Typo in domain
21. Typo in Endpoint - Wrong path in code
22. Request Interceptor Blocking - Middleware blocking
23. Browser Extensions - Ad blocker blocking request
24. VPN/Proxy Issues - Routing through VPN

### ⚙️ Backend Application
25. Unhandled Exception - Bug in endpoint code
26. Database Connection Failed - DB unreachable
27. Rate Limiting - Too many requests
28. Request Timeout - App processing too slow

---

## 🧪 How to Test (Pick Your Preferred Method)

### Method 1: Browser Console (Easiest)
```javascript
// Paste in F12 Console tab:
fetch('https://backend.bandarupay.pro/api/v1/demo-login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'superadmin', password: 'SuperAdmin@123'})
}).then(r => r.json()).then(d => console.log(d)).catch(e => console.error(e))
```

**Advantages:**
- ✅ Tests CORS and frontend environment
- ✅ Shows exact error message
- ✅ No tools needed

**Disadvantages:**
- ❌ Can't test SSL specifically
- ❌ Can't test OPTIONS request

---

### Method 2: curl Command (Most Reliable)
```bash
# Basic test:
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'

# Verbose (see all details):
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}' -v

# Test CORS:
curl -X OPTIONS "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Origin: https://superadmin.bandarupay.pro" \
  -H "Access-Control-Request-Method: POST" -v

# Ignore SSL (test if cert is issue):
curl -k -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'
```

**Advantages:**
- ✅ Works everywhere
- ✅ Can test SSL, CORS, headers
- ✅ No CORS issues with curl

**Disadvantages:**
- ❌ Doesn't test browser CORS

---

### Method 3: Postman (User-Friendly)
**Steps:**
1. Create new POST request
2. URL: `https://backend.bandarupay.pro/api/v1/demo-login`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "username": "superadmin",
  "password": "SuperAdmin@123"
}
```
5. Click Send

**Advantages:**
- ✅ Visual interface
- ✅ Easy to see headers
- ✅ Can save requests

**Disadvantages:**
- ❌ Still doesn't test browser CORS

---

## 📊 Expected Results for Each Test

### ✅ SUCCESS (Working Endpoint)
```bash
# Response:
HTTP/1.1 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "refresh_token": "...",
  "token_type": "bearer",
  "role": "super_admin"
}
```

### ✅ ALSO OK (Endpoint exists, different error)
```bash
# 400 Bad Request (wrong input):
HTTP/1.1 400 Bad Request
{"detail": "Invalid request format"}

# 401 Unauthorized (wrong credentials):
HTTP/1.1 401 Unauthorized  
{"detail": "Invalid credentials"}

# 404 Not Found (endpoint doesn't exist):
HTTP/1.1 404 Not Found
{"detail": "Not found"}
```

### ❌ NETWORK ERRORS (Problem)

**curl: (6) Could not resolve host**
```
Problem: DNS not resolving
Test: nslookup backend.bandarupay.pro
Fix: Check DNS configuration
```

**curl: (7) Failed to connect to backend.bandarupay.pro port 443**
```
Problem: Can't connect to server
Cause: Server down, port closed, firewall
Test: Ping server, check server is running
Fix: Start server, open port
```

**curl: (28) Operation timeout after 300000ms**
```
Problem: Request taking too long
Cause: Server slow, network slow
Test: Check server resources (top, free)
Fix: Optimize code, add resources
```

**curl: (60) SSL certificate problem: certificate has expired**
```
Problem: SSL certificate invalid
Cause: Certificate expired
Test: openssl s_client -connect backend.bandarupay.pro:443
Fix: Renew certificate
```

**Browser: "Failed to fetch" (status 0)**
```
Problem: Browser blocked request
Causes: CORS, SSL, network
Test: Check browser console
Fix: Enable CORS, fix SSL
```

**Browser: "Access-Control-Allow-Origin header missing"**
```
Problem: CORS not configured
Cause: CORSMiddleware not added
Test: curl -X OPTIONS ... (no CORS headers?)
Fix: Add CORS configuration
```

---

## 🎯 Systematic Debugging Steps

### Phase 1: Network Connectivity
```bash
# Step 1: Can you reach the domain?
ping backend.bandarupay.pro

# Step 2: Can you get HTTP response?
curl -I https://backend.bandarupay.pro

# Step 3: What's the IP?
nslookup backend.bandarupay.pro
```

**If any fails:** Network/DNS/firewall issue

---

### Phase 2: Server Status
```bash
# SSH to server and run:
ps aux | grep python           # Is server process running?
netstat -tulpn | grep 8000     # Is port listening?
free -h                         # Enough memory?
df -h                           # Enough disk?
```

**If any shows issue:** Server/resource problem

---

### Phase 3: Endpoint Routing
```bash
# Test endpoint exists
curl -I "https://backend.bandarupay.pro/api/v1/demo-login"

# Test POST with data
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'
```

**If 404:** Endpoint not registered
**If 200/400/401:** Endpoint works

---

### Phase 4: CORS (If browser error)
```bash
# Test CORS headers
curl -X OPTIONS "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Origin: https://superadmin.bandarupay.pro" \
  -H "Access-Control-Request-Method: POST" -v

# Look for:
# Access-Control-Allow-Origin: ...
# Access-Control-Allow-Methods: ...
```

**If missing CORS headers:** Add CORS config

---

### Phase 5: Server Logs
```bash
# SSH to server:
tail -f backend-api/logs/app.log

# Make request again, watch logs for:
# ✅ "POST /api/v1/demo-login HTTP/1.1" 200
# ❌ ERROR messages
# ❌ No request appearing
```

---

## 🔐 CORS Configuration

**If CORS is the issue, add this to your backend:**

```python
from fastapi.middleware.cors import CORSMiddleware

# Add to main.py after creating app:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://superadmin.bandarupay.pro",  # Your frontend
        "https://backend.bandarupay.pro",
        "http://localhost:5172",               # Dev
        "http://localhost:3000",               # Dev
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
    expose_headers=["Content-Length", "Access-Control-Allow-Origin"],
    max_age=600
)

# Restart backend:
# python main.py
```

---

## ✅ How to Confirm It's NOT Frontend Bug

**Test 1: Different Tool**
```bash
# If browser fails, test with curl:
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'

# ✅ Works in curl but not browser → Frontend/CORS issue
# ❌ Fails in curl → Server/network issue
```

**Test 2: Direct on Server**
```bash
# SSH to server and test locally:
curl -X POST "http://localhost:8000/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'

# ✅ Works locally → Frontend/network issue
# ❌ Fails locally → Server issue
```

**Test 3: Check Browser DevTools**
- F12 → Network tab → Look for the request
- ✅ See "demo-login" request with status 200/400/401 → Server works, frontend works
- ❌ Don't see request at all → Frontend not sending request (UI bug)
- ❌ See request with status 0 → Network/CORS/SSL issue

---

## 🚨 Most Common Issues & Quick Fixes

| Issue | Cause | Quick Fix |
|-------|-------|-----------|
| curl: "Could not resolve host" | DNS failing | Check: `nslookup backend.bandarupay.pro` |
| curl: "Failed to connect" | Server down | Run: `python main.py` on server |
| 404 Not Found | Wrong route | Check: `/api/v1/demo-login` exists in code |
| "Failed to fetch" browser | CORS or SSL | Run: `curl -X OPTIONS` test |
| "Access-Control-Allow-Origin missing" | CORS not configured | Add: CORSMiddleware to main.py |
| 500 Internal Server Error | Backend bug | Check: `tail -f app.log` |
| Request timeout | Server slow | Check: `top`, `free -h` |

---

## 📋 Debugging Checklist

- [ ] Run: `ping backend.bandarupay.pro`
- [ ] Run: `curl -I https://backend.bandarupay.pro`
- [ ] Run: `curl -X POST endpoint with data` (verbose `-v`)
- [ ] Run: `nslookup backend.bandarupay.pro`
- [ ] Run: `curl -X OPTIONS` (test CORS)
- [ ] Check: Browser DevTools F12 Network tab
- [ ] Check: Browser DevTools F12 Console for errors
- [ ] SSH to server and run: `ps aux | grep python`
- [ ] SSH to server and run: `tail -f app.log`
- [ ] SSH to server and run: `curl -X POST localhost:8000/api/v1/demo-login`
- [ ] Note: What's the HTTP status code?
- [ ] Note: What's the error message?

---

## 📞 When Reporting Issue

Include:

1. **curl result:**
```bash
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}' -v
# Output: [paste here]
```

2. **DNS result:**
```bash
nslookup backend.bandarupay.pro
# Output: [paste here]
```

3. **Server status:**
```bash
ps aux | grep python
netstat -tulpn | grep 8000
# Output: [paste here]
```

4. **Browser DevTools error:**
- F12 → Console → [paste error message]
- F12 → Network tab → [screenshot of request]

5. **Server logs:**
```bash
tail -f backend-api/logs/app.log
# Output: [paste here]
```

---

## 🎓 Summary

| Aspect | Quick Reference |
|--------|-----------------|
| **Quick Test** | `curl -X POST endpoint` |
| **CORS Test** | `curl -X OPTIONS endpoint` |
| **Server Test** | SSH and run `curl http://localhost:8000/...` |
| **DNS Test** | `nslookup backend.bandarupay.pro` |
| **Server Process** | `ps aux \| grep python` |
| **Port Listening** | `netstat -tulpn \| grep 8000` |
| **Server Logs** | `tail -f app.log` |
| **Browser Error** | F12 Console tab |
| **Network Error** | F12 Network tab |

---

**Start with:**
1. Read: [API_QUICK_TEST_REFERENCE.md](API_QUICK_TEST_REFERENCE.md) (3 min)
2. Run: Tests from that file
3. If stuck, read: [API_NETWORK_ERROR_DEBUGGING_GUIDE.md](API_NETWORK_ERROR_DEBUGGING_GUIDE.md) (detailed reference)

**Questions?** Check the detailed guide for 7-phase systematic debugging.
