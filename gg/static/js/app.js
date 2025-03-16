/**
 * Enhanced RecallAI JavaScript
 * Additional features and interactions for the chatbot UI
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add dark mode support - enhanced version
    setupDarkMode();
    
    // Add keyboard shortcut for sending messages (Ctrl+Enter)
    document.getElementById('userInput').addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            document.getElementById('sendButton').click();
        }
    });

    // Add smooth scrolling to chat box
    const chatBox = document.getElementById('chatBox');
    chatBox.addEventListener('DOMNodeInserted', function() {
        setTimeout(() => {
            chatBox.scrollTop = chatBox.scrollHeight;
        }, 100);
    });

    // Add file drag and drop support
    setupDragAndDrop('textUploadLabel', 'textFile');
    setupDragAndDrop('pdfUploadLabel', 'pdfFile');

    // Add loading animation for Wikipedia search
    document.getElementById('loadWikipediaButton').addEventListener('click', function() {
        const button = this;
        const originalText = button.innerHTML;
        const query = document.getElementById('wikipediaQuery').value.trim();
        
        if (query === '') return;
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
        button.disabled = true;
        
        // Re-enable button after some time (in case of error)
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 30000); // 30 seconds timeout
    });

    // Add typing indicator animation for bot messages
    window.showTypingIndicator = function() {
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typingIndicator';
        typingIndicator.classList.add('bot-message', 'typing-indicator');
        typingIndicator.innerHTML = `
            <div class="message-content">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        `;
        chatBox.appendChild(typingIndicator);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    window.removeTypingIndicator = function() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    };

    // Add copy button to bot messages
    window.addCopyButton = function(messageElement) {
        const copyButton = document.createElement('button');
        copyButton.classList.add('copy-button');
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.setAttribute('data-tooltip', 'Copy message');
        copyButton.addEventListener('click', function() {
            const textToCopy = messageElement.querySelector('.message-content').textContent;
            navigator.clipboard.writeText(textToCopy)
                .then(() => {
                    this.innerHTML = '<i class="fas fa-check"></i>';
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-copy"></i>';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy: ', err);
                });
        });
        messageElement.appendChild(copyButton);
    };

    // Add browser notifications (if supported)
    if ('Notification' in window) {
        window.requestNotificationPermission = function() {
            if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
                Notification.requestPermission();
            }
        };

        window.sendNotification = function(message) {
            if (Notification.permission === 'granted' && document.hidden) {
                new Notification('RecallAI Response', {
                    body: message.length > 100 ? message.substring(0, 100) + '...' : message,
                    icon: '/static/images/bot-icon.png'
                });
            }
        };

        // Request permission when user first interacts with the page
        document.addEventListener('click', function() {
            window.requestNotificationPermission();
        }, {once: true});
    }
});

// Setup dark mode functionality
function setupDarkMode() {
    // Check for saved preferences
    const savedTheme = localStorage.getItem('theme');
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Create the theme toggle button
    const themeToggle = document.createElement('button');
    themeToggle.id = 'themeToggle';
    themeToggle.className = 'theme-toggle-btn';
    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    themeToggle.setAttribute('title', 'Toggle dark mode');
    
    // Add the theme toggle to the page
    const toggleContainer = document.getElementById('theme-toggle-container');
    if (toggleContainer) {
        toggleContainer.appendChild(themeToggle);
    } else {
        // Fallback to app-header if container doesn't exist
        const appHeader = document.querySelector('.app-header');
        if (appHeader) {
            appHeader.appendChild(themeToggle);
        }
    }
    
    // Apply initial theme
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    } else if (savedTheme === 'light') {
        document.body.classList.remove('dark-mode');
        document.body.classList.remove('dark-mode-support');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    } else if (prefersDarkMode) {
        document.body.classList.add('dark-mode-support');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    // Toggle theme on button click
    themeToggle.addEventListener('click', function() {
        if (document.body.classList.contains('dark-mode') || 
            (document.body.classList.contains('dark-mode-support') && !savedTheme)) {
            // Switch to light mode
            document.body.classList.remove('dark-mode');
            document.body.classList.remove('dark-mode-support');
            localStorage.setItem('theme', 'light');
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            themeToggle.setAttribute('title', 'Switch to dark mode');
        } else {
            // Switch to dark mode
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            themeToggle.setAttribute('title', 'Switch to light mode');
        }
    });
    
    // Add listener for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!savedTheme) {
            if (e.matches) {
                document.body.classList.add('dark-mode-support');
                themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            } else {
                document.body.classList.remove('dark-mode-support');
                themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            }
        }
    });
}

// Utility function for file drag and drop
function setupDragAndDrop(dropzoneId, fileInputId) {
    const dropzone = document.getElementById(dropzoneId);
    const fileInput = document.getElementById(fileInputId);
    
    if (!dropzone || !fileInput) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropzone.style.borderColor = '#4361ee';
        dropzone.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
    }
    
    function unhighlight() {
        dropzone.style.borderColor = 'rgba(0,0,0,0.1)';
        dropzone.style.backgroundColor = '';
    }
    
    dropzone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        
        // Trigger change event
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    }
} 