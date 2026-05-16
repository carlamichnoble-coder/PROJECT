import heapq
import json
import os
import sys
from datetime import date, datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QMessageBox, QComboBox, QDateEdit,
    QTimeEdit, QTabWidget, QFrame, QHeaderView, QScrollArea,
    QGridLayout, QTextEdit, QButtonGroup, QRadioButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# ─────────────────────────────────────────────
#  FILE PERSISTENCE  (JSON-based storage) ADDED
# ─────────────────────────────────────────────
DATA_FILE = "clinic_data.json"

def save_data():
    """Serialize all in-memory data to JSON and write to disk."""
    serializable_appts = {}
    for date_str, heap in appointments_by_date.items():
        serializable_appts[date_str] = [(rank, time_val, appt) for rank, time_val, appt in heap]

    payload = {
        "doctors": doctors_map,
        "patients": patients_map,
        "appointments": serializable_appts,
        "occupied_slots": list(occupied_slots)
    }
    with open(DATA_FILE, "w") as f:
        json.dump(payload, f, indent=2)


def load_data():
    """Load persisted data from JSON into in-memory structures."""
    global doctors_map, patients_map, appointments_by_date, occupied_slots
    if not os.path.exists(DATA_FILE):
        return False
    try:
        with open(DATA_FILE, "r") as f:
            payload = json.load(f)
        doctors_map.update(payload.get("doctors", {}))
        patients_map.update(payload.get("patients", {}))
        for date_str, entries in payload.get("appointments", {}).items():
            heap = [(rank, time_val, appt) for rank, time_val, appt in entries]
            heapq.heapify(heap)
            appointments_by_date[date_str] = heap
        occupied_slots.update(tuple(s) for s in payload.get("occupied_slots", []))
        return True
    except Exception as e:
        print(f"[WARN] Could not load data: {e}")
        return False

def reset_system_data():
    """Clears all in-memory data and deletes the saved file."""
    global doctors_map, patients_map, appointments_by_date, occupied_slots
    doctors_map.clear()
    patients_map.clear()
    appointments_by_date.clear()
    occupied_slots.clear()
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

# ─────────────────────────────────────────────
#  DATA STORE  - CHANGED
# ─────────────────────────────────────────────
doctors_map = {}          # Key: username → doctor dict
patients_map = {}         # Key: username → patient dict
appointments_by_date = {} # Key: "YYYY-MM-DD" → Min-Heap list
occupied_slots = set()    # {(doctor_username, date_str, time_str)} for conflict detection

# ─────────────────────────────────────────────
#  BUILT-IN ADMIN ACCOUNT
# ─────────────────────────────────────────────
admin_user = {"username": "admin", "password": "admin123", "role": "admin"}

# ══════════════════════════════════════════════
#  STYLE CONSTANTS
# ══════════════════════════════════════════════
PRIMARY   = "#1a6b5a"
SECONDARY = "#27ae8f"
ACCENT    = "#f0a500"
LIGHT_BG  = "#f4f9f7"
DARK_TEXT = "#1c2b27"
MUTED     = "#7fa99b"
DANGER    = "#c0392b"
SUCCESS   = "#27ae60"
WARNING   = "#e67e22"
CARD_BG   = "#ffffff"
BORDER    = "#d0e8e0"

BASE_STYLE = f"""
QMainWindow, QDialog {{
    background: {LIGHT_BG};
}}
QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    color: {DARK_TEXT};
}}
QLabel#heading {{
    font-size: 22px;
    font-weight: 700;
    color: {PRIMARY};
}}
QLabel#subheading {{
    font-size: 14px;
    color: {MUTED};
}}
QPushButton {{
    background: {PRIMARY};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {SECONDARY};
}}
QPushButton:pressed {{
    background: #145043;
}}
QPushButton#danger {{
    background: {DANGER};
}}
QPushButton#danger:hover {{
    background: #e74c3c;
}}
QPushButton#accent {{
    background: {ACCENT};
    color: {DARK_TEXT};
}}
QPushButton#accent:hover {{
    background: #e09400;
}}
QPushButton#outline {{
    background: transparent;
    color: {PRIMARY};
    border: 2px solid {PRIMARY};
}}
QPushButton#outline:hover {{
    background: {PRIMARY};
    color: white;
}}
QPushButton#success {{
    background: {SUCCESS};
    color: white;
}}
QPushButton#success:hover {{
    background: #219150;
}}
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QTextEdit {{
    background: white;
    border: 1.5px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    color: {DARK_TEXT};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus {{
    border-color: {SECONDARY};
}}
QTableWidget {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 6px;
}}
QTableWidget::item:selected {{
    background: #d4efe8;
    color: {DARK_TEXT};
}}
QHeaderView::section {{
    background: {PRIMARY};
    color: white;
    font-weight: 700;
    padding: 8px;
    border: none;
    font-size: 13px;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: white;
}}
QTabBar::tab {{
    background: {LIGHT_BG};
    color: {MUTED};
    padding: 10px 22px;
    border-radius: 6px 6px 0 0;
    font-weight: 600;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {PRIMARY};
    color: white;
}}
QFrame#card {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QRadioButton {{
    font-size: 13px;
    color: {DARK_TEXT};
    padding: 4px 8px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
}}
"""

# ══════════════════════════════════════════════
#  HELPERS & ALGORITHMS - ADDED & CHANGED
# ══════════════════════════════════════════════

# CHNAGED TO HASH
def find_user_hash(username, password):
    """Hash-based O(1) authentication."""
    if username == admin_user["username"] and password == admin_user["password"]:
        return admin_user
    if username in doctors_map and doctors_map[username]["password"] == password:
        return {"role": "doctor", "data": doctors_map[username]}
    if username in patients_map and patients_map[username]["password"] == password:
        return {"role": "patient", "data": patients_map[username]}
    return None

# AGE COMPUTING
def compute_age(birthdate_str: str) -> int:
    try:
        bd = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except Exception:
        return 0

# FOR ACCOUNT CREATION
def make_doctor_credentials(last_name: str):
    username = f"dr_{last_name.lower().replace(' ', '')}"
    return username, "doc123"


def make_patient_credentials(name: str):
    parts = name.strip().split()
    if len(parts) >= 2:
        username = f"{parts[0].lower()}.{parts[-1].lower()}"
    else:
        username = name.lower().replace(" ", "")
    return username, "1234"


# FOR CONFLICT CHECKING
def time_str_to_minutes(time_str: str) -> int:
    """Convert 'HH:MM' string to total minutes for arithmetic comparison."""
    try:
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    except Exception:
        return 0


def check_30min_conflict(doctor_username: str, date_str: str, new_time_str: str) -> bool:
    """
    IMPROVEMENT: 30-minute buffer conflict detection.
    Returns True if there is a conflict (another appointment within 30 minutes).
    Uses the occupied_slots set for O(1) per slot check.
    Checks ±30 minutes around the requested time.
    """
    new_mins = time_str_to_minutes(new_time_str)
    # Check every 30-minute slot within the ±30 min window
    for delta in range(-30, 31, 30):
        if delta == 0:
            continue
        check_mins = new_mins + delta
        if check_mins < 0:
            continue
        check_h = check_mins // 60
        check_m = check_mins % 60
        candidate = f"{check_h:02d}:{check_m:02d}"
        # We need to check all display formats stored in occupied_slots
        # occupied_slots stores (doc_username, date_str, time_str_display)
        # We'll search the heap for nearby times instead
    # Fall back to heap scan for the 30-min buffer check
    if date_str not in appointments_by_date:
        return False
    new_mins = time_str_to_minutes(new_time_str)
    for _, time_val, appt in appointments_by_date[date_str]:
        # Only check same doctor
        doc_label_prefix = ""
        if doctor_username in doctors_map:
            d = doctors_map[doctor_username]
            doc_label_prefix = f"Dr. {d['name']} — {d['specialization']}"
        if appt.get("doctor", "") != doc_label_prefix:
            continue
        existing_mins = time_str_to_minutes(time_val)
        if abs(new_mins - existing_mins) < 30:
            return True
    return False


# ══════════════════════════════════════════════
#  SHARED WIDGETS - ADDED
# ══════════════════════════════════════════════

def make_header(title: str, subtitle: str = "") -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 8)
    lbl = QLabel(title)
    lbl.setObjectName("heading")
    v.addWidget(lbl)
    if subtitle:
        sub = QLabel(subtitle)
        sub.setObjectName("subheading")
        v.addWidget(sub)
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {BORDER};")
    v.addWidget(line)
    return w


def styled_table(cols: list) -> QTableWidget:
    t = QTableWidget()
    t.setColumnCount(len(cols))
    t.setHorizontalHeaderLabels(cols)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.setStyleSheet(t.styleSheet() + "QTableWidget {alternate-background-color: #eaf5f0;}")
    return t

# FOR APPT FILTERS
def make_filter_bar(callback) -> tuple:
    """
    IMPROVEMENT: Status filter toggle bar.
    Returns (container_widget, get_filter_fn) where get_filter_fn() → selected status string.
    """
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    lbl = QLabel("Filter:")
    lbl.setStyleSheet(f"color:{MUTED};font-weight:600;font-size:13px;")
    layout.addWidget(lbl)

    group = QButtonGroup(container)
    options = [("All", "All"), ("Pending", "Pending"), ("Completed", "Completed"), ("Cancelled", "Cancelled")]
    radios = {}

    for text, val in options:
        rb = QRadioButton(text)
        rb.setStyleSheet(f"""
            QRadioButton {{
                border: 1.5px solid {BORDER};
                border-radius: 14px;
                padding: 4px 12px;
                background: white;
                font-size: 12px;
                font-weight: 600;
            }}
            QRadioButton::indicator {{ width: 0; height: 0; }}
            QRadioButton:checked {{
                background: {PRIMARY};
                color: white;
                border-color: {PRIMARY};
            }}
        """)
        if val == "All":
            rb.setChecked(True)
        group.addButton(rb)
        radios[val] = rb
        layout.addWidget(rb)
        rb.toggled.connect(callback)

    layout.addStretch()

    def get_filter():
        for val, rb in radios.items():
            if rb.isChecked():
                return val
        return "All"

    return container, get_filter


# ══════════════════════════════════════════════
#  DOCTOR DIALOGS - CHANGED
# ══════════════════════════════════════════════

class DoctorDialog(QDialog):
    def __init__(self, parent=None, doctor=None):
        super().__init__(parent)
        self.setWindowTitle("Add Doctor" if doctor is None else "Edit Doctor")
        self.setMinimumWidth(420)
        self.setStyleSheet(BASE_STYLE)
        self.doctor = doctor
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.addWidget(make_header("Doctor Information", "Fill in all required fields"))

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.spec_edit = QLineEdit()
        self.sched_combo = QComboBox()
        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday",
                "Monday-Friday","Monday-Saturday","Saturday-Sunday"]
        self.sched_combo.addItems(days)
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("hh:mm AP")
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("hh:mm AP")
        self.end_time.setTime(QTime(17, 0))

        form.addRow("Full Name *", self.name_edit)
        form.addRow("Specialization *", self.spec_edit)
        form.addRow("Schedule (Days) *", self.sched_combo)
        form.addRow("Start Time *", self.start_time)
        form.addRow("End Time *", self.end_time)
        layout.addLayout(form)

        if self.doctor:
            self.name_edit.setText(self.doctor.get("name", ""))
            self.spec_edit.setText(self.doctor.get("specialization", ""))
            idx = self.sched_combo.findText(self.doctor.get("schedule", ""))
            if idx >= 0:
                self.sched_combo.setCurrentIndex(idx)
            st = QTime.fromString(self.doctor.get("start_time", "08:00"), "HH:mm")
            et = QTime.fromString(self.doctor.get("end_time", "17:00"), "HH:mm")
            self.start_time.setTime(st)
            self.end_time.setTime(et)

        btn_row = QHBoxLayout()
        save = QPushButton("Save Doctor")
        save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("outline")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _save(self):
        name = self.name_edit.text().strip()
        spec = self.spec_edit.text().strip()
        if not name or not spec:
            QMessageBox.warning(self, "Validation", "Name and Specialization are required.")
            return
        st = self.start_time.time().toString("HH:mm")
        et = self.end_time.time().toString("HH:mm")

        # CHANGED TO DICTS IN STORING
        sched = self.sched_combo.currentText()

        if self.doctor is None:
            last = name.split()[-1]
            uname, pwd = make_doctor_credentials(last)
            new_doc = {
                "name": name,
                "specialization": spec,
                "schedule": sched,
                "start_time": st,
                "end_time": et,
                "username": uname,
                "password": pwd
            }
            doctors_map[uname] = new_doc
            save_data()
            QMessageBox.information(self, "Doctor Added",
                f"Doctor added!\n\nUsername: {uname}\nPassword: doc123")
        else:
            self.doctor.update({
                "name": name,
                "specialization": spec,
                "schedule": sched,
                "start_time": st,
                "end_time": et
            })
            save_data()
        self.accept()


# ══════════════════════════════════════════════
#  PATIENT DIALOGS - CHANGED
# ══════════════════════════════════════════════

class PatientDialog(QDialog):
    def __init__(self, parent=None, patient=None):
        super().__init__(parent)
        self.setWindowTitle("Add Patient" if patient is None else "Edit Patient")
        self.setMinimumWidth(440)
        self.setStyleSheet(BASE_STYLE)
        self.patient = patient
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.addWidget(make_header("Patient Information", "Fill in all required fields"))

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.bdate_edit = QDateEdit()
        self.bdate_edit.setDisplayFormat("yyyy-MM-dd")
        self.bdate_edit.setCalendarPopup(True)
        self.bdate_edit.setDate(QDate(2000, 1, 1))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other"])
        self.age_label = QLabel("—")
        self.age_label.setStyleSheet(f"color: {MUTED}; font-weight: 600;")
        self.email_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.address_edit.setFixedHeight(70)

        self.bdate_edit.dateChanged.connect(self._update_age)

        form.addRow("Full Name *", self.name_edit)
        form.addRow("Birthdate *", self.bdate_edit)
        form.addRow("Gender *", self.gender_combo)
        form.addRow("Age (auto)", self.age_label)
        form.addRow("Email *", self.email_edit)
        form.addRow("Address *", self.address_edit)
        layout.addLayout(form)

        if self.patient:
            self.name_edit.setText(self.patient.get("name", ""))
            bd = QDate.fromString(self.patient.get("birthdate", "2000-01-01"), "yyyy-MM-dd")
            self.bdate_edit.setDate(bd)
            idx = self.gender_combo.findText(self.patient.get("gender", "Male"))
            if idx >= 0:
                self.gender_combo.setCurrentIndex(idx)
            self.email_edit.setText(self.patient.get("email", ""))
            self.address_edit.setPlainText(self.patient.get("address", ""))

        self._update_age()

        btn_row = QHBoxLayout()
        save = QPushButton("Save Patient")
        save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("outline")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _update_age(self):
        bd = self.bdate_edit.date().toString("yyyy-MM-dd")
        age = compute_age(bd)
        self.age_label.setText(f"{age} years old")

    def _save(self):
        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        address = self.address_edit.toPlainText().strip()
        bd = self.bdate_edit.date().toString("yyyy-MM-dd")

        if not name or not email or not address:
            QMessageBox.warning(self, "Validation", "Name, Email and Address are required.")
            return

        age = compute_age(bd)

        # CHANGED TO DICT STORING
        if self.patient is None:
            uname, pwd = make_patient_credentials(name)
            new_p = {
                "name": name,
                "birthdate": bd,
                "gender": self.gender_combo.currentText(),
                "age": age,
                "email": email,
                "address": address,
                "username": uname,
                "password": pwd
            }
            patients_map[uname] = new_p
            save_data()
            QMessageBox.information(self, "Patient Added",
                f"Patient added!\n\nUsername: {uname}\nPassword: 1234")
        else:
            self.patient.update({
                "name": name,
                "birthdate": bd,
                "gender": self.gender_combo.currentText(),
                "age": age,
                "email": email,
                "address": address
            })
            save_data()
        self.accept()


# ══════════════════════════════════════════════
#  APPOINTMENT DIALOG
# ══════════════════════════════════════════════

class AppointmentDialog(QDialog):
    """
    IMPROVEMENT: Only doctors/admins can mark urgency.
    IMPROVEMENT: 30-minute spacing enforced on booking.
    """
    def __init__(self, parent=None, patient_data=None, role="patient"):
        super().__init__(parent)
        self.setWindowTitle("Book Appointment")
        self.setMinimumWidth(460)
        self.setStyleSheet(BASE_STYLE)
        self.patient_data = patient_data
        self.role = role  # "patient", "doctor", "admin"
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.addWidget(make_header("Book Appointment", "Schedule a consultation"))

        form = QFormLayout()
        form.setSpacing(10)

        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumDate(QDate.currentDate())

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setTime(QTime(9, 0))

        self.patient_combo = QComboBox()
        for p in patients_map.values():
            self.patient_combo.addItem(p["name"], p["username"])

        self.doctor_combo = QComboBox()
        for uname, d in doctors_map.items():
            self.doctor_combo.addItem(f"Dr. {d['name']} — {d['specialization']}", uname)

        # IMPROVEMENT: Urgency only for doctor/admin roles
        self.urgent_cb = QCheckBox("Mark as Urgent")
        if self.role == "patient":
            self.urgent_cb.setEnabled(False)
            self.urgent_cb.setToolTip("Only doctors or admins can mark appointments as urgent.")
            self.urgent_cb.setStyleSheet(f"color:{MUTED};")

        form.addRow("Date *", self.date_edit)
        form.addRow("Time *", self.time_edit)
        form.addRow("Patient *", self.patient_combo)
        form.addRow("Doctor *", self.doctor_combo)

        # SUBJECT TO CHANGE
        form.addRow("Priority", self.urgent_cb)
        layout.addLayout(form)

        # Time hint
        hint = QLabel("ℹ  Appointments must be at least 30 minutes apart.")
        hint.setStyleSheet(f"color:{MUTED};font-size:11px;")
        layout.addWidget(hint)

        # If patient user, lock patient field to their own record
        if self.patient_data:
            idx = self.patient_combo.findData(self.patient_data["username"])
            if idx >= 0:
                self.patient_combo.setCurrentIndex(idx)
            self.patient_combo.setEnabled(False)

        if not patients_map:
            QMessageBox.warning(self, "No Patients", "No patients registered yet.")
        if not doctors_map:
            QMessageBox.warning(self, "No Doctors", "No doctors registered yet.")

        btn_row = QHBoxLayout()
        book = QPushButton("Book Appointment")
        book.clicked.connect(self._book)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("outline")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        btn_row.addWidget(book)
        layout.addLayout(btn_row)

    def _book(self):
        # CHANGED FOR CONFLICT SCHEDULING
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        time_str = self.time_edit.time().toString("hh:mm AP")
        time_val = self.time_edit.time().toString("HH:mm")
        date_obj = self.date_edit.date()
        time_obj = self.time_edit.time()

        doc_username = self.doctor_combo.currentData()
        doc = doctors_map.get(doc_username)

        if not doc:
            QMessageBox.critical(self, "Error", "Invalid Doctor selection.")
            return

        # --- Day-of-week validation ---
        day_of_week = date_obj.toPyDate().strftime("%A")
        sched = doc["schedule"]
        day_map = {
            "Monday-Friday": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
            "Monday-Saturday": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
            "Saturday-Sunday": ["Saturday","Sunday"],
            "Monday-Sunday": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        }
        if sched in day_map:
            if day_of_week not in day_map[sched]:
                QMessageBox.warning(self, "Invalid Date",
                    f"Dr. {doc['name']} does not work on {day_of_week}s.\nSchedule: {sched}")
                return
        elif sched != day_of_week:
            QMessageBox.warning(self, "Invalid Date",
                f"Dr. {doc['name']} only works on {sched}.")
            return

        # --- Operating hours validation ---
        start_time = QTime.fromString(doc["start_time"], "HH:mm")
        end_time = QTime.fromString(doc["end_time"], "HH:mm")
        if time_obj < start_time or time_obj > end_time:
            QMessageBox.warning(self, "Invalid Time",
                f"Outside office hours ({doc['start_time']} – {doc['end_time']}).")
            return

        # --- Exact slot conflict detection O(1) ---
        conflict_key = (doc_username, date_str, time_str)
        if conflict_key in occupied_slots:
            QMessageBox.critical(self, "Conflict", "This doctor is already booked at this exact time!")
            return

        # IMPROVEMENT: 30-minute buffer conflict detection
        if check_30min_conflict(doc_username, date_str, time_val):
            QMessageBox.warning(self, "Scheduling Conflict",
                "Appointments must be at least 30 minutes apart.\n"
                "Please choose a different time slot.")
            return

        is_urgent = self.urgent_cb.isChecked() and self.role in ("doctor", "admin")
        priority_rank = 0 if is_urgent else 1

        # Determine patient name
        pat_username = self.patient_combo.currentData()
        pat = patients_map.get(pat_username)
        patient_name = pat["name"] if pat else "Unknown"

        appt_data = {
            "time_val": time_val,
            "time_disp": time_str,
            "patient": patient_name,
            "patient_username": pat_username,
            "doctor": self.doctor_combo.currentText(),
            "doctor_username": doc_username,
            "status": "Pending",
            "priority": "Urgent" if is_urgent else "Normal",
            "date": date_str,
        }

        if date_str not in appointments_by_date:
            appointments_by_date[date_str] = []

        heapq.heappush(appointments_by_date[date_str], (priority_rank, time_val, appt_data))
        occupied_slots.add(conflict_key)
        save_data()

        QMessageBox.information(self, "Success",
            f"Appointment booked!\nDate: {date_str}  |  Time: {time_str}\n"
            f"Priority: {'🚨 Urgent' if is_urgent else 'Normal'}")
        self.accept()


# ══════════════════════════════════════════════
#  APPOINTMENT EDIT DIALOG (Doctor/Admin only)
# ══════════════════════════════════════════════

class AppointmentEditDialog(QDialog):
    # CHANGED
    """
    IMPROVEMENT: Only doctors/admins can edit appointments and set urgency/status.
    """
    def __init__(self, parent, appt: dict, role: str):
        super().__init__(parent)
        self.setWindowTitle("Edit Appointment")
        self.setMinimumWidth(400)
        self.setStyleSheet(BASE_STYLE)
        self.appt = appt
        self.role = role
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.addWidget(make_header("Edit Appointment", "Update status or urgency"))

        form = QFormLayout()
        form.setSpacing(10)

        # Read-only info
        info_patient = QLabel(self.appt.get("patient", "—"))
        info_patient.setStyleSheet(f"font-weight:600;color:{DARK_TEXT};")
        info_doctor = QLabel(self.appt.get("doctor", "—"))
        info_doctor.setStyleSheet(f"font-weight:600;color:{DARK_TEXT};")
        info_time = QLabel(f"{self.appt.get('date','—')}  at  {self.appt.get('time_disp','—')}")
        info_time.setStyleSheet(f"font-weight:600;color:{DARK_TEXT};")

        form.addRow("Patient:", info_patient)
        form.addRow("Doctor:", info_doctor)
        form.addRow("Date & Time:", info_time)

        # IMPROVEMENT: Status toggle
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pending", "Completed", "Cancelled"])
        idx = self.status_combo.findText(self.appt.get("status", "Pending"))
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        form.addRow("Status *", self.status_combo)

        # IMPROVEMENT: Urgency — only doctor/admin
        self.urgent_cb = QCheckBox("Mark as Urgent")
        self.urgent_cb.setChecked(self.appt.get("priority", "Normal") == "Urgent")
        form.addRow("Priority", self.urgent_cb)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        save = QPushButton("Save Changes")
        save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("outline")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _save(self):
        # CHANGED
        new_status = self.status_combo.currentText()
        is_urgent = self.urgent_cb.isChecked()

        self.appt["status"] = new_status
        self.appt["priority"] = "Urgent" if is_urgent else "Normal"

        # Re-heapify to reflect new priority
        date_str = self.appt.get("date", "")
        if date_str in appointments_by_date:
            new_rank = 0 if is_urgent else 1
            new_heap = []
            for rank, tv, a in appointments_by_date[date_str]:
                if a is self.appt:
                    new_heap.append((new_rank, tv, a))
                else:
                    new_heap.append((rank, tv, a))
            heapq.heapify(new_heap)
            appointments_by_date[date_str] = new_heap

        save_data()
        self.accept()


# ══════════════════════════════════════════════
#  PANELS
# ══════════════════════════════════════════════

class DoctorsPanel(QWidget):
    def __init__(self, read_only=False):
        super().__init__()
        self.read_only = read_only
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(make_header("Doctors", "Manage clinic doctors"))

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search by name or specialization…")
        self.search.textChanged.connect(self._refresh)
        top.addWidget(self.search)

        if not self.read_only:
            add_btn = QPushButton("+ Add Doctor")
            add_btn.clicked.connect(self._add)
            top.addWidget(add_btn)
        layout.addLayout(top)

        self.table = styled_table(["Name","Specialization","Schedule","Hours","Username"])
        layout.addWidget(self.table)

        if not self.read_only:
            btn_row = QHBoxLayout()
            edit_btn = QPushButton("✏  Edit Selected")
            edit_btn.setObjectName("accent")
            edit_btn.clicked.connect(self._edit)
            del_btn = QPushButton("🗑  Delete Selected")
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(self._delete)
            btn_row.addStretch()
            btn_row.addWidget(edit_btn)
            btn_row.addWidget(del_btn)
            layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        # 1. Clear the table entirely
        self.table.setRowCount(0)

        # 2. Get current search query (to maintain filtering even after a load)
        query = self.search.text().lower().strip()

        # 3. Populate from global doctors_map
        for doc_id, d in doctors_map.items():
            # Apply search filter
            if query:
                match_name = query in d["name"].lower()
                match_spec = query in d["specialization"].lower()
                if not (match_name or match_spec):
                    continue

            # Add data to table
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(d["name"]))
            self.table.setItem(r, 1, QTableWidgetItem(d["specialization"]))
            self.table.setItem(r, 2, QTableWidgetItem(d["schedule"]))
            self.table.setItem(r, 3, QTableWidgetItem(f'{d["start_time"]} – {d["end_time"]}'))
            self.table.setItem(r, 4, QTableWidgetItem(d["username"]))

    def _selected_doctor(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Please select a doctor first.")
            return None
        username = self.table.item(row, 4).text()
        return doctors_map.get(username)

    def _add(self):
        dlg = DoctorDialog(self)
        if dlg.exec():
            self._refresh()

    def _edit(self):
        doc = self._selected_doctor()
        if doc:
            dlg = DoctorDialog(self, doc)
            if dlg.exec():
                self._refresh()

    def _delete(self):
        doc = self._selected_doctor()
        if doc:
            confirm = QMessageBox.question(self, "Delete", f"Delete Dr. {doc['name']}?")
            if confirm == QMessageBox.StandardButton.Yes:
                doctors_map.pop(doc["username"])
                save_data()
                self._refresh()


class PatientsPanel(QWidget):
    def __init__(self, read_only=False):
        super().__init__()
        self.read_only = read_only
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(make_header("Patients", "Manage clinic patients"))

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search by name or email…")
        self.search.textChanged.connect(self._refresh)
        top.addWidget(self.search)

        if not self.read_only:
            add_btn = QPushButton("+ Add Patient")
            add_btn.clicked.connect(self._add)
            top.addWidget(add_btn)
        layout.addLayout(top)

        self.table = styled_table(["Name","Birthdate","Gender","Age","Email","Address"])
        layout.addWidget(self.table)

        if not self.read_only:
            btn_row = QHBoxLayout()
            edit_btn = QPushButton("✏  Edit Selected")
            edit_btn.setObjectName("accent")
            edit_btn.clicked.connect(self._edit)
            del_btn = QPushButton("🗑  Delete Selected")
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(self._delete)
            btn_row.addStretch()
            btn_row.addWidget(edit_btn)
            btn_row.addWidget(del_btn)
            layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        # 1. Handle search query safely
        q = self.search.text().lower().strip() if hasattr(self, "search") else ""
        
        # 2. Clear table to rebuild it
        self.table.setRowCount(0)
        
        # 3. Iterate through the global patients_map
        for p in patients_map.values():
            # Search filter logic
            if q:
                name_match = q in p.get("name", "").lower()
                email_match = q in p.get("email", "").lower()
                if not (name_match or email_match):
                    continue
            
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            # Populate columns
            self.table.setItem(r, 0, QTableWidgetItem(p.get("name", "N/A")))
            self.table.setItem(r, 1, QTableWidgetItem(p.get("birthdate", "N/A")))
            self.table.setItem(r, 2, QTableWidgetItem(p.get("gender", "N/A")))
            
            # Age calculation
            age = compute_age(p.get("birthdate", ""))
            self.table.setItem(r, 3, QTableWidgetItem(str(age)))
            
            self.table.setItem(r, 4, QTableWidgetItem(p.get("email", "N/A")))
            self.table.setItem(r, 5, QTableWidgetItem(p.get("address", "N/A")))
            
            # Store unique ID (username) in column 0 for backend operations
            self.table.item(r, 0).setData(Qt.ItemDataRole.UserRole, p.get("username"))

    def _selected_patient(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Please select a patient first.")
            return None
        username = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return patients_map.get(username)

    def _add(self):
        dlg = PatientDialog(self)
        if dlg.exec():
            self._refresh()

    def _edit(self):
        pat = self._selected_patient()
        if pat:
            dlg = PatientDialog(self, pat)
            if dlg.exec():
                self._refresh()

    def _delete(self):
        pat = self._selected_patient()
        if pat:
            confirm = QMessageBox.question(self, "Delete", f"Delete patient {pat['name']}?")
            if confirm == QMessageBox.StandardButton.Yes:
                patients_map.pop(pat["username"], None)
                save_data()
                self._refresh()


class AppointmentsPanel(QWidget):
    """
    IMPROVEMENTS:
    - Patients only see their own appointments (filtered by patient_username).
    - Status/Urgency columns displayed.
    - Filter toggle bar for Pending/Completed/Cancelled/All.
    - Edit button for doctor/admin roles opens AppointmentEditDialog.
    - Doctor role sees only their own appointments.
    """
    def __init__(self, role="admin", patient_data=None, doctor_data=None):
        super().__init__()
        self.role = role
        self.patient_data = patient_data
        self.doctor_data = doctor_data
        self._get_filter = lambda: "All"
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(make_header("Appointments", "View and manage appointments"))

        # Top row: Book button (patient) + filter bar
        top = QHBoxLayout()

        if self.role == "patient":
            book_btn = QPushButton("+ Book Appointment")
            book_btn.clicked.connect(self._book)
            top.addWidget(book_btn)

        if self.role == "admin":
            book_btn = QPushButton("+ Add Appointment")
            book_btn.clicked.connect(self._book_admin)
            top.addWidget(book_btn)

        top.addStretch()
        layout.addLayout(top)

        # IMPROVEMENT: Filter toggle bar
        filter_bar, self._get_filter = make_filter_bar(self._refresh)
        layout.addWidget(filter_bar)

        # Columns: Date, Time, Patient, Doctor, Priority (Urgency), Status, [Actions]
        cols = ["Date", "Time", "Patient", "Doctor", "Priority", "Status"]
        if self.role in ("doctor", "admin"):
            cols.append("Actions")
        self.table = styled_table(cols)
        # Store appt references for edit by row
        self._appt_refs = []
        layout.addWidget(self.table)

        self._refresh()

    def _refresh(self):
        """
        Refreshes the appointments table based on global data.
        Works for Admin, Doctor, and Patient roles.
        """
        self.table.setRowCount(0)
        self._appt_refs = []  # Clear references to prevent memory leaks or wrong edits
        status_filter = self._get_filter() # Assumes you have a method to get the status combo box value

        # 1. Iterate through sorted dates
        for date_str in sorted(appointments_by_date.keys()):
            # Work on a copy so we don't destroy the global heap
            temp_heap = list(appointments_by_date[date_str])

            while temp_heap:
                # Pop by priority (rank)
                rank, time_val, appt = heapq.heappop(temp_heap)

                # --- ROLE FILTERING ---
                # Patients only see their own
                if self.role == "patient":
                    if appt.get("patient_username") != self.patient_data.get("username"):
                        if appt.get("patient") != self.patient_data.get("name"):
                            continue

                # Doctors only see their own schedule
                if self.role == "doctor":
                    doc_label = f"Dr. {self.doctor_data['name']} — {self.doctor_data['specialization']}"
                    if appt.get("doctor","") != doc_label:
                        continue

                # --- STATUS FILTERING ---
                if status_filter != "All" and appt.get("status","Pending") != status_filter:
                    continue

                # --- UI POPULATION ---
                r = self.table.rowCount()
                self.table.insertRow(r)
                self._appt_refs.append(appt)

                # Basic Columns
                self.table.setItem(r, 0, QTableWidgetItem(date_str))
                self.table.setItem(r, 1, QTableWidgetItem(appt.get("time_disp","")))
                self.table.setItem(r, 2, QTableWidgetItem(appt.get("patient","")))
                self.table.setItem(r, 3, QTableWidgetItem(appt.get("doctor","")))

                # Priority Column
                priority = appt.get("priority", "Normal")
                pri_item = QTableWidgetItem("🚨 Urgent" if priority == "Urgent" else "Normal")
                if priority == "Urgent":
                    pri_item.setForeground(QColor(DANGER))
                    pri_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table.setItem(r, 4, pri_item)

                # Status Column
                status = appt.get("status", "Pending")
                status_item = QTableWidgetItem(status)
                if status == "Completed":
                    status_item.setForeground(QColor(SUCCESS))
                    status_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                elif status == "Pending":
                    status_item.setForeground(QColor(ACCENT))
                elif status == "Cancelled":
                    status_item.setForeground(QColor(DANGER))
                self.table.setItem(r, 5, status_item)

                # Action Buttons (Only for Admin/Doctor)
                if self.role in ("doctor", "admin"):
                    btn_widget = QWidget()
                    btn_layout = QHBoxLayout(btn_widget)
                    btn_layout.setContentsMargins(4, 2, 4, 2)
                    btn_layout.setSpacing(4)

                    edit_btn = QPushButton("✏ Edit")
                    edit_btn.setFixedHeight(28)
                    edit_btn.setStyleSheet(f"background:{ACCENT};color:{DARK_TEXT};border-radius:4px;padding:2px 10px;font-size:12px;font-weight:600;")
                    edit_btn.clicked.connect(lambda checked, a=appt: self._edit_appt(a))
                    btn_layout.addWidget(edit_btn)

                    if status == "Pending":
                        done_btn = QPushButton("✔ Done")
                        done_btn.setFixedHeight(28)
                        done_btn.setStyleSheet(f"background:{SUCCESS};color:white;border-radius:4px;padding:2px 10px;font-size:12px;font-weight:600;")
                        done_btn.clicked.connect(lambda checked, a=appt: self._quick_complete(a))
                        btn_layout.addWidget(done_btn)

                    self.table.setCellWidget(r, 6, btn_widget)

    def _edit_appt(self, appt):
        """IMPROVEMENT: Only doctor/admin can open the edit dialog."""
        dlg = AppointmentEditDialog(self, appt, self.role)
        if dlg.exec():
            self._refresh()

    def _quick_complete(self, appt):
        appt["status"] = "Completed"
        save_data()
        self._refresh()
        QMessageBox.information(self, "Updated", "Appointment marked as Completed.")

    def _book(self):
        """Patient books their own appointment."""
        dlg = AppointmentDialog(self, self.patient_data, role="patient")
        if dlg.exec():
            self._refresh()

    def _book_admin(self):
        """Admin books any appointment."""
        dlg = AppointmentDialog(self, None, role="admin")
        if dlg.exec():
            self._refresh()


# ══════════════════════════════════════════════
#  DASHBOARD WINDOWS
# ══════════════════════════════════════════════

class AdminWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clinic System — Admin Dashboard")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(BASE_STYLE)
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top Bar ---
        topbar = QWidget()
        topbar.setStyleSheet(f"background:{PRIMARY};")
        topbar.setFixedHeight(60)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel("🏥   ClinicSys")
        logo.setStyleSheet("color:white;font-size:20px;font-weight:700;")
        
        role_lbl = QLabel("Logged in as: Admin")
        role_lbl.setStyleSheet("color:#b2dfdb;font-size:13px;")
        
        logout_btn = QPushButton("⏏   Log Out")
        logout_btn.setStyleSheet(
            "background:#ffffff22;color:white;border-radius:4px;padding:6px 16px;font-weight:600;"
        )
        logout_btn.clicked.connect(self._logout)

        tb_layout.addWidget(logo)
        tb_layout.addStretch()
        tb_layout.addWidget(role_lbl)
        tb_layout.addSpacing(16)
        tb_layout.addWidget(logout_btn)
        main_layout.addWidget(topbar)

        # --- Workspace ---
        workspace_container = QWidget()
        workspace_layout = QHBoxLayout(workspace_container)
        workspace_layout.setContentsMargins(16, 16, 16, 16)
        workspace_layout.setSpacing(16)

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background: #f5f5f5; border-radius: 8px; border: 1px solid #ddd;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(12)

        sidebar_title = QLabel("SYSTEM CONTROLS")
        sidebar_title.setStyleSheet("font-weight: bold; color: #555; border: none;")
        
        load_btn = QPushButton("📥   Load Data")
        load_btn.setFixedHeight(40) # Fixed method name
        load_btn.clicked.connect(self._handle_load_data)

        reset_btn = QPushButton("♻️   Reset Data")
        reset_btn.setFixedHeight(40) # Fixed method name
        reset_btn.setStyleSheet("background: #ffebee; color: #c62828;")
        reset_btn.clicked.connect(self._handle_reset_data)

        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(load_btn)
        sidebar_layout.addWidget(reset_btn)
        sidebar_layout.addStretch()

        # Panels (Stored as attributes so we can refresh them)
        self.doc_panel = DoctorsPanel()
        self.pat_panel = PatientsPanel()
        self.app_panel = AppointmentsPanel(role="admin")

        self.tabs = QTabWidget()
        self.tabs.addTab(self.doc_panel, "👨‍⚕️   Doctors")
        self.tabs.addTab(self.pat_panel, "🧑   Patients")
        self.tabs.addTab(self.app_panel, "📅   Appointments")

        workspace_layout.addWidget(sidebar)
        workspace_layout.addWidget(self.tabs)
        main_layout.addWidget(workspace_container)

    def _handle_load_data(self):
        try:
            if load_data():
                # This is the critical step: tell the panels to update
                self.doc_panel._refresh()
                self.pat_panel._refresh()
                self.app_panel._refresh()
                
                QMessageBox.information(self, "Success", "Data loaded successfully.")
            else:
                QMessageBox.warning(self, "Notice", "No data file found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def _handle_reset_data(self):
        reply = QMessageBox.question(self, "Confirm", "Reset all data?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # 1. Clear the actual data
            doctors_map.clear()
            patients_map.clear()
            appointments_by_date.clear()
            occupied_slots.clear()
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            
            # 2. Refresh the UI to show empty panels
            self.doc_panel._refresh()
            self.pat_panel._refresh()
            self.app_panel._refresh()
            
            QMessageBox.warning(self, "Reset", "System cleared.")

    def _logout(self):
        self.logout_requested.emit()
        self.close()

class DoctorWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, doctor_data):
        super().__init__()
        self.doctor_data = doctor_data
        self.setWindowTitle(f"Clinic System — Dr. {doctor_data['name']}")
        self.setMinimumSize(950, 650)
        self.setStyleSheet(BASE_STYLE)
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        topbar = QWidget()
        topbar.setStyleSheet(f"background:{PRIMARY};")
        topbar.setFixedHeight(60)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel("🏥  ClinicSys")
        logo.setStyleSheet("color:white;font-size:20px;font-weight:700;")
        role_lbl = QLabel(
            f"Dr. {self.doctor_data['name']}  |  {self.doctor_data['specialization']}"
        )
        role_lbl.setStyleSheet("color:#b2dfdb;font-size:13px;")
        logout_btn = QPushButton("⏏  Log Out")
        logout_btn.setStyleSheet(
            "background:#ffffff22;color:white;border-radius:4px;padding:6px 16px;font-weight:600;"
        )
        logout_btn.clicked.connect(self._logout)

        tb_layout.addWidget(logo)
        tb_layout.addStretch()
        tb_layout.addWidget(role_lbl)
        tb_layout.addSpacing(16)
        tb_layout.addWidget(logout_btn)
        main_layout.addWidget(topbar)

        tabs = QTabWidget()
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.addWidget(tabs)
        main_layout.addWidget(content)

        tabs.addTab(PatientsPanel(read_only=True), "🧑  Patient Records")
        # IMPROVEMENT: Doctor sees only their own appointments; can edit status/urgency
        tabs.addTab(
            AppointmentsPanel(role="doctor", doctor_data=self.doctor_data),
            "📅  My Schedule"
        )

    def _logout(self):
        self.logout_requested.emit()
        self.close()


# ══════════════════════════════════════════════
#  MY PROFILE PANEL
# ══════════════════════════════════════════════

class MyProfilePanel(QWidget):
    def __init__(self, patient_data: dict):
        super().__init__()
        self.patient_data = patient_data
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)
        outer.addWidget(make_header("My Profile", "Your personal information on file"))

        hero = QFrame()
        hero.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {PRIMARY}, stop:1 {SECONDARY});
                border-radius: 12px;
            }}
        """)
        hero.setFixedHeight(110)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 16, 24, 16)

        avatar = QLabel("👤")
        avatar.setStyleSheet("""
            font-size: 48px;
            background: rgba(255,255,255,0.15);
            border-radius: 36px;
            padding: 6px 14px;
        """)
        avatar.setFixedSize(72, 72)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_block = QVBoxLayout()
        name_lbl = QLabel(self.patient_data.get("name", "—"))
        name_lbl.setStyleSheet("color:white;font-size:20px;font-weight:800;")
        uname_lbl = QLabel(f"@{self.patient_data.get('username','')}")
        uname_lbl.setStyleSheet("color:rgba(255,255,255,0.75);font-size:13px;")
        gender_age = QLabel(
            f"{self.patient_data.get('gender','—')}  ·  "
            f"{compute_age(self.patient_data.get('birthdate',''))} years old"
        )
        gender_age.setStyleSheet("color:rgba(255,255,255,0.85);font-size:13px;")
        name_block.addWidget(name_lbl)
        name_block.addWidget(uname_lbl)
        name_block.addWidget(gender_age)

        hero_layout.addWidget(avatar)
        hero_layout.addSpacing(16)
        hero_layout.addLayout(name_block)
        hero_layout.addStretch()
        outer.addWidget(hero)

        grid = QGridLayout()
        grid.setSpacing(12)

        fields = [
            ("🎂  Date of Birth", self.patient_data.get("birthdate", "—")),
            ("⚧  Gender",         self.patient_data.get("gender", "—")),
            ("🔢  Age",            f"{compute_age(self.patient_data.get('birthdate',''))} years old"),
            ("📧  Email",          self.patient_data.get("email", "—")),
            ("🏠  Address",        self.patient_data.get("address", "—")),
            ("👤  Username",       self.patient_data.get("username", "—")),
        ]

        for i, (label, value) in enumerate(fields):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border: 1px solid {BORDER};
                    border-radius: 10px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            card_layout.setSpacing(4)
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color:{MUTED};font-size:11px;font-weight:700;letter-spacing:0.5px;"
            )
            val = QLabel(value)
            val.setStyleSheet(f"color:{DARK_TEXT};font-size:14px;font-weight:600;")
            val.setWordWrap(True)
            card_layout.addWidget(lbl)
            card_layout.addWidget(val)
            row, col = divmod(i, 2)
            grid.addWidget(card, row, col)

        outer.addLayout(grid)
        outer.addStretch()


# ══════════════════════════════════════════════
#  DOCTORS DIRECTORY PANEL (read-only for patients)
# ══════════════════════════════════════════════

class DoctorsDirectoryPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addWidget(make_header("Our Doctors", "Browse available clinic doctors"))

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search by name or specialization…")
        self.search.textChanged.connect(self._refresh)
        search_row.addWidget(self.search)
        layout.addLayout(search_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        self._refresh()

    def _refresh(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        q = self.search.text().lower()
        filtered = [
            d for d in doctors_map.values()
            if not q or q in d["name"].lower() or q in d["specialization"].lower()
        ]

        if not filtered:
            empty = QLabel("No doctors found matching your search.")
            empty.setStyleSheet(f"color:{MUTED};font-size:14px;margin-top:20px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty)
            self.cards_layout.addStretch()
            return

        for doc in filtered:
            self.cards_layout.addWidget(self._make_doctor_card(doc))
        self.cards_layout.addStretch()

    def _make_doctor_card(self, doc: dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {SECONDARY};
            }}
        """)
        row = QHBoxLayout(card)
        row.setContentsMargins(20, 16, 20, 16)
        row.setSpacing(20)

        avatar = QLabel("👨‍⚕️")
        avatar.setStyleSheet(f"""
            font-size: 30px;
            background: {LIGHT_BG};
            border-radius: 30px;
            padding: 8px 12px;
        """)
        avatar.setFixedSize(60, 60)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(avatar)

        info = QVBoxLayout()
        info.setSpacing(3)
        name_lbl = QLabel(f"Dr. {doc['name']}")
        name_lbl.setStyleSheet(f"font-size:16px;font-weight:700;color:{DARK_TEXT};")
        spec_lbl = QLabel(doc.get("specialization", "—"))
        spec_lbl.setStyleSheet(f"""
            font-size:12px;font-weight:700;color:{SECONDARY};
            background:{LIGHT_BG};border-radius:4px;padding:2px 8px;
        """)
        spec_lbl.setFixedWidth(spec_lbl.sizeHint().width() + 16)
        info.addWidget(name_lbl)
        info.addWidget(spec_lbl)
        row.addLayout(info)
        row.addStretch()

        sched_block = QVBoxLayout()
        sched_block.setSpacing(2)
        sched_block.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        days_lbl = QLabel(f"📅  {doc.get('schedule','—')}")
        days_lbl.setStyleSheet(f"color:{DARK_TEXT};font-size:13px;font-weight:600;")
        days_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        hours_lbl = QLabel(f"🕐  {doc.get('start_time','—')} – {doc.get('end_time','—')}")
        hours_lbl.setStyleSheet(f"color:{MUTED};font-size:12px;")
        hours_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        sched_block.addWidget(days_lbl)
        sched_block.addWidget(hours_lbl)
        row.addLayout(sched_block)
        return card


# ══════════════════════════════════════════════
#  PATIENT WINDOW
# ══════════════════════════════════════════════

class PatientWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, patient_data):
        super().__init__()
        self.patient_data = patient_data
        self.setWindowTitle(f"Clinic System — {patient_data['name']}")
        self.setMinimumSize(900, 620)
        self.setStyleSheet(BASE_STYLE)
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        topbar = QWidget()
        topbar.setStyleSheet(f"background:{PRIMARY};")
        topbar.setFixedHeight(60)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel("🏥  ClinicSys")
        logo.setStyleSheet("color:white;font-size:20px;font-weight:700;")
        role_lbl = QLabel(f"Patient: {self.patient_data['name']}")
        role_lbl.setStyleSheet("color:#b2dfdb;font-size:13px;")
        logout_btn = QPushButton("⏏  Log Out")
        logout_btn.setStyleSheet(
            "background:#ffffff22;color:white;border-radius:4px;"
            "padding:6px 16px;font-weight:600;"
        )
        logout_btn.clicked.connect(self._logout)

        tb_layout.addWidget(logo)
        tb_layout.addStretch()
        tb_layout.addWidget(role_lbl)
        tb_layout.addSpacing(16)
        tb_layout.addWidget(logout_btn)
        main_layout.addWidget(topbar)

        tabs = QTabWidget()
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.addWidget(tabs)
        main_layout.addWidget(content)

        tabs.addTab(MyProfilePanel(self.patient_data), "👤  My Profile")
        # IMPROVEMENT: Patient only sees their own appointments
        tabs.addTab(
            AppointmentsPanel(role="patient", patient_data=self.patient_data),
            "📅  My Appointments"
        )
        tabs.addTab(DoctorsDirectoryPanel(), "👨‍⚕️  Our Doctors")

    def _logout(self):
        self.logout_requested.emit()
        self.close()


# ══════════════════════════════════════════════
#  LOGIN WINDOW
# ══════════════════════════════════════════════

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClinicSys — Login")
        self.setFixedSize(460, 560)
        self.setStyleSheet(BASE_STYLE)
        self._active_window = None
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)

        banner = QWidget()
        banner.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {PRIMARY},stop:1 {SECONDARY});"
        )
        banner.setFixedHeight(170)
        b_layout = QVBoxLayout(banner)
        b_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl = QLabel("🏥")
        icon_lbl.setStyleSheet("font-size:48px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl = QLabel("ClinicSys")
        title_lbl.setStyleSheet("color:white;font-size:28px;font-weight:800;letter-spacing:2px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl = QLabel("Clinic Appointment Management System")
        sub_lbl.setStyleSheet("color:#b2dfdb;font-size:12px;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_layout.addWidget(icon_lbl)
        b_layout.addWidget(title_lbl)
        b_layout.addWidget(sub_lbl)
        outer.addWidget(banner)

        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background: white;
                border-radius: 16px;
                margin: 0 30px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(14)

        welcome = QLabel("Welcome Back")
        welcome.setStyleSheet(f"font-size:20px;font-weight:700;color:{PRIMARY};")
        card_layout.addWidget(welcome)
        hint = QLabel("Please sign in to continue")
        hint.setStyleSheet(f"color:{MUTED};font-size:12px;margin-bottom:4px;")
        card_layout.addWidget(hint)

        u_lbl = QLabel("Username")
        u_lbl.setStyleSheet(f"font-weight:600;font-size:13px;color:{DARK_TEXT};")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        self.username_edit.setFixedHeight(40)
        card_layout.addWidget(u_lbl)
        card_layout.addWidget(self.username_edit)

        p_lbl = QLabel("Password")
        p_lbl.setStyleSheet(f"font-weight:600;font-size:13px;color:{DARK_TEXT};")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setFixedHeight(40)
        self.password_edit.returnPressed.connect(self._login)
        card_layout.addWidget(p_lbl)
        card_layout.addWidget(self.password_edit)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet(f"color:{DANGER};font-size:12px;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.error_lbl)

        login_btn = QPushButton("Sign In  →")
        login_btn.setFixedHeight(44)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY};
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {SECONDARY};
            }}
        """)
        login_btn.clicked.connect(self._login)
        card_layout.addWidget(login_btn)

        outer.addSpacing(16)
        outer.addWidget(card)
        outer.addStretch()

        hint2 = QLabel("Default admin: admin / admin123")
        hint2.setStyleSheet(f"color:{MUTED};font-size:11px;")
        hint2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(hint2)
        outer.addSpacing(10)

    def _login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            self.error_lbl.setText("Please enter both username and password.")
            return

        user = find_user_hash(username, password)
        if user is None:
            self.error_lbl.setText("Invalid username or password.")
            return

        self.error_lbl.setText("")
        self.username_edit.clear()
        self.password_edit.clear()
        self._open_dashboard(user)

    def _open_dashboard(self, user):
        role = user["role"]
        if role == "admin":
            win = AdminWindow()
        elif role == "doctor":
            win = DoctorWindow(user["data"])
        else:
            win = PatientWindow(user["data"])

        win.logout_requested.connect(self._on_logout)
        self._active_window = win
        win.show()
        self.hide()

    def _on_logout(self):
        self._active_window = None
        self.show()

# ══════════════════════════════════════════════
#  SEED DEMO DATA
# ══════════════════════════════════════════════

def seed_demo():
    doc1 = {
        "name": "Maria Santos", "specialization": "General Medicine",
        "schedule": "Monday-Friday", "start_time": "08:00", "end_time": "17:00",
        "username": "dr_santos", "password": "doc123"
    }
    doc2 = {
        "name": "Juan Reyes", "specialization": "Pediatrics",
        "schedule": "Monday-Saturday", "start_time": "09:00", "end_time": "16:00",
        "username": "dr_reyes", "password": "doc123"
    }
    doctors_map[doc1["username"]] = doc1
    doctors_map[doc2["username"]] = doc2

    p1 = {
        "name": "Ana Garcia", "birthdate": "1990-05-15",
        "gender": "Female", "age": compute_age("1990-05-15"),
        "email": "ana.garcia@email.com", "address": "123 Rizal St, CDO",
        "username": "ana.garcia", "password": "1234"
    }
    p2 = {
        "name": "Pedro Lim", "birthdate": "1985-11-20",
        "gender": "Male", "age": compute_age("1985-11-20"),
        "email": "pedro.lim@email.com", "address": "456 Maharlika Ave, CDO",
        "username": "pedro.lim", "password": "1234"
    }
    patients_map[p1["username"]] = p1
    patients_map[p2["username"]] = p2

    date_key = "2026-05-20"
    appt1 = {
        "time_val": "10:00",
        "time_disp": "10:00 AM",
        "patient": "Ana Garcia",
        "patient_username": "ana.garcia",
        "doctor": "Dr. Maria Santos — General Medicine",
        "doctor_username": "dr_santos",
        "status": "Pending",
        "priority": "Normal",
        "date": date_key,
    }
    appt2 = {
        "time_val": "11:00",
        "time_disp": "11:00 AM",
        "patient": "Pedro Lim",
        "patient_username": "pedro.lim",
        "doctor": "Dr. Maria Santos — General Medicine",
        "doctor_username": "dr_santos",
        "status": "Pending",
        "priority": "Urgent",
        "date": date_key,
    }

    if date_key not in appointments_by_date:
        appointments_by_date[date_key] = []

    heapq.heappush(appointments_by_date[date_key], (1, "10:00", appt1))
    heapq.heappush(appointments_by_date[date_key], (0, "11:00", appt2))  # Urgent → rank 0

    occupied_slots.add(("dr_santos", date_key, "10:00 AM"))
    occupied_slots.add(("dr_santos", date_key, "11:00 AM"))


# ══════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    login = LoginWindow()
    login.show()
    sys.exit(app.exec())