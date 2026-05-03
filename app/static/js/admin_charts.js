/**
 * app/static/js/admin_charts.js
 * Centralized Chart.js initialization for all admin pages.
 *
 * Strategy: Data is passed from Jinja2 templates via `data-*` attributes
 * on each <canvas> element, eliminating ALL inline JS from HTML templates.
 *
 * Example usage in template:
 *   <canvas id="trafficChart"
 *           data-labels='{{ chart_labels|tojson }}'
 *           data-views='{{ views_data|tojson }}'
 *           data-clicks='{{ clicks_data|tojson }}'>
 *   </canvas>
 */

'use strict';

// ─────────────────────────────────────────────
// Shared Design Tokens (mirrors admin.css vars)
// ─────────────────────────────────────────────
const CHART_COLORS = {
    accent:       '#c49b48',
    accentAlpha:  'rgba(196, 155, 72, 0.15)',
    blue:         '#3b82f6',
    pink:         '#ec4899',
    slate:        '#94a3b8',
    gridLine:     'rgba(0,0,0,0.05)',
    gridLineLight:'#f1f5f9',
    radarGrid:    '#e2e8f0',
};

const CHART_FONT = { family: 'Noto Kufi Arabic', size: 12 };

/**
 * Safe JSON parse from dataset attribute.
 */
function parseData(el, attr) {
    try { return JSON.parse(el.dataset[attr] || 'null'); }
    catch { return null; }
}

// ─────────────────────────────────────────────
// 1. Traffic Line Chart  (dashboard.html)
//    canvas#trafficChart  →  data-labels, data-views, data-clicks
// ─────────────────────────────────────────────
function initTrafficChart() {
    const el = document.getElementById('trafficChart');
    if (!el) return;

    const labels     = parseData(el, 'labels')  || [];
    const viewsData  = parseData(el, 'views')   || [];
    const clicksData = parseData(el, 'clicks')  || [];

    new Chart(el.getContext('2d'), {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'المشاهدات',
                    data: viewsData,
                    borderColor:          CHART_COLORS.accent,
                    backgroundColor:      CHART_COLORS.accentAlpha,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#fff',
                    pointBorderColor:     CHART_COLORS.accent,
                    pointRadius: 5,
                },
                {
                    label: 'النقرات',
                    data: clicksData,
                    borderColor:     CHART_COLORS.blue,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    pointRadius: 0,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    rtl: true,
                    labels: { font: CHART_FONT, usePointStyle: true },
                },
            },
            scales: {
                y: { beginAtZero: true, grid: { drawBorder: false, color: CHART_COLORS.gridLine } },
                x: { grid: { display: false } },
            },
        },
    });
}

// ─────────────────────────────────────────────
// 2. Vibe Radar Chart  (expert_analytics.html)
//    canvas#vibeChart  →  data-labels, data-values
// ─────────────────────────────────────────────
function initVibeChart() {
    const el = document.getElementById('vibeChart');
    if (!el) return;

    const labels = parseData(el, 'labels') || [];
    const values = parseData(el, 'values') || [];

    new Chart(el, {
        type: 'radar',
        data: {
            labels,
            datasets: [{
                label: 'عدد الطلبات',
                data: values,
                backgroundColor: 'rgba(196, 155, 72, 0.2)',
                borderColor: CHART_COLORS.accent,
                borderWidth: 2,
                pointBackgroundColor: CHART_COLORS.accent,
            }],
        },
        options: {
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: CHART_COLORS.radarGrid },
                    grid:       { color: CHART_COLORS.radarGrid },
                    pointLabels: { font: { family: 'Noto Kufi Arabic', size: 11, weight: '700' } },
                    suggestedMin: 0,
                },
            },
            plugins: { legend: { display: false } },
        },
    });
}

// ─────────────────────────────────────────────
// 3. Gender Doughnut Chart  (expert_analytics.html)
//    canvas#genderChart  →  data-labels, data-values
// ─────────────────────────────────────────────
function initGenderChart() {
    const el = document.getElementById('genderChart');
    if (!el) return;

    new Chart(el, {
        type: 'doughnut',
        data: {
            labels: parseData(el, 'labels') || [],
            datasets: [{
                data:            parseData(el, 'values') || [],
                backgroundColor: [CHART_COLORS.blue, CHART_COLORS.pink, CHART_COLORS.slate],
                borderWidth: 0,
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { font: { family: 'Noto Kufi Arabic' } } },
            },
        },
    });
}

// ─────────────────────────────────────────────
// 4. Apparel Bar Chart  (expert_analytics.html)
//    canvas#apparelChart  →  data-labels, data-values
// ─────────────────────────────────────────────
function initApparelChart() {
    const el = document.getElementById('apparelChart');
    if (!el) return;

    new Chart(el, {
        type: 'bar',
        data: {
            labels: parseData(el, 'labels') || [],
            datasets: [{
                label: 'عدد المرات',
                data:  parseData(el, 'values') || [],
                backgroundColor: CHART_COLORS.accent,
                borderRadius: 4,
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, grid: { color: CHART_COLORS.gridLineLight } },
            },
        },
    });
}

// ─────────────────────────────────────────────
// 5. Price History Line Chart  (item_form.html)
//    canvas#priceHistoryChart  →  data-labels, data-values
// ─────────────────────────────────────────────
function initPriceHistoryChart() {
    const el = document.getElementById('priceHistoryChart');
    if (!el) return;

    new Chart(el.getContext('2d'), {
        type: 'line',
        data: {
            labels: parseData(el, 'labels') || [],
            datasets: [{
                label: 'السعر',
                data:  parseData(el, 'values') || [],
                borderColor:     CHART_COLORS.accent,
                backgroundColor: CHART_COLORS.accentAlpha,
                fill: true,
                tension: 0.4,
            }],
        },
        options: {
            plugins: { legend: { display: false } },
            scales:  { y: { beginAtZero: false } },
        },
    });
}

// ─────────────────────────────────────────────
// Auto-init all charts on DOM ready
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTrafficChart();
    initVibeChart();
    initGenderChart();
    initApparelChart();
    initPriceHistoryChart();
});
