# core/utils.py
import os
import json
import keyring
from pathlib import Path
from typing import Dict, Any, Optional

class ApiKeyManager:
    """Manages API keys for LLM services."""
    SERVICE_NAME = "ai_helper"
    
    @staticmethod
    def save_api_key(provider: str, api_key: str):
        """Save API key to system keyring.
        
        Args:
            provider: Provider name.
            api_key: API key to save.
        """
        keyring.set_password(ApiKeyManager.SERVICE_NAME, provider, api_key)
    
    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Get API key from system keyring.
        
        Args:
            provider: Provider name.
            
        Returns:
            API key or None if not found.
        """
        try:
            return keyring.get_password(ApiKeyManager.SERVICE_NAME, provider)
        except:
            return None
    
    @staticmethod
    def delete_api_key(provider: str):
        """Delete API key from system keyring.
        
        Args:
            provider: Provider name.
            
        Returns:
            Boolean indicating success.
        """
        try:
            keyring.delete_password(ApiKeyManager.SERVICE_NAME, provider)
            return True
        except:
            return False

def clean_code(content: str, extension: str, options: Dict[str, bool]) -> str:
    """Clean code based on options.
    
    Args:
        content: Code content to clean.
        extension: File extension.
        options: Cleaning options.
        
    Returns:
        Cleaned code.
    """
    if not options:
        return content
        
    lines = content.split('\n')
    result = []
    
    # Handle docstrings and comments
    in_docstring = False
    docstring_delimiter = None
    
    for line in lines:
        # Skip blank lines if option is enabled
        if options.get('remove_blank_lines', False) and not line.strip():
            continue
            
        # Handle Python docstrings
        if extension == '.py' and options.get('remove_docstrings', False):
            if not in_docstring:
                # Check for docstring start
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_delimiter = stripped[:3]
                    in_docstring = True
                    if stripped.endswith(docstring_delimiter) and len(stripped) > 3:
                        # Single-line docstring
                        in_docstring = False
                    continue
            else:
                # Check for docstring end
                if docstring_delimiter and line.strip().endswith(docstring_delimiter):
                    in_docstring = False
                    docstring_delimiter = None
                continue
        
        # Skip if we're in a docstring
        if in_docstring:
            continue
            
        # Handle comments
        if options.get('remove_comments', False):
            if extension in ['.py', '.rb', '.sh']:
                # Python/Ruby/Shell-style comments
                comment_pos = line.find('#')
                if comment_pos >= 0:
                    line = line[:comment_pos]
            elif extension in ['.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.cs', '.php']:
                # C-style comments
                comment_pos = line.find('//')
                if comment_pos >= 0:
                    line = line[:comment_pos]
        
        # Add line if it has content or we're not skipping blank lines
        if line.strip() or not options.get('remove_blank_lines', False):
            result.append(line)
    
    return '\n'.join(result)

def estimate_tokens(text: str) -> int:
    """Estimate token count for a text string.
    
    Args:
        text: Text to estimate tokens for.
        
    Returns:
        Estimated token count.
    """
    # Rough estimation: ~4 characters per token for English text
    return len(text) // 4

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Human-readable size string.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if size_bytes >= 100 else f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def get_file_icon_path(extension: str) -> str:
    icon_map = {
        '.py': 'file_py.png',
        '.js': 'file_js.png',
        '.jsx': 'file_jsx.png',
        '.ts': 'file_ts.png',
        '.tsx': 'file_tsx.png',
        '.html': 'file_html.png',
        '.css': 'file_css.png',
        '.json': 'file_json.png',
        '.yml': 'file_yaml.png',
        '.yaml': 'file_yaml.png',
        '.md': 'file_md.png',
        '.txt': 'file_txt.png',
        '.java': 'file_java.png',
        '.c': 'file_c.png',
        '.cpp': 'file_cpp.png',
        '.h': 'file_h.png',
        '.cs': 'file_cs.png',
        '.php': 'file_php.png',
        '.rb': 'file_rb.png',
        '.go': 'file_go.png',
        '.rs': 'file_rs.png',
        '.swift': 'file_swift.png',
        '.sql': 'file_sql.png'
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(os.path.dirname(script_dir), 'resources', 'icons')

    icon_file = icon_map.get(extension.lower(), 'file_generic.png')
    icon_path = os.path.join(resources_dir, icon_file)

    if not os.path.exists(icon_path):
        icon_path = os.path.join(resources_dir, 'file_default.png')

    return icon_path

def get_active_icon_paths():
    """Return paths to active icons needed by the application.
    
    Returns:
        Dictionary of icon paths.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(os.path.dirname(script_dir), 'resources', 'icons')
    
    return {
        'folder': os.path.join(resources_dir, 'folder.png'),
        'folder_open': os.path.join(resources_dir, 'folder_open.png'),
        'file_generic': os.path.join(resources_dir, 'file_generic.png'),
        'code': os.path.join(resources_dir, 'code.png'),
        'context': os.path.join(resources_dir, 'context.png'),
        'prompt': os.path.join(resources_dir, 'prompt.png'),
        'reminder': os.path.join(resources_dir, 'reminder.png')
    }