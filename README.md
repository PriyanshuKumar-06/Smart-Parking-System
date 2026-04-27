# 🚗 Smart Parking System

A university-level full-stack web application built with **Python Flask**, **SQLite**, and modern **HTML/CSS/JS**.

---

## 📁 Project Structure

```
SmartParkingSystem/
├── app.py                   # Main Flask application (all routes + logic)
├── database.db              # SQLite database (auto-created on first run)
├── requirements.txt         # Python dependencies
├── templates/
│   ├── base.html            # Base layout (navbar, flash messages)
│   ├── index.html           # Landing page
│   ├── login.html           # User login
│   ├── register.html        # User registration
│   ├── dashboard.html       # User dashboard + Chart.js donut chart
│   ├── parking.html         # Visual parking grid (click-to-book)
│   ├── book_slot.html       # Slot booking confirmation form
│   ├── my_bookings.html     # User's booking list
│   ├── profile.html         # View/edit user profile
│   ├── admin_login.html     # Admin login
│   ├── admin.html           # Admin dashboard with charts
│   ├── admin_slots.html     # Add/delete parking slots
│   ├── admin_users.html     # View all users
│   └── admin_records.html   # Entry/exit logs
└── static/
    ├── css/style.css        # Full stylesheet (glassmorphism + gradients)
    └── js/main.js           # UI animations + auto-dismiss alerts
```

---

## ⚙️ Setup & Run

### Step 1 — Install Flask
```bash
pip install flask
```

### Step 2 — Run the App
```bash
python app.py
```

### Step 3 — Open in Browser
```
http://127.0.0.1:5000
```

---

## 🔑 Login Credentials

| Role  | Username/Email | Password   |
|-------|----------------|------------|
| Admin | admin          | admin123   |
| User  | Register via `/register` |   |

---

## 🗄️ Database Tables

| Table             | Purpose                            |
|-------------------|------------------------------------|
| `users`           | Registered user accounts           |
| `parking_slots`   | All parking slot definitions       |
| `bookings`        | Slot reservations made by users    |
| `parking_records` | Entry/exit timestamps & duration   |

---

## 🧩 Features

### User Module
- Register with name, email, phone, vehicle number
- Login / logout with Flask sessions
- Update profile details

### Parking Visualization
- Grid layout (like movie seat booking)
- Green = Available | Yellow = Booked | Red = Occupied
- Click a slot → modal popup → Book button

### Booking Module
- Book available slot (with optional entry time)
- Cancel active booking
- View all bookings (active / completed / cancelled)

### Entry/Exit Management
- Check-in → marks slot as **Occupied**
- Check-out → frees slot, calculates duration in minutes

### Admin Panel (Login: admin / admin123)
- Dashboard with stats + Chart.js charts
- Add / delete parking slots
- View all registered users
- View full entry/exit log

---

## 🎨 UI Highlights
- Blue-purple gradient dark theme
- Glassmorphism cards
- FontAwesome icons
- Chart.js doughnut & bar charts
- Smooth animations on card load
- Auto-dismissing flash messages
