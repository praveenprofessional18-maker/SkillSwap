"use strict";

const API = window.SkillSwapAPI;
const UI = window.SkillSwapUI;
const API_ORIGIN = window.SkillSwapConfig.API_BASE_URL;
const byId = (id) => document.getElementById(id);
const make = UI.element.bind(UI);
const appendText = (node, tag, text, className) => node.append(make(tag, text, className));

async function loadDashboard() {
  const [profile, skills, posts, active, unread] = await Promise.all([
    API.me(),     API.skills({ page_size: 100 }), API.posts({ page_size: 5 }),
    API.exchanges("/active"), API.request("/api/notifications/unread-count")
  ]);
  byId("welcome").textContent = `Welcome, ${profile.full_name || profile.username}`;
  [
    ["skills-count", skills.total], ["posts-count", posts.total],
    ["exchanges-count", active.total], ["unread-count", unread.unread_count]
  ].forEach(([id, value]) => { byId(id).textContent = String(value); });
  const list = byId("recent-posts");
  list.replaceChildren();
  (posts.items || []).forEach((post) => {
    const item = make("article", undefined, "content-card");
    appendText(item, "p", post.content);
    appendText(item, "small", `@${post.author} · ${new Date(post.created_at).toLocaleDateString()}`);
    list.append(item);
  });
  if (!posts.items.length) UI.message(list, "No community posts yet. Share the first one.");
}

async function loadProfile() {
  const profile = await API.profile();
  ["full_name", "bio", "location", "experience_level", "availability", "language"].forEach((key) => {
    const field = byId(key);
    if (field) field.value = profile[key] || "";
  });
  byId("profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    await API.updateProfile(data);
    UI.toast("Profile saved.");
  });
}

async function loadSkills() {
  const categories = (await API.categories({ page_size: 100 })).items;
  const select = byId("skill-category");
  const learningCategory = byId("learning-category");
  categories.forEach((category) => {
    const option = make("option", category.name);
    option.value = category.id;
    select.append(option);
    const learningOption = make("option", category.name);
    learningOption.value = category.id;
    learningCategory.append(learningOption);
  });
  const form = byId("skill-form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    data.category_id = Number(data.category_id);
    await API.createSkill(data);
    form.reset();
    UI.toast("Skill added.");
    await renderSkills();
  });
  byId("learning-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    data.category_id = data.category_id ? Number(data.category_id) : null;
    await API.request("/api/users/me/learning-skills", {
      method: "POST", body: JSON.stringify(data)
    });
    event.currentTarget.reset();
    await renderLearningSkills();
  });
  async function renderLearningSkills() {
    const container = byId("learning-skills");
    container.replaceChildren();
    const result = await API.request("/api/users/me/learning-skills");
    result.items.forEach((item) => {
      const card = UI.card(item.skill_name, `${item.level} · learning goal`);
      const remove = make("button", "Remove goal", "button button-outline");
      remove.addEventListener("click", async () => {
        await API.request(`/api/users/me/learning-skills/${item.id}`, { method: "DELETE" });
        await renderLearningSkills();
      });
      card.append(remove);
      container.append(card);
    });
    if (!result.items.length) UI.message(container, "Add a learning goal to help others find you.");
  }
  async function renderSkills() {
    const container = byId("skills-list");
    container.replaceChildren();
    const currentUser = await API.me();
    const params = { page_size: 100, q: byId("skill-filter").value };
    const category = new URLSearchParams(window.location.search).get("category");
    if (category) params.category = category;
    const items = (await API.skills(params)).items;
    const mine = items.filter((skill) => skill.owner_id === currentUser.id);
    const others = items.filter((skill) => skill.owner_id !== currentUser.id);
    [...mine, ...others].forEach((skill) => {
      const card = UI.card(skill.name, `${skill.category} · ${skill.experience_level} · @${skill.owner_username}`);
      appendText(card, "p", skill.description);
      if (skill.owner_id === currentUser.id) {
        const edit = make("button", "Edit", "button button-outline");
        edit.type = "button";
        edit.addEventListener("click", async () => {
          const description = window.prompt("Update the skill description:", skill.description);
          if (description === null) return;
          await API.updateSkill(skill.id, {
            name: skill.name, category_id: skill.category_id,
            experience_level: skill.experience_level, description
          });
          UI.toast("Skill updated.");
          await renderSkills();
        });
        const remove = make("button", "Delete", "button button-danger");
        remove.type = "button";
        remove.addEventListener("click", async () => {
          if (!window.confirm(`Delete ${skill.name}?`)) return;
          await API.deleteSkill(skill.id);
          await renderSkills();
        });
        card.append(edit, remove);
      }
      container.append(card);
    });
    if (!items.length) UI.message(container, "No skills found. Add one to get started.");
  }
  byId("skill-filter").addEventListener("input", () => renderSkills().catch((error) => UI.toast(error.message, true)));
  await renderSkills();
  await renderLearningSkills();
}

async function loadCommunity() {
  const currentUser = await API.me();
  let page = 1;
  const form = byId("post-form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const content = new FormData(form).get("content").toString().trim();
    const file = byId("post-media").files[0];
    if (!content) return UI.toast("Write something before posting.", true);
    const post = await API.createPost({ content });
    if (file) await API.uploadPostMedia(post.id, file);
    form.reset();
    await renderPosts();
  });
  async function renderPosts() {
    const container = byId("posts-list");
    container.replaceChildren();
    const response = await API.posts({ page, page_size: 10, q: byId("post-search").value });
    byId("posts-page-label").textContent = `Page ${response.page} of ${Math.max(1, Math.ceil(response.total / response.page_size))}`;
    byId("posts-previous").disabled = page <= 1;
    byId("posts-next").disabled = page * response.page_size >= response.total;
    for (const post of response.items) {
      const card = make("article", undefined, "content-card post-card");
      appendText(card, "p", post.content);
      appendText(card, "small", `@${post.author} · ${new Date(post.created_at).toLocaleString()}`);
      for (const media of post.media) {
        const source = `${API_ORIGIN}${media.url}`;
        if (media.media_type === "image") {
          const image = make("img", undefined, "post-media");
          image.src = source;
          image.alt = "Post attachment";
          card.append(image);
        } else {
          const video = make("video", undefined, "post-media");
          video.src = source;
          video.controls = true;
          video.preload = "metadata";
          card.append(video);
        }
      }
      const actions = make("div", undefined, "card-actions");
      const like = make("button", `${post.liked ? "Unlike" : "Like"} · ${post.like_count}`, "button button-outline");
      like.type = "button";
      like.addEventListener("click", async () => { await API.toggleLike(post.id, !post.liked); await renderPosts(); });
      const comment = make("button", `Comment · ${post.comment_count}`, "button button-outline");
      comment.type = "button";
      comment.addEventListener("click", async () => {
        const content = window.prompt("Add a comment:");
        if (content && content.trim()) {
          await API.addComment(post.id, content.trim());
          await renderPosts();
        }
      });
      const report = make("button", "Report", "button button-outline");
      report.addEventListener("click", async () => {
        const reason = window.prompt("Why are you reporting this post?");
        if (reason && reason.trim()) {
          await API.request(`/api/posts/${post.id}/report`, {
            method: "POST", body: JSON.stringify({ reason: reason.trim() })
          });
          UI.toast("Report submitted for review.");
        }
      });
      actions.append(like, comment, report);
      if (post.author_id === currentUser.id) {
        const edit = make("button", "Edit post", "button button-outline");
        edit.addEventListener("click", async () => {
          const content = window.prompt("Edit your post:", post.content);
          if (content && content.trim()) {
            await API.request(`/api/posts/${post.id}`, {
              method: "PUT", body: JSON.stringify({ content: content.trim() })
            });
            await renderPosts();
          }
        });
        const remove = make("button", "Delete post", "button button-danger");
        remove.addEventListener("click", async () => {
          if (!window.confirm("Delete this post and its media?")) return;
          await API.request(`/api/posts/${post.id}`, { method: "DELETE" });
          await renderPosts();
        });
        actions.append(edit, remove);
      }
      card.append(actions);
      const comments = await API.comments(post.id);
      (comments.items || []).forEach((entry) => {
        const commentRow = make("p", `@${entry.username}: ${entry.content}`, "comment-row");
        if (entry.user_id === currentUser.id) {
          const remove = make("button", "Delete comment", "button button-outline");
          remove.addEventListener("click", async () => {
            await API.request(`/api/posts/${post.id}/comments/${entry.id}`, { method: "DELETE" });
            await renderPosts();
          });
          commentRow.append(" ", remove);
        } else {
          const reportComment = make("button", "Report comment", "button button-outline");
          reportComment.addEventListener("click", async () => {
            const reason = window.prompt("Why are you reporting this comment?");
            if (reason && reason.trim()) {
              await API.request(`/api/posts/${post.id}/comments/${entry.id}/report`, {
                method: "POST", body: JSON.stringify({ target_type: "comment", target_id: entry.id, reason: reason.trim() })
              });
              UI.toast("Report submitted for review.");
            }
          });
          commentRow.append(" ", reportComment);
        }
        card.append(commentRow);
      });
      container.append(card);
    }
    if (!response.items.length) UI.message(container, "No posts yet. Be the first to share.");
  }
  byId("post-search").addEventListener("input", () => {
    page = 1;
    renderPosts().catch((error) => UI.toast(error.message, true));
  });
  byId("posts-previous").addEventListener("click", async () => { page = Math.max(1, page - 1); await renderPosts(); });
  byId("posts-next").addEventListener("click", async () => { page += 1; await renderPosts(); });
  await renderPosts();
}

async function loadExchanges() {
  const [allSkills, me] = await Promise.all([API.skills({ page_size: 100 }), API.me()]);
  const offered = byId("offered-skill");
  const requested = byId("requested-skill");
  allSkills.items.forEach((skill) => {
    const option = make("option", `${skill.name} · @${skill.owner_username}`);
    option.value = skill.id;
    if (skill.owner_id === me.id) offered.append(option);
    else requested.append(option);
  });
  byId("exchange-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const offeredSkill = allSkills.items.find((s) => s.id === Number(offered.value));
    const requestedSkill = allSkills.items.find((s) => s.id === Number(requested.value));
    if (!offeredSkill || !requestedSkill || offeredSkill.owner_id !== me.id) {
      return UI.toast("Choose one of your skills and another user's skill.", true);
    }
    await API.exchanges("/requests", { method: "POST", body: JSON.stringify({
      receiver_id: requestedSkill.owner_id, offered_skill_id: offeredSkill.id,
      requested_skill_id: requestedSkill.id, duration_days: Number(byId("duration-days").value)
    }) });
    UI.toast("Exchange request sent.");
    await renderExchangeLists();
  });
  async function renderRequests(path, target, ownRequest) {
    const container = byId(target);
    container.replaceChildren();
    const result = await API.exchanges(path);
    for (const request of result.items || []) {
      const card = UI.card(`Request #${request.id}`, `${request.duration_days} days · ${request.status}`);
      appendText(card, "p", `Skills ${request.offered_skill_id} ⇄ ${request.requested_skill_id}`);
      if (request.status === "pending") {
        if (!ownRequest && request.proposed_by_id !== me.id) {
          const accept = make("button", "Accept", "button button-primary");
          accept.addEventListener("click", async () => {
            await API.exchanges(`/requests/${request.id}/accept`, { method: "POST" });
            await renderExchangeLists();
          });
          const counter = make("button", "Counter duration", "button button-outline");
          counter.addEventListener("click", async () => {
            const duration = Number(window.prompt("Propose duration in days (1–365):", request.duration_days));
            if (!Number.isInteger(duration) || duration < 1 || duration > 365) return;
            await API.exchanges(`/requests/${request.id}/counter`, {
              method: "POST", body: JSON.stringify({ duration_days: duration })
            });
            await renderExchangeLists();
          });
          const reject = make("button", "Reject", "button button-danger");
          reject.addEventListener("click", async () => {
            await API.exchanges(`/requests/${request.id}/reject`, { method: "POST" });
            await renderExchangeLists();
          });
          card.append(accept, counter, reject);
        } else if (ownRequest) {
          const action = request.proposed_by_id !== me.id ? "Accept duration" : "Cancel request";
          const button = make("button", action, "button button-outline");
          button.addEventListener("click", async () => {
            if (request.proposed_by_id !== me.id) {
              await API.exchanges(`/requests/${request.id}/accept`, { method: "POST" });
            } else {
              await API.exchanges(`/requests/${request.id}/cancel`, { method: "POST" });
            }
            await renderExchangeLists();
          });
          card.append(button);
        }
      }
      container.append(card);
    }
    if (!(result.items || []).length) UI.message(container, "Nothing here yet.");
  }
  async function renderExchangeLists() {
    await renderRequests("/requests/received", "requests-received", false);
    await renderRequests("/requests/sent", "requests-sent", true);
    const active = byId("exchanges-active");
    active.replaceChildren();
    const activeResult = await API.exchanges("/active");
    for (const exchange of activeResult.items || []) {
      const card = UI.card(`Exchange #${exchange.id}`, `${exchange.status} · ${exchange.remaining_days} days remaining`);
      const complete = make("button", "Mark complete", "button button-primary");
      complete.addEventListener("click", async () => {
        await API.exchanges(`/${exchange.id}/complete`, { method: "POST" });
        await renderExchangeLists();
      });
      const cancel = make("button", "Cancel exchange", "button button-danger");
      cancel.addEventListener("click", async () => {
        await API.exchanges(`/${exchange.id}/cancel`, { method: "POST" });
        await renderExchangeLists();
      });
      card.append(complete, cancel);
      active.append(card);
    }
    if (!activeResult.items.length) UI.message(active, "No active exchanges.");
    const history = byId("exchanges-history");
    history.replaceChildren();
    const old = await API.exchanges("/history");
    (old.items || []).forEach((exchange) => history.append(
      UI.card(`Exchange #${exchange.id}`, `${exchange.status} · cycle ${exchange.cycle_number} · ${exchange.duration_days} days`)
    ));
    if (!(old.items || []).length) UI.message(history, "Completed and cancelled exchanges will appear here.");
  }
  await renderExchangeLists();
}

async function loadNotifications() {
  const result = await API.notifications();
  const container = byId("notifications-list");
  container.replaceChildren();
  (result.items || []).forEach((item) => {
    const card = UI.card(item.type.replaceAll("_", " "), item.message);
    if (!item.is_read) {
      const mark = make("button", "Mark read", "button button-outline");
      mark.addEventListener("click", async () => {
        await API.request(`/api/notifications/${item.id}/read`, { method: "PATCH" });
        await loadNotifications();
      });
      card.append(mark);
    }
    container.append(card);
  });
  if (!(result.items || []).length) UI.message(container, "You're all caught up.");
  byId("mark-all-read").addEventListener("click", async () => {
    await API.request("/api/notifications/read-all", { method: "PATCH" });
    await loadNotifications();
  }, { once: true });
}

async function loadSearch() {
  const form = byId("search-form");
  let timer;
  let page = 1;
  const run = async () => {
    const params = Object.fromEntries(new FormData(form).entries());
    const results = await API.search({ ...params, page, page_size: 20 });
    byId("search-page-label").textContent = `Page ${results.page} of ${Math.max(1, Math.ceil(results.total / results.page_size))}`;
    byId("search-previous").disabled = page <= 1;
    byId("search-next").disabled = page * results.page_size >= results.total;
    const container = byId("search-results");
    container.replaceChildren();
    results.items.forEach((item) => {
      const title = item.name || item.username || item.content || item.full_name;
      const card = UI.card(`${item.type}: ${title || "Result"}`, item.category || item.bio || "");
      if (item.description) appendText(card, "p", item.description);
      container.append(card);
    });
    if (!results.items.length) UI.message(container, "No matching results.");
  };
  form.addEventListener("input", () => {
    page = 1;
    window.clearTimeout(timer);
    timer = window.setTimeout(() => run().catch((error) => UI.toast(error.message, true)), 250);
  });
  form.addEventListener("submit", (event) => { event.preventDefault(); run().catch((error) => UI.toast(error.message, true)); });
  byId("search-previous").addEventListener("click", async () => { page = Math.max(1, page - 1); await run(); });
  byId("search-next").addEventListener("click", async () => { page += 1; await run(); });
  await run();
}

async function loadAdmin() {
  const [stats, users, reports] = await Promise.all([
    API.request("/api/admin/dashboard"), API.request("/api/admin/users?page_size=100"),
    API.request("/api/admin/reports?page_size=100")
  ]);
  const statsNode = byId("admin-stats");
  statsNode.replaceChildren();
  Object.entries(stats).forEach(([key, value]) => statsNode.append(UI.card(key.replaceAll("_", " "), String(value))));
  const userList = byId("admin-users");
  userList.replaceChildren();
  users.items.forEach((user) => {
    const card = UI.card(user.username, `${user.email} · ${user.role} · ${user.is_active ? "active" : "deactivated"}`);
    const button = make("button", user.is_active ? "Deactivate" : "Reactivate", "button button-outline");
    button.addEventListener("click", async () => {
      await API.request(`/api/admin/users/${user.id}/status`, {
        method: "PATCH", body: JSON.stringify({ is_active: !user.is_active })
      });
      await loadAdmin();
    });
    card.append(button);
    userList.append(card);
  });
  const reportList = byId("admin-reports");
  reportList.replaceChildren();
  reports.items.forEach((report) => {
    const card = UI.card(`${report.target_type} #${report.target_id}`, report.reason);
    ["resolved", "dismissed"].forEach((status) => {
      const button = make("button", status, "button button-outline");
      button.addEventListener("click", async () => {
        await API.request(`/api/admin/reports/${report.id}`, {
          method: "PATCH", body: JSON.stringify({ status })
        });
        await loadAdmin();
      });
      card.append(button);
    });
    reportList.append(card);
  });
}

async function loadSettings() {
  const profile = await API.profile();
  byId("settings-email").textContent = profile.email;
  byId("settings-availability").value = profile.availability || "";
  byId("settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await API.updateProfile({ availability: byId("settings-availability").value });
    UI.toast("Settings saved.");
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  const page = document.body.dataset.page;
  if (!page) return;
  try {
    await window.SkillSwapAuth.ready;
    if (document.body.dataset.protected === "true" && !window.SkillSwapAuth.user) return;
    const loaders = {
      dashboard: loadDashboard, profile: loadProfile, skills: loadSkills,
      community: loadCommunity, exchanges: loadExchanges, notifications: loadNotifications,
      search: loadSearch, admin: loadAdmin, settings: loadSettings
    };
    if (loaders[page]) await loaders[page]();
  } catch (error) {
    UI.toast(error.message || "Unable to load this page.", true);
  }
});
