// Factory anomaly bar chart
if (document.getElementById('factoryChart') && factoryData.length) {
    new Chart(document.getElementById('factoryChart'), {
        type: 'bar',
        data: {
            labels: factoryData.map(d => d.factory),
            datasets: [{
                label: 'Anomali Sayisi',
                data: factoryData.map(d => d.count),
                backgroundColor: '#dc2626cc',
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

// Risk distribution donut
if (document.getElementById('riskChart') && riskData.length) {
    const riskColors = { high: '#dc2626', medium: '#ea580c', low: '#22c55e' };
    new Chart(document.getElementById('riskChart'), {
        type: 'doughnut',
        data: {
            labels: riskData.map(d => d.risk_level.toUpperCase()),
            datasets: [{
                data: riskData.map(d => d.count),
                backgroundColor: riskData.map(d => riskColors[d.risk_level] || '#6c757d'),
                borderWidth: 2,
                borderColor: '#fff',
            }]
        },
        options: {
            plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } },
            cutout: '60%',
        }
    });
}

// Anomaly trend line chart
if (document.getElementById('trendChart') && trendData.length) {
    new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: trendData.map(d => d.date),
            datasets: [{
                label: 'Anomali',
                data: trendData.map(d => d.count),
                borderColor: '#dc2626',
                backgroundColor: '#dc262615',
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointHoverRadius: 5,
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } },
                x: { ticks: { maxTicksLimit: 10 } }
            }
        }
    });
}

// Product type quality horizontal bar
if (document.getElementById('qualityChart') && qualityData.length) {
    new Chart(document.getElementById('qualityChart'), {
        type: 'bar',
        data: {
            labels: qualityData.map(d => d.product_type.length > 12
                ? d.product_type.substring(0, 12) + '...'
                : d.product_type),
            datasets: [{
                label: 'Ort. Kalite',
                data: qualityData.map(d => d.avg_quality),
                backgroundColor: '#0d9488cc',
                borderRadius: 4,
                borderSkipped: false,
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, max: 100 } }
        }
    });
}
