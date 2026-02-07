Business Requirement Document (BRD)
For B2B2C Fintech Software Development

1. Introduction
   • Document Purpose: Define business requirements for building a B2B2C digital payments & fintech platform.

• Target Audience: Merchants ( Admin & White Label Partners), Agents ( Master Distributors, Distributors & retailors ) and customers ( End users) , API Users , License Buyers ( BBPS ), Incorporation services, 3rd Party referrals,

• Vision: Create a secure, scalable, and user-friendly platform for Recharges & Bill payments, Banking, Tours & Travel , Loans and Insurance services in a B2B2C model. 2. Business Objectives
• Enable Merchants, Agents and customers to offer digital financial services.

• Provide users ( Master distributors, Distributors, retailors and customers ) with seamless payment options (wallets, UPI, cards, net banking).

• Create multiple revenue streams via commissions, subscriptions, and value-added services.

• Build a scalable ecosystem supporting Recharge & Bill payments, Banking Services Insurance, Tours & Travels , Loans.

• Ensure regulatory compliance with RBI, NPCI, BBPS , BANKS and IT Acts. 3. Scope

• Major Work Scope:

• Separate Digital (Virtual) Wallet for Each Members
• Commission Distribution System from Super Admin to entire hierarchy
• Charges set up system for entire hierarchy
• API Pannel for Super Admin
• Fund Transfer / Return option
• KYC Validations / verifications
• On-boarding members
• Login with OTP & MPIN facility
• Subscription services facility
• Role Upgrade option
• Mapping Management
• Active/ De- Active services, members, schemes
• Pop up Notification for each action.
• Print Receipts
• Export Transactions Data with Excel and PDF
• Transaction status manual change option with Super Admin
• Permissions allowed / Dis-allowed facility
• Settlement management.
• Mobile apps (Android/iOS) + Web portal.
• Role-based dashboards & analytics.
• - Physical POS hardware purchase and Integrate Bank POS SDK and linking with Portal
• - Direct core banking system development (integration only).

• B2B2C hierarchy:

• Super Admin Owner Portal (WEB only)

• Admin Partner Merchant Portal (WEB Only)
• White Label Partner

• Master Distributor Agent
• Distributor Agent User Portal (WEB & APP also)
• Retailer Agent
• Customer (End User).

Note : APP will be Android Play store & IOS Store

• SERVICES :

• Recharge & Bill Payments
• Banking Services
• Loans Services
• Insurance Services
• Tours & Travels

• SUB - SERVICES:

• Recharges – Mobile Recharge, DTH Recharges, FASTAG Recharge

• Bill Payments – Electricity Bill, Water Bill, GAS Cylinder Booking, Credit Card Bill Payments, Internet Bill Payments, Postpaid Bill payments like other BBPS services

• Banking Services - AEPS, DMT, SUVIDHA DMT, PAYMENT GATEWAY, PAYOUT, E-POS, M-ATM, UPI COLLECTION PG, CMS, CREDIT CARD APPLY, PAN CARD APPLY

• Loans Services - Personal Loans, Business Loans, Housing Loans, vehicle Loans

• Insurance services - Life Insurance, Health Insurance, Motor Insurance, Term Insurance

• Tours - Hotel Bookings, Tour Packages

• Travels : IRCTC, BUS, FLIGHT

4. Stakeholders

• Super Admin (Company) – full controls compliance, system setup, and revenue.

• Admin Partner – – branded platform operators, Own API’s Integrate, Controls over downline members, revenue sharing control , create all downline members

• White Label Partner – branded platform operators, Controls over downline members, revenue sharing control , create all downline members

• Master Distributors – Create and manage Distributors , retailers & customers and do the services to customers like bill payments , transfers etc
• Distributors – Create and manage retailors & customers and do the services to customers like bill payments , transfers etc

• Retailors – Create and manage customers & do the services to customers like bill payments , transfers etc

• Customers – consumers of financial services for self use and will get cashbacks from company like scratch cards, loyaty points etc

Note : We should follow updates from Regulatory Authorities time to time – PG’s , Banks , RBI, NPCI, BBPS & Issue Invoices to Banks regarding each services

5. Functional Requirements
   • 5.1 Core Features

• Customer Web & App Features:

Wallet, accept payments (UPI, QR scan & pay), Wallet loading through Payment Gateway, Transfer from wallet to bank accounts by using Payout, Wallet Amount can be used for Bill payments, recharge, FASTAG Recharges, Travel bookings, hotel bookings & New insurance policies Purchase. And New loans and credit cards can apply, Transaction history, complaint raise, refunds, cashback & Scratch cards

• Retailer Web & APP Features:

• Onboard customers, Accept payments (QR, card, UPI), Wallet loading through Payment gateway , Transfer from wallet to bank accounts by using payouts , Wallet Amount can be use for Bill payments, recharge, FASTAG Recharges, Travel bookings, hotel bookings & New insurance policies Purchase. And New loans and credit cards can apply, Commission management & settlement tracking, complaint raise, , reports generate for each service

• Distributor Web & APP Features:

Onboard retailers & customers, accept payments (QR, card, UPI), Wallet loading through Payment Gateway, Transfer from wallet to bank accounts by using payouts, Wallet Amount can be used for Bill payments, recharge, FASTAG Recharges, Travel bookings, hotel bookings & New insurance policies Purchase. And New loans and credit cards can apply, Commission management & settlement tracking, complaint raise, reports generate for each service

• Master Distributor Web & App Features:

Onboard distributors , retailers & customers, accept payments (QR, card, UPI), Wallet loading through Payment Gateway, Transfer from wallet to bank accounts by using payouts, Wallet Amount can be used for Bill payments, recharge, FASTAG Recharges, Travel bookings, hotel bookings & New insurance policies Purchase. And New loans and credit cards can apply, Commission management & settlement tracking, complaint raise, reports generate for each service

• White label partners Web Features :

Branding, own domain, Onboard master distributors, distributors, retailers & customers , Commission management & settlement tracking, complaint raise, , Compliance reports (AML/KYC), reports generate for each services, User management, Role-based access

• Admin Partner Web Features :

Branding, own domain, 3rd party API’s also integrate , Onboard White label partners, master distributors, distributors, retailers & customers. Commission management & settlement tracking, complaint raise, , reports generate for each services , User management, Role-based access, Compliance reports (AML/KYC), Dispute & refund management.

• Super Admin (Owner) Web Features :

Branding, own domain, Any API integrate, Onboard Admins, White label partners, master distributors, distributors, retailers & customers. Commission management & settlement tracking, complaint raise, , reports generate for each services , User management, Role-based access, Compliance reports (AML/KYC), Dispute & refund management.

• API Pannel Features (web ):

All Integrated API’s will be controlled in this panel by super Admin like balances maintain in Each API , Providing API Pannel facility for Admins , Top Up Fund request by Admin and Approvals by Super Admin , Each API Transaction reports and controls

• 5.2 Integrations
• SMS API
• EMIAL API
• WHAT’S APP API
• KYC Verification & Validations API
• PG API
• PAYOUTAPI
• UPI COLLECTION API
• CREDIT CARD BILL PAYMENT API,
• BBPS API
• Recharge API
• AEPS API
• DMT API
• PAN CARD APPLY API
• IRCTC API
• FLIGHT BOOKING API
• BUS BOOKING API
• HOTEL BOOKING API
• INSURANCE APPLY API
• LOANS APPLY API
• CREDIT CARD APPLY API

6. Non-Functional Requirements
   • Security: PCI-DSS, ISO 27001 compliance, encryption (AES, TLS).
   • Scalability: Support 50M+ users & high transaction volumes.
   • Performance: Sub-second transaction response time.
   • Availability: 99.99% uptime with disaster recovery.
   • Compliance: RBI guidelines, data localization, AML/CFT rules.
7. Revenue Model
   • Commission from bill payments,PG,PAYOUT, recharge, AEPS, and DMT.
   • MDR on merchant transactions.
   • Subscription for white-label partners.
   • Ads & cross-selling (insurance, loans, investments).
8. Risks & Mitigation
   • Fraud Risk → Implement AI-based fraud detection.
   • Regulatory Changes → Continuous compliance monitoring.
   • Downtime Risk → Multi-cloud deployment & redundancy.
   • Double time fund credits into wallet risk
9. High-Level Architecture
   • Frontend: Mobile apps + web portal (React, Flutter, or Angular).
   • Backend: Microservices architecture (Node.js / Java Spring Boot).
   • Database: PostgreSQL, MongoDB, Redis for caching.
   • Cloud Infrastructure: AWS / Azure / GCP with Kubernetes.
   • Payment Integration: NPCI UPI APIs, card payment gateways, AEPS.
10. Deliverables
    • Mobile Apps (IOS & Android).
    • B2B2C Admin Portal.
    • APIs integrations.
    • Documentation (User manuals, API docs, Compliance reports).

Required Things :

1. Super Admin Pannel :

• Domain Mapping - https://superadmin.bandarupay.pro/
• Login –SMS OTP – SMS API – DLT MAP
• Login – EMAIL OTP – SMTP server
• Login – Whats App OTP- META
• Any OTP
• Login – MPIN - ?
• Login – Forgot Password ( Any otp) , Forgot MPIN ( Any Otp), Resent OTP ,
• Subscribe Services : Free services | paid services
• Services subscription charges set up for ADMIN & WL
• Subscription amount will be recovered from merchant wallet
• News Banner should run
• Notifications should be provided

A. Super Admin Dashboard :

• Super Admin Wallet load option - done
• Super Admin Wallet balance - Replace name In super admin wallet balance.

• Services categories like recharges & Bills, Banking services, Loans , Insurances , Tours and Travels, (add all services each category),

• Sub services list when we click on each category , like

       Recharge and bill payment ; MOBILE RECHARGES , DTH, BBPS , FASTAG Recharges(all information is added)

       Banking Services :AEPS, DMT, PAYMENT GATEWAY (add to SA), PAYOUT(add to SA), UPI collection PG(add to SA), E-POS,M-ATM(add to SA), CMS, CREDIT CARDS APPLY(add to SA), PAN CARD APPLY (add to SA).

       Loan Services ; Personal Loan, Home Loan, property Loan, Business Loan, Business over draft, Gold Loan, vehicle Loan (in loan services is not working)

      Insurance services(change name to Insurance) ; Health Insurance , vehicle Insurance, Life Insurance , Term Insurance ,  (remove loan repayment),gold loan (remove this )

     Tours & Travels(change in portal Tours & Travel) : Holiday packages (add this), Hotel bookings , IRCTC , BUS , FLIGHT

(In members customer should rediredt properly)
• Each Service related API transactions ( Success, failed, pending)
• Date filter - done
• Downline Users Count
• Profile - (role manager only upgrade not downgrade, can change manager in mapping manager, and integrate backend)
• Support Mobile & Mail id  
• Light & Dark Mode - completed

B. Resources :

• Scheme Manager (add all services and sub services, change operator name to slab, add drop down to all services like aeps , dmt , recharge, pg , payout etc. for multiple banks, in excel sheet add all members, add all category in edit commition)
• Default scheme
• Individual Scheme
• Scheme upload option through excel (need to prepare format accurate)
• Scheme download ( PDF + Excel)
• Scheme activate / deactive (SSIGN ONLY one package at a time)
• Create new scheme
• Scheme edit

C. Members :

• Admin (for add new admin add validation for email, pan card and addhar card, add validation api for pancard and addhar card from setu api, integration pending, while inactive user that time one title should show user is inactivted sucessfully, while user is inactive that time user should show user is inactive please connect with perspective mapping manager, while inactive user then its whole hirachy should be inactive, add status on the heading of active inactive button, name contains (admin name, mobile no, change role to email id, company profile company added date and domain, main wallet replace to Admin wallet and remove remaining, id stock users hirachy wise user count,

# action button transfer founds from user to selected user form super admin to admin, return admin wallet to super admin wallet

# action button ->scheme->change submit button to Assign Scheme, also add drop down for multiple bank schems

# add notification of action completed or failed with valid action name, while add stock that time super admin maintains user wise number wise staff when exist limit that time need to conncet mapping manager,

#action button ->permission->members add all hirachy user create , manage or manage kyc permission
#action button ->permission->members report show all service sub service report

# action button ->permission-> remove wallet fund report option

# action button ->permission-> remove aeps fund, also aeps fund reports, agents report

action button ->permission->portal services add all sub services

# action button ->permission->Transection also show all services or sub services

# action button ->permission->Transection editing also show all services or sub services

# action button ->permission->Transection status remove this

# action button ->permission-> user setting)

• White label
• Master Distributor
• Distributor
• Retailor
• Customer (it should redirect properly)
• Role Upgrade
• KYC management
• Member Edit information
• Scheme assigned
• Profile
• Permissions
• Active/ deactive member option

D. Fund Management :

• Fund Credit
• Fund Debit
• Fund Request
• Wallet Lock ( Globally & Individually )

E. Transaction History

• Bills & recharges  
• Banking Services
• Loans Services
• Insurance services
• Tours & Travels
• Each services txn status change option should be available
• Each transaction customer copy should be available
• Print customer copy
• Search filter by date, by name, by amount, by service etc
• Export option into excel & PDF

F. Reports

• Super Admin Account statement ( ledger )
• Downline user wise ledger report
• Commission reports

• Bills & recharges  
• Banking Services
• Loans Services
• Insurance services
• Tours & Travels
• Each services statistics
• Each services earning report
• Search filter by date, by name, by amount, by service etc
• Wallet credit fund report
• Wallet Debit fund report
• Fund Request Report

G. Help :

• Complaints ( AI chat boat)

H. Settings:

• Banner settings
• Quick Links
• API manager
• System setting
• System downtime control
• Members login history ( user wise/ Map tracking )
• Set transaction limits for each service

I. Notification Management :

• Web Notification
• App Notification
• User wise Notification
• Service Wise Notification
