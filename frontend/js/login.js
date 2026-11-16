"use strict";

const form = document.getElementById("loginForm");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const rememberMeInput = document.getElementById("rememberMe");
const togglePasswordButton = document.querySelector(".toggle-password");
const emailError = document.getElementById("emailError");
const passwordError = document.getElementById("passwordError");
const successMessage = document.getElementById("formSuccess");
if (new URLSearchParams(window.location.search).get("error") === "session_unavailable") {
  successMessage.classList.add("is-error");
  successMessage.textContent = "We could not verify your session. Check your connection and sign in again.";
}

function getPostLoginDestination() {
  const requested = new URLSearchParams(window.location.search).get("next");
  const allowedPages = new Set([
    "admin.html", "community.html", "dashboard.html", "exchanges.html",
    "notifications.html", "profile.html", "search.html", "settings.html", "skills.html"
  ]);
  if (!requested) return "dashboard.html";

  let destination;
  try {
    destination = new URL(requested, window.location.href);
  } catch {
    return "dashboard.html";
  }
  if (destination.origin !== window.location.origin || !allowedPages.has(destination.pathname.split("/").pop())) {
    return "dashboard.html";
  }
  return `${destination.pathname}${destination.search}${destination.hash}`;
}

function setError(input, errorField, message) {
  input.setAttribute("aria-invalid", "true");
  input.closest(".input-wrap").classList.add("input-error");
  errorField.textContent = message;
}

function clearError(input, errorField) {
  input.setAttribute("aria-invalid", "false");
  input.closest(".input-wrap").classList.remove("input-error");
  errorField.textContent = "";
}

function validateEmail(value) {
  const trimmed = value.trim();
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!trimmed) {
    return "Email is required.";
  }

  if (!emailPattern.test(trimmed)) {
    return "Please enter a valid email address.";
  }

  return '';
}

function validatePassword(value) {
  if (!value) {
    return "Password is required.";
  }

  if (value.length < 8) {
    return "Password must be at least 8 characters long.";
  }

  return '';
}

function validateForm() {
  const emailMessage = validateEmail(emailInput.value);
  const passwordMessage = validatePassword(passwordInput.value);

  if (emailMessage) {
    setError(emailInput, emailError, emailMessage);
  } else {
    clearError(emailInput, emailError);
  }

  if (passwordMessage) {
    setError(passwordInput, passwordError, passwordMessage);
  } else {
    clearError(passwordInput, passwordError);
  }

  return !emailMessage && !passwordMessage;
}

emailInput.addEventListener("input", () => {
  if (emailInput.value.trim()) {
    const message = validateEmail(emailInput.value);
    if (message) {
      setError(emailInput, emailError, message);
    } else {
      clearError(emailInput, emailError);
    }
  } else {
    clearError(emailInput, emailError);
  }
});

passwordInput.addEventListener("input", () => {
  if (passwordInput.value.trim()) {
    const message = validatePassword(passwordInput.value);
    if (message) {
      setError(passwordInput, passwordError, message);
    } else {
      clearError(passwordInput, passwordError);
    }
  } else {
    clearError(passwordInput, passwordError);
  }
});

togglePasswordButton.addEventListener("click", () => {
  const isPassword = passwordInput.type === "password";
  passwordInput.type = isPassword ? "text" : "password";
  togglePasswordButton.textContent = isPassword ? "Hide" : "Show";
  togglePasswordButton.setAttribute(
    "aria-label",
    isPassword ? "Hide password" : "Show password"
  );
  passwordInput.focus();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  successMessage.textContent = "";
  successMessage.classList.remove("is-error");

  if (!validateForm()) {
    return;
  }

  const submitButton = form.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  submitButton.classList.add("is-loading");
  submitButton.textContent = "Signing in...";

  try {
    if (!window.SkillSwapAPI) {
      throw new Error("The SkillSwap API helper could not be loaded.");
    }

    await window.SkillSwapAPI.login({
      email: emailInput.value.trim(),
      password: passwordInput.value
    }, rememberMeInput.checked);

    window.location.replace(getPostLoginDestination());
  } catch (error) {
    successMessage.classList.add("is-error");
    if (error.message.toLowerCase().includes("invalid email or password")) {
      successMessage.textContent = "The email or password is incorrect.";
    } else if (error.message === "Failed to fetch") {
      successMessage.textContent =
        "Could not reach the SkillSwap server. Make sure the backend is running, then try again.";
    } else {
      successMessage.textContent = error.message || "Sign in failed. Please try again.";
    }
  } finally {
    submitButton.disabled = false;
    submitButton.classList.remove("is-loading");
    submitButton.textContent = "Log in";
  }
});
