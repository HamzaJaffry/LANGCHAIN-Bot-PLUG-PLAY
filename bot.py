import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from config import Config
from filehandler import (process_documents, list_documents, delete_all, initialize_components, allowed_file)
import logging
from database import Database

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
db = Database()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if process_documents():
                return jsonify({'success': 'File uploaded and processed into embeddings'}), 200
            return jsonify({'error': 'Error processing document'}), 500
        except Exception as e:
            return jsonify({'error': f'Error: {str(e)}'}), 500
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/query', methods=['POST'])
def query():
    from filehandler import qa_chain, memory

    try:
        # Ensure components are initialized
        initialize_components()

        if not qa_chain:
            return jsonify({'error': 'No documents loaded'}), 400

        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query'}), 400

        # Store the question first
        question_stored = db.add_question(data['query'])
        logger.debug(f"Question storage status: {question_stored}")

        # Then process with QA chain
        result = qa_chain({"question": data['query']})
        
        return jsonify({
            'answer': result['answer'],
            'question_stored': question_stored,
            'chat_history': str(memory.chat_memory.messages[-5:])
        }), 200

    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/documents', methods=['GET'])
def get_documents():
    docs = list_documents()
    return jsonify({'documents': docs}), 200

@app.route('/embeddings', methods=['DELETE'])
def reset_all():
    if delete_all():
        return jsonify({'message': 'All documents and embeddings deleted successfully'}), 200
    return jsonify({'error': 'Error deleting files'}), 500

@app.route('/add_question', methods=['POST'])
def add_question():
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        
        if not data or 'question' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid data format'}), 400
            
        question = data.get('question')
        if not question or not question.strip():
            return jsonify({'status': 'error', 'message': 'Empty question'}), 400
            
        db.add_question(question)
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error in add_question: {e}")  # Debug log
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/suggestions', methods=['GET'])
def get_suggestions():
    query = request.args.get('q', '')
    logging.debug(f"Getting suggestions for: {query}")
    suggestions = db.get_suggestions(query)
    return jsonify(suggestions)

if __name__ == "__main__":
    process_documents()
    app.run(debug=True)
