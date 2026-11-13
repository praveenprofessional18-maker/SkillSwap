"use strict";

const loginForm = document.querySelector("#login-form");
const loginStatus = document.querySelector("#login-status");
const passwordInput = document.querySelector("#password");
const passwordToggle = document.querySelector("#password-toggle");
const year = document.querySelector("#current-year");

if (year) year.textContent = String(new Date().getFullYear());

if (passwordInput && passwordToggle) {
  passwordToggle.addEventListener("click", () => {
    const showPassword = passwordInput.type === "password";
    passwordInput.type = showPassword ? "text" : "password";
    passwordToggle.setAttribute("aria-pressed", String(showPassword));
    passwordToggle.setAttribute("aria-label", showPassword ? "Hide password" : "Show password");
    passwordToggle.textContent = showPassword ? "Hide" : "Show";
  });
}

if (loginForm && loginStatus) {
  loginForm.addEventListener("submit", event => {
    event.preventDefault();
    if (!loginForm.reportValidity()) return;
    loginStatus.textContent = "Sign-in isn't connected yet. Your credentials were not sent.";
  });
}
