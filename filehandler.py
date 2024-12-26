import os
import time
import logging
import shutil
from langchain_community.document_loaders import (
    UnstructuredExcelLoader,
    PyPDFLoader,
    Docx2txtLoader,
    DirectoryLoader,
    TextLoader
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY

# Global variables and initialization
chat = None
vectorstore = None
qa_chain = None
chat_prompt = None
memory = ConversationBufferWindowMemory(
    k=Config.MEMORY_K,
    memory_key=Config.MEMORY_KEY,
    output_key=Config.OUTPUT_KEY,
    return_messages=True
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def initialize_components():
    global chat, chat_prompt
    if not chat:
        chat = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        system_message = SystemMessagePromptTemplate.from_template(Config.SYSTEM_TEMPLATE)
        human_message = HumanMessagePromptTemplate.from_template("{question}")
        chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def process_documents():
    global vectorstore, qa_chain, chat, chat_prompt

    initialize_components()

    documents = []
    loaders = {
        "*.pdf": (PyPDFLoader, {}),
        "*.docx": (Docx2txtLoader, {}),
        "*.xlsx": (UnstructuredExcelLoader, {"mode": "single"}),
        "*.txt": (TextLoader, {})
    }

    for glob_pattern, (loader_class, loader_args) in loaders.items():
        loader = DirectoryLoader(
            path=Config.UPLOAD_FOLDER,
            glob=glob_pattern,
            loader_cls=loader_class,
            loader_kwargs=loader_args
        )
        try:
            documents.extend(loader.load())
        except Exception as e:
            logger.error(f"Error loading {glob_pattern}: {str(e)}")

    if documents:
        try:
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(documents)

            if vectorstore is None:
                vectorstore = FAISS.from_documents(splits, embeddings)
            else:
                vectorstore.add_documents(splits)

            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=chat,
                retriever=vectorstore.as_retriever(),
                memory=memory,
                return_source_documents=True,
                combine_docs_chain_kwargs={
                    'prompt': chat_prompt,
                    'output_key': 'answer'
                }
            )

            vectorstore.save_local(os.path.join(Config.UPLOAD_FOLDER, 'vectorstore'))
            return True
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}")
            return False
    return False

def list_documents():
    docs_path = Config.UPLOAD_FOLDER
    if os.path.exists(docs_path):
        files = []
        for file in os.listdir(docs_path):
            if file.endswith(tuple(Config.ALLOWED_EXTENSIONS)):
                file_path = os.path.join(docs_path, file)
                files.append({
                    'name': file,
                    'size': os.path.getsize(file_path),
                    'date': time.ctime(os.path.getctime(file_path))
                })
        return files
    return []

def delete_all():
    global vectorstore, qa_chain

    vectorstore = None
    qa_chain = None

    try:
        vectorstore_path = os.path.join(Config.UPLOAD_FOLDER, 'vectorstore')
        if os.path.exists(vectorstore_path):
            shutil.rmtree(vectorstore_path)

        docs_path = Config.UPLOAD_FOLDER
        if os.path.exists(docs_path):
            for file in os.listdir(docs_path):
                if file.endswith(tuple(Config.ALLOWED_EXTENSIONS)):
                    os.remove(os.path.join(docs_path, file))

        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        logger.info("Successfully deleted all documents and embeddings")
        return True

    except Exception as e:
        logger.error(f"Error during deletion: {str(e)}")
        return False
