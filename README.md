# SMR Motors – Modernized Bike Selling Marketplace

A modern, responsive, and secure pre-owned two-wheeler marketplace built for SMR Motors (Kelambakkam, Tamil Nadu). Upgraded with Google OAuth 2.0, TiDB Cloud MySQL-compatible connectivity with SSL/TLS, completely redesigned User & Admin Panels, secure multi-image uploads, and a comprehensive REST API.

---

## Key Features & Modernizations

1. **Google OAuth 2.0 Sign-In for Users**:
   - One-click Google Sign-In with Google Identity Services (GIS).
   - Backend ID token verification directly against Google OAuth servers.
   - Automatic registration for first-time users, instant linking for existing accounts.
   - Secure JWT session token issuance (7-day validity).
   - Zero exposure of OAuth secrets on the frontend.
   - Instant Demo/Local testing mode for development before production Google credentials are set.

2. **TiDB Cloud Database Migration**:
   - High-performance, distributed MySQL-compatible connection pooling using `mysql2`.
   - Native TLS/SSL encryption enabled by default (`TIDB_SSL=true`).
   - Automated startup migration and standalone migration runner (`npm run migrate`).
   - 8 normalized tables: `users`, `admins`, `bikes`, `enquiries`, `favorites`, `categories`, `contact_messages`, `admin_audit_logs`.
   - Resilient offline fallback store so the application runs smoothly even if external cluster credentials are being configured.

3. **Complete User Panel Redesign (`/profile.html`)**:
   - Executive dashboard cards: Total Enquiries, Listed Bikes, Approved Bikes, Pending Approvals, Favorites.
   - Google Profile display (Avatar, Full Name, Email, Phone number editor).
   - My Bike Listings: Add new listing with multi-image upload & preview, edit details, delete listing, check approval status & rejection reasons.
   - My Enquiries: View submitted enquiries, enquiry status, and administrator replies.
   - Saved Favorites: Wishlist saved bikes with instant removal.
   - Strict privilege escalation protection: Users cannot modify their role or grant themselves admin rights.

4. **Complete Admin Panel Redesign (`/admin.html`)**:
   - Isolated, secure administrator login system using bcrypt password verification.
   - Real-time marketplace metrics: Total users, active bikes, pending approvals, rejected listings, enquiries, contact messages.
   - Bike approval workflow: Approve listings or reject with custom feedback to the seller.
   - Price adjustment and "Mark as Sold Out" controls.
   - User management: Search, filter, view details, and manage user accounts.
   - Enquiry & Contact Message management: Update enquiry status (`pending`, `in_progress`, `completed`), submit replies, mark messages as read.
   - Immutable security audit log tracking all administrator actions.
   - In-portal admin password change.

5. **Multi-Image Upload System**:
   - Built with Multer and stored securely in `public/uploads/`.
   - Whitelisted MIME types: JPEG, PNG, WebP, AVIF.
   - File size validation (5MB max per image, max 6 images per listing).
   - Client-side image preview and removal before upload.

---

## Technology Stack

- **Runtime**: Node.js (v18+)
- **Backend Framework**: Express.js 4
- **Database**: TiDB Cloud (Distributed MySQL-compatible) / `mysql2` with SSL
- **Authentication**: Google OAuth 2.0 (Users) + Bcrypt & JWT (Admin & Users)
- **File Uploads**: Multer
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3, Bootstrap 5.3, SweetAlert2, FontAwesome 6

---

## Local Setup Instructions

### 1. Prerequisites
- Node.js (v18 or higher) installed on your system.
- An active internet connection for installing dependencies and connecting to TiDB Cloud.

### 2. Install Dependencies
Open your terminal in the project directory (`g:\SMRbikeSite-final`):
```bash
npm install
```

### 3. Environment Configuration
Copy the provided `.env.example` file to create `.env`:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Command Prompt / Bash
cp .env.example .env
```

Open `.env` in an editor and configure your credentials.

---

## How to Configure TiDB Cloud

1. Sign up or log into [TiDB Cloud](https://tidbcloud.com).
2. Create a Serverless Cluster (free tier available).
3. Click **Connect** and select **Node.js / MySQL2**.
4. Obtain your connection parameters:
   - Host (e.g., `gateway01.ap-southeast-1.prod.aws.tidbcloud.com`)
   - Port (Default: `4000`)
   - User (e.g., `xxxxxx.root`)
   - Password
   - Database (e.g., `smr_motors`)
5. Update your `.env` file:
   ```env
   TIDB_HOST=gateway01.ap-southeast-1.prod.aws.tidbcloud.com
   TIDB_PORT=4000
   TIDB_USER=your_tidb_username
   TIDB_PASSWORD=your_tidb_password
   TIDB_DATABASE=smr_motors
   TIDB_SSL=true
   ```
6. Run database migrations:
   ```bash
   npm run migrate
   ```
   This creates all 8 tables, indexes, default categories from `category.json`, sample inventory from `data.json`, and seeds the initial admin account.

---

## How to Configure Google OAuth 2.0

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "SMR Motors").
3. Navigate to **APIs & Services** > **OAuth consent screen**:
   - User Type: **External**
   - Fill in App Name ("SMR Motors") and support email.
   - Save and continue.
4. Navigate to **Credentials** > **Create Credentials** > **OAuth Client ID**:
   - Application type: **Web application**
   - Name: `SMR Motors Web Client`
   - **Authorized JavaScript origins**:
     - `http://localhost:5000`
     - `http://127.0.0.1:5000`
   - **Authorized redirect URIs**:
     - `http://localhost:5000/api/auth/google/callback`
5. Click **Create** and copy your **Client ID** and **Client Secret**.
6. Paste into your `.env`:
   ```env
   GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_CALLBACK_URL=http://localhost:5000/api/auth/google/callback
   ```
> *Note for local evaluation*: If `GOOGLE_CLIENT_ID` is not yet configured, the login page features an instant **Local Testing / Demo Mode** allowing you to test the complete user experience with one click!

---

## How to Create the First Secure Admin Account

Admin credentials must NEVER be placed in plaintext in source code or git. Use the built-in seed utility:

```bash
# Usage: node scripts/seed-admin.js <username> <email> <password>
npm run seed-admin admin admin@smrmotors.com YourSecurePassword123!
```

This generates a salt and bcrypt hash, saves the admin in the database, and outputs the exact `.env` variables to add:
```env
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@smrmotors.com
ADMIN_PASSWORD_HASH=<generated_bcrypt_hash>
```

---

## Starting the Application

To start the modernized SMR Motors server:
```bash
npm start
```
Or for auto-reloading development mode:
```bash
npm run dev
```

Once running, access the application in your browser:
- **Marketplace Homepage**: [http://localhost:5000/](http://localhost:5000/)
- **User Google Login**: [http://localhost:5000/userLogin.html](http://localhost:5000/userLogin.html)
- **User Dashboard**: [http://localhost:5000/profile.html](http://localhost:5000/profile.html)
- **Admin Console**: [http://localhost:5000/admin.html](http://localhost:5000/admin.html)
- **Sell a Bike**: [http://localhost:5000/bikeSelling.html](http://localhost:5000/bikeSelling.html)

---

## Running the Automated Test Suite

A complete test suite is included validating all 24 critical paths (Auth, Permissions, Database, Bike CRUD, Approval, Enquiries):
```bash
npm test
```
*(All 24 automated tests execute and report status).*

---

## REST API Reference

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/google` | Verify Google ID token & sign in | Public |
| `POST` | `/api/auth/demo-google` | Local development Google mock | Public |
| `GET` | `/api/auth/me` | Current user profile | User JWT |
| `POST` | `/api/auth/logout` | Session sign out | Public |
| `GET` | `/api/users/profile` | Get user profile | User JWT |
| `PUT` | `/api/users/profile` | Update user name & phone | User JWT |
| `GET` | `/api/users/dashboard` | Aggregated user stats | User JWT |
| `GET` | `/api/users/listings` | User's listed bikes | User JWT |
| `GET` | `/api/users/enquiries` | User's submitted enquiries | User JWT |
| `GET` | `/api/users/favorites` | User's saved favorites | User JWT |
| `POST` | `/api/users/favorites/:bikeId`| Save bike to favorites | User JWT |
| `DELETE`| `/api/users/favorites/:bikeId`| Remove from favorites | User JWT |
| `GET` | `/api/bikes` | List bikes (filter by price, brand, search)| Public |
| `GET` | `/api/bikes/:id` | Single bike details | Public |
| `POST` | `/api/bikes` | Create bike (multipart images) | Optional User |
| `PUT` | `/api/bikes/:id` | Update bike details | Owner / Admin |
| `DELETE`| `/api/bikes/:id` | Delete bike listing | Owner / Admin |
| `POST` | `/api/enquiries` | Submit bike enquiry | Optional User |
| `GET` | `/api/enquiries` | Retrieve enquiries | Admin / User |
| `POST` | `/api/contact` | Submit website contact form | Public |
| `POST` | `/api/admin/login` | Admin login & JWT generation | Public |
| `GET` | `/api/admin/dashboard` | Real-time admin metrics | Admin JWT |
| `GET` | `/api/admin/users` | List registered users | Admin JWT |
| `GET` | `/api/admin/bikes` | List bikes with approvals queue | Admin JWT |
| `PUT` | `/api/admin/bikes/:id/approve`| Approve pending bike listing | Admin JWT |
| `PUT` | `/api/admin/bikes/:id/reject`| Reject bike with reason | Admin JWT |
| `PUT` | `/api/admin/bikes/:id/price` | Update bike selling price | Admin JWT |
| `PUT` | `/api/admin/bikes/:id/soldout`| Mark bike as sold out | Admin JWT |
| `GET` | `/api/admin/messages` | View contact form messages | Admin JWT |
| `GET` | `/api/admin/audit-logs`| View immutable security audit logs | Admin JWT |
| `POST` | `/api/admin/change-password` | Update admin password | Admin JWT |

---

## License & Credits
© 2025 SMR Motors. All Rights Reserved.
