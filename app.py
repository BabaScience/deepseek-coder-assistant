import logging
import os
from pathlib import Path
import glob
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('code_assistant.log')
    ]
)

class EnhancedCodeAssistant:
    def __init__(self, model_name="deepseek-ai/deepseek-coder-1.3b-instruct"):
        """Initialize the code assistant with the specified model."""
        logging.info(f"Initializing EnhancedCodeAssistant with model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
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
            logging.info(f"Loaded .gitignore from {gitignore_path}")
        else:
            self.gitignore_spec = None
            logging.info("No .gitignore file found")

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
            
            file_count = 0
            ignored_count = 0
            
            extensions = [
                '.py', '.js', '.jsx', '.ts', '.tsx', 
                '.css', '.scss', '.html', '.java',
                '.cpp', '.c', '.h', '.hpp', '.go',
                '.rs', '.php', '.rb', '.swift'
            ]
            
            for ext in extensions:
                for file in glob.glob(f"{project_path}/**/*{ext}", recursive=True):
                    if not self.is_ignored(file):
                        try:
                            with open(file, 'r', encoding='utf-8') as f:
                                self.project_files[file] = f.read()
                                file_count += 1
                        except Exception as e:
                            logging.warning(f"Could not read {file}: {str(e)}")
                    else:
                        ignored_count += 1

            return f"Loaded {file_count} files from {project_path} (ignored {ignored_count} files)"
        except Exception as e:
            logging.error(f"Error loading project: {str(e)}")
            raise

    def modify_file(self, file_path, instruction):
        """Modify an existing file based on the given instruction."""
        if not self.current_project:
            return "No project loaded. Use !load first."
            
        full_path = str(self.current_project / file_path)
        if full_path not in self.project_files:
            return f"File {file_path} not found"
            
        prompt = f"""
        Given the following file content:
        ```
        {self.project_files[full_path]}
        ```
        
        Modification instruction: {instruction}
        
        Please provide the complete modified file content while maintaining the original structure and functionality.
        Only output the modified code without any explanations.
        """
        
        modified_content = self.generate_code(prompt)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            self.project_files[full_path] = modified_content
            return f"Successfully modified {file_path}"
        except Exception as e:
            logging.error(f"Error writing to file: {str(e)}")
            return f"Error writing to file: {str(e)}"

    def create_file(self, file_path, instruction):
        """Create a new file based on the given instruction."""
        if not self.current_project:
            return "No project loaded. Use !load first."
            
        full_path = str(self.current_project / file_path)
        
        if os.path.exists(full_path):
            return f"File {file_path} already exists"
            
        prompt = f"""
        Create a new file with the following requirements:
        File path: {file_path}
        Requirements: {instruction}
        
        Please provide only the complete file content without any explanations.
        """
        
        new_content = self.generate_code(prompt)
        
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.project_files[full_path] = new_content
            return f"Successfully created {file_path}"
        except Exception as e:
            logging.error(f"Error creating file: {str(e)}")
            return f"Error creating file: {str(e)}"

    def generate_code(self, prompt, max_length=2048, temperature=0.7):
        """Generate code based on the given prompt."""
        try:
            messages = [{"role": "user", "content": prompt}]
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt"
            ).to(self.model.device)
            
            outputs = self.model.generate(
                inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            return self.tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
        except Exception as e:
            logging.error(f"Error generating code: {str(e)}")
            raise

    def get_file_content(self, file_path):
        """Get the content of a specific file in the project."""
        if not self.current_project:
            return "No project loaded"
            
        full_path = str(self.current_project / file_path)
        return self.project_files.get(full_path, "File not found")

    def list_project_files(self):
        """List all files currently loaded in the project."""
        if not self.current_project:
            return "No project loaded"
            
        return "\n".join(
            os.path.relpath(f, self.current_project) 
            for f in self.project_files.keys()
        )

def print_help():
    """Print help message with available commands."""
    help_message = """
Available Commands:
-----------------
!load <path>      Load project from specified path
!modify <file>    Modify existing file
!new <file>       Create new file
!list             List all project files
!help             Show this help message
!exit             Exit the assistant

For direct code generation, simply type your prompt.
"""
    print(help_message)

def main():
    assistant = EnhancedCodeAssistant()
    print("AI Code Assistant initialized.")
    print_help()
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command.startswith("!load"):
                _, path = command.split(" ", 1)
                print(assistant.load_project(path))
                
            elif command.startswith("!modify"):
                _, file_path = command.split(" ", 1)
                instruction = input("Enter modification instructions: ")
                result = assistant.modify_file(file_path, instruction)
                print(result)
                
            elif command.startswith("!new"):
                _, file_path = command.split(" ", 1)
                instruction = input("Enter file requirements: ")
                result = assistant.create_file(file_path, instruction)
                print(result)
                
            elif command == "!list":
                print(assistant.list_project_files())
                
            elif command == "!help":
                print_help()
                
            elif command.lower() in ['!exit', 'exit', 'quit']:
                print("Goodbye!")
                break
                
            else:
                result = assistant.generate_code(command)
                print(result)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
