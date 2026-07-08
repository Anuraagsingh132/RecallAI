import { fetchApi } from './api.js';
import { showToast } from './ui.js';
import { setView } from './app.js';

const TOKEN_KEY = 'recallai_token';
const EXPIRY_KEY = 'recallai_token_exp';

// --- Token Management ---

export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EXPIRY_KEY);
}

export function isTokenExpired() {
    const exp = localStorage.getItem(EXPIRY_KEY);
    if (!exp) return false;
    // Check if current time (in seconds) is past the expiry time
    return Math.floor(Date.now() / 1000) > parseInt(exp, 10);
}

function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => 
            '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
        ).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

// --- DOM Elements ---
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const tabLogin = document.getElementById('tab-login');
const tabRegister = document.getElementById('tab-register');
const logoutBtn = document.getElementById('logout-btn');

export function initAuth() {
    const activeClasses = ['border-primary', 'text-primary'];
    const inactiveClasses = ['border-transparent', 'text-on-surface-variant', 'hover:text-on-surface'];

    tabLogin.addEventListener('click', () => {
        tabLogin.classList.add(...activeClasses);
        tabLogin.classList.remove(...inactiveClasses);
        tabRegister.classList.add(...inactiveClasses);
        tabRegister.classList.remove(...activeClasses);
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
    });

    tabRegister.addEventListener('click', () => {
        tabRegister.classList.add(...activeClasses);
        tabRegister.classList.remove(...inactiveClasses);
        tabLogin.classList.add(...inactiveClasses);
        tabLogin.classList.remove(...activeClasses);
        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
    });

    // Forms
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    logoutBtn.addEventListener('click', handleLogout);
}

async function handleLogin(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const usernameInput = document.getElementById('login-username').value;
    const passwordInput = document.getElementById('login-password').value;

    btn.disabled = true;
    btn.textContent = 'Signing in...';

    const formData = new URLSearchParams();
    formData.append('username', usernameInput);
    formData.append('password', passwordInput);

    try {
        const data = await fetchApi('/auth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData.toString()
        });

        // Store token and expiry
        localStorage.setItem(TOKEN_KEY, data.access_token);
        const decoded = parseJwt(data.access_token);
        if (decoded && decoded.exp) {
            localStorage.setItem(EXPIRY_KEY, decoded.exp);
        }

        // Set UI state
        document.getElementById('current-username').textContent = usernameInput;
        document.getElementById('user-initial').textContent = usernameInput.charAt(0).toUpperCase();
        
        loginForm.reset();
        showToast('Logged in successfully', 'success');
        
        // Transition view
        setView('app-view');
        
        // Dynamically load user data
        import('./documents.js').then(m => m.loadDocuments());
        import('./conversations.js').then(m => m.loadConversations());

    } catch (err) {
        if (err.status !== 429) { // 429 handled globally
            showToast(err.message || 'Login failed', 'error');
        }
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;

    btn.disabled = true;
    btn.textContent = 'Creating...';

    try {
        await fetchApi('/auth/register', {
            method: 'POST',
            body: { username, password }
        });

        showToast('Account created! Please log in.', 'success');
        tabLogin.click(); // Switch to login tab
        document.getElementById('login-username').value = username;
        document.getElementById('login-password').focus();
        registerForm.reset();
    } catch (err) {
        if (err.status !== 429) {
            showToast(err.message || 'Registration failed', 'error');
        }
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }
}

async function handleLogout() {
    try {
        // Attempt server logout, but don't block client logout if it fails
        await fetchApi('/auth/logout', { method: 'POST' });
    } catch (e) {
        console.warn('Server logout failed, clearing local state anyway', e);
    } finally {
        forceLogout();
    }
}

export function forceLogout() {
    clearToken();
    setView('auth-view');
}
