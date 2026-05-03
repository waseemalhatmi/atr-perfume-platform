/**
 * app/static/js/admin_ux.js
 * Centralized Administrative UI Logic
 */

/**
 * Tab switching logic for admin forms
 * @param {string} tabId - ID of the tab to show (without 'tab-' prefix)
 * @param {Event} evt - The click event
 */
function showTab(tabId, evt) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(t => {
        t.style.display = 'none';
        t.classList.remove('active');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.form-tab').forEach(b => {
        b.classList.remove('active');
    });

    // Show selected tab content
    const targetTab = document.getElementById('tab-' + tabId);
    if (targetTab) {
        targetTab.style.display = 'block';
        targetTab.classList.add('active');
    }

    // Set clicked button as active
    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add('active');
    }
}

/**
 * Image preview logic for file inputs
 * @param {HTMLInputElement} input - The file input element
 * @param {string} previewId - ID of the container element for preview
 */
function previewImage(input, previewId = 'image-preview') {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById(previewId);
            if (preview) {
                preview.innerHTML = `<img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: contain;">`;
            }
        }
        reader.readAsDataURL(input.files[0]);
    }
}

/**
 * Modal System Logic
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);
}

function closeModal(modalId) {
    const modal = typeof modalId === 'string' ? document.getElementById(modalId) : modalId;
    if (!modal) return;
    modal.classList.remove('active');
    setTimeout(() => modal.style.display = 'none', 300);
}

/**
 * Message Preview Logic (Specific to messages.html but using shared modal)
 */
function showMsg(id, subject, sender) {
    const content = document.getElementById('msg-content-' + id).innerText;
    const modalSubject = document.getElementById('modal-subject');
    const modalSender = document.getElementById('modal-sender');
    const modalBody = document.getElementById('modal-body');

    if (modalSubject) modalSubject.innerText = subject;
    if (modalSender) modalSender.innerText = 'رسالة من: ' + sender;
    if (modalBody) modalBody.innerText = content;
    
    openModal('msg-modal');
}

/**
 * Global Admin UI Initializations
 */
document.addEventListener('DOMContentLoaded', () => {
    // Toast notification auto-dismiss
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 500);
        }, 5000);
    });

    // Add click listeners for closing toasts and modals
    document.addEventListener('click', (e) => {
        const closeBtn = e.target.closest('.toast-close');
        if (closeBtn) {
            const toast = closeBtn.closest('.toast');
            if (toast) {
                toast.classList.add('hiding');
                setTimeout(() => toast.remove(), 500);
            }
        }

        // Modal backdrop click
        if (e.target.classList.contains('modal-overlay')) {
            closeModal(e.target);
        }
    });

    // Escape key modal close
    window.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal-overlay.active');
            if (activeModal) closeModal(activeModal);
        }
    });
});
