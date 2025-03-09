# gui/message_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QSplitter, QFrame, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from gui.blocks import BlocksContainer, PromptBlock, CodeBlock, ContextBlock, ReminderBlock

class MessagePanel(QWidget):
    """Panel for constructing messages."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.selected_files = {"code": [], "context": []}
        self.prompt_data = {
            "prompt": "",
            "reminder": ""
        }
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Message Construction:")
        header_label.setFont(QFont(header_label.font().family(), 12, QFont.Weight.Bold))
        
        preview_button = QPushButton("Preview")
        preview_button.clicked.connect(self._preview_message)
        
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self._reset_blocks)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(preview_button)
        header_layout.addWidget(reset_button)
        
        layout.addLayout(header_layout)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Message composition area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Blocks container
        self.blocks_container = BlocksContainer()
        self.scroll_area.setWidget(self.blocks_container)
        
        # Add initial blocks
        self.prompt_block = self.blocks_container.add_block("prompt", "")
        
        layout.addWidget(self.scroll_area, 1)
        
        # Message preview
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setPlaceholderText("Message preview will appear here...")
        self.preview_edit.setVisible(False)
        
        layout.addWidget(self.preview_edit)
        
        # Hint text
        hint_label = QLabel(
            "Drag blocks to rearrange. Click 'Edit' on a block to modify its content.\n"
            "The assembled message will be sent to the LLM API."
        )
        hint_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(hint_label)
    
    def set_prompt(self, prompt_data):
        self.prompt_data = prompt_data
        
        # Update prompt block
        if hasattr(self, 'prompt_block'):
            self.prompt_block.content = prompt_data.get('prompt', '')
            self.prompt_block.content_widget.setText(prompt_data.get('prompt', ''))
        
        # Add or update reminder block if needed
        reminder_text = prompt_data.get('reminder', '')
        
        if reminder_text:
            # Check if reminder block exists
            reminder_block = None
            for i in range(self.blocks_container.blocks_layout.count() - 1):
                widget = self.blocks_container.blocks_layout.itemAt(i).widget()
                if isinstance(widget, ReminderBlock):
                    reminder_block = widget
                    break
                    
            if reminder_block:
                reminder_block.content = reminder_text
                reminder_block.content_widget.setText(reminder_text)
            else:
                self.blocks_container.add_block("reminder", reminder_text)
        else:
            # Remove reminder block if it exists
            for i in range(self.blocks_container.blocks_layout.count() - 1):
                widget = self.blocks_container.blocks_layout.itemAt(i).widget()
                if isinstance(widget, ReminderBlock):
                    self.blocks_container.blocks_layout.takeAt(i).widget().deleteLater()
                    break
    
    def update_files(self, selected_files):
        self.selected_files = selected_files
        
        # Check if we need to add/remove blocks
        has_code = bool(selected_files.get('code', []))
        has_context = bool(selected_files.get('context', []))
        
        # Update or add code block
        if has_code:
            code_content = "Selected code files:"
            for file in selected_files['code']:
                code_content += f"\n- {file['path']}"
                
            # Check if code block exists
            code_block = None
            for i in range(self.blocks_container.blocks_layout.count() - 1):
                widget = self.blocks_container.blocks_layout.itemAt(i).widget()
                if isinstance(widget, CodeBlock):
                    code_block = widget
                    break
                    
            if code_block:
                code_block.content = code_content
                code_block.content_widget.setText(code_content)
            else:
                self.blocks_container.add_block("code", code_content)
        else:
            # Remove code block if it exists
            for i in range(self.blocks_container.blocks_layout.count() - 1):
                widget = self.blocks_container.blocks_layout.itemAt(i).widget()
                if isinstance(widget, CodeBlock):
                    self.blocks_container.blocks_layout.takeAt(i).widget().deleteLater()
                    break
        
        # Update or add context block
        if has_context:
            context_content = "Selected context files:"
            for file in selected_files['context']:
                context_content += f"\n- {file['path']}"
                
            # Check if context block exists
            context_block = None
            for i in range(self.blocks_container.blocks_layout.count() - 1):
                widget = self.blocks_container.blocks_layout.itemAt(i).widget()
                if isinstance(widget, ContextBlock):
                    context_block = widget
                    break
                    
            if context_block:
                context_block.content = context_content
                context_block.content_widget.setText(context_content)
            else:
                self.blocks_container.add_block("context", context_content)
        else:
            # Remove context block if it exists
            for i in range(self.blocks_container.blocks_layout.count() - 1):
                widget = self.blocks_container.blocks_layout.itemAt(i).widget()
                if isinstance(widget, ContextBlock):
                    self.blocks_container.blocks_layout.takeAt(i).widget().deleteLater()
                    break
    
    def _preview_message(self):
        """Preview the assembled message."""
        # Get preview text
        preview_text = self.get_assembled_message(substitute_files=False)
        
        # Show preview
        self.preview_edit.setText(preview_text)
        self.preview_edit.setVisible(True)
    
    def _reset_blocks(self):
        """Reset blocks to default order."""
        # Clear all blocks
        while self.blocks_container.blocks_layout.count() > 1:  # Keep stretch item
            widget = self.blocks_container.blocks_layout.takeAt(0).widget()
            widget.deleteLater()
        
        # Add blocks in default order
        self.prompt_block = self.blocks_container.add_block("prompt", self.prompt_data.get('prompt', ''))
        
        if self.selected_files.get('code', []):
            code_content = "Selected code files:"
            for file in self.selected_files['code']:
                code_content += f"\n- {file['path']}"
                
            self.blocks_container.add_block("code", code_content)
            
        if self.selected_files.get('context', []):
            context_content = "Selected context files:"
            for file in self.selected_files['context']:
                context_content += f"\n- {file['path']}"
                
            self.blocks_container.add_block("context", context_content)
        
        # Add reminder block if it exists
        if self.prompt_data.get('reminder', ''):
            self.blocks_container.add_block("reminder", self.prompt_data.get('reminder', ''))
        
        # Hide preview
        self.preview_edit.setVisible(False)
    
    def get_assembled_message(self, substitute_files=True):
        # Get blocks content
        blocks_content = ""
        
        for i in range(self.blocks_container.blocks_layout.count() - 1):  # Exclude stretch item
            widget = self.blocks_container.blocks_layout.itemAt(i).widget()
            
            if isinstance(widget, PromptBlock):
                blocks_content += f"######## PROMPT ########\n//// PROMPT – START ////\n{widget.content}\n//// PROMPT – END ////\n\n"
            elif isinstance(widget, CodeBlock):
                if substitute_files and self.selected_files.get('code', []):
                    # Use placeholder text for preview or real file content for sending
                    if not substitute_files:
                        blocks_content += f"######## CODE ########\n//// CODE – START ////\n{widget.content}\n//// CODE – END ////\n\n"
                    else:
                        blocks_content += f"######## CODE ########\n//// CODE – START ////\n{{code}}\n//// CODE – END ////\n\n"
                else:
                    blocks_content += f"######## CODE ########\n//// CODE – START ////\n{widget.content}\n//// CODE – END ////\n\n"
            elif isinstance(widget, ContextBlock):
                if substitute_files and self.selected_files.get('context', []):
                    # Use placeholder text for preview or real file content for sending
                    if not substitute_files:
                        blocks_content += f"######## CONTEXT ########\n//// CONTEXT – START ////\n{widget.content}\n//// CONTEXT – END ////\n\n"
                    else:
                        blocks_content += f"######## CONTEXT ########\n//// CONTEXT – START ////\n{{context}}\n//// CONTEXT – END ////\n\n"
                else:
                    blocks_content += f"######## CONTEXT ########\n//// CONTEXT – START ////\n{widget.content}\n//// CONTEXT – END ////\n\n"
            elif isinstance(widget, ReminderBlock):
                blocks_content += f"######## REMINDER ########\n//// REMINDER – START ////\n{widget.content}\n//// REMINDER – END ////\n\n"
        
        return blocks_content.strip()