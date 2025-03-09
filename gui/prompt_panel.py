# gui/prompt_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QDialog, QLineEdit, QFormLayout,
    QDialogButtonBox, QMessageBox, QFrame, QSplitter, QGridLayout,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class SavePromptDialog(QDialog):
    """Dialog for saving a prompt."""
    
    def __init__(self, parent=None, name="", prompt_id=""):
        super().__init__(parent)
        self.setWindowTitle("Save Prompt")
        self.setMinimumWidth(400)
        
        # Set up layout
        layout = QVBoxLayout(self)
        
        # Form layout for prompt details
        form_layout = QFormLayout()
        
        # Prompt name
        self.name_edit = QLineEdit()
        if name:
            self.name_edit.setText(name)
        form_layout.addRow("Display Name:", self.name_edit)
        
        # Prompt ID
        self.id_edit = QLineEdit()
        if prompt_id:
            self.id_edit.setText(prompt_id)
        else:
            # Generate ID from name if not provided
            self.name_edit.textChanged.connect(self._update_id_from_name)
        form_layout.addRow("Prompt ID:", self.id_edit)
        
        layout.addLayout(form_layout)
        
        # Note about ID
        note_label = QLabel("* The Prompt ID will be used as the filename and cannot be changed later.")
        note_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(note_label)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _update_id_from_name(self, name):
        """Update prompt ID based on name."""
        if not self.id_edit.text():
            # Convert name to a valid ID
            import re
            prompt_id = re.sub(r'[^\w\-_]', '_', name.lower())
            self.id_edit.setText(prompt_id)
    
    def get_prompt_name(self):
        """Get the entered prompt name."""
        return self.name_edit.text()
    
    def get_prompt_id(self):
        """Get the entered prompt ID."""
        return self.id_edit.text()

class PromptPanel(QWidget):
    """Panel for prompt management."""
    
    # Signals
    prompt_selected = pyqtSignal(dict)
    
    def __init__(self, file_manager, parent=None):
        super().__init__(parent)
        
        self.file_manager = file_manager
        self.current_prompt_id = None
        self.current_prompt_data = {
            "name": "",
            "prompt": "",
            "reminder": ""
        }
        
        self._init_ui()
        self._load_prompts()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Prompt selection header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        prompt_label = QLabel("Prompt:")
        prompt_label.setFont(QFont(prompt_label.font().family(), 12, QFont.Weight.Bold))
        
        self.prompt_combo = QComboBox()
        self.prompt_combo.setMinimumWidth(250)
        self.prompt_combo.setMaximumWidth(500)
        self.prompt_combo.currentIndexChanged.connect(self._prompt_selected)
        
        new_button = QPushButton("New")
        new_button.clicked.connect(self._new_prompt)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._save_prompt)
        
        save_as_button = QPushButton("Save As...")
        save_as_button.clicked.connect(self._save_prompt_as)
        
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._delete_prompt)
        
        header_layout.addWidget(prompt_label)
        header_layout.addWidget(self.prompt_combo, 1)
        header_layout.addWidget(new_button)
        header_layout.addWidget(save_button)
        header_layout.addWidget(save_as_button)
        header_layout.addWidget(delete_button)
        
        layout.addLayout(header_layout)
        
        # Content tabs
        self.tabs = QTabWidget()
        
        # Prompt content tab
        prompt_tab = QWidget()
        prompt_layout = QVBoxLayout(prompt_tab)
        prompt_layout.setContentsMargins(0, 0, 0, 0)
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your prompt here...")
        
        prompt_layout.addWidget(QLabel("Prompt Content:"))
        prompt_layout.addWidget(self.prompt_edit)
        
        # Variables hint
        variables_label = QLabel(
            "Available variables: {code} - Inserts code files, {context} - Inserts context files\n"
            "The prompt text will be sent to the AI model along with the selected files."
        )
        variables_label.setStyleSheet("color: gray; font-style: italic;")
        prompt_layout.addWidget(variables_label)
        
        # Reminder content tab
        reminder_tab = QWidget()
        reminder_layout = QVBoxLayout(reminder_tab)
        reminder_layout.setContentsMargins(0, 0, 0, 0)
        
        self.reminder_edit = QTextEdit()
        self.reminder_edit.setPlaceholderText("Enter optional reminder instructions here...")
        
        reminder_layout.addWidget(QLabel("Reminder Content:"))
        reminder_layout.addWidget(self.reminder_edit)
        
        # Reminder hint
        reminder_hint = QLabel(
            "The reminder is optional text added at the end of your message.\n"
            "Use it to provide additional instructions or reminders to the AI model."
        )
        reminder_hint.setStyleSheet("color: gray; font-style: italic;")
        reminder_layout.addWidget(reminder_hint)
        
        # Add tabs
        self.tabs.addTab(prompt_tab, "Prompt")
        self.tabs.addTab(reminder_tab, "Reminder")
        
        layout.addWidget(self.tabs)
    
    def set_file_manager(self, file_manager):
        """Set the file manager and reload prompts."""
        self.file_manager = file_manager
        self._load_prompts()
    
    def _load_prompts(self):
        """Load available prompts."""
        if not self.file_manager:
            return
            
        # Remember current selection
        current_id = self.current_prompt_id
        
        # Clear combo box
        self.prompt_combo.clear()
        
        # Get prompts
        prompts = self.file_manager.get_prompts()
        
        # Add to combo box
        for prompt_id, prompt_data in sorted(prompts.items(), key=lambda x: x[1].get('name', x[0])):
            display_name = prompt_data.get('name', prompt_id)
            self.prompt_combo.addItem(display_name, prompt_id)
        
        # Add custom option
        self.prompt_combo.addItem("Custom", "custom")
        
        # Restore previous selection if possible
        if current_id:
            for i in range(self.prompt_combo.count()):
                if self.prompt_combo.itemData(i) == current_id:
                    self.prompt_combo.setCurrentIndex(i)
                    return
                    
        # Select first prompt if available
        if self.prompt_combo.count() > 0:
            self.prompt_combo.setCurrentIndex(0)
    
    def _prompt_selected(self, index):
        """Handle prompt selection."""
        # Get prompt ID
        prompt_id = self.prompt_combo.currentData()
        self.current_prompt_id = prompt_id
        
        if prompt_id == "custom":
            # Custom prompt
            self.current_prompt_data = {
                "name": "Custom",
                "prompt": "",
                "reminder": ""
            }
            self.prompt_edit.clear()
            self.reminder_edit.clear()
        else:
            # Load prompt data
            prompt_data = self.file_manager.get_prompt(prompt_id)
            
            if prompt_data:
                self.current_prompt_data = prompt_data
                self.prompt_edit.setText(prompt_data.get('prompt', ''))
                self.reminder_edit.setText(prompt_data.get('reminder', ''))
            else:
                self.current_prompt_data = {
                    "name": self.prompt_combo.currentText(),
                    "prompt": "",
                    "reminder": ""
                }
                self.prompt_edit.clear()
                self.reminder_edit.clear()
        
        # Emit signal
        self._emit_prompt_data()
    
    def _emit_prompt_data(self):
        """Emit current prompt data."""
        # Update with latest content from editors
        self.current_prompt_data['prompt'] = self.prompt_edit.toPlainText()
        self.current_prompt_data['reminder'] = self.reminder_edit.toPlainText()
        
        # Emit signal
        self.prompt_selected.emit(self.current_prompt_data)
    
    def _new_prompt(self):
        """Create a new prompt."""
        # Select custom option
        for i in range(self.prompt_combo.count()):
            if self.prompt_combo.itemData(i) == "custom":
                self.prompt_combo.setCurrentIndex(i)
                break
    
    def _save_prompt(self):
        """Save the current prompt."""
        if self.current_prompt_id == "custom":
            # Need to save as new
            self._save_prompt_as()
            return
            
        # Update prompt data with current content
        self.current_prompt_data['prompt'] = self.prompt_edit.toPlainText()
        self.current_prompt_data['reminder'] = self.reminder_edit.toPlainText()
        
        if not self.current_prompt_data['prompt']:
            QMessageBox.warning(
                self,
                "Empty Prompt",
                "Cannot save an empty prompt."
            )
            return
            
        # Save prompt
        success = self.file_manager.save_prompt(self.current_prompt_id, self.current_prompt_data)
        
        if success:
            QMessageBox.information(
                self,
                "Success",
                f"Prompt '{self.current_prompt_data['name']}' saved successfully."
            )
        else:
            QMessageBox.warning(
                self,
                "Save Failed",
                f"Failed to save prompt '{self.current_prompt_data['name']}'."
            )
    
    def _save_prompt_as(self):
        """Save the prompt with a new name and ID."""
        # Show dialog
        dialog = SavePromptDialog(
            self, 
            name=self.current_prompt_data.get('name', ''),
            prompt_id=self.current_prompt_id if self.current_prompt_id != "custom" else ""
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            prompt_name = dialog.get_prompt_name()
            prompt_id = dialog.get_prompt_id()
            
            if not prompt_name or not prompt_id:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Please enter both a name and ID for the prompt."
                )
                return
                
            # Update prompt data with current content
            prompt_data = {
                "name": prompt_name,
                "prompt": self.prompt_edit.toPlainText(),
                "reminder": self.reminder_edit.toPlainText()
            }
            
            if not prompt_data['prompt']:
                QMessageBox.warning(
                    self,
                    "Empty Prompt",
                    "Cannot save an empty prompt."
                )
                return
                
            # Save prompt
            success = self.file_manager.save_prompt(prompt_id, prompt_data)
            
            if success:
                # Reload prompts
                self._load_prompts()
                
                # Update current prompt
                self.current_prompt_id = prompt_id
                self.current_prompt_data = prompt_data
                
                # Select new prompt
                for i in range(self.prompt_combo.count()):
                    if self.prompt_combo.itemData(i) == prompt_id:
                        self.prompt_combo.setCurrentIndex(i)
                        break
                        
                QMessageBox.information(
                    self,
                    "Success",
                    f"Prompt saved as '{prompt_name}'."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Save Failed",
                    f"Failed to save prompt as '{prompt_name}'."
                )
    
    def _delete_prompt(self):
        """Delete the current prompt."""
        if self.current_prompt_id == "custom":
            QMessageBox.information(
                self,
                "Cannot Delete",
                "Cannot delete the 'Custom' option."
            )
            return
            
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the prompt '{self.current_prompt_data.get('name', self.current_prompt_id)}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Delete prompt
            success = self.file_manager.delete_prompt(self.current_prompt_id)
            
            if success:
                # Reload prompts
                self._load_prompts()
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Prompt '{self.current_prompt_data.get('name', self.current_prompt_id)}' deleted."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    f"Failed to delete prompt '{self.current_prompt_data.get('name', self.current_prompt_id)}'."
                )
    
    def get_prompt_data(self):
        """Get the current prompt data."""
        # Update with latest content from editors
        self.current_prompt_data['prompt'] = self.prompt_edit.toPlainText()
        self.current_prompt_data['reminder'] = self.reminder_edit.toPlainText()
        
        return self.current_prompt_data