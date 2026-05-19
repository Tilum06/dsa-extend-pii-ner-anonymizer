/**
 * PII Detection Web Demo - Frontend Script
 * Handles user interactions and API communication
 */

/* ============================================================
   Entity colour map
   ============================================================ */
const ENTITY_COLORS = {
    NAME:         { color: '#3b82f6', bg: 'rgba(59,130,246,0.18)' },
    EMAIL:        { color: '#f59e0b', bg: 'rgba(245,158,11,0.18)' },
    PHONE:        { color: '#10b981', bg: 'rgba(16,185,129,0.18)' },
    ADDRESS:      { color: '#a855f7', bg: 'rgba(168,85,247,0.18)' },
    USERNAME:     { color: '#ec4899', bg: 'rgba(236,72,153,0.18)' },
    URL:          { color: '#06b6d4', bg: 'rgba(6,182,212,0.18)' },
    ORGANIZATION: { color: '#14b8a6', bg: 'rgba(20,184,166,0.18)' },
    LOCATION:     { color: '#38bdf8', bg: 'rgba(56,189,248,0.18)' },
};

/* ============================================================
   State
   ============================================================ */
let currentResults = null;

/* ============================================================
   Core: Process text
   ============================================================ */
async function processText() {
    const inputText = document.getElementById('inputText').value.trim();

    if (!inputText) {
        showError('Please enter text to process');
        return;
    }

    clearError();
    showLoading();

    try {
        const response = await fetch('/api/detect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: inputText }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        const data = await response.json();
        hideLoading();
        currentResults = data;
        displayResults(data);

    } catch (error) {
        hideLoading();
        console.error('Error:', error);
        showError(`Error processing: ${error.message}`);
    }
}

/* ============================================================
   Display results
   ============================================================ */
function displayResults(data) {
    const resultSection = document.getElementById('resultSection');
    const summaryPanel = document.getElementById('summaryPanel');

    // --- Highlighted tokens ---
    renderHighlightedTokens(data.token_entities || []);

    // --- Anonymized text ---
    document.getElementById('anonymizedText').textContent = data.anonymized_text;

    // --- Update summary panel ---
    updateSummaryPanel(data.entities || []);

    // --- Show sections ---
    resultSection.classList.remove('hidden');
    summaryPanel.classList.remove('hidden');

    // Switch to first tab
    switchTab('tagged');
}

/* ---- Highlighted inline tokens ---- */
function renderHighlightedTokens(tokenEntities) {
    const container = document.getElementById('highlightedText');
    const legend = document.getElementById('entityLegend');
    container.innerHTML = '';
    legend.innerHTML = '';

    const seenTypes = new Set();

    tokenEntities.forEach((item, idx) => {
        const span = document.createElement('span');
        span.classList.add('token');

        if (item.label !== 'O') {
            // Extract base entity type from BIO label (e.g. "B-NAME" → "NAME")
            const baseType = item.label.replace(/^[BI]-/, '');
            span.classList.add('entity', `entity-${baseType}`);
            span.textContent = escapeHtml(item.token);
            seenTypes.add(baseType);
        } else {
            span.textContent = item.token;
        }

        container.appendChild(span);

        // Add a space between tokens
        if (idx < tokenEntities.length - 1) {
            container.appendChild(document.createTextNode(' '));
        }
    });

    // Build legend
    for (const type of [...seenTypes].sort()) {
        const colors = ENTITY_COLORS[type] || { color: '#64748b', bg: 'rgba(100,116,139,0.15)' };
        const item = document.createElement('span');
        item.classList.add('legend-item');
        item.innerHTML =
            `<span class="legend-dot" style="background:${colors.color}"></span>${type}`;
        legend.appendChild(item);
    }
}

/* ---- Summary Panel ---- */
function updateSummaryPanel(entities) {
    const totalEl = document.getElementById('totalEntities');
    const entityTypes = ['NAME', 'EMAIL', 'PHONE', 'ADDRESS', 'USERNAME', 'URL', 'ORGANIZATION', 'LOCATION'];
    
    // Count entities by type
    const counts = {};
    entityTypes.forEach(type => counts[type] = 0);
    
    entities.forEach(entity => {
        if (counts.hasOwnProperty(entity.type)) {
            counts[entity.type]++;
        }
    });

    // Update total
    totalEl.textContent = entities.length;

    // Update individual counts
    entityTypes.forEach(type => {
        const el = document.getElementById(`count-${type}`);
        if (el) {
            el.textContent = counts[type];
        }
    });
}

/* ============================================================
   Tabs
   ============================================================ */
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active state from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const tabEl = document.getElementById(`tab-${tabName}`);
    if (tabEl) {
        tabEl.classList.add('active');
    }

    // Mark button as active
    const btnEl = document.querySelector(`[data-tab="${tabName}"]`);
    if (btnEl) {
        btnEl.classList.add('active');
    }
}

// Tab button listeners
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });

    // Keyboard shortcut for process
    document.getElementById('inputText').addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            processText();
        }
    });
});

/* ============================================================
   UI helpers
   ============================================================ */
function showLoading() {
    document.getElementById('loadingSpinner').classList.remove('hidden');
    document.getElementById('processBtn').disabled = true;
}

function hideLoading() {
    document.getElementById('loadingSpinner').classList.add('hidden');
    document.getElementById('processBtn').disabled = false;
}

function showError(message) {
    const section = document.getElementById('errorSection');
    document.getElementById('errorText').textContent = message;
    section.classList.remove('hidden');
}

function clearError() {
    document.getElementById('errorSection').classList.add('hidden');
}

function clearAll() {
    document.getElementById('inputText').value = '';
    document.getElementById('resultSection').classList.add('hidden');
    document.getElementById('summaryPanel').classList.add('hidden');
    clearError();
    currentResults = null;
}

/* ---- Load Sample ---- */
function loadSample() {
    const sample = SAMPLE_TEXTS[Math.floor(Math.random() * SAMPLE_TEXTS.length)];
    document.getElementById('inputText').value = sample;
    document.getElementById('inputText').focus();
}

/* ---- Copy to clipboard ---- */
function copyToClipboard() {
    const text = document.getElementById('anonymizedText').textContent;
    if (!text) {
        showError('No text to copy');
        return;
    }

    navigator.clipboard.writeText(text)
        .then(() => {
            const btn = document.getElementById('copyBtn');
            const orig = btn.textContent;
            btn.textContent = '✓ Copied!';
            setTimeout(() => { btn.textContent = orig; }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy:', err);
            showError('Unable to copy text');
        });
}

/* ---- HTML escaping ---- */
function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}
