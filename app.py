"""
Smart Parking System - Main Application
Flask-based web application for managing parking slots, bookings, and users.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps

# ─────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'smart_parking_secret_2024'  # Secret key for session management

# Database file path
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# Hardcoded admin credentials (simple approach for university project)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'


# ─────────────────────────────────────────────
# Database Helper Functions
# ─────────────────────────────────────────────

def get_db():
    """Create and return a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn


def init_db():
    """Initialize the database with tables and sample data."""
    conn = get_db()
    cursor = conn.cursor()

    # ── Create Users Table ──────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT NOT NULL,
            vehicle_number TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Create Parking Slots Table ──────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number TEXT UNIQUE NOT NULL,
            slot_type TEXT DEFAULT 'regular',   -- regular, premium, handicapped
            status TEXT DEFAULT 'available',     -- available, booked, occupied
            floor TEXT DEFAULT 'G',              -- G, 1, 2
            section TEXT DEFAULT 'A'             -- A, B, C
        )
    ''')

    # ── Create Bookings Table ───────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expected_entry TEXT,
            status TEXT DEFAULT 'active',        -- active, cancelled, completed
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (slot_id) REFERENCES parking_slots(id)
        )
    ''')

    # ── Create Parking Records Table (Entry/Exit Logs) ──────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            booking_id INTEGER,
            entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_time TIMESTAMP,
            duration_minutes INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (slot_id) REFERENCES parking_slots(id)
        )
    ''')

    # ── Insert Sample Parking Slots if not already present ─────────────
    cursor.execute("SELECT COUNT(*) FROM parking_slots")
    if cursor.fetchone()[0] == 0:
        # Generate 30 slots across 2 floors and 3 sections
        slots = []
        floor_sections = [
            ('G', 'A'), ('G', 'B'), ('G', 'C'),
            ('1', 'A'), ('1', 'B'), ('1', 'C'),
        ]
        slot_count = 1
        for floor, section in floor_sections:
            for i in range(1, 6):  # 5 slots per section
                slot_number = f"{floor}{section}{i:02d}"
                slot_type = 'premium' if section == 'A' and i <= 2 else ('handicapped' if i == 5 and floor == 'G' else 'regular')
                slots.append((slot_number, slot_type, 'available', floor, section))
                slot_count += 1

        cursor.executemany(
            "INSERT INTO parking_slots (slot_number, slot_type, status, floor, section) VALUES (?, ?, ?, ?, ?)",
            slots
        )

    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully!")


# ─────────────────────────────────────────────
# Decorators / Guards
# ─────────────────────────────────────────────

def login_required(f):
    """Decorator: Redirect to login if user is not logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator: Redirect if not logged in as admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────
# Public Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Home / Landing page."""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        vehicle_number = request.form.get('vehicle_number', '').strip().upper()

        # Basic validation
        if not all([name, email, password, phone, vehicle_number]):
            flash('All fields are required!', 'danger')
            return render_template('register.html')

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password, phone, vehicle_number) VALUES (?, ?, ?, ?, ?)",
                (name, email, password, phone, vehicle_number)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered. Please use a different email.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()
        conn.close()

        if user:
            session.clear()
            # Store user info in session
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash(f'Welcome back, {user["name"]}! 🚗', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User Logout — clears session."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


# ─────────────────────────────────────────────
# User Routes (Protected)
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing stats and active bookings."""
    conn = get_db()

    # Fetch overall parking stats
    total_slots = conn.execute("SELECT COUNT(*) FROM parking_slots").fetchone()[0]
    available_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE status='available'").fetchone()[0]
    occupied_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE status='occupied'").fetchone()[0]
    booked_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE status='booked'").fetchone()[0]

    # Fetch user's active bookings
    active_bookings = conn.execute('''
        SELECT b.*, ps.slot_number, ps.floor, ps.section, ps.slot_type, ps.status as slot_status
        FROM bookings b
        JOIN parking_slots ps ON b.slot_id = ps.id
        WHERE b.user_id = ? AND b.status = 'active'
        ORDER BY b.booking_time DESC
    ''', (session['user_id'],)).fetchall()

    # Fetch user's parking records (history)
    recent_records = conn.execute('''
        SELECT pr.*, COALESCE(ps.slot_number, 'Deleted Slot') as slot_number
        FROM parking_records pr
        LEFT JOIN parking_slots ps ON pr.slot_id = ps.id
        WHERE pr.user_id = ?
        ORDER BY pr.entry_time DESC
        LIMIT 5
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return render_template('dashboard.html',
                           total_slots=total_slots,
                           available_slots=available_slots,
                           occupied_slots=occupied_slots,
                           booked_slots=booked_slots,
                           active_bookings=active_bookings,
                           recent_records=recent_records)


@app.route('/parking')
@login_required
def parking():
    """Visual parking slot grid view."""
    conn = get_db()

    # Get all slots grouped by floor
    slots = conn.execute(
        "SELECT * FROM parking_slots ORDER BY floor, section, slot_number"
    ).fetchall()

    # Group slots by floor
    floors = {}
    for slot in slots:
        floor = slot['floor']
        if floor not in floors:
            floors[floor] = []
        floors[floor].append(dict(slot))

    conn.close()
    return render_template('parking.html', floors=floors)


@app.route('/book/<int:slot_id>', methods=['GET', 'POST'])
@login_required
def book_slot(slot_id):
    """Book a specific parking slot."""
    conn = get_db()
    slot = conn.execute("SELECT * FROM parking_slots WHERE id = ?", (slot_id,)).fetchone()

    if not slot:
        flash('Slot not found!', 'danger')
        conn.close()
        return redirect(url_for('parking'))

    if slot['status'] != 'available':
        flash('Sorry, this slot is no longer available.', 'warning')
        conn.close()
        return redirect(url_for('parking'))

    if request.method == 'POST':
        expected_entry = request.form.get('expected_entry', '')

        # Create booking record
        booking_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "INSERT INTO bookings (user_id, slot_id, expected_entry, booking_time) VALUES (?, ?, ?, ?)",
            (session['user_id'], slot_id, expected_entry, booking_time)
        )

        # Update slot status to 'booked'
        conn.execute("UPDATE parking_slots SET status = 'booked' WHERE id = ?", (slot_id,))
        conn.commit()
        conn.close()

        flash(f'Slot {slot["slot_number"]} booked successfully!', 'success')
        return redirect(url_for('my_bookings'))

    conn.close()
    return render_template('book_slot.html', slot=slot)


@app.route('/my-bookings')
@login_required
def my_bookings():
    """View all bookings for the logged-in user."""
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, ps.slot_number, ps.floor, ps.section, ps.slot_type, ps.status as slot_status
        FROM bookings b
        JOIN parking_slots ps ON b.slot_id = ps.id
        WHERE b.user_id = ?
        ORDER BY b.booking_time DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/cancel-booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel an active booking (accepts both GET link and POST form)."""
    conn = get_db()

    # Fetch the booking and verify ownership
    booking = conn.execute(
        "SELECT * FROM bookings WHERE id = ? AND user_id = ?",
        (booking_id, session['user_id'])
    ).fetchone()

    if not booking or booking['status'] != 'active':
        flash('Booking not found or already cancelled.', 'danger')
        conn.close()
        return redirect(url_for('my_bookings'))

    # If user checked in but is cancelling instead of checking out,
    # close the open parking record so it doesn't show as "Ongoing".
    conn.execute(
        """UPDATE parking_records
           SET exit_time = ?, duration_minutes = 0
           WHERE booking_id = ? AND exit_time IS NULL""",
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), booking_id)
    )

    # Cancel booking and free the slot
    conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    conn.execute("UPDATE parking_slots SET status = 'available' WHERE id = ?", (booking['slot_id'],))
    conn.commit()
    conn.close()

    flash('Booking cancelled successfully. Slot is now available.', 'success')
    return redirect(url_for('my_bookings'))


@app.route('/checkin/<int:booking_id>')
@login_required
def check_in(booking_id):
    """Check in to a booked slot (marks slot as occupied)."""
    conn = get_db()

    booking = conn.execute(
        "SELECT * FROM bookings WHERE id = ? AND user_id = ?",
        (booking_id, session['user_id'])
    ).fetchone()

    if not booking or booking['status'] != 'active':
        flash('Invalid booking for check-in.', 'danger')
        conn.close()
        return redirect(url_for('my_bookings'))

    slot = conn.execute("SELECT status FROM parking_slots WHERE id = ?", (booking['slot_id'],)).fetchone()
    if slot and slot['status'] == 'occupied':
        flash('You have already checked in.', 'info')
        conn.close()
        return redirect(url_for('my_bookings'))

    # Create parking record (entry log)
    conn.execute(
        "INSERT INTO parking_records (user_id, slot_id, booking_id, entry_time) VALUES (?, ?, ?, ?)",
        (session['user_id'], booking['slot_id'], booking_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )

    # Mark slot as occupied
    conn.execute("UPDATE parking_slots SET status = 'occupied' WHERE id = ?", (booking['slot_id'],))
    conn.commit()
    conn.close()

    flash('✅ Check-in successful! Your slot is now occupied.', 'success')
    return redirect(url_for('my_bookings'))


@app.route('/checkout/<int:booking_id>')
@login_required
def check_out(booking_id):
    """Check out from a slot (frees the slot and calculates duration)."""
    conn = get_db()

    booking = conn.execute(
        "SELECT * FROM bookings WHERE id = ? AND user_id = ?",
        (booking_id, session['user_id'])
    ).fetchone()

    if not booking:
        flash('Booking not found.', 'danger')
        conn.close()
        return redirect(url_for('my_bookings'))

    slot = conn.execute("SELECT status FROM parking_slots WHERE id = ?", (booking['slot_id'],)).fetchone()
    if slot and slot['status'] != 'occupied':
        flash('You are not checked in yet.', 'info')
        conn.close()
        return redirect(url_for('my_bookings'))

    # Find all open parking records for this booking (in case of double check-in clicks)
    records = conn.execute(
        "SELECT * FROM parking_records WHERE booking_id = ? AND exit_time IS NULL",
        (booking_id,)
    ).fetchall()

    if records:
        exit_time_dt = datetime.now()
        exit_time_str = exit_time_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        for record in records:
            entry_time = datetime.strptime(record['entry_time'], '%Y-%m-%d %H:%M:%S')
            duration = int((exit_time_dt - entry_time).total_seconds() / 60)  # Duration in minutes
            
            conn.execute(
                "UPDATE parking_records SET exit_time = ?, duration_minutes = ? WHERE id = ?",
                (exit_time_str, duration, record['id'])
            )

    # Mark booking as completed and slot as available
    conn.execute("UPDATE bookings SET status = 'completed' WHERE id = ?", (booking_id,))
    conn.execute("UPDATE parking_slots SET status = 'available' WHERE id = ?", (booking['slot_id'],))
    conn.commit()
    conn.close()

    flash('🏁 Check-out successful! Slot is now free.', 'success')
    return redirect(url_for('my_bookings'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update user profile."""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        vehicle_number = request.form.get('vehicle_number', '').strip().upper()

        conn.execute(
            "UPDATE users SET name=?, phone=?, vehicle_number=? WHERE id=?",
            (name, phone, vehicle_number, session['user_id'])
        )
        conn.commit()
        session['user_name'] = name  # Update name in session
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    conn.close()
    return render_template('profile.html', user=user)


# ─────────────────────────────────────────────
# API Route (for AJAX calls from JS)
# ─────────────────────────────────────────────

@app.route('/api/slot/<int:slot_id>')
def get_slot_info(slot_id):
    """Return slot info as JSON for modal popup."""
    if 'user_id' not in session and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    slot = conn.execute("SELECT * FROM parking_slots WHERE id = ?", (slot_id,)).fetchone()
    conn.close()

    if slot:
        return jsonify({
            'id': slot['id'],
            'slot_number': slot['slot_number'],
            'slot_type': slot['slot_type'],
            'status': slot['status'],
            'floor': slot['floor'],
            'section': slot['section']
        })
    return jsonify({'error': 'Slot not found'}), 404


# ─────────────────────────────────────────────
# Admin Routes
# ─────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session['is_admin'] = True
            session['admin_name'] = 'Administrator'
            flash('Welcome, Admin! 👨‍💼', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('is_admin', None)
    session.pop('admin_name', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics."""
    conn = get_db()

    # Slot statistics
    total_slots = conn.execute("SELECT COUNT(*) FROM parking_slots").fetchone()[0]
    available_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE status='available'").fetchone()[0]
    occupied_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE status='occupied'").fetchone()[0]
    booked_slots = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE status='booked'").fetchone()[0]

    # User stats
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    active_bookings = conn.execute("SELECT COUNT(*) FROM bookings WHERE status='active'").fetchone()[0]

    # Recent bookings
    recent_bookings = conn.execute('''
        SELECT b.*, u.name as user_name, u.vehicle_number, COALESCE(ps.slot_number, 'Deleted Slot') as slot_number
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        LEFT JOIN parking_slots ps ON b.slot_id = ps.id
        ORDER BY b.booking_time DESC
        LIMIT 10
    ''').fetchall()

    # Slot type breakdown
    slot_types = conn.execute('''
        SELECT slot_type, COUNT(*) as count
        FROM parking_slots GROUP BY slot_type
    ''').fetchall()

    # Get all slots grouped by floor for the layout
    slots = conn.execute(
        "SELECT * FROM parking_slots ORDER BY floor, section, slot_number"
    ).fetchall()

    floors = {}
    for slot in slots:
        floor = slot['floor']
        if floor not in floors:
            floors[floor] = []
        floors[floor].append(dict(slot))

    conn.close()

    return render_template('admin.html',
                           total_slots=total_slots,
                           available_slots=available_slots,
                           occupied_slots=occupied_slots,
                           booked_slots=booked_slots,
                           total_users=total_users,
                           total_bookings=total_bookings,
                           active_bookings=active_bookings,
                           recent_bookings=recent_bookings,
                           slot_types=slot_types,
                           floors=floors)


@app.route('/admin/force-checkout/<int:slot_id>', methods=['POST'])
@admin_required
def admin_force_checkout(slot_id):
    """Admin: Manually checkout an occupied or booked slot."""
    conn = get_db()
    slot = conn.execute("SELECT * FROM parking_slots WHERE id = ?", (slot_id,)).fetchone()
    
    if not slot or slot['status'] == 'available':
        flash('Slot is already available or not found.', 'info')
        conn.close()
        return redirect(url_for('admin_dashboard'))

    # Find the active booking for this slot
    booking = conn.execute(
        "SELECT * FROM bookings WHERE slot_id = ? AND status = 'active' ORDER BY booking_time DESC LIMIT 1",
        (slot_id,)
    ).fetchone()

    if booking:
        booking_id = booking['id']
        
        # Close any open parking records (in case of double check-ins)
        records = conn.execute(
            "SELECT * FROM parking_records WHERE booking_id = ? AND exit_time IS NULL",
            (booking_id,)
        ).fetchall()

        if records:
            exit_time_dt = datetime.now()
            exit_time_str = exit_time_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            for record in records:
                entry_time = datetime.strptime(record['entry_time'], '%Y-%m-%d %H:%M:%S')
                duration = int((exit_time_dt - entry_time).total_seconds() / 60)

                conn.execute(
                    "UPDATE parking_records SET exit_time = ?, duration_minutes = ? WHERE id = ?",
                    (exit_time_str, duration, record['id'])
                )

        # Mark booking as completed
        conn.execute("UPDATE bookings SET status = 'completed' WHERE id = ?", (booking_id,))

    # Update slot status
    conn.execute("UPDATE parking_slots SET status = 'available' WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()

    flash(f'Slot {slot["slot_number"]} checked out manually.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/slots')
@admin_required
def admin_slots():
    """Admin: manage parking slots."""
    conn = get_db()
    slots = conn.execute("SELECT * FROM parking_slots ORDER BY floor, section, slot_number").fetchall()
    conn.close()
    return render_template('admin_slots.html', slots=slots)


@app.route('/admin/add-slot', methods=['POST'])
@admin_required
def add_slot():
    """Admin: add a new parking slot."""
    slot_number = request.form.get('slot_number', '').strip().upper()
    slot_type = request.form.get('slot_type', 'regular')
    floor = request.form.get('floor', 'G')
    section = request.form.get('section', 'A')

    if not slot_number:
        flash('Slot number is required!', 'danger')
        return redirect(url_for('admin_slots'))

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO parking_slots (slot_number, slot_type, status, floor, section) VALUES (?, ?, 'available', ?, ?)",
            (slot_number, slot_type, floor, section)
        )
        conn.commit()
        flash(f'Slot {slot_number} added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Slot number {slot_number} already exists!', 'danger')
    finally:
        conn.close()

    return redirect(url_for('admin_slots'))


@app.route('/admin/delete-slot/<int:slot_id>')
@admin_required
def delete_slot(slot_id):
    """Admin: delete a parking slot."""
    conn = get_db()
    slot = conn.execute("SELECT * FROM parking_slots WHERE id = ?", (slot_id,)).fetchone()

    if slot and slot['status'] == 'available':
        conn.execute("DELETE FROM parking_slots WHERE id = ?", (slot_id,))
        conn.commit()
        flash(f'Slot {slot["slot_number"]} deleted.', 'success')
    else:
        flash('Cannot delete an occupied or booked slot.', 'danger')

    conn.close()
    return redirect(url_for('admin_slots'))


@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin: view all users."""
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)


@app.route('/admin/records')
@admin_required
def admin_records():
    """Admin: view entry/exit logs."""
    conn = get_db()
    records = conn.execute('''
        SELECT pr.*, u.name as user_name, u.vehicle_number, COALESCE(ps.slot_number, 'Deleted Slot') as slot_number
        FROM parking_records pr
        JOIN users u ON pr.user_id = u.id
        LEFT JOIN parking_slots ps ON pr.slot_id = ps.id
        ORDER BY pr.entry_time DESC
    ''').fetchall()
    conn.close()
    return render_template('admin_records.html', records=records)


# ─────────────────────────────────────────────
# Run Application
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()          # Initialize DB on first run
    print("[*] Smart Parking System starting...")
    print("[*] Open http://127.0.0.1:5000 in your browser")
    print("[*] Admin: username=admin, password=admin123")
    app.run(debug=True, port=5000)
