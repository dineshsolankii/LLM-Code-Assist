/**
 * CodeMirror Editor Wrapper — with unsaved indicator and active line
 */
const Editor = {
    instance: null,
    element: null,
    currentFile: null,
    modified: false,

    init(elementId) {
        this.element = document.getElementById(elementId);
        if (!this.element || typeof CodeMirror === 'undefined') return;

        this.instance = CodeMirror(this.element, {
            theme: 'dracula',
            lineNumbers: true,
            matchBrackets: true,
            autoCloseBrackets: true,
            styleActiveLine: true,
            indentUnit: 4,
            tabSize: 4,
            indentWithTabs: false,
            lineWrapping: true,
            mode: 'python',
            extraKeys: {
                'Ctrl-S': () => { if (typeof App !== 'undefined') App.saveCurrentFile(); },
                'Cmd-S':  () => { if (typeof App !== 'undefined') App.saveCurrentFile(); },
                'Tab': (cm) => { cm.execCommand(cm.somethingSelected() ? 'indentMore' : 'insertSoftTab'); }
            }
        });

        this.instance.on('change', () => {
            if (!this.modified) {
                this.modified = true;
                if (this.currentFile && typeof App !== 'undefined') {
                    App.markTabModified(this.currentFile, true);
                }
            }
        });
    },

    setValue(content, mode) {
        if (!this.instance) return;
        this.instance.setValue(content || '');
        if (mode) this.instance.setOption('mode', mode);
        this.modified = false;
        this.instance.clearHistory();
        setTimeout(() => this.instance.refresh(), 50);
    },

    getValue() {
        return this.instance ? this.instance.getValue() : '';
    },

    setMode(filename) {
        if (!this.instance) return;
        const ext = (filename.split('.').pop() || '').toLowerCase();
        const modes = {
            'py':   'python',
            'js':   'javascript',
            'html': 'htmlmixed',
            'css':  'css',
            'json': { name: 'javascript', json: true },
            'xml':  'xml',
            'md':   'markdown',
            'txt':  'text/plain',
            'yml':  'yaml',
            'yaml': 'yaml',
            'sh':   'shell',
            'bash': 'shell',
            'toml': 'text/plain',
            'ini':  'text/plain'
        };
        this.instance.setOption('mode', modes[ext] || 'text/plain');
    },

    setFontSize(size) {
        if (!this.element) return;
        this.element.style.fontSize = size + 'px';
        if (this.instance) this.instance.refresh();
    },

    setTabSize(size) {
        if (!this.instance) return;
        this.instance.setOption('tabSize', size);
        this.instance.setOption('indentUnit', size);
    },

    setLineWrapping(wrap) {
        if (!this.instance) return;
        this.instance.setOption('lineWrapping', wrap);
    },

    focus() {
        if (this.instance) this.instance.focus();
    },

    refresh() {
        if (this.instance) setTimeout(() => this.instance.refresh(), 100);
    }
};
