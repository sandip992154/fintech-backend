# BandruPay Superadmin Portal – Issues & Risk Audit (Backend + Superadmin UI)

> Scope: backend-api + superadmin (VS Code workspace), excluding virtual environments. Focused on authentication, OTP, wallet/transactions, and fintech-grade concerns.

## 1. Authentication System

- **[Critical] Demo login bypasses OTP and is active in production**  
  - Endpoint: `/api/v1/auth/demo-login` in `backend-api/services/auth/auth.py`.  
  - Frontend: `superadmin/src/services/authService.js` and `superadmin/src/pages/SignIn.jsx` call this for instant login.  
  - Behavior: accepts `superadmin / SuperAdmin@123`, skips OTP/email verification, returns full-access JWT with `super_admin` role.  
  - Render-deployed backend tests (`test_render_backend.py`) confirm the endpoint is exposed externally.  
  - **Risk:** Any attacker with hard-coded demo credentials gets full superadmin access without 2FA.

- **[Critical] Hard‑coded superadmin credentials used everywhere**  
  - `.env` contains `SUPERADMIN_USERNAME=superadmin` and `SUPERADMIN_PASSWORD=SuperAdmin@123`.  
  - Same credentials appear in tests, docs, and frontend demo flows (`DEMO_LOGIN_FIX.md`, `DEMO_BUTTON_IMPLEMENTATION.md`, `API_CONFIGURATION_FINAL.md`, `STATUS.md`, etc.).  
  - **Risk:** Industry-standard guidance for fintech forbids static admin credentials; they must be changeable, rotated, and not hard-coded.

- **[High] Access token lifetime is extremely long**  
  - `.env`: `ACCESS_TOKEN_EXPIRE_MINUTES=28800` (≈ 20 days) and `REFRESH_TOKEN_EXPIRE_DAYS=30`.  
  - In `auth.py` and `auth/utils.py`, access tokens pick up this long duration by default.  
  - **Risk:** Compromised access token gives almost month-long full access; for fintech, access tokens should typically be minutes to a few hours.

- **[High] Multiple overlapping login flows increase attack surface**  
  - `auth.py` exposes: 
    - `/login` (form, sends OTP).  
    - `/login-otp-verify` (verifies OTP, issues tokens).  
    - `/login-json` (JSON login + OTP) with special superadmin handling.  
    - `/demo-login` (OTP-bypass).  
    - Separate superadmin auth in `services/auth/superadmin_auth.py` and 2FA in `two_factor.py`.  
  - **Risk:** Lot of legacy paths and special cases (e.g., `login_json` has hard-coded superadmin password `Superadmin@123`) make it easy to miss a vulnerable route or inconsistent logic.

- **[Medium] Inconsistent password handling and reset flows**  
  - `init_superadmin` in `database/init_db.py` overwrites superadmin password from `.env` at each startup; UI password changes for superadmin are not authoritative.  
  - Password reset and change flows for other roles are implemented but not consistently enforced for superadmin.  
  - **Risk:** Operators can be confused; password rotation policies cannot be reliably enforced.

- **[Medium] Brute-force protection not clearly applied to all login flows**  
  - There is a `RateLimiter` class in `services/auth/rate_limiter.py`, but it is not obviously integrated with `/login`, `/login-json`, or `/demo-login`.  
  - OTP attempt limits exist in some flows (see OTP section), but classic password login attempts are not clearly rate-limited per IP/user.  
  - **Risk:** Credentials (especially hard-coded ones) can be brute-forced without strong rate limiting or account lockout.

## 2. OTP System & 2FA

- **[High] Two different OTP storage models and inconsistent hashing**  
  - Model A: `services/models/models.py::OTP` (table `otps`) – stores **plaintext** OTP codes as `String(10)`. Used by `/login`, `/login-otp-verify`, `/login-json`.  
  - Model B: `services/models/user_models.py::OTP` (table `otp_records`) – designed to store **HMAC‑SHA256 hashes** of OTPs with wider `String(64)` fields.  
  - `services/otp_service.py` correctly hashes OTPs in `OTPRequest` (another table `otp_requests`).  
  - **Risk:** Some OTP flows are secure (hashed) and others are not (plaintext), making it easier to misuse and weakening overall security.

- **[Medium] OTP validity and attempts inconsistent across flows**  
  - `otp_service.py` enforces `max_attempts=3` and expires OTPs properly for PIN/MPIN use cases.  
  - Login OTPs (`/login`, `/login-otp-verify`, `/login-json`) implement their own logic on `otps` table with:  
    - Simple 4‑digit numeric OTP, stored in plaintext.  
    - Basic cooldown via `settings.OTP_COOLDOWN_MINUTES` and `MAX_OTP_ATTEMPTS`, but not as strict as `otp_service.py`.  
  - **Risk:** Attackers can target weaker OTP implementations; complexity increases the chance of misconfigurations.

- **[Medium] Multiple OTP generators and email senders**  
  - `services/auth/utils.generate_otp`, inline `random.randint` in `auth.py`, separate `OTPService.generate_otp`, and profile/MPIN routers each have OTP generation and email sending paths (`email_utils`, `notification_utils`, `services.integrations.email_service.EmailService`).  
  - **Risk:** Hard to audit and uniformly secure; inconsistent randomness, rate limiting, and logging rules.

- **[Low] In-memory OTP router left unused**  
  - `services/auth/otp.py` defines an in-memory `otp_storage` and `/send-otp`, `/verify-otp` endpoints but is not mounted in `main.py`.  
  - **Risk:** Currently unused, but if mounted accidentally it would introduce a less controlled OTP channel.

## 3. Database Models (Wallet, Transactions, Commission)

- **[High] Monetary amounts use `Float` instead of precise decimal**  
  - `services/models/transaction_models.py`:
    - `Transaction.amount`, `Wallet.balance`, `WalletTransaction.amount`, `WalletTransaction.balance_after`, `CommissionStructure.commission_percentage`, `CommissionStructure.charge_percentage`, `CommissionStructure.min_amount`, `CommissionStructure.max_amount` all use `Float`.  
  - **Risk:** Fintech systems must avoid binary floating point due to rounding errors; use `Numeric(precision, scale)` / `Decimal` everywhere for money and rates.

- **[Medium] Wallet balance stored and also derived from transactions without strong constraints**  
  - `Wallet.balance` and `WalletTransaction.balance_after` are both tracked; wallet updates (e.g., in `services/business/commission.py`) manually increment `wallet.balance` + insert `WalletTransaction`.  
  - No DB-level constraints ensure that sum of wallet transactions equals wallet balance.  
  - **Risk:** Race conditions or partial failures can desync wallet balance from history; for fintech wallets, invariant checks and transactional integrity are critical.

- **[Medium] Service provider API credentials stored in plain text**  
  - `ServiceProvider.api_key` and `ServiceProvider.api_secret` are plain strings in `service_providers` table.  
  - **Risk:** If DB is compromised, all external API keys/secrets are immediately exposed. They should be encrypted at rest and/or stored in a dedicated secrets system.

- **[Low] Commented-out relationships and duplicated relationship definitions**  
  - `Wallet.user` relationship is commented out (while other code expects some user ↔ wallet navigation).  
  - `ServiceProvider.transactions` relationship is declared twice.  
  - **Risk:** Not directly a security issue, but signals model design inconsistency and potential ORM confusion.

## 4. Payment / Recharge / Wallet Flow

- **[High] No explicit idempotency or double‑spend protection on transactions**  
  - `Transaction.reference_id` is unique, which helps, but there is no transparent idempotency layer for API calls like wallet topup or money transfer (e.g., idempotency keys per client request).  
  - **Risk:** Network retries or client bugs can cause duplicate charges or credits.

- **[Medium] Settlement and payout flows not fully enforced at backend**  
  - Frontend `PortalSetting.jsx` and wallet/settlement UI screens expose settlement types and locked amounts, but corresponding backend enforcement is not clearly present (e.g., preventing transfers below locked amounts, per-role settlement rules).  
  - **Risk:** Business logic might be only partially implemented; financial constraints can be bypassed via API.

- **[Medium] Commission calculation correctness depends on `Float` and manual business logic**  
  - `services/business/commission.py::CommissionCalculator` uses `Decimal` for in-memory amounts but then writes via models using `Float`.  
  - Commission transactions and wallet updates are performed in a single DB session but without explicit transaction boundaries or row-level locking.  
  - **Risk:** Under concurrency, floating-point rounding and race conditions can produce mismatched commissions and balances.

- **[Low] Some transaction-related components still placeholder in frontend**  
  - Example: `CommissionWallet.jsx` returns just `CommissionWallet` text, indicating incomplete reporting UI.  
  - Risk is mainly completeness/UX, not core security, but indicates work-in-progress areas for a production fintech platform.

## 5. Config & Secrets Management

- **[Critical] Production secrets committed into the repo**  
  - `.env` contains:
    - `DATABASE_URL` with Render production Postgres credentials.
    - `SMTP_USERNAME` and `SMTP_PASSWORD` (Gmail app password).  
    - `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET`.  
    - `SECRET_KEY` for JWT.  
  - **Risk:** Anyone with repo access can connect to production DB, send emails, and forge JWTs.

- **[High] OTP hash secret has unsafe default**  
  - `OTPService` uses `OTP_HASH_SECRET` env var but can fall back to a hard-coded default if not set.  
  - **Risk:** If the default is ever used in any environment, all OTP hashes become predictable across deployments.

## 6. Monitoring, Auditing, and Compliance Gaps

- **[High] Limited security/audit logging for critical events**  
  - Login attempts, OTP generation/verification, wallet debits/credits, and commission payouts are not consistently logged in an audit trail table or external SIEM.  
  - **Risk:** Difficult to investigate fraud, disputes, or operational incidents — a core requirement for fintech systems.

- **[Medium] No explicit KYC/AML checkpoints in flows**  
  - User and agent onboarding flows do not clearly enforce KYC status before enabling high-risk operations (high-value transfers, payouts, bulk recharge).  
  - **Risk:** Regulatory exposure and higher fraud risk if used in production with real money.

- **[Medium] Rate limits and abuse detection not centralized**  
  - Some per-endpoint protections exist (e.g., OTP attempt caps), but there is no clear, global rate-limiting or anomaly-detection layer (per IP / per user / per API key).  
  - **Risk:** Susceptible to credential stuffing, OTP bombing, and API abuse.

## 7. Suggested Next Steps (High-Level)

- Lock down or remove `/api/v1/auth/demo-login` in any non-development environment; require real OTP/2FA for all superadmin access.  
- Rotate all committed secrets (DB, SMTP, Cloudinary, JWT, OTP hash) and migrate them to environment-specific secret stores; remove `.env` from version control.  
- Migrate all monetary fields to `Numeric(precision, scale)` and refactor wallet logic to be fully transactional and idempotent.  
- Unify OTP handling onto a single, hashed implementation (`otp_requests` / `otp_records`) and deprecate plaintext `otps` table.  
- Add comprehensive audit logging for auth, OTP, wallet, and commission events, and integrate with monitoring/alerting.  
- Tighten token lifetimes and centralize rate limiting and security policies suitable for a fintech-grade deployment.