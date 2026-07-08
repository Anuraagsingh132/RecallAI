import { showToast, showSessionExpiredModal } from './ui.js';
import { getToken, clearToken, isTokenExpired } from './auth.js';

export const API_BASE_URL = ''; // Empty string so it uses current origin (since backend and frontend are unified)

/**
 * Normalized custom error wrapper
 */
export class ApiError extends Error {
    constructor(message, status, data) {
        super(message);
        this.status = status;
        this.data = data;
    }
}

/**
 * Core fetch wrapper with auth injection and normalized errors
 */
export async function fetchApi(endpoint, options = {}, retries = 1) {
    // Proactive expiry check
    if (isTokenExpired()) {
        showSessionExpiredModal();
        throw new Error('Session expired proactively');
    }

    const headers = new Headers(options.headers || {});
    
    // Auto-inject JSON header if body is an object and not FormData/URLSearchParams
    if (options.body && !(options.body instanceof FormData) && !(options.body instanceof URLSearchParams) && typeof options.body === 'object') {
        options.body = JSON.stringify(options.body);
        headers.set('Content-Type', 'application/json');
    }

    // Auto-inject Auth token
    const token = getToken();
    if (token && !headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const config = {
        ...options,
        headers
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        // Handle 401 Unauthorized globally
        if (response.status === 401) {
            clearToken();
            showSessionExpiredModal();
            throw new ApiError('Unauthorized', 401, null);
        }

        // Handle Rate Limiting
        if (response.status === 429) {
            const retryAfter = response.headers.get('Retry-After');
            showToast(`Rate limited. Try again in ${retryAfter || 60}s.`, 'error');
            throw new ApiError('Rate Limited', 429, null);
        }

        // Normal response parsing
        if (response.status === 204) return null; // No content (e.g. DELETE)

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            const msg = data?.detail || 'An unexpected error occurred';
            throw new ApiError(msg, response.status, data);
        }

        return data;

    } catch (error) {
        // Retry logic for idempotent GET requests on transient network failures
        if (error.name === 'TypeError' && retries > 0 && (!options.method || options.method === 'GET')) {
            console.warn(`Network error fetching ${endpoint}. Retrying...`);
            await new Promise(res => setTimeout(res, 1000));
            return fetchApi(endpoint, options, retries - 1);
        }

        // Rethrow ApiErrors directly, wrap others
        if (error instanceof ApiError) throw error;
        
        showToast('Network error. Check your connection.', 'error');
        throw error;
    }
}
