// DOM Cache for global elements to avoid redundant queries in click handlers
const domCache = {
    galleryOverlay: () => document.querySelector("[data-gallery-overlay]"),
    specsOverlay: () => document.querySelector(".item-details-dialog"),
    searchOverlay: () => document.querySelector(".luxury-search-overlay"),
    filterSidebar: () => document.querySelector(".luxury-filter-sidebar"),
};

function handleGlobalClicks(e) {
    const target = e.target;
    
    // Quick exit for irrelevant clicks
    if (target === document || target === document.body) return;

    // Mode Toggle
    const modeToggle = target.closest('.mode-toggle');
    if (modeToggle) {
        handleModeToggle();
        return;
    }

    // Gallery Actions
    const openGalleryBtn = target.closest("[data-gallery-open]");
    if (openGalleryBtn) {
        initGallery(e);
        return;
    }

    const galleryClose = target.closest("[data-gallery-close]");
    if (galleryClose) {
        const overlay = domCache.galleryOverlay();
        if (overlay) overlay.hidden = true;
        return;
    }

    const imageControl = target.closest(".item-gallery__nav");
    if (imageControl) {
        handleImageControls(imageControl);
        return;
    }

    // Specification Overlay
    const fullSpecsBtn = target.closest(".item-details-dialog__action");
    if (fullSpecsBtn) {
        const overlay = domCache.specsOverlay();
        if (overlay) overlay.classList.toggle('is-open');
        return;
    }

    const specsOverlay = domCache.specsOverlay();
    const closeFullSpecs = target.closest(".item-details-dialog__close") || target.closest(".item-details-dialog__overlay");
    if (closeFullSpecs || target === specsOverlay) {
        closeOverlay();
        return;
    }

    // Interactions
    const saveBtn = target.closest(".save-btn");
    if (saveBtn) {
        if (!ensureAuthenticated(e, saveBtn, generalMsg + 'save')) return;
        const item = saveBtn.closest("[data-id]");
        submitUserInteraction(item, 'save', saveBtn);
        return;
    }

    const itemBuyBtn = target.closest(".item-buy-link");
    if (itemBuyBtn) {
        e.preventDefault();
        handleAffiliateClick(itemBuyBtn);
        return;
    }

    // Alerts
    const messagesCloseBtn = target.closest('.alert-close');
    if (messagesCloseBtn) {
        closeFlashMsg(messagesCloseBtn);
        return;
    }

    // Search Overlay
    const searchToggleBtn = target.closest('.search-toggle');
    if (searchToggleBtn) {
        const overlay = domCache.searchOverlay();
        if (overlay) overlay.classList.add('active');
        return;
    }

    const closeSearchBtn = target.closest('.search-overlay-close') || target.closest('.search-overlay-backdrop');
    if (closeSearchBtn) {
        const overlay = domCache.searchOverlay();
        if (overlay) overlay.classList.remove('active');
        return;
    }

    // Filter Sidebar
    const openFilterBtn = target.closest('.mobile-filter-open');
    if (openFilterBtn) {
        const sidebar = domCache.filterSidebar();
        if (sidebar) sidebar.classList.add('is-open');
        return;
    }

    const closeFilterBtn = target.closest('.mobile-filter-close');
    if (closeFilterBtn) {
        const sidebar = domCache.filterSidebar();
        if (sidebar) sidebar.classList.remove('is-open');
        return;
    }

    // Dropdowns (Combined for performance)
    const dropdownTrigger = target.closest(".dropdown-trigger");
    const dropdown = target.closest(".dropdown");
    
    if (dropdownTrigger) {
        const parentDropdown = dropdownTrigger.closest(".dropdown");
        document.querySelectorAll(".dropdown.is-active").forEach(el => {
            if (el !== parentDropdown) el.classList.remove("is-active");
        });
        if (parentDropdown) parentDropdown.classList.toggle("is-active");
        return;
    } else if (!dropdown) {
        // Close all when clicking outside
        const activeDropdowns = document.querySelectorAll(".dropdown.is-active");
        if (activeDropdowns.length > 0) {
            activeDropdowns.forEach(el => el.classList.remove("is-active"));
        }
    }

    // Accordion
    const accordionTrigger = target.closest(".accordion-trigger");
    if (accordionTrigger) {
        const item = accordionTrigger.closest(".accordion-item");
        const content = item.querySelector(".accordion-content");

        if (item.classList.contains("is-active")) {
            item.classList.remove("is-active");
            content.style.maxHeight = null;
        } else {
            const parent = item.closest(".accordion");
            if (parent) {
                parent.querySelectorAll(".accordion-item.is-active").forEach(sibling => {
                    sibling.classList.remove("is-active");
                    sibling.querySelector(".accordion-content").style.maxHeight = null;
                });
            }
            item.classList.add("is-active");
            content.style.maxHeight = content.scrollHeight + "px";
        }
        return;
    }
}


function handleGlobalSubmits(e) {
    const subscribeForm = e.target.closest("[data-newsletter-form]");
    if (subscribeForm) {
        const btn = e.submitter;
        e.preventDefault();
        handleSubscribing(subscribeForm, btn);
        return;
    }

    const contactForm = e.target.closest(".contact-form");
    if (contactForm) {
        e.preventDefault();
        handleUserMessages(contactForm);
        return;
    }

    const searchForm = e.target.closest(".header-search__form");
    if (searchForm) {
        e.preventDefault();
        handleSearch(searchForm);
        return;
    }
}

function handleGlobalChanges(e) {
    const filterForm = e.target.closest('#luxury-filter-form');
    if (filterForm) {
        filterForm.submit();
    }
}

document.addEventListener('click', handleGlobalClicks);
document.addEventListener('submit', handleGlobalSubmits);
document.addEventListener('change', handleGlobalChanges);
