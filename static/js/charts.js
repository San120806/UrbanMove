document.addEventListener('DOMContentLoaded', function() {
    // Colors and fonts matching our CSS variables
    const fontColor = '#94a3b8'; // text-secondary
    const gridColor = 'rgba(255, 255, 255, 0.05)';
    const fontFamily = "'Outfit', sans-serif";

    // Global configurations for Chart.js
    Chart.defaults.font.family = fontFamily;
    Chart.defaults.color = fontColor;
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;

    // Fetch the analytical data
    fetch('/api/analytics')
        .then(response => response.json())
        .then(res => {
            if (!res.success) {
                console.error("Failed to load analytics: ", res.error);
                return;
            }

            // --------------------------------------------------------
            // 1. Revenue Line Chart
            // --------------------------------------------------------
            const revCtx = document.getElementById('revenueChart').getContext('2d');
            
            // Create gradient for the area chart
            const revGradient = revCtx.createLinearGradient(0, 0, 0, 300);
            revGradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
            revGradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

            new Chart(revCtx, {
                type: 'line',
                data: {
                    labels: res.revenue.labels,
                    datasets: [{
                        label: 'Revenue ($)',
                        data: res.revenue.data,
                        borderColor: '#6366f1',
                        borderWidth: 3,
                        backgroundColor: revGradient,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#818cf8',
                        pointBorderColor: 'rgba(255, 255, 255, 0.8)',
                        pointHoverRadius: 7,
                        pointRadius: 4
                    }]
                },
                options: {
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { color: gridColor },
                            ticks: { font: { size: 11 } }
                        },
                        y: {
                            grid: { color: gridColor },
                            ticks: {
                                font: { size: 11 },
                                callback: function(value) { return '$' + value; }
                            }
                        }
                    }
                }
            });

            // --------------------------------------------------------
            // 2. Ride Volume Bar Chart
            // --------------------------------------------------------
            const volCtx = document.getElementById('volumeChart').getContext('2d');
            new Chart(volCtx, {
                type: 'bar',
                data: {
                    labels: res.volume.labels,
                    datasets: [{
                        label: 'Trips Booked',
                        data: res.volume.data,
                        backgroundColor: '#f59e0b',
                        borderRadius: 6,
                        borderSkipped: false,
                        maxBarThickness: 30
                    }]
                },
                options: {
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { font: { size: 11 } }
                        },
                        y: {
                            grid: { color: gridColor },
                            ticks: {
                                font: { size: 11 },
                                precision: 0
                            }
                        }
                    }
                }
            });

            // --------------------------------------------------------
            // 3. Driver Status Doughnut Chart
            // --------------------------------------------------------
            const statusCtx = document.getElementById('driverStatusChart').getContext('2d');
            
            // Map labels to matching CSS colors: Active -> Green, Offline -> Slate/Gray, Suspended -> Red
            const colorMap = {
                'Active': '#10b981',
                'Offline': '#64748b',
                'Suspended': '#ef4444'
            };
            const chartColors = res.driver_status.labels.map(label => colorMap[label] || '#6366f1');

            new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: res.driver_status.labels,
                    datasets: [{
                        data: res.driver_status.data,
                        backgroundColor: chartColors,
                        borderWidth: 3,
                        borderColor: '#111a2e', // Matches card background
                        hoverOffset: 4
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                padding: 15,
                                font: { size: 12 }
                            }
                        }
                    },
                    cutout: '65%'
                }
            });

        })
        .catch(err => {
            console.error("Error fetching analytics api: ", err);
        });
});
