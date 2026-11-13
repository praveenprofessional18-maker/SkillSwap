"use strict";

const menuToggle = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#primary-navigation");

function closeNavigation() {
  if (!menuToggle || !navigation) return;
  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.setAttribute("aria-label", "Open navigation");
  navigation.classList.remove("is-open");
}

if (menuToggle && navigation) {
  menuToggle.addEventListener("click", () => {
    const isOpen = menuToggle.getAttribute("aria-expanded") !== "true";
    menuToggle.setAttribute("aria-expanded", String(isOpen));
    menuToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
    navigation.classList.toggle("is-open", isOpen);
  });

  navigation.addEventListener("click", event => {
    if (event.target instanceof Element && event.target.closest("a")) closeNavigation();
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeNavigation();
  });

  window.addEventListener("resize", () => {
    if (window.matchMedia("(min-width: 681px)").matches) closeNavigation();
  });
}

const year = document.querySelector("#current-year");
if (year) year.textContent = String(new Date().getFullYear());

async function loadLandingData() {
  const categoryGrid = document.querySelector("#category-grid");
  const featured = document.querySelector("#featured-skills");
  if (!categoryGrid || !featured) return;
  const [categories, skills] = await Promise.all([
    window.SkillSwapAPI.request("/api/skills/categories?page_size=100"),
    window.SkillSwapAPI.skills({ page: 1, page_size: 6 })
  ]);
  categoryGrid.replaceChildren();
  categories.items.forEach((category, index) => {
    const link = document.createElement("a");
    link.className = `category-card category-${["lavender", "blue", "peach", "mint", "yellow", "pink"][index % 6]}`;
    link.href = `skills.html?category=${encodeURIComponent(category.name)}`;
    const icon = document.createElement("span");
    icon.className = "category-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "✳";
    const title = document.createElement("h3");
    title.textContent = category.name;
    const action = document.createElement("span");
    action.className = "category-link";
    action.textContent = "Explore skills ↗";
    link.append(icon, title, action);
    categoryGrid.append(link);
  });
  featured.replaceChildren();
  if (!skills.items.length) {
    const empty = document.createElement("p");
    empty.className = "filter-status";
    empty.textContent = "No community skills have been added yet. Create an account and share what you can teach.";
    featured.append(empty);
    return;
  }
  skills.items.forEach((skill) => {
    const card = document.createElement("article");
    card.className = "content-card";
    const title = document.createElement("h3");
    title.textContent = skill.name;
    const category = document.createElement("p");
    category.textContent = `${skill.category} · ${skill.experience_level}`;
    const owner = document.createElement("small");
    owner.textContent = `Shared by @${skill.owner_username}`;
    card.append(title, category, owner);
    featured.append(card);
  });
}

loadLandingData().catch(error => {
  document.querySelectorAll("#category-grid, #featured-skills").forEach((container) => {
    const message = document.createElement("p");
    message.className = "filter-status";
    message.textContent = error.message || "Community data is unavailable right now.";
    container.replaceChildren(message);
  });
});

const revealElements = [...document.querySelectorAll(".reveal")];
if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  document.documentElement.classList.add("js-ready");
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -24px 0px" });

  revealElements.forEach(element => revealObserver.observe(element));
} else {
  revealElements.forEach(element => element.classList.add("is-visible"));
}
