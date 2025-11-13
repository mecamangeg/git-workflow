// Git Workflow Guardian - Dashboard JavaScript

let trendsChart = null;
let rulesChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadViolations();
    loadRepositories();
    loadTrends();

    // Auto-refresh every 30 seconds
    setInterval(refreshData, 30000);
});

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        // Update stats cards
        document.getElementById('complianceScore').textContent =
            Math.round(data.compliance_score) + '%';
        document.getElementById('totalViolations').textContent =
            data.total_violations || 0;
        document.getElementById('criticalCount').textContent =
            data.by_severity?.critical || 0;
        document.getElementById('warningCount').textContent =
            data.by_severity?.warning || 0;
        document.getElementById('suggestionCount').textContent =
            data.by_severity?.suggestion || 0;
        document.getElementById('overrideCount').textContent =
            data.overridden_count || 0;

        // Update rules chart
        updateRulesChart(data.by_rule || {});

    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadViolations() {
    try {
        const response = await fetch('/api/violations/live');
        const data = await response.json();

        const liveFeed = document.getElementById('liveFeed');

        if (data.violations.length === 0) {
            liveFeed.innerHTML = '<p class="loading">No recent violations (last hour)</p>';
            return;
        }

        liveFeed.innerHTML = data.violations.map(v => `
            <div class="violation-item ${v.severity}">
                <div class="violation-header">
                    <span class="violation-rule">${v.rule_name}</span>
                    <span class="violation-time">${formatTime(v.timestamp)}</span>
                </div>
                <div class="violation-details">
                    <strong>Branch:</strong> ${v.branch || 'N/A'} |
                    <strong>Repo:</strong> ${getRepoName(v.repo)} |
                    <strong>Severity:</strong> ${v.severity}
                    ${v.overridden ? ' | <span style="color: #f59e0b">⚠️ Overridden</span>' : ''}
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load violations:', error);
    }
}

async function loadRepositories() {
    try {
        const response = await fetch('/api/repositories');
        const data = await response.json();

        const reposList = document.getElementById('repositoriesList');

        if (data.repositories.length === 0) {
            reposList.innerHTML = '<p class="loading">No repositories being monitored</p>';
            return;
        }

        reposList.innerHTML = data.repositories.map(repo => `
            <div class="repo-item">
                <div class="repo-name">${repo.name}</div>
                <div class="repo-path">${repo.path}</div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load repositories:', error);
    }
}

async function loadTrends() {
    try {
        const response = await fetch('/api/trends?days=30');
        const data = await response.json();

        updateTrendsChart(data);

    } catch (error) {
        console.error('Failed to load trends:', error);
    }
}

function updateTrendsChart(data) {
    const ctx = document.getElementById('trendsChart').getContext('2d');

    if (trendsChart) {
        trendsChart.destroy();
    }

    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Violations per Day',
                data: data.daily_counts,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function updateRulesChart(rulesData) {
    const ctx = document.getElementById('rulesChart').getContext('2d');

    if (rulesChart) {
        rulesChart.destroy();
    }

    const labels = Object.keys(rulesData);
    const values = Object.values(rulesData);

    rulesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Violation Count',
                data: values,
                backgroundColor: [
                    '#dc2626',
                    '#f59e0b',
                    '#10b981',
                    '#2563eb',
                    '#8b5cf6',
                    '#ec4899'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) { // < 1 minute
        return 'Just now';
    } else if (diff < 3600000) { // < 1 hour
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m ago`;
    } else if (diff < 86400000) { // < 1 day
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    } else {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
}

function getRepoName(path) {
    return path.split('/').pop() || path;
}

function exportCSV() {
    window.location.href = '/api/export/csv';
}

function refreshData() {
    loadStats();
    loadViolations();
    loadRepositories();
    loadTrends();
}
