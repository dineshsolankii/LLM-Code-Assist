/**
 * Toast Notification System — with progress bar, dismiss on click, dedup
 */
const Notify = {
    container: null,
    _active: new Set(),

    init() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;max-width:440px;';
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'info', duration = 5000) {
        if (!this.container) this.init();

        // Deduplicate same message
        const key = `${type}:${message}`;
        if (this._active.has(key)) return;
        this._active.add(key);

        const icons = {
            success: 'fa-check-circle',
            error:   'fa-exclamation-circle',
            info:    'fa-info-circle',
            warning: 'fa-exclamation-triangle'
        };
        const titles = { success: 'Success', error: 'Error', info: 'Info', warning: 'Warning' };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.style.setProperty('--duration', `${duration / 1000}s`);
        toast.innerHTML = `
            <i class="fas ${icons[type] || icons.info} toast-icon"></i>
            <div class="toast-body">
                <div class="toast-title">${titles[type]}</div>
                <div class="toast-message">${this._escapeHtml(message)}</div>
            </div>
            <button onclick="this.parentElement.remove()" style="background:none;border:none;color:currentColor;opacity:0.5;cursor:pointer;padding:0;margin-left:0.5rem;font-size:0.875rem;" title="Dismiss">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Dismiss on click anywhere on toast
        toast.addEventListener('click', () => {
            this._dismiss(toast, key);
        });

        this.container.appendChild(toast);

        // Auto-dismiss
        const timer = setTimeout(() => this._dismiss(toast, key), duration);
        toast._dismissTimer = timer;
    },

    _dismiss(toast, key) {
        if (!toast.parentElement) return;
        clearTimeout(toast._dismissTimer);
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(110%) scale(0.9)';
        setTimeout(() => {
            toast.remove();
            this._active.delete(key);
        }, 350);
    },

    _escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    },

    success(msg, dur) { this.show(msg, 'success', dur || 4000); },
    error(msg, dur)   { this.show(msg, 'error',   dur || 7000); },
    info(msg, dur)    { this.show(msg, 'info',     dur || 4000); },
    warning(msg, dur) { this.show(msg, 'warning',  dur || 5000); }
};

document.addEventListener('DOMContentLoaded', () => Notify.init());
