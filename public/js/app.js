const app = {
    streamer: null,
    currentJobId: null,

    init() {
        this.streamer = new LogStreamer(document.getElementById('terminal-output'));
        this.router.init();
        CronBuilder.init();
        this.bindEvents();
    },

    bindEvents() {
        document.getElementById('job-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.saveJob();
        });

        document.getElementById('btn-run-job').addEventListener('click', async () => {
            if (this.currentJobId) {
                await this.runJob(this.currentJobId);
            }
        });

        const searchInput = document.getElementById('job-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                this.loadJobs();
            });
        }
    },

    async loadDashboard() {
        try {
            const stats = await api.getStats();
            document.getElementById('dashboard-stats').innerHTML = components.renderStats(stats);
            
            const jobs = await api.getJobs();
            const activeJobs = jobs.filter(job => job.enabled);
            const tbody = document.getElementById('dashboard-active-jobs');
            if (activeJobs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">No active jobs.</td></tr>';
            } else {
                tbody.innerHTML = activeJobs.map(job => components.renderActiveJobRow(job)).join('');
            }
        } catch (e) {
            console.error(e);
        }
    },

    async loadJobs() {
        try {
            const jobs = await api.getJobs();
            const searchInput = document.getElementById('job-search');
            const query = searchInput ? searchInput.value.toLowerCase() : '';
            const filteredJobs = jobs.filter(job => job.name.toLowerCase().includes(query));
            
            const tbody = document.getElementById('jobs-list-tbody');
            if (filteredJobs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">No jobs found.</td></tr>';
            } else {
                tbody.innerHTML = filteredJobs.map(job => components.renderJobTableRow(job)).join('');
            }
        } catch (e) {
            console.error(e);
        }
    },

    async loadJobEdit(id) {
        const form = document.getElementById('job-form');
        if (id === 'new') {
            document.getElementById('job-edit-title').textContent = 'New Job';
            form.reset();
            document.getElementById('job-id').value = '';
            document.getElementById('job-cron').value = '0 * * * *';
        } else {
            document.getElementById('job-edit-title').textContent = 'Edit Job';
            try {
                const job = await api.getJob(id);
                document.getElementById('job-id').value = job.id;
                document.getElementById('job-name').value = job.name;
                document.getElementById('job-command').value = job.command;
                document.getElementById('job-cron').value = job.cron_expression;
                document.getElementById('job-cwd').value = job.working_directory || '';
                document.getElementById('job-enabled').checked = job.enabled;
            } catch (e) {
                console.error(e);
                this.router.navigate('#jobs');
            }
        }
    },

    async loadJobDetail(id) {
        this.currentJobId = id;
        try {
            const job = await api.getJob(id);
            document.getElementById('job-detail-title').textContent = `Job: ${job.name}`;
            
            const runs = await api.getJobRuns(id);
            if (runs && runs.length > 0) {
                const latestRun = runs[0];
                if (latestRun.status === 'running') {
                    this.streamer.connect(latestRun.id);
                } else {
                    document.getElementById('terminal-output').innerHTML = '';
                    this.streamer.appendLog('stdout', latestRun.stdout || '');
                    if (latestRun.stderr) {
                        this.streamer.appendLog('stderr', latestRun.stderr);
                    }
                    this.streamer.appendLog('system', `\n[Run finished with status: ${latestRun.status}, exit code: ${latestRun.exit_code}]`);
                }
            } else {
                document.getElementById('terminal-output').innerHTML = '<span class="log-system">No runs yet. Click "Run Now" to test.</span>';
            }
            
        } catch (e) {
            console.error(e);
            this.router.navigate('#jobs');
        }
    },

    async saveJob() {
        const id = document.getElementById('job-id').value;
        const data = {
            name: document.getElementById('job-name').value,
            command: document.getElementById('job-command').value,
            cron_expression: document.getElementById('job-cron').value,
            working_directory: document.getElementById('job-cwd').value,
            enabled: document.getElementById('job-enabled').checked,
        };

        try {
            if (id) {
                await api.updateJob(id, data);
            } else {
                await api.createJob(data);
            }
            this.router.navigate('#jobs');
        } catch (e) {
            alert('Failed to save job: ' + e.message);
        }
    },

    async toggleJob(id, enable) {
        try {
            if (enable) await api.startJob(id);
            else await api.stopJob(id);
            await this.loadJobs();
        } catch (e) {
            console.error(e);
        }
    },

    async deleteJob(id) {
        try {
            await api.deleteJob(id);
            const hash = window.location.hash.slice(1);
            if (hash === 'jobs') await this.loadJobs();
            else await this.loadDashboard();
        } catch (e) {
            alert('Failed to delete job: ' + e.message);
        }
    },

    async runJob(id) {
        try {
            await api.runJob(id);
            setTimeout(() => this.loadJobDetail(id), 500);
        } catch (e) {
            alert('Failed to start run: ' + e.message);
        }
    },

    router: {
        init() {
            window.addEventListener('hashchange', () => this.handleRoute());
            this.handleRoute();
        },
        navigate(hash) {
            window.location.hash = hash;
        },
        handleRoute() {
            let hash = window.location.hash.slice(1) || 'dashboard';
            let viewId = 'dashboard-view';
            let navId = 'dashboard';

            if (app.streamer) app.streamer.disconnect();

            if (hash === 'dashboard') {
                viewId = 'dashboard-view';
                navId = 'dashboard';
                app.loadDashboard();
            } else if (hash === 'jobs') {
                viewId = 'jobs-view';
                navId = 'jobs';
                app.loadJobs();
            } else if (hash.startsWith('job-edit/')) {
                const id = hash.split('/')[1];
                viewId = 'job-edit-view';
                navId = 'jobs';
                app.loadJobEdit(id);
            } else if (hash.startsWith('job-detail/')) {
                const id = hash.split('/')[1];
                viewId = 'job-detail-view';
                navId = 'jobs';
                app.loadJobDetail(id);
            }

            document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

            const activeView = document.getElementById(viewId);
            if (activeView) activeView.classList.add('active');

            const activeNav = document.querySelector(`.nav-item[data-view="${navId}"]`);
            if (activeNav) activeNav.classList.add('active');
        }
    }
};

window.addEventListener('DOMContentLoaded', () => {
    app.init();
});
