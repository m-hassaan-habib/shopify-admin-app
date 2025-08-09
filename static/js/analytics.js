document.addEventListener('DOMContentLoaded', () => {
    let ctx = document.getElementById('earningsChart').getContext('2d');
    let labels = JSON.parse(document.getElementById('chartLabels').textContent);
    let values = JSON.parse(document.getElementById('chartValues').textContent);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Earnings',
                data: values,
                borderColor: '#3a5eb4',
                backgroundColor: 'rgba(58, 94, 180, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Earnings'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });

    document.querySelectorAll('.range-toggle').forEach(link => {
        link.addEventListener('click', event => {
            event.preventDefault();
            let range = event.target.dataset.range;
            window.location.search = `?range=${range}`;
        });
    });
});