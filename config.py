import os

class Config:
    # Directory Configuration
    UPLOAD_FOLDER = os.path.abspath('documents')  # Correctly references the local 'documents' folder
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'xlsx'}
    
    # API Configuration
    OPENAI_API_KEY = "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"
    
    # Template Configuration
    SYSTEM_TEMPLATE = """You are a helpful AI assistant named RAMEEN that answers questions based on the following context:
    {context}
    Follow these guidelines:
    - Always be professional and courteous
    - Always answer in the language chosen by the user
    - Provide concise, accurate answers based on the context
    - If information is not in the context, say so
    - Include relevant quotes from source documents when possible
    - Maintain context from previous conversations: {chat_history}
    - Format complex information in a readable way
    """
    
    # Memory Configuration
    MEMORY_K = 5
    MEMORY_KEY = "chat_history"
    OUTPUT_KEY = "answer"
