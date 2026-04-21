async function initAllSaves() {
    const buttons = Array.from(document.querySelectorAll(".save-btn"));
    const targets = [];
    
    buttons.forEach(btn => {
        const item = btn.closest("[data-id]");
        targets.push({ ...item.dataset });
    });
    if (targets.length === 0) return;
    
    const params = new URLSearchParams();
    for (const t of targets) {
        params.append("type", t.type);
        params.append("id", t.id);
    }

    const res = await fetch(`/check-save-batch?${params.toString()}`);
    if (!res.ok) return;

    const data = await res.json();

    buttons.forEach(btn => {
        const item = btn.closest("[data-id]");
        const key = `${item.dataset.type}:${item.dataset.id}`;
        
        btn.classList.toggle('active', key in data);
        
    });
}

async function submitUserInteraction(
    targetItem,
    interactionType,
    targetBtn = null
) {
    const targetType = targetItem.dataset.type;
    const targetId = targetItem.dataset.id;
    
    const fd = new FormData();
    
    fd.append("type", targetType);
    fd.append("id", targetId);
    fd.append("interaction_type", interactionType);

    if (targetBtn) targetBtn.classList.add('is-loading');

    try {
        const res = await fetch("/handle-interaction", {
            method: "POST",
            body: fd
        });

        const result = await res.json();
        
        if (!res.ok) {
            showInlineTooltip(
                targetBtn,
                result.error || "Something went wrong"
            );
            return;
        }
        if (interactionType === 'save') {
            targetBtn.classList.toggle('active', result.status == 'saved')
        }
    } catch (e) {
        console.error("Interaction failed:", e);
    } finally {
        if (targetBtn) targetBtn.classList.remove('is-loading');
    }
}