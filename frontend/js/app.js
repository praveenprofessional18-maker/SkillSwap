"use strict";

const menuToggle = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#primary-navigation");
const filterButtons = [...document.querySelectorAll(".filter-chip")];
const courseCards = [...document.querySelectorAll("[data-course-category]")];
const filterStatus = document.querySelector("#filter-status");
const categoryLinks = [...document.querySelectorAll("[data-category-link]")];

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

function filterCourses(category) {
  let visibleCount = 0;
  courseCards.forEach(card => {
    const matches = category === "all" || card.dataset.courseCategory === category;
    card.hidden = !matches;
    if (matches) visibleCount += 1;
  });

  filterButtons.forEach(button => {
    const isActive = button.dataset.filter === category;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });

  if (filterStatus) {
    filterStatus.textContent = visibleCount === 0
      ? "No featured classes in this category just yet. Check back soon."
      : category === "all" ? "" : `${visibleCount} featured ${visibleCount === 1 ? "class" : "classes"} in this category.`;
  }
}

filterButtons.forEach(button => {
  button.addEventListener("click", () => filterCourses(button.dataset.filter || "all"));
});

categoryLinks.forEach(link => {
  link.addEventListener("click", () => {
    const category = link.dataset.categoryLink || "all";
    filterCourses(category);
  });
});

const year = document.querySelector("#current-year");
if (year) year.textContent = String(new Date().getFullYear());

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
