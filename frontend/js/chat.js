import { fetchApi, API_BASE_URL } from './api.js';
import { renderMarkdown, showToast } from './ui.js';
import { prependNewConversation } from './conversations.js';

const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatHistory = document.getElementById('chat-history');
const chatMessagesContainer = document.getElementById('chat-messages-container');
const sendBtn = document.getElementById('send-msg-btn');
const emptyState = document.getElementById('chat-empty-state');

export let activeConversationId = null;
let currentDocuments = [];
let selectedDocumentIds = [];

const selectorPills = document.getElementById('selector-pills');

const pillActiveClasses = ['bg-primary', 'text-on-primary', 'border-primary'];
const pillInactiveClasses = ['bg-surface-container', 'text-on-surface', 'border-outline-variant'];

export function initChat() {
    chatForm.addEventListener('submit', handleSendMessage);
    
    // Delegate pill clicks
    selectorPills.addEventListener('click', (e) => {
        const pill = e.target.closest('.pill');
        if (pill) {
            const docId = pill.getAttribute('data-id');
            if (docId === 'all') {
                selectedDocumentIds = [];
                document.querySelectorAll('.pill').forEach(p => {
                    p.classList.remove(...pillActiveClasses);
                    p.classList.add(...pillInactiveClasses);
                });
                pill.classList.remove(...pillInactiveClasses);
                pill.classList.add(...pillActiveClasses);
            } else {
                // Toggle doc
                const index = selectedDocumentIds.indexOf(docId);
                if (index > -1) {
                    selectedDocumentIds.splice(index, 1);
                    pill.classList.remove(...pillActiveClasses);
                    pill.classList.add(...pillInactiveClasses);
                    if (selectedDocumentIds.length === 0) {
                        const allPill = document.querySelector('.pill.all-docs');
                        allPill.classList.remove(...pillInactiveClasses);
                        allPill.classList.add(...pillActiveClasses);
                    }
                } else {
                    selectedDocumentIds.push(docId);
                    pill.classList.remove(...pillInactiveClasses);
                    pill.classList.add(...pillActiveClasses);
                    const allPill = document.querySelector('.pill.all-docs');
                    allPill.classList.remove(...pillActiveClasses);
                    allPill.classList.add(...pillInactiveClasses);
                }
            }
        }
    });
    
    // Auto-grow textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim().length > 0) {
            sendBtn.disabled = false;
        } else {
            sendBtn.disabled = true;
        }
    });

    // Handle Enter vs Shift+Enter
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) chatForm.dispatchEvent(new Event('submit'));
        }
    });
}

export async function populateDocumentSelector() {
    try {
        currentDocuments = await fetchApi('/documents') || [];
        // Only keep COMPLETED docs
        const readyDocs = currentDocuments.filter(d => d.status === 'COMPLETED');
        
        let html = `<span class="pill all-docs inline-flex items-center gap-1 border rounded-DEFAULT px-2 py-1 font-label-md text-label-md cursor-pointer hover:opacity-90 transition-colors ${pillActiveClasses.join(' ')}" data-id="all">All Documents</span>`;
        readyDocs.forEach(doc => {
            html += `<span class="pill inline-flex items-center gap-1 border rounded-DEFAULT px-2 py-1 font-label-md text-label-md cursor-pointer hover:bg-surface-variant transition-colors ${pillInactiveClasses.join(' ')}" data-id="${doc.id}" title="${doc.filename}">${doc.filename}</span>`;
        });
        
        selectorPills.innerHTML = html;
        selectedDocumentIds = []; // reset to all
    } catch (e) {
        console.error('Failed to load docs for selector', e);
    }
}

export function clearChatWindow() {
    activeConversationId = null;
    chatMessagesContainer.innerHTML = '';
    chatMessagesContainer.appendChild(emptyState);
    emptyState.classList.remove('hidden');
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;
}

export async function loadChatHistory(convId) {
    activeConversationId = convId;
    emptyState.classList.add('hidden');
    chatMessagesContainer.innerHTML = `
        <div class="flex flex-col items-start gap-1 w-full animate-pulse">
            <div class="w-1/2 h-20 bg-surface-container-high rounded-xl"></div>
        </div>
    `;
    
    try {
        const messages = await fetchApi(`/conversations/${convId}/messages`);
        chatMessagesContainer.innerHTML = '';
        
        if (messages.length === 0) {
            chatMessagesContainer.appendChild(emptyState);
            emptyState.classList.remove('hidden');
        } else {
            messages.forEach(msg => {
                let answerFound = msg.answer_found;
                if (answerFound === undefined) {
                    answerFound = msg.content !== "I cannot find the answer in the provided documents.";
                }
                appendMessage(msg.role, msg.content, answerFound, msg.sources || msg.citations);
            });
            scrollToBottom();
        }
    } catch (e) {
        chatMessagesContainer.innerHTML = '<div class="w-full text-center text-error p-xl">Failed to load messages.</div>';
    }
}

async function handleSendMessage(e) {
    e.preventDefault();
    const content = chatInput.value.trim();
    if (!content) return;

    // Reset input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    chatInput.disabled = true;
    sendBtn.disabled = true;

    emptyState.classList.add('hidden');
    
    // 1. Append user message optimistically
    appendMessage('user', content);
    scrollToBottom();
    
    // 2. Add typing indicator
    const typingId = addTypingIndicator();
    scrollToBottom();

    try {
        // Lazy initialization of conversation if none exists
        if (!activeConversationId) {
            const convData = await fetchApi('/conversations', { method: 'POST' });
            activeConversationId = convData.conversation_id;
            prependNewConversation(activeConversationId, content.substring(0, 40) + '...');
        }

        // 3. Send message via native fetch to get the stream
        const payload = { content };
        if (selectedDocumentIds.length > 0) {
            payload.document_ids = selectedDocumentIds;
        }

        const token = localStorage.getItem('recallai_token');
        const response = await fetch(`${API_BASE_URL}/conversations/${activeConversationId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Remove typing indicator
        document.getElementById(typingId)?.remove();

        // 4. Create an empty AI message bubble to stream into
        const aiMessageDiv = createStreamingMessageBubble();
        const bubble = aiMessageDiv.querySelector('.message-bubble');
        
        let fullText = "";
        let sources = null;

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // Parse SSE lines
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep the last incomplete part in the buffer
            
            for (const chunk of lines) {
                if (chunk.trim() === '') continue;
                
                const eventMatch = chunk.match(/event: (.*)/);
                const dataMatch = chunk.match(/data: (.*)/);
                
                if (eventMatch && dataMatch) {
                    const event = eventMatch[1];
                    const data = JSON.parse(dataMatch[1]);
                    
                    if (event === 'sources') {
                        sources = data;
                        if (sources && sources.length > 0) {
                            appendSourcesToBubble(bubble, sources);
                            scrollToBottom();
                        }
                    } else if (event === 'token') {
                        fullText += data;
                        
                        // We wrap the markdown in a container so we don't overwrite the sources container
                        let textContainer = bubble.querySelector('.text-container');
                        if (!textContainer) {
                            textContainer = document.createElement('div');
                            textContainer.className = 'text-container';
                            bubble.insertBefore(textContainer, bubble.firstChild);
                        }
                        
                        textContainer.innerHTML = renderMarkdown(fullText);
                        scrollToBottom();
                    } else if (event === 'done') {
                        break;
                    }
                }
            }
        }
        
        if (fullText.trim() === "I cannot find the answer in the provided documents.") {
            bubble.classList.add('not-found');
        }

    } catch (err) {
        document.getElementById(typingId)?.remove();
        showToast('Failed to send message.', 'error');
        // Restore input so user doesn't lose their typing
        chatInput.value = content;
    } finally {
        chatInput.disabled = false;
        chatInput.focus();
        // check value length to re-enable button if we restored content
        sendBtn.disabled = chatInput.value.trim().length === 0;
    }
}

function createStreamingMessageBubble() {
    const div = document.createElement('div');
    div.className = `flex flex-col items-start gap-1 w-full`;
    
    div.innerHTML = `
        <div class="flex items-center gap-2 mb-1">
            <div class="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center font-bold text-on-secondary-container">
                <span class="material-symbols-outlined text-[18px]">auto_awesome</span>
            </div>
            <span class="font-label-md text-label-md text-on-surface-variant">RecallAI</span>
        </div>
        <div class="message-bubble bg-surface-container border border-outline-variant rounded-2xl rounded-tl-sm px-lg py-md max-w-[85%] font-body-md text-body-md text-on-surface shadow-sm markdown-body w-full">
            <div class="text-container"></div>
        </div>
    `;
    chatMessagesContainer.appendChild(div);
    return div;
}

function appendSourcesToBubble(bubble, sources) {
    if (bubble.querySelector('.sources-container')) return;
    
    const sourcesContainer = document.createElement('div');
    sourcesContainer.className = 'sources-container';
    sourcesContainer.style.marginTop = '10px';
    
    const toggle = document.createElement('button');
    toggle.className = 'sources-toggle';
    toggle.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
        Sources (${sources.length})
    `;
    
    const list = document.createElement('div');
    list.className = 'sources-list hidden';
    
    sources.forEach(src => {
        const item = document.createElement('div');
        item.className = 'source-item';
        const docName = src.filename || src.document_name || 'Unknown Document';
        const excerptHtml = src.excerpt ? `<div class="source-excerpt">"${src.excerpt}"</div>` : '';
        item.innerHTML = `
            <div class="source-header">${docName} (Page ${src.page_number})</div>
            ${excerptHtml}
        `;
        list.appendChild(item);
    });
    
    toggle.addEventListener('click', () => {
        list.classList.toggle('hidden');
        const polyline = toggle.querySelector('polyline');
        if (list.classList.contains('hidden')) {
            polyline.setAttribute('points', '6 9 12 15 18 9');
        } else {
            polyline.setAttribute('points', '18 15 12 9 6 15');
        }
    });
    
    sourcesContainer.appendChild(toggle);
    sourcesContainer.appendChild(list);
    bubble.appendChild(sourcesContainer);
}

function appendMessage(role, content, answerFound = true, sources = null) {
    const div = document.createElement('div');
    
    if (role === 'user') {
        div.className = `flex flex-col items-end gap-1 w-full`;
        div.innerHTML = `
            <div class="flex items-center gap-2 mb-1 flex-row-reverse">
                <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center font-bold text-on-primary" id="user-avatar-msg">U</div>
                <span class="font-label-md text-label-md text-on-surface-variant">You</span>
            </div>
            <div class="message-bubble bg-primary text-on-primary rounded-2xl rounded-tr-sm px-lg py-md max-w-[85%] font-body-md text-body-md shadow-sm">
                ${content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}
            </div>
        `;
        const userInitial = document.getElementById('user-initial');
        if (userInitial && div.querySelector('#user-avatar-msg')) {
            div.querySelector('#user-avatar-msg').textContent = userInitial.textContent;
        }
    } else {
        div.className = `flex flex-col items-start gap-1 w-full`;
        
        let bubbleClass = "message-bubble bg-surface-container border border-outline-variant rounded-2xl rounded-tl-sm px-lg py-md max-w-[85%] font-body-md text-body-md text-on-surface shadow-sm markdown-body w-full";
        if (answerFound === false) {
            bubbleClass += " border-error-container bg-error-container/10";
        }

        const bubble = document.createElement('div');
        bubble.className = bubbleClass;
        
        const textContainer = document.createElement('div');
        textContainer.className = 'text-container';
        textContainer.innerHTML = renderMarkdown(content);
        bubble.appendChild(textContainer);
        
        if (sources && sources.length > 0) {
            appendSourcesToBubble(bubble, sources);
        }

        div.innerHTML = `
            <div class="flex items-center gap-2 mb-1">
                <div class="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center font-bold text-on-secondary-container">
                    <span class="material-symbols-outlined text-[18px]">auto_awesome</span>
                </div>
                <span class="font-label-md text-label-md text-on-surface-variant">RecallAI</span>
            </div>
        `;
        div.appendChild(bubble);
    }
    
    chatMessagesContainer.appendChild(div);
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = `flex flex-col items-start gap-1 w-full`;
    
    div.innerHTML = `
        <div class="flex items-center gap-2 mb-1">
            <div class="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center font-bold text-on-secondary-container">
                <span class="material-symbols-outlined text-[18px]">auto_awesome</span>
            </div>
            <span class="font-label-md text-label-md text-on-surface-variant">RecallAI</span>
        </div>
        <div class="message-bubble bg-surface-container border border-outline-variant rounded-2xl rounded-tl-sm px-lg py-md text-on-surface shadow-sm">
            <div class="flex items-center gap-1 h-6">
                <div class="w-2 h-2 rounded-full bg-outline animate-bounce" style="animation-delay: 0ms"></div>
                <div class="w-2 h-2 rounded-full bg-outline animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2 h-2 rounded-full bg-outline animate-bounce" style="animation-delay: 300ms"></div>
            </div>
        </div>
    `;
    chatMessagesContainer.appendChild(div);
    return id;
}

function scrollToBottom() {
    // Only scroll if we are reasonably close to the bottom (prevent yanking if user scrolled up)
    const distanceToBottom = chatHistory.scrollHeight - chatHistory.scrollTop - chatHistory.clientHeight;
    if (distanceToBottom < 150 || chatMessagesContainer.children.length <= 2) {
        chatHistory.scrollTo({
            top: chatHistory.scrollHeight,
            behavior: 'smooth'
        });
    }
}
