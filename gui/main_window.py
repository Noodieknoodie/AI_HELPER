# gui/main_window.py
import os
import sys
import json
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget, QMessageBox, QDialog,
    QDialogButtonBox, QLabel, QLineEdit, QFormLayout,
    QComboBox, QStatusBar, QFileDialog, QProgressBar, QGroupBox, QSlider, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QFont

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
    
    def __init__(self, parent=None, service_name=None, available_services=None):
        super().__init__(parent)
        self.setWindowTitle("API Key Configuration")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.service_combo = QComboBox()
        for service in available_services or []:
            self.service_combo.addItem(service.capitalize(), service)
        
        if service_name and available_services:
            for i in range(self.service_combo.count()):
                if self.service_combo.itemData(i) == service_name:
                    self.service_combo.setCurrentIndex(i)
                    break
        
        form_layout.addRow("Service:", self.service_combo)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter API key")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API Key:", self.api_key_edit)
        
        layout.addLayout(form_layout)
        
        self.update_button = QPushButton("Load Current Key")
        self.update_button.clicked.connect(self.load_current_key)
        layout.addWidget(self.update_button)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_current_key(self):
        service_name = self.service_combo.currentData()
        api_key = ApiKeyManager.get_api_key(service_name)
        if api_key:
            self.api_key_edit.setText(api_key)
            self.api_key_edit.setPlaceholderText("")
        else:
            self.api_key_edit.clear()
            self.api_key_edit.setPlaceholderText("No API key stored for this service")
    
    def get_service_name(self):
        return self.service_combo.currentData()
    
    def get_api_key(self):
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
        response = self.llm_service.send_request(self.prompt, self.progress.emit)
        self.finished.emit(response)

class ModelSettingsDialog(QDialog):
    """Dialog for configuring model-specific settings."""
    
    def __init__(self, parent=None, llm_service=None):
        super().__init__(parent)
        self.setWindowTitle("Model Settings")
        self.setMinimumWidth(400)
        self.llm_service = llm_service
        
        layout = QVBoxLayout(self)
        model_caps = self.llm_service._get_model_capabilities()
        model_name = "Unknown Model"
        for model in self.llm_service.api_config.get("models", []):
            if model.get("id") == self.llm_service.model_id:
                model_name = model.get("name", "Unknown Model")
                break
        
        info_label = QLabel(f"Settings for {model_name}")
        info_label.setFont(QFont(info_label.font().family(), 12, QFont.Weight.Bold))
        layout.addWidget(info_label)
        
        self.thinking_group = QGroupBox("Extended Thinking")
        thinking_layout = QVBoxLayout()
        
        supports_thinking = model_caps.get("supports_extended_thinking", False)
        if supports_thinking:
            self.thinking_check = QCheckBox("Enable Extended Thinking")
            self.thinking_check.setChecked(self.llm_service.use_extended_thinking)
            thinking_layout.addWidget(self.thinking_check)
            
            budget_layout = QHBoxLayout()
            budget_layout.addWidget(QLabel("Token Budget:"))
            
            self.budget_slider = QSlider(Qt.Orientation.Horizontal)
            self.budget_slider.setMinimum(1000)
            self.budget_slider.setMaximum(int(model_caps.get("max_tokens_extended", 16000)))
            self.budget_slider.setValue(self.llm_service.extended_thinking_budget)
            self.budget_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.budget_slider.setTickInterval(5000)
            
            self.budget_label = QLabel(f"{self.budget_slider.value()}")
            self.budget_slider.valueChanged.connect(lambda v: self.budget_label.setText(f"{v}"))
            
            budget_layout.addWidget(self.budget_slider)
            budget_layout.addWidget(self.budget_label)
            
            thinking_layout.addLayout(budget_layout)
        else:
            thinking_layout.addWidget(QLabel("The current model does not support extended thinking."))
        
        self.thinking_group.setLayout(thinking_layout)
        layout.addWidget(self.thinking_group)
        
        self.output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        max_tokens_label = QLabel("Max Output Tokens:")
        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setMinimum(100)
        
        if model_caps.get("supports_long_output", False):
            self.max_tokens_input.setMaximum(int(model_caps.get("max_output_tokens", 128000)))
        else:
            self.max_tokens_input.setMaximum(int(model_caps.get("max_tokens_default", 8192)))
        
        self.max_tokens_input.setValue(self.llm_service.parameters.get("max_tokens", 4000))
        self.max_tokens_input.setSingleStep(1000)
        
        max_tokens_layout = QHBoxLayout()
        max_tokens_layout.addWidget(max_tokens_label)
        max_tokens_layout.addWidget(self.max_tokens_input)
        
        output_layout.addLayout(max_tokens_layout)
        
        temp_label = QLabel("Temperature:")
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(100)
        self.temp_slider.setValue(int(self.llm_service.parameters.get("temperature", 0.7) * 100))
        self.temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temp_slider.setTickInterval(10)
        
        self.temp_value = QLabel(f"{self.temp_slider.value()/100}")
        self.temp_slider.valueChanged.connect(lambda v: self.temp_value.setText(f"{v/100}"))
        
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_value)
        
        output_layout.addLayout(temp_layout)
        
        self.output_group.setLayout(output_layout)
        layout.addWidget(self.output_group)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def save_settings(self):
        if self.llm_service:
            model_caps = self.llm_service._get_model_capabilities()
            if model_caps.get("supports_extended_thinking", False):
                self.llm_service.set_extended_thinking(
                    self.thinking_check.isChecked(),
                    self.budget_slider.value()
                )
            self.llm_service.set_parameter("max_tokens", self.max_tokens_input.value())
            self.llm_service.set_parameter("temperature", self.temp_slider.value() / 100)

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
        api_key = ApiKeyManager.get_api_key(self.llm_service.api_provider)
        if api_key:
            self.llm_service.set_api_key(api_key)
        else:
            QMessageBox.information(
                self,
                "API Key Required",
                "Please configure your API key to use AI features."
            )
            self._configure_api_key()
        
        self.llm_thread = None
        self.statusBar().showMessage(f"Project: {os.path.basename(config['project_root'])} - Ready")
    
    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("AI Helper")
        self.setMinimumSize(1200, 800)
        Style.apply_application_style(QApplication.instance())
        
        self._create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        self.file_panel = FilePanel(self.file_manager, self.config)
        self.main_splitter.addWidget(self.file_panel)
        
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.prompt_panel = PromptPanel(self.file_manager)
        self.right_splitter.addWidget(self.prompt_panel)
        
        self.message_panel = MessagePanel()
        self.right_splitter.addWidget(self.message_panel)
        
        self.output_panel = OutputPanel(self.file_manager)
        self.right_splitter.addWidget(self.output_panel)
        
        self.right_splitter.setSizes([200, 400, 200])
        
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([400, 800])
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
        self._connect_signals()
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()
        
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
        
        settings_menu = menu_bar.addMenu("Settings")
        
        api_key_action = QAction("Configure API Key", self)
        api_key_action.triggered.connect(self._configure_api_key)
        settings_menu.addAction(api_key_action)
        
        model_settings_action = QAction("Model Settings", self)
        model_settings_action.triggered.connect(self._show_model_settings)
        settings_menu.addAction(model_settings_action)
        
        provider_menu = settings_menu.addMenu("API Provider")
        self.provider_actions = {}
        
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Connect signals between components."""
        self.file_panel.files_selected.connect(self.message_panel.update_files)
        self.prompt_panel.prompt_selected.connect(self.message_panel.set_prompt)
    
    def _populate_provider_menu(self):
        """Populate the provider submenu."""
        if not hasattr(self, 'llm_service'):
            return
            
        settings_menu = self.menuBar().actions()[1].menu()
        provider_menu = settings_menu.actions()[1].menu()
        
        provider_menu.clear()
        self.provider_actions = {}
        
        providers = self.llm_service.get_available_providers()
        provider_group = QActionGroup(self)
        provider_group.setExclusive(True)
        
        for provider in providers:
            action = QAction(provider.capitalize(), self, checkable=True)
            action.setChecked(provider == self.llm_service.api_provider)
            action.setData(provider)
            
            action.triggered.connect(lambda checked, p=provider: self._set_provider(p))
            
            provider_group.addAction(action)
            provider_menu.addAction(action)
            self.provider_actions[provider] = action
    
    def _select_project(self):
        """Handle project directory selection."""
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if directory:
            self.config["project_root"] = directory
            self.file_manager = FileManager(directory, self.config)
            
            self.file_panel.set_file_manager(self.file_manager)
            self.prompt_panel.set_file_manager(self.file_manager)
            self.output_panel.set_file_manager(self.file_manager)
            
            self.statusBar().showMessage(f"Project: {os.path.basename(directory)} - Ready")
    
    def _configure_api_key(self):
        """Configure API key."""
        if not hasattr(self, 'llm_service'):
            return
            
        dialog = ApiKeyDialog(
            self,
            self.llm_service.api_provider,
            self.llm_service.get_available_providers()
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            service_name = dialog.get_service_name()
            api_key = dialog.get_api_key()
            
            if api_key:
                ApiKeyManager.save_api_key(service_name, api_key)
                
                if service_name != self.llm_service.api_provider:
                    self.llm_service.set_provider(service_name)
                    
                    if service_name in self.provider_actions:
                        self.provider_actions[service_name].setChecked(True)
                
                self.llm_service.set_api_key(api_key)
                
                self.statusBar().showMessage(f"API key saved for {service_name}")
    
    def _set_provider(self, provider):
        """Set the current API provider."""
        if self.llm_service.set_provider(provider):
            api_key = ApiKeyManager.get_api_key(provider)
            if api_key:
                self.llm_service.set_api_key(api_key)
                self.statusBar().showMessage(f"Switched to {provider}")
            else:
                self._configure_api_key()
    
    def _save_output(self):
        """Save current output to file."""
        response_text = self.output_panel.get_response_text()
        if not response_text:
            QMessageBox.warning(self, "Warning", "No output to save.")
            return
            
        output_path = self.file_manager.save_output(response_text, "manual_save")
        
        if output_path:
            QMessageBox.information(
                self,
                "Success",
                f"Output saved to:\n{output_path}"
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to save output.")
    
    def _show_model_settings(self):
        """Show dialog for model-specific settings."""
        if not hasattr(self, 'llm_service') or not self.llm_service.api_key:
            QMessageBox.warning(self, "Warning", "No API key configured. Please configure API key first.")
            self._configure_api_key()
            return
        
        dialog = ModelSettingsDialog(self, self.llm_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.save_settings()
            self.statusBar().showMessage(f"Model settings updated")

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
        
        if hasattr(self, 'llm_service'):
            self._populate_provider_menu()

