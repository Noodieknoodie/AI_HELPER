# gui/output_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QCheckBox, QGroupBox, QTabWidget, QFileDialog,
    QProgressBar, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import os
import re

class OutputPanel(QWidget):
    """Panel for output configuration and preview."""
    
    def __init__(self, file_manager, parent=None):
        super().__init__(parent)
        
        self.file_manager = file_manager
        self.response_text = ""
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Format tab
        format_tab = QWidget()
        format_layout = QVBoxLayout(format_tab)
        
        # Format editor
        format_header = QHBoxLayout()
        
        format_label = QLabel("Output Format:")
        format_label.setFont(QFont(format_label.font().family(), 12, QFont.Weight.Bold))
        
        reset_button = QPushButton("Reset to Default")
        reset_button.clicked.connect(self._reset_format)
        
        format_header.addWidget(format_label)
        format_header.addStretch()
        format_header.addWidget(reset_button)
        
        format_layout.addLayout(format_header)
        
        self.format_edit = QTextEdit()
        self.format_edit.setPlaceholderText("Enter output format...")
        self._reset_format()  # Set default format
        
        format_layout.addWidget(self.format_edit, 1)
        
        # Include options
        options_group = QGroupBox("Include in Output")
        options_layout = QHBoxLayout(options_group)
        
        self.include_prompt_check = QCheckBox("Prompt")
        self.include_prompt_check.setChecked(True)
        
        self.include_response_check = QCheckBox("Response")
        self.include_response_check.setChecked(True)
        
        self.include_code_check = QCheckBox("Code")
        self.include_code_check.setChecked(True)
        
        self.include_context_check = QCheckBox("Context")
        self.include_context_check.setChecked(False)
        
        self.include_reminder_check = QCheckBox("Reminder")
        self.include_reminder_check.setChecked(False)
        
        options_layout.addWidget(self.include_prompt_check)
        options_layout.addWidget(self.include_response_check)
        options_layout.addWidget(self.include_code_check)
        options_layout.addWidget(self.include_context_check)
        options_layout.addWidget(self.include_reminder_check)
        options_layout.addStretch()
        
        format_layout.addWidget(options_group)
        
        # Variables reminder
        variables_label = QLabel(
            "Available variables: {prompt}, {response}, {code}, {context}, {reminder}\n"
            "Use these variables to arrange content in the output file."
        )
        variables_label.setStyleSheet("color: gray; font-style: italic;")
        
        format_layout.addWidget(variables_label)
        
        # Response tab
        response_tab = QWidget()
        response_layout = QVBoxLayout(response_tab)
        
        response_header = QHBoxLayout()
        
        response_label = QLabel("AI Response:")
        response_label.setFont(QFont(response_label.font().family(), 12, QFont.Weight.Bold))
        
        save_button = QPushButton("Save Response")
        save_button.clicked.connect(self._save_response)
        
        response_header.addWidget(response_label)
        response_header.addStretch()
        response_header.addWidget(save_button)
        
        response_layout.addLayout(response_header)
        
        self.response_edit = QTextEdit()
        self.response_edit.setReadOnly(True)
        self.response_edit.setPlaceholderText("AI response will appear here...")
        
        response_layout.addWidget(self.response_edit, 1)
        
        # Add tabs
        self.tabs.addTab(format_tab, "Format")
        self.tabs.addTab(response_tab, "Response")
        
        layout.addWidget(self.tabs, 1)
    
    def set_file_manager(self, file_manager):
        """Set the file manager."""
        self.file_manager = file_manager
    
    def _reset_format(self):
        """Reset the output format to default."""
        default_format = """######## RESPONSE ########
{response}

######## CODE ########
{code}

######## CONTEXT ########
{context}

######## REMINDER ########
{reminder}"""
        
        self.format_edit.setText(default_format)
    
    def set_response(self, response_text):
        """Set the response text."""
        self.response_text = response_text
        self.response_edit.setText(response_text)
        
        # Switch to response tab
        self.tabs.setCurrentIndex(1)
    
    def get_response_text(self):
        """Get the response text."""
        return self.response_text
    
    def get_output_options(self):
        """Get the output options."""
        return {
            "include_prompt": self.include_prompt_check.isChecked(),
            "include_response": self.include_response_check.isChecked(),
            "include_code": self.include_code_check.isChecked(),
            "include_context": self.include_context_check.isChecked(),
            "include_reminder": self.include_reminder_check.isChecked()
        }
    
    def format_output(self, response, prompt, code_files, context_files, options=None):
        """Format the output based on the template and options."""
        if options is None:
            options = self.get_output_options()
            
        # Get template
        template = self.format_edit.toPlainText()
        
        # Prepare data
        data = {}
        
        if options.get("include_prompt", True):
            data["prompt"] = f"//// PROMPT – START ////\n{prompt}\n//// PROMPT – END ////"
        else:
            data["prompt"] = ""
            
        if options.get("include_response", True):
            data["response"] = f"//// RESPONSE – START ////\n{response}\n//// RESPONSE – END ////"
        else:
            data["response"] = ""
            
        if options.get("include_code", True) and code_files:
            code_content = self.file_manager.compile_files(code_files)
            data["code"] = f"//// CODE – START ////\n{code_content}\n//// CODE – END ////"
        else:
            data["code"] = ""
            
        if options.get("include_context", True) and context_files:
            context_content = self.file_manager.compile_files(context_files)
            data["context"] = f"//// CONTEXT – START ////\n{context_content}\n//// CONTEXT – END ////"
        else:
            data["context"] = ""
            
        if options.get("include_reminder", True) and "{reminder}" in template:
            # Extract reminder from prompt if present
            reminder_match = re.search(r"######## REMINDER ########\n//// REMINDER – START ////\n(.*?)\n//// REMINDER – END ////", prompt, re.DOTALL)
            if reminder_match:
                reminder_content = reminder_match.group(1)
                data["reminder"] = f"//// REMINDER – START ////\n{reminder_content}\n//// REMINDER – END ////"
            else:
                data["reminder"] = ""
        else:
            data["reminder"] = ""
            
        # Replace variables in template
        output = template
        for key, value in data.items():
            pattern = '{' + key + '}'
            output = re.sub(pattern, value, output, flags=re.IGNORECASE)
            
        return output
    
    def _save_response(self):
        """Save the response to a file."""
        if not self.response_text:
            QMessageBox.warning(
                self,
                "No Response",
                "There is no response to save."
            )
            return
            
        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Response",
            os.path.join(self.file_manager.outputs_dir, "response.txt"),
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.response_text)
                    
                QMessageBox.information(
                    self,
                    "Success",
                    f"Response saved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    f"Failed to save response: {str(e)}"
                )