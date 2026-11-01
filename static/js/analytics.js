/**
 * EXPIRYGUARD AI — ANALYTICS CHARTS (Chart.js)
 * Visualizing real database records for sales trends, expiry health, and top products
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (typeof Chart === 'undefined') return;

  try {
    const res = await fetch('/api/analytics/data');
    const data = await res.json();

    // 1. Sales Trend Chart
    const salesCanvas = document.getElementById('chart-sales-trend');
    if (salesCanvas && data.sales_trend) {
      new Chart(salesCanvas, {
        type: 'line',
        data: {
          labels: data.sales_trend.labels,
          datasets: [
            {
              label: 'Daily Revenue (₹)',
              data: data.sales_trend.revenue,
              borderColor: '#EC4899',
              backgroundColor: 'rgba(236, 72, 153, 0.15)',
              borderWidth: 3,
              fill: true,
              tension: 0.35,
              pointBackgroundColor: '#DB2777',
              pointRadius: 5
            },
            {
              label: 'Units Sold',
              data: data.sales_trend.units,
              borderColor: '#6366F1',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.35,
              pointBackgroundColor: '#4F46E5',
              pointRadius: 4,
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: 'Revenue (₹)' },
              grid: { color: '#FFE4E8' }
            },
            y1: {
              beginAtZero: true,
              position: 'right',
              title: { display: true, text: 'Units' },
              grid: { display: false }
            },
            x: {
              grid: { display: false }
            }
          }
        }
      });
    }

    // 2. Expiry Status Breakdown Doughnut Chart
    const expiryCanvas = document.getElementById('chart-expiry-distribution');
    if (expiryCanvas && data.expiry_distribution) {
      new Chart(expiryCanvas, {
        type: 'doughnut',
        data: {
          labels: data.expiry_distribution.labels,
          datasets: [{
            data: data.expiry_distribution.data,
            backgroundColor: [
              '#DC2626', // Expired
              '#EA580C', // <=7d
              '#D97706', // <=15d
              '#CA8A04', // <=30d
              '#10B981'  // Safe
            ],
            borderWidth: 2,
            borderColor: '#FFFFFF'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom' }
          },
          cutout: '65%'
        }
      });
    }

    // 3. Top Products Chart
    const topCanvas = document.getElementById('chart-top-products');
    if (topCanvas && data.top_products && data.top_products.length > 0) {
      new Chart(topCanvas, {
        type: 'bar',
        data: {
          labels: data.top_products.map(p => p.name),
          datasets: [{
            label: 'Units Sold',
            data: data.top_products.map(p => p.units),
            backgroundColor: '#F472B6',
            borderRadius: 6
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { beginAtZero: true, grid: { color: '#FFE4E8' } },
            y: { grid: { display: false } }
          }
        }
      });
    }

  } catch (err) {
    console.error("Failed to render analytics charts:", err);
  }
});
