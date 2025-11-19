/**
 * LegalReasonerX - Utility Functions
 * Handles API calls, storage, and UI interactions
 */

// API Base URL
const API_BASE_URL = window.location.origin;

// Storage keys
const STORAGE_KEYS = {
    COURT_LISTENER_TOKEN: 'courtListenerToken',
    OPENAI_API_KEY: 'openaiApiKey',
    PRECEDENT_DATA: 'precedentData',
    THEME: 'theme'
};

// API utilities
const API = {
    async processCitation(citation, apiToken) {
        return await this.post('/api/process-citation', {
            citation,
            api_token: apiToken
        });
    },

    async generateNetwork(citationDict) {
        return await this.post('/api/generate-network', {
            citation_dict: citationDict
        });
    },

    async extractOpinions(apiToken, precedentData) {
        return await this.post('/api/extract-opinions', {
            api_token: apiToken,
            precedent_data: precedentData
        });
    },

    async analyzeReasoning(baseOpinionText, precedentOpinionText, openaiApiKey) {
        return await this.post('/api/analyze-reasoning', {
            base_opinion_text: baseOpinionText,
            precedent_opinion_text: precedentOpinionText,
            openai_api_key: openaiApiKey
        });
    },

    async extractEntities(baseOpinionText, precedentOpinionText, openaiApiKey) {
        return await this.post('/api/extract-entities', {
            base_opinion_text: baseOpinionText,
            precedent_opinion_text: precedentOpinionText,
            openai_api_key: openaiApiKey
        });
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'API request failed');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
};

// Storage utilities
const Storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Storage error:', error);
            return false;
        }
    },

    get(key) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : null;
        } catch (error) {
            console.error('Storage error:', error);
            return null;
        }
    },

    remove(key) {
        localStorage.removeItem(key);
    },

    clear() {
        localStorage.clear();
    },

    // API Token methods
    getCourtListenerToken() {
        return this.get(STORAGE_KEYS.COURT_LISTENER_TOKEN);
    },

    setCourtListenerToken(token) {
        return this.set(STORAGE_KEYS.COURT_LISTENER_TOKEN, token);
    },

    getOpenAIKey() {
        return this.get(STORAGE_KEYS.OPENAI_API_KEY);
    },

    setOpenAIKey(key) {
        return this.set(STORAGE_KEYS.OPENAI_API_KEY, key);
    },

    // Precedent data methods
    getPrecedentData() {
        return this.get(STORAGE_KEYS.PRECEDENT_DATA);
    },

    setPrecedentData(data) {
        return this.set(STORAGE_KEYS.PRECEDENT_DATA, data);
    }
};

// UI utilities
const UI = {
    showLoading(message = 'Loading...') {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.id = 'loading-overlay';
        overlay.innerHTML = `
            <div class="spinner"></div>
            <p style="color: var(--text-primary); font-weight: 600;">${message}</p>
        `;
        document.body.appendChild(overlay);
    },

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => overlay.remove(), 300);
        }
    },

    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        // Find a container or use body
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alert, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.style.animation = 'slideInDown 0.3s ease-out reverse';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    },

    showError(message) {
        this.showAlert(message, 'error');
    },

    showSuccess(message) {
        this.showAlert(message, 'success');
    },

    showWarning(message) {
        this.showAlert(message, 'warning');
    },

    showInfo(message) {
        this.showAlert(message, 'info');
    },

    createModal(title, content, buttons = []) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.id = 'modal-overlay';

        const buttonsHTML = buttons.map(btn =>
            `<button class="btn ${btn.class || 'btn-primary'}" onclick="${btn.onclick}">${btn.text}</button>`
        ).join('');

        overlay.innerHTML = `
            <div class="modal">
                <h2>${title}</h2>
                <div class="modal-content">
                    ${content}
                </div>
                <div class="modal-actions" style="margin-top: var(--spacing-lg); display: flex; gap: var(--spacing-md); justify-content: flex-end;">
                    ${buttonsHTML}
                    <button class="btn btn-outline" onclick="UI.closeModal()">Close</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                UI.closeModal();
            }
        });
    },

    closeModal() {
        const overlay = document.getElementById('modal-overlay');
        if (overlay) {
            overlay.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => overlay.remove(), 300);
        }
    },

    animateElement(element, animation = 'scaleIn') {
        element.style.animation = `${animation} var(--transition-slow) ease-out`;
    },

    createSkeleton(count = 3) {
        let skeleton = '<div class="skeleton skeleton-title"></div>';
        for (let i = 0; i < count; i++) {
            skeleton += '<div class="skeleton skeleton-text"></div>';
        }
        return skeleton;
    },

    updateProgress(percentage) {
        let progressBar = document.getElementById('progress-bar');
        if (!progressBar) {
            const container = document.querySelector('.container');
            const progressContainer = document.createElement('div');
            progressContainer.innerHTML = '<div class="progress"><div id="progress-bar" class="progress-bar"></div></div>';
            container.insertBefore(progressContainer, container.firstChild);
            progressBar = document.getElementById('progress-bar');
        }
        progressBar.style.width = `${percentage}%`;
    },

    hideProgress() {
        const progress = document.querySelector('.progress');
        if (progress) {
            progress.remove();
        }
    }
};

// Navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

// Form validation
const Validator = {
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    isEmpty(value) {
        return !value || value.trim() === '';
    },

    validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;

        const inputs = form.querySelectorAll('input[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (this.isEmpty(input.value)) {
                input.style.borderColor = 'var(--error)';
                isValid = false;
            } else {
                input.style.borderColor = 'var(--border)';
            }
        });

        return isValid;
    }
};

// Citation formatter
const CitationFormatter = {
    abbreviateCaseName(name, maxLength = 25) {
        if (name.length <= maxLength) return name;

        const parts = name.split(' v. ');
        if (parts.length > 1) {
            return `${parts[0].substring(0, 12)}... v. ${parts[1].substring(0, 12)}...`;
        }

        return name.substring(0, maxLength) + '...';
    },

    formatOpinionText(opinions, caseName) {
        let allOpinion = '';
        const delimiter = '='.repeat(50);

        if (!opinions[caseName]) return '';

        opinions[caseName].forEach(precedent => {
            Object.entries(precedent).forEach(([title, data]) => {
                const opinion = `
${title}
Case name: ${data.case_name}
Opinion type: ${data.type}
Source link: ${data.link}

${data.opinion}
${delimiter}

`;
                allOpinion += opinion;
            });
        });

        return allOpinion;
    }
};

// Export utilities
window.API = API;
window.Storage = Storage;
window.UI = UI;
window.Validator = Validator;
window.CitationFormatter = CitationFormatter;
window.STORAGE_KEYS = STORAGE_KEYS;
