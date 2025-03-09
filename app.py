# app.py
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from config import init_config
from gui.main_window import MainWindow

def find_project_root():
    """Find the project root directory (parent of AI_HELP)."""
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    return current_dir.parent

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'icons', 'app_icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Find project root (parent of the AI_HELP directory)
    project_root = find_project_root()
    
    # Initialize configuration
    config = init_config(project_root)
    
    # Create and show the main window
    window = MainWindow(config)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()