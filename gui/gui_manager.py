# gui/gui_manager.py
import os
import sys
import logging
import shutil
import time
# import serial
import cv2
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QFormLayout, QWidget, QLineEdit, QPushButton,
                             QTextEdit, QTabWidget, QMessageBox, QLabel, QDateEdit, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QFileDialog, QAction, QProgressBar, QShortcut)
from PyQt5.QtCore import QDate, QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QTextDocument, QKeySequence
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

from config import IMAGE_FOLDER
from database.database_manager import (create_tables, add_contractor, add_employee, check_id_exists,
                                       get_all_employees, get_all_contractors, get_db_connection)
from face_recognition.face_recognition_manager import load_database, recognize_face, face_analysis_app, save_database
from video_capture.video_capture_thread import VideoCaptureThread
ipcam=0
# ipcam = "rtsp://admin:1234Admin@192.168.1.250:554/cam/realmonitor?channel=1&subtype=0"
# port = 'COM3'
# ser=serial.Serial(port=port, baudrate=9600, timeout=0.1)
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class FaceDatabaseManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.face_database = load_database()
        self.multi_face_popup = None

    def initUI(self):
        self.setWindowTitle('Face Embeddings Database Manager')
        self.setGeometry(100, 100, 800, 600)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.initTabs()
        self.createActions()
        self.apply_styles()
        logging.info("UI Initialized")

    def initTabs(self):
        tab_initializers = [
            self.initAddModifyTab, self.initDeleteTab, self.initViewTab, self.initContractorDetailsTab,
            self.initEmployeeDetailsTab, self.initViewTablesTab, self.initFaceRecognitionTab,
            self.initCheckInCheckOutTab, self.initViewDataTab, self.initFaceRecognitionTab2
        ]
        try:
            for init in tab_initializers:
                init()
            logging.info("Tabs Initialized")
        except Exception as e:
            logging.error(f"Error initializing tabs: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while initializing tabs.")

    def initAddModifyTab(self):
        add_modify_tab = QWidget()
        self.tabs.addTab(add_modify_tab, "Add/Modify")
        form_layout = QFormLayout()
        self.person_name_input = QLineEdit(self)
        self.person_name_input.setPlaceholderText("Enter the name of the Employee")
        form_layout.addRow("Employee Name:", self.person_name_input)
        button_layout = QVBoxLayout()
        self.add_button = QPushButton('Add new entries', self)
        self.add_button.clicked.connect(lambda: self.record_video("add"))
        self.update_button = QPushButton('Update existing entries', self)
        self.update_button.clicked.connect(lambda: self.record_video("update"))
        self.stop_button = QPushButton('Stop Recording', self)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_recording)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.stop_button)
        self.status_display = QTextEdit(self)
        self.status_display.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_display)
        add_modify_tab.setLayout(layout)

    def initDeleteTab(self):
        delete_tab = QWidget()
        self.tabs.addTab(delete_tab, "Delete")
        form_layout = QFormLayout()
        self.delete_person_name_input = QLineEdit(self)
        self.delete_person_name_input.setPlaceholderText("Enter the name of the Employee")
        form_layout.addRow("Employee Name:", self.delete_person_name_input)
        self.delete_button = QPushButton('Delete an entry', self)
        self.delete_button.clicked.connect(self.delete_entry)
        self.delete_status_display = QTextEdit(self)
        self.delete_status_display.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.delete_status_display)
        delete_tab.setLayout(layout)

    def initViewTab(self):
        view_tab = QWidget()
        self.tabs.addTab(view_tab, "View")
        self.view_button = QPushButton('View all entries', self)
        self.view_button.clicked.connect(self.view_database)
        self.view_status_display = QTextEdit(self)
        self.view_status_display.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.view_button)
        layout.addWidget(self.view_status_display)
        view_tab.setLayout(layout)

    def initContractorDetailsTab(self):
        contractor_tab = QWidget()
        self.tabs.addTab(contractor_tab, "Contractor Details")
        form_layout = QFormLayout()
        self.contractor_name_input = QLineEdit(self)
        self.contractor_name_input.setPlaceholderText("Enter the contractor name")
        self.contractor_name_input.setEnabled(False)
        form_layout.addRow("Contractor Name:", self.contractor_name_input)
        self.contractor_id_input = QLineEdit(self)
        self.contractor_id_input.setPlaceholderText("Enter the contractor ID")
        self.contractor_id_input.editingFinished.connect(self.check_contractor_id)
        form_layout.addRow("Contractor ID:", self.contractor_id_input)
        self.contractor_phone_input = QLineEdit(self)
        self.contractor_phone_input.setPlaceholderText("Enter the contractor phone")
        self.contractor_phone_input.setEnabled(False)
        form_layout.addRow("Contractor Phone:", self.contractor_phone_input)
        self.contractor_address_input = QTextEdit(self)
        self.contractor_address_input.setPlaceholderText("Enter the contractor address")
        self.contractor_address_input.setEnabled(False)
        form_layout.addRow("Contractor Address:", self.contractor_address_input)
        self.contractor_aadhaar_input = QLineEdit(self)
        self.contractor_aadhaar_input.setPlaceholderText("Enter the contractor Aadhaar ID")
        self.contractor_aadhaar_input.setEnabled(False)
        form_layout.addRow("Contractor Aadhaar ID:", self.contractor_aadhaar_input)
        self.save_contractor_button = QPushButton('Save Contractor Details', self)
        self.save_contractor_button.setEnabled(False)
        self.save_contractor_button.clicked.connect(self.save_contractor_details)
        self.contractor_status_display = QTextEdit(self)
        self.contractor_status_display.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.save_contractor_button)
        layout.addWidget(self.contractor_status_display)
        contractor_tab.setLayout(layout)

    def initEmployeeDetailsTab(self):
        employee_tab = QWidget()
        self.tabs.addTab(employee_tab, "Employee Details")
        form_layout = QFormLayout()
        self.employee_id_input = QLineEdit(self)
        self.employee_id_input.setPlaceholderText("Enter the employee ID")
        self.employee_id_input.editingFinished.connect(self.check_employee_id)
        form_layout.addRow("Employee ID:", self.employee_id_input)
        self.employee_name_input = QLineEdit(self)
        self.employee_name_input.setPlaceholderText("Enter the employee name")
        self.employee_name_input.setEnabled(False)
        form_layout.addRow("Employee Name:", self.employee_name_input)
        self.employee_phone_input = QLineEdit(self)
        self.employee_phone_input.setPlaceholderText("Enter the employee phone")
        self.employee_phone_input.setEnabled(False)
        form_layout.addRow("Employee Phone Number:", self.employee_phone_input)
        self.employee_aadhaar_input = QLineEdit(self)
        self.employee_aadhaar_input.setPlaceholderText("Enter the employee Aadhaar ID")
        self.employee_aadhaar_input.setEnabled(False)
        form_layout.addRow("Employee Aadhaar ID:", self.employee_aadhaar_input)
        self.employee_address_input = QTextEdit(self)
        self.employee_address_input.setPlaceholderText("Enter the employee address")
        self.employee_address_input.setEnabled(False)
        form_layout.addRow("Employee Address:", self.employee_address_input)
        self.contractor_id_input_for_employee = QLineEdit(self)
        self.contractor_id_input_for_employee.setPlaceholderText("Enter the contractor's ID")
        self.contractor_id_input_for_employee.setEnabled(False)
        form_layout.addRow("Contractor's ID:", self.contractor_id_input_for_employee)
        self.save_employee_button = QPushButton('Save Employee Details', self)
        self.save_employee_button.setEnabled(False)
        self.save_employee_button.clicked.connect(self.save_employee_details)
        self.capture_face_button = QPushButton('Capture Face Embedding', self)
        self.capture_face_button.setEnabled(False)
        self.capture_face_button.clicked.connect(self.capture_face_embedding)
        self.stop_employee_recording_button = QPushButton('Stop Recording', self)
        self.stop_employee_recording_button.setEnabled(False)
        self.stop_employee_recording_button.clicked.connect(self.stop_recording)
        self.employee_status_display = QTextEdit(self)
        self.employee_status_display.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.save_employee_button)
        layout.addWidget(self.capture_face_button)
        layout.addWidget(self.stop_employee_recording_button)
        layout.addWidget(self.employee_status_display)
        employee_tab.setLayout(layout)

    def initFaceRecognitionTab(self):
        recognition_tab = QWidget()
        self.tabs.addTab(recognition_tab, "Face Recognition")
        self.recognition_button = QPushButton('Start Recognition', self)
        self.recognition_button.clicked.connect(self.start_recognition)
        self.stop_recognition_button = QPushButton('Stop Recognition', self)
        self.stop_recognition_button.clicked.connect(self.stop_recognition)
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(1280, 720)
        self.video_label.setStyleSheet("background-color: black;")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        layout = QVBoxLayout()
        layout.addWidget(self.recognition_button)
        layout.addWidget(self.stop_recognition_button)
        layout.addWidget(self.video_label)
        layout.addWidget(self.progress_bar)
        recognition_tab.setLayout(layout)

    def initFaceRecognitionTab2(self):
        recognition_tab2 = QWidget()
        self.tabs.addTab(recognition_tab2, "Face Recognition 2")
        self.recognition_button2 = QPushButton('Start Recognition', self)
        self.recognition_button2.clicked.connect(self.start_recognition2)
        self.stop_recognition_button2 = QPushButton('Stop Recognition', self)
        self.stop_recognition_button2.clicked.connect(self.stop_recognition2)
        self.video_label2 = QLabel(self)
        self.video_label2.setFixedSize(1280, 720)
        self.video_label2.setStyleSheet("background-color: black;")
        self.progress_bar2 = QProgressBar(self)
        self.progress_bar2.setVisible(False)
        self.known_face_label = QLabel(self)
        self.unknown_face_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.recognition_button2)
        layout.addWidget(self.stop_recognition_button2)
        layout.addWidget(self.video_label2)
        layout.addWidget(self.progress_bar2)
        layout.addWidget(self.known_face_label)
        layout.addWidget(self.unknown_face_label)
        recognition_tab2.setLayout(layout)

    def update_image(self, label, image_path):
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)

    def initViewTablesTab(self):
        view_tables_tab = QWidget()
        self.tabs.addTab(view_tables_tab, "View Tables")
        self.view_employees_button = QPushButton('View Employees', self)
        self.view_employees_button.clicked.connect(self.view_employees)
        self.view_contractors_button = QPushButton('View Contractors', self)
        self.view_contractors_button.clicked.connect(self.view_contractors)
        self.employees_display = QTextEdit(self)
        self.employees_display.setReadOnly(True)
        self.contractors_display = QTextEdit(self)
        self.contractors_display.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.view_employees_button)
        layout.addWidget(self.employees_display)
        layout.addWidget(self.view_contractors_button)
        layout.addWidget(self.contractors_display)
        view_tables_tab.setLayout(layout)

    def initCheckInCheckOutTab(self):
        checkin_checkout_tab = QWidget()
        self.tabs.addTab(checkin_checkout_tab, "Check-In/Check-Out")
        self.checkin_button = QPushButton('Check In', self)
        self.checkin_button.clicked.connect(lambda: self.start_face_recognition("checkin"))
        self.checkout_button = QPushButton('Check Out', self)
        self.checkout_button.clicked.connect(lambda: self.start_face_recognition("checkout"))
        self.checkin_checkout_status_display = QTextEdit(self)
        self.checkin_checkout_status_display.setReadOnly(True)
        self.video_label_2 = QLabel(self)
        self.video_label_2.setFixedSize(1280, 720)
        self.video_label_2.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.addWidget(self.checkin_button)
        layout.addWidget(self.checkout_button)
        layout.addWidget(self.video_label_2)
        layout.addWidget(self.checkin_checkout_status_display)
        checkin_checkout_tab.setLayout(layout)

    def initViewDataTab(self):
        view_data_tab = QWidget()
        self.tabs.addTab(view_data_tab, "View Data")
        layout = QVBoxLayout()
        self.filter_layout = QHBoxLayout()
        self.filter_from_label = QLabel("From:")
        self.filter_from_date = QDateEdit()
        self.filter_from_date.setDate(QDate.currentDate().addMonths(-1))
        self.filter_from_date.setDisplayFormat("yyyy-MM-dd")
        self.filter_layout.addWidget(self.filter_from_label)
        self.filter_layout.addWidget(self.filter_from_date)
        self.filter_to_label = QLabel("To:")
        self.filter_to_date = QDateEdit()
        self.filter_to_date.setDate(QDate.currentDate())
        self.filter_to_date.setDisplayFormat("yyyy-MM-dd")
        self.filter_layout.addWidget(self.filter_to_label)
        self.filter_layout.addWidget(self.filter_to_date)
        self.filter_contractor_label = QLabel("Contractor Name:")
        self.filter_contractor_name = QLineEdit()
        self.filter_layout.addWidget(self.filter_contractor_label)
        self.filter_layout.addWidget(self.filter_contractor_name)
        self.filter_name_label = QLabel("Name:")
        self.filter_name = QLineEdit()
        self.filter_layout.addWidget(self.filter_name_label)
        self.filter_layout.addWidget(self.filter_name)
        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.filter_data)
        self.filter_layout.addWidget(self.filter_button)
        layout.addLayout(self.filter_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Date", "Time In", "Time Out"])
        layout.addWidget(self.table)
        self.graph_button = QPushButton("Generate Graph")
        self.graph_button.clicked.connect(self.generate_graph)
        layout.addWidget(self.graph_button)
        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        layout.addWidget(self.export_button)
        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print_data)
        layout.addWidget(self.print_button)
        view_data_tab.setLayout(layout)
        self.clear_table_button = QPushButton("Clear Check-In/Check-Out Table")
        self.clear_table_button.clicked.connect(self.clear_checkin_checkout_table)
        layout.addWidget(self.clear_table_button)

    def createActions(self):
        self.add_shortcut('Ctrl+Q', self.close)
        self.add_shortcut('Ctrl+V', self.view_database)
        self.add_shortcut('Ctrl+A', self.record_video, "add")
        self.add_shortcut('Ctrl+U', self.record_video, "update")
        self.add_shortcut('Ctrl+D', self.delete_entry)

    def add_shortcut(self, sequence, method, *args):
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.activated.connect(lambda: method(*args))

    def check_id(self, id_input, table, id_column, name_input, phone_input, address_input, aadhaar_input, button, status_display):
        id_value = id_input.text().strip()
        try:
            if not check_id_exists(table, id_column, id_value):
                name_input.setEnabled(True)
                phone_input.setEnabled(True)
                address_input.setEnabled(True)
                aadhaar_input.setEnabled(True)
                button.setEnabled(True)
                status_display.append(f"{id_column} exists. You can enter the details.")
            else:
                name_input.setEnabled(False)
                phone_input.setEnabled(False)
                address_input.setEnabled(False)
                aadhaar_input.setEnabled(False)
                button.setEnabled(False)
                status_display.append(f"{id_column} does not exist.")
            logging.info(f"Checked {id_column}: {id_value}")
        except Exception as e:
            logging.error(f"Error checking {id_column}: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while checking {id_column}.")

    def check_contractor_id(self):
        self.check_id(
            self.contractor_id_input, "contractors", "contractor_id",
            self.contractor_name_input, self.contractor_phone_input, self.contractor_address_input,
            self.contractor_aadhaar_input, self.save_contractor_button, self.contractor_status_display
        )

    def check_employee_id(self):
        self.check_id(
            self.employee_id_input, "employees", "employee_id",
            self.employee_name_input, self.employee_phone_input, self.employee_address_input,
            self.employee_aadhaar_input, self.save_employee_button, self.employee_status_display
        )

    def save_details(self, details, table, status_display):
        if not all(details.values()):
            self.show_error_message("Please fill in all details.")
            return
        try:
            if table == 'contractor':
                add_contractor(details)
            else:
                add_employee(details)
            status_display.append(f"Saved {table} details: {details}")
            logging.info(f"Saved {table} details: {details}")
        except Exception as e:
            logging.error(f"Error saving {table} details: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while saving {table} details.")

    def save_contractor_details(self):
        details = {
            'name': self.contractor_name_input.text().strip(),
            'id': self.contractor_id_input.text().strip(),
            'phone': self.contractor_phone_input.text().strip(),
            'address': self.contractor_address_input.toPlainText().strip(),
            'aadhaar': self.contractor_aadhaar_input.text().strip()
        }
        self.save_details(details, 'contractor', self.contractor_status_display)

    def save_employee_details(self):
        details = {
            'employee_id': self.employee_id_input.text().strip(),
            'name': self.employee_name_input.text().strip(),
            'phone': self.employee_phone_input.text().strip(),
            'aadhaar': self.employee_aadhaar_input.text().strip(),
            'address': self.employee_address_input.toPlainText().strip(),
            'contractor_id': self.contractor_id_input_for_employee.text().strip()
        }
        self.save_details(details, 'employee', self.employee_status_display)

    def capture_face_embedding(self):
        person_name = self.employee_name_input.text().strip()
        if not person_name:
            self.show_error_message("Please enter the employee name.")
            return
        self.record_video(person_name, "capture")

    def view_database(self):
        self.view_status_display.clear()
        try:
            database = load_database()
            if not database:
                self.view_status_display.append("No entries found in the database.")
            else:
                self.view_status_display.append("Database entries:")
                for person_name, embeddings in database.items():
                    self.view_status_display.append(f"{person_name}: {len(embeddings)} embeddings")
            logging.info("Viewed database entries")
        except Exception as e:
            logging.error(f"Error viewing database: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while viewing the database.")

    def view_employees(self):
        self.view_table(self.employees_display, get_all_employees, "employees")

    def view_contractors(self):
        self.view_table(self.contractors_display, get_all_contractors, "contractors")

    def view_table(self, display_widget, fetch_function, table_name):
        display_widget.clear()
        try:
            entries = fetch_function()
            if not entries:
                display_widget.append(f"No {table_name} found in the database.")
            else:
                display_widget.append(f"{table_name.capitalize()} in the database:")
                for entry in entries:
                    display_widget.append(str(entry))
            logging.info(f"Viewed {table_name}")
        except Exception as e:
            logging.error(f"Error viewing {table_name}: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while viewing {table_name}.")

    def add_entries(self):
        self.status_display.clear()
        self.record_video("add")

    def update_entries(self):
        self.status_display.clear()
        self.record_video("update")

    def delete_entry(self):
        self.delete_status_display.clear()
        person_name = self.delete_person_name_input.text().strip()
        if not person_name:
            self.show_error_message("Please enter a person name.")
            return
        self.delete_from_database(person_name)

    def delete_from_database(self, person_name):
        try:
            database = load_database()
            if person_name in database:
                del database[person_name]
                save_database(database)
                person_folder = os.path.join(IMAGE_FOLDER, person_name)
                if os.path.exists(person_folder):
                    shutil.rmtree(person_folder)
                self.delete_status_display.append(f"Deleted {person_name} from the database and removed their folder.")
                logging.info(f"Deleted {person_name} from the database")
            else:
                self.delete_status_display.append(f"{person_name} not found in the database.")
        except Exception as e:
            logging.error(f"Error deleting {person_name} from database: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while deleting {person_name} from the database.")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)
        logging.error(message)

    def record_video(self, action):
        person_name = self.person_name_input.text().strip()
        if not person_name:
            self.show_error_message("Please enter a person name.")
            return
        try:
            if not hasattr(self, 'capture_thread') or not self.capture_thread.isRunning():
                self.capture_thread = VideoCaptureThread(person_name)
                self.capture_thread.finished.connect(self.recording_finished)
                self.capture_thread.embeddingCaptured.connect(self.embedding_captured)
                self.capture_thread.start()
                self.stop_button.setEnabled(True)
                self.stop_employee_recording_button.setEnabled(True)
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
                self.status_display.append(f"Started {action} entries for {person_name}.")
                self.employee_status_display.append(f"Started {action} entries for {person_name}.")
                logging.info(f"Started {action} entries for {person_name}")
            else:
                self.status_display.append("A recording session is already in progress. Please stop it first.")
                self.employee_status_display.append("A recording session is already in progress. Please stop it first.")
        except Exception as e:
            logging.error(f"Error starting video recording: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while starting the video recording.")

    def stop_recording(self):
        try:
            if hasattr(self, 'capture_thread') and self.capture_thread.isRunning():
                self.capture_thread.stop()
                self.stop_button.setEnabled(False)
                self.stop_employee_recording_button.setEnabled(False)
                self.progress_bar.setVisible(False)
                self.status_display.append("Stopped recording session.")
                self.employee_status_display.append("Stopped recording session.")
                logging.info("Stopped recording session")
        except Exception as e:
            logging.error(f"Error stopping video recording: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while stopping the video recording.")

    def recording_finished(self, person_name, frame_count):
        self.status_display.append(f"Finished recording session for {person_name}. Saved {frame_count} embeddings.")
        self.employee_status_display.append(f"Finished recording session for {person_name}. Saved {frame_count} embeddings.")
        self.stop_button.setEnabled(False)
        self.stop_employee_recording_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        logging.info(f"Finished recording session for {person_name}. Saved {frame_count} embeddings.")

    def embedding_captured(self, embedding, cropped_face, frame_path):
        self.status_display.append(f"Captured embedding and saved cropped face to {frame_path}")
        self.employee_status_display.append(f"Captured embedding and saved cropped face to {frame_path}")
        logging.info(f"Captured embedding and saved cropped face to {frame_path}")

    def start_recognition(self):
        self.status_display.clear()
        try:
            if not hasattr(self, 'cap') or self.cap is None:
                self.face_database = load_database()
                self.cap = cv2.VideoCapture(ipcam)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.timer = QTimer()
                self.timer.timeout.connect(self.update_frame)
                self.timer.start(0)  # Reduce frame rate for recognition
                self.status_display.append("Started face recognition.")
                logging.info("Started face recognition")
            else:
                self.status_display.append("Face recognition is already running.")
        except Exception as e:
            logging.error(f"Error starting face recognition: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while starting face recognition.")

    def update_frame(self):
        self.update_frame_common(self.video_label, self.status_display)

    def start_recognition2(self):
        self.status_display.clear()
        try:
            if not hasattr(self, 'cap2') or self.cap2 is None:
                self.face_database = load_database()
                self.cap2 = cv2.VideoCapture(ipcam)
                self.cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.timer2 = QTimer()
                self.timer2.timeout.connect(self.update_frame2)
                self.timer2.start(0)  # Reduce frame rate for recognition
                self.status_display.append("Started face recognition.")
                logging.info("Started face recognition")
            else:
                self.status_display.append("Face recognition is already running.")
        except Exception as e:
            logging.error(f"Error starting face recognition: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while starting face recognition.")

    def update_frame2(self):
        self.update_frame_common2(self.video_label2, self.status_display)

    def update_frame_common(self, video_label, status_display):
        try:
            ret, frame = self.cap.read()
            if not ret:
                status_display.append("Failed to capture video frame.")
                logging.error("Failed to capture video frame.")
                return
            frame = cv2.resize(frame, (1280, 720))
            faces = face_analysis_app.get(frame)
            for face in faces:
                bbox = face.bbox.astype(int)
                embedding = face.normed_embedding
                identity, confidence = recognize_face(embedding, self.face_database)

                # labelling
                # label = f"{identity}" if identity != "Unknown" else f"Unknown"; ser.write(b'1') if identity != "Unknown" else ser.write(b'0')
                # label = f"{identity}" if identity != "Unknown" else f"Unknown"
                label = f"{identity} ({confidence:.2f})" if identity != "Unknown" else f"Unknown ({confidence:.2f})"

                color = (0, 255, 0) if identity != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                cv2.putText(frame, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            video_label.setPixmap(pixmap)
        except Exception as e:
            logging.error(f"Error updating frame: {e}")
            status_display.append("An error occurred while updating frame.")

    def update_frame_common2(self, video_label2, status_display):
        try:
            ret, frame = self.cap2.read()
            if not ret:
                status_display.append("Failed to capture video frame.")
                logging.error("Failed to capture video frame.")
                return
            frame = cv2.resize(frame, (1280, 720))
            faces = face_analysis_app.get(frame)
            if len(faces) != 1:
                if not self.multi_face_popup:
                    self.multi_face_popup = QMessageBox()
                    self.multi_face_popup.setIcon(QMessageBox.Warning)
                    self.multi_face_popup.setWindowTitle("Multiple Faces Detected")
                    self.multi_face_popup.setText("Multiple faces detected. Please ensure only one face is visible.")
                    self.multi_face_popup.setStandardButtons(QMessageBox.Ok)
                    self.multi_face_popup.setModal(True)
                    self.multi_face_popup.show()
                self.multi_face_popup.raise_()
            else:
                if self.multi_face_popup:
                    self.multi_face_popup.accept()
                    self.multi_face_popup = None
                face = faces[0]
                bbox = face.bbox.astype(int)
                embedding = face.normed_embedding
                identity, confidence = recognize_face(embedding, self.face_database)
                # label = f"{identity}" if identity != "Unknown" else f"Unknown"; ser.write(b'1') if identity != "Unknown" else ser.write(b'0')
                # label = f"{identity} ({confidence:.2f})" if identity != "Unknown" else f"Unknown ({confidence:.2f})"
                color = (0, 255, 0) if identity != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                cv2.putText(frame, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                if identity != "Unknown":
                    self.update_image(self.known_face_label, "01.jpg")
                else:
                    self.update_image(self.unknown_face_label, "11.jpg")
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            video_label2.setPixmap(pixmap)
        except Exception as e:
            logging.error(f"Error updating frame: {e}")
            status_display.append("An error occurred while updating frame.")

    def stop_recognition(self):
        self.stop_recognition_common(self.video_label, self.status_display)

    def stop_recognition2(self):
        self.stop_recognition_common2(self.video_label2, self.status_display)

    def stop_recognition_common(self, video_label, status_display):
        try:
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                self.cap = None
                self.timer.stop()
                video_label.clear()
                status_display.append("Face recognition stopped.")
                logging.info("Face recognition stopped")
            else:
                status_display.append("Face recognition is not running.")
        except Exception as e:
            logging.error(f"Error stopping face recognition: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while stopping face recognition.")

    def stop_recognition_common2(self, video_label2, status_display):
        try:
            if hasattr(self, 'cap2') and self.cap2 is not None:
                self.cap2.release()
                self.cap2 = None
                self.timer2.stop()
                video_label2.clear()
                status_display.append("Face recognition stopped.")
                logging.info("Face recognition stopped")
            else:
                status_display.append("Face recognition is not running.")
        except Exception as e:
            logging.error(f"Error stopping face recognition: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while stopping face recognition.")

    def check_in(self):
        self.start_face_recognition("checkin")

    def check_out(self):
        self.start_face_recognition("checkout")

    def start_face_recognition(self, action):
        self.checkin_checkout_status_display.clear()
        try:
            if not hasattr(self, 'cap') or self.cap is None:
                self.face_database = load_database()
                self.cap = cv2.VideoCapture(ipcam)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.timer = QTimer()
                self.timer.timeout.connect(lambda: self.update_frame_with_action(action))
                self.timer.start(0)  # Reduce frame rate for recognition
                self.checkin_checkout_status_display.append(f"Started face recognition for {action}.")
                logging.info(f"Started face recognition for {action}")
            else:
                self.checkin_checkout_status_display.append("Face recognition is already running.")
        except Exception as e:
            logging.error(f"Error starting face recognition for {action}: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while starting face recognition for {action}.")

    def update_frame_with_action(self, action):
        self.update_frame_common(self.video_label_2, self.checkin_checkout_status_display)
        self.handle_recognition_action(action)

    def handle_recognition_action(self, action):
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.checkin_checkout_status_display.append("Failed to capture video frame.")
                logging.error("Failed to capture video frame.")
                return
            frame = cv2.resize(frame, (1280, 720))
            faces = face_analysis_app.get(frame)
            for face in faces:
                bbox = face.bbox.astype(int)
                embedding = face.normed_embedding
                identity, confidence = recognize_face(embedding, self.face_database)
                # label = f"{identity}" if identity != "Unknown" else f"Unknown"; ser.write(b'1') if identity != "Unknown" else ser.write(b'0')
                label = f"{identity} ({confidence:.2f})" if identity != "Unknown" else f"Unknown ({confidence:.2f})"
                color = (0, 255, 0) if identity != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                cv2.putText(frame, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                if identity != "Unknown":
                    self.update_checkin_checkout(identity, action)
                    self.stop_face_recognition()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.video_label_2.setPixmap(pixmap)
        except Exception as e:
            logging.error(f"Error updating frame with action {action}: {e}")
            self.checkin_checkout_status_display.append("An error occurred while updating frame.")

    def update_checkin_checkout(self, employee_name, action):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                if action == "checkin":
                    c.execute('''INSERT INTO checkin_checkout (employee_name, checkin_time) VALUES (?, ?)''',
                              (employee_name, current_time))
                    self.checkin_checkout_status_display.append(f"{employee_name} checked in at {current_time}.")
                elif action == "checkout":
                    c.execute(
                        '''UPDATE checkin_checkout SET checkout_time = ? WHERE employee_name = ? AND checkout_time IS NULL''',
                        (current_time, employee_name))
                    self.checkin_checkout_status_display.append(f"{employee_name} checked out at {current_time}.")
                conn.commit()
                logging.info(f"{employee_name} {action} at {current_time}")
        except Exception as e:
            logging.error(f"Error updating checkin/checkout: {e}")
            self.checkin_checkout_status_display.append(f"An error occurred during {action}.")

    def stop_face_recognition(self):
        self.stop_recognition_common(self.video_label_2, self.checkin_checkout_status_display)

    def filter_data(self):
        from_date = self.filter_from_date.date().toString("yyyy-MM-dd")
        to_date = self.filter_to_date.date().toString("yyyy-MM-dd")
        contractor_name = self.filter_contractor_name.text()
        name = self.filter_name.text()
        query = "SELECT employee_name, date(checkin_time), time(checkin_time), time(checkout_time) FROM checkin_checkout WHERE date(checkin_time) BETWEEN ? AND ?"
        params = [from_date, to_date]
        if contractor_name:
            query += " AND employee_name IN (SELECT name FROM employees WHERE contractor_id = ?)"
            params.append(contractor_name)
        if name:
            query += " AND employee_name = ?"
            params.append(name)
        self.execute_query(query, params)

    def execute_query(self, query, params):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                data = cursor.fetchall()
            self.table.setRowCount(len(data))
            for row, (employee_name, date, time_in, time_out) in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(employee_name))
                self.table.setItem(row, 1, QTableWidgetItem(date))
                self.table.setItem(row, 2, QTableWidgetItem(time_in))
                self.table.setItem(row, 3, QTableWidgetItem(time_out))
            logging.info(f"Filtered data with params: {params}")
        except Exception as e:
            logging.error(f"Error filtering data: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while filtering data.")

    def generate_graph(self):
        from_date = self.filter_from_date.date().toString("yyyy-MM-dd")
        to_date = self.filter_to_date.date().toString("yyyy-MM-dd")
        self.execute_graph_query("SELECT date(checkin_time) FROM checkin_checkout WHERE date(checkin_time) BETWEEN ? AND ?", [from_date, to_date])

    def execute_graph_query(self, query, params):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                data = cursor.fetchall()
            if data:
                df = pd.DataFrame(data, columns=["Date"])
                date_counts = df['Date'].value_counts().sort_index()
                date_counts.plot(kind='bar', color='#4CAF50')
                plt.xlabel('Date')
                plt.ylabel('Number of Entries')
                plt.title('Employee Entries per Date')
                plt.show()
                logging.info("Generated graph for employee entries per date")
            else:
                QMessageBox.information(self, "No Data", "No data available for the selected date range.")
                logging.info("No data available for generating graph")
        except Exception as e:
            logging.error(f"Error generating graph: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while generating graph.")

    def export_to_csv(self):
        from_date = self.filter_from_date.date().toString("yyyy-MM-dd")
        to_date = self.filter_to_date.date().toString("yyyy-MM-dd")
        self.execute_export_query("SELECT employee_name, date(checkin_time), time(checkin_time), time(checkout_time) FROM checkin_checkout WHERE date(checkin_time) BETWEEN ? AND ?", [from_date, to_date])

    def execute_export_query(self, query, params):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                data = cursor.fetchall()
            if data:
                df = pd.DataFrame(data, columns=["Name", "Date", "Time In", "Time Out"])
                file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
                if file_path:
                    df.to_csv(file_path, index=False)
                    QMessageBox.information(self, "Success", "Data exported successfully!")
                    logging.info(f"Data exported to {file_path}")
            else:
                QMessageBox.warning(self, "No Data", "No data available for the selected date range.")
                logging.info("No data available for export to CSV")
        except Exception as e:
            logging.error(f"Error exporting data to CSV: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while exporting data to CSV.")

    def print_data(self):
        from_date = self.filter_from_date.date().toString("yyyy-MM-dd")
        to_date = self.filter_to_date.date().toString("yyyy-MM-dd")
        self.execute_print_query("SELECT employee_name, date(checkin_time), time(checkin_time), time(checkout_time) FROM checkin_checkout WHERE date(checkin_time) BETWEEN ? AND ?", [from_date, to_date])

    def clear_checkin_checkout_table(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM checkin_checkout")
                conn.commit()
                logging.info("Cleared checkin_checkout table")
                QMessageBox.information(self, "Success", "The checkin_checkout table has been cleared.")
        except Exception as e:
            logging.error(f"Error clearing checkin_checkout table: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while clearing the checkin_checkout table.")

    def execute_print_query(self, query, params):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                data = cursor.fetchall()
            if data:
                printer = QPrinter(QPrinter.HighResolution)
                dialog = QPrintDialog(printer, self)
                if dialog.exec_() == QPrintDialog.Accepted:
                    text = "\n".join([f"Name: {row[0]}, Date: {row[1]}, Time In: {row[2]}, Time Out: {row[3]}" for row in data])
                    document = QTextDocument()
                    document.setPlainText(text)
                    document.print_(printer)
                    logging.info("Printed data")
            else:
                QMessageBox.warning(self, "No Data", "No data available for the selected date range.")
                logging.info("No data available for printing")
        except Exception as e:
            logging.error(f"Error printing data: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while printing data.")

    def closeEvent(self, event):
        try:
            self.stop_recording()
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
            if hasattr(self, 'timer'):
                self.timer.stop()
            logging.info("Application closed")
            event.accept()
        except Exception as e:
            logging.error(f"Error during application close: {e}")
            event.accept()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;  /* Slightly lighter background for contrast */
            }
            QTabWidget::pane {
                border: 1px solid #000000;  /* Bold border color */
                border-radius: 5px;
                background: #ffffff;  /* Bright white background for tabs */
            }
            QTabBar::tab {
                background: #808080;  /* Darker grey for unselected tabs */
                color: #ffffff;  /* White text for contrast */
                border: 1px solid #000000;  /* Bold border */
                padding: 10px;
                border-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: #404040;  /* Even darker grey for selected and hovered tabs */
            }
            QTabBar::tab:selected {
                color: #ffffff;  /* White text for contrast */
                font-weight: bold;
            }
            QPushButton {
                background-color: #606060;  /* Darker grey for buttons */
                color: #ffffff;  /* White text for contrast */
                border-radius: 10px;
                padding: 10px;
                border: 1px solid #000000;  /* Bold border */
            }
            QPushButton:hover {
                background-color: #404040;  /* Darker grey for hovered buttons */
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #000000;  /* Bold border */
                border-radius: 5px;
                background-color: #f5f5f5;  /* Light grey background */
                color: #000000;  /* Black text for contrast */
            }
            QTextEdit {
                background-color: #f5f5f5;  /* Light grey background */
                border: 1px solid #000000;  /* Bold border */
                border-radius: 5px;
                color: #000000;  /* Black text for contrast */
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #000000;  /* Black text for bold appearance */
            }
            QProgressBar {
                text-align: center;
                background-color: #808080;  /* Darker grey background */
                border: 1px solid #000000;  /* Bold border */
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #404040;  /* Darker grey for progress */
            }
        """)


if __name__ == '__main__':
    create_tables()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    main_window = FaceDatabaseManager()
    main_window.show()
    logging.info("Application started")
    sys.exit(app.exec_())
