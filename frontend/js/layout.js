"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const host = document.querySelector("#app-header");
  if (!host) return;
  const header = document.createElement("header");
  header.className = "app-header";
  const brand = document.createElement("a");
  brand.className = "app-brand";
  brand.href = "dashboard.html";
  brand.textContent = "SkillSwap";
  const nav = document.createElement("nav");
  nav.setAttribute("aria-label", "Main navigation");
  [
    ["Dashboard", "dashboard.html"], ["Skills", "skills.html"], ["Community", "community.html"],
    ["Exchanges", "exchanges.html"], ["Search", "search.html"], ["Notifications", "notifications.html"],
    ["Profile", "profile.html"], ["Settings", "settings.html"]
  ].forEach(([label, href]) => {
    const link = document.createElement("a");
    link.textContent = label;
    link.href = href;
    nav.append(link);
  });
  const addAdminLink = () => {
    if (nav.querySelector('a[href="admin.html"]')) return;
    const adminLink = document.createElement("a");
    adminLink.textContent = "Admin";
    adminLink.href = "admin.html";
    nav.append(adminLink);
  };
  if (document.body.dataset.admin === "true") addAdminLink();
  else window.SkillSwapAuth.ready.then((user) => {
    if (user && user.role === "admin") addAdminLink();
  });
  const logout = document.createElement("button");
  logout.type = "button";
  logout.className = "button button-outline";
  logout.textContent = "Log out";
  logout.addEventListener("click", () => window.SkillSwapAPI.logout());
  header.append(brand, nav, logout);
  host.replaceChildren(header);
});
