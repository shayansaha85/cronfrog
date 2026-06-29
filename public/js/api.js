const api = {
    baseUrl: '/api',
    
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        try {
            const response = await fetch(url, { ...options, headers });
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'API request failed');
            }
            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    },

    getJobs() { return this.request('/jobs'); },
    getJob(id) { return this.request(`/jobs/${id}`); },
    createJob(data) { return this.request('/jobs', { method: 'POST', body: JSON.stringify(data) }); },
    updateJob(id, data) { return this.request(`/jobs/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
    deleteJob(id) { return this.request(`/jobs/${id}`, { method: 'DELETE' }); },
    startJob(id) { return this.request(`/jobs/${id}/start`, { method: 'POST' }); },
    stopJob(id) { return this.request(`/jobs/${id}/stop`, { method: 'POST' }); },
    runJob(id) { return this.request(`/jobs/${id}/run`, { method: 'POST' }); },
    killJobRun(jobId, runId) { return this.request(`/jobs/${jobId}/runs/${runId}/kill`, { method: 'POST' }); },
    getJobRuns(jobId) { return this.request(`/jobs/${jobId}/runs`); },
    getStats() { return this.request('/stats'); }
};
