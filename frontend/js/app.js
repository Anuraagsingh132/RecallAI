import { initAuth, getToken } from './auth.js';
import { initDocuments, loadDocuments } from './documents.js';
import { initConversations, loadConversations } from './conversations.js';
import { initChat } from './chat.js';

// DOM Elements
const authView = document.getElementById('auth-view');
const appView = document.getElementById('app-view');
const navDocs = document.getElementById('nav-docs');
const panelDocs = document.getElementById('panel-docs');
const panelChat = document.getElementById('panel-chat');
const sidebar = document.getElementById('sidebar');
const openSidebarBtn = document.getElementById('open-sidebar-btn');
const closeSidebarBtn = document.getElementById('close-sidebar-btn');
const mobileHeaderTitle = document.getElementById('mobile-header-title');

// Router / View Management
export function setView(viewId) {
    if (viewId === 'auth-view') {
        authView.classList.remove('hidden');
        appView.classList.add('hidden');
    } else {
        authView.classList.add('hidden');
        appView.classList.remove('hidden');
    }
}

export function showPanel(panelId) {
    const activeNavClasses = ['bg-surface-container-highest', 'dark:bg-surface-container-highest', 'text-on-surface', 'font-semibold'];
    const inactiveNavClasses = ['text-on-surface-variant'];

    if (panelId === 'panel-docs') {
        panelDocs.classList.remove('hidden');
        panelChat.classList.add('hidden');
        navDocs.classList.add(...activeNavClasses);
        navDocs.classList.remove(...inactiveNavClasses);
        document.querySelectorAll('.chat-item').forEach(el => {
            el.classList.remove(...activeNavClasses);
            el.classList.add(...inactiveNavClasses);
        });
        if(mobileHeaderTitle) mobileHeaderTitle.textContent = 'Document Library';
    } else if (panelId === 'panel-chat') {
        panelDocs.classList.add('hidden');
        panelChat.classList.remove('hidden');
        navDocs.classList.remove(...activeNavClasses);
        navDocs.classList.add(...inactiveNavClasses);
        if(mobileHeaderTitle) mobileHeaderTitle.textContent = 'Chat';
    }
}

// Bootstrap
function bootstrap() {
    // Initialize components
    initAuth();
    initDocuments();
    initConversations();
    initChat();

    // Event listeners for App Shell Navigation
    navDocs.addEventListener('click', () => {
        showPanel('panel-docs');
        sidebar.classList.remove('open');
    });

    // Mobile Sidebar toggle
    openSidebarBtn.addEventListener('click', () => sidebar.classList.add('open'));
    closeSidebarBtn.addEventListener('click', () => sidebar.classList.remove('open'));
    
    // Close sidebar on click outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && sidebar.classList.contains('open') && 
            !sidebar.contains(e.target) && e.target !== openSidebarBtn && !openSidebarBtn.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });

    // Routing Logic
    if (getToken()) {
        setView('app-view');
        showPanel('panel-docs');
        loadDocuments();
        loadConversations();
    } else {
        setView('auth-view');
    }
}

// Run bootstrapper
document.addEventListener('DOMContentLoaded', bootstrap);
