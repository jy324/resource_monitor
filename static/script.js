// Resource Monitor Dashboard JavaScript

// API configuration - uses relative path for flexibility
const API_BASE = '/api';
const REFRESH_INTERVAL = 10000; // 10 seconds

// State management
let refreshTimer = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Resource Monitor Dashboard initialized');
    loadDashboard();
    startAutoRefresh();
});

// Start auto-refresh
function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    refreshTimer = setInterval(loadDashboard, REFRESH_INTERVAL);
}

// Load dashboard data
async function loadDashboard() {
    try {
        // Fetch latest data and summary in parallel
        const [latestResponse, summaryResponse] = await Promise.all([
            fetch(`${API_BASE}/latest`),
            fetch(`${API_BASE}/summary`)
        ]);

        if (!latestResponse.ok || !summaryResponse.ok) {
            throw new Error('Failed to fetch data');
        }

        const latestData = await latestResponse.json();
        const summaryData = await summaryResponse.json();

        // Update dashboard
        updateSummary(summaryData);
        updateServers(latestData);
        updateLastUpdate();
        updateSystemStatus('healthy');
        hideError();

    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError(`无法加载数据: ${error.message}`);
        updateSystemStatus('error');
    }
}

// Update summary section
function updateSummary(data) {
    document.getElementById('totalServers').textContent = data.total_servers || 0;
    document.getElementById('onlineServers').textContent = data.servers_online || 0;
    document.getElementById('offlineServers').textContent = data.servers_offline || 0;
}

// Update servers grid
function updateServers(data) {
    const grid = document.getElementById('serversGrid');
    
    if (!data.servers || data.servers.length === 0) {
        grid.innerHTML = '<div class="no-data">暂无服务器数据</div>';
        return;
    }

    grid.innerHTML = '';
    
    data.servers.forEach(server => {
        const card = createServerCard(server);
        grid.appendChild(card);
    });
}

// Create server card
function createServerCard(server) {
    const card = document.createElement('div');
    const metrics = server.resource_metrics;
    const disk = server.disk_metrics;
    
    const status = metrics?.status || 'unknown';
    card.className = `server-card ${status === 'connected' ? 'online' : 'offline'}`;
    
    let html = `
        <div class="server-header">
            <div class="server-name">${escapeHtml(server.name || 'Unknown')}</div>
            <div class="server-status ${status === 'connected' ? 'connected' : 'disconnected'}">
                ${status === 'connected' ? '在线' : '离线'}
            </div>
        </div>
    `;
    
    if (metrics && status === 'connected') {
        html += `<div class="server-host">${escapeHtml(metrics.host || '')}</div>`;
        
        // CPU
        if (metrics.cpu !== null && metrics.cpu !== undefined) {
            const cpuLevel = getCpuLevel(metrics.cpu);
            const cpuId = `cpu-${server.name}`;
            const cpuCollapsed = isCollapsed(cpuId);
            const cpuIcon = cpuCollapsed ? '▶' : '▼';
            const cpuClass = cpuCollapsed ? ' collapsed' : '';
            html += `
                <div class="metric-section collapsible-section">
                    <div class="metric-title collapsible-header" onclick="toggleCollapse('${cpuId}')">
                        <span>💻 CPU 使用率</span>
                        <span class="collapse-icon">${cpuIcon}</span>
                    </div>
                    <div class="collapsible-content${cpuClass}" id="${cpuId}">
                        <div class="metric-item">
                            <span class="metric-label">当前使用率</span>
                            <span class="metric-value">${metrics.cpu.toFixed(1)}%</span>
                        </div>
                        <div class="metric-bar">
                            <div class="metric-bar-fill ${cpuLevel}" style="width: ${metrics.cpu}%"></div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Memory
        if (metrics.memory) {
            const memLevel = getUsageLevel(metrics.memory.percentage);
            const memId = `mem-${server.name}`;
            const memCollapsed = isCollapsed(memId);
            const memIcon = memCollapsed ? '▶' : '▼';
            const memClass = memCollapsed ? ' collapsed' : '';
            html += `
                <div class="metric-section collapsible-section">
                    <div class="metric-title collapsible-header" onclick="toggleCollapse('${memId}')">
                        <span>🧠 内存使用</span>
                        <span class="collapse-icon">${memIcon}</span>
                    </div>
                    <div class="collapsible-content${memClass}" id="${memId}">
                        <div class="metric-item">
                            <span class="metric-label">已使用</span>
                            <span class="metric-value">${formatMemory(metrics.memory.used_mb)} / ${formatMemory(metrics.memory.total_mb)}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">使用率</span>
                            <span class="metric-value">${metrics.memory.percentage.toFixed(1)}%</span>
                        </div>
                        <div class="metric-bar">
                            <div class="metric-bar-fill ${memLevel}" style="width: ${metrics.memory.percentage}%"></div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // GPU
        if (metrics.gpu && metrics.gpu.length > 0) {
            const gpuId = `gpu-${server.name}`;
            const gpuCollapsed = isCollapsed(gpuId);
            const gpuIcon = gpuCollapsed ? '▶' : '▼';
            const gpuClass = gpuCollapsed ? ' collapsed' : '';
            html += `
                <div class="metric-section collapsible-section">
                    <div class="metric-title collapsible-header" onclick="toggleCollapse('${gpuId}')">
                        <span>🎮 GPU 状态</span>
                        <span class="collapse-icon">${gpuIcon}</span>
                    </div>
                    <div class="collapsible-content${gpuClass}" id="${gpuId}">
            `;
            metrics.gpu.forEach((gpu, index) => {
                const gpuLevel = getUsageLevel(gpu.utilization);
                html += `
                    <div class="gpu-item">
                        <div class="metric-item">
                            <span class="metric-label">GPU ${gpu.index}: ${escapeHtml(gpu.name)}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">利用率</span>
                            <span class="metric-value">${gpu.utilization.toFixed(1)}%</span>
                        </div>
                        <div class="metric-bar">
                            <div class="metric-bar-fill ${gpuLevel}" style="width: ${gpu.utilization}%"></div>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">显存</span>
                            <span class="metric-value">${formatMemory(gpu.memory_used_mb)} / ${formatMemory(gpu.memory_total_mb)}</span>
                        </div>
                    </div>
                `;
            });
            html += `</div></div>`;
        }
    }
    
    // Disk usage
    if (disk && disk.disk && Object.keys(disk.disk).length > 0) {
        const diskId = `disk-${server.name}`;
        const diskCollapsed = isCollapsed(diskId);
        const diskIcon = diskCollapsed ? '▶' : '▼';
        const diskClass = diskCollapsed ? ' collapsed' : '';
        html += `
            <div class="metric-section collapsible-section">
                <div class="metric-title collapsible-header" onclick="toggleCollapse('${diskId}')">
                    <span>💾 磁盘使用</span>
                    <span class="collapse-icon">${diskIcon}</span>
                </div>
                <div class="collapsible-content${diskClass}" id="${diskId}">
        `;
        Object.entries(disk.disk).forEach(([path, info]) => {
            if (info) {
                const diskLevel = getUsageLevel(info.percentage);
                html += `
                    <div class="metric-item">
                        <span class="metric-label"><span class="disk-path">${escapeHtml(path)}</span></span>
                        <span class="metric-value">${info.percentage.toFixed(1)}%</span>
                    </div>
                    <div class="metric-bar">
                        <div class="metric-bar-fill ${diskLevel}" style="width: ${info.percentage}%"></div>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">已使用 / 总容量</span>
                        <span class="metric-value">${formatDisk(info.used_mb)} / ${formatDisk(info.total_mb)}</span>
                    </div>
                `;
            }
        });
        html += `</div></div>`;
    }
    
    // Timestamp
    const timestamp = metrics?.timestamp || disk?.timestamp;
    if (timestamp) {
        html += `<div class="timestamp">更新时间: ${formatTimestamp(timestamp)}</div>`;
    }
    
    card.innerHTML = html;
    return card;
}

// Utility functions
function formatMemory(mb) {
    if (mb >= 1024) {
        return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb.toFixed(0)} MB`;
}

function formatDisk(mb) {
    if (mb >= 1024 * 1024) {
        return `${(mb / (1024 * 1024)).toFixed(1)} TB`;
    } else if (mb >= 1024) {
        return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb.toFixed(0)} MB`;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function getCpuLevel(value) {
    if (value > 80) return 'high';
    if (value > 50) return 'medium';
    return '';
}

function getUsageLevel(value) {
    if (value > 85) return 'high';
    if (value > 60) return 'medium';
    return '';
}

function updateLastUpdate() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function updateSystemStatus(status) {
    const badge = document.getElementById('systemStatus');
    badge.className = `status-badge ${status}`;
    badge.textContent = status === 'healthy' ? '正常运行' : '错误';
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.style.display = 'none';
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Check if a section should be collapsed based on localStorage
function isCollapsed(elementId) {
    const state = localStorage.getItem(`collapse-${elementId}`);
    return state === 'collapsed';
}

// Toggle collapse/expand for metric sections
function toggleCollapse(elementId) {
    const content = document.getElementById(elementId);
    const header = content.previousElementSibling;
    const icon = header.querySelector('.collapse-icon');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        icon.textContent = '▼';
        // Save expanded state
        localStorage.setItem(`collapse-${elementId}`, 'expanded');
    } else {
        content.classList.add('collapsed');
        icon.textContent = '▶';
        // Save collapsed state
        localStorage.setItem(`collapse-${elementId}`, 'collapsed');
    }
}
