/**
 * PII Detection Web Demo - Frontend Script
 * Handles user interactions and API communication
 */

/* ============================================================
   Entity colour map (must match CSS variables)
   ============================================================ */
const ENTITY_COLORS = {
    EMAIL:    { color: '#f59e0b', bg: 'rgba(245,158,11,0.15)' },
    URL:      { color: '#06b6d4', bg: 'rgba(6,182,212,0.15)'  },
    PHONE:    { color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
    ADDRESS:  { color: '#f97316', bg: 'rgba(249,115,22,0.15)' },
    NAME:     { color: '#ec4899', bg: 'rgba(236,72,153,0.15)' },
    USERNAME: { color: '#8b5cf6', bg: 'rgba(139,92,246,0.15)' },
};

/* ============================================================
   Core: Process text
   ============================================================ */
async function processText() {
    const inputText = document.getElementById('inputText').value.trim();

    if (!inputText) {
        showError('Vui lòng nhập văn bản để xử lý');
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
        displayResults(data);

    } catch (error) {
        hideLoading();
        console.error('Error:', error);
        showError(`Lỗi xử lý: ${error.message}`);
    }
}

/* ============================================================
   Display results
   ============================================================ */
function displayResults(data) {
    const resultSection  = document.getElementById('resultSection');

    // --- Highlighted tokens ---
    renderHighlightedTokens(data.token_entities || []);

    // --- Anonymized text ---
    document.getElementById('anonymizedText').textContent = data.anonymized_text;

    // --- Entities table ---
    renderEntitiesTable(data.entities || []);

    // --- Show section ---
    resultSection.classList.remove('hidden');
}

/* ---- Highlighted inline tokens ---- */
function renderHighlightedTokens(tokenEntities) {
    const container = document.getElementById('highlightedText');
    const legend    = document.getElementById('entityLegend');
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
            span.innerHTML = escapeHtml(item.token) +
                `<span class="entity-label">${escapeHtml(item.label)}</span>`;
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

/* ---- Entities table ---- */
function renderEntitiesTable(entities) {
    const tbody = document.getElementById('entitiesBody');
    tbody.innerHTML = '';

    if (!entities.length) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="4" style="text-align:center;color:var(--text-muted);padding:24px;">
            Không phát hiện thông tin cá nhân</td>`;
        tbody.appendChild(row);
        return;
    }

    entities.forEach(entity => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="entity-badge entity-badge-${escapeHtml(entity.type)}">${escapeHtml(entity.type)}</span></td>
            <td>${escapeHtml(entity.text)}</td>
            <td>${entity.start}</td>
            <td>${entity.end}</td>
        `;
        tbody.appendChild(row);
    });
}

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
    clearError();
}

/* ---- Copy to clipboard ---- */
function copyToClipboard() {
    const text = document.getElementById('anonymizedText').textContent;
    if (!text) {
        showError('Không có văn bản để sao chép');
        return;
    }

    navigator.clipboard.writeText(text)
        .then(() => {
            const btn = document.getElementById('copyBtn');
            const orig = btn.innerHTML;
            btn.innerHTML = '<span class="btn-icon">✅</span> Đã sao chép!';
            setTimeout(() => { btn.innerHTML = orig; }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy:', err);
            showError('Không thể sao chép văn bản');
        });
}

/* ---- HTML escaping ---- */
function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

/* ============================================================
   Keyboard shortcut: Ctrl+Enter to process
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('inputText').addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            processText();
        }
    });
});
