class CodeAssistantError(Exception):
    """Base exception class for code assistant"""
    pass

class ProjectLoadError(CodeAssistantError):
    """Raised when project loading fails"""
    pass

class FileOperationError(CodeAssistantError):
    """Raised when file operations fail"""
    pass
