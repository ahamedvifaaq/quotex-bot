document.addEventListener('DOMContentLoaded', () => {
    // Initialize Chart
    const ctx = document.getElementById('performanceChart').getContext('2d');
    const performanceChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Wins', 'Losses'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8' }
                }
            },
            cutout: '70%'
        }
    });

    function formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    }

    function formatDate(timestamp) {
        return new Date(timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    async function updateDashboard() {
        try {
            // Fetch Stats
            const statsRes = await fetch('/api/stats');
            const stats = await statsRes.json();

            document.getElementById('total-trades').textContent = stats.total_trades;
            document.getElementById('win-rate').textContent = `${stats.win_rate}%`;
            document.getElementById('win-rate-bar').style.width = `${stats.win_rate}%`;

            const profitEl = document.getElementById('total-profit');
            profitEl.textContent = formatCurrency(stats.total_profit);
            profitEl.style.color = stats.total_profit >= 0 ? '#10b981' : '#ef4444';

            // Update Chart
            performanceChart.data.datasets[0].data = [stats.wins, stats.losses];
            performanceChart.update();

            // Fetch Trades
            const tradesRes = await fetch('/api/trades');
            const trades = await tradesRes.json();

            const tbody = document.getElementById('trades-body');
            tbody.innerHTML = trades.map(trade => `
                <tr>
                    <td>${trade.asset}</td>
                    <td class="direction-${trade.direction.toLowerCase()}">
                        ${trade.direction.toUpperCase()}
                    </td>
                    <td>${formatCurrency(trade.amount)}</td>
                    <td class="${trade.result ? trade.result.toLowerCase() : 'pending'}">
                        ${trade.result || 'PENDING'}
                    </td>
                    <td class="${trade.profit >= 0 ? 'win' : 'loss'}">
                        ${trade.profit ? formatCurrency(trade.profit) : '-'}
                    </td>
                    <td>${formatDate(trade.timestamp)}</td>
                </tr>
            `).join('');

        } catch (error) {
            console.error('Error updating dashboard:', error);
        }
    }

    // Initial load
    updateDashboard();

    // Auto-refresh every 5 seconds
    setInterval(updateDashboard, 5000);
});
