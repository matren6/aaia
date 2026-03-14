/**
 * Chart.js Utility Functions
 * Helpers for creating and managing charts used throughout the dashboard
 */

class ChartUtils {
    /**
     * Create a line chart for time-series data
     */
    static createLineChart(canvasId, labels, datasets, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets.map(dataset => ({
                    label: dataset.label,
                    data: dataset.data,
                    borderColor: dataset.borderColor || '#007bff',
                    backgroundColor: dataset.backgroundColor || 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: dataset.fill !== false,
                    tension: 0.4,
                    ...dataset
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                ...options
            }
        });
    }

    /**
     * Create a bar chart
     */
    static createBarChart(canvasId, labels, datasets, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets.map(dataset => ({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: dataset.backgroundColor || '#007bff',
                    borderColor: dataset.borderColor || '#0056b3',
                    borderWidth: 1,
                    ...dataset
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                ...options
            }
        });
    }

    /**
     * Create a pie or doughnut chart
     */
    static createPieChart(canvasId, labels, data, options = {}, type = 'pie') {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const colors = [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF',
            '#FF9F40',
            '#FF6384',
            '#C9CBCF'
        ];

        return new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                },
                ...options
            }
        });
    }

    /**
     * Create a progress gauge chart
     */
    static createGaugeChart(canvasId, value, maxValue = 100, label = '', options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const percentage = (value / maxValue) * 100;
        const color = percentage > 80 ? '#28a745' : percentage > 50 ? '#ffc107' : '#dc3545';

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [label, ''],
                datasets: [{
                    data: [percentage, 100 - percentage],
                    backgroundColor: [color, '#e9ecef']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                },
                ...options
            }
        });
    }

    /**
     * Create a mixed chart (line + bar)
     */
    static createMixedChart(canvasId, labels, lineData, barData, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        type: 'bar',
                        label: barData.label || 'Bar Data',
                        data: barData.data,
                        backgroundColor: barData.backgroundColor || '#36A2EB',
                        borderColor: barData.borderColor || '#0056b3',
                        borderWidth: 1
                    },
                    {
                        type: 'line',
                        label: lineData.label || 'Line Data',
                        data: lineData.data,
                        borderColor: lineData.borderColor || '#FF6384',
                        backgroundColor: lineData.backgroundColor || 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true
                    }
                },
                ...options
            }
        });
    }

    /**
     * Create a radar chart
     */
    static createRadarChart(canvasId, labels, datasets, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: datasets.map(dataset => ({
                    label: dataset.label,
                    data: dataset.data,
                    borderColor: dataset.borderColor || '#007bff',
                    backgroundColor: dataset.backgroundColor || 'rgba(0, 123, 255, 0.1)',
                    ...dataset
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                ...options
            }
        });
    }

    /**
     * Generate random color
     */
    static getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    /**
     * Generate color palette
     */
    static generateColorPalette(count) {
        const palette = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
        ];
        
        const result = [];
        for (let i = 0; i < count; i++) {
            result.push(palette[i % palette.length]);
        }
        return result;
    }

    /**
     * Destroy chart and cleanup
     */
    static destroyChart(chart) {
        if (chart) {
            chart.destroy();
        }
    }
}

// Export for use in modules (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartUtils;
}
