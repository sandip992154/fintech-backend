# Wallet Flow - Complete Testing Guide

## Fixed Issues:
1. ✅ Backend parameter order - `data: WalletTopupRequest = Body(...)` now comes LAST
2. ✅ Frontend refresh mechanism - Custom event system added
3. ✅ Dashboard sync - MyWallet listens to wallet updates
4. ✅ Automatic refresh - After adding funds, balance and history auto-update

## Complete Wallet Flow:

### Step 1: Add Funds
1. Open app → `http://localhost:5172`
2. Click **"Super Admin wallet"** button (top right corner)
3. Modal opens with form
4. Enter amount (e.g., 1000)
5. Enter description (e.g., "Initial load")
6. Click **"Add Funds"** button

### Expected Behavior During Step 1:
✅ Form validates - amount required and > 0
✅ Loading spinner shows during submission
✅ Success toast notification: "₹1000.00 added to wallet successfully!"
✅ Form clears
✅ Modal closes

### Step 2: Auto Refresh
After modal closes:
✅ Custom event "walletUpdated" is dispatched
✅ MyWallet page receives event
✅ WalletBalanceCard refreshes data
✅ WalletHistory refreshes transactions

### Step 3: View Updated Balance
Go to dashboard or wallet page:
✅ Balance card shows new balance (₹1000.00)
✅ "Refresh" button available to manually refresh

### Step 4: View Transaction History
Scroll down to see transaction history:
✅ Shows date & time
✅ Shows transaction type (credit/debit)
✅ Shows amount (with currency formatting)
✅ Shows description/remark
✅ Shows balance after transaction
✅ Shows reference ID

## API Endpoints Verification:

### POST /api/v1/transactions/wallet/topup/{user_id}
```bash
curl -X POST "http://localhost:8000/api/v1/transactions/wallet/topup/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"amount": 1000, "remark": "Test load"}'
```

Expected Response:
```json
{
  "success": true,
  "message": "Wallet topped up successfully",
  "data": {
    "id": 1,
    "user_id": 1,
    "balance": 1000.0,
    "transaction_id": "TOPUP12345678",
    "amount_added": 1000,
    "remark": "Test load",
    "last_updated": "2026-02-15T22:05:00.000Z"
  }
}
```

### GET /api/v1/transactions/wallet/{user_id}/transactions
```bash
curl "http://localhost:8000/api/v1/transactions/wallet/1/transactions?limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected Response:
```json
{
  "success": true,
  "data": {
    "wallet_id": 1,
    "wallet_balance": 1000.0,
    "transactions": [
      {
        "id": 1,
        "amount": 1000,
        "type": "credit",
        "reference_id": "TOPUP12345678",
        "remark": "Test load",
        "balance_after": 1000.0,
        "created_at": "2026-02-15T22:05:00.000Z"
      }
    ],
    "total_count": 1,
    "limit": 10,
    "offset": 0
  }
}
```

## Troubleshooting:

### Error: "Validation error" with "query.amount: Field required"
**Cause**: Backend parameter order issue
**Fix**: ✅ FIXED - Put Depends parameters before Body parameter

### Error: Balance not updating
**Cause**: Refresh not triggered
**Fix**: 
- Click "Refresh" button on wallet card
- Or check browser console for errors
- Or navigate away and back to page

### Error: Transaction history empty
**Cause**: Wallet not created yet
**Fix**: Create wallet first by clicking "Create Wallet" button

### Error: Amount showing as 0
**Cause**: Response format mismatch
**Fix**: Check network tab to verify API response structure

## Manual Testing Checklist:

- [ ] Add funds from Header wallet button
- [ ] See success notification
- [ ] Check balance updates automatically
- [ ] Check transaction appears in history
- [ ] Check description/remark is saved
- [ ] Check date/time is correct
- [ ] Click Refresh button - balance refreshes
- [ ] Add another amount
- [ ] See both transactions in history with correct order (newest first)
- [ ] Check pagination if > 10 transactions
