# gui/main_window.py
import os
import sys
import json
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget, QMessageBox, QDialog,
    QDialogButtonBox, QLabel, QLineEdit, QFormLayout,
    QComboBox, QStatusBar, QFileDialog, QProgressBar,
    QGroupBox, QCheckBox, QSlider, QSpinBox, QFrame, QGridLayout, QPushButton, QApplication)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QFont, QActionGroup

from core.file_manager import FileManager
from core.llm_service import LLMService
from core.utils import ApiKeyManager
from gui.style import Style
from gui.file_panel import FilePanel
from gui.prompt_panel import PromptPanel
from gui.message_panel import MessagePanel
from gui.output_panel import OutputPanel

class ApiKeyDialog(QDialog):
    """Dialog for entering API keys."""
    
    def __init__(self, parent=None, config=None, service_name=None, available_services=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("API Key Configuration")
        self.setMinimumWidth(400)
        
        # Set up layout
        layout = QVBoxLayout(self)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        
        # Service selection
        self.service_combo = QComboBox()
        for service in available_services or []:
            self.service_combo.addItem(service.capitalize(), service)
        
        # Set initial service if provided
        if service_name and available_services:
            for i in range(self.service_combo.count()):
                if self.service_combo.itemData(i) == service_name:
                    self.service_combo.setCurrentIndex(i)
                    break
        
        form_layout.addRow("Service:", self.service_combo)
        
        # API key input
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter API key")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API Key:", self.api_key_edit)
        
        layout.addLayout(form_layout)
        
        # Show key checkbox
        self.show_key_check = QCheckBox("Show API Key")
        self.show_key_check.stateChanged.connect(self._toggle_key_visibility)
        layout.addWidget(self.show_key_check)
        
        # Load current key
        self.update_button = QPushButton("Load Current Key")
        self.update_button.clicked.connect(self.load_current_key)
        layout.addWidget(self.update_button)
        
        # Note about .env file
        env_path = os.path.join(self.config["project_root"], ".env")
        note_label = QLabel(f"Keys are stored in: {env_path}")
        note_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(note_label)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _toggle_key_visibility(self, state):
        """Toggle visibility of API key."""
        if state == Qt.CheckState.Checked:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def load_current_key(self):
        """Load the current API key for the selected service."""
        service_name = self.service_combo.currentData()
        api_key = ApiKeyManager.get_api_key(self.config, service_name)
        if api_key:
            self.api_key_edit.setText(api_key)
            self.api_key_edit.setPlaceholderText("")
        else:
            self.api_key_edit.clear()
            self.api_key_edit.setPlaceholderText("No API key stored for this service")
    
    def get_service_name(self):
        """Get the selected service name."""
        return self.service_combo.currentData()
    
    def get_api_key(self):
        """Get the entered API key."""
        return self.api_key_edit.text()

class LLMWorker(QThread):
    """Worker thread for LLM API requests."""
    
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, llm_service, prompt):
        super().__init__()
        self.llm_service = llm_service
        self.prompt = prompt
    
    def run(self):
        """Run the LLM request."""
        response = self.llm_service.send_request(self.prompt, self.progress.emit)
        self.finished.emit(response)

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, config):
        super().__init__()
        
        # Initialize core components
        self.config = config
        self.file_manager = FileManager(config["project_root"], config)
        
        # Initialize GUI
        self._setup_ui()
        
        # Initialize LLM service (without API key initially)
        self.llm_service = LLMService(config)
        
        # Try to load API key
        api_key = ApiKeyManager.get_api_key(self.config, self.llm_service.api_provider)
        if api_key:
            self.llm_service.set_api_key(api_key)
        else:
            # Prompt for API key if none is found
            QMessageBox.information(
                self,
                "API Key Required",
                "Please configure your API key to use AI features."
            )
            self._configure_api_key()
        
        # Initialize worker thread
        self.llm_thread = None
        
        # Set status bar
        self.statusBar().showMessage(f"Project: {os.path.basename(config['project_root'])} - Ready")
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Set window properties
        self.setWindowTitle("AI Helper")
        self.setMinimumSize(1200, 800)
        
        # Apply style
        Style.apply_application_style(QApplication.instance())
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Create file panel
        self.file_panel = FilePanel(self.file_manager, self.config)
        self.main_splitter.addWidget(self.file_panel)
        
        # Create right side panel with vertical splitter
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Create prompt panel
        self.prompt_panel = PromptPanel(self.file_manager)
        self.right_splitter.addWidget(self.prompt_panel)
        
        # Create message panel
        self.message_panel = MessagePanel()
        self.right_splitter.addWidget(self.message_panel)
        
        # Create output panel
        self.output_panel = OutputPanel(self.file_manager)
        self.right_splitter.addWidget(self.output_panel)
        
        # Set splitter proportions
        self.right_splitter.setSizes([200, 400, 200])  # Height proportions for panels
        
        # Add right panel to main splitter
        self.main_splitter.addWidget(self.right_splitter)
        
        # Set split proportions (40% for file panel, 60% for right panel)
        self.main_splitter.setSizes([400, 800])
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
        # Set up signals
        self._connect_signals()
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        set_project_action = QAction("Set Project Directory", self)
        set_project_action.triggered.connect(self._select_project)
        file_menu.addAction(set_project_action)
        
        save_output_action = QAction("Save Output", self)
        save_output_action.triggered.connect(self._save_output)
        file_menu.addAction(save_output_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        
        api_key_action = QAction("Configure API Key", self)
        api_key_action.triggered.connect(self._configure_api_key)
        settings_menu.addAction(api_key_action)
        
        model_settings_action = QAction("Model Settings", self)
        model_settings_action.triggered.connect(self._show_model_settings)
        settings_menu.addAction(model_settings_action)
        
        # Add provider submenu
        provider_menu = settings_menu.addMenu("API Provider")
        
        # Will populate this dynamically once LLM service is initialized
        self.provider_actions = {}
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Connect signals between components."""
        # File panel to message panel
        self.file_panel.files_selected.connect(self.message_panel.update_files)
        
        # Prompt panel to message panel
        self.prompt_panel.prompt_selected.connect(self.message_panel.set_prompt)
    
    def _populate_provider_menu(self):
        """Populate the provider submenu."""
        if not hasattr(self, 'llm_service'):
            return
            
        # Get parent menu
        settings_menu = self.menuBar().actions()[1].menu()
        provider_menu = settings_menu.actions()[2].menu()
        
        # Clear existing actions
        provider_menu.clear()
        self.provider_actions = {}
        
        # Add provider actions
        providers = self.llm_service.get_available_providers()
        provider_group = QActionGroup(self)
        provider_group.setExclusive(True)
        
        for provider in providers:
            action = QAction(provider.capitalize(), self, checkable=True)
            action.setChecked(provider == self.llm_service.api_provider)
            action.setData(provider)
            
            # Connect to handler
            action.triggered.connect(lambda checked, p=provider: self._set_provider(p))
            
            provider_group.addAction(action)
            provider_menu.addAction(action)
            self.provider_actions[provider] = action
    
    def _select_project(self):
        """Handle project directory selection."""
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if directory:
            # Update config
            self.config["project_root"] = directory
            
            # Reinitialize file manager
            self.file_manager = FileManager(directory, self.config)
            
            # Update file panel
            self.file_panel.set_file_manager(self.file_manager)
            
            # Update prompt panel
            self.prompt_panel.set_file_manager(self.file_manager)
            
            # Update output panel
            self.output_panel.set_file_manager(self.file_manager)
            
            # Update status bar
            self.statusBar().showMessage(f"Project: {os.path.basename(directory)} - Ready")
    
    def _configure_api_key(self):
        """Configure API key."""
        if not hasattr(self, 'llm_service'):
            return
            
        dialog = ApiKeyDialog(
            self,
            self.config,
            self.llm_service.api_provider,
            self.llm_service.get_available_providers()
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            service_name = dialog.get_service_name()
            api_key = dialog.get_api_key()
            
            if api_key:
                # Save API key
                ApiKeyManager.save_api_key(self.config, service_name, api_key)
                
                # Update LLM service
                if service_name != self.llm_service.api_provider:
                    self.llm_service.set_provider(service_name)
                    
                    # Update provider menu
                    if service_name in self.provider_actions:
                        self.provider_actions[service_name].setChecked(True)
                
                self.llm_service.set_api_key(api_key)
                
                self.statusBar().showMessage(f"API key saved for {service_name}")
    
    def _show_model_settings(self):
        """Show dialog for model-specific settings."""
        if not hasattr(self, 'llm_service') or not self.llm_service.api_key:
            QMessageBox.warning(self, "Warning", "No API key configured. Please configure API key first.")
            self._configure_api_key()
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Model Settings")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Get model info
        model_caps = self.llm_service._get_model_capabilities()
        model_name = "Unknown Model"
        for model in self.llm_service.api_config.get("models", []):
            if model.get("id") == self.llm_service.model_id:
                model_name = model.get("name", "Unknown Model")
                break
        
        # Model information header
        info_layout = QGridLayout()
        
        provider_label = QLabel("Provider:")
        provider_value = QLabel(self.llm_service.api_provider.capitalize())
        provider_value.setStyleSheet("font-weight: bold;")
        
        model_label = QLabel("Model:")
        model_value = QLabel(model_name)
        model_value.setStyleSheet("font-weight: bold;")
        
        context_label = QLabel("Context Window:")
        context_value = QLabel(f"{model_caps.get('context_window', 'Unknown'):,} tokens")
        
        info_layout.addWidget(provider_label, 0, 0)
        info_layout.addWidget(provider_value, 0, 1)
        info_layout.addWidget(model_label, 1, 0)
        info_layout.addWidget(model_value, 1, 1)
        info_layout.addWidget(context_label, 2, 0)
        info_layout.addWidget(context_value, 2, 1)
        
        layout.addLayout(info_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Provider-specific settings
        if self.llm_service.api_provider == "anthropic":
            # Extended thinking settings (only if supported)
            if model_caps.get("supports_extended_thinking", False):
                thinking_group = QGroupBox("Extended Thinking")
                thinking_layout = QVBoxLayout()
                
                thinking_check = QCheckBox("Enable Extended Thinking")
                thinking_check.setChecked(getattr(self.llm_service, 'use_extended_thinking', False))
                thinking_layout.addWidget(thinking_check)
                
                # Budget slider
                budget_layout = QHBoxLayout()
                budget_layout.addWidget(QLabel("Token Budget:"))
                
                budget_slider = QSlider(Qt.Orientation.Horizontal)
                budget_slider.setMinimum(4000)
                budget_slider.setMaximum(int(model_caps.get("max_tokens_extended", 64000)))
                budget_slider.setValue(getattr(self.llm_service, 'extended_thinking_budget', 16000))
                budget_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
                budget_slider.setTickInterval(10000)
                
                budget_label = QLabel(f"{budget_slider.value():,}")
                budget_slider.valueChanged.connect(lambda v: budget_label.setText(f"{v:,}"))
                
                budget_layout.addWidget(budget_slider)
                budget_layout.addWidget(budget_label)
                
                thinking_layout.addLayout(budget_layout)
                thinking_layout.addWidget(QLabel("Extended thinking enables Claude to reason more thoroughly."))
                
                thinking_group.setLayout(thinking_layout)
                layout.addWidget(thinking_group)
        
        elif self.llm_service.api_provider == "openai":
            # Reasoning settings (only if supported)
            if model_caps.get("supports_reasoning", False):
                reasoning_group = QGroupBox("Reasoning Settings")
                reasoning_layout = QVBoxLayout()
                
                # Reasoning effort
                effort_layout = QHBoxLayout()
                effort_layout.addWidget(QLabel("Reasoning Effort:"))
                
                effort_combo = QComboBox()
                effort_combo.addItems(["low", "medium", "high"])
                
                # Set current value
                current_effort = getattr(self.llm_service, 'reasoning_effort', 'medium')
                index = effort_combo.findText(current_effort)
                if index >= 0:
                    effort_combo.setCurrentIndex(index)
                
                effort_layout.addWidget(effort_combo)
                reasoning_layout.addLayout(effort_layout)
                
                reasoning_layout.addWidget(QLabel("Low: Faster responses with less thinking"))
                reasoning_layout.addWidget(QLabel("Medium: Balanced approach (default)"))
                reasoning_layout.addWidget(QLabel("High: More thorough thinking, more tokens used"))
                
                reasoning_group.setLayout(reasoning_layout)
                layout.addWidget(reasoning_group)
        
        elif self.llm_service.api_provider == "gemini":
            # Thinking settings (only if supported)
            if model_caps.get("supports_thinking", False):
                thinking_group = QGroupBox("Thinking")
                thinking_layout = QVBoxLayout()
                
                thinking_check = QCheckBox("Enable Thinking")
                thinking_check.setChecked(getattr(self.llm_service, 'use_thinking', False))
                thinking_layout.addWidget(thinking_check)
                
                thinking_layout.addWidget(QLabel("Thinking enables Gemini to reason through complex problems step by step."))
                
                thinking_group.setLayout(thinking_layout)
                layout.addWidget(thinking_group)
        
        # Common settings for all models
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        # Max tokens
        tokens_layout = QHBoxLayout()
        tokens_layout.addWidget(QLabel("Max Tokens:"))
        
        max_tokens_input = QSpinBox()
        max_tokens_input.setMinimum(100)
        max_tokens_input.setMaximum(100000)  # Default high maximum
        
        # Set maximum based on model capabilities
        if self.llm_service.api_provider == "anthropic":
            if model_caps.get("supports_long_output", False):
                max_tokens_input.setMaximum(int(model_caps.get("max_output_tokens", 128000)))
            else:
                max_tokens_input.setMaximum(int(model_caps.get("max_tokens_default", 8192)))
        elif self.llm_service.api_provider == "openai":
            if model_caps.get("supports_reasoning", False):
                max_tokens_input.setMaximum(int(model_caps.get("max_completion_tokens", 100000)))
            else:
                max_tokens_input.setMaximum(int(model_caps.get("max_tokens_default", 16384)))
        elif self.llm_service.api_provider == "gemini":
            max_tokens_input.setMaximum(int(model_caps.get("output_token_limit", 8192)))
        
        # Set current value based on provider
        if self.llm_service.api_provider == "gemini":
            max_tokens_input.setValue(self.llm_service.parameters.get("max_output_tokens", 4000))
        else:
            max_tokens_input.setValue(self.llm_service.parameters.get("max_tokens", 4000))
        
        max_tokens_input.setSingleStep(1000)
        
        tokens_layout.addWidget(max_tokens_input)
        output_layout.addLayout(tokens_layout)
        
        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        
        temp_slider = QSlider(Qt.Orientation.Horizontal)
        temp_slider.setMinimum(0)
        temp_slider.setMaximum(200)  # 0-2 range (will divide by 100)
        temp_slider.setValue(int(self.llm_service.parameters.get("temperature", 0.7) * 100))
        temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        temp_slider.setTickInterval(25)
        
        temp_value = QLabel(f"{temp_slider.value() / 100:.2f}")
        temp_slider.valueChanged.connect(lambda v: temp_value.setText(f"{v / 100:.2f}"))
        
        temp_layout.addWidget(temp_slider)
        temp_layout.addWidget(temp_value)
        
        output_layout.addLayout(temp_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save settings based on provider
            if self.llm_service.api_provider == "anthropic":
                if model_caps.get("supports_extended_thinking", False):
                    self.llm_service.set_extended_thinking(
                        thinking_check.isChecked(),
                        budget_slider.value()
                    )
            
            elif self.llm_service.api_provider == "openai":
                if model_caps.get("supports_reasoning", False):
                    self.llm_service.set_reasoning_effort(effort_combo.currentText())
            
            elif self.llm_service.api_provider == "gemini":
                if model_caps.get("supports_thinking", False):
                    self.llm_service.set_thinking(thinking_check.isChecked())
            
            # Common settings
            if self.llm_service.api_provider == "gemini":
                self.llm_service.set_parameter("max_output_tokens", max_tokens_input.value())
            else:
                self.llm_service.set_parameter("max_tokens", max_tokens_input.value())
            
            self.llm_service.set_parameter("temperature", temp_slider.value() / 100)
            
            self.statusBar().showMessage(f"Model settings updated")
    
    def _check_gemini_dependencies(self):
        """Check if Gemini dependencies are installed."""
        try:
            import google.generativeai
            return True
        except ImportError:
            result = QMessageBox.question(
                self,
                "Missing Dependencies",
                "The Google Generative AI package is required for Gemini models.\n"
                "Would you like to install it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if result == QMessageBox.StandardButton.Yes:
                try:
                    import subprocess
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
                    QMessageBox.information(
                        self,
                        "Success",
                        "google-generativeai has been installed successfully."
                    )
                    return True
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Installation Failed",
                        f"Failed to install dependencies: {str(e)}\n\n"
                        "Please try installing manually with:\n"
                        "pip install google-generativeai"
                    )
                    return False
            return False
    
    def _set_provider(self, provider):
        """Set the current API provider."""
        # Check dependencies for Gemini
        if provider == "gemini" and not self._check_gemini_dependencies():
            return
        
        if self.llm_service.set_provider(provider):
            # Try to load API key for this provider
            api_key = ApiKeyManager.get_api_key(self.config, provider)
            if api_key:
                self.llm_service.set_api_key(api_key)
                self.statusBar().showMessage(f"Switched to {provider}")
            else:
                # Prompt for API key
                self._configure_api_key()
    
    def _save_output(self):
        """Save current output to file."""
        response_text = self.output_panel.get_response_text()
        if not response_text:
            QMessageBox.warning(self, "Warning", "No output to save.")
            return
            
        # Save output
        output_path = self.file_manager.save_output(response_text, "manual_save")
        
        if output_path:
            QMessageBox.information(
                self,
                "Success",
                f"Output saved to:\n{output_path}"
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to save output.")
    
    def _run_combine_ai(self):
        """Run the 'COMBINE + AI' operation."""
        if not hasattr(self, 'llm_service') or not self.llm_service.api_key:
            QMessageBox.warning(self, "Warning", "No API key configured. Please configure API key first.")
            self._configure_api_key()
            return
            
        # Get message from message panel
        message = self.message_panel.get_assembled_message()
        if not message:
            QMessageBox.warning(self, "Warning", "No message to send. Please configure your message first.")
            return
            
        # Set up UI for processing
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.statusBar().showMessage("Sending request to AI...")
        
        # Run in thread
        self.llm_thread = LLMWorker(self.llm_service, message)
        self.llm_thread.progress.connect(self.progress_bar.setValue)
        self.llm_thread.finished.connect(self._handle_llm_response)
        self.llm_thread.start()
    
    def _handle_llm_response(self, response):
        """Handle LLM response."""
        # Reset UI
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("AI response received")
        
        # Show response
        self.output_panel.set_response(response)
        
        # Format and save output
        output_options = self.output_panel.get_output_options()
        assembled_message = self.message_panel.get_assembled_message(substitute_files=False)
        files = self.file_panel.get_selected_files()
        
        output_content = self.output_panel.format_output(
            response, 
            assembled_message,
            files.get('code', []),
            files.get('context', []),
            output_options
        )
        
        # Save output
        output_path = self.file_manager.save_output(output_content, "ai_analysis")
        
        if output_path:
            self.statusBar().showMessage(f"Response saved to {output_path}")
            
            # Show notification
            QMessageBox.information(
                self,
                "Success",
                f"AI response saved to:\n{output_path}"
            )
        else:
            self.statusBar().showMessage("Error saving response")
    
    def _run_code_combine(self):
        """Run the 'CODE COMBINE' operation."""
        # Get selected files
        files = self.file_panel.get_selected_files()
        
        if not files.get('code') and not files.get('context'):
            QMessageBox.warning(self, "Warning", "No files selected.")
            return
            
        # Format output without AI response
        output_options = self.output_panel.get_output_options()
        assembled_message = self.message_panel.get_assembled_message(substitute_files=False)
        
        output_content = self.output_panel.format_output(
            "", 
            assembled_message,
            files.get('code', []),
            files.get('context', []),
            output_options
        )
        
        # Save output
        output_path = self.file_manager.save_output(output_content, "code_combine")
        
        if output_path:
            self.statusBar().showMessage(f"Code combined and saved to {output_path}")
            
            # Show notification
            QMessageBox.information(
                self,
                "Success",
                f"Combined code saved to:\n{output_path}"
            )
        else:
            self.statusBar().showMessage("Error saving combined code")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About AI Helper",
            "AI Helper v1.0\n\nA tool for analyzing code projects with AI assistance.\n\nBuilt with PyQt6."
        )
    
    def showEvent(self, event):
        """Handle window show event."""
        super().showEvent(event)
        
        # Populate provider menu after service is initialized
        if hasattr(self, 'llm_service'):
            self._populate_provider_menu()