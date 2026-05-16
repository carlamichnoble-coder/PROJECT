import sys
from datetime import date, datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QMessageBox, QComboBox, QDateEdit,
    QTimeEdit, QTabWidget, QFrame, QHeaderView, QScrollArea,
    QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QColor

# ─────────────────────────────────────────────
#  DATA STORE  (simple in-memory lists)
# ─────────────────────────────────────────────
doctors = []
patients = []
appointments = []

# ─────────────────────────────────────────────
#  BUILT-IN ADMIN ACCOUNT
# ─────────────────────────────────────────────
admin_user = {"username": "admin", "password": "admin123", "role": "admin"}

# ══════════════════════════════════════════════
#  STYLE CONSTANTS
# ══════════════════════════════════════════════
PRIMARY   = "#1a6b5a"   # deep teal
SECONDARY = "#27ae8f"   # medium teal
ACCENT    = "#f0a500"   # amber
LIGHT_BG  = "#f4f9f7"
DARK_TEXT = "#1c2b27"
MUTED     = "#7fa99b"
DANGER    = "#c0392b"
SUCCESS   = "#27ae60"
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
"""

# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

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


def find_user(username: str, password: str):
    if username == admin_user["username"] and password == admin_user["password"]:
        return admin_user
    for d in doctors:
        if d["username"] == username and d["password"] == password:
            return {"username": username, "password": password, "role": "doctor", "data": d}
    for p in patients:
        if p["username"] == username and p["password"] == password:
            return {"username": username, "password": password, "role": "patient", "data": p}
    return None

# ══════════════════════════════════════════════
#  SHARED WIDGETS
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


def styled_table(cols: list[str]) -> QTableWidget:
    t = QTableWidget()
    t.setColumnCount(len(cols))
    t.setHorizontalHeaderLabels(cols)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.setStyleSheet(t.styleSheet() + "QTableWidget {alternate-background-color: #eaf5f0;}")
    return t

# ══════════════════════════════════════════════
#  DOCTOR DIALOGS
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
            self.name_edit.setText(self.doctor.get("name",""))
            self.spec_edit.setText(self.doctor.get("specialization",""))
            idx = self.sched_combo.findText(self.doctor.get("schedule",""))
            if idx >= 0:
                self.sched_combo.setCurrentIndex(idx)
            st = QTime.fromString(self.doctor.get("start_time","08:00"), "HH:mm")
            et = QTime.fromString(self.doctor.get("end_time","17:00"), "HH:mm")
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
        if self.doctor is None:
            last = name.split()[-1]
            uname, pwd = make_doctor_credentials(last)
            new_doc = {
                "name": name, "specialization": spec,
                "schedule": self.sched_combo.currentText(),
                "start_time": st, "end_time": et,
                "username": uname, "password": pwd
            }
            doctors.append(new_doc)
            QMessageBox.information(self, "Doctor Added",
                f"Doctor added!\n\nLogin credentials:\nUsername: {uname}\nPassword: doc123")
        else:
            self.doctor["name"] = name
            self.doctor["specialization"] = spec
            self.doctor["schedule"] = self.sched_combo.currentText()
            self.doctor["start_time"] = st
            self.doctor["end_time"] = et
        self.accept()

# ══════════════════════════════════════════════
#  PATIENT DIALOGS
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
            self.name_edit.setText(self.patient.get("name",""))
            bd = QDate.fromString(self.patient.get("birthdate","2000-01-01"), "yyyy-MM-dd")
            self.bdate_edit.setDate(bd)
            idx = self.gender_combo.findText(self.patient.get("gender","Male"))
            if idx >= 0: self.gender_combo.setCurrentIndex(idx)
            self.email_edit.setText(self.patient.get("email",""))
            self.address_edit.setPlainText(self.patient.get("address",""))

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
        if self.patient is None:
            uname, pwd = make_patient_credentials(name)
            new_p = {
                "name": name, "birthdate": bd,
                "gender": self.gender_combo.currentText(),
                "age": age, "email": email, "address": address,
                "username": uname, "password": pwd
            }
            patients.append(new_p)
            QMessageBox.information(self, "Patient Added",
                f"Patient added!\n\nLogin credentials:\nUsername: {uname}\nPassword: 1234")
        else:
            self.patient["name"] = name
            self.patient["birthdate"] = bd
            self.patient["gender"] = self.gender_combo.currentText()
            self.patient["age"] = age
            self.patient["email"] = email
            self.patient["address"] = address
        self.accept()

# ══════════════════════════════════════════════
#  APPOINTMENT DIALOG
# ══════════════════════════════════════════════

class AppointmentDialog(QDialog):
    def __init__(self, parent=None, patient_data=None):
        super().__init__(parent)
        self.setWindowTitle("Book Appointment")
        self.setMinimumWidth(440)
        self.setStyleSheet(BASE_STYLE)
        self.patient_data = patient_data  # pre-fill if patient user
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
        for p in patients:
            self.patient_combo.addItem(p["name"])

        self.doctor_combo = QComboBox()
        for d in doctors:
            self.doctor_combo.addItem(f"Dr. {d['name']} — {d['specialization']}")

        form.addRow("Date *", self.date_edit)
        form.addRow("Time *", self.time_edit)
        form.addRow("Patient *", self.patient_combo)
        form.addRow("Doctor *", self.doctor_combo)
        layout.addLayout(form)

        # If patient user, lock patient field
        if self.patient_data:
            idx = self.patient_combo.findText(self.patient_data["name"])
            if idx >= 0:
                self.patient_combo.setCurrentIndex(idx)
            self.patient_combo.setEnabled(False)

        if not patients:
            QMessageBox.warning(self, "No Patients", "No patients registered yet.")
        if not doctors:
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
        if not patients or not doctors:
            QMessageBox.warning(self, "Error", "Need at least one doctor and one patient.")
            return
        appt = {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "time": self.time_edit.time().toString("hh:mm AP"),
            "patient": self.patient_combo.currentText(),
            "doctor": self.doctor_combo.currentText(),
            "status": "Pending"
        }
        appointments.append(appt)
        QMessageBox.information(self, "Booked", "Appointment booked successfully!")
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

        # Search + buttons
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
        q = self.search.text().lower() if hasattr(self, 'search') else ""
        self.table.setRowCount(0)
        for d in doctors:
            if q and q not in d["name"].lower() and q not in d["specialization"].lower():
                continue
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
        name = self.table.item(row, 0).text()
        for d in doctors:
            if d["name"] == name:
                return d
        return None

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
                doctors.remove(doc)
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

        add_btn = QPushButton("+ Add Patient")
        add_btn.clicked.connect(self._add)
        top.addWidget(add_btn)
        layout.addLayout(top)

        self.table = styled_table(["Name","Birthdate","Gender","Age","Email","Address"])
        layout.addWidget(self.table)

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
        q = self.search.text().lower() if hasattr(self, 'search') else ""
        self.table.setRowCount(0)
        for p in patients:
            if q and q not in p["name"].lower() and q not in p.get("email","").lower():
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(p["name"]))
            self.table.setItem(r, 1, QTableWidgetItem(p.get("birthdate","")))
            self.table.setItem(r, 2, QTableWidgetItem(p.get("gender","")))
            age = compute_age(p.get("birthdate",""))
            self.table.setItem(r, 3, QTableWidgetItem(str(age)))
            self.table.setItem(r, 4, QTableWidgetItem(p.get("email","")))
            self.table.setItem(r, 5, QTableWidgetItem(p.get("address","")))

    def _selected_patient(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Please select a patient first.")
            return None
        name = self.table.item(row, 0).text()
        for p in patients:
            if p["name"] == name:
                return p
        return None

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
                patients.remove(pat)
                self._refresh()


class AppointmentsPanel(QWidget):
    def __init__(self, role="admin", patient_data=None, doctor_data=None):
        super().__init__()
        self.role = role
        self.patient_data = patient_data
        self.doctor_data = doctor_data
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(make_header("Appointments", "View and manage appointments"))

        top = QHBoxLayout()
        if self.role == "patient":
            book_btn = QPushButton("+ Book Appointment")
            book_btn.clicked.connect(self._book)
            top.addStretch()
            top.addWidget(book_btn)
        layout.addLayout(top)

        cols = ["Date","Time","Patient","Doctor","Status"]
        if self.role == "doctor":
            cols.append("Action")
        self.table = styled_table(cols)
        layout.addWidget(self.table)

        self._refresh()

    def _refresh(self):
        self.table.setRowCount(0)
        for appt in appointments:
            if self.role == "patient" and appt["patient"] != self.patient_data["name"]:
                continue
            if self.role == "doctor":
                doc_label = f"Dr. {self.doctor_data['name']} — {self.doctor_data['specialization']}"
                if appt["doctor"] != doc_label:
                    continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(appt["date"]))
            self.table.setItem(r, 1, QTableWidgetItem(appt["time"]))
            self.table.setItem(r, 2, QTableWidgetItem(appt["patient"]))
            self.table.setItem(r, 3, QTableWidgetItem(appt["doctor"]))

            status_item = QTableWidgetItem(appt["status"])
            if appt["status"] == "Completed":
                status_item.setForeground(QColor(SUCCESS))
            elif appt["status"] == "Pending":
                status_item.setForeground(QColor(ACCENT))
            self.table.setItem(r, 4, status_item)

            if self.role == "doctor":
                if appt["status"] == "Pending":
                    btn = QPushButton("✔ Complete")
                    btn.setStyleSheet(f"background:{SUCCESS};color:white;border-radius:4px;padding:4px 10px;font-size:12px;")
                    btn.clicked.connect(lambda checked, a=appt: self._complete(a))
                    self.table.setCellWidget(r, 5, btn)
                else:
                    done = QLabel("  ✔ Done")
                    done.setStyleSheet(f"color:{SUCCESS};font-weight:700;")
                    self.table.setCellWidget(r, 5, done)

    def _complete(self, appt):
        appt["status"] = "Completed"
        self._refresh()
        QMessageBox.information(self, "Updated", "Appointment marked as Completed.")

    def _book(self):
        dlg = AppointmentDialog(self, self.patient_data)
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
        self.setMinimumSize(950, 650)
        self.setStyleSheet(BASE_STYLE)
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        topbar = QWidget()
        topbar.setStyleSheet(f"background:{PRIMARY};")
        topbar.setFixedHeight(60)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)
        logo = QLabel("🏥  ClinicSys")
        logo.setStyleSheet("color:white;font-size:20px;font-weight:700;")
        role_lbl = QLabel("Logged in as: Admin")
        role_lbl.setStyleSheet("color:#b2dfdb;font-size:13px;")
        logout_btn = QPushButton("⏏  Log Out")
        logout_btn.setStyleSheet("background:#ffffff22;color:white;border-radius:4px;padding:6px 16px;font-weight:600;")
        logout_btn.clicked.connect(self._logout)
        tb_layout.addWidget(logo)
        tb_layout.addStretch()
        tb_layout.addWidget(role_lbl)
        tb_layout.addSpacing(16)
        tb_layout.addWidget(logout_btn)
        main_layout.addWidget(topbar)

        # Tabs
        tabs = QTabWidget()
        tabs.setContentsMargins(16, 16, 16, 16)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.addWidget(tabs)
        main_layout.addWidget(content)

        tabs.addTab(DoctorsPanel(), "👨‍⚕️  Doctors")
        tabs.addTab(PatientsPanel(), "🧑  Patients")
        tabs.addTab(AppointmentsPanel(role="admin"), "📅  Appointments")

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
        role_lbl = QLabel(f"Dr. {self.doctor_data['name']}  |  {self.doctor_data['specialization']}")
        role_lbl.setStyleSheet("color:#b2dfdb;font-size:13px;")
        logout_btn = QPushButton("⏏  Log Out")
        logout_btn.setStyleSheet("background:#ffffff22;color:white;border-radius:4px;padding:6px 16px;font-weight:600;")
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

        tabs.addTab(PatientsPanel(), "🧑  Patients")
        tabs.addTab(AppointmentsPanel(role="doctor", doctor_data=self.doctor_data), "📅  My Appointments")

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

        # Avatar + name hero strip
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
        avatar.setStyleSheet(f"""
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

        # Info cards grid
        grid = QGridLayout()
        grid.setSpacing(12)

        fields = [
            ("🎂  Date of Birth", self.patient_data.get("birthdate", "—")),
            ("⚧  Gender",        self.patient_data.get("gender", "—")),
            ("🔢  Age",           f"{compute_age(self.patient_data.get('birthdate',''))} years old"),
            ("📧  Email",         self.patient_data.get("email", "—")),
            ("🏠  Address",       self.patient_data.get("address", "—")),
            ("👤  Username",      self.patient_data.get("username", "—")),
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
            lbl.setStyleSheet(f"color:{MUTED};font-size:11px;font-weight:700;letter-spacing:0.5px;")
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

        # Search bar
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search by name or specialization…")
        self.search.textChanged.connect(self._refresh)
        search_row.addWidget(self.search)
        layout.addLayout(search_row)

        # Scroll area holding doctor cards
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
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        q = self.search.text().lower()
        filtered = [
            d for d in doctors
            if not q or q in d["name"].lower() or q in d["specialization"].lower()
        ]

        if not filtered:
            empty = QLabel("No doctors found.")
            empty.setStyleSheet(f"color:{MUTED};font-size:14px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty)
            self.cards_layout.addStretch()
            return

        for doc in filtered:
            card = self._make_doctor_card(doc)
            self.cards_layout.addWidget(card)

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

        # Avatar circle
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

        # Name + specialization
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

        # Schedule block
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
#  PATIENT WINDOW  (updated with 3 tabs)
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

        # ── Top bar ──
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

        # ── Tabs ──
        tabs = QTabWidget()
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.addWidget(tabs)
        main_layout.addWidget(content)

        tabs.addTab(MyProfilePanel(self.patient_data),                        "👤  My Profile")
        tabs.addTab(AppointmentsPanel(role="patient",
                                      patient_data=self.patient_data),        "📅  My Appointments")
        tabs.addTab(DoctorsDirectoryPanel(),                                   "👨‍⚕️  Our Doctors")

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
        self.setFixedSize(460, 540)
        self.setStyleSheet(BASE_STYLE)
        self._active_window = None
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)

        # Top banner
        banner = QWidget()
        banner.setStyleSheet(f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {PRIMARY},stop:1 {SECONDARY});")
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

        # Form card
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
        user = find_user(username, password)
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
    # Doctors
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
    doctors.extend([doc1, doc2])

    # Patients
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
    patients.extend([p1, p2])

    # Sample appointment
    appointments.append({
        "date": "2026-05-20", "time": "10:00 AM",
        "patient": "Ana Garcia",
        "doctor": "Dr. Maria Santos — General Medicine",
        "status": "Pending"
    })


# ══════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    seed_demo()
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())