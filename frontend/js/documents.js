import { fetchApi } from './api.js';
import { showToast, showConfirmModal } from './ui.js';

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadBtn = document.getElementById('upload-btn');
const docsList = document.getElementById('docs-list');
const emptyState = document.getElementById('docs-empty-state');
const searchInput = document.getElementById('doc-search');
const uploadSidebarBtn = document.getElementById('upload-sidebar-btn');

let pollingIntervals = {};
let allDocuments = []; // Cache for filtering

export function initDocuments() {
    // File Picker
    if (uploadBtn) uploadBtn.addEventListener('click', () => fileInput.click());
    if (uploadSidebarBtn) uploadSidebarBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and Drop
    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                handleUploadQueue(Array.from(e.dataTransfer.files));
            }
        });
    }

    // Search filter
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            renderDocuments(e.target.value);
        }, 300);
    });
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleUploadQueue(Array.from(e.target.files));
        e.target.value = ''; // Reset input
    }
}

async function handleUploadQueue(files) {
    const pdfFiles = files.filter(f => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'));
    
    if (pdfFiles.length < files.length) {
        showToast('Only PDF files are allowed. Skipped invalid files.', 'warning');
    }
    if (pdfFiles.length === 0) return;

    // Filter out duplicate files
    const validFiles = pdfFiles.filter(file => {
        const isDuplicate = allDocuments.some(d => d.filename === file.name);
        if (isDuplicate) showToast(`"${file.name}" already exists`, 'warning');
        return !isDuplicate;
    });

    if (validFiles.length === 0) return;

    // Add all to UI as UPLOADING
    const uploadTasks = validFiles.map((file, idx) => {
        // Generate a temporary ID for the UI
        const tempId = `temp-${Date.now()}-${idx}`;
        const newDoc = {
            id: tempId,
            filename: file.name,
            created_at: new Date().toISOString(),
            status: 'UPLOADING'
        };
        allDocuments.unshift(newDoc);
        return { file, doc: newDoc };
    });

    renderDocuments(searchInput.value);
    showToast(`Uploading ${uploadTasks.length} document(s)...`, 'info');

    // Process sequentially to avoid DDoS
    for (const task of uploadTasks) {
        const formData = new FormData();
        formData.append('file', task.file);
        
        try {
            const response = await fetchApi('/documents/upload', {
                method: 'POST',
                body: formData
            });
            
            // Update temp doc with real DB id
            task.doc.id = response.document_id;
            task.doc.status = response.status || 'PENDING';
            renderDocuments(searchInput.value);
            startPolling(task.doc.id);
        } catch (e) {
            task.doc.status = 'ERROR';
            renderDocuments(searchInput.value);
            showToast(`Failed to upload ${task.file.name}`, 'error');
        }
    }
}

export async function loadDocuments() {
    docsList.innerHTML = '<tr class="skeleton"><td colspan="4"></td></tr><tr class="skeleton"><td colspan="4"></td></tr>';
    
    try {
        allDocuments = await fetchApi('/documents') || [];
        // Sort descending by upload date
        allDocuments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        renderDocuments();
        
        // Resume polling for any documents that are still pending/processing
        allDocuments.forEach(doc => {
            if (doc.status === 'PENDING' || doc.status === 'PROCESSING') {
                startPolling(doc.id);
            }
        });
    } catch (e) {
        docsList.innerHTML = '';
    }
}

function renderDocuments(filterText = '') {
    if (allDocuments.length === 0) {
        docsList.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    docsList.innerHTML = '';

    const lowerFilter = filterText.toLowerCase();
    const filtered = allDocuments.filter(doc => doc.filename.toLowerCase().includes(lowerFilter));

    if (filtered.length === 0 && filterText) {
        docsList.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 2rem; color: var(--clr-text-secondary);">No documents match "${filterText}"</td></tr>`;
        return;
    }

    filtered.forEach(doc => {
        const tr = document.createElement('tr');
        tr.id = `doc-${doc.id}`;
        tr.className = 'hover:bg-surface-container-low transition-colors group';
        
        let badgeHtml = '';
        if (doc.status === 'UPLOADING' || doc.status === 'PROCESSING') {
            badgeHtml = `<span class="inline-flex items-center px-2 py-1 rounded-md bg-surface-container-high text-on-surface-variant font-label-md text-label-md border border-outline-variant"><span class="material-symbols-outlined text-[14px] animate-spin mr-1">sync</span> ${doc.status}</span>`;
        } else if (doc.status === 'COMPLETED') {
            badgeHtml = `<span class="inline-flex items-center px-2 py-1 rounded-md bg-[#e6f4ea] text-[#137333] font-label-md text-label-md border border-[#ceead6]">COMPLETED</span>`;
        } else if (doc.status === 'ERROR') {
            badgeHtml = `<span class="inline-flex items-center px-2 py-1 rounded-md bg-error-container text-on-error-container font-label-md text-label-md border border-error-container">ERROR</span>`;
        }

        tr.innerHTML = `
            <td class="py-md px-lg">
                <div class="flex items-center gap-md">
                    <span class="material-symbols-outlined text-outline text-[20px]">description</span>
                    <span class="font-body-md text-body-md font-medium text-on-surface">${doc.filename}</span>
                </div>
            </td>
            <td class="py-md px-lg font-body-md text-body-md text-on-surface-variant">${formatRelativeTime(doc.created_at)}</td>
            <td class="py-md px-lg">${badgeHtml}</td>
            <td class="py-md px-lg text-right">
                <button class="text-on-surface-variant hover:text-error p-xs opacity-0 group-hover:opacity-100 transition-opacity delete-btn">
                    <span class="material-symbols-outlined text-[20px]">delete</span>
                </button>
            </td>
        `;

        tr.querySelector('.delete-btn').addEventListener('click', () => handleDelete(doc.id, doc.filename));
        docsList.appendChild(tr);
    });
}

function startPolling(docId) {
    if (pollingIntervals[docId]) return;

    let attempts = 0;
    const maxAttempts = 120; // 5 minutes at 2.5s intervals

    const poll = async () => {
        attempts++;
        if (attempts > maxAttempts) {
            clearInterval(pollingIntervals[docId]);
            delete pollingIntervals[docId];
            showToast('Polling timeout. Refresh the page to see final status.', 'warning');
            return;
        }

        try {
            const doc = await fetchApi(`/documents/${docId}`);
            
            // Update cache
            const index = allDocuments.findIndex(d => d.id === docId);
            if (index !== -1 && allDocuments[index].status !== doc.status) {
                allDocuments[index].status = doc.status;
                renderDocuments(searchInput.value);
            }

            if (doc.status === 'COMPLETED' || doc.status === 'ERROR') {
                clearInterval(pollingIntervals[docId]);
                delete pollingIntervals[docId];
                if (doc.status === 'COMPLETED') showToast(`${doc.filename} is ready for chat!`, 'success');
            }
        } catch (e) {
            // Stop polling on 404 or auth error
            if (e.status === 404 || e.status === 401) {
                clearInterval(pollingIntervals[docId]);
                delete pollingIntervals[docId];
            }
        }
    };

    pollingIntervals[docId] = setInterval(poll, 2500);
}

async function handleDelete(docId, filename) {
    const confirmed = await showConfirmModal('Delete Document', `This will permanently remove "${filename}" and its indexed content. Proceed?`);
    if (!confirmed) return;

    // Optimistic UI update
    const docRow = document.getElementById(`doc-${docId}`);
    if (docRow) docRow.style.opacity = '0.5';

    try {
        await fetchApi(`/documents/${docId}`, { method: 'DELETE' });
        
        // Remove from cache and re-render
        allDocuments = allDocuments.filter(d => d.id !== docId);
        renderDocuments(searchInput.value);
        showToast('Document deleted successfully', 'success');
        
        // Clear interval if it was polling
        if (pollingIntervals[docId]) {
            clearInterval(pollingIntervals[docId]);
            delete pollingIntervals[docId];
        }
    } catch (e) {
        // Rollback optimistic update
        if (docRow) docRow.style.opacity = '1';
        showToast('Failed to delete document', 'error');
    }
}

// Utility
function formatRelativeTime(dateStr) {
    if (!dateStr) return 'Unknown';
    const d = new Date(dateStr);
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
    return d.toLocaleDateString();
}
