// Document upload handling
document.getElementById('uploadForm').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    const file = document.getElementById('file').files[0];
    const status = document.getElementById('uploadStatus');
    
    if (!file) {
        status.textContent = 'Please select a file';
        return;
    }
    
    formData.append('file', file);
    status.textContent = 'Uploading...';
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        status.textContent = result.success || result.error;
    } catch (error) {
        status.textContent = 'Error uploading file';
        console.error('Error:', error);
    }
};

// Query handling
async function askQuestion() {
    const query = document.getElementById('query').value;
    const response = document.getElementById('response');
    
    if (!query.trim()) {
        response.innerHTML = '<div class="error">Please enter a question</div>';
        return;
    }
    
    response.innerHTML = '<div class="loading">Processing query...</div>';
    
    try {
        const result = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await result.json();
        
        if (!result.ok) {
            throw new Error(data.error || 'Failed to process query');
        }
        
        response.innerHTML = `<div class="answer">${data.answer}</div>`;
    } catch (error) {
        response.innerHTML = `<div class="error">${error.message}</div>`;
        console.error('Query error:', error);
    }
}

// Document management
async function listDocuments() {
    const docList = document.getElementById('documentList');
    try {
        const response = await fetch('/documents');
        const data = await response.json();
        if (data.documents.length > 0) {
            const html = data.documents.map(doc => `
                <div class="document-item">
                    <span>${doc.name}</span>
                    <span>${(doc.size/1024).toFixed(2)} KB</span>
                    <span>${doc.date}</span>
                </div>
            `).join('');
            docList.innerHTML = html;
        } else {
            docList.innerHTML = '<p>No documents uploaded</p>';
        }
    } catch (error) {
        docList.innerHTML = '<p class="error">Error loading documents</p>';
    }
}

async function deleteEmbeddings() {
    if (confirm('Are you sure you want to delete all documents and embeddings?')) {
        try {
            const response = await fetch('/embeddings', { method: 'DELETE' });
            const data = await response.json();
            alert(data.message || data.error);
            listDocuments(); // Refresh document list
        } catch (error) {
            alert('Error deleting files');
        }
    }
}

async function addQuestion(questionText) {
    console.log('Sending question:', questionText); // Debug log
    try {
        const response = await fetch('/add_question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: questionText })
        });
        const data = await response.json();
        console.log('Server response:', data); // Debug log
        if (!response.ok) throw new Error(data.message);
    } catch (error) {
        console.error('Error adding question:', error);
    }
}

async function getSuggestions(query) {
    try {
        const response = await fetch(`/suggestions?q=${encodeURIComponent(query)}`);
        const suggestions = await response.json();
        return suggestions;
    } catch (error) {
        console.error('Error fetching suggestions:', error);
        return [];
    }
}

// Initialize document list on page load
document.addEventListener('DOMContentLoaded', listDocuments);

document.addEventListener('DOMContentLoaded', function() {
    const queryInput = document.querySelector('#query');
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.id = 'suggestions-container';
    queryInput.parentNode.insertBefore(suggestionsContainer, queryInput.nextSibling);

    let debounceTimer;

    queryInput.addEventListener('input', function(e) {
        clearTimeout(debounceTimer);
        const query = e.target.value;

        if (query.length < 2) {
            suggestionsContainer.innerHTML = '';
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/suggestions?q=${encodeURIComponent(query)}`);
                const suggestions = await response.json();
                
                suggestionsContainer.innerHTML = '';
                suggestions.forEach(suggestion => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';
                    div.textContent = suggestion;
                    div.onclick = () => {
                        queryInput.value = suggestion;
                        suggestionsContainer.innerHTML = '';
                    };
                    suggestionsContainer.appendChild(div);
                });
            } catch (error) {
                console.error('Error fetching suggestions:', error);
            }
        }, 300);
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#suggestions-container') && !e.target.closest('#query')) {
            suggestionsContainer.innerHTML = '';
        }
    });
});