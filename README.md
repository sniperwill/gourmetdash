# 🍽️ GourmetDash — Food Delivery System

A full-stack food delivery web application built with **Flask** (backend),
**MongoDB** (database), and **server-rendered HTML/CSS/JS** (frontend).
Supports three user roles: **Customer**, **Restaurant Owner**, and **Delivery Agent**.

---

## 📸 Preview

| Home Page          | Customer View     | Restaurant Dashboard |
| ------------------ | ----------------- | -------------------- |
| Browse restaurants | Filter by cuisine | Manage orders & menu |

---

## 🗂️ Project Structure

```
gourmetdash/
├── app.py ← Flask backend (all API routes)
├── db.py ← MongoDB connection + collections
├── config.py ← App configuration (.env loader)
├── flask_bcrypt.py ← Password hashing setup
├── flask_cors.py ← CORS configuration
├── seed.py ← Populate DB with demo data
├── requirements.txt ← Python dependencies
├── .env ← Your secret keys (you create this)
└── templates/
    └── index.html ← Frontend (all views in one file)

```

---

## ⚙️ Tech Stack

| Layer    | Technology                              |
| -------- | --------------------------------------- |
| Frontend | HTML, CSS, Vanilla JS (server-rendered) |
| Backend  | Python 3.x + Flask                      |
| Database | MongoDB                                 |
| Auth     | JWT (PyJWT) + Bcrypt password hashing   |

---

## ✅ Prerequisites

Before you begin, make sure you have these installed:

### 1. Python 3.8+

Download from → https://www.python.org/downloads/

> ⚠️ During install, **check "Add Python to PATH"**

Verify install:

```cmd
python --version
```

---

### 2. MongoDB Community Server

Download from → https://www.mongodb.com/try/download/community

**Steps:**

1. Download and run the installer (choose "Complete" setup)
2. Check **"Install MongoDB as a Service"** — this makes it start automatically
3. After install, MongoDB runs at `mongodb://localhost:27017` by default

Verify MongoDB is running:

```cmd
mongosh
```

You should see a `>` prompt. Type `exit` to quit.

> 💡 If `mongosh` is not found, also install **MongoDB Shell** from:
> https://www.mongodb.com/try/download/shell

---

### 3. Git (optional, for cloning)

Download from → https://git-scm.com/downloads

---

## 🚀 Setup — Step by Step

### Step 1 — Get the project files

**Option A — Clone with Git:**

```cmd
git clone https://github.com/your-username/gourmetdash.git
cd gourmetdash
```

**Option B — Download ZIP:**

1. Download and extract the ZIP
2. Open CMD and navigate to the folder:

```cmd
cd D:\harshita\resume+portfolio\price guide\gourmetdash
```

---

### If package imports are missing

Run the install commands directly through the virtual environment. This avoids activation issues in PowerShell and works even when `pip` is not yet available.

```powershell
venv\Scripts\python.exe -m ensurepip --upgrade
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 2 — Create a Virtual Environment

A virtual environment keeps project packages isolated from your system Python.

```cmd
python -m venv venv
```

If the `venv` folder already exists, skip this step and just install the dependencies.

---

### Step 3 — Activate the Virtual Environment

**Command Prompt (CMD):**

```cmd
venv\Scripts\activate.bat
```

**PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

If you do not want to activate the environment, you can still run commands with `venv\Scripts\python.exe` directly.

> ⚠️ If PowerShell blocks it, run this once:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

✅ You'll know it worked when you see `(venv)` at the start of your prompt:

```
✅ Database seeded!
==========================================
Customer: ravi@example.com
Restaurant: rajesh@tajmahal.com
Delivery: rahul@delivery.com
Password: password123 (all accounts)
==========================================

```

---

### Step 7 — Run the App

```cmd
python app.py
```

You should see:

```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

Open your browser and go to → **http://localhost:5000**

🎉 **GourmetDash is live!**

---

## 👤 Demo Login Credentials

| Role             | Email               | Password    |
| ---------------- | ------------------- | ----------- |
| Customer         | ravi@example.com    | password123 |
| Restaurant Owner | rajesh@tajmahal.com | password123 |
| Delivery Agent   | rahul@delivery.com  | password123 |

---

## 🔌 API Endpoints Reference

All API routes are prefixed with `/api/`.
Protected routes require `Authorization: Bearer <token>` header.

### Auth

| Method | Endpoint         | Auth | Description               |
| ------ | ---------------- | ---- | ------------------------- |
| POST   | /api/auth/signup | ❌   | Register new account      |
| POST   | /api/auth/login  | ❌   | Login → returns JWT token |

### Restaurants

| Method | Endpoint                          | Auth          | Description            |
| ------ | --------------------------------- | ------------- | ---------------------- |
| GET    | /api/restaurants                  | ❌            | List all restaurants   |
| GET    | /api/restaurants/\<id\>           | ❌            | Get one restaurant     |
| PUT    | /api/restaurants/\<id\>           | 🔒 restaurant | Update restaurant info |
| GET    | /api/restaurants/\<id\>/analytics | 🔒 restaurant | Dashboard stats        |
| GET    | /api/restaurants/\<id\>/menu      | ❌            | Get full menu          |

### Menu Items

| Method | Endpoint         | Auth          | Description      |
| ------ | ---------------- | ------------- | ---------------- |
| POST   | /api/menu        | 🔒 restaurant | Add menu item    |
| PUT    | /api/menu/\<id\> | 🔒 restaurant | Edit menu item   |
| DELETE | /api/menu/\<id\> | 🔒 restaurant | Delete menu item |

### Orders

| Method | Endpoint                  | Auth        | Description          |
| ------ | ------------------------- | ----------- | -------------------- |
| POST   | /api/orders               | 🔒 customer | Place new order      |
| GET    | /api/orders               | 🔒 any      | Get orders (by role) |
| PUT    | /api/orders/\<id\>/status | 🔒 any      | Update order status  |

### Delivery

| Method | Endpoint                       | Auth        | Description             |
| ------ | ------------------------------ | ----------- | ----------------------- |
| GET    | /api/delivery/available-orders | 🔒 delivery | Orders ready for pickup |
| GET    | /api/delivery/earnings         | 🔒 delivery | Earnings summary        |
| PUT    | /api/delivery/profile          | 🔒 delivery | Update agent profile    |

### Search

| Method | Endpoint              | Auth | Description                   |
| ------ | --------------------- | ---- | ----------------------------- |
| GET    | /api/search?q=biryani | ❌   | Search restaurants and dishes |

---

## 🛑 Common Errors & Fixes

| Error                                          | Cause                          | Fix                                                           |
| ---------------------------------------------- | ------------------------------ | ------------------------------------------------------------- |
| `'venv\Scripts\activate' is not recognized`    | Using CMD, not PowerShell      | Use `venv\Scripts\activate.bat`                               |
| `Import "flask_bcrypt" could not be resolved`  | Pylance warning, not installed | `pip install flask-bcrypt`                                    |
| `ModuleNotFoundError: No module named 'flask'` | venv not activated             | Run `venv\Scripts\activate.bat` first                         |
| `ServerSelectionTimeoutError`                  | MongoDB not running            | Start MongoDB service from Windows Services                   |
| `Address already in use` on port 5000          | Another app using port 5000    | `python app.py` → change port at bottom of `app.py` to `5001` |
| `.env not found`                               | Missing `.env` file            | Create it manually as shown in Step 5                         |

---

## 🗄️ MongoDB Collections

| Collection        | Stores                                  |
| ----------------- | --------------------------------------- |
| `users`           | All users (customers, owners, agents)   |
| `restaurants`     | Restaurant profiles and settings        |
| `menu_items`      | All food items linked to restaurants    |
| `orders`          | Order history with status tracking      |
| `delivery_agents` | Agent profiles, ratings, delivery count |

To view your data visually, install **MongoDB Compass** (free GUI):
https://www.mongodb.com/try/download/compass

Connect with: `mongodb://localhost:27017`

---

## 🔄 Re-seeding the Database

If you want to reset all data back to demo state:

```cmd
python seed.py
```

> ⚠️ This **wipes all existing data** and re-inserts demo records.

---

## 📁 VS Code Setup Tips

1. Open the project folder: `File → Open Folder → gourmetdash`
2. Install recommended extensions:
   - **Python** (Microsoft)
   - **Pylance** (Microsoft)
   - **MongoDB for VS Code** (MongoDB Inc.)
3. Select your interpreter: `Ctrl+Shift+P` → **Python: Select Interpreter**
   → choose `./venv/Scripts/python.exe`

---

## 📄 License

This project is for educational purposes.

---

_Built with ❤️ using Flask + MongoDB_
