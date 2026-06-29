const components = {
    renderStats(stats) {
        return `
            <div class="stat-card glass-panel">
                <h3>Total Jobs</h3>
                <div class="value">${stats.total_jobs}</div>
            </div>
            <div class="stat-card glass-panel">
                <h3>Active Jobs</h3>
                <div class="value" style="color: var(--success)">${stats.active_jobs}</div>
            </div>
            <div class="stat-card glass-panel">
                <h3>Failed Runs</h3>
                <div class="value" style="color: var(--danger)">${stats.failed_runs}</div>
            </div>
        `;
    },

    renderActiveJobRow(job) {
        const isFailed = job.last_status === 'failed';
        const rowClass = isFailed ? 'row-failed' : '';
        const badgeClass = isFailed ? 'badge-danger' : (job.last_status === 'running' ? 'badge-warning' : 'badge-success');
        const badgeText = isFailed ? 'Failed' : (job.last_status === 'running' ? 'Running' : 'Active');
        
        return `
            <tr class="clickable-row ${rowClass}" onclick="app.router.navigate('#job-detail/${job.id}')">
                <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                <td style="font-weight: 500">${this.escapeHtml(job.name)}</td>
                <td style="color: var(--text-secondary)">${this.formatLocalTime(job.last_run_at) || 'Never'}</td>
                <td style="color: var(--text-secondary)">${this.formatLocalTime(job.next_run_time) || 'N/A'}</td>
            </tr>
        `;
    },

    renderJobTableRow(job) {
        const isRunning = job.last_status === 'running';
        const isFailed = job.last_status === 'failed';
        
        let badgeClass = 'badge-disabled';
        let badgeText = 'Disabled';
        
        if (job.enabled) {
            if (isRunning) { badgeClass = 'badge-warning'; badgeText = 'Running'; }
            else if (isFailed) { badgeClass = 'badge-danger'; badgeText = 'Failed'; }
            else { badgeClass = 'badge-success'; badgeText = 'Active'; }
        }

        const rowClass = (isFailed && job.enabled) ? 'row-failed' : '';

        return `
            <tr class="clickable-row ${rowClass}" onclick="app.router.navigate('#job-detail/${job.id}')">
                <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                <td style="font-weight: 500">${this.escapeHtml(job.name)}</td>
                <td><span class="job-cron">${this.escapeHtml(job.cron_expression)}</span></td>
                <td style="font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-secondary)">${this.escapeHtml(job.command)}</td>
                <td>
                    <div class="job-card-actions" style="margin-top: 0; display: inline-flex;">
                        <button class="btn btn-small" onclick="event.stopPropagation(); app.router.navigate('#job-edit/${job.id}')">Edit</button>
                        ${job.enabled 
                            ? `<button class="btn btn-small" onclick="event.stopPropagation(); app.toggleJob(${job.id}, false)">Disable</button>`
                            : `<button class="btn btn-small" onclick="event.stopPropagation(); app.toggleJob(${job.id}, true)">Enable</button>`
                        }
                        <button class="btn btn-small" style="color: var(--danger); border-color: rgba(239, 68, 68, 0.3)" onclick="event.stopPropagation(); if(confirm('Are you sure?')) app.deleteJob(${job.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    },

    formatLocalTime(utcStr) {
        if (!utcStr) return '';
        try {
            // utcStr from python backend is typically "YYYY-MM-DD HH:MM:SS"
            const t = utcStr.replace(' ', 'T') + 'Z';
            const date = new Date(t);
            if (isNaN(date.getTime())) return utcStr;
            return date.toLocaleString();
        } catch(e) {
            return utcStr;
        }
    },

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
             .toString()
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
};
