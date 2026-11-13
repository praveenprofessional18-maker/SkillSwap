"use strict";

window.SkillSwapUI = {
  element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  },
  message(container, text, className = "empty-state") {
    container.replaceChildren(this.element("p", text, className));
  },
  async load(container, action) {
    this.message(container, "Loading…", "loading-state");
    try {
      await action();
    } catch (error) {
      this.message(container, error.message || "Something went wrong.", "error-state");
    }
  },
  toast(text, isError = false) {
    let node = document.querySelector("#toast");
    if (!node) {
      node = this.element("div", "", "toast");
      node.id = "toast";
      node.setAttribute("role", "status");
      document.body.append(node);
    }
    node.textContent = text;
    node.classList.toggle("toast-error", isError);
    node.classList.add("toast-visible");
    window.setTimeout(() => node.classList.remove("toast-visible"), 3200);
  },
  card(title, details) {
    const card = this.element("article", undefined, "content-card");
    card.append(this.element("h2", title));
    if (details) card.append(this.element("p", details));
    return card;
  }
};

window.addEventListener("unhandledrejection", (event) => {
  event.preventDefault();
  window.SkillSwapUI.toast(event.reason && event.reason.message
    ? event.reason.message
    : "The action failed. Please try again.", true);
});
