# File: main.py
import sys
import os

# Add the new directories to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'business'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'dal'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'common'))


from PyQt5.QtWidgets import QApplication
from ui.welcome_window import WelcomeWindow

def main():
    app = QApplication(sys.argv)
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()