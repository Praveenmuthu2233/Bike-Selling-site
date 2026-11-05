/**
 * SMR Motors - Global Theme Management Engine
 * ============================================
 * - Default Theme: LIGHT MODE for all first-time visitors
 * - Storage Key: 'smr_theme' ('light' | 'dark')
 * - Instant execution to prevent Theme Flash / FOUC
 * - Synchronizes UI icons (☀️ for Light Mode / 🌙 for Dark Mode)
 * - Accessible tooltips and aria-labels
 * - Dispatches 'smr-theme-changed' custom event
 */

(function () {
  const STORAGE_KEY = 'smr_theme';

  function getSavedTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'dark' || saved === 'light') {
        return saved;
      }
      return 'light'; // Default is ALWAYS light mode
    } catch (e) {
      return 'light';
    }
  }

  function applyTheme(theme, persist) {
    if (persist === undefined) persist = true;
    const validTheme = theme === 'dark' ? 'dark' : 'light';
    
    // Apply data-theme attribute on root <html> element
    document.documentElement.setAttribute('data-theme', validTheme);
    
    if (persist) {
      try {
        localStorage.setItem(STORAGE_KEY, validTheme);
      } catch (e) {
        // Storage access might be restricted
      }
    }

    // Update all theme toggle buttons across the page
    updateToggleButtons(validTheme);

    // Notify listeners (charts, graphs, embedded widgets)
    try {
      window.dispatchEvent(new CustomEvent('smr-theme-changed', {
        detail: { theme: validTheme }
      }));
    } catch (e) {}

    return validTheme;
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || getSavedTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    return applyTheme(next, true);
  }

  function updateToggleButtons(theme) {
    const isDark = theme === 'dark';
    const tooltipText = isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode';

    document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
      btn.setAttribute('aria-label', tooltipText);
      btn.setAttribute('title', tooltipText);

      // Icon update
      const icon = btn.querySelector('i');
      if (icon) {
        if (isDark) {
          icon.className = 'fas fa-sun';
          icon.style.color = '#F59E0B'; // Warm Sun Yellow
        } else {
          icon.className = 'fas fa-moon';
          icon.style.color = '#64748B'; // Cool Moon Slate
        }
      }

      // Optional text update if button has label
      const textLabel = btn.querySelector('.theme-toggle-label');
      if (textLabel) {
        textLabel.textContent = isDark ? 'Light' : 'Dark';
      }
    });
  }

  // 1. Immediate Execution (Runs as soon as script is encountered in <head>)
  const initialTheme = getSavedTheme();
  document.documentElement.setAttribute('data-theme', initialTheme);

  // 2. DOM Ready Hook to sync toggle buttons
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      updateToggleButtons(document.documentElement.getAttribute('data-theme') || initialTheme);
    });
  } else {
    updateToggleButtons(initialTheme);
  }

  // 3. Expose Public Global API on window.SMRTheme
  window.SMRTheme = {
    get: getSavedTheme,
    set: function (t) { return applyTheme(t, true); },
    toggle: toggleTheme,
    apply: applyTheme,
    refreshUI: function () {
      updateToggleButtons(document.documentElement.getAttribute('data-theme') || getSavedTheme());
    }
  };
})();
