document.addEventListener("DOMContentLoaded", () => {
    initApp();
    initUserInteractions();
    // NOTE: Global event listeners (click, submit, change) are registered in main.js
    // Do NOT duplicate them here
});

window.addEventListener("pageshow", initUserInteractions);

document.addEventListener("change", handleCountryToggle);


function initApp() {
    initTheme();
    handleFlashMessages();
}

// Run on page load and when coming back via back/forward buttons
function initUserInteractions() {
    if (isAuthenticated) {
        initAllSaves();
    }
}

const generalMsg = 'please sign in to ';
const csrfToken = window.APP?.csrfToken || "";

function handleFlashMessages() {
    // ------------------------------
    // Global messages (top-right)
    // ------------------------------
    const globalMessages = document.querySelectorAll('.flash-messages .alert');
    globalMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100%)';
            setTimeout(() => msg.remove(), 500);
        }, 2500);
    });
}

// ------------------------------
// Manual close for global messages
// ------------------------------
function closeFlashMsg(btn) {
    const alert = btn.parentElement;
    alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    alert.style.opacity = '0';
    alert.style.transform = 'translateX(100%)';
    setTimeout(() => alert.remove(), 300);
}


async function handleCountryToggle(e) {
    if (!e.target.classList.contains("country-toggle")) return;
    
    const country = e.target.value || "";
    
    await fetch("/set-country", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ country })
    });
    
    // Optional: reload page to apply country filtering
    window.location.reload();
    
}
