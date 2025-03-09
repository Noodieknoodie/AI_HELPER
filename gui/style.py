# gui/style.py
from PyQt6.QtGui import QColor, QFont, QPalette, QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

class Style:
    # Colors
    PRIMARY = "#0A84FF"  # Vibrant blue for primary actions and selections
    SECONDARY = "#00B889"  # Teal for secondary highlights 
    CODE = "#FF9500"  # Amber orange for code file selections
    CONTEXT = "#4682B4"  # Steel blue for context selections
    PROMPT = "#F6F8FA"  # Light gray for prompt blocks
    REMINDER = "#F0FFF0"  # Light mint for reminder blocks
    BACKGROUND = "#F5F7F9"  # Light gray with subtle blue tint
    FOREGROUND = "#2C3E50"  # Deep blue-gray for text
    SURFACE = "#FFFFFF"  # White for component surfaces
    BORDER = "#E1E4E8"  # Light gray for borders
    ERROR = "#E63946"  # Red for errors
    SUCCESS = "#2ECC71"  # Green for success indicators
    
    # Font sizes
    FONT_SMALL = 9
    FONT_NORMAL = 10
    FONT_LARGE = 12
    FONT_HEADER = 14
    
    # Spacing
    PADDING_SMALL = 4
    PADDING_NORMAL = 8
    PADDING_LARGE = 12
    MARGIN_SMALL = 4
    MARGIN_NORMAL = 8
    MARGIN_LARGE = 16
    
    # Borders
    BORDER_RADIUS = 6
    BORDER_WIDTH = 1
    
    @staticmethod
    def apply_application_style(app):
        """Apply the application style to QApplication."""
        app.setStyle("Fusion")
        
        # Set app-wide style
        app.setStyleSheet(f"""
            QMainWindow, QDialog, QWidget {{ 
                background-color: {Style.BACKGROUND}; 
                color: {Style.FOREGROUND};
                font-size: {Style.FONT_NORMAL}pt;
            }}
            
            QLabel {{ 
                color: {Style.FOREGROUND}; 
                font-size: {Style.FONT_NORMAL}pt;
            }}
            
            QPushButton {{ 
                background-color: {Style.SURFACE}; 
                border: 1px solid {Style.BORDER}; 
                border-radius: 4px; 
                padding: 6px 12px; 
                color: {Style.FOREGROUND};
            }}
            
            QPushButton:hover {{ 
                background-color: #F0F0F0; 
            }}
            
            QPushButton:pressed {{ 
                background-color: #E8E8E8; 
            }}
            
            QPushButton:disabled {{ 
                background-color: #F5F5F5; 
                color: #AAAAAA; 
            }}
            
            QPushButton#primaryButton {{ 
                background-color: {Style.PRIMARY}; 
                color: white; 
                font-weight: bold;
            }}
            
            QPushButton#primaryButton:hover {{ 
                background-color: #0071E3; 
            }}
            
            QPushButton#primaryButton:pressed {{ 
                background-color: #005BBF; 
            }}
            
            QPushButton#secondaryButton {{ 
                background-color: {Style.SECONDARY}; 
                color: white; 
                font-weight: bold;
            }}
            
            QPushButton#secondaryButton:hover {{ 
                background-color: #00A67A; 
            }}
            
            QPushButton#secondaryButton:pressed {{ 
                background-color: #008F69; 
            }}
            
            QLineEdit, QTextEdit, QPlainTextEdit {{ 
                background-color: {Style.SURFACE}; 
                border: 1px solid {Style.BORDER};
                border-radius: 4px;
                padding: 6px;
                selection-background-color: {Style.PRIMARY};
                selection-color: white;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ 
                border: 1px solid {Style.PRIMARY}; 
            }}
            
            QTreeView, QListView, QTableView {{ 
                background-color: {Style.SURFACE};
                alternate-background-color: #F9FAFB;
                border: 1px solid {Style.BORDER};
                selection-background-color: #E5F3FF;
                selection-color: {Style.FOREGROUND};
                outline: none;
            }}
            
            QTreeView::item, QListView::item {{ 
                padding: 2px 4px; 
                min-height: 24px;
            }}
            
            QTreeView::item:selected, QListView::item:selected {{ 
                background-color: #E5F3FF;
                color: {Style.FOREGROUND};
            }}
            
            QTreeView::item:hover, QListView::item:hover {{ 
                background-color: #F5F9FF;
            }}
            
            QHeaderView::section {{ 
                background-color: #EAEDF0;
                padding: 4px;
                border: 1px solid {Style.BORDER};
                font-weight: bold;
            }}
            
            QComboBox {{ 
                background-color: {Style.SURFACE}; 
                border: 1px solid {Style.BORDER}; 
                border-radius: 4px; 
                padding: 4px 8px; 
                min-height: 24px;
            }}
            
            QComboBox::drop-down {{ 
                subcontrol-origin: padding; 
                subcontrol-position: center right; 
                width: 20px; 
                border-left: 1px solid {Style.BORDER}; 
            }}
            
            QComboBox QAbstractItemView {{ 
                background-color: {Style.SURFACE}; 
                border: 1px solid {Style.BORDER}; 
                selection-background-color: #E5F3FF; 
            }}
            
            QProgressBar {{ 
                border: 1px solid {Style.BORDER}; 
                border-radius: 4px; 
                background-color: {Style.SURFACE}; 
                text-align: center; 
            }}
            
            QProgressBar::chunk {{ 
                background-color: {Style.PRIMARY}; 
                width: 1px; 
            }}
            
            QScrollBar:vertical {{ 
                border: none; 
                background-color: #F0F0F0; 
                width: 8px; 
                margin: 0px; 
            }}
            
            QScrollBar::handle:vertical {{ 
                background-color: #C1C1C1; 
                min-height: 30px; 
                border-radius: 4px; 
            }}
            
            QScrollBar::handle:vertical:hover {{ 
                background-color: #A8A8A8; 
            }}
            
            QScrollBar:horizontal {{ 
                border: none; 
                background-color: #F0F0F0; 
                height: 8px; 
                margin: 0px; 
            }}
            
            QScrollBar::handle:horizontal {{ 
                background-color: #C1C1C1; 
                min-width: 30px; 
                border-radius: 4px; 
            }}
            
            QScrollBar::handle:horizontal:hover {{ 
                background-color: #A8A8A8; 
            }}
            
            QScrollBar::add-line, QScrollBar::sub-line {{ 
                border: none; 
                background: none; 
            }}
            
            QScrollBar::add-page, QScrollBar::sub-page {{ 
                background: none; 
            }}
            
            QTabWidget::pane {{ 
                border: 1px solid {Style.BORDER}; 
                border-radius: 4px; 
                top: -1px; 
            }}
            
            QTabBar::tab {{ 
                background-color: #EAEDF0; 
                border: 1px solid {Style.BORDER}; 
                border-bottom: none; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
                padding: 6px 12px; 
                margin-right: 2px; 
            }}
            
            QTabBar::tab:selected {{ 
                background-color: {Style.SURFACE}; 
                border-bottom: 1px solid {Style.SURFACE}; 
            }}
            
            QTabBar::tab:hover:!selected {{ 
                background-color: #F0F0F0; 
            }}
            
            QSplitter::handle {{ 
                background-color: {Style.BORDER}; 
            }}
            
            QSplitter::handle:horizontal {{ 
                width: 2px; 
            }}
            
            QSplitter::handle:vertical {{ 
                height: 2px; 
            }}
            
            QGroupBox {{ 
                border: 1px solid {Style.BORDER}; 
                border-radius: 4px; 
                margin-top: 16px; 
                font-weight: bold; 
            }}
            
            QGroupBox::title {{ 
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                left: 8px; 
                padding: 0 5px; 
            }}
            
            /* Custom block styles */
            .PromptBlock {{ 
                border: 1px solid #E1E4E8; 
                border-left: 3px solid #0A84FF; 
                border-radius: 4px; 
                background-color: {Style.PROMPT}; 
            }}
            
            .CodeBlock {{ 
                border: 1px solid #E1E4E8; 
                border-left: 3px solid {Style.CODE}; 
                border-radius: 4px; 
                background-color: #FFF8ED; 
            }}
            
            .ContextBlock {{ 
                border: 1px solid #E1E4E8; 
                border-left: 3px solid {Style.CONTEXT}; 
                border-radius: 4px; 
                background-color: #F0F8FF; 
            }}
            
            .ReminderBlock {{ 
                border: 1px solid #E1E4E8; 
                border-left: 3px solid {Style.SECONDARY}; 
                border-radius: 4px; 
                background-color: {Style.REMINDER}; 
            }}
            
            .BlockHeader {{ 
                background-color: rgba(0, 0, 0, 0.05); 
                padding: 6px 8px; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
            }}
            
            .BlockContent {{ 
                padding: 8px; 
            }}
        """)