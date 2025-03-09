# core/api_keys.py
import os
import dotenv
from pathlib import Path

def get_env_file_path(config):
    """Get the path to the .env file in the project directory."""
    project_root = config["project_root"]
    return os.path.join(project_root, ".env")

def load_keys(config):
    """Load API keys from .env file."""
    env_path = get_env_file_path(config)
    
    if os.path.exists(env_path):
        # Load environment variables from .env file
        dotenv.load_dotenv(env_path)
    
    # Return dictionary of provider keys
    return {
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
        "openai": os.environ.get("OPENAI_API_KEY", ""),
        "gemini": os.environ.get("GEMINI_API_KEY", "")
    }

def save_key(config, provider, api_key):
    """Save API key to .env file."""
    env_path = get_env_file_path(config)
    
    # Create mapping of provider names to env var names
    env_vars = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY"
    }
    
    # Get env var name for this provider
    env_var = env_vars.get(provider)
    if not env_var:
        return False
    
    # Load existing variables
    env_vars_dict = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars_dict[key] = value
    
    # Update or add new key
    env_vars_dict[env_var] = api_key
    
    # Write back to file
    with open(env_path, 'w') as f:
        for key, value in env_vars_dict.items():
            f.write(f"{key}={value}\n")
    
    # Update environment variable in current process
    os.environ[env_var] = api_key
    
    return True