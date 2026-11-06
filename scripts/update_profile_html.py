import re

def update_profile_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update chat styles in <style>
    old_chat_css_target = """    .chat-dashboard-container {
      display: flex;
      height: 700px;
      max-height: calc(100vh - 160px);
      background: #0b1120;
      border: 1px solid var(--border-subtle, #1e293b);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.4);
    }"""

    new_chat_css = """    .chat-dashboard-container {
      display: flex;
      height: 700px;
      max-height: calc(100vh - 160px);
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
    }
    .chat-sidebar {
      width: 340px;
      border-right: 1px solid #E2E8F0;
      display: flex;
      flex-direction: column;
      background: #FFFFFF;
      flex-shrink: 0;
    }
    .chat-sidebar-header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid #E2E8F0;
      background: #F8FAFC;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .chat-sidebar-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #0F172A;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .chat-online-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.75rem;
      font-weight: 600;
      color: #16A34A;
      background: #F0FDF4;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      border: 1px solid #BBF7D0;
    }
    .pulsing-dot {
      width: 7px;
      height: 7px;
      background: #16A34A;
      border-radius: 50%;
      animation: pulse-glow 2s infinite;
    }
    .chat-conv-list {
      flex: 1;
      overflow-y: auto;
      background: #FFFFFF;
    }
    .chat-conv-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.85rem 1rem;
      border-bottom: 1px solid #F1F5F9;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
      background: #FFFFFF;
    }
    .chat-conv-item:hover {
      background: #F8FAFC;
    }
    .chat-conv-item.active {
      background: #EFF6FF;
      border-left: 3px solid #2563EB;
    }
    .chat-conv-avatar {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: #EFF6FF;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      color: #2563EB;
      flex-shrink: 0;
      overflow: hidden;
      border: 1px solid #E2E8F0;
    }
    .chat-conv-avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .chat-conv-info {
      flex: 1;
      min-width: 0;
    }
    .chat-conv-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.2rem;
    }
    .chat-conv-name {
      font-weight: 600;
      font-size: 0.92rem;
      color: #0F172A;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .chat-conv-time {
      font-size: 0.72rem;
      color: #94A3B8;
    }
    .chat-conv-bottom {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }
    .chat-conv-snippet {
      font-size: 0.82rem;
      color: #64748B;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
    }
    .chat-unread-badge {
      background: #2563EB;
      color: #FFFFFF;
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
    .chat-main-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: #F8FAFC;
      position: relative;
    }
    .chat-view-header {
      padding: 0.9rem 1.25rem;
      background: #FFFFFF;
      border-bottom: 1px solid #E2E8F0;
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }
    .chat-back-btn {
      display: none;
      background: none;
      border: none;
      color: #172033;
      font-size: 1.1rem;
      cursor: pointer;
      padding: 0.25rem 0.5rem;
    }
    .chat-header-avatar {
      position: relative;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #2563EB, #1D4ED8);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: #FFFFFF;
      font-size: 0.85rem;
    }
    .chat-header-avatar .online-indicator {
      position: absolute;
      bottom: 0;
      right: 0;
      width: 10px;
      height: 10px;
      background: #16A34A;
      border: 2px solid #FFFFFF;
      border-radius: 50%;
    }
    .chat-header-info {
      flex: 1;
      min-width: 0;
    }
    .chat-header-name {
      font-size: 1rem;
      font-weight: 700;
      color: #0F172A;
    }
    .chat-header-status {
      font-size: 0.78rem;
      color: #16A34A;
    }
    .chat-status-chip {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      text-transform: capitalize;
    }
    .chat-status-chip.open {
      background: #F0FDF4;
      color: #16A34A;
      border: 1px solid #BBF7D0;
    }
    .chat-status-chip.resolved {
      background: #F1F5F9;
      color: #64748B;
      border: 1px solid #E2E8F0;
    }
    .chat-pinned-bike-card {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.6rem 1.25rem;
      background: #EFF6FF;
      border-bottom: 1px solid #BFDBFE;
    }
    .chat-pinned-bike-card img {
      width: 48px;
      height: 48px;
      object-fit: cover;
      border-radius: 6px;
      border: 1px solid #CBD5E1;
    }
    .pinned-bike-details {
      flex: 1;
    }
    .pinned-bike-title {
      font-size: 0.88rem;
      font-weight: 700;
      color: #0F172A;
    }
    .pinned-bike-price {
      font-size: 0.82rem;
      font-weight: 700;
      color: #2563EB;
    }
    .chat-messages-stream {
      flex: 1;
      padding: 1.25rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
      background: #F8FAFC;
    }
    .chat-placeholder {
      margin: auto;
      text-align: center;
      max-width: 380px;
      color: #64748B;
    }
    .chat-placeholder-icon {
      font-size: 3rem;
      color: #94A3B8;
      margin-bottom: 1rem;
    }
    .chat-placeholder h3 {
      color: #0F172A;
      margin-bottom: 0.5rem;
    }
    .chat-placeholder p {
      font-size: 0.9rem;
      line-height: 1.5;
      color: #64748B;
    }
    /* WhatsApp Light Theme Message Bubbles */
    .chat-bubble-row {
      display: flex;
      flex-direction: column;
    }
    .chat-bubble-row.outgoing {
      align-items: flex-end;
    }
    .chat-bubble-row.incoming {
      align-items: flex-start;
    }
    .chat-bubble {
      max-width: 72%;
      padding: 0.65rem 0.9rem;
      border-radius: 12px;
      position: relative;
      font-size: 0.92rem;
      line-height: 1.45;
      word-break: break-word;
    }
    .chat-bubble.outgoing {
      background: #EFF6FF;
      color: #1E3A8A;
      border-top-right-radius: 2px;
      border: 1px solid #BFDBFE;
    }
    .chat-bubble.incoming {
      background: #FFFFFF;
      color: #172033;
      border-top-left-radius: 2px;
      border-left: 3px solid #2563EB;
      border-top: 1px solid #E2E8F0;
      border-right: 1px solid #E2E8F0;
      border-bottom: 1px solid #E2E8F0;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .chat-bubble-sender {
      font-size: 0.75rem;
      font-weight: 700;
      color: #2563EB;
      margin-bottom: 0.2rem;
    }
    .chat-bubble-text {
      white-space: pre-wrap;
    }
    .chat-bubble-meta {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.35rem;
      margin-top: 0.25rem;
      font-size: 0.7rem;
      color: #64748B;
    }
    .chat-read-tick {
      color: #94A3B8;
    }
    .chat-read-tick.read {
      color: #2563EB;
    }
    .chat-date-pill {
      align-self: center;
      background: #E2E8F0;
      color: #475569;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 0.2rem 0.75rem;
      border-radius: 9999px;
      margin: 0.5rem 0;
      border: 1px solid #CBD5E1;
    }
    .chat-input-bar {
      padding: 0.75rem 1rem;
      background: #FFFFFF;
      border-top: 1px solid #E2E8F0;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .chat-input-bar textarea {
      flex: 1;
      background: #F8FAFC;
      border: 1px solid #CBD5E1;
      color: #172033;
      border-radius: 20px;
      padding: 0.6rem 1rem;
      font-size: 0.92rem;
      resize: none;
      max-height: 100px;
      outline: none;
      font-family: inherit;
    }
    .chat-input-bar textarea:focus {
      border-color: #2563EB;
      background: #FFFFFF;
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
    }
    .chat-send-btn {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      background: linear-gradient(135deg, #2563EB, #1D4ED8);
      border: none;
      color: #FFFFFF;
      font-size: 1rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.15s ease, box-shadow 0.15s ease;
      flex-shrink: 0;
    }
    .chat-send-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 0 12px rgba(37, 99, 235, 0.4);
    }
    .chat-send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }"""

    # Replace the chat styles block
    chat_style_pattern = r'    \.chat-dashboard-container\s*\{.*?(?=\s*@media \(max-width: 768px\))'
    content = re.sub(chat_style_pattern, new_chat_css, content, flags=re.DOTALL)

    # 2. Update renderUserChatConvList
    old_render_conv_list = """    function renderUserChatConvList(convs) {
      const convList = document.getElementById('userChatConvList');
      if (!convs || convs.length === 0) {
        convList.innerHTML = `
          <div style="text-align: center; padding: 3rem 1.5rem; color: var(--text-muted);">
            <i class="fas fa-inbox" style="font-size: 2.2rem; color: #334155; margin-bottom: 0.75rem;"></i>
            <p style="margin: 0; font-size: 0.95rem; font-weight: 600; color: #fff;">No active conversations.</p>
            <p style="font-size: 0.82rem; margin-top: 0.35rem; color: var(--text-muted);">Start an inquiry below to chat with SMR Support.</p>
            <button class="btn btn-sm btn-primary" onclick="openNewChatModal()" style="margin-top: 1rem;">
              <i class="fas fa-plus"></i> Start New Inquiry
            </button>
          </div>
        `;
        return;
      }

      convList.innerHTML = convs.map(c => {
        const isActive = Number(c.id) === Number(currentUserChatConvId) ? 'active' : '';
        const timeStr = formatChatTime(c.last_message_at || c.created_at);
        const thumbHtml = c.bike_image 
          ? `<img src="${escapeHtml(c.bike_image)}" alt="Bike" onerror="this.src='/static/images/IMG-20251204-WA0053.jpg'">`
          : `<i class="fas fa-headset"></i>`;
        const unreadBadge = c.unread_count > 0 
          ? `<span class="chat-unread-badge">${c.unread_count}</span>` 
          : '';

        return `
          <div class="chat-conv-item ${isActive}" data-conv-id="${c.id}" onclick="openUserConversation(${c.id})">
            <div class="chat-conv-avatar">${thumbHtml}</div>
            <div class="chat-conv-info">
              <div class="chat-conv-top">
                <span class="chat-conv-name">${escapeHtml(c.subject || 'Support Chat')}</span>
                <span class="chat-conv-time">${timeStr}</span>
              </div>
              <div class="chat-conv-bottom">
                <span class="chat-conv-snippet">${escapeHtml(c.last_message || '...')}</span>
                ${unreadBadge}
              </div>
            </div>
          </div>
        `;
      }).join('');
    }"""

    new_render_conv_list = """    function renderUserChatConvList(convs) {
      const convList = document.getElementById('userChatConvList');
      if (!convs || convs.length === 0) {
        convList.innerHTML = `
          <div style="text-align: center; padding: 3rem 1.5rem; color: var(--text-muted);">
            <i class="fas fa-inbox" style="font-size: 2.2rem; color: #94A3B8; margin-bottom: 0.75rem;"></i>
            <p style="margin: 0; font-size: 0.95rem; font-weight: 600; color: #0F172A;">No active conversations.</p>
            <p style="font-size: 0.82rem; margin-top: 0.35rem; color: var(--text-muted);">Start an inquiry below to chat with SMR Support.</p>
            <button class="btn btn-sm btn-primary" onclick="openNewChatModal()" style="margin-top: 1rem;">
              <i class="fas fa-plus"></i> Start New Inquiry
            </button>
          </div>
        `;
        return;
      }

      convList.innerHTML = convs.map(c => {
        const isActive = Number(c.id) === Number(currentUserChatConvId) ? 'active' : '';
        const timeStr = formatChatTime(c.last_message_at || c.created_at);
        const thumbHtml = c.bike_image 
          ? `<img src="${escapeHtml(c.bike_image)}" alt="Bike" onerror="this.src='/static/images/IMG-20251204-WA0053.jpg'">`
          : `<i class="fas fa-motorcycle" style="color:var(--accent-primary);"></i>`;
        const unreadBadge = c.unread_count > 0 
          ? `<span class="chat-unread-badge">${c.unread_count}</span>` 
          : '';

        const displayTitle = c.bike_title || c.subject || 'Support Chat';
        const pricePill = c.bike_price 
          ? `<span style="font-size:0.75rem; font-weight:700; color:var(--accent-primary); background:#EFF6FF; border:1px solid #BFDBFE; padding:1px 6px; border-radius:4px;">₹${Number(c.bike_price).toLocaleString('en-IN')}</span>` 
          : '';
        const bikeTag = c.bike_id 
          ? `<span style="font-size:0.7rem; color:#64748B; display:inline-flex; align-items:center; gap:3px;"><i class="fas fa-motorcycle" style="color:var(--accent-primary);"></i> Bike #${c.bike_id}</span>` 
          : `<span style="font-size:0.7rem; color:#64748B;"><i class="fas fa-headset"></i> Support</span>`;

        return `
          <div class="chat-conv-item ${isActive}" data-conv-id="${c.id}" onclick="openUserConversation(${c.id})">
            <div class="chat-conv-avatar">${thumbHtml}</div>
            <div class="chat-conv-info">
              <div class="chat-conv-top">
                <span class="chat-conv-name" title="${escapeHtml(displayTitle)}">${escapeHtml(displayTitle)}</span>
                <span class="chat-conv-time">${timeStr}</span>
              </div>
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.25rem;">
                ${bikeTag}
                ${pricePill}
              </div>
              <div class="chat-conv-bottom">
                <span class="chat-conv-snippet">${escapeHtml(c.last_message || '...')}</span>
                ${unreadBadge}
              </div>
            </div>
          </div>
        `;
      }).join('');
    }"""

    content = content.replace(old_render_conv_list, new_render_conv_list)

    # 3. Update loadUserChat to handle URL bike_id and active conversation selection
    old_load_user_chat = """    async function loadUserChat(keepActiveId = null) {
      const convList = document.getElementById('userChatConvList');
      if (!convList) return;
      try {
        const res = await apiRequest('/api/chat/conversations');
        userChatLoadedConvs = res.conversations || [];
        renderUserChatConvList(userChatLoadedConvs);

        const urlParams = new URLSearchParams(window.location.search);
        const urlConv = urlParams.get('conv_id');
        const targetId = keepActiveId || currentUserChatConvId || (urlConv ? parseInt(urlConv, 10) : null);

        if (targetId && userChatLoadedConvs.some(c => Number(c.id) === Number(targetId))) {
          openUserConversation(Number(targetId));
        } else if (userChatLoadedConvs.length > 0 && window.innerWidth > 768 && !currentUserChatConvId) {
          openUserConversation(userChatLoadedConvs[0].id);
        } else if (userChatLoadedConvs.length === 0) {
          currentUserChatConvId = null;
          pauseUserChatPolling();
          const placeholder = document.getElementById('userChatPlaceholder');
          if (placeholder) placeholder.style.display = 'block';
          const header = document.getElementById('userChatHeader');
          if (header) header.style.display = 'none';
          const inputBar = document.getElementById('userChatInputBar');
          if (inputBar) inputBar.style.display = 'none';
          const pinnedBike = document.getElementById('userChatPinnedBike');
          if (pinnedBike) pinnedBike.style.display = 'none';
        }
      } catch (e) {
        convList.innerHTML = `<div style="text-align:center; padding:2.5rem 1rem; color:var(--color-danger);">${escapeHtml(e.message)}</div>`;
      }
    }"""

    new_load_user_chat = """    async function loadUserChat(keepActiveId = null) {
      const convList = document.getElementById('userChatConvList');
      if (!convList) return;
      try {
        const res = await apiRequest('/api/chat/conversations');
        userChatLoadedConvs = res.conversations || [];
        renderUserChatConvList(userChatLoadedConvs);

        const urlParams = new URLSearchParams(window.location.search);
        const urlConv = urlParams.get('conv_id');
        const urlBikeId = urlParams.get('bike_id') || urlParams.get('bikeId');

        let targetId = keepActiveId || currentUserChatConvId;
        if (!targetId && urlConv) {
          targetId = parseInt(urlConv, 10);
        }
        if (!targetId && urlBikeId) {
          const matchedByBike = userChatLoadedConvs.find(c => Number(c.bike_id) === Number(urlBikeId));
          if (matchedByBike) {
            targetId = matchedByBike.id;
          }
        }

        if (targetId && userChatLoadedConvs.some(c => Number(c.id) === Number(targetId))) {
          openUserConversation(Number(targetId));
        } else if (urlBikeId && !userChatLoadedConvs.some(c => Number(c.bike_id) === Number(urlBikeId))) {
          openNewChatModal(urlBikeId);
        } else if (userChatLoadedConvs.length > 0 && window.innerWidth > 768 && !currentUserChatConvId) {
          openUserConversation(userChatLoadedConvs[0].id);
        } else if (userChatLoadedConvs.length === 0) {
          currentUserChatConvId = null;
          pauseUserChatPolling();
          const placeholder = document.getElementById('userChatPlaceholder');
          if (placeholder) placeholder.style.display = 'block';
          const header = document.getElementById('userChatHeader');
          if (header) header.style.display = 'none';
          const inputBar = document.getElementById('userChatInputBar');
          if (inputBar) inputBar.style.display = 'none';
          const pinnedBike = document.getElementById('userChatPinnedBike');
          if (pinnedBike) pinnedBike.style.display = 'none';
        }
      } catch (e) {
        convList.innerHTML = `<div style="text-align:center; padding:2.5rem 1rem; color:var(--color-danger);">${escapeHtml(e.message)}</div>`;
      }
    }"""

    content = content.replace(old_load_user_chat, new_load_user_chat)

    # 4. In openUserConversation, set header and placeholder to bike title
    old_header_name_line = "document.getElementById('userChatHeaderName').innerText = conv.subject || 'SMR Motors Support Team';"
    new_header_name_line = """const chatHeaderTitle = conv.bike_title || conv.subject || 'SMR Motors Support Team';
        document.getElementById('userChatHeaderName').innerText = chatHeaderTitle;
        const chatInputEl = document.getElementById('userChatMessageInput');
        if (chatInputEl) {
          chatInputEl.placeholder = conv.bike_title ? `Ask about ${conv.bike_title}...` : 'Type your message to SMR Support...';
        }"""
    content = content.replace(old_header_name_line, new_header_name_line)

    # 5. In openNewChatModal, prevent duplicate conversations for existing bikes
    old_open_modal_start = """    async function openNewChatModal(prefillBikeId = null) {
      const modal = document.getElementById('new-chat-modal');
      if (!modal) return;"""

    new_open_modal_start = """    async function openNewChatModal(prefillBikeId = null) {
      if (prefillBikeId && userChatLoadedConvs && userChatLoadedConvs.length > 0) {
        const existingConv = userChatLoadedConvs.find(c => Number(c.bike_id) === Number(prefillBikeId));
        if (existingConv) {
          openUserConversation(existingConv.id);
          return;
        }
      }

      const modal = document.getElementById('new-chat-modal');
      if (!modal) return;"""
    content = content.replace(old_open_modal_start, new_open_modal_start)

    # 6. Replace white text inline styles in profile HTML with dark text for light mode
    content = content.replace('color:#FFF;', 'color:#0F172A;')
    content = content.replace('color:#fff;', 'color:#0F172A;')
    content = content.replace('color: #FFF;', 'color: #0F172A;')
    content = content.replace('color: #fff;', 'color: #0F172A;')
    content = content.replace('background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); border-radius:6px; font-size:0.8rem; color:#FCA5A5;', 'background:#FEF2F2; border:1px solid #FECACA; border-radius:6px; font-size:0.8rem; color:#DC2626;')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated profile file successfully:", filepath)

if __name__ == '__main__':
    update_profile_file('my-node-app/templates/profile.html')
    update_profile_file('user/profile.html')
