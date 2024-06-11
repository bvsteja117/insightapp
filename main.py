# main.py
import sys
from PyQt5.QtWidgets import QApplication
from database.database_manager import create_tables
from gui.gui_manager import FaceDatabaseManager


def main():
    # Initialize the database and create tables if they don't exist
    create_tables()

    # Initialize the Qt Application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create and show the main window
    main_window = FaceDatabaseManager()
    main_window.show()

    # Start the Qt event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
