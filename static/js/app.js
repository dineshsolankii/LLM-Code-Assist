/**
 * LLM Code Assist — Main Application Controller
 * Handles all SPA navigation, state, and API interactions.
 */
const App = {
    currentScreen: 'dashboard',
    currentProject: null,
    currentFile: null,
    analysis: null,
    selectedFramework: null,
    projects: [],
    settings: {},
    _confirmResolveCallback: null,

    async init() {
        console.log('🚀 LLM Code Assist initializing...');

        // Initialize subsystems
        Editor.init('code-editor');
        Terminal.init('terminal-output', 'terminal-panel');
        Socket.init();

        // Socket event handlers
        Socket.on('output', (data) => {
            Terminal.write(data.output || data.line || String(data), data.type || 'stdout');
        });
        Socket.on('finished', () => {
            Terminal.writeSuccess('--- Execution finished ---');
            this._setRunning(false);
        });
        Socket.on('stopped', () => {
            Terminal.writeSystem('--- Execution stopped ---');
            this._setRunning(false);
        });
        Socket.on('error', (data) => {
            Terminal.writeError(data.error || 'Execution error');
            this._setRunning(false);
        });

        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const screen = link.dataset.screen;
                if (screen) this.showScreen(screen);
                // Close mobile sidebar
                this.closeSidebar();
            });
        });

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            const ctrl = e.ctrlKey || e.metaKey;
            if (ctrl && e.key === 'n') { e.preventDefault(); this.showScreen('create'); }
            if (ctrl && e.key === 's') { e.preventDefault(); this.saveCurrentFile(); }
        });

        // Load data
        await this._loadUser();
        this._loadProjects();  // async, shows skeletons
        this._loadFrameworks();
        this._checkHealth();
    },

    // ─── Screen Navigation ────────────────────────────────────────────────────

    showScreen(name) {
        const current = document.getElementById(`screen-${this.currentScreen}`);
        if (current) current.classList.add('hidden');

        const next = document.getElementById(`screen-${name}`);
        if (next) {
            next.classList.remove('hidden');
            next.classList.add('screen-enter');
            setTimeout(() => next.classList.remove('screen-enter'), 300);
        }

        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        const link = document.querySelector(`.nav-link[data-screen="${name}"]`);
        if (link) link.classList.add('active');

        this.currentScreen = name;

        if (name === 'editor') {
            Editor.refresh();
            // Update breadcrumb
            this._updateBreadcrumb();
        }
        if (name === 'settings') {
            this._loadSettingsForm();
        }
    },

    // ─── Sidebar (mobile) ─────────────────────────────────────────────────────

    openSidebar() {
        const sidebar = document.getElementById('sidebar');
        const backdrop = document.getElementById('sidebar-backdrop');
        if (sidebar) sidebar.classList.add('open');
        if (backdrop) backdrop.classList.add('visible');
    },

    closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        const backdrop = document.getElementById('sidebar-backdrop');
        if (sidebar) sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('visible');
    },

    // ─── User ─────────────────────────────────────────────────────────────────

    async _loadUser() {
        try {
            const data = await API.getCurrentUser();
            if (data.success && data.user) {
                const u = data.user;
                this._setText('user-name', u.name || 'User');
                this._setText('user-email', u.email || '');
                this._setText('settings-name', u.name || 'User');
                this._setText('settings-email', u.email || '');

                const avatarUrl = u.picture_url ||
                    `https://ui-avatars.com/api/?name=${encodeURIComponent(u.name || 'U')}&background=6366f1&color=fff&size=80`;

                document.querySelectorAll('#user-avatar, #settings-avatar, #profile-avatar').forEach(el => {
                    if (el) {
                        el.src = avatarUrl;
                        el.onerror = () => { el.src = `https://ui-avatars.com/api/?name=U&background=6366f1&color=fff`; };
                    }
                });
                if (document.getElementById('profile-name')) this._setText('profile-name', u.name || 'User');
                if (document.getElementById('profile-email')) this._setText('profile-email', u.email || '');
            }
        } catch(e) { console.warn('Failed to load user:', e.message); }
    },

    // ─── Projects ─────────────────────────────────────────────────────────────

    async _loadProjects() {
        this._showSkeletons(true);
        try {
            const data = await API.getProjects();
            if (data.success) {
                this.projects = data.projects || [];
                this._renderProjects();
                this._setText('stat-projects', this.projects.length);
            }
        } catch(e) {
            console.error('Failed to load projects:', e.message);
            Notify.error('Failed to load projects');
        } finally {
            this._showSkeletons(false);
        }
    },

    _showSkeletons(show) {
        const skeletons = document.getElementById('skeleton-projects');
        const grid = document.getElementById('projects-grid');
        if (skeletons) skeletons.style.display = show ? '' : 'none';
        if (grid && show) grid.style.display = 'none';
        if (grid && !show) grid.style.display = '';
    },

    _renderProjects(filter) {
        const grid = document.getElementById('projects-grid');
        const sidebar = document.getElementById('sidebar-projects');
        const noProjects = document.getElementById('no-projects');

        if (!grid) return;

        const projects = filter
            ? this.projects.filter(p => p.name.toLowerCase().includes(filter.toLowerCase()))
            : this.projects;

        if (projects.length === 0 && !filter) {
            grid.innerHTML = '';
            if (noProjects) noProjects.classList.remove('hidden');
            if (sidebar) sidebar.innerHTML = '<p class="px-3 py-2 text-xs" style="color:#334155;">No projects yet</p>';
            return;
        }

        if (noProjects) noProjects.classList.add('hidden');

        const frameworkIcons = {
            python: 'fab fa-python', flask: 'fas fa-flask',
            gradio: 'fas fa-globe', streamlit: 'fas fa-chart-bar'
        };
        const frameworkColors = {
            python:    'rgba(234,179,8,0.15)',
            flask:     'rgba(34,197,94,0.15)',
            gradio:    'rgba(59,130,246,0.15)',
            streamlit: 'rgba(239,68,68,0.15)'
        };
        const frameworkIconColors = {
            python: '#facc15', flask: '#4ade80', gradio: '#60a5fa', streamlit: '#f87171'
        };

        grid.innerHTML = projects.map(p => {
            const icon = frameworkIcons[p.framework] || 'fas fa-code';
            const bg   = frameworkColors[p.framework] || 'rgba(99,102,241,0.15)';
            const ic   = frameworkIconColors[p.framework] || '#818cf8';
            const date = p.created_at ? new Date(p.created_at).toLocaleDateString() : '--';
            const desc = p.description || 'No description';
            const status = p.status || 'ready';
            return `
                <div class="project-card" onclick="App.openProject('${this._escapeHtml(p.name)}')">
                    <div class="flex items-start gap-3 mb-3">
                        <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                             style="background:${bg}; border:1px solid ${ic}22;">
                            <i class="${icon} text-sm" style="color:${ic};"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <h3 class="font-semibold truncate" style="color:#f1f5f9;">${this._escapeHtml(p.name)}</h3>
                            <span class="text-xs capitalize" style="color:#64748b;">${p.framework || 'python'}</span>
                        </div>
                        <button onclick="event.stopPropagation(); App.deleteProject('${this._escapeHtml(p.name)}')"
                                class="p-1.5 rounded-lg transition-all opacity-0 hover:opacity-100 flex-shrink-0"
                                style="color:#475569;"
                                onmouseover="this.style.background='rgba(239,68,68,0.12)';this.style.color='#f87171';"
                                onmouseout="this.style.background='';this.style.color='#475569';"
                                title="Delete project">
                            <i class="fas fa-trash-alt text-xs"></i>
                        </button>
                    </div>
                    <p class="text-sm line-clamp-2 mb-3" style="color:#64748b;">${this._escapeHtml(desc)}</p>
                    <div class="flex items-center justify-between text-xs" style="color:#334155;">
                        <div class="flex items-center gap-1.5">
                            <i class="fas fa-clock"></i>
                            <span>${date}</span>
                        </div>
                        <span class="badge-${status === 'ready' ? 'green' : 'indigo'}">${status}</span>
                    </div>
                </div>
            `;
        }).join('');

        // Bind hover for delete button visibility
        grid.querySelectorAll('.project-card').forEach(card => {
            const btn = card.querySelector('button');
            if (btn) {
                card.addEventListener('mouseenter', () => btn.style.opacity = '1');
                card.addEventListener('mouseleave', () => btn.style.opacity = '0');
            }
        });

        if (sidebar) {
            sidebar.innerHTML = this.projects.slice(0, 8).map(p => {
                const icon = frameworkIcons[p.framework] || 'fas fa-folder';
                const ic   = frameworkIconColors[p.framework] || '#818cf8';
                return `
                    <div class="sidebar-project-link ${this.currentProject === p.name ? 'active' : ''}"
                         onclick="App.openProject('${this._escapeHtml(p.name)}')">
                        <i class="${icon} text-xs" style="color:${ic}; flex-shrink:0;"></i>
                        <span class="truncate">${this._escapeHtml(p.name)}</span>
                    </div>
                `;
            }).join('');
        }
    },

    filterProjects(query) {
        this._renderProjects(query);
    },

    async openProject(name) {
        this.currentProject = name;
        this._setText('editor-project-name', name);

        const proj = this.projects.find(p => p.name === name);
        if (proj) {
            const badge = document.getElementById('editor-framework-badge');
            if (badge) {
                badge.textContent = proj.framework || 'python';
                badge.classList.remove('hidden');
            }
        }

        this.showScreen('editor');
        this._updateBreadcrumb();
        await this.refreshFiles();

        // Update sidebar active state
        document.querySelectorAll('.sidebar-project-link').forEach(el => {
            el.classList.toggle('active', el.textContent.trim() === name);
        });
    },

    async refreshFiles() {
        if (!this.currentProject) return;
        try {
            const data = await API.getFiles(this.currentProject);
            if (data.success) this._renderFileTree(data.files || []);
        } catch(e) {
            Notify.error('Failed to load files');
        }
    },

    _renderFileTree(files) {
        const tree = document.getElementById('file-tree');
        if (!tree) return;

        if (files.length === 0) {
            tree.innerHTML = `<div class="px-3 py-6 text-center text-xs" style="color:#334155;">
                <i class="fas fa-folder-open mb-2 text-lg opacity-30 block"></i>No files</div>`;
            return;
        }

        const fileIcons = {
            'py': ['fab fa-python', '#facc15'],
            'js': ['fab fa-js', '#facc15'],
            'html': ['fab fa-html5', '#f97316'],
            'css': ['fab fa-css3', '#60a5fa'],
            'json': ['fas fa-file-code', '#4ade80'],
            'md': ['fas fa-file-alt', '#94a3b8'],
            'txt': ['fas fa-file', '#64748b'],
            'yml': ['fas fa-file-code', '#a78bfa'],
            'yaml': ['fas fa-file-code', '#a78bfa'],
            'sh': ['fas fa-terminal', '#4ade80'],
            'toml': ['fas fa-file-code', '#fb923c'],
            'ini': ['fas fa-cog', '#94a3b8']
        };

        tree.innerHTML = files.map(f => {
            if (f.type === 'directory') {
                return `<div class="file-item" style="cursor:default;">
                    <i class="fas fa-folder text-xs" style="color:#ca8a04;"></i>
                    <span>${this._escapeHtml(f.name)}/</span>
                </div>`;
            }
            const ext = (f.name.split('.').pop() || '').toLowerCase();
            const [icon, color] = fileIcons[ext] || ['fas fa-file', '#64748b'];
            const active = this.currentFile === f.name ? ' active' : '';
            return `<div class="file-item${active}" data-file="${this._escapeHtml(f.name)}"
                         onclick="App.openFile('${this._escapeHtml(f.path || f.name)}')">
                <i class="${icon} text-xs" style="color:${color};"></i>
                <span class="truncate">${this._escapeHtml(f.name)}</span>
            </div>`;
        }).join('');
    },

    async openFile(filename) {
        if (!this.currentProject) return;
        try {
            const data = await API.getFileContent(this.currentProject, filename);
            if (data.success) {
                this.currentFile = filename;
                Editor.setMode(filename);
                Editor.setValue(data.content || '');
                Editor.currentFile = filename;
                Editor.modified = false;

                // Hide placeholder, show editor
                const placeholder = document.getElementById('editor-placeholder');
                const editorEl = document.getElementById('code-editor');
                if (placeholder) placeholder.style.display = 'none';
                if (editorEl) editorEl.style.display = '';

                this._updateEditorTabs(filename);
                this._updateBreadcrumb();

                // Highlight active file in tree
                document.querySelectorAll('.file-item').forEach(el => el.classList.remove('active'));
                const active = document.querySelector(`.file-item[data-file="${CSS.escape(filename)}"]`);
                if (active) active.classList.add('active');
            }
        } catch(e) {
            Notify.error(`Failed to open ${filename}: ${e.message}`);
        }
    },

    _updateEditorTabs(filename) {
        const tabs = document.getElementById('editor-tabs');
        if (!tabs) return;

        if (!tabs.querySelector(`[data-tab="${CSS.escape(filename)}"]`)) {
            const tab = document.createElement('div');
            tab.className = 'editor-tab';
            tab.dataset.tab = filename;
            tab.innerHTML = `
                <span class="tab-filename">${this._escapeHtml(filename)}</span>
                <span class="tab-modified" style="display:none;" title="Unsaved changes">●</span>
                <i class="fas fa-times text-xs ml-1" style="opacity:0.4;"
                   onclick="event.stopPropagation(); App.closeTab('${this._escapeHtml(filename)}')"
                   onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.4'"></i>
            `;
            tab.addEventListener('click', () => this.openFile(filename));
            tabs.appendChild(tab);
        }

        tabs.querySelectorAll('.editor-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === filename);
        });
    },

    markTabModified(filename, modified) {
        const tabs = document.getElementById('editor-tabs');
        if (!tabs) return;
        const tab = tabs.querySelector(`[data-tab="${CSS.escape(filename)}"]`);
        if (tab) {
            const dot = tab.querySelector('.tab-modified');
            if (dot) dot.style.display = modified ? '' : 'none';
        }
    },

    closeTab(filename) {
        const tabs = document.getElementById('editor-tabs');
        const tab = tabs?.querySelector(`[data-tab="${CSS.escape(filename)}"]`);
        if (tab) tab.remove();
        if (this.currentFile === filename) {
            const remaining = tabs?.querySelector('.editor-tab');
            if (remaining) {
                this.openFile(remaining.dataset.tab);
            } else {
                this.currentFile = null;
                Editor.setValue('');
                const placeholder = document.getElementById('editor-placeholder');
                const editorEl = document.getElementById('code-editor');
                if (placeholder) placeholder.style.display = '';
                if (editorEl) editorEl.style.display = 'none';
                this._updateBreadcrumb();
            }
        }
    },

    async saveCurrentFile() {
        if (!this.currentProject || !this.currentFile) return;
        try {
            await API.saveFile(this.currentProject, this.currentFile, Editor.getValue());
            Editor.modified = false;
            this.markTabModified(this.currentFile, false);
            Notify.success(`Saved ${this.currentFile}`);
        } catch(e) {
            Notify.error(`Failed to save: ${e.message}`);
        }
    },

    _updateBreadcrumb() {
        const bc = document.getElementById('editor-breadcrumb');
        if (!bc) return;
        let html = '<span style="color:var(--text-muted);">Projects</span>';
        if (this.currentProject) {
            html += ' <i class="fas fa-chevron-right text-xs" style="color:var(--text-muted);"></i> ';
            html += `<span style="color:var(--text-primary); font-weight:500;">${this._escapeHtml(this.currentProject)}</span>`;
        }
        if (this.currentFile) {
            html += ' <i class="fas fa-chevron-right text-xs" style="color:var(--text-muted);"></i> ';
            html += `<span class="breadcrumb-current">${this._escapeHtml(this.currentFile)}</span>`;
        }
        bc.innerHTML = html;
    },

    // ─── Project Creation ──────────────────────────────────────────────────────

    async _loadFrameworks() {
        try {
            const data = await API.getFrameworks();
            if (data.success) {
                const grid = document.getElementById('framework-grid');
                if (!grid) return;

                const frameworkColors = {
                    python:    { bg:'rgba(234,179,8,0.12)',   border:'rgba(234,179,8,0.25)',   icon:'#facc15' },
                    flask:     { bg:'rgba(34,197,94,0.12)',   border:'rgba(34,197,94,0.25)',   icon:'#4ade80' },
                    gradio:    { bg:'rgba(59,130,246,0.12)',  border:'rgba(59,130,246,0.25)',  icon:'#60a5fa' },
                    streamlit: { bg:'rgba(239,68,68,0.12)',   border:'rgba(239,68,68,0.25)',   icon:'#f87171' }
                };

                grid.innerHTML = data.frameworks.map(f => {
                    const colors = frameworkColors[f.id] || { bg:'rgba(99,102,241,0.12)', border:'rgba(99,102,241,0.25)', icon:'#818cf8' };
                    return `
                        <div class="framework-card" data-framework="${f.id}"
                             onclick="App.selectFramework('${f.id}', this)">
                            <div class="w-10 h-10 rounded-xl mx-auto mb-3 flex items-center justify-center"
                                 style="background:${colors.bg}; border:1px solid ${colors.border};">
                                <i class="${f.icon} text-lg" style="color:${colors.icon};"></i>
                            </div>
                            <h4 class="text-sm font-semibold mb-1" style="color:#f1f5f9;">${this._escapeHtml(f.name)}</h4>
                            <p class="text-xs" style="color:#64748b;">${this._escapeHtml(f.description)}</p>
                        </div>
                    `;
                }).join('');
            }
        } catch(e) { console.warn('Failed to load frameworks:', e.message); }
    },

    selectFramework(id, el) {
        this.selectedFramework = id;
        document.querySelectorAll('.framework-card').forEach(c => c.classList.remove('selected'));
        if (el) el.classList.add('selected');
    },

    async analyzeRequirements() {
        const requirements = document.getElementById('project-requirements')?.value?.trim();
        const name = document.getElementById('project-name')?.value?.trim();

        if (!name) { Notify.warning('Please enter a project name'); return; }
        if (!requirements) { Notify.warning('Please describe your project'); return; }
        if (!this.selectedFramework) { Notify.warning('Please select a framework'); return; }

        // Update step indicators
        const s1 = document.getElementById('step-1-dot');
        const s2 = document.getElementById('step-2-dot');
        const conn = document.getElementById('step-connector');

        this._showLoading('Analyzing requirements with AI...');
        try {
            const data = await API.analyzeRequirements(requirements);
            if (data.success) {
                this.analysis = data.analysis;
                this._renderAnalysis(data.analysis);

                // Transition to step 2 with animation
                document.getElementById('create-step-1')?.classList.add('hidden');
                const step2 = document.getElementById('create-step-2');
                if (step2) {
                    step2.classList.remove('hidden');
                    step2.style.display = 'flex';
                }

                if (s1) { s1.className = 'step-dot done'; s1.innerHTML = '<i class="fas fa-check text-xs"></i>'; }
                if (conn) conn.classList.add('done');
                if (s2) s2.className = 'step-dot active';

                Notify.success('Requirements analyzed successfully!');
            }
        } catch(e) {
            Notify.error(`Analysis failed: ${e.message}`);
        } finally {
            this._hideLoading();
        }
    },

    _renderAnalysis(analysis) {
        const container = document.getElementById('analysis-result');
        if (!container || !analysis) return;

        const sections = [];
        if (analysis.description) {
            sections.push(`<div class="mb-3"><div class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#818cf8;">Description</div><p style="color:#94a3b8;">${this._escapeHtml(analysis.description)}</p></div>`);
        }
        if (analysis.features?.length) {
            const featList = analysis.features.map(f => {
                const name = typeof f === 'string' ? f : (f.name || '');
                const desc = typeof f === 'object' ? (f.description || '') : '';
                return `<li>${this._escapeHtml(name)}${desc ? ': <span style="color:#64748b;">' + this._escapeHtml(desc) + '</span>' : ''}</li>`;
            }).join('');
            sections.push(`<div class="mb-3"><div class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#818cf8;">Features</div><ul class="space-y-1 text-sm" style="list-style:disc;padding-left:1.25rem;color:#94a3b8;">${featList}</ul></div>`);
        }
        if (analysis.suggested_frameworks?.length) {
            const tags = analysis.suggested_frameworks.map(t => `<span class="badge-indigo">${this._escapeHtml(t)}</span>`).join('');
            sections.push(`<div class="mb-3"><div class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#818cf8;">Frameworks</div><div class="flex flex-wrap gap-2">${tags}</div></div>`);
        }
        if (analysis.suggested_packages?.length) {
            const pkgs = analysis.suggested_packages.slice(0, 8).map(t => `<span class="badge-indigo">${this._escapeHtml(t)}</span>`).join('');
            sections.push(`<div class="mb-3"><div class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:#818cf8;">Packages</div><div class="flex flex-wrap gap-2">${pkgs}</div></div>`);
        }
        if (analysis.file_structure?.length) {
            const files = analysis.file_structure.slice(0, 10).map(f => `<div class="flex items-center gap-2"><i class="fas fa-file text-xs" style="color:#4ade80;"></i><span style="color:#94a3b8;">${this._escapeHtml(f.path || '')}</span></div>`).join('');
            sections.push(`<div><div class="text-xs font-semibold uppercase tracking-wider mb-2" style="color:#818cf8;">File Structure</div><div class="space-y-1 text-sm font-mono">${files}</div></div>`);
        }

        container.innerHTML = sections.join('') || '<p style="color:#475569;">Analysis complete. Ready to generate.</p>';
    },

    backToStep1() {
        document.getElementById('create-step-1')?.classList.remove('hidden');
        const step2 = document.getElementById('create-step-2');
        if (step2) { step2.classList.add('hidden'); step2.style.display = ''; }

        const s1 = document.getElementById('step-1-dot');
        const s2 = document.getElementById('step-2-dot');
        const conn = document.getElementById('step-connector');
        if (s1) { s1.className = 'step-dot active'; s1.textContent = '1'; }
        if (conn) conn.classList.remove('done');
        if (s2) { s2.className = 'step-dot pending'; s2.textContent = '2'; }
    },

    async generateProject() {
        const name = document.getElementById('project-name')?.value?.trim();
        if (!name || !this.analysis || !this.selectedFramework) {
            Notify.error('Missing required information — go back and fill in all fields');
            return;
        }

        this._showLoading('Generating project code...');
        try {
            const data = await API.createProject({
                projectName: name,
                framework: this.selectedFramework,
                analysis: this.analysis,
                requirements: document.getElementById('project-requirements')?.value || ''
            });

            if (data.success) {
                Notify.success(`Project "${name}" created successfully!`);
                await this._loadProjects();
                this.openProject(name);

                // Reset form
                this.backToStep1();
                if (document.getElementById('project-name')) document.getElementById('project-name').value = '';
                if (document.getElementById('project-requirements')) document.getElementById('project-requirements').value = '';
                const counter = document.getElementById('req-counter');
                if (counter) counter.textContent = '0 / 4000';
                this.analysis = null;
                this.selectedFramework = null;
                document.querySelectorAll('.framework-card').forEach(c => c.classList.remove('selected'));
            }
        } catch(e) {
            Notify.error(`Project creation failed: ${e.message}`);
        } finally {
            this._hideLoading();
        }
    },

    async deleteProject(name) {
        const confirmed = await this._confirm(
            `Delete "${name}"?`,
            'This will permanently delete the project and all its files. This cannot be undone.',
            'Delete Project'
        );
        if (!confirmed) return;

        try {
            await API.deleteProject(name);
            Notify.success(`Project "${name}" deleted`);
            if (this.currentProject === name) {
                this.currentProject = null;
                this.currentFile = null;
                this.showScreen('dashboard');
            }
            await this._loadProjects();
        } catch(e) {
            Notify.error(`Failed to delete: ${e.message}`);
        }
    },

    // ─── Execution ────────────────────────────────────────────────────────────

    runProject() {
        if (!this.currentProject) { Notify.warning('No project selected'); return; }
        if (!Socket.isConnected()) { Notify.error('Not connected to server'); return; }

        const file = this.currentFile || 'app.py';
        Terminal.clear();
        Terminal.show();
        Terminal.writeSystem(`▶ Starting ${this.currentProject} / ${file}...`);

        const sent = Socket.execute(this.currentProject, file);
        if (sent) this._setRunning(true);
    },

    stopExecution() {
        Socket.stop();
        Terminal.writeSystem('⏹ Stopping execution...');
    },

    _setRunning(running) {
        const btnRun  = document.getElementById('btn-run');
        const btnStop = document.getElementById('btn-stop');
        if (btnRun)  btnRun.classList.toggle('hidden', running);
        if (btnStop) btnStop.classList.toggle('hidden', !running);
    },

    clearTerminal() { Terminal.clear(); },
    toggleTerminal() { Terminal.toggle(); },

    // ─── AI Chat ─────────────────────────────────────────────────────────────

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const msg = input?.value?.trim();
        if (!msg) return;
        input.value = '';

        this._addChatMessage(msg, 'user');

        if (!this.currentProject || !this.currentFile) {
            this._addChatMessage('Please open a project file first, then I can help you modify it.', 'ai');
            return;
        }

        this._showTyping(true);
        try {
            const data = await API.customizeCode(
                this.currentProject, this.currentFile, Editor.getValue(), msg
            );
            this._showTyping(false);
            if (data.success && data.code) {
                Editor.setValue(data.code);
                this.markTabModified(this.currentFile, true);
                this._addChatMessage('Done! I\'ve updated the code in the editor. Review the changes — press ⌘S to save.', 'ai');
                Notify.success('Code updated by AI');
            } else {
                this._addChatMessage(data.error || 'I couldn\'t apply that change. Try rephrasing.', 'ai');
            }
        } catch(e) {
            this._showTyping(false);
            this._addChatMessage(`Error: ${e.message}`, 'ai');
            Notify.error('AI customization failed');
        }
    },

    _showTyping(show) {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            if (show) {
                indicator.classList.remove('hidden');
                // Add typing dots if not already there
                if (!indicator.querySelector('.typing-dot')) {
                    indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
                }
                const msgs = document.getElementById('chat-messages');
                if (msgs) msgs.scrollTop = msgs.scrollHeight;
            } else {
                indicator.classList.add('hidden');
            }
        }
    },

    _addChatMessage(text, role) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        // Remove initial placeholder if present
        const welcome = container.querySelector('.chat-msg.ai');
        // Don't remove welcome on first message, it's fine

        const div = document.createElement('div');
        div.className = `chat-msg ${role}`;
        div.textContent = text;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },

    // ─── Settings ─────────────────────────────────────────────────────────────

    async _loadSettingsForm() {
        try {
            const data = await API.getPreferences();
            if (data.success && data.preferences) {
                const prefs = data.preferences;
                const fs = document.getElementById('settings-font-size');
                const ts = document.getElementById('settings-tab-size');
                const ww = document.getElementById('settings-word-wrap');
                const ou = document.getElementById('settings-ollama-url');
                if (fs && prefs.fontSize) fs.value = prefs.fontSize;
                if (ts && prefs.tabSize)  ts.value = prefs.tabSize;
                if (ww && prefs.wordWrap !== undefined) ww.checked = prefs.wordWrap;
                if (ou && prefs.ollamaUrl) ou.value = prefs.ollamaUrl;
            }
        } catch(e) { /* preferences optional */ }
    },

    async saveSettings() {
        const prefs = {
            fontSize:  document.getElementById('settings-font-size')?.value  || '14',
            tabSize:   document.getElementById('settings-tab-size')?.value   || '4',
            wordWrap:  document.getElementById('settings-word-wrap')?.checked ?? true,
            ollamaUrl: document.getElementById('settings-ollama-url')?.value || 'http://localhost:11434'
        };

        try {
            await API.savePreferences(prefs);
            this._applySettings(prefs);
            Notify.success('Settings saved!');
        } catch(e) {
            Notify.error('Failed to save settings');
        }
    },

    _applySettings(prefs) {
        if (prefs.fontSize) Editor.setFontSize(parseInt(prefs.fontSize));
        if (prefs.tabSize)  Editor.setTabSize(parseInt(prefs.tabSize));
        if (prefs.wordWrap !== undefined) Editor.setLineWrapping(prefs.wordWrap);
        this.settings = prefs;
    },

    // ─── Health Check ─────────────────────────────────────────────────────────

    async _checkHealth() {
        try {
            const data = await API.getHealth();
            const statusEl = document.getElementById('stat-status');
            if (statusEl) {
                statusEl.textContent = data.status === 'ok' ? 'Online' : 'Offline';
                statusEl.className = `status-badge ${data.status === 'ok' ? 'online' : 'offline'}`;
            }
        } catch(e) {
            const statusEl = document.getElementById('stat-status');
            if (statusEl) { statusEl.textContent = 'Offline'; statusEl.className = 'status-badge offline'; }
        }

        try {
            const mdata = await API.getActiveModel();
            if (mdata.success) {
                const short = mdata.model ? mdata.model.split(':')[0].replace('qwen2.5-coder', 'Qwen') : '--';
                this._setText('stat-model', short);
                this._setText('active-model', mdata.model || '--');
                this._setText('stat-model-settings', mdata.model || '--');
            }
        } catch(e) { /* model info optional */ }
    },

    async refreshModel() {
        await this._checkHealth();
        Notify.info('Model info refreshed');
    },

    // ─── Custom Confirm Modal ─────────────────────────────────────────────────

    _confirm(title, message, okLabel = 'Confirm') {
        return new Promise((resolve) => {
            this._confirmResolveCallback = resolve;
            const modal = document.getElementById('confirm-modal');
            const titleEl = document.getElementById('confirm-title');
            const msgEl = document.getElementById('confirm-message');
            const okBtn = document.getElementById('confirm-ok-btn');
            if (titleEl) titleEl.textContent = title;
            if (msgEl) msgEl.textContent = message;
            if (okBtn) okBtn.textContent = okLabel;
            if (modal) modal.classList.remove('hidden');
        });
    },

    _confirmResolve(result) {
        const modal = document.getElementById('confirm-modal');
        if (modal) modal.classList.add('hidden');
        if (this._confirmResolveCallback) {
            this._confirmResolveCallback(result);
            this._confirmResolveCallback = null;
        }
    },

    // ─── Helpers ─────────────────────────────────────────────────────────────

    _escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    },

    _showLoading(text) {
        const overlay = document.getElementById('loading-overlay');
        const loadText = document.getElementById('loading-text');
        if (overlay) overlay.classList.remove('hidden');
        if (loadText) loadText.textContent = text || 'Processing...';
    },

    _hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.add('hidden');
    },

    _setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text != null ? String(text) : '';
    }
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
