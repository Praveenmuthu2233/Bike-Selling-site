import os

admin_html_path = os.path.join("my-node-app", "templates", "admin.html")
with open(admin_html_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add CSS
css_snippet = """  <style>
    /* WhatsApp-Style Admin Customer Chat Interface */
    .admin-chat-container {
      display: flex;
      height: 740px;
      max-height: calc(100vh - 150px);
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.06);
    }
    .admin-chat-sidebar {
      width: 360px;
      border-right: 1px solid #e2e8f0;
      display: flex;
      flex-direction: column;
      background: #f8fafc;
      flex-shrink: 0;
    }
    .admin-chat-sidebar-header {
      padding: 1rem;
      border-bottom: 1px solid #e2e8f0;
      background: #ffffff;
    }
    .admin-chat-filter-pills {
      display: flex;
      gap: 0.35rem;
      margin-top: 0.75rem;
      overflow-x: auto;
      padding-bottom: 2px;
    }
    .admin-chat-filter-btn {
      padding: 0.35rem 0.75rem;
      font-size: 0.78rem;
      font-weight: 600;
      border-radius: 20px;
      border: 1px solid #e2e8f0;
      background: #ffffff;
      color: #64748b;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    }
    .admin-chat-filter-btn:hover {
      background: #f1f5f9;
      color: #0f172a;
    }
    .admin-chat-filter-btn.active {
      background: #ea580c;
      border-color: #ea580c;
      color: #ffffff;
    }
    .admin-chat-conv-list {
      flex: 1;
      overflow-y: auto;
    }
    .admin-chat-conv-item {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      padding: 0.9rem 1rem;
      border-bottom: 1px solid #f1f5f9;
      cursor: pointer;
      transition: all 0.15s ease;
      background: #ffffff;
    }
    .admin-chat-conv-item:hover {
      background: #f8fafc;
    }
    .admin-chat-conv-item.active {
      background: #fff7ed;
      border-left: 4px solid #ea580c;
    }
    .admin-chat-avatar {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: #e2e8f0;
      color: #475569;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      flex-shrink: 0;
      font-size: 0.95rem;
    }
    .admin-chat-avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .admin-chat-conv-info {
      flex: 1;
      min-width: 0;
    }
    .admin-chat-conv-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.2rem;
    }
    .admin-chat-conv-name {
      font-weight: 700;
      font-size: 0.92rem;
      color: #0f172a;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .admin-chat-conv-time {
      font-size: 0.72rem;
      color: #94a3b8;
    }
    .admin-chat-conv-mid {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      margin-bottom: 0.25rem;
    }
    .admin-chat-bike-tag {
      font-size: 0.72rem;
      font-weight: 600;
      color: #ea580c;
      background: rgba(234, 88, 12, 0.08);
      padding: 0.1rem 0.45rem;
      border-radius: 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 160px;
    }
    .admin-chat-conv-bottom {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }
    .admin-chat-conv-snippet {
      font-size: 0.82rem;
      color: #64748b;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
    }
    .admin-chat-unread-badge {
      background: #ea580c;
      color: #ffffff;
      font-size: 0.72rem;
      font-weight: 700;
      min-width: 18px;
      height: 18px;
      border-radius: 9999px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 0.35rem;
      flex-shrink: 0;
    }
    .admin-chat-main {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: #ffffff;
      position: relative;
    }
    .admin-chat-header {
      padding: 0.85rem 1.25rem;
      border-bottom: 1px solid #e2e8f0;
      background: #ffffff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }
    .admin-chat-header-left {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      min-width: 0;
    }
    .admin-chat-back-btn {
      display: none;
      background: none;
      border: none;
      color: #0f172a;
      font-size: 1.1rem;
      cursor: pointer;
      padding: 0.25rem 0.5rem;
    }
    .admin-chat-header-details h4 {
      margin: 0;
      font-size: 1rem;
      font-weight: 700;
      color: #0f172a;
    }
    .admin-chat-header-meta {
      font-size: 0.78rem;
      color: #64748b;
      display: flex;
      gap: 0.75rem;
      margin-top: 0.15rem;
      flex-wrap: wrap;
    }
    .admin-chat-header-actions {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .admin-chat-pinned-bike {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.6rem 1.25rem;
      background: #fff7ed;
      border-bottom: 1px solid #fed7aa;
    }
    .admin-chat-pinned-bike img {
      width: 48px;
      height: 48px;
      object-fit: cover;
      border-radius: 6px;
      border: 1px solid #fed7aa;
    }
    .admin-chat-pinned-info {
      flex: 1;
    }
    .admin-chat-pinned-title {
      font-size: 0.88rem;
      font-weight: 700;
      color: #9a3412;
    }
    .admin-chat-pinned-price {
      font-size: 0.82rem;
      font-weight: 700;
      color: #ea580c;
    }
    .admin-chat-messages-stream {
      flex: 1;
      padding: 1.25rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
      background: #f8fafc;
    }
    .admin-chat-bubble-row {
      display: flex;
      flex-direction: column;
    }
    .admin-chat-bubble-row.outgoing {
      align-items: flex-end;
    }
    .admin-chat-bubble-row.incoming {
      align-items: flex-start;
    }
    .admin-chat-bubble {
      max-width: 72%;
      padding: 0.65rem 0.9rem;
      border-radius: 12px;
      font-size: 0.92rem;
      line-height: 1.45;
      word-break: break-word;
      position: relative;
    }
    .admin-chat-bubble.outgoing {
      background: #0f172a;
      color: #ffffff;
      border-top-right-radius: 2px;
    }
    .admin-chat-bubble.incoming {
      background: #ffffff;
      color: #0f172a;
      border-top-left-radius: 2px;
      border: 1px solid #e2e8f0;
      border-left: 3px solid #ea580c;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .admin-chat-sender-tag {
      font-size: 0.75rem;
      font-weight: 700;
      margin-bottom: 0.2rem;
    }
    .admin-chat-bubble.incoming .admin-chat-sender-tag {
      color: #ea580c;
    }
    .admin-chat-bubble.outgoing .admin-chat-sender-tag {
      color: #38bdf8;
    }
    .admin-chat-bubble-text {
      white-space: pre-wrap;
    }
    .admin-chat-bubble-meta {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.35rem;
      margin-top: 0.25rem;
      font-size: 0.7rem;
      opacity: 0.8;
    }
    .admin-chat-quick-replies {
      padding: 0.5rem 1.25rem;
      background: #ffffff;
      border-top: 1px solid #f1f5f9;
      display: flex;
      gap: 0.4rem;
      overflow-x: auto;
      white-space: nowrap;
    }
    .admin-chat-quick-pill {
      font-size: 0.75rem;
      padding: 0.25rem 0.65rem;
      background: #f1f5f9;
      color: #475569;
      border: 1px solid #e2e8f0;
      border-radius: 15px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .admin-chat-quick-pill:hover {
      background: #fff7ed;
      color: #ea580c;
      border-color: #fed7aa;
    }
    .admin-chat-input-bar {
      padding: 0.75rem 1.25rem;
      background: #ffffff;
      border-top: 1px solid #e2e8f0;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .admin-chat-input-bar textarea {
      flex: 1;
      border: 1px solid #cbd5e1;
      border-radius: 20px;
      padding: 0.6rem 1rem;
      font-size: 0.92rem;
      resize: none;
      outline: none;
      font-family: inherit;
      max-height: 100px;
    }
    .admin-chat-input-bar textarea:focus {
      border-color: #ea580c;
      box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.1);
    }
    .admin-chat-send-btn {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      background: linear-gradient(135deg, #ea580c, #f97316);
      border: none;
      color: #ffffff;
      font-size: 1rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: all 0.15s ease;
    }
    .admin-chat-send-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 0 10px rgba(234, 88, 12, 0.4);
    }
    .admin-chat-placeholder {
      margin: auto;
      text-align: center;
      max-width: 400px;
      color: #94a3b8;
    }
    .admin-chat-placeholder i {
      font-size: 3.5rem;
      color: #cbd5e1;
      margin-bottom: 1rem;
    }
    @media (max-width: 900px) {
      .admin-chat-sidebar {
        width: 100%;
      }
      .admin-chat-container.chat-active-mobile .admin-chat-sidebar {
        display: none;
      }
      .admin-chat-container.chat-active-mobile .admin-chat-main {
        display: flex;
      }
      .admin-chat-main {
        display: none;
      }
      .admin-chat-back-btn {
        display: block;
      }
    }
  </style>
</head>"""

content = content.replace("</head>", css_snippet, 1)

# 2. Add Sidebar navigation link
nav_target = """          <a class="nav-item" id="nav-messages" onclick="switchAdminTab('tab-messages', this)">
            <i class="fas fa-comments"></i>
            <span>Contact Messages</span>
          </a>"""

nav_replacement = """          <a class="nav-item" id="nav-messages" onclick="switchAdminTab('tab-messages', this)">
            <i class="fas fa-comments"></i>
            <span>Contact Messages</span>
          </a>
          <a class="nav-item" id="nav-customer-chat" onclick="switchAdminTab('tab-customer-chat', this)">
            <i class="fas fa-comment-dots"></i>
            <span>Customer Chat</span>
            <span class="nav-badge warning" id="nav-badge-chat" style="display:none;">0</span>
          </a>"""

content = content.replace(nav_target, nav_replacement, 1)

# 3. Add tab pane for tab-customer-chat right after tab-messages
tab_target = """          </div>
        </section>

        <!-- ==================================================
             TAB 11: REPORTS & EXPORTS"""

tab_replacement = """          </div>
        </section>

        <!-- ==================================================
             TAB: DEDICATED CUSTOMER CHAT DASHBOARD
             ================================================== -->
        <section class="admin-tab-pane" id="tab-customer-chat">
          <div class="admin-chat-container" id="adminChatContainer">
            <!-- Left: Conversation list & filters -->
            <aside class="admin-chat-sidebar">
              <div class="admin-chat-sidebar-header">
                <div class="toolbar-search-input" style="width: 100%;">
                  <i class="fas fa-search"></i>
                  <input type="text" id="adminChatSearch" placeholder="Search customer, email, bike..." oninput="debounceAdminChatSearch()">
                </div>
                <div class="admin-chat-filter-pills">
                  <button class="admin-chat-filter-btn active" onclick="setAdminChatFilter('all', this)">All</button>
                  <button class="admin-chat-filter-btn" onclick="setAdminChatFilter('unread', this)">Unread</button>
                  <button class="admin-chat-filter-btn" onclick="setAdminChatFilter('open', this)">Open</button>
                  <button class="admin-chat-filter-btn" onclick="setAdminChatFilter('resolved', this)">Resolved</button>
                </div>
              </div>
              <div class="admin-chat-conv-list" id="adminChatConvList">
                <div style="text-align: center; padding: 3rem 1rem; color: #94a3b8;">
                  <i class="fas fa-spinner fa-spin"></i> Loading customer conversations...
                </div>
              </div>
            </aside>

            <!-- Right: Active Chat Window -->
            <section class="admin-chat-main" id="adminChatMain">
              <!-- Active Chat Header -->
              <div class="admin-chat-header" id="adminChatHeader" style="display: none;">
                <div class="admin-chat-header-left">
                  <button class="admin-chat-back-btn" onclick="closeAdminMobileChatView()" title="Back to conversations">
                    <i class="fas fa-arrow-left"></i>
                  </button>
                  <div class="admin-chat-avatar" id="adminChatHeaderAvatar">U</div>
                  <div class="admin-chat-header-details">
                    <h4 id="adminChatHeaderCustomerName">Customer Name</h4>
                    <div class="admin-chat-header-meta">
                      <span id="adminChatHeaderCustomerEmail"><i class="fas fa-envelope"></i> email@example.com</span>
                      <span id="adminChatHeaderCustomerPhone"><i class="fas fa-phone"></i> +91 ...</span>
                    </div>
                  </div>
                </div>
                <div class="admin-chat-header-actions">
                  <!-- Superadmin staff assignment dropdown -->
                  <div id="adminChatStaffAssignWrap" style="display: none; align-items: center; gap: 0.35rem;">
                    <label style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Assignee:</label>
                    <select id="adminChatAssignSelect" class="form-control" style="font-size: 0.78rem; padding: 0.25rem 0.5rem; height: auto;" onchange="handleAdminChatStaffAssign(this)">
                      <option value="">Unassigned</option>
                    </select>
                  </div>
                  <button class="btn btn-sm btn-outline" id="adminChatToggleStatusBtn" onclick="toggleAdminChatStatus()">
                    <i class="fas fa-check"></i> Mark Resolved
                  </button>
                </div>
              </div>

              <!-- Pinned Bike Context Banner (if conversation has a related bike) -->
              <div class="admin-chat-pinned-bike" id="adminChatPinnedBike" style="display: none;">
                <img id="adminChatBikeThumb" src="/static/images/IMG-20251204-WA0053.jpg" alt="Bike">
                <div class="admin-chat-pinned-info">
                  <div class="admin-chat-pinned-title" id="adminChatBikeTitle">Motorcycle Name</div>
                  <div class="admin-chat-pinned-price" id="adminChatBikePrice">₹0</div>
                </div>
                <a id="adminChatBikeLink" href="#" target="_blank" class="btn btn-xs btn-outline">
                  <i class="fas fa-external-link-alt"></i> View Bike
                </a>
              </div>

              <!-- Messages Stream -->
              <div class="admin-chat-messages-stream" id="adminChatMessagesStream">
                <div class="admin-chat-placeholder" id="adminChatPlaceholder">
                  <i class="fas fa-comments"></i>
                  <h3 style="color:#0f172a; margin-bottom:0.5rem;">Customer Support Messenger</h3>
                  <p style="font-size:0.9rem; line-height:1.5;">Select a customer conversation from the left to read messages, provide assistance, and answer bike inquiries.</p>
                </div>
              </div>

              <!-- Quick Replies Bar -->
              <div class="admin-chat-quick-replies" id="adminChatQuickReplies" style="display: none;">
                <span class="admin-chat-quick-pill" onclick="insertAdminQuickReply('Yes, this motorcycle is available for inspection at our showroom.')">Available for Inspection</span>
                <span class="admin-chat-quick-pill" onclick="insertAdminQuickReply('Our showroom is open Monday through Saturday from 9:00 AM to 8:00 PM.')">Showroom Hours</span>
                <span class="admin-chat-quick-pill" onclick="insertAdminQuickReply('We provide complete RC ownership transfer and vehicle financing assistance.')">RC Transfer & Finance</span>
                <span class="admin-chat-quick-pill" onclick="insertAdminQuickReply('Would you like to schedule a personal test ride this weekend?')">Schedule Test Ride</span>
              </div>

              <!-- Reply Input Bar -->
              <div class="admin-chat-input-bar" id="adminChatInputBar" style="display: none;">
                <textarea id="adminChatMessageInput" rows="1" placeholder="Type a reply to the customer..." onkeydown="handleAdminChatKeyDown(event)"></textarea>
                <button class="admin-chat-send-btn" id="adminChatSendBtn" onclick="sendAdminChatMessage()" title="Send reply">
                  <i class="fas fa-paper-plane"></i>
                </button>
              </div>
            </section>
          </div>
        </section>

        <!-- ==================================================
             TAB 11: REPORTS & EXPORTS"""

content = content.replace(tab_target, tab_replacement, 1)

# 4. In switchAdminTab:
titles_target = """        'tab-staff': ['Staff Management', 'Personnel & Access Control'],
        'tab-messages': ['Contact Messages', 'Inbound Inquiries'],"""

titles_replacement = """        'tab-staff': ['Staff Management', 'Personnel & Access Control'],
        'tab-messages': ['Contact Messages', 'Inbound Inquiries'],
        'tab-customer-chat': ['Customer Chat', 'Real-Time Support Messenger'],"""

content = content.replace(titles_target, titles_replacement, 1)

tab_loaders_target = """      else if (tabId === 'tab-staff') loadAdminStaff();
      else if (tabId === 'tab-messages') loadAdminMessages(1);"""

tab_loaders_replacement = """      else if (tabId === 'tab-staff') loadAdminStaff();
      else if (tabId === 'tab-messages') loadAdminMessages(1);
      else if (tabId === 'tab-customer-chat') loadAdminChat();
      else if (typeof pauseAdminChatPolling === 'function') pauseAdminChatPolling();"""

content = content.replace(tab_loaders_target, tab_loaders_replacement, 1)

# 5. In navMap:
navmap_target = """          'tab-staff': 'nav-staff',
          'tab-messages': 'nav-messages',"""

navmap_replacement = """          'tab-staff': 'nav-staff',
          'tab-messages': 'nav-messages',
          'tab-customer-chat': 'nav-customer-chat',"""

content = content.replace(navmap_target, navmap_replacement, 1)

# 6. In DOMContentLoaded:
init_target = """        if (hash && document.getElementById(hash)) {
          switchAdminTab(hash, document.getElementById(navMap[hash]));
        } else {"""

init_replacement = """        const chatParam = urlParams.get('tab');
        if (chatParam === 'customer-chat' || chatParam === 'chat') {
          switchAdminTab('tab-customer-chat', document.getElementById('nav-customer-chat'));
          const convParam = urlParams.get('conv_id');
          if (convParam) {
            setTimeout(() => openAdminConversation(parseInt(convParam)), 400);
          }
        } else if (hash && document.getElementById(hash)) {
          switchAdminTab(hash, document.getElementById(navMap[hash]));
        } else {"""

content = content.replace(init_target, init_replacement, 1)

# Add periodic badge check:
badge_target = """        loadAdminNotifications();"""
badge_replacement = """        loadAdminNotifications();
        updateAdminChatUnreadBadge();
        setInterval(updateAdminChatUnreadBadge, 8000);"""

content = content.replace(badge_target, badge_replacement, 1)

# 7. Add Admin Chat JavaScript functions right before </script>
js_functions = """
    // ---------------------------------------------------------------------------
    // SMR MOTORS - ADMIN CHAT MANAGEMENT SYSTEM (REAL-TIME & TIDB PERSISTENT)
    // ---------------------------------------------------------------------------
    let currentAdminChatConvId = null;
    let currentAdminChatFilter = 'all';
    let adminChatSearchTimer = null;
    let adminChatPollTimer = null;
    let adminChatLastMsgId = 0;
    let adminChatConversations = [];
    let currentActiveConvData = null;

    async function updateAdminChatUnreadBadge() {
      try {
        const res = await apiRequest('/api/chat/unread-count', { skipAuthRedirect: true });
        const badge = document.getElementById('nav-badge-chat');
        if (badge) {
          if (res.unread_count > 0) {
            badge.innerText = res.unread_count;
            badge.style.display = 'inline-block';
          } else {
            badge.style.display = 'none';
          }
        }
      } catch (e) {
        // Silently ignore
      }
    }

    async function loadAdminChat() {
      const convList = document.getElementById('adminChatConvList');
      if (!convList) return;
      const search = (document.getElementById('adminChatSearch')?.value || '').trim();

      try {
        let endpoint = `/api/admin/chat/conversations?filter=${encodeURIComponent(currentAdminChatFilter)}`;
        if (search) endpoint += `&search=${encodeURIComponent(search)}`;

        const res = await apiRequest(endpoint);
        adminChatConversations = res.conversations || [];
        renderAdminChatConvList(adminChatConversations);

        // Load staff members for assignment dropdown if Superadmin
        loadAdminStaffForChat();

        // Check URL query param conv_id
        const urlParams = new URLSearchParams(window.location.search);
        const convParam = urlParams.get('conv_id');
        if (convParam) {
          openAdminConversation(parseInt(convParam));
        } else if (adminChatConversations.length > 0 && window.innerWidth > 900 && !currentAdminChatConvId) {
          openAdminConversation(adminChatConversations[0].id);
        }
      } catch (e) {
        convList.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--admin-danger);">${escapeHtml(e.message)}</div>`;
      }
    }

    function setAdminChatFilter(filter, btn) {
      currentAdminChatFilter = filter;
      document.querySelectorAll('.admin-chat-filter-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      loadAdminChat();
    }

    function debounceAdminChatSearch() {
      if (adminChatSearchTimer) clearTimeout(adminChatSearchTimer);
      adminChatSearchTimer = setTimeout(() => {
        loadAdminChat();
      }, 350);
    }

    function renderAdminChatConvList(convs) {
      const convList = document.getElementById('adminChatConvList');
      if (!convs || convs.length === 0) {
        convList.innerHTML = `
          <div style="text-align: center; padding: 3rem 1rem; color: #94a3b8;">
            <i class="fas fa-inbox" style="font-size: 2.2rem; color: #cbd5e1; margin-bottom: 0.75rem;"></i>
            <p style="margin: 0; font-size: 0.9rem; font-weight:600;">No conversations found.</p>
            <p style="font-size: 0.8rem; margin-top: 0.25rem;">Adjust search filters above.</p>
          </div>
        `;
        return;
      }

      convList.innerHTML = convs.map(c => {
        const isActive = c.id === currentAdminChatConvId ? 'active' : '';
        const timeStr = formatChatTime(c.last_message_at || c.created_at);
        const avatarLetter = (c.customer.name || 'U').charAt(0).toUpperCase();
        const avatarHtml = c.customer.avatar
          ? `<img src="${escapeHtml(c.customer.avatar)}" alt="${escapeHtml(c.customer.name)}">`
          : `<span>${avatarLetter}</span>`;
        const unreadBadge = c.unread_count > 0 
          ? `<span class="admin-chat-unread-badge">${c.unread_count}</span>` 
          : '';
        const bikeTag = c.bike 
          ? `<span class="admin-chat-bike-tag"><i class="fas fa-motorcycle"></i> ${escapeHtml(c.bike.title || c.bike.model)}</span>` 
          : '';
        const statusClass = c.status === 'resolved' ? 'color:#94a3b8;' : 'color:#10b981;';

        return `
          <div class="admin-chat-conv-item ${isActive}" onclick="openAdminConversation(${c.id})">
            <div class="admin-chat-avatar">${avatarHtml}</div>
            <div class="admin-chat-conv-info">
              <div class="admin-chat-conv-top">
                <span class="admin-chat-conv-name">${escapeHtml(c.customer.name)}</span>
                <span class="admin-chat-conv-time">${timeStr}</span>
              </div>
              <div class="admin-chat-conv-mid">
                ${bikeTag}
                <span style="font-size:0.7rem; font-weight:600; text-transform:capitalize; ${statusClass}">${c.status}</span>
              </div>
              <div class="admin-chat-conv-bottom">
                <span class="admin-chat-conv-snippet">${escapeHtml(c.last_message)}</span>
                ${unreadBadge}
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    async function openAdminConversation(convId) {
      currentAdminChatConvId = convId;
      adminChatLastMsgId = 0;
      pauseAdminChatPolling();

      const container = document.getElementById('adminChatContainer');
      if (container) container.classList.add('chat-active-mobile');

      document.querySelectorAll('#adminChatConvList .admin-chat-conv-item').forEach(el => el.classList.remove('active'));
      const activeEl = document.querySelector(`#adminChatConvList .admin-chat-conv-item[onclick*="${convId}"]`);
      if (activeEl) activeEl.classList.add('active');

      document.getElementById('adminChatPlaceholder').style.display = 'none';
      document.getElementById('adminChatHeader').style.display = 'flex';
      document.getElementById('adminChatQuickReplies').style.display = 'flex';
      document.getElementById('adminChatInputBar').style.display = 'flex';

      const stream = document.getElementById('adminChatMessagesStream');
      stream.innerHTML = '<div style="text-align:center; padding:3rem; color:#94a3b8;"><i class="fas fa-spinner fa-spin"></i> Loading conversation...</div>';

      try {
        const res = await apiRequest(`/api/chat/conversations/${convId}/messages`);
        const conv = res.conversation;
        currentActiveConvData = conv;
        const messages = res.messages || [];

        // Header info
        document.getElementById('adminChatHeaderCustomerName').innerText = conv.customer_name || 'Customer';
        document.getElementById('adminChatHeaderCustomerEmail').innerHTML = `<i class="fas fa-envelope"></i> ${escapeHtml(conv.customer_email || 'No email')}`;
        document.getElementById('adminChatHeaderCustomerPhone').innerHTML = `<i class="fas fa-id-badge"></i> Subject: ${escapeHtml(conv.subject || 'Support Chat')}`;

        const avatarEl = document.getElementById('adminChatHeaderAvatar');
        if (conv.customer_avatar) {
          avatarEl.innerHTML = `<img src="${escapeHtml(conv.customer_avatar)}" alt="User">`;
        } else {
          avatarEl.innerText = (conv.customer_name || 'U').charAt(0).toUpperCase();
        }

        // Toggle Status Button
        const statusBtn = document.getElementById('adminChatToggleStatusBtn');
        if (conv.status === 'resolved') {
          statusBtn.innerHTML = '<i class="fas fa-undo"></i> Reopen Chat';
          statusBtn.className = 'btn btn-sm btn-secondary';
        } else {
          statusBtn.innerHTML = '<i class="fas fa-check"></i> Mark Resolved';
          statusBtn.className = 'btn btn-sm btn-outline';
        }

        // Superadmin staff assign dropdown
        const assignWrap = document.getElementById('adminChatStaffAssignWrap');
        const role = (JSON.parse(localStorage.getItem('admin_user') || '{}')).role;
        if (role === 'superadmin') {
          assignWrap.style.display = 'flex';
          const assignSelect = document.getElementById('adminChatAssignSelect');
          if (assignSelect) assignSelect.value = conv.assigned_admin_id || '';
        } else {
          assignWrap.style.display = 'none';
        }

        // Pinned Bike Banner
        const pinnedCard = document.getElementById('adminChatPinnedBike');
        if (conv.bike_id && conv.bike_title) {
          document.getElementById('adminChatBikeThumb').src = conv.bike_image || '/static/images/IMG-20251204-WA0053.jpg';
          document.getElementById('adminChatBikeTitle').innerText = conv.bike_title;
          document.getElementById('adminChatBikePrice').innerText = conv.bike_price ? `₹${Number(conv.bike_price).toLocaleString('en-IN')}` : '';
          document.getElementById('adminChatBikeLink').href = `/enquiry-bike-details.html?id=${conv.bike_id}`;
          pinnedCard.style.display = 'flex';
        } else {
          pinnedCard.style.display = 'none';
        }

        stream.innerHTML = '';
        renderAdminMessagesBatch(messages, stream, false);
        scrollAdminChatToBottom();
        updateAdminChatUnreadBadge();
        startAdminChatDeltaPolling();
      } catch (e) {
        stream.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--admin-danger);">${escapeHtml(e.message)}</div>`;
      }
    }

    function renderAdminMessagesBatch(messages, container, isAppend = false) {
      if (!messages || messages.length === 0) {
        if (!isAppend) {
          container.innerHTML = '<div style="text-align:center; padding:2rem; color:#94a3b8; font-size:0.85rem;">No messages in this chat yet. Type a reply below.</div>';
        }
        return;
      }

      messages.forEach(msg => {
        if (document.getElementById(`admin-msg-${msg.id}`)) return;

        const isOutgoing = (msg.sender_role === 'admin' || msg.sender_role === 'superadmin');
        const row = document.createElement('div');
        row.id = `admin-msg-${msg.id}`;
        row.className = `admin-chat-bubble-row ${isOutgoing ? 'outgoing' : 'incoming'}`;

        const bubble = document.createElement('div');
        bubble.className = `admin-chat-bubble ${isOutgoing ? 'outgoing' : 'incoming'}`;

        const senderTag = document.createElement('div');
        senderTag.className = 'admin-chat-sender-tag';
        senderTag.innerText = isOutgoing ? 'SMR Staff Response' : (currentActiveConvData?.customer_name || 'Customer');
        bubble.appendChild(senderTag);

        const textDiv = document.createElement('div');
        textDiv.className = 'admin-chat-bubble-text';
        textDiv.textContent = msg.message;
        bubble.appendChild(textDiv);

        const metaDiv = document.createElement('div');
        metaDiv.className = 'admin-chat-bubble-meta';
        const timeSpan = document.createElement('span');
        timeSpan.innerText = formatChatTime(msg.created_at);
        metaDiv.appendChild(timeSpan);

        if (isOutgoing) {
          const tick = document.createElement('i');
          tick.className = `fas fa-check-double chat-read-tick ${msg.is_read ? 'read' : ''}`;
          tick.style.marginLeft = '4px';
          tick.title = msg.is_read ? 'Seen by Customer' : 'Delivered';
          metaDiv.appendChild(tick);
        }

        bubble.appendChild(metaDiv);
        row.appendChild(bubble);
        container.appendChild(row);

        if (msg.id > adminChatLastMsgId) {
          adminChatLastMsgId = msg.id;
        }
      });
    }

    function startAdminChatDeltaPolling() {
      pauseAdminChatPolling();
      adminChatPollTimer = setInterval(async () => {
        if (!currentAdminChatConvId || document.visibilityState === 'hidden') return;
        try {
          const res = await apiRequest(`/api/chat/conversations/${currentAdminChatConvId}/messages?since_id=${adminChatLastMsgId}`, { skipAuthRedirect: true });
          if (res.success && res.messages && res.messages.length > 0) {
            const stream = document.getElementById('adminChatMessagesStream');
            renderAdminMessagesBatch(res.messages, stream, true);
            scrollAdminChatToBottom();
            updateAdminChatUnreadBadge();
          }
        } catch (e) {
          // Poll fails safely
        }
      }, 2500);
    }

    function pauseAdminChatPolling() {
      if (adminChatPollTimer) {
        clearInterval(adminChatPollTimer);
        adminChatPollTimer = null;
      }
    }

    async function sendAdminChatMessage() {
      if (!currentAdminChatConvId) return;
      const input = document.getElementById('adminChatMessageInput');
      const text = input.value.trim();
      if (!text) return;

      const btn = document.getElementById('adminChatSendBtn');
      btn.disabled = true;

      try {
        const res = await apiRequest(`/api/chat/conversations/${currentAdminChatConvId}/messages`, {
          method: 'POST',
          body: { message: text }
        });

        if (res.success && res.message) {
          input.value = '';
          const stream = document.getElementById('adminChatMessagesStream');
          renderAdminMessagesBatch([res.message], stream, true);
          scrollAdminChatToBottom();
          loadAdminChat();
        } else {
          showAdminToast(res.message || 'Failed to send message', 'error');
        }
      } catch (e) {
        showAdminToast(e.message || 'Failed to send message', 'error');
      } finally {
        btn.disabled = false;
        input.focus();
      }
    }

    function handleAdminChatKeyDown(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendAdminChatMessage();
      }
    }

    function insertAdminQuickReply(text) {
      const input = document.getElementById('adminChatMessageInput');
      if (input) {
        input.value = text;
        input.focus();
      }
    }

    async function toggleAdminChatStatus() {
      if (!currentAdminChatConvId || !currentActiveConvData) return;
      const newStatus = currentActiveConvData.status === 'resolved' ? 'open' : 'resolved';
      try {
        const res = await apiRequest(`/api/admin/chat/conversations/${currentAdminChatConvId}/status`, {
          method: 'PUT',
          body: { status: newStatus }
        });
        if (res.success) {
          showAdminToast(`Conversation marked as ${newStatus}`, 'success');
          openAdminConversation(currentAdminChatConvId);
          loadAdminChat();
        } else {
          showAdminToast(res.message || 'Failed to update status', 'error');
        }
      } catch (e) {
        showAdminToast(e.message, 'error');
      }
    }

    async function loadAdminStaffForChat() {
      const select = document.getElementById('adminChatAssignSelect');
      if (!select) return;
      try {
        const res = await apiRequest('/api/admin/staff', { skipAuthRedirect: true });
        if (res.success && res.staff) {
          select.innerHTML = '<option value="">Unassigned</option>';
          res.staff.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.username} (${s.role})`;
            select.appendChild(opt);
          });
          if (currentActiveConvData && currentActiveConvData.assigned_admin_id) {
            select.value = currentActiveConvData.assigned_admin_id;
          }
        }
      } catch (e) {
        // Staff endpoint might be restricted to superadmin
      }
    }

    async function handleAdminChatStaffAssign(select) {
      if (!currentAdminChatConvId) return;
      const staffId = select.value ? parseInt(select.value) : null;
      try {
        const res = await apiRequest(`/api/admin/chat/conversations/${currentAdminChatConvId}/assign`, {
          method: 'PUT',
          body: { assigned_admin_id: staffId }
        });
        if (res.success) {
          showAdminToast('Staff assigned successfully', 'success');
          loadAdminChat();
        } else {
          showAdminToast(res.message || 'Assignment failed', 'error');
        }
      } catch (e) {
        showAdminToast(e.message, 'error');
      }
    }

    function closeAdminMobileChatView() {
      const container = document.getElementById('adminChatContainer');
      if (container) container.classList.remove('chat-active-mobile');
      pauseAdminChatPolling();
      currentAdminChatConvId = null;
    }

    function scrollAdminChatToBottom() {
      const stream = document.getElementById('adminChatMessagesStream');
      if (stream) stream.scrollTop = stream.scrollHeight;
    }
"""

content = content.replace("</script>", js_functions + "\n  </script>", 1)

with open(admin_html_path, "w", encoding="utf-8") as f:
    f.write(content)

print("[Patch Admin Chat] Successfully applied Admin Chat modifications to admin.html!")
