# RecallAI Frontend (Vanilla JS)

This is a complete, production-ready frontend for the RecallAI platform built exclusively with Vanilla HTML, CSS, and JavaScript. 

No frameworks, no npm, and no build step are required. It uses native ES modules to structure the logic into focused, maintainable files.

## Features
- **Authentication**: JWT-based login/registration with automatic expiry checking.
- **Document Management**: Drag-and-drop PDF uploads, optimistic UI updates, polling for background job status (`PENDING` -> `PROCESSING` -> `COMPLETED`), and deletion.
- **RAG Chat**: Context-aware chat with AI, complete with typing indicators, markdown rendering (via CDN scripts), and dynamic "Sources" dropdowns citing exact pages from your PDFs.
- **Design System**: Fully responsive mobile-first architecture utilizing CSS Variables for easy theming (includes automatic dark mode via `prefers-color-scheme`).

## How to run locally

Since it uses native ES modules (`<script type="module">`), you cannot just double-click `index.html` to open it via the `file://` protocol due to browser CORS restrictions on local files.

You must serve the directory using any local static web server. 

**Using Node (npx):**
```bash
npx serve .
```

**Using Python:**
```bash
python -m http.server 3000
```

Then, open `http://localhost:3000` in your browser.

## Configuration

By default, the frontend expects the RecallAI backend to be running at `http://localhost:8000`. 

If your backend is hosted elsewhere (e.g., Render), simply change the `API_BASE_URL` constant at the top of `js/api.js`:

```javascript
export const API_BASE_URL = 'https://recallai-web.onrender.com';
```
