import os
from pathlib import Path
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from .logger import logger

class ProjectFileHandler:
    def __init__(self):
        self.current_project = None
        self.project_files = {}
        self.gitignore_spec = None

    def load_gitignore(self, project_path):
        """Load and parse .gitignore file if it exists."""
        gitignore_path = os.path.join(project_path, '.gitignore')
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read().splitlines()
            self.gitignore_spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_content)
            logger.info(f"Loaded .gitignore from {gitignore_path}")
        else:
            self.gitignore_spec = None
            logger.info("No .gitignore file found")

    def is_ignored(self, file_path):
        """Check if a file should be ignored based on .gitignore rules."""
        if self.gitignore_spec is None:
            return False
        relative_path = os.path.relpath(file_path, self.current_project)
        return self.gitignore_spec.match_file(relative_path)

    def load_project(self, project_path):
        """Load a project and index its files, respecting .gitignore rules."""
        try:
            self.current_project = Path(project_path)
            self.project_files = {}
            self.load_gitignore(project_path)
            
            extensions = [
                '.py', '.js', '.jsx', '.ts', '.tsx', 
                '.css', '.scss', '.html', '.java',
                '.cpp', '.c', '.h', '.hpp', '.go',
                '.rs', '.php', '.rb', '.swift'
            ]
            
            file_count = ignored_count = 0
            
            for ext in extensions:
                for file in self.current_project.rglob(f"*{ext}"):
                    if not self.is_ignored(str(file)):
                        try:
                            content = file.read_text(encoding='utf-8')
                            self.project_files[str(file)] = content
                            file_count += 1
                        except Exception as e:
                            logger.warning(f"Could not read {file}: {str(e)}")
                    else:
                        ignored_count += 1

            return f"Loaded {file_count} files from {project_path} (ignored {ignored_count} files)"
        except Exception as e:
            logger.error(f"Error loading project: {str(e)}")
            raise
