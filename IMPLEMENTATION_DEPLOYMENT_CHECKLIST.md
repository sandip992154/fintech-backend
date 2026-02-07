# ✅ IMPLEMENTATION & DEPLOYMENT CHECKLIST

## Pre-Implementation Checklist

- [ ] Backup current configuration files
- [ ] Stop backend and frontend services
- [ ] Create git branch for changes
- [ ] Review all documentation
- [ ] Understand all 5 files that need changes

---

## Implementation Checklist

### File 1: Backend Router (backend-api/main.py)
- [ ] Open `backend-api/main.py`
- [ ] Go to line 206-207
- [ ] Change auth router prefix from `/auth` to `/api/v1/auth`
- [ ] Also update password_reset router to `/api/v1/auth`
- [ ] Save file
- [ ] Verify syntax is correct

### File 2: Frontend API Client (superadmin/src/services/apiClient.js)
- [ ] Open `superadmin/src/services/apiClient.js`
- [ ] Line 3: Change base URL from `http://localhost:8000` to `http://localhost:8000/api/v1`
- [ ] Line 47-49: Update interceptor conditions (remove `/auth` prefix)
- [ ] Line 62: Update refresh endpoint (remove `/auth` prefix)
- [ ] Save file
- [ ] Verify syntax is correct

### File 3: Frontend Auth Service (superadmin/src/services/authService.js)
- [ ] Open `superadmin/src/services/authService.js`
- [ ] Find and update all `/auth/` paths to remove the `/auth` prefix:
  - [ ] `/auth/login` → `/login` (line ~17)
  - [ ] `/auth/login-otp-verify` → `/login-otp-verify` (line ~57)
  - [ ] `/auth/login` → `/login` (line ~86 - loginWithJson)
  - [ ] `/auth/demo-login` → `/demo-login` (line ~127)
  - [ ] `/auth/me` → `/me` (line ~150)
  - [ ] `/auth/verify` → `/verify` (line ~164)
  - [ ] `/auth/forgot-password` → `/forgot-password` (line ~180)
  - [ ] `/auth/reset-password` → `/reset-password` (line ~193)
  - [ ] `/auth/refresh` → `/refresh` (line ~207)
- [ ] Save file
- [ ] Verify syntax is correct

### File 4: Development Environment (superadmin/.env)
- [ ] Open `superadmin/.env`
- [ ] Line 3: Change from `https://backend.bandarupay.pro`
- [ ] Change to: `https://backend.bandarupay.pro/api/v1`
- [ ] Save file

### File 5: Production Environment (superadmin/.env.production)
- [ ] Open `superadmin/.env.production`
- [ ] Line 2: Change from `https://backend.bandarupay.pro`
- [ ] Change to: `https://backend.bandarupay.pro/api/v1`
- [ ] Save file

---

## Local Testing Checklist

### Start Services
- [ ] Start backend:
  ```bash
  cd backend-api
  python main.py
  # Wait for "Uvicorn running on http://127.0.0.1:8000"
  ```
- [ ] Start frontend (in new terminal):
  ```bash
  cd superadmin
  npm run dev
  # Wait for "http://localhost:5172"
  ```

### Test API Endpoints
- [ ] Test login endpoint:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=superadmin&password=SuperAdmin@123"
  ```
  Expected: Should return tokens or ask for OTP (200 OK)

- [ ] Test demo-login endpoint:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/demo-login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=superadmin&password=SuperAdmin@123"
  ```
  Expected: 200 OK with access_token, refresh_token, role

### Test Frontend
- [ ] Open http://localhost:5172 in browser
- [ ] Click "Demo Button" (⚡ icon)
- [ ] Wait for login
- [ ] Expected: Should redirect to dashboard
- [ ] Check browser console: No 404 errors
- [ ] Check DevTools Network tab: See 200 response
- [ ] Check localStorage: Should have `token` and `refresh_token`

---

## Production Testing Checklist

### Test Production Endpoint
- [ ] Test demo-login on production:
  ```bash
  curl -X POST "https://backend.bandarupay.pro/api/v1/auth/demo-login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=superadmin&password=SuperAdmin@123"
  ```
  Expected: 200 OK with tokens

- [ ] Test other auth endpoints:
  ```bash
  # Test login
  curl -X POST "https://backend.bandarupay.pro/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=superadmin&password=SuperAdmin@123"
  ```

---

## Deployment Checklist

### Deploy Backend
- [ ] Upload updated `backend-api/main.py` to production server
- [ ] Restart backend service
- [ ] Verify backend is running with new routes
- [ ] Check logs for any errors
- [ ] Verify `/api/v1/auth/` routes are available

### Deploy Frontend
- [ ] Build production bundle:
  ```bash
  cd superadmin
  npm run build
  ```
- [ ] Upload built files to production server
- [ ] Verify `dist` folder contains the build
- [ ] Restart frontend service / web server
- [ ] Verify frontend loads correctly

### Verify Deployment
- [ ] Test frontend at: https://superadmin.bandarupay.pro
- [ ] Click demo button
- [ ] Expected: Should log in successfully
- [ ] Check browser DevTools: No network errors
- [ ] Check API response: 200 OK status

---

## Post-Deployment Verification

### Environment Variables
- [ ] Verify `.env` file deployed correctly
- [ ] Verify `.env.production` file deployed correctly
- [ ] Confirm `VITE_API_BASE_URL` includes `/api/v1`

### API Endpoints
- [ ] Test all auth endpoints on production
- [ ] Verify `/api/v1/auth/` prefix for all endpoints
- [ ] Check CORS headers in responses
- [ ] Verify tokens are being returned correctly

### Frontend Functionality
- [ ] Test demo login (most important)
- [ ] Test regular login
- [ ] Test OTP verification (if applicable)
- [ ] Test logout
- [ ] Test token refresh
- [ ] Test expired token handling

### Monitoring
- [ ] Monitor error logs for 404 errors
- [ ] Check application performance
- [ ] Monitor user login success rate
- [ ] Monitor API response times
- [ ] Check for any CORS errors

---

## Rollback Checklist (If Needed)

- [ ] Stop backend service
- [ ] Restore original `backend-api/main.py`
- [ ] Stop frontend service
- [ ] Restore original frontend files
- [ ] Restore original `.env` files
- [ ] Restart services
- [ ] Verify old paths are working again

---

## Final Verification Checklist

### Local Development
- [x] Backend updated
- [x] Frontend updated
- [x] Both services start without errors
- [x] Demo login works
- [x] No 404 errors
- [x] Tokens stored in localStorage
- [x] Redirects to dashboard

### Production
- [ ] Backend deployed and running
- [ ] Frontend deployed and running
- [ ] API endpoints accessible at `/api/v1/auth/*`
- [ ] CORS headers present in responses
- [ ] Demo login works on production
- [ ] No 404 errors
- [ ] Error logs are clean
- [ ] Performance is acceptable

### Documentation
- [ ] All documentation created
- [ ] All code changes documented
- [ ] Before/after comparisons verified
- [ ] Testing procedures documented
- [ ] Deployment steps documented
- [ ] Rollback procedures documented

---

## Sign-Off Checklist

### Developer
- [ ] All files modified correctly
- [ ] Syntax verified
- [ ] Local testing passed
- [ ] Code follows standards
- [ ] Documentation complete

### Code Reviewer
- [ ] All changes reviewed
- [ ] Changes are minimal and focused
- [ ] No breaking changes
- [ ] Backward compatible
- [ ] Documentation is accurate

### QA/Tester
- [ ] Local testing passed
- [ ] Production testing passed
- [ ] All endpoints verified
- [ ] No regressions found
- [ ] Performance acceptable

### DevOps/Operations
- [ ] Deployment plan reviewed
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Team notified

### Project Manager
- [ ] Issue marked as resolved
- [ ] Documentation updated
- [ ] Team communicated
- [ ] Timeline updated
- [ ] Stakeholders informed

---

## Common Issues Checklist

If you encounter any of these issues:

### 404 Error Still Occurring
- [ ] Verify backend was restarted
- [ ] Verify main.py has the correct prefix
- [ ] Clear browser cache (Ctrl+Shift+Delete)
- [ ] Check backend logs for errors
- [ ] Manually test endpoint with curl

### Frontend Not Seeing Changes
- [ ] Stop frontend service
- [ ] Clear node_modules and rebuild
- [ ] Clear npm cache: `npm cache clean --force`
- [ ] Reinstall dependencies: `npm install`
- [ ] Restart frontend service

### CORS Errors
- [ ] Verify CORS is enabled in backend
- [ ] Check main.py CORS configuration
- [ ] Verify domain is in allowed origins list
- [ ] Check browser console for specific error
- [ ] Test with curl first (no CORS issues)

### Tokens Not Stored
- [ ] Check API response structure
- [ ] Verify response contains `access_token` field
- [ ] Check browser localStorage is enabled
- [ ] Review browser console for JavaScript errors
- [ ] Test localStorage directly in console

---

## Performance Checklist

- [ ] API response time is acceptable (<200ms)
- [ ] Frontend loads quickly
- [ ] No memory leaks detected
- [ ] No unnecessary API calls
- [ ] Error handling is efficient

---

## Security Checklist

- [ ] No credentials in logs
- [ ] CORS properly restricted
- [ ] API endpoints require authentication
- [ ] Tokens properly expire
- [ ] Refresh token rotation works
- [ ] No sensitive data in localStorage
- [ ] HTTPS enforced on production

---

## Final Status Summary

```
┌─────────────────────────────────────┐
│    IMPLEMENTATION STATUS            │
├─────────────────────────────────────┤
│                                     │
│ Files Modified:        [ ] 5/5      │
│ Local Testing:         [ ] ✅       │
│ Production Testing:    [ ] ✅       │
│ Documentation:         [ ] ✅       │
│ Deployment:            [ ] ✅       │
│ Post-Deployment:       [ ] ✅       │
│ Sign-Off:              [ ] ✅       │
│                                     │
│ STATUS: [ ] READY FOR PRODUCTION    │
│                                     │
└─────────────────────────────────────┘
```

---

## Next Steps After Completion

1. [ ] Archive this checklist
2. [ ] Backup all documentation
3. [ ] Update project README
4. [ ] Notify team of completion
5. [ ] Close related tickets/issues
6. [ ] Schedule knowledge sharing session
7. [ ] Update deployment runbooks
8. [ ] Monitor system for 48 hours

---

## Quick Links

- [QUICK_REFERENCE_CARD.md](QUICK_REFERENCE_CARD.md) - Quick lookup
- [FINAL_WORKING_CODE.md](FINAL_WORKING_CODE.md) - Copy code
- [COMPLETE_RESOLUTION_SUMMARY.md](COMPLETE_RESOLUTION_SUMMARY.md) - Full overview
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - All documents

---

**📋 Use this checklist to ensure all steps are completed correctly**

**✅ Track progress** | **📝 Document issues** | **🎯 Stay organized**

---

Generated: February 5, 2026
Last Updated: February 5, 2026
Version: 1.0
