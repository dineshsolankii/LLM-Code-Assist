/**
 * API Client Module — with timeout, retry, and proper error handling
 */
const API = {
    DEFAULT_TIMEOUT: 90000, // 90s for Ollama requests
    MAX_RETRIES: 2,

    async request(url, options = {}, retries = 0) {
        const controller = new AbortController();
        const timeout = options.timeout || this.DEFAULT_TIMEOUT;
        const timer = setTimeout(() => controller.abort(), timeout);

        try {
            const defaults = {
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                signal: controller.signal
            };
            const config = { ...defaults, ...options };
            if (options.body && typeof options.body === 'object') {
                config.body = JSON.stringify(options.body);
            }
            // Remove custom fields not needed by fetch
            delete config.timeout;

            const response = await fetch(url, config);

            // Handle 401 — redirect to login
            if (response.status === 401) {
                window.location.href = '/auth/login';
                throw new Error('Unauthorized — redirecting to login');
            }

            // Retry on 502/503/504
            if ((response.status === 502 || response.status === 503 || response.status === 504) && retries < this.MAX_RETRIES) {
                await new Promise(r => setTimeout(r, 1000 * (retries + 1)));
                return this.request(url, options, retries + 1);
            }

            let data;
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                data = { error: text || `HTTP ${response.status}` };
            }

            if (!response.ok) {
                const errMsg = data.error || data.message || `HTTP ${response.status}: ${response.statusText}`;
                throw new Error(errMsg);
            }
            return data;

        } catch (err) {
            if (err.name === 'AbortError') {
                throw new Error(`Request timed out after ${timeout / 1000}s. Is Ollama running?`);
            }
            console.error(`API Error [${url}]:`, err.message);
            throw err;
        } finally {
            clearTimeout(timer);
        }
    },

    get(url, opts) { return this.request(url, { ...opts }); },
    post(url, body, opts) { return this.request(url, { method: 'POST', body, ...opts }); },
    put(url, body, opts) { return this.request(url, { method: 'PUT', body, ...opts }); },
    del(url, opts) { return this.request(url, { method: 'DELETE', ...opts }); },

    // Convenience methods matching backend routes
    async getFrameworks() { return this.get('/api/frameworks', { timeout: 10000 }); },
    async getProjects() { return this.get('/api/project', { timeout: 10000 }); },
    async createProject(data) { return this.post('/api/project/create', data, { timeout: 300000 }); }, // 5 min for project gen
    async deleteProject(name) { return this.del(`/api/project/${encodeURIComponent(name)}`, { timeout: 15000 }); },
    async getFiles(project) { return this.get(`/api/project/${encodeURIComponent(project)}/files`, { timeout: 10000 }); },
    async getFileContent(project, path) {
        return this.get(`/api/project/${encodeURIComponent(project)}/file?path=${encodeURIComponent(path)}`, { timeout: 10000 });
    },
    async saveFile(project, path, content) {
        return this.post(`/api/project/${encodeURIComponent(project)}/file`, { path, content }, { timeout: 15000 });
    },
    async analyzeRequirements(requirements) {
        return this.post('/api/analyze', { requirements }, { timeout: 120000 }); // 2 min for analysis
    },
    async customizeCode(projectName, filePath, code, request) {
        return this.post('/api/customize-code', {
            projectName, filePath, currentCode: code, customizationRequest: request
        }, { timeout: 120000 });
    },
    async getCurrentUser() { return this.get('/auth/me', { timeout: 10000 }); },
    async getPreferences() { return this.get('/auth/preferences', { timeout: 10000 }); },
    async savePreferences(prefs) { return this.put('/auth/preferences', prefs, { timeout: 10000 }); },
    async getHealth() { return this.get('/health', { timeout: 5000 }); },
    async getActiveModel() { return this.get('/api/model', { timeout: 10000 }); },
    async getTasks() { return this.get('/api/tasks', { timeout: 10000 }); }
};
