# gui/file_panel.py
import os
from typing import Dict, List, Set, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QComboBox, QLineEdit, QScrollArea,
    QCheckBox, QHeaderView, QFileDialog, QMenu, QGridLayout
)
from PyQt6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, 
    QSortFilterProxyModel, QDir, Signal, pyqtSignal
)
from PyQt6.QtGui import (
    QIcon, QColor, QBrush, QFont
)

from core.file_manager import FileManager
from core.utils import format_file_size, get_file_icon_path, get_active_icon_paths

class FileListItem(QListWidgetItem):
    """Custom list item for file list."""
    
    def __init__(self, file_info: Dict[str, Any], parent=None):
        """Initialize a file list item.
        
        Args:
            file_info: Dictionary with file information.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.file_info = file_info
        self.category = None  # 'code' or 'context' or None
        
        # Set text and tooltip
        self.setText(file_info['path'])
        self.setToolTip(f"{file_info['full_path']}\nSize: {format_file_size(file_info['size'])}")
        
        # Set icon based on file extension
        extension = file_info['extension'].lower()
        icon_path = get_file_icon_path(extension)
        self.setIcon(QIcon(icon_path))
    
    def set_category(self, category: Optional[str]):
        """Set the category for this file item.
        
        Args:
            category: 'code', 'context', or None.
        """
        self.category = category
        
        # Update appearance based on category
        if category == 'code':
            self.setBackground(QColor(255, 248, 237))  # Light orange
            self.setForeground(QColor(0, 0, 0))
            self.setText(f"{self.file_info['path']} [CODE]")
        elif category == 'context':
            self.setBackground(QColor(240, 248, 255))  # Light blue
            self.setForeground(QColor(0, 0, 0))
            self.setText(f"{self.file_info['path']} [CONTEXT]")
        else:
            # Reset background and text
            self.setBackground(QBrush())
            self.setForeground(QColor(0, 0, 0))
            self.setText(self.file_info['path'])

class FilePanel(QWidget):
    """Panel for selecting files."""
    
    # Signals
    files_selected = pyqtSignal(dict)
    
    def __init__(self, file_manager: FileManager, config: Dict, parent=None):
        """Initialize the file panel.
        
        Args:
            file_manager: FileManager instance.
            config: Configuration dictionary.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.file_manager = file_manager
        self.config = config
        
        self._init_ui()
        self._load_files()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Add search bar
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.textChanged.connect(self._filter_files)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Extension filter
        extension_layout = QVBoxLayout()
        extension_label = QLabel("File Extensions:")
        extension_layout.addWidget(extension_label)
        
        # Add scrollable area for extensions
        extension_scroll = QScrollArea()
        extension_scroll.setWidgetResizable(True)
        extension_scroll.setMaximumHeight(80)
        
        extension_widget = QWidget()
        self.extension_layout = QGridLayout(extension_widget)
        self.extension_layout.setContentsMargins(5, 5, 5, 5)
        self.extension_layout.setSpacing(5)
        
        extension_scroll.setWidget(extension_widget)
        extension_layout.addWidget(extension_scroll)
        
        layout.addLayout(extension_layout)
        
        # File list header (selection counts and buttons)
        list_header = QHBoxLayout()
        
        # Selection counts
        self.code_count = QLabel("Code: 0")
        self.context_count = QLabel("Context: 0")
        
        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_selection)
        
        list_header.addWidget(self.code_count)
        list_header.addWidget(self.context_count)
        list_header.addStretch()
        list_header.addWidget(clear_btn)
        
        layout.addLayout(list_header)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.file_list, 1)  # Stretch to fill available space
        
        # Selection buttons
        btn_layout = QHBoxLayout()
        
        # Create buttons with custom styling
        select_code_btn = QPushButton("Select as CODE")
        select_code_btn.clicked.connect(lambda: self._set_selection_category("code"))
        select_code_btn.setStyleSheet(f"background-color: rgba(255, 165, 0, 0.6); color: black;")
        
        select_context_btn = QPushButton("Select as CONTEXT")
        select_context_btn.clicked.connect(lambda: self._set_selection_category("context"))
        select_context_btn.setStyleSheet(f"background-color: rgba(100, 149, 237, 0.6); color: black;")
        
        clear_selection_btn = QPushButton("Clear Selection")
        clear_selection_btn.clicked.connect(lambda: self._set_selection_category(None))
        
        btn_layout.addWidget(select_code_btn)
        btn_layout.addWidget(select_context_btn)
        btn_layout.addWidget(clear_selection_btn)
        
        layout.addLayout(btn_layout)
    
    def set_file_manager(self, file_manager: FileManager):
        """Set the file manager and reload files.
        
        Args:
            file_manager: FileManager instance.
        """
        self.file_manager = file_manager
        self._load_files()
    
    def _load_files(self):
        """Load files from the file manager."""
        if not self.file_manager:
            return
            
        # Clear file list
        self.file_list.clear()
        
        # Get all files
        files = self.file_manager.get_project_files()
        
        # Add to list
        for file in files:
            item = FileListItem(file)
            self.file_list.addItem(item)
        
        # Set up file extension filters
        self._setup_extension_filters(files)
        
        # Update status
        self._update_selection_counts()
    
    def _setup_extension_filters(self, files: List[Dict[str, Any]]):
        """Set up file extension filter checkboxes.
        
        Args:
            files: List of file information dictionaries.
        """
        # Clear existing filters
        while self.extension_layout.count():
            item = self.extension_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get unique extensions
        extensions = self.file_manager.get_unique_extensions(files)
        
        # Add checkbox for each extension
        row, col = 0, 0
        max_cols = 4  # Number of checkboxes per row
        
        for ext in sorted(extensions):
            if not ext:
                continue  # Skip files with no extension
                
            checkbox = QCheckBox(ext)
            checkbox.setChecked(ext in self.file_manager.core_extensions)
            checkbox.stateChanged.connect(self._apply_extension_filter)
            
            self.extension_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def _apply_extension_filter(self):
        """Apply extension filter to the file list."""
        # Get selected extensions
        selected_extensions = set()
        
        for i in range(self.extension_layout.count()):
            widget = self.extension_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                selected_extensions.add(widget.text())
        
        # Hide/show files based on extension
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            
            if isinstance(item, FileListItem):
                ext = item.file_info["extension"]
                
                if ext in selected_extensions:
                    item.setHidden(False)
                else:
                    item.setHidden(True)
    
    def _filter_files(self):
        """Filter files based on search text."""
        search_text = self.search_input.text().lower()
        
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            
            if search_text:
                # Only show if it matches the search text and isn't filtered by extension
                path = item.file_info['path'].lower()
                item.setHidden(search_text not in path or item.isHidden())
            else:
                # Keep extension filter
                pass
    
    def _show_context_menu(self, position):
        """Show context menu for file list.
        
        Args:
            position: Position where context menu was requested.
        """
        menu = QMenu()
        
        # Get selected items
        selected_items = self.file_list.selectedItems()
        
        if not selected_items:
            return
        
        # Add menu actions
        code_action = menu.addAction("Select as CODE")
        code_action.triggered.connect(lambda: self._set_selection_category("code"))
        
        context_action = menu.addAction("Select as CONTEXT")
        context_action.triggered.connect(lambda: self._set_selection_category("context"))
        
        menu.addSeparator()
        
        clear_action = menu.addAction("Clear Selection")
        clear_action.triggered.connect(lambda: self._set_selection_category(None))
        
        # Show menu
        menu.exec(self.file_list.mapToGlobal(position))
    
    def _set_selection_category(self, category: Optional[str]):
        """Set category for selected files.
        
        Args:
            category: 'code', 'context', or None.
        """
        # Get selected items
        selected_items = self.file_list.selectedItems()
        
        for item in selected_items:
            if isinstance(item, FileListItem):
                item.set_category(category)
        
        # Update counts
        self._update_selection_counts()
        
        # Emit signal with updated selections
        self.files_selected.emit(self.get_selected_files())
    
    def _update_selection_counts(self):
        """Update selection count labels."""
        code_count = 0
        context_count = 0
        
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            
            if isinstance(item, FileListItem) and not item.isHidden():
                if item.category == 'code':
                    code_count += 1
                elif item.category == 'context':
                    context_count += 1
        
        self.code_count.setText(f"Code: {code_count}")
        self.context_count.setText(f"Context: {context_count}")
    
    def _clear_selection(self):
        """Clear all file selections."""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            
            if isinstance(item, FileListItem):
                item.set_category(None)
        
        # Update counts
        self._update_selection_counts()
        
        # Emit signal with empty selections
        self.files_selected.emit(self.get_selected_files())
    
    def get_selected_files(self):
        """Get selected files by category.
        
        Returns:
            Dictionary with 'code' and 'context' lists of file information.
        """
        selected_files = {
            'code': [],
            'context': []
        }
        
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            
            if isinstance(item, FileListItem) and not item.isHidden():
                if item.category == 'code':
                    selected_files['code'].append(item.file_info)
                elif item.category == 'context':
                    selected_files['context'].append(item.file_info)
        
        return selected_files