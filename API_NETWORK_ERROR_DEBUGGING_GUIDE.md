# 🔧 API NETWORK ERROR DEBUGGING GUIDE

**Endpoint:** `https://backend.bandarupay.pro/api/v1/demo-login`
**Error Type:** Network Error
**Objective:** Identify root cause without UI refactoring

---

## 📋 PART 1: All Possible Real-World Causes

### Network Layer Issues
| # | Cause | Symptoms | Priority |
|---|-------|----------|----------|
| 1 | **DNS Resolution Failure** | Cannot reach domain, "ERR_NAME_NOT_RESOLVED" | HIGH |
| 2 | **Firewall Blocking** | Connection timeout, request hangs | HIGH |
| 3 | **SSL/TLS Certificate Error** | "ERR_SSL_PROTOCOL_ERROR", "ERR_CERT_*" | HIGH |
| 4 | **Network Timeout** | Request hangs then times out (30s) | HIGH |
| 5 | **Connection Refused** | "ERR_CONNECTION_REFUSED", port closed | HIGH |

### Server Configuration Issues
| # | Cause | Symptoms | Priority |
|---|-------|----------|----------|
| 6 | **Server Down/Not Running** | Connection refused, no response | HIGH |
| 7 | **Wrong Port** | Connection refused (port not open) | HIGH |
| 8 | **Reverse Proxy Misconfigured** | 502 Bad Gateway, 503 Unavailable | HIGH |
| 9 | **Load Balancer Issue** | Intermittent failures, 502/503 errors | MEDIUM |
| 10 | **Server Out of Memory** | Slow response, eventual connection refused | MEDIUM |

### API Routing Issues
| # | Cause | Symptoms | Priority |
|---|-------|----------|----------|
| 11 | **Route Not Registered** | 404 Not Found | HIGH |
| 12 | **Wrong URL Path** | 404 Not Found | HIGH |
| 13 | **API Prefix Missing** | 404 Not Found (/demo-login vs /api/v1/demo-login) | HIGH |
| 14 | **Method Not Allowed** | 405 Method Not Allowed | HIGH |

### CORS & Headers Issues
| # | Cause | Symptoms | Priority |
|---|-------|----------|----------|
| 15 | **CORS Not Enabled** | Browser blocks request, "ERR_CORS_ERROR" | HIGH |
| 16 | **CORS Wrong Origin** | "Access-Control-Allow-Origin" doesn't match | HIGH |
| 17 | **CORS Missing Headers** | Preflight fails, browser blocks request | HIGH |
| 18 | **Missing Auth Headers** | 401/403 (but still a network response) | MEDIUM |
| 19 | **Invalid Content-Type** | 415 Unsupported Media Type | MEDIUM |

### Client-Side Issues
| # | Cause | Symptoms | Priority |
|---|-------|----------|----------|
| 20 | **Wrong URL** | Network error, DNS fails if domain wrong | MEDIUM |
| 21 | **Typo in Endpoint** | 404 if path wrong | MEDIUM |
| 22 | **Request Interceptor Blocking** | Network error from middleware | LOW |
| 23 | **Browser Extensions Blocking** | Intermittent, unclear origin | LOW |
| 24 | **VPN/Proxy Issues** | Intermittent timeouts, DNS issues | LOW |

### Backend Application Issues
| # | Cause | Symptoms | Priority |
|---|-------|----------|----------|
| 25 | **Unhandled Exception** | 500 Internal Server Error | HIGH |
| 26 | **Database Connection Failed** | 500, service unavailable | HIGH |
| 27 | **Rate Limiting** | 429 Too Many Requests | MEDIUM |
| 28 | **Request Timeout in App** | 504 Gateway Timeout | MEDIUM |

---

## ✅ PART 2: Step-by-Step Debugging Checklist

### Phase 1: Verify Basic Connectivity (Do First)

- [ ] **Can you ping the domain?**
  ```bash
  ping backend.bandarupay.pro
  ```
  ✅ Works? → DNS is fine, continue
  ❌ Fails? → Go to "DNS Issue" section

- [ ] **Can you reach the domain in browser?**
  Open: `https://backend.bandarupay.pro`
  ✅ Loads anything (page/error)? → Server is up
  ❌ Nothing loads? → Server might be down

- [ ] **Check if HTTPS works**
  Open: `https://backend.bandarupay.pro`
  ✅ Works? → SSL is fine
  ❌ "Certificate error"? → Go to "SSL Issue" section

- [ ] **Can you curl the domain?**
  ```bash
  curl -I https://backend.bandarupay.pro
  ```
  ✅ HTTP response? → Server is responding
  ❌ Connection error? → Go to "Connection Issue" section

---

### Phase 2: Test the Specific Endpoint (Core Debugging)

- [ ] **Test with curl (most reliable)**
  ```bash
  curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
    -H "Content-Type: application/json" \
    -d '{"username":"superadmin","password":"SuperAdmin@123"}' \
    -v
  ```
  ✅ Response? → Go to "Analyze Response" section
  ❌ Error? → Note the exact error, continue

- [ ] **Test endpoint path exists**
  ```bash
  curl -I "https://backend.bandarupay.pro/api/v1/demo-login"
  ```
  ✅ 200/400/401? → Endpoint exists
  ❌ 404? → Endpoint not found, go to "Route Issue" section

- [ ] **Test without auth headers**
  ```bash
  curl -X POST "https://backend.bandarupay.pro/api/v1" \
    -H "Content-Type: application/json"
  ```
  ✅ Any response? → Server is up
  ❌ Connection error? → Server issue

- [ ] **Test from different machine/network**
  If possible, test from another computer
  ✅ Works elsewhere? → Your network/firewall issue
  ❌ Fails everywhere? → Server issue

---

### Phase 3: Check CORS Configuration (If getting CORS error)

- [ ] **Check browser console for CORS error**
  Press F12 → Console tab
  ✅ See "Access-Control-Allow-Origin" error? → CORS issue
  ❌ See different error? → Different problem

- [ ] **Verify request headers (Browser DevTools)**
  F12 → Network tab → Click request
  Check request headers for:
  - `Origin: https://superadmin.bandarupay.pro`
  - `Access-Control-Request-Method: POST`

- [ ] **Verify response headers (Browser DevTools)**
  F12 → Network tab → Click request → Response headers
  Look for:
  - `Access-Control-Allow-Origin: https://superadmin.bandarupay.pro`
  - `Access-Control-Allow-Methods: POST, GET, OPTIONS`
  - `Access-Control-Allow-Headers: Content-Type, Authorization`

- [ ] **Test OPTIONS preflight (curl)**
  ```bash
  curl -X OPTIONS "https://backend.bandarupay.pro/api/v1/demo-login" \
    -H "Origin: https://superadmin.bandarupay.pro" \
    -H "Access-Control-Request-Method: POST" \
    -v
  ```
  ✅ 200 OK with CORS headers? → CORS is configured
  ❌ 404 or no CORS headers? → CORS not configured

---

### Phase 4: Check Server Status (If connection fails)

- [ ] **Check server logs**
  SSH into server:
  ```bash
  tail -f /path/to/backend/logs/app.log
  ```
  ✅ See requests coming in? → Server is receiving requests
  ❌ No requests? → Request not reaching server

- [ ] **Check if server process is running**
  ```bash
  ps aux | grep python  # For Python backend
  ps aux | grep node    # For Node backend
  ```
  ✅ Process running? → Server is up
  ❌ Not running? → Server crashed

- [ ] **Check if port is listening**
  ```bash
  netstat -tulpn | grep 8000  # Check specific port
  # or
  lsof -i :8000
  ```
  ✅ Shows listening? → Server is listening
  ❌ Nothing? → Server not listening on this port

- [ ] **Check server resource usage**
  ```bash
  free -h          # Memory
  df -h            # Disk
  top              # CPU
  ```
  ✅ Resources available? → No resource issue
  ❌ High usage? → Server might be struggling

---

### Phase 5: Check DNS Resolution (If DNS fails)

- [ ] **Test DNS resolution**
  ```bash
  nslookup backend.bandarupay.pro
  # or
  dig backend.bandarupay.pro
  ```
  ✅ Shows IP address? → DNS resolves
  ❌ "NXDOMAIN" or fails? → DNS issue

- [ ] **Check if IP is correct**
  ```bash
  nslookup backend.bandarupay.pro
  ```
  Note the IP address, then:
  ✅ Is it your server IP? → DNS correct
  ❌ Is it different? → DNS points to wrong server

- [ ] **Test direct IP connection**
  If DNS shows IP is `123.45.67.89`:
  ```bash
  curl -X POST "https://123.45.67.89/api/v1/demo-login" \
    -H "Host: backend.bandarupay.pro" \
    -H "Content-Type: application/json"
  ```
  ✅ Works? → DNS is issue
  ❌ Fails? → Server is issue

---

### Phase 6: Check SSL Certificate (If SSL error)

- [ ] **Check certificate validity**
  ```bash
  openssl s_client -connect backend.bandarupay.pro:443
  ```
  Look for:
  ✅ "Verify return code: 0 (ok)"? → Certificate valid
  ❌ "Verify return code: 1" or expired date? → Certificate issue

- [ ] **Check certificate expiration**
  ```bash
  openssl s_client -connect backend.bandarupay.pro:443 | grep "notAfter"
  ```
  ✅ Date in future? → Certificate valid
  ❌ Date in past? → Certificate expired

- [ ] **Test with curl ignoring cert (diagnosis only)**
  ```bash
  curl -k -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
    -H "Content-Type: application/json" \
    -d '{"username":"superadmin","password":"SuperAdmin@123"}'
  ```
  ✅ Works with -k? → Certificate is the issue
  ❌ Still fails with -k? → Different issue

---

### Phase 7: Analyze Response (When you get a response)

- [ ] **Identify the HTTP status code**
  ```
  ✅ 200 OK → Successful request
  ✅ 400 Bad Request → Request format wrong (but endpoint exists)
  ✅ 401 Unauthorized → Authentication failed (but endpoint exists)
  ✅ 403 Forbidden → Permission denied (but endpoint exists)
  ✅ 404 Not Found → Route doesn't exist
  ✅ 405 Method Not Allowed → Wrong HTTP method
  ✅ 429 Too Many Requests → Rate limited
  ❌ 500 Internal Server Error → Server error
  ❌ 502 Bad Gateway → Proxy/reverse proxy issue
  ❌ 503 Service Unavailable → Server overloaded
  ❌ 504 Gateway Timeout → Request timeout
  ```

- [ ] **Check response body for error message**
  ```bash
  curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
    -H "Content-Type: application/json" \
    -d '{"username":"superadmin","password":"SuperAdmin@123"}' | jq .
  ```
  Read error message for clues

---

## 🧪 PART 3: How to Test from Browser, curl, Postman

### Test 1: Browser Console (JavaScript)

**Code:**
```javascript
fetch('https://backend.bandarupay.pro/api/v1/demo-login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'superadmin',
    password: 'SuperAdmin@123'
  })
})
.then(r => r.json())
.then(data => console.log('Success:', data))
.catch(err => console.error('Error:', err))
```

**Run in:** F12 → Console tab → Paste code → Enter

**Expected Results:**
- ✅ **200 OK:** `Success: { access_token: "...", ... }`
- ✅ **400 Bad Request:** `Error: SyntaxError: Unexpected token...` (JSON parse error)
- ✅ **401 Unauthorized:** `Error: { detail: "Invalid credentials" }`
- ❌ **CORS Error:** `Error: TypeError: Failed to fetch` (Network error in console)
- ❌ **DNS Error:** `Error: TypeError: Failed to fetch` (Site unreachable)
- ❌ **Connection Refused:** `Error: TypeError: Failed to fetch` (Connection refused)

**What Each Result Means:**
- Success with token → Endpoint works perfectly
- 400/401/403 → Endpoint exists, credential issue
- CORS error → CORS not configured
- Failed to fetch → Network/DNS/firewall issue

---

### Test 2: curl Command Line

**Basic Test:**
```bash
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'
```

**Verbose Test (Shows headers and more info):**
```bash
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}' \
  -v
```

**With Timeout (test connection speed):**
```bash
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}' \
  --max-time 10 \
  -v
```

**Ignore SSL (diagnosis only - finds cert issues):**
```bash
curl -k -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}' \
  -v
```

**Test OPTIONS (CORS preflight):**
```bash
curl -X OPTIONS "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Origin: https://superadmin.bandarupay.pro" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

**Expected Results:**
- ✅ **200 OK:** `{ "access_token": "...", ... }`
- ✅ **400 Bad Request:** `{ "detail": "Invalid input", ... }`
- ✅ **401 Unauthorized:** `{ "detail": "Invalid credentials", ... }`
- ❌ **404 Not Found:** `{ "detail": "Not found", ... }`
- ❌ **Connection timeout:** `curl: (28) Operation timeout...`
- ❌ **Connection refused:** `curl: (7) Failed to connect to...`
- ❌ **DNS error:** `curl: (6) Could not resolve host...`
- ❌ **SSL error:** `curl: (60) SSL certificate problem...`

**What Each Result Means:**
- 200/400/401 → Endpoint reachable
- 404 → Endpoint doesn't exist at this path
- Timeout → Server slow or unreachable
- Connection refused → Server not listening
- DNS error → Domain doesn't resolve
- SSL error → Certificate problem

---

### Test 3: Postman

**Steps:**

1. **Create new request:**
   - Method: `POST`
   - URL: `https://backend.bandarupay.pro/api/v1/demo-login`

2. **Set headers:**
   - Click "Headers" tab
   - Add: `Content-Type: application/json`

3. **Set body:**
   - Click "Body" tab
   - Select "raw"
   - Select "JSON" from dropdown
   - Paste:
   ```json
   {
     "username": "superadmin",
     "password": "SuperAdmin@123"
   }
   ```

4. **Send request:**
   - Click "Send" button
   - Check response status and body

5. **Check headers (debugging):**
   - Click "Headers" in response
   - Look for `Access-Control-Allow-Origin` header

**Expected Results:**
- ✅ **Status 200:** Response body shows tokens
- ✅ **Status 400:** Response shows validation error
- ✅ **Status 401:** Response shows auth error
- ❌ **Status 404:** Endpoint not found
- ❌ **Status 500:** Server error - check server logs
- ❌ **Connection timeout:** Blue "Error" bar with message
- ❌ **Certificate error:** Red error message about SSL

**What Each Result Means:**
- 200/400/401 → Endpoint works, debug credentials
- 404 → Path is wrong or endpoint not registered
- 500 → Server-side error, check backend logs
- Timeout/Connection error → Server unreachable
- Certificate error → SSL issue

---

## 📊 PART 4: Expected Results & What They Mean

### Response Status Codes

| Status | Name | Meaning | Action |
|--------|------|---------|--------|
| **200** | OK | Success, endpoint works | Check response for tokens |
| **201** | Created | Resource created | Success |
| **400** | Bad Request | Invalid input format | Check request body format |
| **401** | Unauthorized | Authentication failed | Check credentials |
| **403** | Forbidden | Access denied | Check permissions/auth |
| **404** | Not Found | Endpoint doesn't exist | Check URL path, verify route registered |
| **405** | Method Not Allowed | Wrong HTTP method | Use POST not GET |
| **429** | Too Many Requests | Rate limited | Wait before retrying |
| **500** | Internal Server Error | Server error | Check backend logs |
| **502** | Bad Gateway | Proxy error | Check reverse proxy/load balancer |
| **503** | Service Unavailable | Server overloaded | Check server resources |
| **504** | Gateway Timeout | Request timeout | Server too slow or unresponsive |

### Network Error Messages (curl)

| Error | Meaning | Likely Cause | Check |
|-------|---------|-------|-------|
| `Could not resolve host` | DNS failed | DNS config wrong | `nslookup backend.bandarupay.pro` |
| `Failed to connect` | Connection refused | Server down/port wrong | `curl https://backend.bandarupay.pro` |
| `Operation timeout` | Request took too long | Server slow/firewall | `curl --max-time 30` |
| `SSL certificate problem` | Certificate invalid | Cert expired or wrong | `openssl s_client -connect...` |
| `Empty reply from server` | Server crashed mid-response | Server process died | Check server logs |
| `Connection reset by peer` | Server forcibly closed | Firewall/proxy issue | Test from different network |

### Browser CORS Errors

| Error Message | Meaning | Fix |
|-------|---------|-------|
| `Access-Control-Allow-Origin header missing` | CORS not enabled | Enable CORS in backend |
| `Origin 'https://superadmin.bandarupay.pro' not allowed` | Frontend origin not in allowed list | Add origin to CORS config |
| `Missing required header Content-Type` | CORS preflight failed | Add header to CORS `allowed_headers` |
| `Method POST not allowed by CORS policy` | POST not in allowed methods | Add POST to CORS `allowed_methods` |

---

## 🔐 PART 5: CORS Configuration (If CORS Issue)

### Current CORS Setup (in backend-api/main.py)

**Check if this exists:**
```python
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "https://backend.bandarupay.pro",
    "https://www.bandarupay.pro",
    "https://admin.bandarupay.pro",
    "https://customer.bandarupay.pro",
    "https://mds.bandarupay.pro",
    "https://retailer.bandarupay.pro",
    "https://superadmin.bandarupay.pro",  # ← Frontend URL
    "https://whitelable.bandarupay.pro",
    "https://backend.bandarupay.pro",
    # Development URLs
    "http://localhost:5172",  # ← Dev frontend port
    "http://localhost:8000",
    # ... more origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "Accept",
        "Origin", 
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=[
        "Content-Length",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials"
    ],
    max_age=600
)
```

### If CORS is the Issue

**Add missing frontend origin:**
```python
origins = [
    # ... existing origins
    "https://superadmin.bandarupay.pro",  # ← Your frontend URL
    "https://your-frontend-url.com",       # ← If different
]
```

**If using development:**
```python
origins = [
    # ... production origins
    "http://localhost:5172",   # Vite dev server
    "http://localhost:3000",   # If using different port
]
```

**After changes:**
1. Restart backend: `python main.py`
2. Test from browser again
3. Check for `Access-Control-Allow-Origin` header in response

### Verify CORS is Working

**Test preflight:**
```bash
curl -X OPTIONS "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Origin: https://superadmin.bandarupay.pro" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

**Expected response headers:**
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://superadmin.bandarupay.pro
Access-Control-Allow-Methods: POST, GET, OPTIONS, PUT, DELETE, PATCH
Access-Control-Allow-Headers: Content-Type, Authorization, Accept, ...
Access-Control-Max-Age: 600
```

---

## 🎯 PART 6: Confirm It's NOT a Frontend Bug

### Test 1: Direct Server Testing

**Skip frontend entirely:**
```bash
# Test directly from server
ssh user@backend.bandarupay.pro
curl -X POST "http://localhost:8000/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'
```

✅ **Works locally on server?** → Server is fine, issue is network/frontend
❌ **Fails on server?** → Server/endpoint issue

### Test 2: Different Frontend Test

**Test from completely different frontend:**
- Try from Postman (not browser)
- Try from curl (not browser)
- Try from different browser

✅ **Works from Postman/curl but not browser?** → Frontend/CORS issue
❌ **Fails everywhere?** → Server issue

### Test 3: Check Network in Browser DevTools

**Steps:**
1. Open Frontend in browser
2. Press F12 → Network tab
3. Try to login (triggers API call)
4. Look at the failed request
5. Click on it and check:

**Check these details:**
- **Request URL:** Is it exactly `https://backend.bandarupay.pro/api/v1/demo-login`?
- **Request Headers:** Does it include `Content-Type: application/json`?
- **Response Status:** What is the status? (if any response)
- **Response Headers:** Does it have CORS headers?
- **Type:** What does it show? (xhr, fetch, etc)

**Interpretation:**
- ✅ Status 200/400/401 + response → Server is responding, frontend can send requests
- ❌ Status 0 + No response headers → Network/CORS/server issue
- ❌ Request shows "Blocked by CORS policy" → CORS issue
- ❌ Request doesn't appear at all → Frontend not making request (UI logic bug)

### Test 4: Check Frontend Code is Correct

**Verify these in your frontend code:**
```javascript
// 1. Is URL correct?
const url = "https://backend.bandarupay.pro/api/v1/demo-login"
// ✅ Should have /api/v1 prefix
// ✅ Should use https not http
// ✅ Should be exact domain

// 2. Is method correct?
method: 'POST'  // Not GET
// ✅ Should be POST

// 3. Are headers correct?
headers: {
  'Content-Type': 'application/json'
}
// ✅ Should include Content-Type

// 4. Is body correct?
body: JSON.stringify({...})
// ✅ Should be JSON string

// 5. Is error handled?
.catch(err => console.error(err))
// ✅ Should show actual error in console
```

**Conclusion:**
- ✅ If frontend code is correct and you see actual HTTP responses (200/400/401) → **Server issue**
- ❌ If frontend code is correct but get network error (status 0) → **Network/CORS/server issue**
- ❌ If frontend code sends wrong data (no request in network tab) → **Frontend bug**

---

## 📋 PART 7: Server Log Analysis

### Location: Check Backend Logs

**For Python FastAPI backend:**
```bash
tail -f backend-api/logs/app.log
# or
tail -f /var/log/bandaru-pay/app.log
```

**Look for:**
```
✅ "POST /api/v1/demo-login HTTP/1.1" 200  → Request successful
✅ "POST /api/v1/demo-login HTTP/1.1" 401  → Auth failed but endpoint hit
❌ "POST /api/v1/demo-login HTTP/1.1" 404  → Endpoint doesn't exist
❌ No request logged at all               → Request not reaching server
❌ "ERROR" in logs                         → Server error
```

### Check Error Logs

**Look for:**
```
ERROR: [errno 104] Connection reset by peer
ERROR: [errno 111] Connection refused
ERROR: 500 Internal Server Error
ERROR: Unhandled exception in...
```

### Check Access Logs

**Most important: Verify request is being received**
```bash
tail -f /var/log/nginx/access.log  # If using nginx
# or
tail -f /var/log/apache2/access.log  # If using apache
```

**Look for:**
```
✅ backend.bandarupay.pro POST /api/v1/demo-login 200
✅ backend.bandarupay.pro POST /api/v1/demo-login 401
❌ backend.bandarupay.pro POST /api/v1/demo-login 404
❌ No request logged = request not reaching server
```

---

## 🚨 PART 8: Quick Decision Tree

```
Network Error on https://backend.bandarupay.pro/api/v1/demo-login

│
├─ [Test: curl -I https://backend.bandarupay.pro]
│
├─ Fails? → Connection error
│  ├─ Error: "Could not resolve host"
│  │  └─ DNS ISSUE → Run: nslookup backend.bandarupay.pro
│  │
│  ├─ Error: "Failed to connect to"
│  │  └─ CONNECTION REFUSED → Server down
│  │     └─ Check: ps aux | grep python
│  │
│  ├─ Error: "Operation timeout"
│  │  └─ TIMEOUT ISSUE → Server slow/unreachable
│  │
│  └─ Error: "SSL certificate problem"
│     └─ SSL ISSUE → openssl s_client -connect backend.bandarupay.pro:443
│
└─ Works? → Server is up
   │
   ├─ [Test: curl -X POST endpoint with body]
   │
   ├─ Status 404?
   │  └─ ROUTE NOT FOUND → Check backend router config
   │
   ├─ Status 500?
   │  └─ SERVER ERROR → Check backend logs
   │
   ├─ Status 200/400/401?
   │  └─ ENDPOINT WORKS → Check frontend
   │     ├─ [Test: curl -X OPTIONS with CORS headers]
   │     ├─ No CORS headers?
   │     │  └─ CORS NOT CONFIGURED → Add CORS middleware
   │     └─ Has CORS headers?
   │        └─ CORS OK → Check frontend code
   │           └─ Try from Postman/curl instead of browser
   │              ├─ Works?
   │              │  └─ FRONTEND BUG → Check fetch/axios code
   │              └─ Fails?
   │                 └─ FIREWALL/PROXY ISSUE → Test from different network
   │
   └─ Timeout?
      └─ SERVER SLOW → Check server resources
```

---

## 🔍 PART 9: Final Checklist - What to Report

When you've debugged, report these findings:

- [ ] **Connectivity Test:** `curl -I https://backend.bandarupay.pro`
  - Result: ________________

- [ ] **Endpoint Test:** `curl -X POST endpoint with body`
  - Status Code: ________________
  - Response: ________________

- [ ] **DNS Test:** `nslookup backend.bandarupay.pro`
  - Result: ________________

- [ ] **CORS Test:** `curl -X OPTIONS with CORS headers`
  - Headers in response: ________________

- [ ] **Server Logs:** `tail -f app.log`
  - Error found: ________________

- [ ] **Server Status:** `ps aux | grep python`
  - Process running: Y / N

- [ ] **Port Status:** `netstat -tulpn | grep 8000`
  - Listening: Y / N

- [ ] **Frontend Test:** Works in Postman/curl?
  - Y / N

- [ ] **CORS Header Origin:** 
  - From: ________________
  - Expected: ________________

---

## 💡 Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| curl: "Could not resolve host" | Check DNS: `nslookup backend.bandarupay.pro` |
| curl: "Failed to connect" | Start server: `python main.py` |
| curl: "SSL certificate problem" | Test with: `curl -k` (diagnose only) |
| 404 Not Found | Check route: `/api/v1/demo-login` vs `/demo-login` |
| Browser "Failed to fetch" | Check CORS headers in response |
| "Access-Control-Allow-Origin" missing | Enable CORS in backend |
| 500 Internal Server Error | Check backend logs: `tail -f app.log` |
| Connection timeout | Server too slow: check resources `top`, `free` |

---

**Use this guide to systematically identify the cause of your network error.**
**Start with Part 2 (Checklist) and work through each phase.**
