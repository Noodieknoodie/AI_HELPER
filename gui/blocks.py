# gui/blocks.py
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMenu, QCheckBox, QDialog, QDialogButtonBox, QGridLayout,
    QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QMimeData, QPointF, pyqtSignal
from PyQt6.QtGui import QDrag, QMouseEvent, QIcon, QFont
import os

class ContentBlock(QFrame):
    """Base class for draggable content blocks."""
    
    # Signals
    moved = pyqtSignal(int, int)  # From index, to index
    removed = pyqtSignal(int)     # Index
    edited = pyqtSignal(int, str)  # Index, new content
    
    def __init__(self, title, content="", color="#FFFFFF", parent=None):
        super().__init__(parent)
        
        self.title = title
        self.content = content
        self.block_color = color
        self.drag_start_position = None
        
        # Set up styling
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setStyleSheet(f"QFrame {{ background-color: {color}; border-radius: 4px; }}")
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet(
            f"background-color: rgba(0, 0, 0, 0.05); border-top-left-radius: 4px; border-top-right-radius: 4px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        # Grip icon for dragging
        grip_label = QLabel("↕")
        grip_label.setStyleSheet("color: gray; font-weight: bold;")
        grip_label.setCursor(Qt.CursorShape.SizeAllCursor)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont(title_label.font().family(), 10, QFont.Weight.Bold))
        
        # Action buttons
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self._edit_content)
        
        remove_button = QPushButton("✕")
        remove_button.setMaximumWidth(30)
        remove_button.clicked.connect(self._remove_block)
        
        header_layout.addWidget(grip_label)
        header_layout.addWidget(title_label, 1)
        header_layout.addWidget(edit_button)
        header_layout.addWidget(remove_button)
        
        layout.addWidget(header)
        
        # Content
        self.content_widget = QTextEdit()
        self.content_widget.setReadOnly(True)
        self.content_widget.setText(self.content)
        self.content_widget.setMaximumHeight(150)  # Limit maximum height
        
        layout.addWidget(self.content_widget)
    
    def _edit_content(self):
        """Edit the block content."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {self.title}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        editor = QTextEdit()
        editor.setText(self.content)
        
        layout.addWidget(QLabel(f"Edit {self.title} Content:"))
        layout.addWidget(editor)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update content
            self.content = editor.toPlainText()
            self.content_widget.setText(self.content)
            
            # Emit signal
            index = self.parent().layout().indexOf(self)
            self.edited.emit(index, self.content)
    
    def _remove_block(self):
        """Remove the block."""
        # Get index
        index = self.parent().layout().indexOf(self)
        
        # Emit signal
        self.removed.emit(index)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for drag and drop."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for drag and drop."""
        if not self.drag_start_position:
            return
            
        if (event.position() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        # Start drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.title)
        drag.setMimeData(mime_data)
        
        # Get index
        index = self.parent().layout().indexOf(self)
        
        # Execute drag
        result = drag.exec(Qt.DropAction.MoveAction)
        
        # Reset drag start position
        self.drag_start_position = None

class PromptBlock(ContentBlock):
    """Block for prompt content."""
    
    def __init__(self, content="", parent=None):
        super().__init__("Prompt", content, "#F6F8FA", parent)

class CodeBlock(ContentBlock):
    """Block for code files."""
    
    def __init__(self, content="", parent=None):
        super().__init__("Code Files", content, "#FFF8ED", parent)
        
        # Add cleaning options button
        header_widget = self.layout().itemAt(0).widget()
        header_layout = header_widget.layout()
        
        # Insert cleaning options button before the last item (remove button)
        clean_button = QPushButton("Clean...")
        clean_button.clicked.connect(self._show_cleaning_options)
        
        header_layout.insertWidget(header_layout.count() - 1, clean_button)
    
    def _show_cleaning_options(self):
        """Show code cleaning options."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Code Cleaning Options")
        
        layout = QVBoxLayout(dialog)
        
        # Cleaning options
        options_layout = QGridLayout()
        
        self.remove_comments_check = QCheckBox("Remove Comments")
        self.remove_blank_lines_check = QCheckBox("Remove Blank Lines")
        self.remove_docstrings_check = QCheckBox("Remove Docstrings")
        
        options_layout.addWidget(self.remove_comments_check, 0, 0)
        options_layout.addWidget(self.remove_blank_lines_check, 0, 1)
        options_layout.addWidget(self.remove_docstrings_check, 1, 0)
        
        layout.addWidget(QLabel("Select code cleaning options:"))
        layout.addLayout(options_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply cleaning options
            cleaning_options = {
                "remove_comments": self.remove_comments_check.isChecked(),
                "remove_blank_lines": self.remove_blank_lines_check.isChecked(),
                "remove_docstrings": self.remove_docstrings_check.isChecked()
            }
            
            # Skip if no options selected
            if not any(cleaning_options.values()):
                return
            
            # Get file extensions from the content
            file_paths = self.content.strip().split('\n')
            
            # Clean each file based on its extension
            cleaned_content = []
            for path in file_paths:
                path = path.strip()
                if not path:
                    continue
                
                # Determine file extension for proper cleaning
                extension = os.path.splitext(path)[1].lower()
                
                # Only add the path to the cleaned content
                cleaned_content.append(path)
            
            # Update the content
            if cleaned_content:
                self.content = '\n'.join(cleaned_content)
                self.content_widget.setText(self.content)
                
                # Emit signal to update the content
                index = self.parent().layout().indexOf(self)
                self.edited.emit(index, self.content)
                
                # Show confirmation message
                QMessageBox.information(
                    self,
                    "Code Cleaning",
                    f"Code files will be cleaned when processing with these options:\n"
                    f"• Remove comments: {'Yes' if cleaning_options['remove_comments'] else 'No'}\n"
                    f"• Remove blank lines: {'Yes' if cleaning_options['remove_blank_lines'] else 'No'}\n"
                    f"• Remove docstrings: {'Yes' if cleaning_options['remove_docstrings'] else 'No'}"
                )

class ContextBlock(ContentBlock):
    """Block for context files."""
    
    def __init__(self, content="", parent=None):
        super().__init__("Context Files", content, "#F0F8FF", parent)

class ReminderBlock(ContentBlock):
    """Block for reminder content."""
    
    def __init__(self, content="", parent=None):
        super().__init__("Reminder", content, "#F0FFF0", parent)

class BlocksContainer(QWidget):
    """Container for content blocks."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAcceptDrops(True)
        
        # Set up layout
        self.blocks_layout = QVBoxLayout(self)
        self.blocks_layout.setContentsMargins(0, 0, 0, 0)
        self.blocks_layout.setSpacing(8)
        self.blocks_layout.addStretch()
    
    def add_block(self, block_type, content=""):
        """Add a block of the specified type."""
        if block_type == "prompt":
            block = PromptBlock(content, self)
        elif block_type == "code":
            block = CodeBlock(content, self)
        elif block_type == "context":
            block = ContextBlock(content, self)
        elif block_type == "reminder":
            block = ReminderBlock(content, self)
        else:
            return None
            
        # Connect signals
        block.moved.connect(self._move_block)
        block.removed.connect(self._remove_block)
        
        # Add to layout before the stretch item
        self.blocks_layout.insertWidget(self.blocks_layout.count() - 1, block)
        
        return block
    
    def _move_block(self, from_index, to_index):
        """Move a block from one position to another."""
        if from_index == to_index:
            return
            
        # Get the widget
        widget = self.blocks_layout.takeAt(from_index).widget()
        
        # Insert at new position
        self.blocks_layout.insertWidget(to_index, widget)
    
    def _remove_block(self, index):
        """Remove a block."""
        widget = self.blocks_layout.takeAt(index).widget()
        widget.deleteLater()
    
    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handle drag move events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events."""
        if event.mimeData().hasText():
            # Get source widget
            source = event.source()
            
            # Get source index
            source_index = self.blocks_layout.indexOf(source)
            
            # Get drop position
            pos = event.position().y()
            
            # Determine target index
            target_index = -1
            
            for i in range(self.blocks_layout.count() - 1):  # Exclude stretch item
                widget = self.blocks_layout.itemAt(i).widget()
                widget_pos = widget.pos().y()
                widget_height = widget.height()
                
                if pos < widget_pos + widget_height / 2:
                    target_index = i
                    break
                
                if i == self.blocks_layout.count() - 2:  # Last widget before stretch
                    target_index = i + 1
            
            if target_index == -1:
                target_index = 0
                
            # Move the block
            self._move_block(source_index, target_index)
            
            event.acceptProposedAction()
    
    def get_blocks_content(self):
        """Get the content of all blocks in order."""
        content = {}
        
        for i in range(self.blocks_layout.count() - 1):  # Exclude stretch item
            widget = self.blocks_layout.itemAt(i).widget()
            
            if isinstance(widget, PromptBlock):
                content["prompt"] = widget.content
            elif isinstance(widget, CodeBlock):
                content["code"] = widget.content
            elif isinstance(widget, ContextBlock):
                content["context"] = widget.content
            elif isinstance(widget, ReminderBlock):
                content["reminder"] = widget.content
        
        return content