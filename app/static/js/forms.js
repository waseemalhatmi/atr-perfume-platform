async function handleSearch(form) {
    const formData = new FormData(form);
    const query = (formData.get('query') || '').trim();

    if (query === '') return;

    // Redirect to GET search page for shareable URLs
    window.location.href = `/search?q=${encodeURIComponent(query)}`;
}

async function handleCommentPosting(form, formType) {
    
    if (formType === 'reply') {
        const parentComment = form.closest('.comment');
        const commentAuthor = parentComment.querySelector('.comment__author').textContent;
        
        if (commentAuthor === userEmail) {
            showInlineTooltip(form, "You can't reply on your own comment");
            return;
        }
    }
    const wrapper = form.classList.contains("comment__reply-form")
        ? form.closest(".comment__replies")
        : form.closest(".comments");
        
        const textarea = form.querySelector("textarea");
        const content = textarea.value.trim();
        if (!content) {
            showInlineTooltip(form, "You can't post an empty comment");
            return;
        }

    const item = wrapper.closest("[data-id]");

    submitUserInteraction(item,
                        'comment',
                        null,
                        content,
                        { wrapper, textarea, form, formType }
    );
}


async function handleSubscribing(form, btn) {
    if (btn) btn.classList.add('is-loading');
    
    try {
        const fd = new FormData(form);
        if (btn && btn.name) {
            fd.append(btn.name, btn.value);
        }

        const response = await fetch(form.action, {
            method: "POST",
            body: fd,
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });

        const data = await response.json();
        
        showInlineTooltip(
            btn || form,
            data.success ? data.message : data.error,
            2500
        );

        if (data.success) {
            document.querySelector("[data-newsletter]").innerHTML = data.html;
        }
    } catch (e) {
        console.error("Subscription failed:", e);
    } finally {
        if (btn) btn.classList.remove('is-loading');
    }
}

async function handleUserMessages(form) {
    const btn = form.querySelector('button[type="submit"]');
    if (btn) btn.classList.add('is-loading');

    try {
        const formData = new FormData(form);

        const res = await fetch("/contact", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        if (data.success) form.reset();
        showInlineTooltip(
            btn || form,
            data.success ? data.message : data.error
        );
    } catch (e) {
        console.error("Message submission failed:", e);
    } finally {
        if (btn) btn.classList.remove('is-loading');
    }
}
