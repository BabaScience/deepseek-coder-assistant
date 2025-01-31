import streamlit as st
from pathlib import Path
import time
from src.assistant.code_assistant import CodeAssistant
from src.utils.logger import logger

def refresh_project(assistant, project_path):
    """Refresh project files by reloading the project"""
    if project_path:
        try:
            return assistant.load_project(project_path)
        except Exception as e:
            st.error(f"Error refreshing project: {str(e)}")
            return None

def show_file_editor(file_content, file_path):
    """Show editor for file content with syntax highlighting"""
    file_extension = Path(file_path).suffix[1:]
    return st.text_area(
        "Edit File Content",
        value=file_content,
        height=400,
        key=f"editor_{file_path}_{int(time.time())}"
    )

def create_enhanced_ui():
    st.set_page_config(
        page_title="AI Code Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .file-tree {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
        }
        .stSidebar {
            min-width: 400px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'assistant' not in st.session_state:
        st.session_state.assistant = CodeAssistant()
        st.session_state.current_file = None
        st.session_state.file_content = None
        st.session_state.project_path = None
    
    st.title("🤖 AI Code Assistant")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Project Management")
        
        # Project loader
        project_path = st.text_input("Project Path")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("📂 Load Project", use_container_width=True):
                with st.spinner("Loading project..."):
                    try:
                        result = refresh_project(st.session_state.assistant, project_path)
                        if result:
                            st.session_state.project_path = project_path
                            st.success(result)
                    except Exception as e:
                        st.error(f"Failed to load project: {str(e)}")
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                if st.session_state.project_path:
                    with st.spinner("Refreshing..."):
                        refresh_project(st.session_state.assistant, st.session_state.project_path)
                else:
                    st.warning("No project loaded")
        
        # File browser
        if st.session_state.assistant.file_handler.project_files:
            st.subheader("Project Files")
            files = list(st.session_state.assistant.file_handler.project_files.keys())
            selected_file = st.selectbox(
                "Select a file to edit",
                files,
                format_func=lambda x: Path(x).name
            )
            if selected_file:
                st.session_state.current_file = selected_file
                st.session_state.file_content = st.session_state.assistant.file_handler.project_files[selected_file]
    
    # Main content
    tabs = st.tabs(["File Editor", "Generate Code", "Modify File", "Create File"])


    # File Editor Tab
    with tabs[0]:
        if st.session_state.current_file and st.session_state.file_content:
            edited_content = show_file_editor(
                st.session_state.file_content,
                st.session_state.current_file
            )
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Save Changes", use_container_width=True):
                    try:
                        with st.spinner("Saving changes..."):
                            # Create backup before saving
                            st.session_state.assistant.file_handler.backup_file(st.session_state.current_file)
                            # Save changes
                            with open(st.session_state.current_file, 'w', encoding='utf-8') as f:
                                f.write(edited_content)
                            # Update in-memory content
                            st.session_state.assistant.file_handler.project_files[st.session_state.current_file] = edited_content
                            st.session_state.file_content = edited_content
                            st.success("Changes saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving file: {str(e)}")
            
            with col2:
                if st.button("Restore Backup", use_container_width=True):
                    try:
                        if st.session_state.assistant.file_handler.restore_backup(st.session_state.current_file):
                            st.success("File restored from backup")
                            # Refresh content after restore
                            with open(st.session_state.current_file, 'r', encoding='utf-8') as f:
                                restored_content = f.read()
                            st.session_state.file_content = restored_content
                            st.session_state.assistant.file_handler.project_files[st.session_state.current_file] = restored_content
                            st.experimental_rerun()
                        else:
                            st.warning("No backup found")
                    except Exception as e:
                        st.error(f"Error restoring backup: {str(e)}")
        else:
            st.info("Select a file from the sidebar to edit")

    
    # Generate Code Tab
    with tabs[1]:
        prompt = st.text_area("Enter your prompt", height=150)
        if st.button("Generate Code", use_container_width=True):
            if prompt:
                with st.spinner("Generating code..."):
                    progress_bar = st.progress(0)
                    status = st.empty()
                    
                    try:
                        result = st.session_state.assistant.generate_code(prompt)
                        progress_bar.progress(100)
                        st.code(result)
                    except Exception as e:
                        st.error(f"Error generating code: {str(e)}")
                    finally:
                        progress_bar.empty()

            else:
                st.warning("Please enter a prompt")
    
    # Modify File Tab
    with tabs[2]:
        file_path = st.text_input("File Path")
        instructions = st.text_area("Modification Instructions", height=150)
        if st.button("Modify File", use_container_width=True):
            if file_path and instructions:
                with st.spinner("Modifying file..."):
                    try:
                        result = st.session_state.assistant.modify_file(file_path, instructions)
                        if "Successfully" in result:
                            refresh_project(st.session_state.assistant, st.session_state.project_path)
                        st.success(result)
                    except Exception as e:
                        st.error(f"Error modifying file: {str(e)}")
            else:
                st.warning("Please fill in all fields")
    
    # Create File Tab
    with tabs[3]:
        new_file_path = st.text_input("New File Path")
        requirements = st.text_area("File Requirements", height=150)
        if st.button("Create File", use_container_width=True):
            if new_file_path and requirements:
                with st.spinner("Creating file..."):
                    try:
                        result = st.session_state.assistant.create_file(new_file_path, requirements)
                        if "Successfully" in result:
                            refresh_project(st.session_state.assistant, st.session_state.project_path)
                        st.success(result)
                    except Exception as e:
                        st.error(f"Error creating file: {str(e)}")
            else:
                st.warning("Please fill in all fields")

def main():
    create_enhanced_ui()

if __name__ == "__main__":
    main()
