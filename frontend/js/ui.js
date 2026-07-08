/**
 * Global UI Managers (Toasts, Modals, Markdown)
 */

// --- TOASTS ---
const toastContainer = document.getElementById('toast-container');

export function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- MODALS ---
const modalOverlay = document.getElementById('confirm-modal');
const modalTitle = document.getElementById('modal-title');
const modalDesc = document.getElementById('modal-desc');
const btnConfirm = document.getElementById('modal-confirm');
const btnCancel = document.getElementById('modal-cancel');

export function showConfirmModal(title, description) {
    return new Promise((resolve) => {
        modalTitle.textContent = title;
        modalDesc.textContent = description;
        modalOverlay.classList.remove('hidden');
        
        // Focus trap simple implementation
        btnCancel.focus();

        const handleConfirm = () => cleanup(true);
        const handleCancel = () => cleanup(false);
        const handleEscape = (e) => {
            if (e.key === 'Escape') cleanup(false);
        };

        const cleanup = (result) => {
            modalOverlay.classList.add('hidden');
            btnConfirm.removeEventListener('click', handleConfirm);
            btnCancel.removeEventListener('click', handleCancel);
            document.removeEventListener('keydown', handleEscape);
            resolve(result);
        };

        btnConfirm.addEventListener('click', handleConfirm);
        btnCancel.addEventListener('click', handleCancel);
        document.addEventListener('keydown', handleEscape);
    });
}

export function showSessionExpiredModal() {
    showConfirmModal('Session Expired', 'Your session has expired. Please log in again.').then(() => {
        import('./auth.js').then(module => module.forceLogout());
    });
}

const promptOverlay = document.getElementById('prompt-modal');
const promptTitle = document.getElementById('prompt-modal-title');
const promptDesc = document.getElementById('prompt-modal-desc');
const promptInput = document.getElementById('prompt-modal-input');
const btnPromptConfirm = document.getElementById('prompt-modal-confirm');
const btnPromptCancel = document.getElementById('prompt-modal-cancel');

export function showPromptModal(title, description, defaultValue = '') {
    return new Promise((resolve) => {
        promptTitle.textContent = title;
        promptDesc.textContent = description;
        promptInput.value = defaultValue;
        promptOverlay.classList.remove('hidden');
        
        promptInput.focus();

        const handleConfirm = () => cleanup(promptInput.value.trim());
        const handleCancel = () => cleanup(null);
        const handleEscape = (e) => {
            if (e.key === 'Escape') cleanup(null);
            if (e.key === 'Enter') cleanup(promptInput.value.trim());
        };

        const cleanup = (result) => {
            promptOverlay.classList.add('hidden');
            btnPromptConfirm.removeEventListener('click', handleConfirm);
            btnPromptCancel.removeEventListener('click', handleCancel);
            document.removeEventListener('keydown', handleEscape);
            resolve(result);
        };

        btnPromptConfirm.addEventListener('click', handleConfirm);
        btnPromptCancel.addEventListener('click', handleCancel);
        document.addEventListener('keydown', handleEscape);
    });
}

// --- MARKDOWN ---
export function renderMarkdown(rawText) {
    if (!window.marked || !window.DOMPurify) {
        // Fallback if CDNs failed to load
        return rawText.replace(/\n/g, '<br>');
    }
    // Parse markdown and sanitize HTML output
    return DOMPurify.sanitize(marked.parse(rawText));
}
