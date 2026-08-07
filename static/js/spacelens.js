/* ============================================================
   SpaceLens AI — Client-side Logic
   ============================================================ */

"use strict";

/* ── Image upload preview ────────────────────────────────── */
(function initUploadZone() {
  const zone  = document.getElementById('uploadZone');
  const input = document.getElementById('id_image');
  const preview = document.getElementById('imagePreview');
  const previewWrap = document.getElementById('previewWrap');

  if (!zone || !input) return;

  // Click the hidden file input
  zone.addEventListener('click', () => input.click());

  // Drag & drop visual feedback
  ['dragenter', 'dragover'].forEach(evt =>
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.add('dragover'); })
  );
  ['dragleave', 'drop'].forEach(evt =>
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.remove('dragover'); })
  );

  zone.addEventListener('drop', e => {
    const file = e.dataTransfer.files[0];
    if (file) {
      // Transfer to file input via DataTransfer
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      showPreview(file);
    }
  });

  input.addEventListener('change', () => {
    if (input.files[0]) showPreview(input.files[0]);
  });

  function showPreview(file) {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = e => {
      if (preview) {
        preview.src = e.target.result;
        if (previewWrap) previewWrap.classList.remove('d-none');
      }
    };
    reader.readAsDataURL(file);
    // Update zone text
    const title = zone.querySelector('.upload-title');
    if (title) title.textContent = file.name;
  }
})();

/* ── Prediction form — loading overlay ───────────────────── */
(function initPredictForm() {
  const form    = document.getElementById('predictForm');
  const overlay = document.getElementById('loadingOverlay');

  if (!form) return;

  form.addEventListener('submit', function () {
    if (overlay) overlay.classList.remove('d-none');
    const btn = form.querySelector('[type=submit]');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="sl-spinner me-2"></span>Analysing…';
    }
  });
})();

/* ── Auto-dismiss alerts ─────────────────────────────────── */
(function autoDismissAlerts() {
  document.querySelectorAll('.sl-alert[data-auto-dismiss]').forEach(el => {
    const delay = parseInt(el.dataset.autoDismiss, 10) || 5000;
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, delay);
  });
})();

/* ── Probability chart (Chart.js) ────────────────────────── */
function renderProbabilityChart(canvasId, labels, values) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || typeof Chart === 'undefined') return;

  const maxVal = Math.max(...values);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Confidence (%)',
        data: values,
        backgroundColor: values.map(v =>
          v === maxVal
            ? 'rgba(56, 189, 248, 0.7)'
            : 'rgba(56, 189, 248, 0.2)'
        ),
        borderColor: values.map(v =>
          v === maxVal ? 'rgba(56, 189, 248, 1)' : 'rgba(56, 189, 248, 0.4)'
        ),
        borderWidth: 1,
        borderRadius: 6,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.x.toFixed(2)} %`
          }
        }
      },
      scales: {
        x: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: {
            color: '#8b98a9',
            font: { family: "'Exo 2', sans-serif", size: 11 },
            callback: v => v + '%'
          }
        },
        y: {
          grid: { display: false },
          ticks: {
            color: '#e2e8f0',
            font: { family: "'Exo 2', sans-serif", size: 12 }
          }
        }
      }
    }
  });
}

/* ── Sidebar active-link highlight ──────────────────────── */
(function markActiveNavLink() {
  const links = document.querySelectorAll('.sl-sidebar .nav-link');
  const path  = window.location.pathname;
  links.forEach(link => {
    if (link.getAttribute('href') && path.startsWith(link.getAttribute('href'))) {
      link.classList.add('active');
    }
  });
})();

/* ── Smooth scroll for anchor links ─────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});
