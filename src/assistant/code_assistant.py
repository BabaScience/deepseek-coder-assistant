import os
from pathlib import Path
from ..utils.logger import logger
from ..utils.file_handler import ProjectFileHandler
from ..utils.exceptions import CodeAssistantError
from .model_handler import ModelHandler

class CodeAssistant:
    def __init__(self, model_name=None):
        self.model_handler = ModelHandler()
        self.file_handler = ProjectFileHandler()

    def load_project(self, project_path):
        return self.file_handler.load_project(project_path)

    def modify_file(self, file_path, instruction):
        if not self.file_handler.current_project:
            return "No project loaded. Use !load first."
            
        full_path = str(self.file_handler.current_project / file_path)
        if full_path not in self.file_handler.project_files:
            return f"File {file_path} not found"
            
        try:
            # Create backup before modification
            self.file_handler.backup_file(full_path)
            
            prompt = f"""
            Current file content:
            ```
            {self.file_handler.project_files[full_path]}
            ```
            
            Modification instruction: {instruction}
            
            Please provide the complete modified file content while maintaining the original structure and functionality.
            Only output the modified code without any explanations.
            """
            
            modified_content = self.model_handler.generate(prompt)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            self.file_handler.project_files[full_path] = modified_content
            self.file_handler.track_changes('modify', full_path)
            
            return f"Successfully modified {file_path}"
        except Exception as e:
            logger.error(f"Error modifying file: {str(e)}")
            # Attempt to restore from backup
            if self.file_handler.restore_backup(full_path):
                return f"Error occurred, restored from backup: {str(e)}"
            return f"Error modifying file: {str(e)}"

    def create_file(self, file_path, instruction):
        if not self.file_handler.current_project:
            return "No project loaded. Use !load first."
            
        full_path = str(self.file_handler.current_project / file_path)
        
        if os.path.exists(full_path):
            return f"File {file_path} already exists"
            
        try:
            prompt = f"""
            Create a new file with the following requirements:
            File path: {file_path}
            Requirements: {instruction}
            
            Please provide only the complete file content without any explanations.
            """
            
            new_content = self.model_handler.generate(prompt)
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.file_handler.project_files[full_path] = new_content
            self.file_handler.track_changes('create', full_path)
            
            return f"Successfully created {file_path}"
        except Exception as e:
            logger.error(f"Error creating file: {str(e)}")
            return f"Error creating file: {str(e)}"

    def generate_code(self, prompt):
        return self.model_handler.generate(prompt)

    def list_files(self):
        if not self.file_handler.current_project:
            return "No project loaded"
            
        return "\n".join(
            os.path.relpath(f, self.file_handler.current_project) 
            for f in self.file_handler.project_files.keys()
        )

    def get_project_stats(self):
        """Get project statistics"""
        if not self.file_handler.current_project:
            return "No project loaded"
        return self.file_handler.project_metadata
