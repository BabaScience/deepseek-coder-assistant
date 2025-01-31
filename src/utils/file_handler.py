import os
import time
import shutil
import yaml
from pathlib import Path
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from .logger import logger
from .exceptions import ProjectLoadError, FileOperationError

class ProjectFileHandler:
    def __init__(self):
        self.current_project = None
        self.project_files = {}
        self.gitignore_spec = None
        self.project_metadata = {}
        self.config = self.load_config()
        self.changes = []
        
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


    def load_config(self):
        """Load assistant configuration"""
        config_path = Path.home() / '.code_assistant' / 'config.yaml'
        default_config = {
            'backup_enabled': True,
            'max_file_size': 10_000_000,  # 10MB
            'excluded_binary': ['.pyc', '.exe', '.dll', '.so', '.dylib'],
            'backup_count': 5
        }
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        return default_config

    def backup_file(self, file_path):
        """Create backup before modifications"""
        if not self.config['backup_enabled']:
            return
            
        try:
            backup_dir = self.current_project / '.backups'
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"{Path(file_path).name}.{int(time.time())}.bak"
            shutil.copy2(file_path, backup_path)
            
            # Clean old backups
            backups = list(backup_dir.glob(f"{Path(file_path).name}.*.bak"))
            if len(backups) > self.config['backup_count']:
                oldest = min(backups, key=os.path.getctime)
                oldest.unlink()
        except Exception as e:
            raise FileOperationError(f"Backup failed: {str(e)}")

    def restore_backup(self, file_path):
        """Restore file from latest backup"""
        backup_dir = self.current_project / '.backups'
        try:
            backups = list(backup_dir.glob(f"{Path(file_path).name}.*.bak"))
            if backups:
                latest_backup = max(backups, key=os.path.getctime)
                shutil.copy2(latest_backup, file_path)
                return True
            return False
        except Exception as e:
            raise FileOperationError(f"Restore failed: {str(e)}")

    def analyze_code(self, file_path):
        """Analyze code for quality and metrics"""
        try:
            extension = Path(file_path).suffix
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            analysis = {
                'lines': len(content.splitlines()),
                'size': len(content),
                'language': extension[1:] if extension else 'unknown',
                'last_modified': os.path.getmtime(file_path)
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Analysis failed for {file_path}: {e}")
            return None

    def track_changes(self, change_type, file_path):
        """Track project changes"""
        change = {
            'timestamp': time.time(),
            'type': change_type,
            'file': file_path,
            'analysis': self.analyze_code(file_path)
        }
        self.changes.append(change)

    def load_project(self, project_path):
        """Load a project and index its files"""
        if not os.path.exists(project_path):
            raise ProjectLoadError(f"Project path {project_path} does not exist")

        try:
            self.current_project = Path(project_path)
            self.project_files = {}
            self.load_gitignore(project_path)
            
            self.project_metadata = {
                'last_modified': time.time(),
                'file_count': 0,
                'language_stats': {},
                'total_lines': 0
            }

            extensions = [
                '.py', '.js', '.jsx', '.ts', '.tsx',
                '.css', '.scss', '.html', '.java',
                '.cpp', '.c', '.h', '.hpp', '.go',
                '.rs', '.php', '.rb', '.swift',
                '.md', '.json', '.yaml', '.yml'
            ]
            
            file_count = ignored_count = 0
            
            for ext in extensions:
                for file in self.current_project.rglob(f"*{ext}"):
                    if not self.is_ignored(str(file)):
                        try:
                            if file.stat().st_size > self.config['max_file_size']:
                                logger.warning(f"Skipping large file: {file}")
                                continue
                                
                            content = file.read_text(encoding='utf-8')
                            self.project_files[str(file)] = content
                            
                            # Update metadata
                            analysis = self.analyze_code(file)
                            if analysis:
                                self.project_metadata['total_lines'] += analysis['lines']
                                lang = analysis['language']
                                self.project_metadata['language_stats'][lang] = \
                                    self.project_metadata['language_stats'].get(lang, 0) + 1
                            
                            file_count += 1
                        except Exception as e:
                            logger.warning(f"Could not read {file}: {str(e)}")
                    else:
                        ignored_count += 1

            self.project_metadata['file_count'] = file_count
            return f"Loaded {file_count} files from {project_path} (ignored {ignored_count} files)"
        except Exception as e:
            raise ProjectLoadError(f"Failed to load project: {str(e)}")

