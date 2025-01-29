from ..utils.logger import logger
from ..assistant.code_assistant import CodeAssistant

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

def handle_commands():
    assistant = CodeAssistant()
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
                print(assistant.list_files())
                
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
            logger.error(f"Error: {str(e)}")
            print(f"Error: {str(e)}")
