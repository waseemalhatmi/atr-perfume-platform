function handleGlobalClicks(e) {
    const modeToggle = e.target.closest('.mode-toggle');
    if (modeToggle) {
        handleModeToggle();
        return;
    }

    // ---------- Gallery open / close / arrow clicks ----------
    const galleryOverlay = document.querySelector("[data-gallery-overlay]");

    const openGalleryBtn = e.target.closest("[data-gallery-open]");
    if (openGalleryBtn) {
        initGallery(e);
        return;
    }

    const galleryClose = e.target.closest("[data-gallery-close]");
    if (galleryClose) {
        if (galleryOverlay) galleryOverlay.hidden = true;
        return;
    }

    const imageControl = e.target.closest(".item-gallery__nav");
    if (imageControl) {
        handleImageControls(imageControl);
        return;
    }

    const fullSpecsBtn = e.target.closest(".item-details-dialog__action");
    if (fullSpecsBtn) {
        const overlay = document.querySelector(".item-details-dialog");
        overlay.classList.toggle('is-open');
        return;
    }

    const fullSpecsOverlay = document.querySelector(".item-details-dialog");
    const closeFullSpecs = e.target.closest(".item-details-dialog__close") || e.target.closest(".item-details-dialog__overlay");
    if (closeFullSpecs || e.target == fullSpecsOverlay) {
        closeOverlay();
        return;
    }

    const saveBtn = e.target.closest(".save-btn");
    if (saveBtn) {
        if (!ensureAuthenticated(e, saveBtn, generalMsg + 'save')) return;

        const item = saveBtn.closest("[data-id]");

        submitUserInteraction(
            item,
            'save',
            saveBtn
        );
        return;
    }

    const itemBuyBtn = e.target.closest(".item-buy-link");
    if (itemBuyBtn) {
        e.preventDefault();
        handleAffiliateClick(itemBuyBtn);
        return;
    }

    const messagesCloseBtn = e.target.closest('.alert-close');
    if (messagesCloseBtn) {
        closeFlashMsg(messagesCloseBtn);
        return;
    }

    const searchToggleBtn = e.target.closest('.search-toggle');
    if (searchToggleBtn) {
        const siteHeader = searchToggleBtn.closest('.site-header');
        const overlay = document.querySelector('.luxury-search-overlay');
        if (overlay) overlay.classList.add('active');
        return;
    }

    const closeSearchBtn = e.target.closest('.search-overlay-close') || e.target.closest('.search-overlay-backdrop');
    if (closeSearchBtn) {
        const overlay = document.querySelector('.luxury-search-overlay');
        if (overlay) overlay.classList.remove('active');
        return;
    }

    const openFilterBtn = e.target.closest('.mobile-filter-open');
    if (openFilterBtn) {
        const sidebar = document.querySelector('.luxury-filter-sidebar');
        if (sidebar) sidebar.classList.add('is-open');
        return;
    }

    const closeFilterBtn = e.target.closest('.mobile-filter-close');
    if (closeFilterBtn) {
        const sidebar = document.querySelector('.luxury-filter-sidebar');
        if (sidebar) sidebar.classList.remove('is-open');
        return;
    }

    const user = e.target.closest(".nav-user");
    if (user) {
        document.querySelectorAll(".nav-user")
            .forEach(el => {
                if (el !== user) el.classList.remove("active");
            });

        if (user) {
            user.classList.toggle("active");
        }
    }

    // New Atoms: Dropdown
    const dropdownTrigger = e.target.closest(".dropdown-trigger");
    if (dropdownTrigger) {
        const dropdown = dropdownTrigger.closest(".dropdown");
        
        document.querySelectorAll(".dropdown.is-active").forEach(el => {
            if (el !== dropdown) el.classList.remove("is-active");
        });
        
        if (dropdown) dropdown.classList.toggle("is-active");
        return;
    } else {
        // Close dropdowns if clicking outside
        if (!e.target.closest(".dropdown")) {
            document.querySelectorAll(".dropdown.is-active").forEach(el => {
                el.classList.remove("is-active");
            });
        }
    }

    // New Atoms: Accordion
    const accordionTrigger = e.target.closest(".accordion-trigger");
    if (accordionTrigger) {
        const item = accordionTrigger.closest(".accordion-item");
        const content = item.querySelector(".accordion-content");

        if (item.classList.contains("is-active")) {
            item.classList.remove("is-active");
            content.style.maxHeight = null;
        } else {
            // Optional: Close siblings
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
