/**
 * SocketIO Connection Manager
 */
const Socket = {
    io: null,
    connected: false,
    handlers: {},
    _reconnecting: false,

    init() {
        if (typeof io === 'undefined') {
            console.warn('Socket.IO not loaded');
            return;
        }
        this.io = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 15,
            reconnectionDelayMax: 5000
        });

        this.io.on('connect', () => {
            this.connected = true;
            this._reconnecting = false;
            console.log('Socket connected:', this.io.id);
            this._updateStatusIndicator('connected');
            this._emit('connected');
        });

        this.io.on('disconnect', (reason) => {
            this.connected = false;
            console.warn('Socket disconnected:', reason);
            this._updateStatusIndicator('disconnected');
            this._emit('disconnected', { reason });
            // Reset running state on disconnect to avoid stuck UI
            if (typeof App !== 'undefined' && App._setRunning) {
                App._setRunning(false);
            }
        });

        this.io.on('reconnect_attempt', (attempt) => {
            this._reconnecting = true;
            console.log(`Socket reconnecting... attempt ${attempt}`);
            this._updateStatusIndicator('reconnecting');
        });

        this.io.on('reconnect', () => {
            this._reconnecting = false;
            console.log('Socket reconnected');
            this._updateStatusIndicator('connected');
        });

        this.io.on('reconnect_failed', () => {
            this._reconnecting = false;
            console.error('Socket reconnection failed');
            this._updateStatusIndicator('failed');
        });

        // Execution events
        this.io.on('execution_output', (data) => { this._emit('output', data); });
        this.io.on('execution_stopped', () => {
            this._emit('stopped');
            if (typeof App !== 'undefined' && App._setRunning) App._setRunning(false);
        });
        this.io.on('execution_finished', (data) => {
            this._emit('finished', data);
            if (typeof App !== 'undefined' && App._setRunning) App._setRunning(false);
        });
        this.io.on('execution_error', (data) => {
            this._emit('error', data);
            if (typeof App !== 'undefined' && App._setRunning) App._setRunning(false);
        });

        // Analysis events
        this.io.on('analysis_result', (data) => { this._emit('analysis_result', data); });
        this.io.on('analysis_progress', (data) => { this._emit('analysis_progress', data); });
        this.io.on('analysis_error', (data) => { this._emit('analysis_error', data); });
    },

    execute(projectName, fileName) {
        if (!this.io || !this.connected) {
            console.warn('Socket not connected, cannot execute');
            return false;
        }
        this.io.emit('execute', { projectName, fileName });
        return true;
    },

    stop() {
        if (!this.io) return;
        this.io.emit('stop_execution');
    },

    isConnected() {
        return this.connected;
    },

    on(event, callback) {
        if (!this.handlers[event]) this.handlers[event] = [];
        this.handlers[event].push(callback);
    },

    off(event, callback) {
        if (!this.handlers[event]) return;
        if (callback) {
            this.handlers[event] = this.handlers[event].filter(h => h !== callback);
        } else {
            delete this.handlers[event];
        }
    },

    _emit(event, data) {
        (this.handlers[event] || []).forEach(h => {
            try { h(data); } catch(e) { console.error('Socket handler error:', e); }
        });
    },

    _updateStatusIndicator(state) {
        const el = document.getElementById('connection-status');
        if (!el) return;
        el.className = 'connection-status';
        const dot = el.querySelector('.conn-dot');
        const text = el.querySelector('.conn-text');

        if (state === 'connected') {
            el.style.opacity = '0';
            setTimeout(() => { el.style.opacity = ''; }, 2000);
            if (dot) dot.className = 'conn-dot connected';
            if (text) text.textContent = 'Connected';
        } else if (state === 'disconnected') {
            el.style.opacity = '1';
            if (dot) dot.className = 'conn-dot disconnected';
            if (text) text.textContent = 'Disconnected';
        } else if (state === 'reconnecting') {
            el.style.opacity = '1';
            if (dot) dot.className = 'conn-dot reconnecting';
            if (text) text.textContent = 'Reconnecting...';
        } else if (state === 'failed') {
            el.style.opacity = '1';
            if (dot) dot.className = 'conn-dot disconnected';
            if (text) text.textContent = 'Connection failed';
        }
    }
};
