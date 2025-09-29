// Configuração da API
const API_BASE_URL = 'http://127.0.0.1:8000';

// Estado da aplicação
let appState = {
    documents: [],
    isConnected: false,
    stats: {
        indexed_documents: 0,
        embedding_model: 'Carregando...',
        llm_model: 'Carregando...'
    }
};


// Elementos DOM
const elements = {
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),
    docCount: document.getElementById('doc-count'),
    embeddingModel: document.getElementById('embedding-model'),
    llmModel: document.getElementById('llm-model'),
    documentText: document.getElementById('document-text'),
    addDocumentBtn: document.getElementById('add-document-btn'),
    documentsContainer: document.getElementById('documents-container'),
    questionInput: document.getElementById('question-input'),
    topKSelect: document.getElementById('top-k'),
    askQuestionBtn: document.getElementById('ask-question-btn'),
    chatMessages: document.getElementById('chat-messages'),
    loadingOverlay: document.getElementById('loading-overlay'),
    toastContainer: document.getElementById('toast-container')
};

// Inicialização da aplicação
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

// Inicializar aplicação
async function initializeApp() {
    await checkApiStatus();
    updateUI();
}

// Configurar event listeners
function setupEventListeners() {
    // Adicionar documento
    elements.addDocumentBtn.addEventListener('click', addDocument);
    
    // Fazer pergunta
    elements.askQuestionBtn.addEventListener('click', askQuestion);
    
    // Enter para enviar pergunta
    elements.questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askQuestion();
        }
    });
    
    // Enter para adicionar documento
    elements.documentText.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            addDocument();
        }
    });
    
    // Verificar status periodicamente
    setInterval(checkApiStatus, 30000); // A cada 30 segundos
}

// Verificar status da API
async function checkApiStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        if (response.ok) {
            const data = await response.json();
            appState.isConnected = true;
            appState.stats = data;
            updateConnectionStatus(true);
            updateStats();
        } else {
            throw new Error('API não disponível');
        }
    } catch (error) {
        appState.isConnected = false;
        updateConnectionStatus(false);
        console.error('Erro ao verificar status da API:', error);
    }
}

// Atualizar status de conexão
function updateConnectionStatus(isConnected) {
    if (isConnected) {
        elements.statusDot.className = 'status-dot online';
        elements.statusText.textContent = 'Conectado à API';
    } else {
        elements.statusDot.className = 'status-dot offline';
        elements.statusText.textContent = 'Desconectado';
    }
}

// Atualizar estatísticas
function updateStats() {
    elements.docCount.textContent = appState.stats.indexed_documents || 0;
    elements.embeddingModel.textContent = appState.stats.embedding_model || 'N/A';
    elements.llmModel.textContent = appState.stats.llm_model || 'N/A';
}

// Atualizar interface
function updateUI() {
    updateDocumentsList();
    updateButtonStates();
}

// Atualizar lista de documentos
function updateDocumentsList() {
    if (appState.documents.length === 0) {
        elements.documentsContainer.innerHTML = '<p class="empty-state">Nenhum documento indexado ainda.</p>';
    } else {
        elements.documentsContainer.innerHTML = appState.documents
            .map((doc, index) => `
                <div class="document-item">
                    <div class="document-index">${index + 1}</div>
                    <div class="document-text">${escapeHtml(doc)}</div>
                </div>
            `).join('');
    }
}

// Atualizar estado dos botões
function updateButtonStates() {
    const hasConnection = appState.isConnected;
    const hasDocuments = appState.documents.length > 0;
    
    elements.addDocumentBtn.disabled = !hasConnection;
    elements.askQuestionBtn.disabled = !hasConnection || !hasDocuments;
}

// Adicionar documento
async function addDocument() {
    const text = elements.documentText.value.trim();
    
    if (!text) {
        showToast('Por favor, digite um texto para indexar.', 'error');
        return;
    }
    
    if (!appState.isConnected) {
        showToast('Não é possível adicionar documento. API desconectada.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/ingest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        if (response.ok) {
            const data = await response.json();
            appState.documents.push(text);
            elements.documentText.value = '';
            
            showToast('Documento adicionado com sucesso!', 'success');
            updateUI();
            await checkApiStatus(); // Atualizar contagem
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao adicionar documento');
        }
    } catch (error) {
        console.error('Erro ao adicionar documento:', error);
        showToast(`Erro ao adicionar documento: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Fazer pergunta
async function askQuestion() {
    const question = elements.questionInput.value.trim();
    const topK = parseInt(elements.topKSelect.value);
    
    if (!question) {
        showToast('Por favor, digite uma pergunta.', 'error');
        return;
    }
    
    if (!appState.isConnected) {
        showToast('Não é possível fazer pergunta. API desconectada.', 'error');
        return;
    }
    
    if (appState.documents.length === 0) {
        showToast('Adicione alguns documentos antes de fazer perguntas.', 'error');
        return;
    }
    
    // Adicionar mensagem do usuário ao chat
    addChatMessage(question, 'user');
    elements.questionInput.value = '';
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                question: question,
                top_k: topK
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            addChatMessage(data.answer, 'bot', data.context);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao processar pergunta');
        }
    } catch (error) {
        console.error('Erro ao fazer pergunta:', error);
        addChatMessage(`Desculpe, ocorreu um erro: ${error.message}`, 'bot');
        showToast(`Erro ao processar pergunta: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Adicionar mensagem ao chat
function addChatMessage(message, sender, context = null) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}-message`;
    
    const avatar = sender === 'user' ? 'fa-user' : 'fa-robot';
    
    let contextHtml = '';
    if (context && sender === 'bot') {
        contextHtml = `
            <div class="context-info">
                <strong>Contexto utilizado:</strong><br>
                ${escapeHtml(context)}
            </div>
        `;
    }
    
    messageElement.innerHTML = `
        <div class="message-avatar">
            <i class="fas ${avatar}"></i>
        </div>
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
            ${contextHtml}
        </div>
    `;
    
    elements.chatMessages.appendChild(messageElement);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Carregar documentos de exemplo
function addExampleDocs() {
    const examples = [
        "A capital da França é Paris.",
        "O Brasil é o maior produtor de café do mundo.",
        "Python é uma linguagem de programação popular e versátil.",
        "O Rio de Janeiro é conhecido pelo Cristo Redentor e pelas praias de Copacabana e Ipanema.",
        "Machine Learning é um subcampo da inteligência artificial que permite aos computadores aprender sem serem explicitamente programados."
    ];
    
    if (!appState.isConnected) {
        showToast('Não é possível carregar exemplos. API desconectada.', 'error');
        return;
    }
    
    showLoading(true);
    
    // Adicionar documentos sequencialmente
    addExampleDocsSequentially(examples, 0);
}

// Adicionar documentos de exemplo sequencialmente
async function addExampleDocsSequentially(examples, index) {
    if (index >= examples.length) {
        showLoading(false);
        showToast('Documentos de exemplo carregados com sucesso!', 'success');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/ingest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: examples[index] })
        });
        
        if (response.ok) {
            appState.documents.push(examples[index]);
            updateUI();
            await checkApiStatus();
            
            // Continuar com o próximo documento
            setTimeout(() => {
                addExampleDocsSequentially(examples, index + 1);
            }, 500);
        } else {
            throw new Error('Erro ao adicionar documento de exemplo');
        }
    } catch (error) {
        showLoading(false);
        showToast(`Erro ao carregar exemplos: ${error.message}`, 'error');
    }
}

// Limpar todos os documentos
function clearAllDocuments() {
    if (appState.documents.length === 0) {
        showToast('Não há documentos para limpar.', 'info');
        return;
    }
    
    if (confirm('Tem certeza que deseja limpar todos os documentos? Esta ação não pode ser desfeita.')) {
        appState.documents = [];
        updateUI();
        showToast('Todos os documentos foram removidos da interface. Reinicie a API para limpar o índice.', 'info');
    }
}

// Mostrar/ocultar loading
function showLoading(show) {
    if (show) {
        elements.loadingOverlay.classList.remove('hidden');
    } else {
        elements.loadingOverlay.classList.add('hidden');
    }
}

// Mostrar toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<div class="toast-message">${escapeHtml(message)}</div>`;
    
    elements.toastContainer.appendChild(toast);
    
    // Remover toast após 5 segundos
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 5000);
}

// Escapar HTML para prevenir XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Função para debug (pode ser removida em produção)
window.debugApp = function() {
    console.log('Estado da aplicação:', appState);
    console.log('Elementos DOM:', elements);
};
