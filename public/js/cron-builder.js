const CronBuilder = {
    init() {
        this.input = document.getElementById('job-cron');
        this.preview = document.getElementById('cron-preview');
        this.tabs = document.querySelectorAll('.cron-tab');
        this.contents = document.querySelectorAll('.cron-tab-content');
        
        if (!this.input) return;

        this.currentMode = 'custom';
        this.bindEvents();
        this.updatePreview();
    },

    bindEvents() {
        this.tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.tabs.forEach(t => t.classList.remove('active'));
                this.contents.forEach(c => {
                    c.classList.remove('active');
                    c.style.display = 'none';
                });
                
                const target = e.target;
                target.classList.add('active');
                this.currentMode = target.dataset.tab;
                
                const activeContent = document.getElementById(`cron-tab-${this.currentMode}`);
                activeContent.classList.add('active');
                activeContent.style.display = 'block';
                
                this.updateCronFromUI();
            });
        });

        // Bind all inputs
        document.querySelectorAll('.cron-num-input, .cron-day-chk').forEach(el => {
            el.addEventListener('input', () => this.updateCronFromUI());
            el.addEventListener('change', () => this.updateCronFromUI());
        });

        this.input.addEventListener('input', () => {
            if (this.currentMode === 'custom') {
                this.updatePreview();
            }
        });
    },

    updateCronFromUI() {
        if (this.currentMode === 'custom') {
            this.updatePreview();
            return;
        }

        let cron = '* * * * *';
        
        if (this.currentMode === 'minutes') {
            const min = document.getElementById('cron-min-val').value || 5;
            cron = `*/${min} * * * *`;
        } else if (this.currentMode === 'hourly') {
            const min = document.getElementById('cron-hour-min').value || 0;
            cron = `${min} * * * *`;
        } else if (this.currentMode === 'daily') {
            const h = document.getElementById('cron-daily-hour').value || 0;
            const m = document.getElementById('cron-daily-min').value || 0;
            cron = `${m} ${h} * * *`;
        } else if (this.currentMode === 'weekly') {
            const h = document.getElementById('cron-weekly-hour').value || 0;
            const m = document.getElementById('cron-weekly-min').value || 0;
            
            const checks = document.querySelectorAll('.cron-day-chk:checked');
            let days = Array.from(checks).map(c => c.value).join(',');
            if (!days) days = '*';
            
            cron = `${m} ${h} * * ${days}`;
        } else if (this.currentMode === 'monthly') {
            const h = document.getElementById('cron-monthly-hour').value || 0;
            const m = document.getElementById('cron-monthly-min').value || 0;
            const d = document.getElementById('cron-monthly-day').value || 1;
            cron = `${m} ${h} ${d} * *`;
        }

        this.input.value = cron;
        this.updatePreview();
    },

    updatePreview() {
        this.preview.textContent = "Current expression: " + this.input.value;
    }
};
