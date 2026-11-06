import os
import re

def update_components_css():
    path = 'my-node-app/static/components.css'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Brand and gradient replacements
    content = content.replace('#FF6B00', '#2563EB')
    content = content.replace('#E05E00', '#1D4ED8')
    content = content.replace('#ea580c', '#2563EB')
    content = content.replace('#f97316', '#1D4ED8')
    content = content.replace('rgba(255, 107, 0,', 'rgba(37, 99, 235,')
    content = content.replace('rgba(255,107,0,', 'rgba(37, 99, 235,')

    # Button secondary & outline
    content = re.sub(
        r'\.btn-secondary\s*\{[^}]*\}',
        '''.btn-secondary {
  background: #F1F5F9;
  color: #172033;
  border-color: #CBD5E1;
}''',
        content
    )
    content = re.sub(
        r'\.btn-secondary:hover\s*\{[^}]*\}',
        '''.btn-secondary:hover {
  background: #E2E8F0;
  border-color: #94A3B8;
  color: #0F172A;
}''',
        content
    )
    content = re.sub(
        r'\.btn-outline\s*\{[^}]*\}',
        '''.btn-outline {
  background: #FFFFFF;
  color: #172033;
  border-color: #CBD5E1;
}''',
        content
    )
    content = re.sub(
        r'\.btn-outline:hover\s*\{[^}]*\}',
        '''.btn-outline:hover {
  border-color: #2563EB;
  color: #2563EB;
  background: #EFF6FF;
}''',
        content
    )

    # Bike Card
    content = re.sub(
        r'\.bike-card\s*\{[^}]*\}',
        '''.bike-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-normal);
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: var(--shadow-sm);
}''',
        content
    )
    content = re.sub(
        r'\.bike-card:hover\s*\{[^}]*\}',
        '''.bike-card:hover {
  transform: translateY(-5px);
  border-color: #2563EB;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08), 0 0 15px rgba(37, 99, 235, 0.15);
}''',
        content
    )
    content = re.sub(
        r'\.bike-card-img-wrapper\s*\{[^}]*\}',
        '''.bike-card-img-wrapper {
  position: relative;
  width: 100%;
  padding-top: 62%;
  overflow: hidden;
  background: #F1F5F9;
}''',
        content
    )
    content = re.sub(
        r'\.bike-card-title\s*\{[^}]*\}',
        '''.bike-card-title {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: #0F172A;
  line-height: 1.3;
}''',
        content
    )
    content = re.sub(
        r'\.bike-price-value\s*\{[^}]*\}',
        '''.bike-price-value {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 800;
  color: #0F172A;
}''',
        content
    )

    # Card Slider Controls
    content = re.sub(
        r'\.card-slider-arrow\s*\{[^}]*\}',
        '''.card-slider-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid #CBD5E1;
  color: #172033;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 3;
  opacity: 0;
  transition: all 0.22s ease;
  font-size: 0.78rem;
}''',
        content
    )
    content = re.sub(
        r'\.card-slider-dots\s*\{[^}]*\}',
        '''.card-slider-dots {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 5px;
  z-index: 3;
  padding: 4px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(6px);
  border: 1px solid #E2E8F0;
}''',
        content
    )
    content = re.sub(
        r'\.card-slider-dot\s*\{[^}]*\}',
        '''.card-slider-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.25);
  border: none;
  padding: 0;
  cursor: pointer;
  transition: all 0.25s ease;
}''',
        content
    )
    content = re.sub(
        r'\.card-img-counter\s*\{[^}]*\}',
        '''.card-img-counter {
  position: absolute;
  top: 1rem;
  right: 3.5rem;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border: 1px solid #CBD5E1;
  color: #172033;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 3px 8px;
  border-radius: 12px;
  z-index: 2;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 3px;
  pointer-events: none;
}''',
        content
    )
    content = re.sub(
        r'\.bike-fav-btn\s*\{[^}]*\}',
        '''.bike-fav-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid #CBD5E1;
  color: #64748B;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  z-index: 2;
}''',
        content
    )

    # Filters panel
    content = re.sub(
        r'\.filters-panel\s*\{[^}]*\}',
        '''.filters-panel {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 2.5rem;
  box-shadow: var(--shadow-sm);
}''',
        content
    )
    content = re.sub(
        r'\.form-control\s*\{[^}]*\}',
        '''.form-control {
  width: 100%;
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
  color: #172033;
  font-family: var(--font-body);
  transition: all var(--transition-fast);
}''',
        content
    )
    content = re.sub(
        r'\.form-control:focus\s*\{[^}]*\}',
        '''.form-control:focus {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  background: #FFFFFF;
}''',
        content
    )

    # Stats cards
    content = re.sub(
        r'\.stat-card\s*\{[^}]*\}',
        '''.stat-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  transition: all var(--transition-fast);
}''',
        content
    )
    content = re.sub(
        r'\.stat-val\s*\{[^}]*\}',
        '''.stat-val {
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 800;
  color: #0F172A;
  line-height: 1.2;
}''',
        content
    )

    # Tables
    content = re.sub(
        r'\.table-card\s*\{[^}]*\}',
        '''.table-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}''',
        content
    )
    content = re.sub(
        r'\.data-table th\s*\{[^}]*\}',
        '''.data-table th {
  background: #F8FAFC;
  padding: 0.9rem 1.25rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #E2E8F0;
  white-space: nowrap;
}''',
        content
    )
    content = re.sub(
        r'\.data-table td\s*\{[^}]*\}',
        '''.data-table td {
  padding: 1rem 1.25rem;
  font-size: 0.92rem;
  color: #172033;
  border-bottom: 1px solid #E2E8F0;
  vertical-align: middle;
}''',
        content
    )
    content = re.sub(
        r'\.data-table tr:hover td\s*\{[^}]*\}',
        '''.data-table tr:hover td {
  background: #F8FAFC;
}''',
        content
    )

    # Modals
    content = re.sub(
        r'\.modal-dialog\s*\{[^}]*\}',
        '''.modal-dialog {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 580px;
  box-shadow: var(--shadow-lg);
  transform: translateY(20px) scale(0.97);
  transition: all var(--transition-normal);
  overflow: hidden;
  color: #172033;
}''',
        content
    )

    # Toast
    content = re.sub(
        r'\.toast\s*\{[^}]*\}',
        '''.toast {
  pointer-events: auto;
  min-width: 320px;
  max-width: 420px;
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  border-radius: var(--radius-md);
  padding: 0.9rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  color: #172033;
  animation: slideInToast 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}''',
        content
    )

    # Pagination
    content = re.sub(
        r'\.pagination-btn\s*\{[^}]*\}',
        '''.pagination-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  min-width: 38px;
  height: 38px;
  padding: 0 0.85rem;
  font-size: 0.88rem;
  font-weight: 600;
  border-radius: var(--radius-md);
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  color: #475569;
  cursor: pointer;
  transition: all var(--transition-fast);
}''',
        content
    )
    content = re.sub(
        r'\.pagination-btn:hover:not\(:disabled\)\s*\{[^}]*\}',
        '''.pagination-btn:hover:not(:disabled) {
  border-color: #2563EB;
  color: #2563EB;
  background: #EFF6FF;
  transform: translateY(-1px);
}''',
        content
    )
    content = re.sub(
        r'\.pagination-btn\.active\s*\{[^}]*\}',
        '''.pagination-btn.active {
  background: #2563EB;
  border-color: #2563EB;
  color: #FFFFFF;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
}''',
        content
    )

    # Profile dropdown
    content = re.sub(
        r'\.user-profile-trigger\s*\{[^}]*\}',
        '''.user-profile-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.35rem 0.85rem 0.35rem 0.45rem;
  border-radius: 9999px;
  background: #F1F5F9;
  border: 1px solid #CBD5E1;
  color: #172033;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: 600;
  transition: all 0.2s ease;
  user-select: none;
}''',
        content
    )
    content = re.sub(
        r'\.user-profile-dropdown-menu\s*\{[^}]*\}',
        '''.user-profile-dropdown-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 270px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  padding: 0.5rem 0;
  z-index: 1000;
  display: none;
  animation: dropdownFadeScale 0.18s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}''',
        content
    )
    content = re.sub(
        r'\.dropdown-user-header\s*\{[^}]*\}',
        '''.dropdown-user-header {
  padding: 0.85rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-bottom: 1px solid #E2E8F0;
  background: #F8FAFC;
}''',
        content
    )
    content = re.sub(
        r'\.dropdown-user-name\s*\{[^}]*\}',
        '''.dropdown-user-name {
  font-size: 0.92rem;
  font-weight: 700;
  color: #0F172A;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}''',
        content
    )
    content = re.sub(
        r'\.dropdown-item-link\s*\{[^}]*\}',
        '''.dropdown-item-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 1.15rem;
  color: #475569;
  text-decoration: none;
  font-size: 0.86rem;
  font-weight: 600;
  transition: all 0.15s ease;
  cursor: pointer;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
}''',
        content
    )
    content = re.sub(
        r'\.dropdown-item-link:hover\s*\{[^}]*\}',
        '''.dropdown-item-link:hover {
  background: #F1F5F9;
  color: #0F172A;
  padding-left: 1.35rem;
}''',
        content
    )
    content = re.sub(
        r'\.dropdown-divider\s*\{[^}]*\}',
        '''.dropdown-divider {
  height: 1px;
  background: #E2E8F0;
  margin: 0.35rem 0;
}''',
        content
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated:", path)

    # Also update static/css/components.css if present
    legacy = 'my-node-app/static/css/components.css'
    if os.path.exists(legacy):
        with open(legacy, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated legacy:", legacy)

def update_user_css():
    path = 'my-node-app/static/user.css'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('#FF6B00', '#2563EB')
    content = content.replace('#ea580c', '#2563EB')
    content = content.replace('#f97316', '#1D4ED8')
    content = content.replace('rgba(255, 107, 0,', 'rgba(37, 99, 235,')

    content = re.sub(
        r'\.user-sidebar\s*\{[^}]*\}',
        '''.user-sidebar {
  width: 280px;
  background: #FFFFFF;
  border-right: 1px solid #E2E8F0;
  padding: 2rem 1.25rem;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}''',
        content
    )
    content = re.sub(
        r'\.user-name\s*\{[^}]*\}',
        '''.user-name {
  font-size: 1.2rem;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 0.2rem;
}''',
        content
    )
    content = re.sub(
        r'\.user-nav-link\s*\{[^}]*\}',
        '''.user-nav-link {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  color: #475569;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  cursor: pointer;
}''',
        content
    )
    content = re.sub(
        r'\.user-nav-link:hover\s*\{[^}]*\}',
        '''.user-nav-link:hover {
  background: #F1F5F9;
  color: #0F172A;
}''',
        content
    )
    content = re.sub(
        r'\.user-nav-link\.active\s*\{[^}]*\}',
        '''.user-nav-link.active {
  background: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
}''',
        content
    )
    content = re.sub(
        r'\.user-main-content\s*\{[^}]*\}',
        '''.user-main-content {
  flex: 1;
  padding: 2.5rem;
  background: #F8FAFC;
  min-width: 0;
}''',
        content
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated:", path)

    legacy = 'my-node-app/static/css/user.css'
    if os.path.exists(legacy):
        with open(legacy, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated legacy:", legacy)

def update_auth_css():
    path = 'my-node-app/static/auth.css'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('#FF6B00', '#2563EB')
    content = content.replace('#ea580c', '#2563EB')
    content = content.replace('#f97316', '#1D4ED8')
    content = content.replace('rgba(255, 107, 0,', 'rgba(37, 99, 235,')

    content = re.sub(
        r'\.auth-card\s*\{[^}]*\}',
        '''.auth-card {
  width: 100%;
  max-width: 480px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-xl);
  padding: 2.5rem 2.25rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}''',
        content
    )
    content = re.sub(
        r'\.auth-title\s*\{[^}]*\}',
        '''.auth-title {
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  color: #0F172A;
}''',
        content
    )
    content = re.sub(
        r'\.auth-subtitle\s*\{[^}]*\}',
        '''.auth-subtitle {
  font-size: 0.95rem;
  color: #64748B;
}''',
        content
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated:", path)

    legacy = 'my-node-app/static/css/auth.css'
    if os.path.exists(legacy):
        with open(legacy, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated legacy:", legacy)

def update_admin_modern_css():
    path = 'my-node-app/static/adminModern.css'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('--admin-primary: #F97316;', '--admin-primary: #2563EB;')
    content = content.replace('--admin-primary-hover: #EA580C;', '--admin-primary-hover: #1D4ED8;')
    content = content.replace('--admin-primary-light: #FFF7ED;', '--admin-primary-light: #EFF6FF;')
    content = content.replace('--admin-primary-border: #FDBA74;', '--admin-primary-border: #BFDBFE;')
    content = content.replace('--admin-sidebar-accent: #F97316;', '--admin-sidebar-accent: #2563EB;')
    content = content.replace('rgba(249, 115, 22, 0.12)', 'rgba(37, 99, 235, 0.15)')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated:", path)

if __name__ == '__main__':
    update_components_css()
    update_user_css()
    update_auth_css()
    update_admin_modern_css()
