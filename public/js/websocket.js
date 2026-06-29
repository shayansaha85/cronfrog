class LogStreamer {
    constructor(terminalEl) {
        this.terminalEl = terminalEl;
        this.ws = null;
        this.isAutoScroll = true;
        
        this.terminalEl.addEventListener('scroll', () => {
            const isAtBottom = this.terminalEl.scrollHeight - this.terminalEl.scrollTop <= this.terminalEl.clientHeight + 10;
            this.isAutoScroll = isAtBottom;
        });
    }

    connect(runId) {
        this.disconnect();
        this.terminalEl.innerHTML = '';
        this.appendLog('system', `Connecting to live output stream for run ${runId}...\n`);
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws/runs/${runId}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === 'close') {
                    this.appendLog('system', '\n[Stream Closed by Server]\n');
                    this.ws.close();
                } else {
                    this.appendLog(msg.type, msg.data);
                }
            } catch (e) {
                console.error("WS parse error", e);
            }
        };
        
        this.ws.onclose = () => {
            this.appendLog('system', '\n[Connection Closed]\n');
        };
        
        this.ws.onerror = (err) => {
            this.appendLog('stderr', '\n[WebSocket Error]\n');
        };
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    appendLog(type, text) {
        const span = document.createElement('span');
        span.className = `terminal-line log-${type}`;
        span.textContent = text;
        this.terminalEl.appendChild(span);
        
        if (this.isAutoScroll) {
            this.terminalEl.scrollTop = this.terminalEl.scrollHeight;
        }
    }
}
