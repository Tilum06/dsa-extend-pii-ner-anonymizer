/**
 * PII Detection Web Demo - Frontend Script
 * Handles user interactions and API communication
 */

/**
 * Process text by sending it to the backend API
 */
async function processText() {
    const inputText = document.getElementById('inputText').value.trim();

    // Validate input
    if (!inputText) {
        showError('Vui lòng nhập văn bản để xử lý');
        return;
    }

    // Clear previous errors
    clearError();

    // Show loading spinner
    showLoading();

    try {
        // Send request to backend API
        const response = await fetch('/api/detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: inputText })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Hide loading spinner
        hideLoading();

        // Display results
        displayResults(data);

    } catch (error) {
        hideLoading();
        console.error('Error:', error);
        showError(`Lỗi xử lý: ${error.message}`);
    }
}

/**
 * Display results on the page
 * @param {Object} data - Response data from API
 */
function displayResults(data) {
    const resultSection = document.getElementById('resultSection');
    const anonymizedTextDiv = document.getElementById('anonymizedText');
    const entitiesBody = document.getElementById('entitiesBody');

    // Display anonymized text
    anonymizedTextDiv.textContent = data.anonymized_text;

    // Clear previous table rows
    entitiesBody.innerHTML = '';

    // Check if entities were detected
    if (data.entities && data.entities.length > 0) {
        // Populate entities table
        data.entities.forEach((entity, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="entity-type">${escapeHtml(entity.type)}</span></td>
                <td>${escapeHtml(entity.text)}</td>
                <td>${entity.start}</td>
                <td>${entity.end}</td>
            `;
            entitiesBody.appendChild(row);
        });
    } else {
        // Show message if no entities detected
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" style="text-align: center; color: #999;">Không phát hiện thông tin cá nhân</td>';
        entitiesBody.appendChild(row);
    }

    // Show result section
    resultSection.classList.remove('hidden');
}

/**
 * Show loading spinner
 */
function showLoading() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const processBtn = document.getElementById('processBtn');
    loadingSpinner.classList.remove('hidden');
    processBtn.disabled = true;
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const processBtn = document.getElementById('processBtn');
    loadingSpinner.classList.add('hidden');
    processBtn.disabled = false;
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    const errorSection = document.getElementById('errorSection');
    const errorText = document.getElementById('errorText');
    errorText.textContent = message;
    errorSection.classList.remove('hidden');
}

/**
 * Clear error message
 */
function clearError() {
    const errorSection = document.getElementById('errorSection');
    errorSection.classList.add('hidden');
}

/**
 * Clear all input and results
 */
function clearAll() {
    document.getElementById('inputText').value = '';
    document.getElementById('resultSection').classList.add('hidden');
    clearError();
}

/**
 * Copy anonymized text to clipboard
 */
function copyToClipboard() {
    const anonymizedText = document.getElementById('anonymizedText').textContent;
    
    // Check if text is empty
    if (!anonymizedText) {
        showError('Không có văn bản để sao chép');
        return;
    }

    // Copy to clipboard
    navigator.clipboard.writeText(anonymizedText)
        .then(() => {
            // Show success message
            const copyBtn = document.getElementById('copyBtn');
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '✓ Đã sao chép!';
            copyBtn.style.background = '#4caf50';

            // Reset button text after 2 seconds
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.style.background = '';
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy:', err);
            showError('Không thể sao chép văn bản');
        });
}

/**
 * Escape HTML special characters
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Handle Enter key in textarea
 */
document.addEventListener('DOMContentLoaded', function() {
    const inputText = document.getElementById('inputText');
    inputText.addEventListener('keydown', function(e) {
        // Ctrl+Enter or Cmd+Enter to process
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            processText();
        }
    });
});
