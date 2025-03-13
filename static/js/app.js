// LLM Code Assist - Main Application JavaScript

// Initialize the application when DOM is loaded
let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new CodeAssistApp();
    app.init();
});

class CodeAssistApp {
    constructor() {
        // Initialize settings
        this.settings = {
            theme: localStorage.getItem('theme') || 'dark',
            displayName: localStorage.getItem('displayName') || '',
            autoSave: localStorage.getItem('autoSave') !== 'false',
            lineNumbers: localStorage.getItem('lineNumbers') !== 'false',
            wordWrap: localStorage.getItem('wordWrap') !== 'false',
            autoIndent: localStorage.getItem('autoIndent') !== 'false'
        };

        // State
        this.currentScreen = 'welcome-screen';
        this.currentProject = null;
        this.currentFile = null;
        this.openFiles = {};
        this.editors = {};
        this.analysisResult = null;
        this.socket = null;
        this.isTerminalVisible = true;
        
        // DOM Elements - Using querySelector instead of getElementById for more reliable selection
        this.screens = {
            welcome: document.querySelector('#welcome-screen'),
            projectCreation: document.querySelector('#project-creation-screen'),
            projectList: document.querySelector('#project-list-screen'),
            projectEditor: document.querySelector('#project-editor-screen')
        };
        
        // Buttons - Using querySelector for more reliable selection
        this.buttons = {
            newProject: document.querySelector('#new-project-btn'),
            projects: document.querySelector('#projects-btn'),
            settings: document.querySelector('#settings-btn'),
            createProject: document.querySelector('#create-project-btn'),
            browseProjects: document.querySelector('#browse-projects-btn'),
            closeSettings: document.querySelector('#close-settings-btn'),
            saveSettings: document.querySelector('#save-settings-btn'),
            cancelSettings: document.querySelector('#cancel-settings-btn'),
            analyzeBtn: document.querySelector('#analyze-btn'),
            createProjectConfirmBtn: document.querySelector('#create-project-confirm-btn'),
            modifyAnalysisBtn: document.querySelector('#modify-analysis-btn'),
            refreshProjectsBtn: document.querySelector('#refresh-projects-btn'),
            runProjectBtn: document.querySelector('#run-project-btn'),
            installDepsBtn: document.querySelector('#install-deps-btn'),
            saveFileBtn: document.querySelector('#save-file-btn'),
            customizeCodeBtn: document.querySelector('#customize-code-btn'),
            newFileBtn: document.querySelector('#new-file-btn'),
            editorBackBtn: document.querySelector('#editor-back-btn')
        };
        
        // Dialogs
        this.dialogs = {
            settings: document.querySelector('#settings-dialog'),
            customization: document.querySelector('#customization-dialog'),
            newFile: document.querySelector('#new-file-dialog')
        };
        
        // Loading overlay
        this.loadingOverlay = document.querySelector('#loading-overlay');
        this.loadingMessage = document.querySelector('#loading-message');
        
        // Terminal elements
        this.terminal = document.querySelector('#terminal');
        this.terminalOutput = document.querySelector('#terminal-output');
        this.terminalToggle = document.querySelector('#terminal-toggle');
        this.terminalContent = document.querySelector('#terminal-content');

        // Notification element
        this.notification = document.querySelector('#notification');

        // Bind methods to preserve 'this' context
        this.showScreen = this.showScreen.bind(this);
        this.showNotification = this.showNotification.bind(this);
        this.applyTheme = this.applyTheme.bind(this);
        this.saveSettings = this.saveSettings.bind(this);
        this.loadSettings = this.loadSettings.bind(this);
        this.initSettingsDialog = this.initSettingsDialog.bind(this);
        this.analyzeRequirements = this.analyzeRequirements.bind(this);
        this.createProject = this.createProject.bind(this);
        this.loadProjects = this.loadProjects.bind(this);
        this.filterProjects = this.filterProjects.bind(this);
        this.runProject = this.runProject.bind(this);
        this.installDependencies = this.installDependencies.bind(this);
        this.saveCurrentFile = this.saveCurrentFile.bind(this);
        this.showCustomizationDialog = this.showCustomizationDialog.bind(this);
        this.hideCustomizationDialog = this.hideCustomizationDialog.bind(this);
        this.showNewFileDialog = this.showNewFileDialog.bind(this);
        this.hideNewFileDialog = this.hideNewFileDialog.bind(this);
        this.createNewFile = this.createNewFile.bind(this);
        this.toggleTerminal = this.toggleTerminal.bind(this);
        this.clearTerminal = this.clearTerminal.bind(this);
    }

    showNotification(message, type = 'info') {
        if (!this.notification || !message) return;

        // Clear existing timeouts
        if (this._notificationTimeout) {
            clearTimeout(this._notificationTimeout);
        }

        // Update notification content
        const iconClass = type === 'success' ? 
                         'fa-check-circle' : 
                         type === 'error' ? 
                         'fa-exclamation-circle' : 
                         type === 'warning' ? 
                         'fa-exclamation-triangle' : 'fa-info-circle';
        
        const icon = this.notification.querySelector('i');
        const text = this.notification.querySelector('span');
        
        if (icon) icon.className = `fas ${iconClass}`;
        if (text) text.textContent = message;
        
        // Add the notification
        this.notification.className = `notification ${type} show`;
        
        // Auto-hide after 3 seconds
        this._notificationTimeout = setTimeout(() => {
            this.notification.classList.remove('show');
        }, 3000);
    }

    applyTheme(theme) {
        if (!theme) return;
        document.documentElement.setAttribute('data-theme', theme);
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
    }

    saveSettings() {
        if (!this.dialogs.settings) return;

        try {
            // Get form values
            let displayNameInput = this.dialogs.settings.querySelector('#display-name');
            let autoSaveCheckbox = this.dialogs.settings.querySelector('#auto-save');
            let lineNumbersCheckbox = this.dialogs.settings.querySelector('#line-numbers');
            let wordWrapCheckbox = this.dialogs.settings.querySelector('#word-wrap');
            let autoIndentCheckbox = this.dialogs.settings.querySelector('#auto-indent');

            // Update settings object
            if (displayNameInput) this.settings.displayName = displayNameInput.value;
            if (autoSaveCheckbox) this.settings.autoSave = autoSaveCheckbox.checked;
            if (lineNumbersCheckbox) this.settings.lineNumbers = lineNumbersCheckbox.checked;
            if (wordWrapCheckbox) this.settings.wordWrap = wordWrapCheckbox.checked;
            if (autoIndentCheckbox) this.settings.autoIndent = autoIndentCheckbox.checked;

            // Save to localStorage
            Object.entries(this.settings).forEach(([key, value]) => {
                localStorage.setItem(key, value);
            });

            this.showNotification('Settings saved successfully', 'success');
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showNotification('Failed to save settings', 'error');
        }
    }

    loadSettings() {
        if (!this.settings || !this.dialogs.settings) return;

        // Apply saved theme
        this.applyTheme(this.settings.theme);
        
        // Update theme buttons
        let themeButtons = this.dialogs.settings.querySelectorAll('.theme-btn');
        themeButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === this.settings.theme);
        });

        // Update form inputs
        let displayNameInput = this.dialogs.settings.querySelector('#display-name');
        let autoSaveCheckbox = this.dialogs.settings.querySelector('#auto-save');
        let lineNumbersCheckbox = this.dialogs.settings.querySelector('#line-numbers');
        let wordWrapCheckbox = this.dialogs.settings.querySelector('#word-wrap');
        let autoIndentCheckbox = this.dialogs.settings.querySelector('#auto-indent');

        if (displayNameInput) displayNameInput.value = this.settings.displayName;
        if (autoSaveCheckbox) autoSaveCheckbox.checked = this.settings.autoSave;
        if (lineNumbersCheckbox) lineNumbersCheckbox.checked = this.settings.lineNumbers;
        if (wordWrapCheckbox) wordWrapCheckbox.checked = this.settings.wordWrap;
        if (autoIndentCheckbox) autoIndentCheckbox.checked = this.settings.autoIndent;

        // Apply editor settings if editor exists
        if (this.editor) {
            this.editor.setOption('lineNumbers', this.settings.lineNumbers);
            this.editor.setOption('lineWrapping', this.settings.wordWrap);
            this.editor.setOption('smartIndent', this.settings.autoIndent);
        }
    }

    initSettingsDialog() {
        if (!this.dialogs.settings) return;

        // Set up theme buttons
        const themeButtons = this.dialogs.settings.querySelectorAll('.theme-btn');
        themeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const theme = btn.dataset.theme;
                if (theme) {
                    this.settings.theme = theme;
                    this.applyTheme(theme);
                }
            });
        });
    }

    init() {
        console.log('Initializing LLM Code Assist App...');
        
        // Apply theme first
        this.applyTheme(this.settings.theme);
        
        // Initialize Socket.IO
        this.initSocketIO();
        
        // Initialize settings dialog
        this.initSettingsDialog();
        
        // Initialize event listeners
        this.initEventListeners();
        
        // Load frameworks
        this.loadFrameworks();

        // Show welcome screen by default
        this.showScreen('welcome');
        
        console.log('App initialization complete');
    }

    initEventListeners() {
        console.log('Setting up event listeners...');
        
        // Navigation buttons in header
        if (this.buttons.newProject) {
            this.buttons.newProject.addEventListener('click', () => {
                console.log('New Project button clicked');
                this.showScreen('projectCreation');
            });
        }
        
        if (this.buttons.projects) {
            this.buttons.projects.addEventListener('click', () => {
                console.log('Projects button clicked');
                this.loadProjects();
                this.showScreen('projectList');
            });
        }
        
        if (this.buttons.settings) {
            this.buttons.settings.addEventListener('click', () => {
                console.log('Settings button clicked');
                this.loadSettings();
                this.dialogs.settings.classList.add('active');
            });
        }
        
        // Welcome screen buttons
        if (this.buttons.createProject) {
            this.buttons.createProject.addEventListener('click', () => {
                console.log('Create Project button clicked');
                this.showScreen('projectCreation');
            });
        }
        
        if (this.buttons.browseProjects) {
            this.buttons.browseProjects.addEventListener('click', () => {
                console.log('Browse Projects button clicked');
                this.loadProjects();
                this.showScreen('projectList');
            });
        }
        
        // Settings dialog buttons
        if (this.buttons.closeSettings) {
            this.buttons.closeSettings.addEventListener('click', () => {
                console.log('Close Settings button clicked');
                this.dialogs.settings.classList.remove('active');
            });
        }
        
        if (this.buttons.saveSettings) {
            this.buttons.saveSettings.addEventListener('click', () => {
                console.log('Save Settings button clicked');
                this.saveSettings();
                this.dialogs.settings.classList.remove('active');
            });
        }
        
        if (this.buttons.cancelSettings) {
            this.buttons.cancelSettings.addEventListener('click', () => {
                console.log('Cancel Settings button clicked');
                this.dialogs.settings.classList.remove('active');
            });
        }
        
        // Back buttons
        document.querySelectorAll('.back-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                console.log('Back button clicked');
                this.showScreen('welcome');
            });
        });
        
        if (this.buttons.editorBackBtn) {
            this.buttons.editorBackBtn.addEventListener('click', () => {
                console.log('Editor Back button clicked');
                this.loadProjects();
                this.showScreen('projectList');
            });
        }
        
        // Project creation
        if (this.buttons.analyzeBtn) {
            console.log('Setting up analyze button click handler');
            this.buttons.analyzeBtn.addEventListener('click', this.analyzeRequirements);
        } else {
            console.error('Analyze button not found');
        }
        
        if (this.buttons.createProjectConfirmBtn) {
            this.buttons.createProjectConfirmBtn.addEventListener('click', () => {
                console.log('Create Project Confirm button clicked');
                this.createProject();
            });
        }
        
        if (this.buttons.modifyAnalysisBtn) {
            this.buttons.modifyAnalysisBtn.addEventListener('click', () => {
                console.log('Modify Analysis button clicked');
                const analysisResult = document.querySelector('#analysis-result');
                const createBtn = document.querySelector('#create-project-confirm-btn');
                const modifyBtn = document.querySelector('#modify-analysis-btn');
                
                if (analysisResult) analysisResult.style.display = 'none';
                if (createBtn) createBtn.style.display = 'none';
                if (modifyBtn) modifyBtn.style.display = 'none';
            });
        }
        
        // Project list
        if (this.buttons.refreshProjectsBtn) {
            this.buttons.refreshProjectsBtn.addEventListener('click', () => {
                console.log('Refresh Projects button clicked');
                this.loadProjects();
            });
        }
        
        const projectSearch = document.querySelector('#project-search');
        if (projectSearch) {
            projectSearch.addEventListener('input', (e) => {
                console.log('Project search input:', e.target.value);
                this.filterProjects(e.target.value);
            });
        }
        
        // Editor actions
        if (this.buttons.runProjectBtn) {
            this.buttons.runProjectBtn.addEventListener('click', () => {
                console.log('Run Project button clicked');
                this.runProject();
            });
        }
        
        if (this.buttons.installDepsBtn) {
            this.buttons.installDepsBtn.addEventListener('click', () => {
                console.log('Install Dependencies button clicked');
                this.installDependencies();
            });
        }
        
        if (this.buttons.saveFileBtn) {
            this.buttons.saveFileBtn.addEventListener('click', () => {
                console.log('Save File button clicked');
                this.saveCurrentFile();
            });
        }
        
        if (this.buttons.customizeCodeBtn) {
            this.buttons.customizeCodeBtn.addEventListener('click', () => {
                console.log('Customize Code button clicked');
                this.showCustomizationDialog();
            });
        }
        
        if (this.buttons.newFileBtn) {
            this.buttons.newFileBtn.addEventListener('click', () => {
                console.log('New File button clicked');
                this.showNewFileDialog();
            });
        }
        
        // Terminal controls
        const toggleTerminalBtn = document.querySelector('#toggle-terminal-btn');
        if (toggleTerminalBtn) {
            toggleTerminalBtn.addEventListener('click', () => {
                console.log('Toggle Terminal button clicked');
                this.toggleTerminal();
            });
        }
        
        const clearTerminalBtn = document.querySelector('#clear-terminal-btn');
        if (clearTerminalBtn) {
            clearTerminalBtn.addEventListener('click', () => {
                console.log('Clear Terminal button clicked');
                this.clearTerminal();
            });
        }
        
        // Customization dialog
        const applyCustomizationBtn = document.querySelector('#apply-customization-btn');
        if (applyCustomizationBtn) {
            applyCustomizationBtn.addEventListener('click', () => {
                console.log('Apply Customization button clicked');
                this.applyCustomization();
            });
        }
        
        const closeCustomizationBtn = document.querySelector('#close-customization-btn');
        const cancelCustomizationBtn = document.querySelector('#cancel-customization-btn');
        [closeCustomizationBtn, cancelCustomizationBtn].filter(Boolean).forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    console.log('Close/Cancel Customization button clicked');
                    this.hideCustomizationDialog();
                });
            }
        });
        
        // New file dialog
        const createFileBtn = document.querySelector('#create-file-btn');
        if (createFileBtn) {
            createFileBtn.addEventListener('click', () => {
                console.log('Create File button clicked');
                this.createNewFile();
            });
        }
        
        const closeNewFileBtn = document.querySelector('#close-new-file-btn');
        const cancelNewFileBtn = document.querySelector('#cancel-new-file-btn');
        [closeNewFileBtn, cancelNewFileBtn].filter(Boolean).forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    console.log('Close/Cancel New File button clicked');
                    this.hideNewFileDialog();
                });
            }
        });
        
        console.log('Event listeners setup complete');
    }

    showScreen(screenId) {
        console.log(`Showing screen: ${screenId}`);
        
        if (!screenId || !this.screens) {
            console.error('Invalid screen ID or screens not initialized');
            return;
        }

        // Hide all screens
        Object.values(this.screens).forEach(screen => {
            if (screen) {
                screen.style.display = 'none';
                screen.classList.remove('active');
            }
        });

        // Show the requested screen
        const targetScreen = this.screens[screenId];
        if (targetScreen) {
            targetScreen.style.display = 'block';
            targetScreen.classList.add('active');
            this.currentScreen = screenId;
            console.log(`Screen ${screenId} is now active`);
        } else {
            console.error(`Screen ${screenId} not found`);
        }
    }
    
    initSocketIO() {
        try {
            console.log('Initializing Socket.IO connection...');
            
            // Initialize Socket.IO with reconnection options
            this.socket = io({
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                timeout: 20000,
                transports: ['websocket', 'polling']
            });
            
            this.socket.on('connect', () => {
                console.log('Connected to server via Socket.IO');
                this.showNotification('Connected to server', 'success');
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Socket.IO connection error:', error);
                this.showNotification('Connection error. Attempting to reconnect...', 'error');
            });
            
            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from server:', reason);
                if (reason !== 'io client disconnect') {
                    this.showNotification('Disconnected from server. Attempting to reconnect...', 'warning');
                }
            });
            
            this.socket.on('reconnect', (attemptNumber) => {
                console.log(`Reconnected to server after ${attemptNumber} attempts`);
                this.showNotification('Reconnected to server', 'success');
            });
            
            this.socket.on('reconnect_failed', () => {
                console.error('Failed to reconnect to server');
                this.showNotification('Failed to reconnect to server. Please refresh the page.', 'error');
            });
            
            // Listen for command output from the server
            this.socket.on('command_output', (data) => {
                console.log('Received command output:', data);
                this.handleCommandOutput(data);
            });
            
            // Listen for analysis results
            this.socket.on('analysis_result', (data) => {
                console.log('Received analysis result:', data);
                if (data.success) {
                    this.analysisResult = data.analysis;
                    this.renderAnalysisResult(data.analysis);
                    this.showNotification('Analysis complete', 'success');
                } else {
                    this.showNotification(data.error || 'Failed to analyze requirements', 'error');
                }
                this.hideLoading();
            });
            
            // Listen for analysis errors
            this.socket.on('analysis_error', (error) => {
                console.error('Analysis error:', error);
                this.showNotification(error.message || 'Failed to analyze requirements', 'error');
                this.hideLoading();
            });
            
        } catch (error) {
            console.error('Error initializing Socket.IO:', error);
            this.showNotification('Failed to initialize real-time connection', 'error');
        }
    }
    
    handleCommandOutput(data) {
        if (!data) return;
        
        console.log('Processing command output:', data);
        
        try {
            if (typeof data === 'string') {
                this.appendToTerminal(data + '\n');
                return;
            }
            
            const { type, content } = data;
            
            switch (type) {
                case 'stdout':
                    this.appendToTerminal(content, 'terminal-output');
                    break;
                case 'stderr':
                    this.appendToTerminal(content, 'terminal-error');
                    break;
                case 'info':
                    this.appendToTerminal(content, 'terminal-info');
                    break;
                case 'success':
                    this.appendToTerminal(content, 'terminal-success');
                    break;
                case 'command':
                    this.appendToTerminal(`$ ${content}\n`, 'terminal-command');
                    break;
                default:
                    this.appendToTerminal(content);
            }
        } catch (error) {
            console.error('Error handling command output:', error);
            this.appendToTerminal('Error processing command output\n', 'terminal-error');
        }
    }
    
    showLoading(message = 'Loading...') {
        if (!this.loadingOverlay || !this.loadingMessage) return;
        
        this.loadingMessage.textContent = message;
        this.loadingOverlay.classList.add('active');
    }
    
    hideLoading() {
        if (!this.loadingOverlay) return;
        
        this.loadingOverlay.classList.remove('active');
    }
    
    showCustomizationDialog() {
        if (!this.currentFile) {
            this.showNotification('Please open a file first', 'error');
            return;
        }
        
        document.getElementById('customization-request').value = '';
        this.dialogs.customization.classList.add('active');
    }
    
    hideCustomizationDialog() {
        this.dialogs.customization.classList.remove('active');
    }
    
    showNewFileDialog() {
        document.getElementById('new-file-path').value = '';
        this.dialogs.newFile.classList.add('active');
    }
    
    hideNewFileDialog() {
        this.dialogs.newFile.classList.remove('active');
    }
    
    handleCommandOutput(data) {
        if (!data) return;
        
        try {
            // If data is a string, try to parse it as JSON
            if (typeof data === 'string') {
                try {
                    data = JSON.parse(data);
                } catch (e) {
                    // If it's not JSON, treat it as plain text output
                    this.appendToTerminal(data + '\n', 'terminal-output');
                    return;
                }
            }
            
            // Handle different types of output
            if (data.type === 'output') {
                const output = typeof data.data === 'object' ? 
                    JSON.stringify(data.data, null, 2) : 
                    String(data.data);
                this.appendToTerminal(output + '\n', 'terminal-output');
            } else if (data.type === 'error') {
                const error = typeof data.data === 'object' ? 
                    JSON.stringify(data.data, null, 2) : 
                    String(data.data);
                this.appendToTerminal(`Error: ${error}\n`, 'terminal-error');
            } else if (data.type === 'done') {
                if (data.data && data.data.status === 'error') {
                    const error = typeof data.data.message === 'object' ? 
                        JSON.stringify(data.data.message, null, 2) : 
                        String(data.data.message);
                    this.appendToTerminal(`Error: ${error}\n`, 'terminal-error');
                } else if (data.data && data.data.status === 'success') {
                    const message = typeof data.data.message === 'object' ? 
                        JSON.stringify(data.data.message, null, 2) : 
                        String(data.data.message);
                    this.appendToTerminal(`${message}\n`, 'terminal-success');
                } else {
                    this.appendToTerminal('Command completed successfully\n', 'terminal-success');
                }
            }
        } catch (error) {
            console.error('Error handling command output:', error);
            this.appendToTerminal(`Error handling output: ${error.message}\n`, 'terminal-error');
        }
    }
    
    appendToTerminal(text, className = '') {
        if (!this.terminalContent) {
            this.terminalContent = document.querySelector('#terminal-content');
            if (!this.terminalContent) return;
        }
        
        const span = document.createElement('span');
        if (className) {
            span.className = className;
        }
        
        // Handle ANSI color codes (basic support)
        const ansiColorRegex = /\x1b\[\d+m(.*?)(\x1b\[0m|$)/g;
        if (ansiColorRegex.test(text)) {
            // If text contains ANSI color codes, replace them with styled spans
            const coloredText = text.replace(ansiColorRegex, (match, content) => {
                return content;
            });
            span.textContent = coloredText;
        } else {
            span.textContent = text;
        }
        
        this.terminalContent.appendChild(span);
        
        // Auto-scroll to bottom
        this.terminalContent.scrollTop = this.terminalContent.scrollHeight;
    }
    
    // Framework loading
    loadFrameworks() {
        this.showLoading('Loading frameworks...');
        
        fetch('/api/frameworks')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.renderFrameworks(data.frameworks);
                } else {
                    this.showNotification('Failed to load frameworks', 'error');
                }
                this.hideLoading();
            })
            .catch(error => {
                console.error('Error loading frameworks:', error);
                this.showNotification('Failed to load frameworks', 'error');
                this.hideLoading();
            });
    }
    
    renderFrameworks(frameworks) {
        const container = document.getElementById('framework-options');
        container.innerHTML = '';
        
        frameworks.forEach(framework => {
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'framework';
            radio.value = framework.id;
            radio.id = `framework-${framework.id}`;
            
            const label = document.createElement('label');
            label.htmlFor = `framework-${framework.id}`;
            label.textContent = framework.name;
            
            container.appendChild(radio);
            container.appendChild(label);
        });
    }
    
    // Project Analysis and Creation
    analyzeRequirements() {
        console.log('Analyzing requirements...');
        
        const projectName = document.getElementById('project-name').value.trim();
        const projectRequirements = document.getElementById('project-requirements').value.trim();
        const selectedFramework = document.querySelector('input[name="framework"]:checked');
        
        // Validate inputs
        if (!projectName) {
            this.showNotification('Please enter a project name', 'error');
            return;
        }
        
        if (!projectRequirements) {
            this.showNotification('Please describe your project requirements', 'error');
            return;
        }

        if (!selectedFramework) {
            this.showNotification('Please select a framework', 'error');
            return;
        }
        
        // Reset previous analysis results
        const analysisResult = document.querySelector('#analysis-result');
        const createBtn = document.querySelector('#create-project-confirm-btn');
        const modifyBtn = document.querySelector('#modify-analysis-btn');
        
        if (analysisResult) analysisResult.style.display = 'none';
        if (createBtn) createBtn.style.display = 'none';
        if (modifyBtn) modifyBtn.style.display = 'none';
        
        // Show loading state
        this.showLoading('Analyzing requirements...');
        
        // Check Socket.IO connection
        if (!this.socket || !this.socket.connected) {
            console.error('Socket.IO not connected');
            this.showNotification('Connection error. Please refresh the page.', 'error');
            this.hideLoading();
            return;
        }
        
        // Emit analysis request via Socket.IO
        this.socket.emit('analyze_requirements', {
            name: projectName,
            requirements: projectRequirements,
            framework: selectedFramework.value
        });
    }
    
    renderAnalysisResult(analysis) {
        console.log('Rendering analysis result:', analysis);
        
        const container = document.querySelector('#analysis-content');
        if (!container) {
            console.error('Analysis content container not found');
            return;
        }
        
        try {
            // Format the analysis content with proper escaping and null/undefined checking
            const description = analysis.description ? this.escapeHtml(analysis.description) : 'No description available';
            const projectType = analysis.project_type ? this.escapeHtml(analysis.project_type) : 'Not specified';
            
            // Ensure features and dependencies are arrays before processing
            const features = Array.isArray(analysis.features) ? analysis.features : [];
            const dependencies = Array.isArray(analysis.suggested_packages) ? analysis.suggested_packages : [];
            
            let html = `
                <div class="analysis-section">
                    <h4>Project Type</h4>
                    <p>${projectType}</p>
                </div>
                <div class="analysis-section">
                    <h4>Description</h4>
                    <p>${description}</p>
                </div>
            `;
            
            if (features.length > 0) {
                html += `
                    <div class="analysis-section">
                        <h4>Key Features</h4>
                        <ul>
                            ${features.map(feature => {
                                // Handle both string features and object features
                                if (typeof feature === 'string') {
                                    return `<li>${this.escapeHtml(feature)}</li>`;
                                } else if (feature && typeof feature === 'object') {
                                    const featureName = feature.name || 'Unnamed Feature';
                                    const featureDesc = feature.description || '';
                                    return `<li><strong>${this.escapeHtml(featureName)}</strong>: ${this.escapeHtml(featureDesc)}</li>`;
                                }
                                return '';
                            }).join('')}
                        </ul>
                    </div>
                `;
            }
            
            if (dependencies.length > 0) {
                html += `
                    <div class="analysis-section">
                        <h4>Dependencies</h4>
                        <ul>
                            ${dependencies.map(dep => {
                                if (typeof dep === 'string') {
                                    return `<li>${this.escapeHtml(dep)}</li>`;
                                }
                                return '';
                            }).join('')}
                        </ul>
                    </div>
                `;
            }
            
            container.innerHTML = html;
            
            // Save the analysis result for later use
            this.analysisResult = analysis;
            
            // Show the analysis result and buttons
            const analysisResult = document.querySelector('#analysis-result');
            const createBtn = document.querySelector('#create-project-confirm-btn');
            const modifyBtn = document.querySelector('#modify-analysis-btn');
            
            if (analysisResult) analysisResult.style.display = 'block';
            if (createBtn) createBtn.style.display = 'block';
            if (modifyBtn) modifyBtn.style.display = 'block';
            
        } catch (error) {
            console.error('Error rendering analysis result:', error);
            this.showNotification('Error displaying analysis result', 'error');
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    createProject() {
        console.log('Creating project...');
        
        if (!this.analysisResult) {
            this.showNotification('Please analyze requirements first', 'error');
            return;
        }
        
        const projectName = document.getElementById('project-name').value.trim();
        const selectedFramework = document.querySelector('input[name="framework"]:checked');
        
        if (!projectName) {
            this.showNotification('Please enter a project name', 'error');
            return;
        }
        
        if (!selectedFramework) {
            this.showNotification('Please select a framework', 'error');
            return;
        }
        
        // Show loading state
        this.showLoading('Creating project...');
        
        // Prepare the analysis data, ensuring it has all required fields
        const analysisData = {
            ...this.analysisResult,
            project_type: this.analysisResult.project_type || 'Unknown',
            description: this.analysisResult.description || '',
            features: Array.isArray(this.analysisResult.features) ? this.analysisResult.features : [],
            suggested_packages: Array.isArray(this.analysisResult.suggested_packages) ? this.analysisResult.suggested_packages : []
        };
        
        // Make API request
        fetch('/api/project/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                projectName: projectName,
                framework: selectedFramework.value,
                analysis: analysisData,
                requirements: document.getElementById('project-requirements').value.trim()
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showNotification('Project created successfully', 'success');
                this.openProject(projectName);
            } else {
                throw new Error(data.error || 'Failed to create project');
            }
        })
        .catch(error => {
            console.error('Error creating project:', error);
            this.showNotification(error.message || 'Failed to create project', 'error');
        })
        .finally(() => {
            this.hideLoading();
        });
    }
    
    // Project Loading and File Management
    loadProjects() {
        this.showLoading('Loading projects...');
        
        fetch('/api/project')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.renderProjects(data.projects);
                } else {
                    this.showNotification('Failed to load projects: ' + data.error, 'error');
                }
                this.hideLoading();
            })
            .catch(error => {
                console.error('Error loading projects:', error);
                this.showNotification('Failed to load projects', 'error');
                this.hideLoading();
            });
    }
    
    renderProjects(projects) {
        const container = document.getElementById('project-grid');
        container.innerHTML = '';
        
        if (projects.length === 0) {
            container.innerHTML = '<div class="empty-state">No projects found. Create a new project to get started.</div>';
            return;
        }
        
        projects.forEach(project => {
            const card = document.createElement('div');
            card.className = 'project-card';
            
            // Format date
            const date = new Date(project.created_at);
            const formattedDate = date.toLocaleDateString();
            
            card.setAttribute('data-project', project.name);
            card.innerHTML = `
                <h3>${project.name}</h3>
                <p>${project.description || 'No description'}</p>
                <div class="project-meta">
                    <span>${project.framework || 'Unknown'}</span>
                    <span>${formattedDate}</span>
                </div>
                <div class="project-actions">
                    <button class="secondary-btn open-project-btn" title="Open project">
                        <i class="fas fa-folder-open"></i> Open
                    </button>
                    <button class="secondary-btn delete-project-btn" title="Delete project">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            `;
            
            // Add event listeners
            card.querySelector('.open-project-btn').addEventListener('click', () => {
                this.openProject(project.name);
            });
            
            card.querySelector('.delete-project-btn').addEventListener('click', () => {
                if (confirm(`Are you sure you want to delete ${project.name}?`)) {
                    this.deleteProject(project.name);
                }
            });
            
            container.appendChild(card);
        });
    }
    
    filterProjects(query) {
        query = query.toLowerCase();
        const cards = document.querySelectorAll('.project-card');
        
        cards.forEach(card => {
            const name = card.querySelector('h3').textContent.toLowerCase();
            const description = card.querySelector('p').textContent.toLowerCase();
            
            if (name.includes(query) || description.includes(query)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    openProject(projectName) {
        this.showLoading('Opening project...');
        this.currentProject = projectName;
        
        // Update UI - Check if element exists before setting content
        const projectNameElement = document.getElementById('editor-project-name');
        if (projectNameElement) {
            projectNameElement.textContent = projectName;
        }
        
        // Load project files
        this.loadProjectFiles(projectName);
        
        // Show editor screen
        this.showScreen('projectEditor');
        this.hideLoading();
    }
    
    deleteProject(projectName) {
        if (!projectName) {
            this.showNotification('Invalid project name', 'error');
            return;
        }

        // If this project is currently open, close it first
        if (this.currentProject === projectName) {
            this.currentProject = null;
            this.currentFile = null;
            this.openFiles = {};
            this.editors = {};
            this.showScreen('projectList');
        }

        this.showLoading('Deleting project...');
        
        fetch(`/api/project/${encodeURIComponent(projectName)}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showNotification(`Project ${projectName} deleted successfully`);
                // Remove the project card from UI immediately
                const projectCard = document.querySelector(`.project-card[data-project="${projectName}"]`);
                if (projectCard) {
                    projectCard.remove();
                }
                // Refresh project list
                this.loadProjects();
            } else {
                throw new Error(data.error || 'Failed to delete project');
            }
        })
        .catch(error => {
            console.error('Error deleting project:', error);
            this.showNotification(`Failed to delete project: ${error.message}`, 'error');
        })
        .finally(() => {
            this.hideLoading();
        });
    }
    
    loadProjectFiles(projectName) {
        this.showLoading('Loading project files...');
        
        fetch(`/api/project/${encodeURIComponent(projectName)}/files`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.renderFileTree(data.files);
                    
                    // Open README.md by default if it exists
                    const readmeFile = data.files.find(file => file.name.toLowerCase() === 'readme.md');
                    if (readmeFile) {
                        this.openFile(readmeFile.path);
                    } else if (data.files.length > 0) {
                        // Open the first file
                        this.openFile(data.files[0].path);
                    }
                } else {
                    this.showNotification('Failed to load project files: ' + data.error, 'error');
                }
                this.hideLoading();
            })
            .catch(error => {
                console.error('Error loading project files:', error);
                this.showNotification('Failed to load project files', 'error');
                this.hideLoading();
            });
    }
    
    renderFileTree(files) {
        const container = document.getElementById('file-tree');
        if (!container) {
            console.error('File tree container not found');
            this.showNotification('Failed to render file tree', 'error');
            return;
        }
        
        // Clear the container
        container.innerHTML = '';
        
        if (!files || files.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-tree-message';
            emptyMessage.textContent = 'No files found';
            container.appendChild(emptyMessage);
            return;
        }
        
        // Create a tree structure
        const tree = {};
        
        // Sort files to ensure consistent order
        files.sort((a, b) => a.path.localeCompare(b.path));
        
        files.forEach(file => {
            if (!file.path) {
                console.error('File path is missing:', file);
                return;
            }
            
            const parts = file.path.split('/');
            let current = tree;
            
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i];
                if (!part) continue; // Skip empty parts
                
                if (i === parts.length - 1) {
                    // This is a file
                    if (!current.files) current.files = [];
                    current.files.push({
                        name: part,
                        path: file.path,
                        type: file.type || 'file'
                    });
                } else {
                    // This is a directory
                    if (!current.dirs) current.dirs = {};
                    if (!current.dirs[part]) current.dirs[part] = {};
                    current = current.dirs[part];
                }
            }
        });
        
        // Render the tree starting from the root
        this.renderFileTreeNode(tree, container, '');
    }
    
    renderFileTreeNode(node, container, path) {
        const treeContainer = document.createElement('div');
        treeContainer.className = 'tree-container';
        
        // Render directories first
        if (node.dirs) {
            // Sort directories alphabetically
            const sortedDirs = Object.keys(node.dirs).sort();
            
            sortedDirs.forEach(dirName => {
                const dirNode = document.createElement('div');
                dirNode.className = 'directory-item';
                
                const dirHeader = document.createElement('div');
                dirHeader.className = 'directory-header';
                
                const expandIcon = document.createElement('i');
                expandIcon.className = 'fas fa-chevron-right';
                
                const folderIcon = document.createElement('i');
                folderIcon.className = 'fas fa-folder';
                
                const dirLabel = document.createElement('span');
                dirLabel.textContent = dirName;
                
                dirHeader.appendChild(expandIcon);
                dirHeader.appendChild(folderIcon);
                dirHeader.appendChild(dirLabel);
                
                const dirContent = document.createElement('div');
                dirContent.className = 'directory-content';
                dirContent.style.display = 'none';
                
                // Recursively render the directory's contents
                this.renderFileTreeNode(node.dirs[dirName], dirContent, path ? `${path}/${dirName}` : dirName);
                
                // Add click handler for directory expansion
                dirHeader.addEventListener('click', () => {
                    const isExpanded = dirContent.style.display !== 'none';
                    dirContent.style.display = isExpanded ? 'none' : 'block';
                    expandIcon.className = isExpanded ? 'fas fa-chevron-right' : 'fas fa-chevron-down';
                    folderIcon.className = isExpanded ? 'fas fa-folder' : 'fas fa-folder-open';
                });
                
                dirNode.appendChild(dirHeader);
                dirNode.appendChild(dirContent);
                treeContainer.appendChild(dirNode);
            });
        }
        
        // Then render files
        if (node.files && Array.isArray(node.files)) {
            // Sort files alphabetically
            const sortedFiles = [...node.files].sort((a, b) => a.name.localeCompare(b.name));
            
            sortedFiles.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                
                // Choose icon based on file extension
                let icon = 'fas fa-file';
                const ext = file.name.split('.').pop().toLowerCase();
                
                switch (ext) {
                    case 'py':
                        icon = 'fab fa-python';
                        break;
                    case 'js':
                        icon = 'fab fa-js';
                        break;
                    case 'html':
                        icon = 'fab fa-html5';
                        break;
                    case 'css':
                        icon = 'fab fa-css3-alt';
                        break;
                    case 'md':
                        icon = 'fas fa-file-alt';
                        break;
                    case 'json':
                        icon = 'fas fa-brackets-curly';
                        break;
                    case 'txt':
                        icon = 'fas fa-file-alt';
                        break;
                }
                
                fileItem.innerHTML = `<i class="${icon}"></i> <span>${file.name}</span>`;
                
                // Add click handler to open the file
                fileItem.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (this.openFile) {
                        console.log('Opening file:', file.path);
                        this.openFile(file.path);
                    } else {
                        console.error('openFile method not found');
                        this.showNotification('Failed to open file', 'error');
                    }
                });
                
                treeContainer.appendChild(fileItem);
            });
        }
        
        // Add the tree container to the parent container
        container.appendChild(treeContainer);
    }
    
    // File Editing
    openFile(filePath) {
        this.showLoading('Opening file...');
        
        // Get the project name
        const projectName = this.currentProject;
        
        if (!projectName) {
            console.error('No project selected');
            this.showNotification('No project selected', 'error');
            this.hideLoading();
            return;
        }
        
        if (!filePath) {
            console.error('No file path provided');
            this.showNotification('No file path provided', 'error');
            this.hideLoading();
            return;
        }
        
        console.log('Opening file:', filePath, 'in project:', projectName);

        // Make the API request to get file content
        const url = `/api/project/${encodeURIComponent(projectName)}/file?path=${encodeURIComponent(filePath)}`;
        console.log('Request URL:', url);
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('File content response:', data);
                if (data.success) {
                    this.renderFile(filePath, data.content);
                } else {
                    console.error('Failed to open file:', data.error);
                    this.showNotification('Failed to open file: ' + data.error, 'error');
                }
                this.hideLoading();
            })
            .catch(error => {
                console.error('Error opening file:', error);
                this.showNotification('Failed to open file: ' + error.message, 'error');
                this.hideLoading();
            });
    }
    
    renderFile(filePath, content) {
        // Update current file
        this.currentFile = filePath;
        
        // Get the code editor container
        const codeEditor = document.getElementById('code-editor');
        if (!codeEditor) {
            console.error('Code editor container not found');
            this.showNotification('Failed to initialize editor', 'error');
            return;
        }
        
        // Highlight the file in the tree
        document.querySelectorAll('.file-item.file').forEach(item => {
            item.classList.remove('active');
        });
        
        const fileItems = document.querySelectorAll('.file-item.file');
        for (let i = 0; i < fileItems.length; i++) {
            const item = fileItems[i];
            if (item.textContent.trim() === filePath.split('/').pop()) {
                item.classList.add('active');
                break;
            }
        }
        
        // Check if the file is already open
        if (this.openFiles[filePath]) {
            // Show the tab
            this.showTab(filePath);
            return;
        }
        
        // Create editor container
        const editorContainer = document.createElement('div');
        editorContainer.className = 'editor-instance';
        editorContainer.id = `editor-${this.sanitizeId(filePath)}`;
        editorContainer.style.display = 'none';
        
        // Append the editor container to the code editor
        codeEditor.appendChild(editorContainer);
        
        // Create a new tab
        this.createTab(filePath);
        
        // Initialize CodeMirror
        const editor = CodeMirror(editorContainer, {
            value: content || '',  // Ensure content is never null
            mode: this.getLanguageMode(filePath),
            theme: 'dracula',
            lineNumbers: true,
            indentUnit: 4,
            autoCloseBrackets: true,
            matchBrackets: true,
            styleActiveLine: true,
            lineWrapping: true,
            extraKeys: {
                'Tab': 'indentMore',
                'Shift-Tab': 'indentLess',
                'Ctrl-S': () => this.saveCurrentFile()
            }
        });
        
        // Store the editor instance
        this.editors[filePath] = editor;
        this.openFiles[filePath] = {
            path: filePath,
            name: filePath.split('/').pop(),
            editor: editor
        };
        
        // Show the tab
        this.showTab(filePath);
    }
    
    createTab(filePath) {
        const tabsContainer = document.getElementById('editor-tabs');
        if (!tabsContainer) {
            console.error('Editor tabs container not found');
            this.showNotification('Failed to create tab', 'error');
            return;
        }
        
        const fileName = filePath.split('/').pop();
        
        // Check if tab already exists
        const escapedPath = CSS.escape(filePath);
        const existingTab = tabsContainer.querySelector(`[data-file="${escapedPath}"]`);
        if (existingTab) {
            this.showTab(filePath);
            return;
        }
        
        const tab = document.createElement('div');
        tab.className = 'editor-tab';
        tab.dataset.file = filePath;
        
        // Choose icon based on file extension
        let icon = 'fas fa-file';
        const ext = fileName.split('.').pop().toLowerCase();
        
        switch (ext) {
            case 'py':
                icon = 'fab fa-python';
                break;
            case 'js':
                icon = 'fab fa-js';
                break;
            case 'html':
                icon = 'fab fa-html5';
                break;
            case 'css':
                icon = 'fab fa-css3-alt';
                break;
            case 'md':
                icon = 'fas fa-file-alt';
                break;
            case 'json':
                icon = 'fas fa-brackets-curly';
                break;
            case 'txt':
                icon = 'fas fa-file-alt';
                break;
        }
        
        tab.innerHTML = `
            <i class="${icon}"></i>
            <span>${fileName}</span>
            <button class="close-tab" title="Close">×</button>
        `;
        
        // Add event listeners
        tab.addEventListener('click', (e) => {
            // Don't trigger if clicking the close button
            if (!e.target.classList.contains('close-tab')) {
                this.showTab(filePath);
            }
        });
        
        const closeButton = tab.querySelector('.close-tab');
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeTab(filePath);
            });
        }
        
        // Add the tab to the container
        tabsContainer.appendChild(tab);
        
        // Make the new tab active
        this.showTab(filePath);
    }
    
    showTab(filePath) {
        // Hide all editors
        const codeEditor = document.getElementById('code-editor');
        if (!codeEditor) {
            console.error('Code editor container not found');
            this.showNotification('Failed to display file', 'error');
            return;
        }
        
        codeEditor.querySelectorAll('.editor-instance').forEach(editor => {
            editor.style.display = 'none';
        });
        
        // Show the selected editor
        const editorContainer = document.getElementById(`editor-${this.sanitizeId(filePath)}`);
        if (editorContainer) {
            editorContainer.style.display = 'block';
        } else {
            console.error('Editor container not found for file:', filePath);
            this.showNotification('Failed to display file', 'error');
            return;
        }
        
        // Update current file
        this.currentFile = filePath;
        
        // Update tabs
        const tabsContainer = document.getElementById('editor-tabs');
        if (tabsContainer) {
            // Remove active class from all tabs
            tabsContainer.querySelectorAll('.editor-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Add active class to the selected tab
            const escapedPath = CSS.escape(filePath);
            const tab = tabsContainer.querySelector(`[data-file="${escapedPath}"]`);
            if (tab) {
                tab.classList.add('active');
                
                // Ensure the tab is visible (scroll into view)
                tab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
            }
        }
        
        // Refresh the editor to ensure proper rendering
        if (this.editors[filePath]) {
            this.editors[filePath].refresh();
        }
    }
    
    closeTab(filePath) {
        // Check if the file is modified
        if (this.isFileModified(filePath)) {
            if (!confirm('This file has unsaved changes. Are you sure you want to close it?')) {
                return;
            }
        }
        
        // Remove the tab
        const tab = document.querySelector(`.editor-tab[data-file="${filePath}"]`);
        if (tab) {
            tab.remove();
        }
        
        // Remove the editor
        const editorContainer = document.getElementById(`editor-${this.sanitizeId(filePath)}`);
        if (editorContainer) {
            editorContainer.remove();
        }
        
        // Remove from open files
        delete this.editors[filePath];
        delete this.openFiles[filePath];
        
        // If this was the current file, show another tab
        if (this.currentFile === filePath) {
            const tabs = document.querySelectorAll('.editor-tab');
            if (tabs.length > 0) {
                this.showTab(tabs[0].dataset.file);
            } else {
                this.currentFile = null;
            }
        }
    }
    
    saveCurrentFile() {
        if (!this.currentFile) {
            this.showNotification('No file is currently open', 'error');
            return;
        }
        
        const editor = this.editors[this.currentFile];
        if (!editor) {
            this.showNotification('Editor not found', 'error');
            return;
        }
        
        const content = editor.getValue();
        
        // Extract project name and relative file path
        const projectName = this.currentProject;
        const relativePath = this.currentFile.startsWith(projectName + '/') ? 
            this.currentFile.substring(projectName.length + 1) : this.currentFile;
        
        this.showLoading('Saving file...');
        
        fetch(`/api/project/${encodeURIComponent(projectName)}/file`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: relativePath,
                content: content
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('File saved successfully');
                } else {
                    this.showNotification('Failed to save file: ' + data.error, 'error');
                }
                this.hideLoading();
            })
            .catch(error => {
                console.error('Error saving file:', error);
                this.showNotification('Failed to save file', 'error');
                this.hideLoading();
            });
    }
    
    isFileModified(filePath) {
        // TODO: Implement file modification tracking
        return false;
    }
    
    createNewFile() {
        const filePath = document.getElementById('new-file-path').value.trim();
        
        if (!filePath) {
            this.showNotification('Please enter a file path', 'error');
            return;
        }
        
        const projectName = this.currentProject;
        
        this.showLoading('Creating file...');
        
        fetch(`/api/project/${encodeURIComponent(projectName)}/file`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: filePath,
                content: ''
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('File created successfully');
                    this.hideNewFileDialog();
                    this.loadProjectFiles(this.currentProject);
                    // Use the full path for opening the file
                    const fullPath = this.currentProject + '/' + filePath;
                    this.openFile(fullPath);
                } else {
                    this.showNotification('Failed to create file: ' + data.error, 'error');
                }
                this.hideLoading();
            })
            .catch(error => {
                console.error('Error creating file:', error);
                this.showNotification('Failed to create file', 'error');
                this.hideLoading();
            });
    }
    
    applyCustomization() {
        const request = document.getElementById('customization-request').value.trim();
        
        if (!request) {
            this.showNotification('Please enter a customization request', 'error');
            return;
        }
        
        if (!this.currentFile) {
            this.showNotification('No file is currently open', 'error');
            return;
        }
        
        const editor = this.editors[this.currentFile];
        if (!editor) {
            this.showNotification('Editor not found', 'error');
            return;
        }
        
        const content = editor.getValue();
        
        // Extract project name and relative file path
        const projectName = this.currentProject;
        const relativePath = this.currentFile.startsWith(projectName + '/') ? 
            this.currentFile.substring(projectName.length + 1) : this.currentFile;
        
        this.showLoading('Customizing code...');
        this.hideCustomizationDialog();
        
        fetch('/api/customize-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                projectName: projectName,
                filePath: relativePath,
                currentCode: content,
                customizationRequest: request
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    editor.setValue(data.code);
                    this.showNotification('Code customized successfully');
                } else {
                    this.showNotification('Failed to customize code: ' + data.error, 'error');
                }
                this.hideLoading();
            })
            .catch(error => {
                console.error('Error customizing code:', error);
                this.showNotification('Failed to customize code', 'error');
                this.hideLoading();
            });
    }
    
    // Terminal functionality
    runProject() {
        if (!this.currentProject) {
            this.showNotification('No project is currently open', 'error');
            return;
        }
        
        this.showLoading('Running project...');
        this.clearTerminal();
        
        // Make sure terminal is visible
        if (!this.isTerminalVisible) {
            this.toggleTerminal();
        }
        
        // Emit command to server via Socket.IO
        this.socket.emit('execute_command', {
            projectName: this.currentProject,
            command: 'run'
        }, (response) => {
            // This is the acknowledgment callback
            if (response && response.status === 'started') {
                this.appendToTerminal(`${response.message}\n`, 'terminal-info');
            }
            this.hideLoading();
        });
    }
    
    installDependencies() {
        if (!this.currentProject) {
            this.showNotification('No project is currently open', 'error');
            return;
        }
        
        this.showLoading('Installing dependencies...');
        this.clearTerminal();
        
        // Make sure terminal is visible
        if (!this.isTerminalVisible) {
            this.toggleTerminal();
        }
        
        // Emit command to server via Socket.IO
        this.socket.emit('execute_command', {
            projectName: this.currentProject,
            command: 'install'
        }, (response) => {
            // This is the acknowledgment callback
            if (response && response.status === 'started') {
                this.appendToTerminal(`${response.message}\n`, 'terminal-info');
            }
            this.hideLoading();
        });
    }
    
    handleCommandOutput(data) {
        if (!data) return;
        
        try {
            // If data is a string, try to parse it as JSON
            if (typeof data === 'string') {
                try {
                    data = JSON.parse(data);
                } catch (e) {
                    // If it's not JSON, treat it as plain text output
                    this.appendToTerminal(data + '\n', 'terminal-output');
                    return;
                }
            }
            
            // Handle different types of output
            if (data.type === 'output') {
                const output = typeof data.data === 'object' ? 
                    JSON.stringify(data.data, null, 2) : 
                    String(data.data);
                this.appendToTerminal(output + '\n', 'terminal-output');
            } else if (data.type === 'error') {
                const error = typeof data.data === 'object' ? 
                    JSON.stringify(data.data, null, 2) : 
                    String(data.data);
                this.appendToTerminal(`Error: ${error}\n`, 'terminal-error');
            } else if (data.type === 'done') {
                if (data.data && data.data.status === 'error') {
                    const error = typeof data.data.message === 'object' ? 
                        JSON.stringify(data.data.message, null, 2) : 
                        String(data.data.message);
                    this.appendToTerminal(`Error: ${error}\n`, 'terminal-error');
                } else if (data.data && data.data.status === 'success') {
                    const message = typeof data.data.message === 'object' ? 
                        JSON.stringify(data.data.message, null, 2) : 
                        String(data.data.message);
                    this.appendToTerminal(`${message}\n`, 'terminal-success');
                } else {
                    this.appendToTerminal('Command completed successfully\n', 'terminal-success');
                }
            }
        } catch (error) {
            console.error('Error handling command output:', error);
            this.appendToTerminal(`Error handling output: ${error.message}\n`, 'terminal-error');
        }
    }
    
    appendToTerminal(text, className = '') {
        if (!this.terminalContent) {
            this.terminalContent = document.querySelector('#terminal-content');
            if (!this.terminalContent) return;
        }
        
        const span = document.createElement('span');
        if (className) {
            span.className = className;
        }
        
        // Handle ANSI color codes (basic support)
        const ansiColorRegex = /\x1b\[\d+m(.*?)(\x1b\[0m|$)/g;
        if (ansiColorRegex.test(text)) {
            // If text contains ANSI color codes, replace them with styled spans
            const coloredText = text.replace(ansiColorRegex, (match, content) => {
                return content;
            });
            span.textContent = coloredText;
        } else {
            span.textContent = text;
        }
        
        this.terminalContent.appendChild(span);
        
        // Auto-scroll to bottom
        this.terminalContent.scrollTop = this.terminalContent.scrollHeight;
    }
    
    clearTerminal() {
        if (!this.terminalContent) {
            this.terminalContent = document.getElementById('terminal-content');
            if (!this.terminalContent) return;
        }
        
        this.terminalContent.innerHTML = '';
        this.appendToTerminal('Terminal cleared\n', 'terminal-info');
    }
    
    toggleTerminal() {
        const terminal = document.getElementById('terminal');
        if (!terminal) return;
        
        this.isTerminalVisible = !this.isTerminalVisible;
        terminal.classList.toggle('collapsed', !this.isTerminalVisible);
        
        // Update toggle button text/icon
        const toggleBtn = document.getElementById('toggle-terminal-btn');
        if (toggleBtn) {
            const icon = toggleBtn.querySelector('i');
            if (icon) {
                icon.className = this.isTerminalVisible ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
            }
        }
    }
    
    // Utility functions
    sanitizeId(str) {
        return str.replace(/[^a-zA-Z0-9]/g, '_');
    }
    
    getLanguageMode(filePath) {
        const ext = filePath.split('.').pop().toLowerCase();
        
        switch (ext) {
            case 'py':
                return 'python';
            case 'js':
                return 'javascript';
            case 'html':
                return 'htmlmixed';
            case 'css':
                return 'css';
            case 'md':
                return 'markdown';
            case 'json':
                return 'javascript';
            default:
                return 'text';
        }
    }
}