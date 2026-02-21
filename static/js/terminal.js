/**
 * Terminal Output Manager — with ANSI stripping and auto-scroll
 */
const Terminal = {
    container: null,
    panel: null,
    maxLines: 2000,

    init(containerId, panelId) {
        this.container = document.getElementById(containerId);
        this.panel = document.getElementById(panelId);
    },

    show() {
        if (this.panel) {
            this.panel.style.display = 'flex';
            this.panel.style.flexDirection = 'column';
        }
    },

    hide() {
        if (this.panel) this.panel.style.display = 'none';
    },

    toggle() {
        if (!this.panel) return;
        const isHidden = this.panel.style.display === 'none' || !this.panel.style.display;
        if (isHidden) this.show(); else this.hide();
    },

    isVisible() {
        return this.panel && this.panel.style.display !== 'none' && this.panel.style.display !== '';
    },

    write(text, type = 'stdout') {
        if (!this.container) return;
        this.show();

        const clean = this._stripAnsi(String(text || ''));
        if (!clean.trim() && type === 'stdout') return; // Skip empty stdout lines

        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        line.textContent = clean;
        this.container.appendChild(line);

        // Limit lines
        while (this.container.children.length > this.maxLines) {
            this.container.removeChild(this.container.firstChild);
        }

        this.container.scrollTop = this.container.scrollHeight;
    },

    writeSystem(text)  { this.write(text, 'system'); },
    writeError(text)   { this.write(text, 'stderr'); },
    writeSuccess(text) { this.write(text, 'success'); },

    clear() {
        if (this.container) this.container.innerHTML = '';
    },

    // Strip ANSI escape codes (colors, cursor movement, etc.)
    _stripAnsi(str) {
        // Remove standard ANSI escape sequences
        return str.replace(/\x1b\[[0-9;]*[mGKHFABCDJh]/g, '')
                  .replace(/\x1b\][^\x07]*\x07/g, '')
                  .replace(/\x1b[()][AB012]/g, '')
                  .replace(/[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]/g, ''); // Control chars except \t\n\r
    }
};
