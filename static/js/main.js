/**
 * Smart Parking System - Main JavaScript
 * Handles: auto-dismiss alerts, animations, and UI interactions
 */

// ── Auto-dismiss flash messages after 4 seconds ──────────────
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(function () { alert.remove(); }, 500);
    }, 4000);
  });

  // ── Highlight active nav link ──────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ── Animate stat cards on load ─────────────────────────────
  const cards = document.querySelectorAll('.stat-card, .glass-card');
  cards.forEach(function (card, index) {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    setTimeout(function () {
      card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, index * 60);
  });
});
