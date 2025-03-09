# config.py
import os
import json
from pathlib import Path

import os
import json
from pathlib import Path

# Default configuration settings
DEFAULT_CONFIG = {
    "excluded_dirs": [
        "__pycache__", ".pytest_cache", "venv", ".venv", ".env", "env",
        "virtualenv", "dist", "build", ".mypy_cache", ".coverage", ".tox",
        "node_modules", ".npm", ".yarn", ".cache", "bower_components",
        ".next", ".nuxt", ".output", "dist", "build", "coverage",
        ".git", ".hg", ".svn",
        ".vscode", ".idea", ".vs", ".cursor",
        ".DS_Store", "Thumbs.db", ".ipynb_checkpoints",
        "bin", "obj", "out", "target", "vendor", "packages", "bundle",
        "AI_HELP"
    ],
    "core_extensions": [
        ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".java", ".c", 
        ".cpp", ".h", ".hpp", ".cs", ".php", ".rb", ".go", ".rs", ".swift",
        ".json", ".yaml", ".yml", ".xml", ".sql",
        ".txt", ".md", ".rst", ".markdown"
    ],
    "api": {
        "anthropic": {
            "url": "https://api.anthropic.com/v1/messages",
            "models": [
                {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
                {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
                {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
                {"id": "claude-3-7-sonnet-20250219", "name": "Claude 3.7 Sonnet"}
            ],
            "default_model": "claude-3-7-sonnet-20250219"
        },
        "openai": {
            "url": "https://api.openai.com/v1/chat/completions",
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o"},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
                {"id": "gpt-4", "name": "GPT-4"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
            ],
            "default_model": "gpt-4o"
        }
    },
    "default_api": "anthropic",
    "ui": {
        "theme": {
            "primary": "#0A84FF",
            "secondary": "#00B889",
            "code": "#FF9500",
            "context": "#4682B4",
            "prompt": "#F6F8FA",
            "reminder": "#F0FFF0",
            "background": "#F5F7F9",
            "foreground": "#2C3E50",
            "surface": "#FFFFFF",
            "border": "#E1E4E8",
            "error": "#E63946",
            "success": "#2ECC71"
        },
        "font": {
            "size": {
                "small": 9,
                "normal": 10,
                "large": 12,
                "header": 14
            }
        }
    }
}

def get_config_path(project_root):
    """Get the path to the config file."""
    ai_help_dir = os.path.join(project_root, "AI_HELP")
    return os.path.join(ai_help_dir, "config.json")

def init_config(project_root):
    """Initialize the configuration."""
    config = DEFAULT_CONFIG.copy()
    config["project_root"] = str(project_root)
    
    # Create folders if they don't exist
    ai_help_dir = os.path.join(project_root, "AI_HELP")
    os.makedirs(os.path.join(ai_help_dir, "prompts"), exist_ok=True)
    os.makedirs(os.path.join(ai_help_dir, "outputs"), exist_ok=True)
    
    # Create resources and icons directory
    resources_dir = os.path.join(ai_help_dir, "resources", "icons")
    os.makedirs(resources_dir, exist_ok=True)
    
    # Try to load existing config
    config_path = get_config_path(project_root)
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                # Merge loaded config with defaults (preserving new default fields)
                merge_configs(config, loaded_config)
    except Exception:
        # If loading fails, use default config
        pass
    
    # Save config (ensures any new default fields are written to file)
    save_config(project_root, config)
    
    return config

def save_config(project_root, config):
    """Save the configuration to file."""
    config_path = get_config_path(project_root)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def merge_configs(default_config, loaded_config):
    """Merge loaded config with default config, preserving new default fields."""
    for key, value in loaded_config.items():
        if isinstance(value, dict) and key in default_config and isinstance(default_config[key], dict):
            merge_configs(default_config[key], value)
        else:
            default_config[key] = value