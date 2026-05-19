import json
import os
import sys
from datetime import date, datetime

from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QMessageBox, QComboBox, QDateEdit,
    QTimeEdit, QTabWidget, QFrame, QHeaderView, QScrollArea,
    QGridLayout, QTextEdit, QButtonGroup, QRadioButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# ── Custom data structures and algorithms (all hand-built in custom_ds.py) ───
from custom_ds import (
    HashMap, HashSet, MinHeap, DateAppointmentMap,
    DoctorBST,
    hash_lookup_user,
    time_str_to_minutes,
    check_exact_conflict,
    check_30min_conflict,
    greedy_available_slots,
)

# ─────────────────────────────────────────────
#  FILE PERSISTENCE  (JSON-based storage)
# ─────────────────────────────────────────────
DATA_FILE = "clinic_data.json"


def save_data():
    """Serialise all in-memory custom structures to JSON and write to disk."""
    # HashMap → plain dict for JSON
    payload = {
        "doctors":        {k: v for k, v in doctors_map.items()},
        "patients":       {k: v for k, v in patients_map.items()},
        "appointments":   appointments_by_date.to_serialisable(),
        # HashSet iteration yields encoded string keys;
        # we store them as a list and re-add on load.
        "occupied_slots": list(iter(occupied_slots)),
    }
    with open(DATA_FILE, "w") as f:
        json.dump(payload, f, indent=2)


def load_data():
    """Load persisted JSON into the custom in-memory structures."""
    global doctors_map, patients_map, appointments_by_date, occupied_slots
    if not os.path.exists(DATA_FILE):
        return False
    try:
        with open(DATA_FILE, "r") as f:
            payload = json.load(f)

        # Restore HashMaps
        for k, v in payload.get("doctors", {}).items():
            doctors_map[k] = v
            doctors_bst.insert(v)
        for k, v in payload.get("patients", {}).items():
            patients_map[k] = v

        # Restore DateAppointmentMap (each date → MinHeap)
        appointments_by_date.from_serialisable(payload.get("appointments", {}))

        # Restore HashSet — encoded keys stored as strings
        for encoded_key in payload.get("occupied_slots", []):
            # HashSet.add expects original element; since we stored encoded
            # strings we add them directly via the internal map.
            occupied_slots._map[encoded_key] = True

        return True
    except Exception as e:
        print(f"[WARN] Could not load data: {e}")
        return False


def reset_system_data():
    #clear all custom data structures and delete the data file to reset the system
    doctors_map.clear()
    patients_map.clear()
    appointments_by_date.clear()
    occupied_slots.clear()
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)


# ─────────────────────────────────────────────
#  GLOBAL DATA STORE  — custom structures only
# ─────────────────────────────────────────────
doctors_map          = HashMap()            # username → doctor dict
patients_map         = HashMap()            # username → patient dict
appointments_by_date = DateAppointmentMap() # date_str → MinHeap of appointments
occupied_slots       = HashSet()            # (doc_username, date_str, time_str)
doctors_bst          = DoctorBST()         # doctors sorted by name (BST)
# ─────────────────────────────────────────────
#  BUILT-IN ADMIN ACCOUNT
# ─────────────────────────────────────────────
admin_user = {"username": "admin", "password": "admin123", "role": "admin"}

# ══════════════════════════════════════════════
#  STYLE CONSTANTS
# ══════════════════════════════════════════════
PRIMARY   = "#0d7377"
SECONDARY = "#14919b"
ACCENT    = "#ff9500"
LIGHT_BG  = "#f0f7f7"
DARK_TEXT = "#0d2b2b"
MUTED     = "#5a8a8a"
DANGER    = "#d63230"
SUCCESS   = "#2ecc71"
WARNING   = "#f39c12"
CARD_BG   = "#ffffff"
BORDER    = "#c0dfe0"

BASE_STYLE = f"""
QMainWindow, QDialog {{
    background: {LIGHT_BG};
}}
QWidget {{
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    color: {DARK_TEXT};
}}
QLabel#heading {{
    font-size: 24px;
    font-weight: 800;
    color: {PRIMARY};
    letter-spacing: 0.5px;
}}
QLabel#subheading {{
    font-size: 14px;
    color: {MUTED};
    font-weight: 500;
}}
QPushButton {{
    background: {PRIMARY};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{ 
    background: {SECONDARY}; 
    padding: 10px 18px;
}}
QPushButton:pressed {{ background: #0a4d52; }}
QPushButton#danger {{ background: {DANGER}; }}
QPushButton#danger:hover {{ background: #e74c3c; }}
QPushButton#accent {{ background: {ACCENT}; color: {DARK_TEXT}; }}
QPushButton#accent:hover {{ background: #ffaa1a; }}
QPushButton#outline {{
    background: transparent;
    color: {PRIMARY};
    border: 2px solid {PRIMARY};
}}
QPushButton#outline:hover {{ background: {PRIMARY}; color: white; }}
QPushButton#success {{ background: {SUCCESS}; color: white; }}
QPushButton#success:hover {{ background: #27ae60; }}
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QTextEdit {{
    background: white;
    border: 1.5px solid {BORDER};
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13px;
    color: {DARK_TEXT};
    selection-background-color: {PRIMARY};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QTextEdit:focus {{
    border: 2px solid {SECONDARY};
    background: #fafbfb;
}}
QComboBox::drop-down {{
    border: none;
    background: white;
    border-radius: 0 4px 4px 0;
}}
QAbstractItemView {{
    background: white;
    color: {DARK_TEXT};
    selection-background-color: {PRIMARY};
    selection-color: white;
    border: 1px solid {BORDER};
    outline: none;
    border-radius: 4px;
}}
QTableWidget {{
    background: white;
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    font-size: 12px;
    alternate-background-color: #f7fbfb;
}}
QTableWidget::item {{ 
    padding: 8px; 
    color: {DARK_TEXT};
}}
QTableWidget::item:selected {{ 
    background: #e0f2f4; 
    color: {DARK_TEXT}; 
}}
QHeaderView::section {{
    background: {PRIMARY};
    color: white;
    font-weight: 700;
    padding: 10px;
    border: none;
    font-size: 12px;
    letter-spacing: 0.3px;
}}
QTabWidget::pane {{
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    background: white;
}}
QTabBar::tab {{
    background: {LIGHT_BG};
    color: {MUTED};
    padding: 12px 24px;
    border-radius: 6px 6px 0 0;
    font-weight: 600;
    margin-right: 2px;
    font-size: 13px;
}}
QTabBar::tab:selected {{ 
    background: white;
    color: {PRIMARY}; 
    border-bottom: 3px solid {PRIMARY};
}}
QFrame#card {{
    background: white;
    border: 1.5px solid {BORDER};
    border-radius: 10px;
}}
QRadioButton {{
    font-size: 13px;
    color: {DARK_TEXT};
    padding: 4px 8px;
    font-weight: 500;
}}
QRadioButton::indicator {{ width: 16px; height: 16px; }}
QCheckBox {{
    font-size: 13px;
    color: {DARK_TEXT};
    padding: 4px;
    font-weight: 500;
}}
QCheckBox::indicator {{ width: 16px; height: 16px; }}
QScrollArea {{
    background: transparent;
    border: none;
}}
"""

# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

def find_user(username, password):
    """Delegate to custom hash_lookup_user (O(1) average)."""
    return hash_lookup_user(username, password, admin_user, doctors_map, patients_map)


def compute_age(birthdate_str: str) -> int:
    try:
        bd = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except Exception:
        return 0


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


# ══════════════════════════════════════════════
#  SHARED WIDGETS
# ══════════════════════════════════════════════

def make_header(title: str, subtitle: str = "") -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 12)
    lbl = QLabel(title)
    lbl.setObjectName("heading")
    v.addWidget(lbl)
    if subtitle:
        sub = QLabel(subtitle)
        sub.setObjectName("subheading")
        v.addWidget(sub)
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {BORDER}; height: 1px;")
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


def make_filter_bar(callback) -> tuple:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    lbl = QLabel("Filter:")
    lbl.setStyleSheet(f"color:{MUTED};font-weight:600;font-size:13px;")
    layout.addWidget(lbl)

    group = QButtonGroup(container)
    options = [("All", "All"), ("Pending", "Pending"),
               ("In-Progress", "In-Progress"),
               ("Completed", "Completed"), ("Cancelled", "Cancelled")]
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
#  DOCTOR DIALOG
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
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday", "Monday-Friday", "Monday-Saturday", "Saturday-Sunday"]
        self.sched_combo.addItems(days)
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("hh:mm AP")
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("hh:mm AP")
        self.end_time.setTime(QTime(17, 0))

        form.addRow("Full Name *",        self.name_edit)
        form.addRow("Specialization *",   self.spec_edit)
        form.addRow("Schedule (Days) *",  self.sched_combo)
        form.addRow("Start Time *",       self.start_time)
        form.addRow("End Time *",         self.end_time)
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
        st    = self.start_time.time().toString("HH:mm")
        et    = self.end_time.time().toString("HH:mm")
        sched = self.sched_combo.currentText()

        if self.doctor is None:
            last  = name.split()[-1]
            uname, pwd = make_doctor_credentials(last)
            new_doc = {
                "name": name, "specialization": spec,
                "schedule": sched, "start_time": st, "end_time": et,
                "username": uname, "password": pwd
            }
            doctors_map[uname] = new_doc          # HashMap O(1) insert
            doctors_bst.insert(new_doc) 
            save_data()
            QMessageBox.information(self, "Doctor Added",
                f"Doctor added!\n\nUsername: {uname}")
        else:
            self.doctor["name"]           = name
            self.doctor["specialization"] = spec
            self.doctor["schedule"]       = sched
            self.doctor["start_time"]     = st
            self.doctor["end_time"]       = et
            save_data()
        self.accept()


# ══════════════════════════════════════════════
#  PATIENT DIALOG
# ══════════════════════════════════════════════

class PatientDialog(QDialog):
    def __init__(self, parent=None, patient=None):
        super().__init__(parent)
        self.setWindowTitle("Add Patient" if patient is None else "Edit Patient")
        self.setMinimumWidth(480)
        self.setStyleSheet(BASE_STYLE)
        self.patient = patient
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.addWidget(make_header("Patient Information", "Fill in all required fields"))

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit   = QLineEdit()
        self.bdate_edit  = QDateEdit()
        self.bdate_edit.setDisplayFormat("yyyy-MM-dd")
        self.bdate_edit.setCalendarPopup(True)
        self.bdate_edit.setDate(QDate(2000, 1, 1))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other"])
        self.age_label   = QLabel("—")
        self.age_label.setStyleSheet(f"color: {MUTED}; font-weight: 600;")
        self.email_edit  = QLineEdit()
        self.address_edit = QTextEdit()
        self.address_edit.setFixedHeight(70)
        self.condition_edit = QLineEdit()#new field for patient's medical condition
        self.condition_edit.setPlaceholderText("e.g., Hypertension, Diabetes, General, Cardiovascular, Arthritis")
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(70)
        self.notes_edit.setPlaceholderText("e.g., BP monitoring, Lab results, Annual physical, Patient request, Joint pain")

        self.bdate_edit.dateChanged.connect(self._update_age)

        form.addRow("Full Name *",   self.name_edit)
        form.addRow("Birthdate *",   self.bdate_edit)
        form.addRow("Gender *",      self.gender_combo)
        form.addRow("Age (auto)",    self.age_label)
        form.addRow("Email *",       self.email_edit)
        form.addRow("Address *",     self.address_edit)
        form.addRow("Condition",     self.condition_edit)#new field for patient's medical condition
        form.addRow("Medical Notes", self.notes_edit)
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
            self.condition_edit.setText(self.patient.get("condition", ""))#new field for patient's medical condition
            self.notes_edit.setPlainText(self.patient.get("notes", ""))

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
        bd  = self.bdate_edit.date().toString("yyyy-MM-dd")
        age = compute_age(bd)
        self.age_label.setText(f"{age} years old")

    def _save(self):
        name    = self.name_edit.text().strip()
        email   = self.email_edit.text().strip()
        address = self.address_edit.toPlainText().strip()
        condition = self.condition_edit.text().strip()
        notes   = self.notes_edit.toPlainText().strip()
        bd      = self.bdate_edit.date().toString("yyyy-MM-dd")

        if not name or not email or not address:
            QMessageBox.warning(self, "Validation", "Name, Email and Address are required.")
            return

        age = compute_age(bd)

        if self.patient is None:
            uname, pwd = make_patient_credentials(name)
            new_p = {
                "name": name, "birthdate": bd,
                "gender": self.gender_combo.currentText(),
                "age": age, "email": email, "address": address,
                "condition": condition, "notes": notes,
                "username": uname, "password": pwd
            }
            patients_map[uname] = new_p       # HashMap O(1) insert
            save_data()
            QMessageBox.information(self, "Patient Added",
                f"Patient added!\n\nUsername: {uname}")
        else:
            self.patient["name"]      = name
            self.patient["birthdate"] = bd
            self.patient["gender"]    = self.gender_combo.currentText()
            self.patient["age"]       = age
            self.patient["email"]     = email
            self.patient["address"]   = address
            self.patient["condition"] = condition
            self.patient["notes"]     = notes
            save_data()
        self.accept()


# ══════════════════════════════════════════════
#  APPOINTMENT DIALOG
# ══════════════════════════════════════════════

class AppointmentDialog(QDialog):
    """
    Book a new appointment.
    - Only doctors/admins may mark urgency.
    - 30-minute spacing enforced (custom conflict detection).
    - Exact-slot conflict detected via HashSet O(1).
    """

    def __init__(self, parent=None, patient_data=None, role="patient"):
        super().__init__(parent)
        self.setWindowTitle("Book Appointment")
        self.setMinimumWidth(460)
        self.setStyleSheet(BASE_STYLE)
        self.patient_data = patient_data
        self.role = role
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

        # Replace the existing time_edit row with this block:
        time_row = QHBoxLayout()
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setTime(QTime(9, 0))
        time_row.addWidget(self.time_edit)

        suggest_btn = QPushButton("💡 Find Slots")
        suggest_btn.setObjectName("outline")
        suggest_btn.clicked.connect(self._suggest_slots)
        time_row.addWidget(suggest_btn)

        

        self.patient_combo = QComboBox()
        for p in patients_map.values():          # HashMap.values() O(capacity)
            self.patient_combo.addItem(p["name"], p["username"])

        self.doctor_combo = QComboBox()
        for uname, d in doctors_map.items():     # HashMap.items() O(capacity)
            self.doctor_combo.addItem(
                f"Dr. {d['name']} — {d['specialization']}", uname)

        self.urgent_cb = QCheckBox("Mark as Urgent")
        if self.role == "patient":
            self.urgent_cb.setEnabled(False)
            self.urgent_cb.setToolTip("Only doctors or admins can mark appointments as urgent.")
            self.urgent_cb.setStyleSheet(f"color:{MUTED};")

        form.addRow("Date *",     self.date_edit)
        form.addRow("Time *",     time_row)
        form.addRow("Patient *",  self.patient_combo)
        form.addRow("Doctor *",   self.doctor_combo)
        form.addRow("Priority",   self.urgent_cb)
        layout.addLayout(form)

        hint = QLabel("ℹ  Appointments must be at least 30 minutes apart.")
        hint.setStyleSheet(f"color:{MUTED};font-size:11px;")
        layout.addWidget(hint)

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

    def _suggest_slots(self):
        """Greedy slot optimizer — shows all available times for the chosen doctor/date."""
        doc_username = self.doctor_combo.currentData()
        doc          = doctors_map.get(doc_username)
        date_str     = self.date_edit.date().toString("yyyy-MM-dd")

        if not doc:
            QMessageBox.warning(self, "Select Doctor", "Please choose a doctor first.")
            return

        # ── Greedy optimization algorithm ─────────────────────────────────
        slots = greedy_available_slots(appointments_by_date, doc, date_str)

        if not slots:
            QMessageBox.information(self, "No Slots",
                f"Dr. {doc['name']} has no available slots on {date_str}.")
            return

        # Let the user pick from the greedy-generated list
        dlg = QDialog(self)
        dlg.setWindowTitle("Available Slots")
        dlg.setMinimumWidth(280)
        dlg.setStyleSheet(BASE_STYLE)
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel(f"<b>Available slots for Dr. {doc['name']}</b><br>{date_str}"))
        combo = QComboBox()
        combo.addItems(slots)
        v.addWidget(combo)
        btn_row = QHBoxLayout()
        ok  = QPushButton("Select")
        ok.clicked.connect(dlg.accept)
        btn_row.addWidget(ok)
        v.addLayout(btn_row)

        if dlg.exec():
            chosen = combo.currentText()          # e.g. "09:00"
            h, m   = int(chosen[:2]), int(chosen[3:])
            self.time_edit.setTime(QTime(h, m))

    def _book(self):
        date_str   = self.date_edit.date().toString("yyyy-MM-dd")
        time_str   = self.time_edit.time().toString("hh:mm AP")
        time_val   = self.time_edit.time().toString("HH:mm")
        date_obj   = self.date_edit.date()
        time_obj   = self.time_edit.time()

        doc_username = self.doctor_combo.currentData()
        doc          = doctors_map.get(doc_username)       # HashMap O(1)

        if not doc:
            QMessageBox.critical(self, "Error", "Invalid Doctor selection.")
            return

        # ── Day-of-week validation ─────────────────────────────────────
        day_of_week = date_obj.toPyDate().strftime("%A")
        sched = doc["schedule"]
        day_map = {
            "Monday-Friday":  ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "Monday-Saturday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "Saturday-Sunday": ["Saturday", "Sunday"],
            "Monday-Sunday":  ["Monday", "Tuesday", "Wednesday", "Thursday",
                               "Friday", "Saturday", "Sunday"],
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

        # ── Operating hours validation ─────────────────────────────────
        start_time = QTime.fromString(doc["start_time"], "HH:mm")
        end_time   = QTime.fromString(doc["end_time"],   "HH:mm")
        if time_obj < start_time or time_obj > end_time:
            QMessageBox.warning(self, "Invalid Time",
                f"Outside office hours ({doc['start_time']} – {doc['end_time']}).")
            return

        # ── Exact-slot conflict (HashSet O(1)) ─────────────────────────
        if check_exact_conflict(occupied_slots, doc_username, date_str, time_str):
            QMessageBox.critical(self, "Conflict",
                "This doctor is already booked at this exact time!")
            return

        # ── 30-minute buffer conflict (custom scan O(k)) ───────────────
        if check_30min_conflict(appointments_by_date, doctors_map,
                                doc_username, date_str, time_val):
            QMessageBox.warning(self, "Scheduling Conflict",
                "Appointments must be at least 30 minutes apart.\n"
                "Please choose a different time slot.")
            return

        is_urgent     = self.urgent_cb.isChecked() and self.role in ("doctor", "admin")
        priority_rank = 0 if is_urgent else 1

        pat_username  = self.patient_combo.currentData()
        pat           = patients_map.get(pat_username)    # HashMap O(1)
        patient_name  = pat["name"] if pat else "Unknown"

        appt_data = {
            "time_val":        time_val,
            "time_disp":       time_str,
            "patient":         patient_name,
            "patient_username": pat_username,
            "doctor":          self.doctor_combo.currentText(),
            "doctor_username": doc_username,
            "status":          "Pending",
            "priority":        "Urgent" if is_urgent else "Normal",
            "date":            date_str,
        }

        # ── MinHeap push O(log n) ──────────────────────────────────────
        appointments_by_date.push(date_str, priority_rank, time_val, appt_data)

        # ── HashSet add O(1) ──────────────────────────────────────────
        occupied_slots.add((doc_username, date_str, time_str))
        save_data()

        QMessageBox.information(self, "Success",
            f"Appointment booked!\nDate: {date_str}  |  Time: {time_str}\n"
            f"Priority: {'🚨 Urgent' if is_urgent else 'Normal'}")
        self.accept()


# ══════════════════════════════════════════════
#  APPOINTMENT EDIT DIALOG (Doctor / Admin only)
# ══════════════════════════════════════════════

class AppointmentEditDialog(QDialog):
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

        info_patient = QLabel(self.appt.get("patient", "—"))
        info_patient.setStyleSheet(f"font-weight:600;color:{DARK_TEXT};")
        info_doctor  = QLabel(self.appt.get("doctor",  "—"))
        info_doctor.setStyleSheet(f"font-weight:600;color:{DARK_TEXT};")
        info_time    = QLabel(
            f"{self.appt.get('date','—')}  at  {self.appt.get('time_disp','—')}")
        info_time.setStyleSheet(f"font-weight:600;color:{DARK_TEXT};")

        form.addRow("Patient:",    info_patient)
        form.addRow("Doctor:",     info_doctor)
        form.addRow("Date & Time:", info_time)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Pending", "In-Progress", "Completed", "Cancelled"])
        idx = self.status_combo.findText(self.appt.get("status", "Pending"))
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        form.addRow("Status *", self.status_combo)

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
        new_status = self.status_combo.currentText()
        is_urgent  = self.urgent_cb.isChecked()

        self.appt["status"]   = new_status
        self.appt["priority"] = "Urgent" if is_urgent else "Normal"

        # Update priority in MinHeap using replace_item O(n) then re-heap
        date_str = self.appt.get("date", "")
        if date_str in appointments_by_date:
            new_rank = 0 if is_urgent else 1
            heap = appointments_by_date.get_heap(date_str)
            heap.replace_item(self.appt, new_rank)   # custom MinHeap method

        save_data()
        self.accept()


# ══════════════════════════════════════════════
#  DASHBOARD PANEL
# ══════════════════════════════════════════════

class DashboardPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.stat_cards = {}  # Store references to stat value labels
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        layout.addWidget(make_header("Dashboard", "System Overview"))

        # Stats Grid
        self.stats_container = QWidget()
        stats_layout = QGridLayout(self.stats_container)
        stats_layout.setSpacing(16)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        # Today's Appointments
        card1, label1 = self._make_stat_card_with_label("  Today's Appointments", ACCENT, DARK_TEXT)
        self.stat_cards["today"] = label1
        stats_layout.addWidget(card1, 0, 0)

        # Total Patients
        card2, label2 = self._make_stat_card_with_label("  Total Patients", SUCCESS, "white")
        self.stat_cards["patients"] = label2
        stats_layout.addWidget(card2, 0, 1)

        # Doctors On Duty
        card3, label3 = self._make_stat_card_with_label("  Doctors On Duty", PRIMARY, "white")
        self.stat_cards["doctors"] = label3
        stats_layout.addWidget(card3, 0, 2)

        # Pending Records
        card4, label4 = self._make_stat_card_with_label("  Pending Records", WARNING, "white")
        self.stat_cards["pending"] = label4
        stats_layout.addWidget(card4, 0, 3)

        layout.addWidget(self.stats_container)

        # Recent Activity Section
        layout.addWidget(make_header("Recent Activity", "Latest appointments and updates"))

        # Recent appointments table
        recent_cols = ["Date", "Time", "Patient", "Doctor", "Status", "Priority"]
        self.recent_table = styled_table(recent_cols)
        layout.addWidget(self.recent_table)

        self._refresh_stats()
        layout.addStretch()

    def _make_stat_card_with_label(self, label: str, bg_color: str, text_color: str) -> tuple:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-radius: 12px;
                border: none;
            }}
        """)
        card.setMinimumHeight(140)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: 600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        val = QLabel("0")
        val.setStyleSheet(f"color: {text_color}; font-size: 36px; font-weight: 800;")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl)
        layout.addWidget(val)

        return card, val

    def _make_stat_card(self, label: str, value: str, bg_color: str, text_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-radius: 12px;
                border: none;
            }}
        """)
        card.setMinimumHeight(140)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: 600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        val = QLabel(value)
        val.setStyleSheet(f"color: {text_color}; font-size: 36px; font-weight: 800;")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl)
        layout.addWidget(val)

        return card

    def _refresh_stats(self):
        """Update all dashboard statistics from current data."""
        # Today's appointments
        today_count = self._count_today_appointments()
        self.stat_cards["today"].setText(str(today_count))
        
        # Total patients
        total_patients = len(list(patients_map.values()))
        self.stat_cards["patients"].setText(str(total_patients))
        
        # Doctors on duty
        doctors_on_duty = len(list(doctors_map.values()))
        self.stat_cards["doctors"].setText(str(doctors_on_duty))
        
        # Pending records
        pending_count = self._count_pending_appointments()
        self.stat_cards["pending"].setText(str(pending_count))
        
        # Refresh recent appointments table
        self._refresh_recent_appointments()

    def _count_today_appointments(self) -> int:
        today = date.today().strftime("%Y-%m-%d")
        if today in appointments_by_date:
            heap = appointments_by_date.get_heap(today)
            return len(list(heap))
        return 0

    def _count_pending_appointments(self) -> int:
        count = 0
        for date_str in appointments_by_date.sorted_dates():
            heap = appointments_by_date.get_heap(date_str)
            for rank, time_val, appt in heap:
                if appt.get("status") == "Pending":
                    count += 1
        return count

    def _refresh_recent_appointments(self):
        self.recent_table.setRowCount(0)
        today = date.today().strftime("%Y-%m-%d")

        # Get all appointments and sort by date/time
        all_appts = []
        for date_str in appointments_by_date.sorted_dates():
            heap = appointments_by_date.get_heap(date_str)
            for rank, time_val, appt in heap:
                all_appts.append((date_str, appt))

        # Show only recent (today and next 5 appointments)
        for i, (date_str, appt) in enumerate(all_appts[-5:]):
            r = self.recent_table.rowCount()
            self.recent_table.insertRow(r)

            self.recent_table.setItem(r, 0, QTableWidgetItem(date_str))
            self.recent_table.setItem(r, 1, QTableWidgetItem(appt.get("time_disp", "")))
            self.recent_table.setItem(r, 2, QTableWidgetItem(appt.get("patient", "")))
            self.recent_table.setItem(r, 3, QTableWidgetItem(appt.get("doctor", "")))

            status = appt.get("status", "Pending")
            status_item = QTableWidgetItem(status)
            if status == "Completed":
                status_item.setForeground(QColor(SUCCESS))
                status_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif status == "Pending":
                status_item.setForeground(QColor(ACCENT))
            elif status == "In-Progress":
                status_item.setForeground(QColor(WARNING))
                status_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif status == "Cancelled":
                status_item.setForeground(QColor(DANGER))
            self.recent_table.setItem(r, 4, status_item)

            priority = appt.get("priority", "Normal")
            pri_item = QTableWidgetItem("🚨 Urgent" if priority == "Urgent" else "Normal")
            if priority == "Urgent":
                pri_item.setForeground(QColor(DANGER))
                pri_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.recent_table.setItem(r, 5, pri_item)


# ══════════════════════════════════════════════
#  DOCTORS PANEL
# ══════════════════════════════════════════════

class DoctorsPanel(QWidget):
    def __init__(self, dashboard=None, read_only=False):
        super().__init__()
        self.dashboard = dashboard
        self.read_only = read_only
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(make_header("Doctors", "Manage clinic doctors"))

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search by name…")
        self.search.textChanged.connect(self._refresh)
        top.addWidget(self.search)

        self.spec_filter = QLineEdit()
        self.spec_filter.setPlaceholderText("🔍  Filter by specialization…")
        self.spec_filter.setMaximumWidth(250)
        self.spec_filter.textChanged.connect(self._refresh)
        top.addWidget(self.spec_filter)

        if not self.read_only:
            add_btn = QPushButton("+ Add Doctor")
            add_btn.clicked.connect(self._add)
            top.addWidget(add_btn)
        layout.addLayout(top)

        self.table = styled_table(["Name", "Specialization", "Schedule", "Hours", "Username"])
        layout.addWidget(self.table)

        if not self.read_only:
            btn_row = QHBoxLayout()
            edit_btn = QPushButton("  Edit Selected")
            edit_btn.setObjectName("accent")
            edit_btn.clicked.connect(self._edit)
            del_btn = QPushButton("  Delete Selected")
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(self._delete)
            btn_row.addStretch()
            btn_row.addWidget(edit_btn)
            btn_row.addWidget(del_btn)
            layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        self.table.setRowCount(0)
        query = self.search.text().lower().strip()
        spec_query = self.spec_filter.text().lower().strip()

        if query:
            # BST prefix search O(n) — finds matching doctors by name
            doctors = doctors_bst.search_prefix(query)
        else:
            # BST inorder O(n) — returns all doctors sorted A→Z by name
            doctors = doctors_bst.inorder()

        # Filter by specialization if specified
        if spec_query:
            doctors = [
                d for d in doctors
                if spec_query in d["specialization"].lower()
            ]

        for d in doctors:
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
        return doctors_map.get(username)             # HashMap O(1)

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
                doctors_bst.delete(doc["name"])    # BST delete O(log n)
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

        self.table = styled_table(["Name", "Birthdate", "Gender", "Age", "Condition", "Notes", "Email", "Address"])
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
        q = self.search.text().lower().strip() if hasattr(self, "search") else ""
        self.table.setRowCount(0)

        # HashMap.values() — all patient records
        for p in patients_map.values():
            if q:
                if q not in p.get("name", "").lower() and q not in p.get("email", "").lower():
                    continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(p.get("name", "N/A")))
            self.table.setItem(r, 1, QTableWidgetItem(p.get("birthdate", "N/A")))
            self.table.setItem(r, 2, QTableWidgetItem(p.get("gender", "N/A")))
            age = compute_age(p.get("birthdate", ""))
            self.table.setItem(r, 3, QTableWidgetItem(str(age)))
            self.table.setItem(r, 4, QTableWidgetItem(p.get("condition", "N/A")))  #new field for patient's medical condition 
            
            self.table.setItem(r, 5, QTableWidgetItem(p.get("email", "N/A")))
            self.table.setItem(r, 6, QTableWidgetItem(p.get("address", "N/A")))
            self.table.item(r, 0).setData(Qt.ItemDataRole.UserRole, p.get("username"))

    def _selected_patient(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Please select a patient first.")
            return None
        username = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return patients_map.get(username)            # HashMap O(1)

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
                patients_map.pop(pat["username"], None)   # HashMap O(1)
                save_data()
                self._refresh()


class AppointmentsPanel(QWidget):
    """
    Appointments view.
    - Patients: only their own appointments.
    - Doctors: only their own schedule.
    - Admin: all appointments.
    - Sorted by priority (MinHeap.snapshot()) then by date (insertion sort in DateAppointmentMap).
    """

    def __init__(self, role="admin", patient_data=None, doctor_data=None):
        super().__init__()
        self.role         = role
        self.patient_data = patient_data
        self.doctor_data  = doctor_data
        self._get_filter  = lambda: "All"
        self._appt_refs   = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(make_header("Appointments", "View and manage appointments"))

        top = QHBoxLayout()
        if self.role == "patient":
            book_btn = QPushButton("+ Book Appointment")
            book_btn.clicked.connect(self._book)
            top.addWidget(book_btn)
        if self.role == "admin":
            book_btn = QPushButton("+ Add Appointment")
            book_btn.clicked.connect(self._book_admin)
            top.addWidget(book_btn)
        if self.role in ("doctor", "admin"):
            # ── Serve Next: pops the highest-priority pending appointment
            # from today's MinHeap — this is where pop_next() is called,
            # making the priority queue serve its true dispatch purpose.
            serve_btn = QPushButton("🔔  Serve Next Patient")
            serve_btn.setObjectName("success")
            serve_btn.setToolTip(
                "Pops the highest-priority pending appointment for today "
                "(Urgent first, then earliest time) from the MinHeap and "
                "marks it In-Progress."
            )
            serve_btn.clicked.connect(self._serve_next)
            top.addWidget(serve_btn)
        top.addStretch()
        layout.addLayout(top)

        filter_bar, self._get_filter = make_filter_bar(self._refresh)
        layout.addWidget(filter_bar)

        cols = ["Date", "Time", "Patient", "Doctor", "Priority", "Status"]
        if self.role in ("doctor", "admin"):
            cols.extend(["Edit", "Complete"])
        self.table = styled_table(cols)
        self._appt_refs = []
        layout.addWidget(self.table)
        self._refresh()

    def _refresh(self):
        self.table.setRowCount(0)
        self._appt_refs = []
        status_filter = self._get_filter()

        # DateAppointmentMap.sorted_dates() uses insertion sort → O(d log d)
        for date_str in appointments_by_date.sorted_dates():
            heap = appointments_by_date.get_heap(date_str)

            # MinHeap.snapshot() returns sorted copy without mutating O(n log n)
            for rank, time_val, appt in heap.snapshot():

                # ── Role filtering ─────────────────────────────────────
                if self.role == "patient":
                    if (appt.get("patient_username") != self.patient_data.get("username")
                            and appt.get("patient") != self.patient_data.get("name")):
                        continue

                if self.role == "doctor":
                    doc_label = (f"Dr. {self.doctor_data['name']} — "
                                 f"{self.doctor_data['specialization']}")
                    if appt.get("doctor", "") != doc_label:
                        continue

                # ── Status filtering ───────────────────────────────────
                if status_filter != "All" and appt.get("status", "Pending") != status_filter:
                    continue

                r = self.table.rowCount()
                self.table.insertRow(r)
                self._appt_refs.append(appt)

                self.table.setItem(r, 0, QTableWidgetItem(date_str))
                self.table.setItem(r, 1, QTableWidgetItem(appt.get("time_disp", "")))
                self.table.setItem(r, 2, QTableWidgetItem(appt.get("patient", "")))
                self.table.setItem(r, 3, QTableWidgetItem(appt.get("doctor",  "")))

                priority   = appt.get("priority", "Normal")
                pri_item   = QTableWidgetItem("🚨 Urgent" if priority == "Urgent" else "Normal")
                if priority == "Urgent":
                    pri_item.setForeground(QColor(DANGER))
                    pri_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table.setItem(r, 4, pri_item)

                status      = appt.get("status", "Pending")
                status_item = QTableWidgetItem(status)
                if status == "Completed":
                    status_item.setForeground(QColor(SUCCESS))
                    status_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                elif status == "Pending":
                    status_item.setForeground(QColor(ACCENT))
                elif status == "In-Progress":
                    status_item.setForeground(QColor(WARNING))
                    status_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                elif status == "Cancelled":
                    status_item.setForeground(QColor(DANGER))
                self.table.setItem(r, 5, status_item)

                if self.role in ("doctor", "admin"):
                    # Edit button in column 6
                    edit_btn = QPushButton("Edit")
                    edit_btn.setFixedHeight(28)
                    edit_btn.setMinimumWidth(60)
                    
                    edit_btn.setStyleSheet(
                        f"background:{ACCENT};color:{DARK_TEXT};border-radius:2px;"
                        f"padding:4px 12px;font-size:11px;font-weight:600;"
                        f"text-align:center;")
                        
                    edit_btn.clicked.connect(lambda checked, a=appt: self._edit_appt(a))
                    self.table.setCellWidget(r, 6, edit_btn)

                    # Done button in column 7 (only for Pending status)
                    if status == "Pending":
                        done_btn = QPushButton("Done")
                        done_btn.setFixedHeight(28)
                        done_btn.setMinimumWidth(60)
                        
                        done_btn.setStyleSheet(
                            f"background:{SUCCESS};color:white;border-radius:2px;"
                            f"padding:4px 12px;font-size:11px;font-weight:600;"
                            f"text-align:center;")
                          
                        done_btn.clicked.connect(lambda checked, a=appt: self._quick_complete(a))
                        self.table.setCellWidget(r, 7, done_btn)

                    self.table.setRowHeight(r, 40)

    def _edit_appt(self, appt):
        dlg = AppointmentEditDialog(self, appt, self.role)
        if dlg.exec():
            self._refresh()

    def _quick_complete(self, appt):
        appt["status"] = "Completed"
        save_data()
        self._refresh()
        QMessageBox.information(self, "Updated", "Appointment marked as Completed.")

    def _book(self):
        dlg = AppointmentDialog(self, self.patient_data, role="patient")
        if dlg.exec():
            self._refresh()

    def _book_admin(self):
        dlg = AppointmentDialog(self, None, role="admin")
        if dlg.exec():
            self._refresh()

    def _serve_next(self):
        """
        MinHeap dispatch — pop the highest-priority PENDING appointment for today.

        This is the concrete use of MinHeap.pop_next():
          - Rank 0 (Urgent) is always served before Rank 1 (Normal).
          - Within the same rank, the earlier time_val wins (FCFS).
        The popped appointment is marked 'In-Progress' so staff know
        which patient to call next.  This demonstrates the priority queue
        fulfilling its dispatch purpose, not merely sorting for display.
        """
        today = date.today().strftime("%Y-%m-%d")

        # Find the nearest date that has pending appointments
        # (today first, then the next future date)
        target_date = None
        for d in appointments_by_date.sorted_dates():
            if d >= today:
                heap = appointments_by_date.get_heap(d)
                # Check if any pending appt belongs to this doctor (if doctor role)
                for _, _, appt in heap:
                    if appt.get("status") == "Pending":
                        if self.role == "doctor":
                            doc_label = (f"Dr. {self.doctor_data['name']} — "
                                         f"{self.doctor_data['specialization']}")
                            if appt.get("doctor") != doc_label:
                                continue
                        target_date = d
                        break
                if target_date:
                    break

        if not target_date:
            QMessageBox.information(self, "Queue Empty",
                "No pending appointments found.")
            return

        heap = appointments_by_date.get_heap(target_date)

        # ── MinHeap.pop_next() — O(log n) priority dispatch ─────────────
        # Pop entries until we find a Pending one that matches role filter.
        # Non-matching pops are pushed back so the heap is not corrupted.
        popped_back = []
        served = None
        while len(heap) > 0:
            rank, time_val, appt = appointments_by_date.pop_next(target_date)
            if appt.get("status") != "Pending":
                popped_back.append((rank, time_val, appt))
                continue
            if self.role == "doctor":
                doc_label = (f"Dr. {self.doctor_data['name']} — "
                             f"{self.doctor_data['specialization']}")
                if appt.get("doctor") != doc_label:
                    popped_back.append((rank, time_val, appt))
                    continue
            # Found the next patient to serve
            appt["status"] = "In-Progress"
            served = appt
            # Push back with updated appt (now In-Progress)
            appointments_by_date.push(target_date, rank, time_val, appt)
            break

        # Restore anything we skipped
        for rank, time_val, appt in popped_back:
            appointments_by_date.push(target_date, rank, time_val, appt)

        if not served:
            QMessageBox.information(self, "Queue Empty",
                "No pending appointments found.")
            return

        save_data()
        self._refresh()
        QMessageBox.information(
            self, "Serving Next Patient",
            f"🔔  Now Serving:\n\n"
            f"  Patient : {served.get('patient', '—')}\n"
            f"  Doctor  : {served.get('doctor', '—')}\n"
            f"  Date    : {served.get('date', '—')}\n"
            f"  Time    : {served.get('time_disp', '—')}\n"
            f"  Priority: {'🚨 Urgent' if served.get('priority') == 'Urgent' else 'Normal'}\n\n"
            f"Status set to In-Progress."
        )


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
        uname_lbl = QLabel(f"@{self.patient_data.get('username', '')}")
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
            ("  Date of Birth", self.patient_data.get("birthdate", "—")),
            ("  Gender",        self.patient_data.get("gender",    "—")),
            ("  Age",           f"{compute_age(self.patient_data.get('birthdate',''))} years old"),
            ("  Email",         self.patient_data.get("email",     "—")),
            ("  Address",       self.patient_data.get("address",   "—")),
            (" Username",      self.patient_data.get("username",  "—")),
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
                f"color:{MUTED};font-size:11px;font-weight:700;letter-spacing:0.5px;")
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
#  DOCTORS DIRECTORY PANEL  (read-only for patients)
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

        q        = self.search.text().lower()
        filtered = [
            d for d in doctors_map.values()          # HashMap.values()
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
            QFrame:hover {{ border-color: {SECONDARY}; }}
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
        days_lbl = QLabel(f"  {doc.get('schedule','—')}")
        days_lbl.setStyleSheet(f"color:{DARK_TEXT};font-size:13px;font-weight:600;")
        days_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        hours_lbl = QLabel(f"  {doc.get('start_time','—')} – {doc.get('end_time','—')}")
        hours_lbl.setStyleSheet(f"color:{MUTED};font-size:12px;")
        hours_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        sched_block.addWidget(days_lbl)
        sched_block.addWidget(hours_lbl)
        row.addLayout(sched_block)
        return card


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

        topbar = QWidget()
        topbar.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {PRIMARY}, stop:1 {SECONDARY});
                border-bottom: 2px solid {SECONDARY};
            }}
        """)
        topbar.setFixedHeight(70)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(24, 0, 24, 0)

        logo     = QLabel("🏥  ClinicSys")
        logo.setStyleSheet("color:white;font-size:22px;font-weight:800;letter-spacing:1px;")
        role_lbl = QLabel("Logged in as: Admin")
        role_lbl.setStyleSheet("color:#c0f0f5;font-size:13px;font-weight:500;")
        logout_btn = QPushButton(" Log Out")
        logout_btn.setStyleSheet(
            f"background:{DANGER};color:white;border-radius:6px;padding:8px 16px;font-weight:600;border:none;")
        logout_btn.clicked.connect(self._logout)

        tb_layout.addWidget(logo)
        tb_layout.addStretch()
        tb_layout.addWidget(role_lbl)
        tb_layout.addSpacing(16)
        tb_layout.addWidget(logout_btn)
        main_layout.addWidget(topbar)

        workspace_container = QWidget()
        workspace_layout    = QHBoxLayout(workspace_container)
        workspace_layout.setContentsMargins(16, 16, 16, 16)
        workspace_layout.setSpacing(16)

        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            f"background: white; border-radius: 8px; border: 1.5px solid {BORDER};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(12)

        sidebar_title = QLabel("SYSTEM CONTROLS")
        sidebar_title.setStyleSheet(f"font-weight: 700; color: {PRIMARY}; border: none; font-size: 12px; letter-spacing: 0.5px;")

        load_btn = QPushButton("   Load Data")
        load_btn.setFixedHeight(40)
        load_btn.setStyleSheet(f"background: #e3f2fd; color: {PRIMARY}; border-radius: 6px; font-weight: 600;")
        load_btn.clicked.connect(self._handle_load_data)
       
        
        reset_btn = QPushButton("  Reset Data")
        reset_btn.setFixedHeight(40)
        reset_btn.setStyleSheet(f"background: #ffebee; color: {DANGER}; border-radius: 6px; font-weight: 600;")
        reset_btn.clicked.connect(self._handle_reset_data)

        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(load_btn)
        sidebar_layout.addWidget(reset_btn)
        sidebar_layout.addStretch()

        self.doc_panel = DoctorsPanel()
        self.pat_panel = PatientsPanel()
        self.app_panel = AppointmentsPanel(role="admin")
        self.dashboard_panel = DashboardPanel()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.dashboard_panel, "  Dashboard")
        self.tabs.addTab(self.doc_panel, "   Doctors")
        self.tabs.addTab(self.pat_panel, "   Patients")
        self.tabs.addTab(self.app_panel, "   Appointments")

        workspace_layout.addWidget(sidebar)
        workspace_layout.addWidget(self.tabs)
        main_layout.addWidget(workspace_container)

    def _handle_load_data(self):
        try:
            if load_data():
                self.dashboard_panel._refresh_recent_appointments()
                self.doc_panel._refresh()
                self.pat_panel._refresh()
                self.app_panel._refresh()
                QMessageBox.information(self, "Success", "Data loaded successfully.")
            else:
                seed_demo()
                QMessageBox.warning(self, "Notice", "No data file found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def _handle_reset_data(self):
        reply = QMessageBox.question(self, "Confirm", "Reset all data?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 1. Clear ALL global data structures
            doctors_map.clear()
            doctors_bst.clear() # <-- ADD THIS line to prevent ghost data in the BST
            patients_map.clear()
            appointments_by_date.clear()
            occupied_slots.clear()
            
            # 2. Wipe the file off disk
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
                
            # 3. Refresh UI panels to blank state
            self.dashboard_panel._refresh_recent_appointments()
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
        topbar.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {PRIMARY}, stop:1 {SECONDARY});
                border-bottom: 2px solid {SECONDARY};
            }}
        """)
        topbar.setFixedHeight(70)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(24, 0, 24, 0)

        logo     = QLabel("🏥  ClinicSys")
        logo.setStyleSheet("color:white;font-size:22px;font-weight:800;letter-spacing:1px;")
        role_lbl = QLabel(
            f"👨‍⚕️  Dr. {self.doctor_data['name']}  |  {self.doctor_data['specialization']}")
        role_lbl.setStyleSheet("color:#c0f0f5;font-size:13px;font-weight:500;")
        logout_btn = QPushButton("🚪  Log Out")
        logout_btn.setStyleSheet(
            f"background:{DANGER};color:white;border-radius:6px;padding:8px 16px;font-weight:600;border:none;")
        logout_btn.clicked.connect(self._logout)

        tb_layout.addWidget(logo)
        tb_layout.addStretch()
        tb_layout.addWidget(role_lbl)
        tb_layout.addSpacing(16)
        tb_layout.addWidget(logout_btn)
        main_layout.addWidget(topbar)

        tabs    = QTabWidget()
        content = QWidget()
        cl      = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.addWidget(tabs)
        main_layout.addWidget(content)

        tabs.addTab(PatientsPanel(read_only=True), "🧑  Patient Records")
        tabs.addTab(
            AppointmentsPanel(role="doctor", doctor_data=self.doctor_data),
            "📅  My Schedule")

    def _logout(self):
        self.logout_requested.emit()
        self.close()


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
        topbar.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {PRIMARY}, stop:1 {SECONDARY});
                border-bottom: 2px solid {SECONDARY};
            }}
        """)
        topbar.setFixedHeight(70)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(24, 0, 24, 0)

        logo     = QLabel("🏥  ClinicSys")
        logo.setStyleSheet("color:white;font-size:22px;font-weight:800;letter-spacing:1px;")
        role_lbl = QLabel(f"👤  {self.patient_data['name']}")
        role_lbl.setStyleSheet("color:#c0f0f5;font-size:13px;font-weight:500;")
        logout_btn = QPushButton("🚪  Log Out")
        logout_btn.setStyleSheet(
            f"background:{DANGER};color:white;border-radius:6px;padding:8px 16px;font-weight:600;border:none;")
        logout_btn.clicked.connect(self._logout)

        tb_layout.addWidget(logo)
        tb_layout.addStretch()
        tb_layout.addWidget(role_lbl)
        tb_layout.addSpacing(16)
        tb_layout.addWidget(logout_btn)
        main_layout.addWidget(topbar)

        tabs    = QTabWidget()
        content = QWidget()
        cl      = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.addWidget(tabs)
        main_layout.addWidget(content)

        tabs.addTab(MyProfilePanel(self.patient_data),   "👤  My Profile")
        tabs.addTab(
            AppointmentsPanel(role="patient", patient_data=self.patient_data),
            "📅  My Appointments")
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
            f"stop:0 {PRIMARY},stop:1 {SECONDARY});")
        banner.setFixedHeight(180)
        b_layout = QVBoxLayout(banner)
        b_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl  = QLabel("🏥")
        icon_lbl.setStyleSheet("font-size:52px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl = QLabel("ClinicSys")
        title_lbl.setStyleSheet(
            "color:white;font-size:32px;font-weight:900;letter-spacing:3px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl   = QLabel("Clinic Appointment Management System")
        sub_lbl.setStyleSheet("color:#c0f0f5;font-size:13px;font-weight:500;")
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
                border: 1.5px solid {BORDER};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 32, 36, 32)
        card_layout.setSpacing(16)

        welcome = QLabel("Welcome Back")
        welcome.setStyleSheet(f"font-size:22px;font-weight:800;color:{PRIMARY};letter-spacing:0.5px;")
        card_layout.addWidget(welcome)
        hint = QLabel("Please sign in to your account")
        hint.setStyleSheet(f"color:{MUTED};font-size:12px;margin-bottom:8px;font-weight:500;")
        card_layout.addWidget(hint)

        u_lbl = QLabel("Username")
        u_lbl.setStyleSheet(f"font-weight:700;font-size:13px;color:{DARK_TEXT};letter-spacing:0.3px;")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        self.username_edit.setFixedHeight(35)
        card_layout.addWidget(u_lbl)
        card_layout.addWidget(self.username_edit)

        p_lbl = QLabel("Password")
        p_lbl.setStyleSheet(f"font-weight:700;font-size:13px;color:{DARK_TEXT};letter-spacing:0.3px;margin-top:6px;")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setFixedHeight(35)
        self.password_edit.returnPressed.connect(self._login)
        card_layout.addWidget(p_lbl)
        card_layout.addWidget(self.password_edit)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet(f"color:{DANGER};font-size:12px;font-weight:600;margin-top:4px;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.error_lbl)

        login_btn = QPushButton("Sign In")
        login_btn.setFixedHeight(46)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY};
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.5px;
                margin-bottom: 10px;
            }}
            QPushButton:hover {{ background: {SECONDARY}; }}
        """)
        login_btn.clicked.connect(self._login)
        card_layout.addWidget(login_btn)

        outer.addSpacing(20)
        outer.addWidget(card)
        outer.addStretch()

       

    def _login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            self.error_lbl.setText("Please enter both username and password.")
            return

        user = find_user(username, password)     # HashMap O(1) lookup
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
    doctors_map["dr_santos"] = doc1     # HashMap O(1)
    doctors_map["dr_reyes"]  = doc2
    doctors_bst.insert(doc1)            # BST O(log n) — maintains sorted order
    doctors_bst.insert(doc2)

    p1 = {
        "name": "Ana Garcia", "birthdate": "1990-05-15",
        "gender": "Female", "age": compute_age("1990-05-15"),
        "email": "ana.garcia@email.com", "address": "123 Rizal St, CDO",
        "condition": "Hypertension", "notes": "BP monitoring, Annual physical",
        "username": "ana.garcia", "password": "1234"
    }
    p2 = {
        "name": "Pedro Lim", "birthdate": "1985-11-20",
        "gender": "Male", "age": compute_age("1985-11-20"),
        "email": "pedro.lim@email.com", "address": "456 Maharlika Ave, CDO",
        "condition": "Diabetes", "notes": "Lab results, Patient request",
        "username": "pedro.lim", "password": "1234"
    }
    patients_map["ana.garcia"] = p1     # HashMap O(1)
    patients_map["pedro.lim"]  = p2

    date_key = "2026-05-20"
    appt1 = {
        "time_val": "10:00", "time_disp": "10:00 AM",
        "patient": "Ana Garcia", "patient_username": "ana.garcia",
        "doctor": "Dr. Maria Santos — General Medicine",
        "doctor_username": "dr_santos",
        "status": "Pending", "priority": "Normal", "date": date_key,
    }
    appt2 = {
        "time_val": "11:00", "time_disp": "11:00 AM",
        "patient": "Pedro Lim", "patient_username": "pedro.lim",
        "doctor": "Dr. Maria Santos — General Medicine",
        "doctor_username": "dr_santos",
        "status": "Pending", "priority": "Urgent", "date": date_key,
    }

    # MinHeap push O(log n)
    appointments_by_date.push(date_key, 1, "10:00", appt1)   # Normal → rank 1
    appointments_by_date.push(date_key, 0, "11:00", appt2)   # Urgent → rank 0

    # HashSet add O(1)
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
