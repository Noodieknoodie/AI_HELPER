# core/file_manager.py
import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Set, Any, Optional
import re

class FileManager:
    """Manages file operations for the AI Helper tool."""
    
    def __init__(self, project_root: str, config: Dict):
        """Initialize the file manager.
        
        Args:
            project_root: Path to the project directory.
            config: Configuration dictionary.
        """
        self.project_root = Path(project_root)
        self.excluded_dirs = set(config.get("excluded_dirs", []))
        self.core_extensions = set(config.get("core_extensions", []))
        
        # Set up AI_HELP directory
        self.ai_help_dir = self.project_root / "AI_HELP"
        self.prompts_dir = self.ai_help_dir / "prompts"
        self.outputs_dir = self.ai_help_dir / "outputs"
        
        # Create directories if they don't exist
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize default prompts if they don't exist
        self._init_default_prompts()
    
    def _init_default_prompts(self):
        """Initialize default prompts if they don't exist."""
        default_prompts = {
            "analyze_code": {
                "name": "Analyze Code",
                "prompt": "Analyze the provided code and provide a detailed assessment including:\n\n1. Overall architecture and design patterns used\n2. Key components and their responsibilities\n3. Data flow and control flow\n4. Strengths of the implementation\n5. Potential improvements or refactoring opportunities\n6. Any bugs or issues you identify\n\nFormat your response with clear headings and use markdown for improved readability.",
                "reminder": "Remember to be thorough yet concise. Focus on the most important aspects of the codebase rather than trivial details."
            },
            
            "explain": {
                "name": "Explain Code",
                "prompt": "Please explain this code in a clear, step-by-step manner. For each file:\n\n1. Describe its overall purpose\n2. Explain key functions and classes\n3. Clarify any complex algorithms or patterns\n4. Point out important logic sections\n5. Explain any non-obvious code or technical decisions\n\nYour explanation should be understandable to a junior developer who is new to this codebase.",
                "reminder": "Use clear language and avoid unnecessary jargon. Break down complex concepts into simpler parts."
            },
            
            "refactor": {
                "name": "Refactor Suggestions",
                "prompt": "Identify refactoring opportunities in this code base. For each file:\n\n1. Identify code smells or anti-patterns\n2. Suggest specific refactoring techniques\n3. Provide reasoning for why the refactoring would improve the code\n4. Consider readability, maintainability, and performance impacts\n5. If possible, show example code for how critical sections could be improved\n\nFocus on high-impact changes that would most significantly improve the quality of the codebase.",
                "reminder": "Prioritize changes that would have the biggest impact on maintainability and readability. Be specific in your suggestions and explain the rationale behind each one."
            },
            
            "review": {
                "name": "Code Review",
                "prompt": "Please perform a comprehensive code review focusing on:\n\n1. Code quality and standards compliance\n2. Potential bugs or edge cases\n3. Security vulnerabilities\n4. Performance considerations\n5. Testing gaps\n\nFor each issue, explain the problem, why it matters, and suggest a specific solution.",
                "reminder": "Be constructive in your feedback. Point out both strengths and weaknesses. Provide actionable suggestions for improvement."
            }
        }
        
        # Save default prompts if they don't exist
        for prompt_id, prompt_data in default_prompts.items():
            prompt_path = self.prompts_dir / f"{prompt_id}.json"
            if not prompt_path.exists():
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    json.dump(prompt_data, f, indent=2)
                    
        # Convert any existing text prompts to JSON format
        self._convert_text_prompts_to_json()
    
    def _convert_text_prompts_to_json(self):
        """Convert any existing text prompts to JSON format."""
        # Find all .txt files in the prompts directory
        for txt_path in self.prompts_dir.glob('*.txt'):
            # Check if a JSON version already exists
            json_path = txt_path.with_suffix('.json')
            if not json_path.exists():
                try:
                    # Read text content
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        prompt_content = f.read()
                    
                    # Create JSON structure
                    prompt_data = {
                        "name": txt_path.stem.replace('_', ' ').title(),
                        "prompt": prompt_content,
                        "reminder": ""  # Empty reminder for converted prompts
                    }
                    
                    # Save as JSON
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(prompt_data, f, indent=2)
                        
                    # Optionally, remove the original .txt file
                    # txt_path.unlink()
                except Exception as e:
                    print(f"Error converting {txt_path.name} to JSON: {str(e)}")
    
    def get_project_files(self, include_extensions: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """Get all files in the project directory matching the criteria.
        
        Args:
            include_extensions: Set of file extensions to include.
                               If None, includes all files.
        
        Returns:
            List of file information dictionaries.
        """
        files = []
        
        # Walk through project directory
        for root, dirs, filenames in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs and not d.startswith('.')]
            
            # Skip the AI_HELP directory itself
            if Path(root) == self.ai_help_dir:
                continue
            
            # Process files
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                    
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(self.project_root)
                extension = os.path.splitext(filename)[1].lower()
                
                # Skip if not in included extensions
                if include_extensions is not None and extension not in include_extensions:
                    continue
                
                # Add file info
                files.append({
                    'name': filename,
                    'path': str(rel_path),
                    'full_path': str(file_path),
                    'extension': extension,
                    'size': file_path.stat().st_size,
                    'is_core': extension in self.core_extensions
                })
        
        return files
    
    def get_unique_extensions(self, files: Optional[List[Dict[str, Any]]] = None) -> Set[str]:
        """Get unique file extensions from the project.
        
        Args:
            files: List of file information dictionaries.
                 If None, gets all project files.
                 
        Returns:
            Set of unique file extensions.
        """
        if files is None:
            files = self.get_project_files()
        
        return {file['extension'] for file in files if file['extension']}
    
    def read_file(self, path: str) -> str:
        """Read and return the content of a file.
        
        Args:
            path: Path to the file (absolute or relative to project root).
            
        Returns:
            String content of the file.
        """
        try:
            if os.path.isabs(path):
                file_path = path
            else:
                file_path = os.path.join(self.project_root, path)
                
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def compile_files(self, files: List[Dict[str, Any]], cleaning_options=None) -> str:
        """Compile content from multiple files with separators.
        
        Args:
            files: List of file information dictionaries.
            cleaning_options: Dictionary of cleaning options.
                             
        Returns:
            String with compiled file content.
        """
        if not files:
            return ""
            
        if cleaning_options is None:
            cleaning_options = {}
            
        compiled = []
        
        for file in files:
            content = self.read_file(file['full_path'])
            extension = file['extension']
            
            # Apply cleaning options
            if cleaning_options.get('remove_comments', False):
                # Simple comment removal (not perfect but works for common languages)
                if extension in ['.py', '.rb']:
                    # Remove Python/Ruby comments
                    lines = []
                    for line in content.split('\n'):
                        comment_pos = line.find('#')
                        if comment_pos >= 0:
                            line = line[:comment_pos]
                        if line.strip():
                            lines.append(line)
                    content = '\n'.join(lines)
                elif extension in ['.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.cs']:
                    # Remove C-style comments
                    # Note: This is a simplified approach
                    import re
                    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
                    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
            
            if cleaning_options.get('remove_blank_lines', False):
                content = '\n'.join(line for line in content.split('\n') if line.strip())
            
            if cleaning_options.get('remove_docstrings', False) and extension in ['.py']:
                # Simple Python docstring removal (not perfect)
                import re
                content = re.sub(r'"""[\s\S]*?"""', '', content)
                content = re.sub(r"'''[\s\S]*?'''", '', content)
            
            # Add file separator and content
            compiled.append(f"######## {file['path']} ########\n```{extension}\n{content}\n```\n")
        
        return "\n".join(compiled)
    
    def get_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Get all prompts from the prompts directory.
        
        Returns:
            Dictionary mapping prompt IDs to prompt data dictionaries.
        """
        prompts = {}
        
        # Load JSON prompts
        for file_path in self.prompts_dir.glob('*.json'):
            prompt_id = file_path.stem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                    prompts[prompt_id] = prompt_data
            except Exception as e:
                print(f"Error loading prompt {file_path}: {str(e)}")
                prompts[prompt_id] = {
                    "name": prompt_id,
                    "prompt": f"Error loading prompt: {str(e)}",
                    "reminder": ""
                }
        
        # Also load any remaining .txt files for backward compatibility
        for file_path in self.prompts_dir.glob('*.txt'):
            prompt_id = file_path.stem
            if prompt_id not in prompts:  # Only if not already loaded as JSON
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        prompt_content = f.read()
                    prompts[prompt_id] = {
                        "name": prompt_id.replace('_', ' ').title(),
                        "prompt": prompt_content,
                        "reminder": ""
                    }
                except Exception as e:
                    print(f"Error loading prompt {file_path}: {str(e)}")
        
        return prompts
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt by ID.
        
        Args:
            prompt_id: ID of the prompt.
            
        Returns:
            Prompt data dictionary or None if not found.
        """
        # Try JSON first
        json_path = self.prompts_dir / f"{prompt_id}.json"
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Fall back to text file for backward compatibility
        txt_path = self.prompts_dir / f"{prompt_id}.txt"
        if txt_path.exists():
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                return {
                    "name": prompt_id.replace('_', ' ').title(),
                    "prompt": prompt_content,
                    "reminder": ""
                }
            except Exception:
                pass
        
        return None
    
    def save_prompt(self, prompt_id: str, prompt_data: Dict[str, Any]) -> bool:
        """Save a prompt to a JSON file.
        
        Args:
            prompt_id: ID for the prompt (will be used as filename).
            prompt_data: Dictionary with prompt data (name, prompt, reminder).
            
        Returns:
            Boolean indicating success.
        """
        try:
            # Sanitize prompt ID for filename
            safe_id = re.sub(r'[^\w\-_]', '_', prompt_id.lower())
            file_path = self.prompts_dir / f"{safe_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving prompt: {str(e)}")
            return False
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt file.
        
        Args:
            prompt_id: ID of the prompt to delete.
            
        Returns:
            Boolean indicating success.
        """
        try:
            # Try to delete JSON file
            json_path = self.prompts_dir / f"{prompt_id}.json"
            if json_path.exists():
                os.remove(json_path)
                return True
            
            # Try to delete text file (backward compatibility)
            txt_path = self.prompts_dir / f"{prompt_id}.txt"
            if txt_path.exists():
                os.remove(txt_path)
                return True
                
            return False
        except Exception:
            return False
    
    def save_output(self, content, task_name):
        """Save output to a file in the outputs directory.
        
        Args:
            content: Content to save.
            task_name: Type of task (used in filename).
            
        Returns:
            Path to the saved file.
        """
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = self.project_root.name
        safe_task = re.sub(r'[^\w\-_]', '_', task_name)
        filename = f"{project_name}_{safe_task}_{timestamp}.txt"
        
        # Save file
        output_path = self.outputs_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return str(output_path)
        except Exception as e:
            print(f"Error saving output: {str(e)}")
            return None