// Flask Chat Application JavaScript
class ChatApp {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.currentLLM = '';
        this.currentModel = '';
        this.currentUsecase = '';
        
        // Model options mapping
        this.modelOptions = {
            'Groq': [],
            'OpenAI': [],
            'Gemini': [],
            'Ollama': []
        };
        
        this.initializeApp();
    }
    
    initializeApp() {
        this.setupSocketConnection();
        this.setupEventListeners();
        this.loadConfiguration();
        this.setupFormValidation();
        this.initializeTheme();
    }
    
    setupSocketConnection() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.isConnected = false;
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('connected', (data) => {
            this.sessionId = data.session_id;
            console.log('Session ID:', this.sessionId);
        });
        
        this.socket.on('message_response', (data) => {
            this.hideTypingIndicator();
            this.addMessage('assistant', data.assistant_reply, data);
            this.enableInput();
        });
        
        this.socket.on('error', (data) => {
            this.hideTypingIndicator();
            this.showError(data.message);
            this.enableInput();
        });
        
        this.socket.on('history_cleared', () => {
            this.clearChatMessages();
            this.showSuccess('Chat history cleared');
        });
        
        this.socket.on('chat_history', (data) => {
            this.loadChatHistory(data.history);
        });
    }
    
    setupEventListeners() {
        // Send button
        document.getElementById('sendBtn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key in input
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // LLM selection change
        document.getElementById('llmSelect').addEventListener('change', (e) => {
            this.handleLLMChange(e.target.value);
        });
        
        // Model selection change
        document.getElementById('modelSelect').addEventListener('change', (e) => {
            this.handleModelChange(e.target.value);
        });
        
        // Use case selection change
        document.getElementById('usecaseSelect').addEventListener('change', (e) => {
            this.handleUsecaseChange(e.target.value);
        });
        
        // Clear history button
        document.getElementById('clearHistoryBtn').addEventListener('click', () => {
            this.clearHistory();
        });
        
        // Export history button
        document.getElementById('exportHistoryBtn').addEventListener('click', () => {
            this.exportHistory();
        });
        
        // Theme toggle button
        document.getElementById('themeToggle').addEventListener('click', () => {
            this.toggleTheme();
        });
    }
    
    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            
            // Store model options
            this.modelOptions = {
                'Groq': config.groq_models,
                'OpenAI': config.openai_models,
                'Gemini': config.gemini_models,
                'Ollama': config.ollama_models
            };
            
            // Set initial LLM and update models
            const initialLLM = document.getElementById('llmSelect').value;
            this.updateModelOptions(initialLLM);
            this.updateChatInfo();
            
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.showError('Failed to load configuration');
        }
    }
    
    setupFormValidation() {
        const inputs = ['llmSelect', 'modelSelect', 'usecaseSelect'];
        inputs.forEach(inputId => {
            document.getElementById(inputId).addEventListener('change', () => {
                this.validateForm();
            });
        });
    }
    
    validateForm() {
        const llm = document.getElementById('llmSelect').value;
        const model = document.getElementById('modelSelect').value;
        const usecase = document.getElementById('usecaseSelect').value;
        
        const isValid = llm && model && usecase;
        const sendBtn = document.getElementById('sendBtn');
        const messageInput = document.getElementById('messageInput');
        
        if (isValid) {
            sendBtn.disabled = false;
            messageInput.disabled = false;
            this.currentLLM = llm;
            this.currentModel = model;
            this.currentUsecase = usecase;
            this.updateChatInfo();
        } else {
            sendBtn.disabled = true;
            messageInput.disabled = true;
        }
    }
    
    handleLLMChange(llm) {
        this.currentLLM = llm;
        this.updateModelOptions(llm);
        this.validateForm();
    }
    
    handleModelChange(model) {
        this.currentModel = model;
        this.validateForm();
    }
    
    handleUsecaseChange(usecase) {
        this.currentUsecase = usecase;
        this.validateForm();
    }
    
    updateModelOptions(llm) {
        const modelSelect = document.getElementById('modelSelect');
        const models = this.modelOptions[llm] || [];
        
        modelSelect.innerHTML = '';
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });
        
        // Select first model by default
        if (models.length > 0) {
            modelSelect.value = models[0];
            this.currentModel = models[0];
        }
    }
    
    updateChatInfo() {
        document.getElementById('currentLLM').textContent = this.currentLLM || 'No LLM selected';
        document.getElementById('currentModel').textContent = this.currentModel || 'No model selected';
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (connected) {
            statusElement.innerHTML = '<i class="fas fa-circle text-success"></i> Connected';
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle text-danger"></i> Disconnected';
        }
    }
    
    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || !this.isConnected) {
            return;
        }
        
        if (!this.currentLLM || !this.currentModel || !this.currentUsecase) {
            this.showError('Please select LLM, model, and use case');
            return;
        }
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input and disable
        messageInput.value = '';
        this.disableInput();
        this.showTypingIndicator();
        
        // Send to server
        this.socket.emit('send_message', {
            message: message,
            selected_llm: this.currentLLM,
            selected_model: this.currentModel,
            selected_usecase: this.currentUsecase
        });
    }
    
    addMessage(role, content, data = null) {
        const chatMessages = document.getElementById('chatMessages');
        
        // Remove welcome message if it exists
        const welcomeMessage = chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message slide-up`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'assistant') {
            let responseTimeInfo = '';
            if (data && data.response_time_seconds) {
                const responseTime = parseFloat(data.response_time_seconds).toFixed(2);
                responseTimeInfo = `<div class="response-time-info">
                    <small class="text-muted">
                        <i class="fas fa-clock"></i> Response time: ${responseTime}s
                    </small>
                </div>`;
            }
            contentDiv.innerHTML = `<i class="fas fa-robot"></i><p>${this.formatMessage(content)}</p>${responseTimeInfo}`;
        } else {
            contentDiv.innerHTML = `<i class="fas fa-user"></i><p>${this.formatMessage(content)}</p>`;
        }
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    formatMessage(content) {
        // Enhanced formatting for better display including tables
        let formatted = content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert markdown tables to HTML tables
        formatted = this.formatTables(formatted);
        
        return formatted;
    }
    
    formatTables(content) {
        // Find table patterns and convert to HTML
        const tableRegex = /(\|.*\|[\r\n]+)+/g;
        
        return content.replace(tableRegex, (match) => {
            const lines = match.trim().split('\n').filter(line => line.trim());
            if (lines.length < 2) return match;
            
            let html = '<div class="table-responsive"><table class="table table-striped table-bordered">';
            
            lines.forEach((line, index) => {
                const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell);
                
                if (index === 0) {
                    // Header row
                    html += '<thead><tr>';
                    cells.forEach(cell => {
                        html += `<th>${cell}</th>`;
                    });
                    html += '</tr></thead><tbody>';
                } else if (index === 1 && cells.every(cell => cell.match(/^[-:]+$/))) {
                    // Skip separator row
                    return;
                } else {
                    // Data row
                    html += '<tr>';
                    cells.forEach(cell => {
                        html += `<td>${cell}</td>`;
                    });
                    html += '</tr>';
                }
            });
            
            html += '</tbody></table></div>';
            return html;
        });
    }
    
    showTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'block';
    }
    
    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
    }
    
    disableInput() {
        document.getElementById('messageInput').disabled = true;
        document.getElementById('sendBtn').disabled = true;
    }
    
    enableInput() {
        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
        document.getElementById('messageInput').focus();
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    clearHistory() {
        if (this.socket && this.isConnected) {
            this.socket.emit('clear_history');
        }
    }
    
    clearChatMessages() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="message assistant-message">
                    <div class="message-content">
                        <i class="fas fa-robot"></i>
                        <p>Welcome! Please select your LLM, model, and use case from the sidebar, then start chatting!</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    loadChatHistory(history) {
        this.clearChatMessages();
        history.forEach(msg => {
            this.addMessage(msg.role, msg.content);
        });
    }
    
    exportHistory() {
        const chatMessages = document.getElementById('chatMessages');
        const messages = Array.from(chatMessages.querySelectorAll('.message')).map(msg => {
            const role = msg.classList.contains('user-message') ? 'user' : 'assistant';
            const content = msg.querySelector('p').textContent;
            return { role, content };
        });
        
        const dataStr = JSON.stringify(messages, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `chat_history_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }
    
    initializeTheme() {
        // Load saved theme or default to light
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    }
    
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
    
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        const themeIcon = document.getElementById('themeIcon');
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-sun';
            themeIcon.parentElement.title = 'Switch to Light Mode';
        } else {
            themeIcon.className = 'fas fa-moon';
            themeIcon.parentElement.title = 'Switch to Dark Mode';
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
