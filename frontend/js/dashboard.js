"use strict";

(() => {
  const API = window.SkillSwapAPI;
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const state = {
    user: null,
    categories: [],
    skills: [],
    catalog: [],
    requests: [],
    activeExchanges: [],
    history: [],
    notifications: [],
    schedule: [],
    conversations: [],
    selectedExchange: null,
    exchangeFilter: "all",
    month: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    selectedDate: new Date(),
    eventDates: new Set(),
  };
  const dialog = $("#app-dialog");
  const dialogContent = $("#dialog-content");

  const escapeHtml = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[char]));
  const itemsOf = (result) => Array.isArray(result) ? result : result?.items || [];
  const pageQuery = (params = {}) => new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "")
  ).toString();

  function showFlash(message, isError = false) {
    const flash = $("#flash-message");
    flash.textContent = message;
    flash.classList.toggle("error", isError);
    flash.hidden = false;
    window.clearTimeout(showFlash.timeout);
    showFlash.timeout = window.setTimeout(() => { flash.hidden = true; }, 4500);
  }

  function formatDate(value, options = { month: "short", day: "numeric" }) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : new Intl.DateTimeFormat(undefined, options).format(date);
  }

  function setAvatar(element, user) {
    element.replaceChildren();
    const initial = (user.full_name || user.name || user.username || "S").trim().charAt(0).toUpperCase();
    if (!user.profile_image) {
      element.textContent = initial;
      return;
    }
    const image = document.createElement("img");
    image.src = user.profile_image;
    image.alt = "";
    image.referrerPolicy = "no-referrer";
    image.onerror = () => { element.textContent = initial; };
    element.append(image);
  }

  function setProfile(user) {
    state.user = user;
    $("#admin-link").hidden = user.role !== "admin";
    const name = user.full_name || user.name || user.username;
    $("#welcome-name").textContent = name.split(/\s+/)[0] || name;
    $("#side-name").textContent = name;
    $("#side-email").textContent = user.email;
    setAvatar($("#side-avatar"), user);
    setAvatar($("#top-avatar"), user);
    setAvatar($("#profile-avatar-large"), user);
    $("#profile-name").value = name;
    $("#profile-email").value = user.email;
    $("#profile-avatar").value = user.profile_image || "";
    $("#profile-bio").value = user.bio || "";
    $("#profile-location").value = user.location || "";
  }

  function courseArt(skill) {
    const text = `${skill.name} ${skill.category || ""}`.toLowerCase();
    const kind = text.includes("android") || text.includes("mobile") ? "android"
      : text.includes("python") ? "python"
        : text.includes("security") || text.includes("cyber") ? "security" : "general";
    const symbols = { android: "◈", python: "⌘", security: "◇", general: "✦" };
    return `<div class="course-art ${kind}"><span class="art-symbol">${symbols[kind]}</span><span class="course-level">${escapeHtml(skill.experience_level || "Beginner")}</span></div>`;
  }

  function renderSkill(skill, owner = false) {
    return `<article class="course-card">
      ${courseArt(skill)}
      <div class="course-body">
        <h3 title="${escapeHtml(skill.name)}">${escapeHtml(skill.name)}</h3>
        <p class="course-instructor">${escapeHtml(skill.category || "Skill")} · @${escapeHtml(skill.owner_username || "member")}</p>
        <p class="skill-description">${escapeHtml(skill.description || "No description provided.")}</p>
        <div class="course-meta"><span>${escapeHtml(skill.experience_level || "Beginner")}</span><span>${owner ? "Your listing" : "Member listing"}</span></div>
        ${owner
          ? `<div class="skill-actions"><button class="button button-outline course-action" data-action="edit-skill" data-id="${skill.id}">Edit</button><button class="button button-quiet course-action" data-action="delete-skill" data-id="${skill.id}">Delete</button></div>`
          : `<button class="button button-primary course-action" data-action="request" data-id="${skill.id}">Request exchange</button>`}
      </div>
    </article>`;
  }

  function renderCatalog(skills) {
    const container = $("#browse-courses");
    const ownId = state.user.id;
    container.innerHTML = skills.length
      ? skills.map((skill) => renderSkill(skill, skill.owner_id === ownId)).join("")
      : `<div class="empty-state"><strong>No listings found</strong>Try another search or publish a skill listing to get started.<br><button class="button button-primary" data-action="publish">Publish a listing</button></div>`;
  }

  function renderDashboard() {
    const ownSkills = state.skills.filter((skill) => skill.owner_id === state.user.id);
    $("#dashboard-courses").innerHTML = ownSkills.length
      ? ownSkills.slice(0, 3).map((skill) => renderSkill(skill, true)).join("")
      : `<div class="empty-state"><strong>Your learning journey starts here</strong>Publish a skill or course listing to tell the community what you can share.<br><button class="button button-primary" data-action="publish">Publish a listing</button></div>`;

    const upcoming = state.schedule.filter((item) => new Date(item.starts_at) >= new Date()).slice(0, 3);
    $("#assignments-list").innerHTML = upcoming.length
      ? upcoming.map((item) => `<div class="assignment-item"><span class="assignment-dot"></span><div class="assignment-info"><strong>${escapeHtml(item.title)}</strong><small>${formatDate(item.starts_at, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</small></div><span class="assignment-status">Scheduled</span></div>`).join("")
      : `<p class="empty-note">No upcoming meetings. Schedule one from an active exchange.</p>`;

    const stats = [
      [state.skills.filter((skill) => skill.owner_id === state.user.id).length, "Your listings"],
      [state.activeExchanges.length, "Active exchanges"],
      [state.history.filter((exchange) => exchange.status === "completed").length, "Completed exchanges"],
      [state.learningGoals || 0, "Learning goals"],
    ];
    $("#mini-stats").innerHTML = stats.map(([number, label]) => `<div class="mini-stat"><strong>${escapeHtml(number)}</strong><span>${escapeHtml(label)}</span></div>`).join("");

    const posts = state.recentPosts || [];
    $("#resource-grid").innerHTML = posts.length
      ? posts.map((post) => `<article class="resource-card"><div class="resource-art"><span>✦</span></div><div class="resource-body"><h3>@${escapeHtml(post.author)}</h3><p>${escapeHtml(post.content)}</p><small>${formatDate(post.created_at, { month: "short", day: "numeric" })} · ${post.like_count} likes</small></div></article>`).join("")
      : `<div class="empty-state"><strong>No recent community posts</strong>Community updates will appear here when members share them.</div>`;

    const pending = state.requests.filter((item) => item.status === "pending" && item.receiver_id === state.user.id).length;
    const unread = state.notifications.filter((item) => !item.is_read).length;
    const reminders = [];
    if (pending) reminders.push(`<div class="reminder-item"><span class="reminder-icon">⇄</span><div><strong>${pending} pending request${pending === 1 ? "" : "s"}</strong><small>Review your incoming exchange requests.</small></div></div>`);
    if (unread) reminders.push(`<div class="reminder-item"><span class="reminder-icon">♧</span><div><strong>${unread} unread update${unread === 1 ? "" : "s"}</strong><small>See what’s new in your notifications.</small></div></div>`);
    const unreadMessages = state.unreadMessages || 0;
    if (unreadMessages) reminders.push(`<div class="reminder-item"><span class="reminder-icon">◌</span><div><strong>${unreadMessages} unread message${unreadMessages === 1 ? "" : "s"}</strong><small>Catch up with your exchange partners.</small></div></div>`);
    $("#reminders-list").innerHTML = reminders.join("") || `<p class="empty-note">You’re all caught up.</p>`;
    renderProfileOverview();
    renderSchedule();
    renderCalendar();
    updateCounts();
  }

  function renderProfileOverview() {
    const ownSkills = state.skills.filter((skill) => skill.owner_id === state.user.id);
    $("#profile-listings").innerHTML = ownSkills.length
      ? ownSkills.map((skill) => `<div class="assignment-item"><span class="assignment-dot"></span><div class="assignment-info"><strong>${escapeHtml(skill.name)}</strong><small>${escapeHtml(skill.category)} · ${escapeHtml(skill.experience_level)}</small></div></div>`).join("")
      : `<p class="empty-note">You have not published a listing yet.</p>`;
    const exchanges = [...state.activeExchanges, ...state.history].slice(0, 5);
    $("#profile-exchanges").innerHTML = exchanges.length
      ? exchanges.map((exchange) => `<div class="assignment-item"><span class="assignment-dot"></span><div class="assignment-info"><strong>${escapeHtml(skillName(exchange.offered_skill_id))} ⇄ ${escapeHtml(skillName(exchange.requested_skill_id))}</strong><small>${escapeHtml(exchange.status)} · ${exchange.duration_days} days</small></div></div>`).join("")
      : `<p class="empty-note">Your accepted exchange history will appear here.</p>`;
  }

  function setCounts() {
    const pending = state.requests.filter((item) => item.status === "pending" && item.receiver_id === state.user.id).length;
    const unread = state.notifications.filter((item) => !item.is_read).length;
    const unreadMessages = state.unreadMessages || 0;
    $("#exchange-count").textContent = pending;
    $("#exchange-count").hidden = !pending;
    $("#notification-count").textContent = unread;
    $("#notification-count").hidden = !unread;
    $("#top-unread-dot").hidden = !unread;
    const messagesNav = $('.nav-link[data-view="messages"]');
    let messageCount = $("#message-count");
    if (!messageCount && unreadMessages) {
      messageCount = document.createElement("span");
      messageCount.className = "nav-count";
      messageCount.id = "message-count";
      messagesNav.append(messageCount);
    }
    if (messageCount) {
      messageCount.textContent = unreadMessages;
      messageCount.hidden = !unreadMessages;
    }
  }

  function updateCounts() {
    setCounts();
  }

  async function loadDashboardData() {
    const [
      profile, skillsResult, postsResult, activeResult, historyResult,
      receivedResult, sentResult, notificationResult, scheduleResult,
      goalsResult, messagesResult
    ] = await Promise.all([
      API.profile(),
      API.skills({ page_size: 100 }),
      API.posts({ page: 1, page_size: 3 }),
      API.exchanges("/active?page_size=100"),
      API.exchanges("/history?page_size=100"),
      API.exchanges("/requests/received?page_size=100"),
      API.exchanges("/requests/sent?page_size=100"),
      API.notifications({ page: 1, page_size: 100 }),
      API.request("/api/schedule?page_size=100"),
      API.request("/api/users/me/learning-skills?page_size=100"),
      API.request("/api/messages/unread-count"),
    ]);
    setProfile(profile);
    state.skills = itemsOf(skillsResult);
    state.catalog = state.skills;
    state.recentPosts = itemsOf(postsResult);
    state.activeExchanges = itemsOf(activeResult);
    state.history = itemsOf(historyResult);
    state.requests = [
      ...itemsOf(receivedResult).map((item) => ({ ...item, incoming: true })),
      ...itemsOf(sentResult).map((item) => ({ ...item, incoming: false })),
    ];
    state.notifications = itemsOf(notificationResult);
    state.schedule = itemsOf(scheduleResult);
    state.learningGoals = goalsResult.total;
    state.unreadMessages = messagesResult.unread_count;
    state.conversations = [];
    renderDashboard();
  }

  async function loadCategories() {
    const result = await API.categories({ page_size: 100 });
    state.categories = itemsOf(result);
    const select = $("#category-filter");
    select.value = "";
    state.categories.forEach((category) => {
      const option = document.createElement("option");
      option.value = category.name;
      option.textContent = category.name;
      select.append(option);
    });
  }

  async function loadCourses(search = "", category = "") {
    const container = $("#browse-courses");
    container.innerHTML = `<div class="loading-card">Finding community listings...</div>`;
    try {
      const result = await API.skills({ q: search.trim(), category, page_size: 100 });
      state.catalog = itemsOf(result);
      renderCatalog(state.catalog);
    } catch (error) {
      container.innerHTML = `<div class="empty-state"><strong>Listings could not be loaded</strong>${escapeHtml(error.message)}</div>`;
    }
  }

  function partnerName(exchange) {
    const partnerId = exchange.requester_id === state.user.id ? exchange.receiver_id : exchange.requester_id;
    const skillId = exchange.requester_id === state.user.id ? exchange.requested_skill_id : exchange.offered_skill_id;
    const skill = state.skills.find((item) => item.id === skillId);
    return skill?.owner_username || `Member ${partnerId}`;
  }

  function skillName(skillId) {
    return state.skills.find((skill) => skill.id === skillId)?.name || "Skill";
  }

  function renderExchangeItem(item) {
    if (item.kind === "request") {
      const partner = item.incoming
        ? state.skills.find((skill) => skill.id === item.offered_skill_id)?.owner_username || `Member ${item.requester_id}`
        : state.skills.find((skill) => skill.id === item.requested_skill_id)?.owner_username || `Member ${item.receiver_id}`;
      const actions = item.status !== "pending" ? `<span class="status-pill ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span>`
        : item.proposed_by_id !== state.user.id
          ? `<button class="button button-primary button-small" data-action="accept" data-id="${item.id}">Accept</button><button class="button button-quiet button-small" data-action="counter" data-id="${item.id}">Counter</button><button class="button button-quiet button-small" data-action="reject" data-id="${item.id}">Decline</button>`
          : item.requester_id === state.user.id
            ? `<button class="button button-quiet button-small" data-action="cancel-request" data-id="${item.id}">Cancel</button><span class="status-pill pending">Waiting</span>`
            : `<span class="status-pill pending">Waiting for the other member</span>`;
      return `<article class="exchange-card"><div class="exchange-main"><h3>${item.incoming ? "From" : "To"} ${escapeHtml(partner)} · ${escapeHtml(skillName(item.offered_skill_id))} ⇄ ${escapeHtml(skillName(item.requested_skill_id))}</h3><p>${item.duration_days} day proposal · Course details only · ₹49 per user stated fee (not collected)</p><small>${formatDate(item.created_at, { month: "short", day: "numeric", year: "numeric" })}</small></div><div class="exchange-actions">${actions}</div></article>`;
    }
    const actions = item.status === "active"
      ? `<button class="button button-quiet button-small" data-action="message" data-id="${item.id}">Message</button><button class="button button-quiet button-small" data-action="schedule" data-id="${item.id}">Schedule</button><button class="button button-quiet button-small" data-action="complete" data-id="${item.id}">Complete</button><button class="button button-quiet button-small" data-action="cancel-active" data-id="${item.id}">Cancel</button>`
      : `<span class="status-pill ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span>`;
    return `<article class="exchange-card"><div class="exchange-main"><h3>Exchange with ${escapeHtml(partnerName(item))} · ${escapeHtml(skillName(item.offered_skill_id))} ⇄ ${escapeHtml(skillName(item.requested_skill_id))}</h3><p>${item.duration_days} days · ${item.status === "active" ? `${item.remaining_days} days remaining` : "Exchange history"} · Details only</p><small>${formatDate(item.start_date, { month: "short", day: "numeric", year: "numeric" })} – ${formatDate(item.end_date, { month: "short", day: "numeric", year: "numeric" })}</small></div><div class="exchange-actions">${actions}</div></article>`;
  }

  function renderExchanges() {
    const requests = state.requests.filter((item) => item.status === "pending").map((item) => ({ ...item, kind: "request" }));
    let exchanges = [...state.activeExchanges.map((item) => ({ ...item, kind: "exchange" })), ...state.history.map((item) => ({ ...item, kind: "exchange" }))];
    let items = [...requests, ...exchanges];
    if (state.exchangeFilter === "pending") items = requests;
    if (state.exchangeFilter === "active") items = exchanges.filter((item) => item.status === "active");
    if (state.exchangeFilter === "history") items = exchanges.filter((item) => item.status !== "active");
    $("#exchange-list").innerHTML = items.length
      ? items.map(renderExchangeItem).join("")
      : `<div class="empty-state"><strong>No ${state.exchangeFilter === "all" ? "" : `${state.exchangeFilter} `}exchanges yet</strong>Find a community listing and send a duration proposal to get started.</div>`;
  }

  async function loadExchanges() {
    try {
      const [received, sent, active, history] = await Promise.all([
        API.exchanges("/requests/received?page_size=100"),
        API.exchanges("/requests/sent?page_size=100"),
        API.exchanges("/active?page_size=100"),
        API.exchanges("/history?page_size=100"),
      ]);
      state.requests = [
        ...itemsOf(received).map((item) => ({ ...item, incoming: true })),
        ...itemsOf(sent).map((item) => ({ ...item, incoming: false })),
      ];
      state.activeExchanges = itemsOf(active);
      state.history = itemsOf(history);
      renderExchanges();
      await loadConversations();
      updateCounts();
    } catch (error) {
      $("#exchange-list").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    }
  }

  async function loadConversations() {
    const result = await API.request("/api/messages?page_size=100");
    state.conversations = itemsOf(result);
    const list = $("#conversation-list");
    list.innerHTML = state.conversations.length
      ? state.conversations.map((item) => `<button class="conversation-option ${state.selectedExchange === item.exchange_id ? "active" : ""}" data-action="open-conversation" data-id="${item.exchange_id}"><strong>${escapeHtml(item.partner_name)}</strong><small>${escapeHtml(item.status)} · ${item.unread_count ? `${item.unread_count} unread` : escapeHtml(item.last_message?.body || "Start a conversation")}</small></button>`).join("")
      : `<p class="empty-note">Your exchange conversations will appear here after an exchange is accepted.</p>`;
    state.unreadMessages = state.conversations.reduce((total, item) => total + item.unread_count, 0);
    updateCounts();
    if (!state.selectedExchange && state.conversations.length) await selectConversation(state.conversations[0].exchange_id);
  }

  async function selectConversation(exchangeId) {
    state.selectedExchange = Number(exchangeId);
    const conversation = state.conversations.find((item) => item.exchange_id === state.selectedExchange);
    $("#conversation-head").textContent = conversation
      ? `${conversation.partner_name} · ${conversation.status} exchange`
      : "Exchange conversation";
    $("#message-input").disabled = false;
    $("#message-send").disabled = false;
    $$(".conversation-option").forEach((item) => item.classList.toggle("active", Number(item.dataset.id) === state.selectedExchange));
    try {
      const result = await API.request(`/api/messages?exchange_id=${state.selectedExchange}&page_size=100`);
      const messages = itemsOf(result);
      $("#message-feed").innerHTML = messages.length
        ? messages.map((message) => `<div class="message-bubble ${message.sender_id === state.user.id ? "mine" : ""}"><small>${escapeHtml(message.sender_name)} · ${formatDate(message.created_at, { hour: "numeric", minute: "2-digit" })}</small>${escapeHtml(message.body)}</div>`).join("")
        : `<div class="message-empty">Thoughtful exchanges start with a hello.</div>`;
      $("#message-feed").scrollTop = $("#message-feed").scrollHeight;
      await refreshUnread();
      const conversationListItem = state.conversations.find((item) => item.exchange_id === state.selectedExchange);
      if (conversationListItem) conversationListItem.unread_count = 0;
      updateCounts();
    } catch (error) {
      showFlash(error.message, true);
    }
  }

  async function refreshUnread() {
    const messages = await API.request("/api/messages/unread-count");
    state.unreadMessages = messages.unread_count;
    const list = await API.notifications({ page: 1, page_size: 100 });
    state.notifications = itemsOf(list);
    updateCounts();
  }

  async function loadNotifications() {
    try {
      const result = await API.notifications({ page: 1, page_size: 100 });
      state.notifications = itemsOf(result);
      $("#notification-list").innerHTML = state.notifications.length
        ? state.notifications.map((item) => `<article class="notification-card ${item.is_read ? "" : "unread"}"><span class="notification-symbol">✦</span><div class="notification-text"><strong>${escapeHtml(item.type.replaceAll("_", " "))}</strong><p>${escapeHtml(item.message)}</p><small>${formatDate(item.created_at, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</small></div>${item.is_read ? "" : `<button data-action="read-notification" data-id="${item.id}">Mark read</button>`}</article>`).join("")
        : `<div class="empty-state"><strong>All quiet for now</strong>Updates about exchanges, messages, and schedules will appear here.</div>`;
      updateCounts();
    } catch (error) {
      $("#notification-list").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    }
  }

  async function loadSchedule(monthOnly = false) {
    try {
      const month = monthOnly
        ? `&month=${state.month.getFullYear()}-${String(state.month.getMonth() + 1).padStart(2, "0")}`
        : "";
      const result = await API.request(`/api/schedule?page_size=100${month}`);
      if (monthOnly) {
        state.eventDates = new Set(itemsOf(result).map((item) => new Date(item.starts_at).getDate()));
        renderCalendar();
      } else {
        state.schedule = itemsOf(result);
        renderSchedule();
        renderCalendar();
      }
    } catch (error) {
      $("#schedule-list").innerHTML = `<p class="schedule-empty">${escapeHtml(error.message)}</p>`;
    }
  }

  function renderSchedule() {
    const upcoming = state.schedule.filter((item) => new Date(item.starts_at) >= new Date()).slice(0, 4);
    $("#schedule-list").innerHTML = upcoming.length
      ? upcoming.map((item) => `<div class="schedule-item"><span class="schedule-time">${formatDate(item.starts_at, { hour: "numeric", minute: "2-digit" })}</span><div><strong>${escapeHtml(item.title)}</strong><small>${formatDate(item.starts_at, { month: "short", day: "numeric" })}</small></div></div>`).join("")
      : `<p class="schedule-empty">No sessions scheduled yet. Accepted exchanges are a good time to plan one.</p>`;
  }

  function renderCalendar() {
    const year = state.month.getFullYear();
    const month = state.month.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const days = new Date(year, month + 1, 0).getDate();
    const previousDays = new Date(year, month, 0).getDate();
    $("#calendar-month").textContent = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" }).format(state.month);
    const labels = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((day) => `<span class="calendar-day-label">${day}</span>`);
    const dates = [];
    for (let index = 0; index < 42; index++) {
      let day = index - firstDay + 1;
      let muted = false;
      let dateYear = year;
      let dateMonth = month;
      if (day < 1) {
        day = previousDays + day;
        muted = true;
        if (--dateMonth < 0) { dateMonth = 11; dateYear--; }
      } else if (day > days) {
        day -= days;
        muted = true;
        if (++dateMonth > 11) { dateMonth = 0; dateYear++; }
      }
      const selected = sameCalendarDay(dateYear, dateMonth, day);
      const hasEvent = !muted && state.eventDates.has(day);
      const iso = `${dateYear}-${String(dateMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      dates.push(`<button class="calendar-date ${muted ? "muted" : ""} ${selected ? "selected" : ""} ${hasEvent ? "has-event" : ""}" data-date="${iso}" aria-label="${iso}">${day}</button>`);
    }
    $("#calendar-grid").innerHTML = labels.concat(dates).join("");
  }

  function sameCalendarDay(year, month, day) {
    return state.selectedDate.getFullYear() === year && state.selectedDate.getMonth() === month && state.selectedDate.getDate() === day;
  }

  function setView(view) {
    const panel = $(`#view-${view}`);
    if (!panel) return;
    $$(".view-panel").forEach((item) => item.classList.toggle("active", item === panel));
    $$(".nav-link[data-view]").forEach((item) => item.classList.toggle("active", item.dataset.view === view));
    $("#view-title").textContent = ({ courses: "Skills & Courses", exchanges: "Exchange Requests", profile: "My Profile", settings: "Settings", help: "Help & Support" })[view] || view.charAt(0).toUpperCase() + view.slice(1);
    if (view === "courses") loadCourses($("#course-search").value, $("#category-filter").value);
    if (view === "exchanges") loadExchanges();
    if (view === "messages") loadConversations();
    if (view === "notifications") loadNotifications();
    closeMobileMenu();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function closeDialog() {
    if (dialog.open) dialog.close();
    dialogContent.replaceChildren();
  }

  function openDialog(markup, onSubmit) {
    dialogContent.innerHTML = markup;
    dialog.showModal();
    $(".dialog-close", dialogContent).addEventListener("click", closeDialog);
    const form = $(".dialog-form", dialogContent);
    if (form && onSubmit) form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submit = $('button[type="submit"]', form);
      const label = submit.textContent;
      submit.disabled = true;
      submit.textContent = "Saving...";
      try {
        await onSubmit(new FormData(form));
        closeDialog();
      } catch (error) {
        let errorNode = $(".dialog-error", form);
        if (!errorNode) {
          errorNode = document.createElement("p");
          errorNode.className = "form-error dialog-error";
          errorNode.setAttribute("role", "alert");
          form.prepend(errorNode);
        }
        errorNode.textContent = error.message;
        submit.disabled = false;
        submit.textContent = label;
      }
    });
  }

  function openSkillDialog(skill = null) {
    const categories = state.categories.map((category) => `<option value="${category.id}" ${skill?.category_id === category.id ? "selected" : ""}>${escapeHtml(category.name)}</option>`).join("");
    const levels = ["Beginner", "Intermediate", "Advanced", "Expert"].map((level) => `<option ${skill?.experience_level === level ? "selected" : ""}>${level}</option>`).join("");
    openDialog(`<div class="dialog-heading"><div><span class="eyebrow">SHARE WHAT YOU KNOW</span><h2>${skill ? "Edit listing" : "Publish a listing"}</h2><p>Share course details you are authorized to describe. Do not upload course files or credentials.</p></div><button class="dialog-close" type="button" aria-label="Close">×</button></div>
      <form class="dialog-form">
        <label for="listing-name">Skill or course title</label><input id="listing-name" name="name" minlength="1" maxlength="120" required value="${escapeHtml(skill?.name || "")}">
        <label for="listing-description">Description</label><textarea id="listing-description" name="description" maxlength="2000" required>${escapeHtml(skill?.description || "")}</textarea>
        <label for="listing-category">Category</label><select id="listing-category" name="category_id" required>${categories}</select>
        <label for="listing-level">Experience level</label><select id="listing-level" name="experience_level">${levels}</select>
        <div class="dialog-note">This listing exchanges details only. SkillSwap does not distribute course media or verify external purchases. ₹49 per user is informational; no payment is processed.</div>
        <button class="button button-primary" type="submit">${skill ? "Save listing" : "Publish listing"}</button>
      </form>`, async (formData) => {
      const body = Object.fromEntries(formData.entries());
      body.category_id = Number(body.category_id);
      const updated = skill
        ? await API.updateSkill(skill.id, body)
        : await API.createSkill(body);
      showFlash(skill ? "Listing updated." : "Your listing is live.");
      await reloadData();
    });
  }

  function openExchangeDialog(skillId) {
    const skill = state.catalog.find((item) => item.id === Number(skillId));
    if (!skill) return;
    const mine = state.skills.filter((item) => item.owner_id === state.user.id);
    if (!mine.length) {
      showFlash("Publish a skill or course listing before requesting an exchange.", true);
      openSkillDialog();
      return;
    }
    openDialog(`<div class="dialog-heading"><div><span class="eyebrow">START AN EXCHANGE</span><h2>Request ${escapeHtml(skill.name)}</h2><p>Choose your listing and propose a duration. The other member must approve.</p></div><button class="dialog-close" type="button" aria-label="Close">×</button></div>
      <form class="dialog-form"><label for="offered-skill">Your listing to offer</label><select id="offered-skill" name="offered_skill_id" required>${mine.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("")}</select>
      <label for="exchange-duration">Exchange duration (days)</label><input id="exchange-duration" name="duration_days" type="number" min="1" max="365" value="14" required>
      <div class="dialog-note">Only listing details are exchanged, never course files or account access. ₹49 per user is not collected by this app.</div><button class="button button-primary" type="submit">Send request</button></form>`, async (formData) => {
      await API.request("/api/exchanges/requests", {
        method: "POST",
        body: JSON.stringify({
          receiver_id: skill.owner_id,
          offered_skill_id: Number(formData.get("offered_skill_id")),
          requested_skill_id: skill.id,
          duration_days: Number(formData.get("duration_days")),
        }),
      });
      showFlash("Exchange request sent.");
      await reloadData();
    });
  }

  function openScheduleDialog(exchangeId) {
    const minimum = new Date(Date.now() + 60_000).toISOString().slice(0, 16);
    openDialog(`<div class="dialog-heading"><div><span class="eyebrow">MAKE A PLAN</span><h2>Schedule an exchange meeting</h2><p>Choose a time during your active exchange.</p></div><button class="dialog-close" type="button" aria-label="Close">×</button></div>
      <form class="dialog-form"><label for="meeting-title">Meeting title</label><input id="meeting-title" name="title" minlength="3" maxlength="120" required value="SkillSwap session">
      <label for="meeting-date">Date and time</label><input id="meeting-date" name="starts_at" type="datetime-local" min="${minimum}" required>
      <button class="button button-primary" type="submit">Add to schedule</button></form>`, async (formData) => {
      const startsAt = new Date(formData.get("starts_at"));
      if (Number.isNaN(startsAt.getTime()) || startsAt <= new Date()) throw new Error("Choose a date and time in the future.");
      await API.request("/api/schedule", {
        method: "POST",
        body: JSON.stringify({ exchange_id: Number(exchangeId), title: formData.get("title"), starts_at: startsAt.toISOString() }),
      });
      showFlash("Meeting added to your schedule.");
      await reloadData();
    });
  }

  function openCounterDialog(requestId) {
    openDialog(`<div class="dialog-heading"><div><span class="eyebrow">EXCHANGE REQUEST</span><h2>Counter the duration</h2><p>Propose a new duration from 1 to 365 days. The other participant must approve it.</p></div><button class="dialog-close" type="button" aria-label="Close">×</button></div>
      <form class="dialog-form"><label for="counter-days">New duration (days)</label><input id="counter-days" name="duration_days" type="number" min="1" max="365" value="14" required><button class="button button-primary" type="submit">Send counter-offer</button></form>`, async (formData) => {
      await API.request(`/api/exchanges/requests/${requestId}/counter`, {
        method: "POST", body: JSON.stringify({ duration_days: Number(formData.get("duration_days")) }),
      });
      showFlash("Counter-offer sent.");
      await reloadData();
    });
  }

  async function handleAction(button) {
    const action = button.dataset.action;
    const id = Number(button.dataset.id);
    try {
      if (action === "browse") setView("courses");
      if (action === "publish") openSkillDialog();
      if (action === "request") openExchangeDialog(id);
      if (action === "edit-skill") {
        const skill = state.skills.find((item) => item.id === id);
        if (skill) openSkillDialog(skill);
      }
      if (action === "delete-skill") {
        const skill = state.skills.find((item) => item.id === id);
        if (skill && window.confirm(`Delete your listing “${skill.name}”?`)) {
          await API.deleteSkill(id);
          showFlash("Listing deleted.");
          await reloadData();
        }
      }
      if (action === "accept" || action === "reject" || action === "cancel-request") {
        const suffix = action === "cancel-request" ? "cancel" : action;
        await API.exchanges(`/requests/${id}/${suffix}`, { method: "POST" });
        showFlash(`Exchange request ${suffix === "cancel" ? "cancelled" : suffix === "reject" ? "declined" : "accepted"}.`);
        await reloadData();
      }
      if (action === "counter") openCounterDialog(id);
      if (action === "message") {
        setView("messages");
        await selectConversation(id);
      }
      if (action === "open-conversation") await selectConversation(id);
      if (action === "schedule") openScheduleDialog(id);
      if (action === "complete") {
        if (window.confirm("Mark this exchange as completed?")) {
          await API.exchanges(`/${id}/complete`, { method: "POST" });
          showFlash("Exchange marked as completed.");
          await reloadData();
        }
      }
      if (action === "cancel-active" && window.confirm("Cancel this active exchange?")) {
        await API.exchanges(`/${id}/cancel`, { method: "POST" });
        showFlash("Exchange cancelled.");
        await reloadData();
      }
      if (action === "read-notification") {
        await API.request(`/api/notifications/${id}/read`, { method: "PATCH" });
        await loadNotifications();
      }
      if (action === "search-category") {
        $("#category-filter").value = button.dataset.category;
        setView("courses");
      }
      if (action === "search-person") {
        $("#global-search").value = button.dataset.username;
        setView("courses");
        await runGlobalSearch(button.dataset.username);
      }
    } catch (error) {
      showFlash(error.message, true);
    }
  }

  async function reloadData() {
    await loadDashboardData();
    if ($("#view-exchanges").classList.contains("active")) await loadExchanges();
    if ($("#view-messages").classList.contains("active")) await loadConversations();
  }

  async function runGlobalSearch(query) {
    const container = $("#browse-courses");
    container.innerHTML = `<div class="loading-card">Searching SkillSwap...</div>`;
    try {
      const result = await API.search({ q: query.trim(), page_size: 100 });
      const results = itemsOf(result);
      container.innerHTML = results.length ? results.map((item) => {
        if (item.type === "skill") {
          const skill = state.skills.find((entry) => entry.id === item.id)
            || { ...item, owner_username: "", experience_level: item.experience_level };
          return renderSkill(skill, skill.owner_id === state.user.id);
        }
        if (item.type === "user") {
          return `<article class="course-card search-result"><div class="course-body"><span class="eyebrow">MEMBER</span><h3>${escapeHtml(item.name || item.username)}</h3><p class="course-instructor">@${escapeHtml(item.username)}</p><button class="button button-outline course-action" data-action="search-person" data-username="${escapeHtml(item.username)}">Find their listings</button></div></article>`;
        }
        if (item.type === "category") {
          return `<article class="course-card search-result"><div class="course-body"><span class="eyebrow">CATEGORY</span><h3>${escapeHtml(item.name)}</h3><button class="button button-outline course-action" data-action="search-category" data-category="${escapeHtml(item.name)}">Browse category</button></div></article>`;
        }
        return "";
      }).join("") : `<div class="empty-state"><strong>No results found</strong>Try another course, skill, member, or category.</div>`;
    } catch (error) {
      container.innerHTML = `<div class="empty-state"><strong>Search unavailable</strong>${escapeHtml(error.message)}</div>`;
    }
  }

  function closeMobileMenu() {
    $("#sidebar").classList.remove("open");
    $("#mobile-overlay").classList.remove("show");
  }

  function bindEvents() {
    document.addEventListener("click", async (event) => {
      const action = event.target.closest("[data-action]");
      if (action) {
        await handleAction(action);
        return;
      }
      const view = event.target.closest("[data-view]");
      if (view) setView(view.dataset.view);
      const dateButton = event.target.closest(".calendar-date");
      if (dateButton) {
        const [year, month, day] = dateButton.dataset.date.split("-").map(Number);
        state.selectedDate = new Date(year, month - 1, day);
        if (state.selectedDate.getMonth() !== state.month.getMonth()) {
          state.month = new Date(year, month - 1, 1);
          loadSchedule(true);
        } else renderCalendar();
      }
    });
    $("#calendar-prev").addEventListener("click", () => {
      state.month = new Date(state.month.getFullYear(), state.month.getMonth() - 1, 1);
      loadSchedule(true);
    });
    $("#calendar-next").addEventListener("click", () => {
      state.month = new Date(state.month.getFullYear(), state.month.getMonth() + 1, 1);
      loadSchedule(true);
    });
    $("#course-search").addEventListener("input", debounce(() => loadCourses($("#course-search").value, $("#category-filter").value), 250));
    $("#category-filter").addEventListener("change", () => loadCourses($("#course-search").value, $("#category-filter").value));
    $("#global-search").addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        setView("courses");
        runGlobalSearch(event.target.value);
      }
    });
    document.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        $("#global-search").focus();
      }
    });
    $$(".filter-chip").forEach((button) => button.addEventListener("click", () => {
      state.exchangeFilter = button.dataset.filter;
      $$(".filter-chip").forEach((chip) => chip.classList.toggle("selected", chip === button));
      renderExchanges();
    }));
    $("#message-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const input = $("#message-input");
      const body = input.value.trim();
      if (!body || !state.selectedExchange) return;
      $("#message-send").disabled = true;
      try {
        await API.request("/api/messages", {
          method: "POST",
          body: JSON.stringify({ exchange_id: state.selectedExchange, body }),
        });
        input.value = "";
        await selectConversation(state.selectedExchange);
        await loadNotifications();
      } catch (error) {
        showFlash(error.message, true);
      } finally {
        $("#message-send").disabled = false;
      }
    });
    $("#profile-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const submit = $('button[type="submit"]', form);
      submit.disabled = true;
      try {
        const data = Object.fromEntries(new FormData(form).entries());
        await API.updateProfile(data);
        state.user = await API.profile();
        setProfile(state.user);
        showFlash("Profile saved.");
      } catch (error) {
        showFlash(error.message, true);
      } finally {
        submit.disabled = false;
      }
    });
    $("#logout-button").addEventListener("click", async () => {
      const button = $("#logout-button");
      button.disabled = true;
      try {
        await API.logout();
      } catch (error) {
        button.disabled = false;
        showFlash(`Logout could not be confirmed by the server: ${error.message}`, true);
      }
    });
    $("#menu-button").addEventListener("click", () => {
      $("#sidebar").classList.add("open");
      $("#mobile-overlay").classList.add("show");
    });
    $("#mobile-overlay").addEventListener("click", closeMobileMenu);
    $("#sidebar-collapse").addEventListener("click", (event) => {
      const collapsed = $(".app-shell").classList.toggle("sidebar-collapsed");
      event.currentTarget.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
      event.currentTarget.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
    });
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeDialog();
    });
  }

  function debounce(callback, wait) {
    let timeout;
    return (...args) => {
      window.clearTimeout(timeout);
      timeout = window.setTimeout(() => callback(...args), wait);
    };
  }

  async function init() {
    bindEvents();
    try {
      const user = await window.SkillSwapAuth.ready;
      if (!user) return;
      await Promise.all([loadCategories(), loadDashboardData()]);
      await loadSchedule(true);
      await loadCourses();
      await loadExchanges();
    } catch (error) {
      showFlash(error.message || "The dashboard could not be loaded.", true);
    }
  }

  init();
})();
