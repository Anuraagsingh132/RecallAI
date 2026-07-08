import { fetchApi } from './api.js';
import { loadChatHistory, clearChatWindow, activeConversationId, populateDocumentSelector } from './chat.js';
import { showPanel } from './app.js';

const conversationsList = document.getElementById('conversations-list');
const newChatBtn = document.getElementById('new-chat-btn');

let allConversations = [];

export function initConversations() {
    newChatBtn.addEventListener('click', handleNewChat);
}

export async function loadConversations() {
    conversationsList.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>';
    
    try {
        allConversations = await fetchApi('/conversations') || [];
        renderConversations();
    } catch (e) {
        conversationsList.innerHTML = '<div style="padding: 10px; color: var(--clr-text-secondary); font-size: 0.8rem;">Failed to load history</div>';
    }
}

function renderConversations() {
    conversationsList.innerHTML = '';
    
    if (allConversations.length === 0) {
        conversationsList.innerHTML = '<div style="padding: 10px; color: var(--clr-text-tertiary); font-size: 0.8rem; text-align: center;">No chat history</div>';
        return;
    }

    allConversations.forEach(conv => {
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-item-wrapper group flex items-center justify-between px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container transition-colors cursor-pointer w-full relative';
        if (conv.id === activeConversationId) wrapper.classList.add('bg-surface-container', 'text-on-surface');
        
        const btn = document.createElement('button');
        btn.className = 'flex items-center gap-3 flex-1 text-left truncate chat-item';
        if (conv.id === activeConversationId) btn.classList.add('active');
        
        // Use SVG icon for chat
        btn.innerHTML = `
            <svg class="shrink-0" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <span class="chat-title truncate font-body-md text-body-md font-medium">${conv.title || 'New Conversation'}</span>
        `;
        
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chat-item-wrapper').forEach(el => {
                el.classList.remove('bg-surface-container', 'text-on-surface');
            });
            document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
            wrapper.classList.add('bg-surface-container', 'text-on-surface');
            btn.classList.add('active');
            
            // On mobile, close sidebar when clicking a chat
            document.getElementById('sidebar').classList.remove('open');
            
            populateDocumentSelector();
            showPanel('panel-chat');
            loadChatHistory(conv.id);
        });
        
        const optionsBtn = document.createElement('button');
        optionsBtn.className = 'opacity-0 group-hover:opacity-100 transition-opacity p-1 text-on-surface-variant hover:text-on-surface shrink-0';
        optionsBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg>`;
        
        const dropdown = document.createElement('div');
        dropdown.className = 'dropdown-menu hidden';
        dropdown.innerHTML = `
            <button class="dropdown-item" data-action="rename">Rename</button>
            <button class="dropdown-item" data-action="clear">Clear Chat</button>
            <button class="dropdown-item danger" data-action="delete">Delete</button>
        `;
        
        optionsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.dropdown-menu').forEach(el => {
                if (el !== dropdown) el.classList.add('hidden');
            });
            dropdown.classList.toggle('hidden');
        });
        
        dropdown.addEventListener('click', async (e) => {
            e.stopPropagation();
            const action = e.target.getAttribute('data-action');
            if (!action) return;
            dropdown.classList.add('hidden');
            
            if (action === 'rename') {
                import('./ui.js').then(async ({ showPromptModal, showToast }) => {
                    const newTitle = await showPromptModal('Rename Conversation', 'Enter a new title:', conv.title || 'New Conversation');
                    if (newTitle !== null) {
                        try {
                            await fetchApi(`/conversations/${conv.id}`, { method: 'PATCH', body: { title: newTitle } });
                            conv.title = newTitle;
                            btn.querySelector('.chat-title').textContent = newTitle;
                            showToast('Renamed successfully', 'success');
                        } catch (err) {
                            showToast('Failed to rename', 'error');
                        }
                    }
                });
            } else if (action === 'clear') {
                import('./ui.js').then(async ({ showConfirmModal, showToast }) => {
                    if (await showConfirmModal('Clear Chat', 'Are you sure you want to clear all messages?')) {
                        try {
                            await fetchApi(`/conversations/${conv.id}/messages`, { method: 'DELETE' });
                            if (activeConversationId === conv.id) {
                                loadChatHistory(conv.id); // Will load empty state
                            }
                            showToast('Chat cleared', 'success');
                        } catch (err) {
                            showToast('Failed to clear chat', 'error');
                        }
                    }
                });
            } else if (action === 'delete') {
                import('./ui.js').then(async ({ showConfirmModal, showToast }) => {
                    if (await showConfirmModal('Delete Conversation', 'Are you sure you want to delete this conversation? This cannot be undone.')) {
                        try {
                            await fetchApi(`/conversations/${conv.id}`, { method: 'DELETE' });
                            allConversations = allConversations.filter(c => c.id !== conv.id);
                            renderConversations();
                            if (activeConversationId === conv.id) {
                                handleNewChat();
                            }
                            showToast('Conversation deleted', 'success');
                        } catch (err) {
                            showToast('Failed to delete', 'error');
                        }
                    }
                });
            }
        });
        
        wrapper.appendChild(btn);
        wrapper.appendChild(optionsBtn);
        wrapper.appendChild(dropdown);
        conversationsList.appendChild(wrapper);
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown-menu').forEach(el => el.classList.add('hidden'));
    }, { once: false });
}

function handleNewChat() {
    // Lazy creation: don't call POST /conversations yet.
    // Clear chat window, set active ID to null.
    // The POST happens when the first message is sent.
    clearChatWindow();
    populateDocumentSelector();
    
    document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
    showPanel('panel-chat');
    
    // On mobile, close sidebar
    document.getElementById('sidebar').classList.remove('open');
}

// Called by chat.js when a new conversation is lazily created and first message sent
export function prependNewConversation(convId, title) {
    allConversations.unshift({
        id: convId,
        title: title,
        created_at: new Date().toISOString()
    });
    renderConversations();
}
