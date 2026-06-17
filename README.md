# MyWeblogC — Bilingual Weblog with Template Management

A full-featured weblog application built with **Flask + MongoDB** supporting **English and Persian (فارسی)** content.

---

## Features

| Feature | Description |
|---------|-------------|
| **Template Scanner** | Upload any HTML/CSS/JS template → auto-extracts all sections |
| **Section Editor** | Edit each section's content (rich text) and CSS per language |
| **Bilingual** | All content fields have English + Persian variants |
| **Categories** | Hierarchical categories/subcategories shown in nav menu |
| **Posts** | Posts with custom CSS/JS, assigned to categories |
| **Auth** | Admin and user roles; user profile page |
| **Responsive** | Bootstrap 5, RTL support for Persian |

---

## Prerequisites

- **Python 3.10+**
- **MongoDB** running locally (default port `27017`)

### Install MongoDB (if not installed)

Download from https://www.mongodb.com/try/download/community and install.
Start the service:
- Windows: MongoDB runs as a service automatically after install
- Or start manually: `"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe"`

---

## Local Setup & Run

### Step 1 — Create virtual environment

```bash
cd "d:\learning\python learning\django\myWeblogC"
python -m venv venv
```

### Step 2 — Activate virtual environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment

The `.env` file is already created with defaults. Edit it if needed:

```
MONGO_URI=mongodb://localhost:27017/myweblogc
SECRET_KEY=change-this-to-a-random-secret-key
FLASK_ENV=development
```

### Step 5 — Run the application

```bash
python run.py
```

The app starts at: **http://localhost:5000**

---

## Default Admin Account

On first run, an admin account is created automatically:

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

**Change this password after first login!**

---

## How to Use

### 1. Upload a Template
1. Login as admin → **Admin Panel → Templates → Upload Template**
2. Upload an `.html` file or paste HTML content
3. The system extracts all sections automatically (looks for `id` attributes on `<section>`, `<header>`, `<footer>`, etc.)
4. After upload, click **Sections** to see all extracted sections

### 2. Edit Sections
1. Click **Edit Section** on any section
2. Edit **English content** (rich text editor)
3. Add **Persian content** in the FA tab (right-to-left)
4. Add custom **CSS** per section per language
5. Save → activate the template from the template list

### 3. Create Categories
1. **Admin → Categories → Add Category**
2. Fill English name (required) + Persian name
3. Leave "Parent Category" empty for top-level, or select a parent for subcategories
4. Categories appear in the navigation menu automatically

### 4. Create Posts
1. **Admin → Posts → New Post**
2. Fill English title (required) + Persian title
3. Write content in the EN/FA tabs using the rich text editor
4. Add custom CSS/JS if needed
5. Select a category
6. Check "Published" to make it live
7. Posts appear in the menu by category

### 5. Switch Language
- Click the **FA** / **EN** button in the navbar or admin sidebar
- The site switches to Persian (RTL) or English

---

## Project Structure

```
myWeblogC/
├── run.py                      # Entry point
├── requirements.txt
├── .env                        # Environment variables
├── app/
│   ├── __init__.py             # App factory
│   ├── config.py               # Configuration
│   ├── extensions.py           # Flask extensions
│   ├── models/
│   │   ├── user.py             # User model + auth
│   │   ├── template.py         # Template & section operations
│   │   ├── category.py         # Category CRUD
│   │   └── post.py             # Post CRUD
│   ├── routes/
│   │   ├── auth.py             # Login / Register / Logout
│   │   ├── admin/__init__.py   # All admin routes
│   │   └── public/__init__.py  # Public website routes
│   ├── utils/
│   │   ├── template_parser.py  # HTML section extractor
│   │   └── helpers.py          # Utilities
│   ├── static/
│   │   ├── css/                # Stylesheets
│   │   ├── js/                 # JavaScript
│   │   └── uploads/            # User uploads
│   └── templates/
│       ├── base.html           # Public base layout
│       ├── admin/              # Admin panel templates
│       ├── auth/               # Login / Register pages
│       └── public/             # Website pages
```

---

## MongoDB Collections

| Collection | Purpose |
|-----------|---------|
| `users` | Admin and customer accounts |
| `site_templates` | Uploaded HTML templates |
| `sections` | Editable sections extracted from templates |
| `categories` | Hierarchical category tree |
| `posts` | Blog posts with bilingual content |
