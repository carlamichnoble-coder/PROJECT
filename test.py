import sys
import sqlite3
import bisect
import heapq
from datetime import datetime, date
from contextlib import contextmanager

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QMessageBox, QFrame, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

# ─────────────────────────── DATABASE CONFIG ──────────────────────────────────
DB_PATH = "clinic_db.sqlite"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn, conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ─────────────────────────── DATA STRUCTURES & ALGORITHMS ─────────────────────

class ClinicEngine:
    """
    High-performance logic layer using Advanced Data Structures.
    """
    def __init__(self):
        # HashMap {id: data} for O(1) Patient Retrieval
        self.patient_cache = {}
        # HashMap {doc_id: [(start, end)]} for O(log n) Conflict Detection (Interval Tree logic)
        self.doctor_intervals = {}
        # Min-Heap for O(log n) Dashboard Sorting
        self.priority_queue = []

    def sync_cache(self):
        """Sync SQL data into optimized memory structures."""
        with db() as (conn, c):
            # 1. Fill Patient HashMap
            c.execute("SELECT * FROM patients")
            self.patient_cache = {row['id']: dict(row) for row in rows} if (rows := c.fetchall()) else {}

            # 2. Fill Doctor Intervals (Sorted Lists for Binary Search)
            c.execute("SELECT doctor_id, start_time, end_time FROM schedule_slots WHERE is_available = 0")
            self.doctor_intervals = {}
            for row in c.fetchall():
                d_id = row['doctor_id']
                if d_id not in self.doctor_intervals:
                    self.doctor_intervals[d_id] = []
                # Use bisect to keep intervals sorted during insertion: O(n log n) total sync
                bisect.insort(self.doctor_intervals[d_id], (row['start_time'], row['end_time']))

            # 3. Fill Dashboard Heap
            c.execute("""
                SELECT s.start_time, p.full_name 
                FROM appointments a 
                JOIN patients p ON a.patient_id = p.id 
                JOIN schedule_slots s ON a.slot_id = s.id 
                WHERE a.status = 'pending'
            """)
            self.priority_queue = [(row['start_time'], row['full_name']) for row in c.fetchall()]
            heapq.heapify(self.priority_queue)

    def check_conflict(self, doc_id, start_iso, end_iso):
        """O(log n) Conflict Detection using Binary Search."""
        intervals = self.doctor_intervals.get(doc_id, [])
        new_interval = (start_iso, end_iso)
        
        idx = bisect.bisect_left(intervals, new_interval)
        
        # Check overlap with previous
        if idx > 0 and start_iso < intervals[idx-1][1]:
            return True
        # Check overlap with next
        if idx < len(intervals) and end_iso > intervals[idx][0]:
            return True
        return False

# Global Engine Instance
Engine = ClinicEngine()

# ─────────────────────────── UI COMPONENTS ───────────────────────────────────

STYLE = """
QMainWindow { background-color: #0f172a; }
QWidget { color: #f8fafc; font-family: 'Segoe UI'; }
QFrame#card { background-color: #1e293b; border-radius: 10px; border: 1px solid #334155; }
QPushButton { background-color: #38bdf8; color: #0f172a; font-weight: bold; border-radius: 6px; padding: 8px; }
QPushButton:hover { background-color: #7dd3fc; }
QLineEdit, QDateEdit, QComboBox { background-color: #0f172a; border: 1px solid #334155; padding: 5px; border-radius: 4px; }
QTableWidget { background-color: #1e293b; gridline-color: #334155; border: none; }
QHeaderView::section { background-color: #0f172a; color: #94a3b8; padding: 5px; font-weight: bold; }
"""

class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setFixedSize(400, 300)
        layout = QVBoxLayout(self)
        
        card = QFrame(); card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        
        title = QLabel("🏥 ClinicSys Login")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.u = QLineEdit(); self.u.setPlaceholderText("Username")
        self.p = QLineEdit(); self.p.setPlaceholderText("Password"); self.p.setEchoMode(QLineEdit.EchoMode.Password)
        
        btn = QPushButton("Login")
        btn.clicked.connect(self.handle_login)
        
        for w in [title, self.u, self.p, btn]: card_layout.addWidget(w)
        layout.addWidget(card)

    def handle_login(self):
        # Simplified for demo
        with db() as (conn, c):
            c.execute("SELECT id, role, username FROM users WHERE username=? AND password=?", (self.u.text(), self.p.text()))
            user = c.fetchone()
            if user:
                Engine.sync_cache()
                self.on_success(user['id'], user['username'], user['role'])
            else:
                QMessageBox.warning(self, "Error", "Invalid Credentials")

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        header = QLabel("Upcoming Appointments (Priority Queue Sorted)"); header.setStyleSheet("font-size: 18px; color: #38bdf8;")
        layout.addWidget(header)
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Time", "Patient Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self):
        Engine.sync_cache()
        # Peek at heap without destroying it or use sorted(heap) for display
        sorted_list = sorted(Engine.priority_queue)
        self.table.setRowCount(len(sorted_list))
        for i, (time, name) in enumerate(sorted_list):
            self.table.setItem(i, 0, QTableWidgetItem(time))
            self.table.setItem(i, 1, QTableWidgetItem(name))

class MainWindow(QMainWindow):
    def __init__(self, uid, uname, role):
        super().__init__()
        self.setWindowTitle(f"Clinic Management System - {uname} ({role})")
        self.resize(900, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # Sidebar
        sidebar = QFrame(); sidebar.setFixedWidth(200); sidebar.setObjectName("card")
        side_lay = QVBoxLayout(sidebar)
        
        dash_btn = QPushButton("📊 Dashboard")
        dash_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        book_btn = QPushButton("📅 Book Appointment")
        book_btn.clicked.connect(self.open_booking)
        
        side_lay.addWidget(dash_btn)
        side_lay.addWidget(book_btn)
        side_lay.addStretch()
        
        # Stack
        self.stack = QStackedWidget()
        self.dash_page = Dashboard()
        self.stack.addWidget(self.dash_page)
        
        layout.addWidget(sidebar)
        layout.addWidget(self.stack)

    def open_booking(self):
        dlg = BookingDialog(self)
        if dlg.exec():
            self.dash_page.refresh()

class BookingDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Algorithm-Validated Booking")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.doc_selector = QComboBox()
        with db() as (conn, c):
            c.execute("SELECT id, full_name FROM doctors")
            for d in c.fetchall(): self.doc_selector.addItem(d['full_name'], d['id'])
            
        self.pat_selector = QComboBox()
        # Using HashMap Cache for O(1) patient listing
        for p_id, p_data in Engine.patient_cache.items():
            self.pat_selector.addItem(p_data['full_name'], p_id)
            
        self.start_dt = QLineEdit("2025-06-01 10:00:00") # ISO format for simple logic
        self.end_dt = QLineEdit("2025-06-01 10:30:00")
        
        form.addRow("Doctor:", self.doc_selector)
        form.addRow("Patient:", self.pat_selector)
        form.addRow("Start (ISO):", self.start_dt)
        form.addRow("End (ISO):", self.end_dt)
        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.validate_and_save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def validate_and_save(self):
        d_id = self.doc_selector.currentData()
        start = self.start_dt.text()
        end = self.end_dt.text()
        
        # ALGORITHM: O(log n) Interval Conflict Check
        if Engine.check_conflict(d_id, start, end):
            QMessageBox.critical(self, "Conflict Detected", "This doctor is already busy during this interval!")
            return

        # No conflict -> Save to DB
        try:
            with db() as (conn, c):
                # 1. Create slot
                c.execute("INSERT INTO schedule_slots (doctor_id, start_time, end_time, is_available) VALUES (?,?,?,0)", 
                          (d_id, start, end))
                slot_id = c.lastrowid
                # 2. Create appointment
                c.execute("INSERT INTO appointments (patient_id, doctor_id, slot_id, status) VALUES (?,?,?, 'pending')",
                          (self.pat_selector.currentData(), d_id, slot_id))
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

# ─────────────────────────── MAIN ───────────────────────────────────────────

def init_db():
    """Ensure minimal tables exist for the demo."""
    with db() as (conn, c):
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS doctors (id INTEGER PRIMARY KEY, full_name TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY, full_name TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS schedule_slots (id INTEGER PRIMARY KEY, doctor_id INTEGER, start_time TEXT, end_time TEXT, is_available INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS appointments (id INTEGER PRIMARY KEY, patient_id INTEGER, doctor_id INTEGER, slot_id INTEGER, status TEXT)")
        
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin')")
            c.execute("INSERT INTO doctors VALUES (1, 'Dr. Smith')")
            c.execute("INSERT INTO patients VALUES (1, 'John Doe')")

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    
    main_win = None
    def launch_main(uid, uname, role):
        global main_win
        login_win.close()
        main_win = MainWindow(uid, uname, role)
        main_win.show()

    login_win = LoginWindow(launch_main)
    login_win.show()
    sys.exit(app.exec())