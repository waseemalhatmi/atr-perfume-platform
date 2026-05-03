// luxury-features.js
// Handles Price Alerts and Perfume Quiz interactive features

document.addEventListener('DOMContentLoaded', () => {
  const csrfToken = window.APP?.csrfToken || "";

  // ================= PRICE ALERTS =================
  const priceAlertTriggers = document.querySelectorAll('.price-alert-trigger');
  const alertModal = document.getElementById('price-alert-modal');
  const alertCloseBtn = alertModal ? alertModal.querySelector('.alert-close-btn') : null;
  const alertBackdrop = alertModal ? alertModal.querySelector('.alert-backdrop') : null;
  const priceAlertForm = document.getElementById('price-alert-form');
  const priceAlertItemId = document.getElementById('price-alert-item-id');

  if (priceAlertTriggers && alertModal) {
    priceAlertTriggers.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const itemId = btn.getAttribute('data-item-id');
        if (priceAlertItemId) priceAlertItemId.value = itemId;
        
        alertModal.classList.add('active');
      });
    });
  }

  const closeAlertModal = () => { if (alertModal) alertModal.classList.remove('active'); };
  if (alertCloseBtn) alertCloseBtn.addEventListener('click', closeAlertModal);
  if (alertBackdrop) alertBackdrop.addEventListener('click', closeAlertModal);

  if (priceAlertForm) {
    priceAlertForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(priceAlertForm);
      const data = Object.fromEntries(formData.entries());
      
      const btn = priceAlertForm.querySelector('button[type="submit"]');
      const originText = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التسجيل...';

      try {
        const res = await fetch('/alerts/subscribe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify(data)
        });
        
        const result = await res.json();
        
        if (result.success) {
          btn.innerHTML = '<i class="fas fa-check"></i> ' + result.message;
          btn.style.background = 'var(--gold-primary)';
          setTimeout(() => {
            closeAlertModal();
            btn.innerHTML = originText;
            priceAlertForm.reset();
          }, 2000);
        } else {
          alert('خطأ: ' + result.error);
          btn.innerHTML = originText;
        }
      } catch (err) {
        alert('حدث خطأ بالاتصال بالمزود');
        btn.innerHTML = originText;
      }
    });
  }

  // ================= PERFUME QUIZ =================
  const quizOpenBtns = document.querySelectorAll('.quiz-open-btn');
  const quizModal = document.getElementById('perfume-quiz-modal');
  const quizCloseBtn = quizModal ? quizModal.querySelector('.quiz-close') : null;
  const quizBackdrop = quizModal ? quizModal.querySelector('.quiz-backdrop') : null;

  if (quizOpenBtns && quizModal) {
    quizOpenBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        quizModal.classList.add('active');
        resetQuiz();
      });
    });
  }

  const closeQuizModal = () => { if (quizModal) quizModal.classList.remove('active'); };
  if (quizCloseBtn) quizCloseBtn.addEventListener('click', closeQuizModal);
  if (quizBackdrop) quizBackdrop.addEventListener('click', closeQuizModal);

  let quizAnswers = {};
  const TOTAL_STEPS = 5;
  
  function resetQuiz() {
    quizAnswers = {};
    if (!quizModal) return;
    const steps = quizModal.querySelectorAll('.quiz-step');
    steps.forEach(s => {
      s.style.display = 'none';
      s.style.opacity = '0';
      s.style.transform = 'translateY(20px)';
    });
    showQuizStep('1');
  }

  function showQuizStep(stepValue) {
    const step = quizModal.querySelector(`.quiz-step[data-step="${stepValue}"]`);
    if (step) {
      step.style.display = 'block';
      setTimeout(() => {
        step.style.transition = 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1), transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
        step.style.opacity = '1';
        step.style.transform = 'translateY(0)';
      }, 50);
    }
  }

  function hideQuizStep(stepValue) {
    const step = quizModal.querySelector(`.quiz-step[data-step="${stepValue}"]`);
    if (step) {
      step.style.opacity = '0';
      step.style.transform = 'translateY(-20px)';
      setTimeout(() => {
        step.style.display = 'none';
      }, 300);
    }
  }

  // Listen for option clicks
  if (quizModal) {
    const quizOptions = quizModal.querySelectorAll('.quiz-option');
    quizOptions.forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const answer = btn.getAttribute('data-answer');
        const key = btn.getAttribute('data-key');
        const currentStepEl = btn.closest('.quiz-step');
        const currentStep = parseInt(currentStepEl.getAttribute('data-step'));
        
        // Visual feedback
        btn.classList.add('active');
        
        // Store answer
        quizAnswers[key] = answer;
        
        setTimeout(async () => {
          hideQuizStep(currentStep.toString());
          
          if (currentStep < TOTAL_STEPS) {
            setTimeout(() => showQuizStep((currentStep + 1).toString()), 350);
          } else {
            // Quiz finished! Show loader
            setTimeout(() => showQuizStep('loading'), 350);
            await fetchQuizRecommendations();
          }
        }, 400); // Short delay for selection feedback
      });
    });
  }

  async function fetchQuizRecommendations() {
    try {
      const res = await fetch('/quiz/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(quizAnswers)
      });
      const data = await res.json();
      
      if (data.success) {
        setTimeout(() => {
          hideQuizStep('loading');
          const resultsBox = quizModal.querySelector('.quiz-results-box');
          resultsBox.innerHTML = data.html;
          setTimeout(() => showQuizStep('results'), 400);
        }, 2000); // Artificial delay for premium expert feel
      }
    } catch(err) {
      console.error("Quiz Error", err);
      closeQuizModal();
    }
  }

  // ================= NOTIFICATIONS =================
  const notifToggle = document.querySelector('.notifications-toggle');
  const notifDropdown = document.querySelector('.notifications-dropdown');
  const notifList = document.getElementById('notifications-list');
  const notifBadge = document.getElementById('notification-count');
  const markAllReadBtn = document.getElementById('mark-all-read');

  if (notifToggle && window.APP.isAuthenticated) {
    notifToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      notifDropdown.classList.toggle('active');
      if (notifDropdown.classList.contains('active')) {
        fetchNotifications();
      }
    });

    document.addEventListener('click', () => {
        if (notifDropdown) notifDropdown.classList.remove('active');
    });

    notifDropdown.addEventListener('click', (e) => e.stopPropagation());

    // Efficient Event Delegation for dynamic notification items
    notifList.addEventListener('click', async (e) => {
      const item = e.target.closest('.notification-item');
      if (item && !item.classList.contains('read-loading')) {
        const id = item.getAttribute('data-id');
        item.classList.add('read-loading'); // Prevent double click
        try {
          await fetch(`/api/notifications/mark-read/${id}`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken }
          });
          item.classList.remove('unread');
        } catch (err) {
          item.classList.remove('read-loading');
        }
      }
    });

    async function fetchNotifications() {
      if (document.hidden) return; // Smart pause when tab is inactive
      
      try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        
        // Update badge efficiently
        if (data.unread_count > 0) {
          notifBadge.textContent = data.unread_count;
          notifBadge.style.display = 'flex';
        } else {
          notifBadge.style.display = 'none';
        }

        // Render list only if changed or open
        if (data.notifications.length > 0) {
          notifList.innerHTML = data.notifications.map(n => `
            <a href="${n.link || '#'}" class="notification-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
              <div class="notification-item__title">${n.title}</div>
              <div class="notification-item__msg">${n.message}</div>
              <span class="notification-item__date">${n.created_at}</span>
            </a>
          `).join('');
        } else {
          notifList.innerHTML = '<div class="notifications-empty">ليس لديك إشعارات جديدة</div>';
        }
      } catch (err) {
        console.error("Notif Error", err);
      }
    }

    // Initial check
    fetchNotifications();
    
    // Use setTimeout instead of setInterval to prevent overlapping calls if network is slow
    const startPolling = () => {
      setTimeout(async () => {
        await fetchNotifications();
        startPolling();
      }, 60000);
    };
    startPolling();
  }

  // ================= PRICE CHART =================
  const priceCanvas = document.getElementById('priceChart');
  if (priceCanvas) {
    const itemId = priceCanvas.getAttribute('data-item-id');
    
    async function initPriceChart() {
      try {
        const res = await fetch(`/api/items/${itemId}/price-history`);
        const historyData = await res.json();
        
        if (historyData.length === 0) {
           priceCanvas.parentElement.innerHTML = '<div class="flex items-center justify-center h-full text-muted">سيظهر مخطط الأسعار هنا بمجرد توفر بيانات كافية (3 أيام على الأقل)</div>';
           return;
        }

        const labels = historyData.map(h => h.date);
        const prices = historyData.map(h => h.price);

        new Chart(priceCanvas, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: 'السعر',
              data: prices,
              borderColor: '#d4af37',
              backgroundColor: 'rgba(212, 175, 55, 0.1)',
              borderWidth: 3,
              tension: 0.4,
              fill: true,
              pointBackgroundColor: '#d4af37',
              pointRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: {
                beginAtZero: false,
                grid: { color: 'rgba(255,255,255,0.05)' }
              },
              x: {
                grid: { display: false }
              }
            }
          }
        });
      } catch (err) {
        console.error("Chart Error", err);
      }
    }

    initPriceChart();
  }

});
