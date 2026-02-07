# ⚡ QUICK TESTING REFERENCE - API_NETWORK_ERROR

**Endpoint:** `https://backend.bandarupay.pro/api/v1/demo-login`

---

## 🚀 Quick Tests (Copy & Run)

### Test 1: Browser Console (Fastest)
```javascript
fetch('https://backend.bandarupay.pro/api/v1/demo-login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'superadmin', password: 'SuperAdmin@123'})
}).then(r => r.json()).then(d => console.log('✅', d)).catch(e => console.error('❌', e))
```
**Open:** Browser → F12 → Console → Paste → Enter
**See:** Success or detailed error message

---

### Test 2: Basic curl
```bash
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'
```
**See:** HTTP status and response body

---

### Test 3: curl Verbose (Shows all details)
```bash
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}' -v
```
**See:** Request headers, response headers, status code

---

### Test 4: Check If Server is Up
```bash
curl -I https://backend.bandarupay.pro
```
**See:** Any HTTP response = server is up

---

### Test 5: Check If Endpoint Exists
```bash
curl -I "https://backend.bandarupay.pro/api/v1/demo-login"
```
**See:** 
- 404 = endpoint doesn't exist
- 200/400/401 = endpoint exists

---

### Test 6: Test CORS Preflight
```bash
curl -X OPTIONS "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Origin: https://superadmin.bandarupay.pro" \
  -H "Access-Control-Request-Method: POST" -v
```
**See:** CORS headers in response (Access-Control-Allow-*)

---

### Test 7: DNS Check
```bash
nslookup backend.bandarupay.pro
```
**See:** IP address of server

---

### Test 8: Direct Local Test (SSH to server first)
```bash
curl -X POST "http://localhost:8000/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}'
```
**See:** Does endpoint work locally on server?

---

### Test 9: Ignore SSL (Diagnose certificate issues)
```bash
curl -k -X POST "https://backend.bandarupay.pro/api/v1/demo-login" \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"SuperAdmin@123"}' -v
```
**See:** Works = SSL certificate is issue

---

### Test 10: Check Server is Listening
```bash
netstat -tulpn | grep 8000
```
**See:** If port 8000 shows LISTEN

---

---

## 📊 Response Codes Quick Reference

| Code | Name | Meaning |
|------|------|---------|
| 200 | OK | ✅ Success |
| 400 | Bad Request | Input format wrong |
| 401 | Unauthorized | Wrong credentials |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Server Error | Backend bug |
| 502 | Bad Gateway | Proxy error |
| 504 | Timeout | Server too slow |

---

## 🎯 Expected Results

### ✅ Good Responses
```bash
# When working perfectly:
curl -X POST "https://backend.bandarupay.pro/api/v1/demo-login" ...
# Returns HTTP 200 with:
{
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "token_type": "bearer",
  "role": "super_admin"
}
```

### ✅ Also OK (Endpoint exists, different error)
```bash
# HTTP 401 (bad credentials but endpoint exists):
HTTP/1.1 401 Unauthorized
{"detail": "Invalid credentials"}

# HTTP 404 (endpoint not registered):
HTTP/1.1 404 Not Found
{"detail": "Not found"}
```

### ❌ Network Errors (Something's broken)
```bash
# DNS fails:
curl: (6) Could not resolve host backend.bandarupay.pro

# Connection refused:
curl: (7) Failed to connect to backend.bandarupay.pro port 443

# Timeout:
curl: (28) Operation timeout after...

# SSL certificate:
curl: (60) SSL certificate problem: certificate has expired
```

---

## 🔧 CORS Quick Fix

If you see "Access-Control-Allow-Origin" missing:

**In your backend `main.py`, ensure this exists:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://superadmin.bandarupay.pro"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True
)
```

**Then restart backend:**
```bash
python main.py
```

---

## 📋 Decision Tree

```
Error on frontend?
├─ Can you curl the endpoint? 
│  ├─ Yes (200/400/401) → CORS or frontend issue
│  └─ No (curl error) → Server/network issue
└─ Check browser DevTools (F12)
   ├─ See HTTP response → Frontend issue
   └─ See "Failed to fetch" or "0" status → Network issue
```

---

## ✅ Final Confirmation

**When it's working:**
1. ✅ Browser shows login successful
2. ✅ curl shows 200 with tokens
3. ✅ Postman shows 200 with tokens
4. ✅ Browser DevTools shows 200 status
5. ✅ Server logs show the request

**Start with this document, then read the full guide if needed.**
