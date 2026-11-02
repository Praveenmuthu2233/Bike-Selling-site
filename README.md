# SMR Motors – Complete Website Modernization & Reorganization

A high-performance, modern pre-owned motorcycle marketplace engineered with **Google Identity Services OAuth 2.0**, **TiDB Cloud MySQL**, and a **premium automotive design system**.

---

## 📁 Project Architecture & Clean Folder Structure

```text
SMRbikeSite-final/
│
├── index.html                   # Modern Marketplace Homepage (Search, Filters, Inventory Grid)
├── about.html                   # About SMR Motors, 45-Point Inspection Standard & Team
├── contact.html                 # Showroom Contact, Hours, Location Map & Lead Form
├── login.html                   # Google Identity Services OAuth 2.0 Sign In & Demo Sandbox
├── register.html                # User Onboarding with Google Authentication
├── bike-details.html            # Vehicle Detail Page (Multi-Photo Viewer, Specs, Test Ride Booking)
├── sell-bike.html               # 100% Free Listing Submission with Drag-and-Drop Multi-Image Upload
├── sold-bikes.html              # Sold Motorcycles Gallery & Delivery Showcase
│
├── admin/                       # Dedicated Admin Management Console
│   ├── login.html               # Isolated Administrator Login
│   ├── dashboard.html           # Admin Portal (Stats, Approvals, Rejections with Reason, Enquiries)
│   ├── users.html               # User Management & Governance Directory
│   ├── css/
│   │   └── admin.css            # Admin Sidebar, Topbar, Modals & Data Tables
│   └── js/
│       └── admin.js             # Admin Logic, Approval Workflow & Audit Log Display
│
├── user/                        # Customer & Rider Dashboard
│   ├── dashboard.html           # Rider Overview & Summary Telemetry
│   ├── profile.html             # Profile Details, Phone Update & Privilege Protection
│   ├── my-listings.html         # User Listed Motorcycles, Review Status & Deletions
│   ├── enquiries.html           # Test Ride Requests & Seller Communications
│   └── favorites.html           # Bookmarked Vehicles Wishlist
│
├── assets/                      # Shared Static Resources
│   ├── css/
│   │   ├── style.css            # Design System (Theme Variables, Reset, Navbar, Footer)
│   │   ├── components.css       # Buttons, Cards, Badges, Modals, Toasts, Filters, Tables
│   │   ├── auth.css             # Google Buttons, Auth Cards, Security Notes
│   │   ├── user.css             # User Dashboard Layout & Profile Cards
│   │   └── responsive.css       # Mobile Drawer & Responsive Breakpoints
│   ├── js/
│   │   ├── config.js            # Base URL & Client Configuration
│   │   ├── api.js               # REST Client with JWT & Toast Notifications
│   │   ├── auth.js              # Google OAuth GIS & Session Handler
│   │   ├── main.js              # Header Scroll, Mobile Nav Drawer & Forms
│   │   └── marketplace.js       # Dynamic Inventory Loader, Search & Price Filters
│   ├── images/                  # Vehicle Photos & Branding Assets
│   └── icons/                   # Custom Icons & Graphics
│
├── sql/
│   └── schema.sql               # TiDB Cloud MySQL 8.0 DDL Schema for 8 Core Tables
│
├── config/
│   └── db.js                    # Database Bridge & Connection Pool Exporter
│
├── src/                         # Server Architecture
│   ├── config/
│   │   ├── db.js                # TiDB Cloud Connection Pool with SSL & In-Memory Fallback
│   │   └── initDb.js            # Automated Database Migrations & Initial Seed Data
│   ├── controllers/             # Express Route Handlers (Auth, Bikes, Users, Admin, Enquiries)
│   ├── middleware/              # Auth, AdminAuth, AuditLogger, Multer 5MB Multi-Image Upload
│   └── routes/
│       └── api.js               # REST API Routes mounted under /api
│
├── scripts/
│   ├── migrate.js               # CLI Migration Utility
│   └── seed-admin.js            # Admin Bcrypt Password Hashing & Seeder
│
├── tests/
│   └── api.test.js              # 27-Point Automated Verification Suite
│
├── server.js                    # Unified Express Server (APIs, Assets, Clean & Legacy Routes)
├── package.json                 # Node.js Dependencies & NPM Scripts
└── .env.example                 # Environment Variable Template
```

---

## 🎨 Unified Design System

- **Automotive Aesthetic**: Dark Mode Deep Midnight Slate (`#0B0F17`, `#121824`) with Racing Orange accents (`#FF6B00`).
- **Typography**: `Outfit` for bold modern automotive headings, `Plus Jakarta Sans` for clean legible UI typography.
- **Glassmorphism**: Translucent headers and modals with `-webkit-backdrop-filter: blur(16px)`.
- **Responsive Layouts**: Desktop, tablet, and mobile drawer views with smooth transitions.
- **Micro-Interactions**: Hover zoom on bike cards, animated toast notifications, and loading indicators.

---

## 🚀 Running the Project Locally

```powershell
# 1. Install dependencies
npm install

# 2. Run the 27-Point Automated Test Suite
npm test

# 3. Start development server with auto-reload
npm run dev

# 4. Or start standard production server
npm start
```

---

## 🌐 URLs & Navigation Directory

| Page | URL | Purpose |
| :--- | :--- | :--- |
| **Marketplace** | [http://localhost:5000/](http://localhost:5000/) | Live motorcycle inventory, search, and filters |
| **About Us** | [http://localhost:5000/about.html](http://localhost:5000/about.html) | Company history & 45-point inspection standards |
| **Contact Showroom** | [http://localhost:5000/contact.html](http://localhost:5000/contact.html) | Showroom address, hours & contact form |
| **User Sign In** | [http://localhost:5000/login.html](http://localhost:5000/login.html) | Google Identity Services OAuth & instant demo login |
| **User Register** | [http://localhost:5000/register.html](http://localhost:5000/register.html) | Google sign up and onboarding |
| **Sell Motorcycle** | [http://localhost:5000/sell-bike.html](http://localhost:5000/sell-bike.html) | Multi-image vehicle submission |
| **Sold Gallery** | [http://localhost:5000/sold-bikes.html](http://localhost:5000/sold-bikes.html) | Delivered bikes and trust metrics |
| **User Dashboard** | [http://localhost:5000/user/dashboard.html](http://localhost:5000/user/dashboard.html) | Rider overview and metrics |
| **User Profile** | [http://localhost:5000/user/profile.html](http://localhost:5000/user/profile.html) | Contact info and Google link |
| **My Listings** | [http://localhost:5000/user/my-listings.html](http://localhost:5000/user/my-listings.html) | Manage listings and view rejection feedback |
| **Admin Login** | [http://localhost:5000/admin/login.html](http://localhost:5000/admin/login.html) | Dedicated secure portal login |
| **Admin Console** | [http://localhost:5000/admin/dashboard.html](http://localhost:5000/admin/dashboard.html) | Vehicle approval/rejection, prices, enquiries |
| **User Governance** | [http://localhost:5000/admin/users.html](http://localhost:5000/admin/users.html) | Registered user directory & activation controls |

---

## 🔐 Credentials for Local Testing

- **User Demo Login**: Click **"Sign In as Demo Rider"** on `login.html` for instant local session.
- **Admin Portal**:
  - Username: `admin`
  - Password: `admin123`
