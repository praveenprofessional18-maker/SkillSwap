"use strict";

const form = document.getElementById("loginForm");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const togglePasswordButton = document.getElementById("togglePassword");
const submitButton = document.getElementById("loginSubmit");
const emailError = document.getElementById("emailError");
const passwordError = document.getElementById("passwordError");
const formStatus = document.getElementById("formStatus");

function clearStatus() {
  formStatus.textContent = "";
  formStatus.classList.remove("is-error");
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

  if (!trimmed) return "Email address is required.";
  if (!emailPattern.test(trimmed)) return "Please enter a valid email address.";
  return "";
}

function validatePassword(value) {
  if (!value) return "Password is required.";
  return "";
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

  if (emailMessage) {
    emailInput.focus();
  } else if (passwordMessage) {
    passwordInput.focus();
  }

  return !emailMessage && !passwordMessage;
}

emailInput.addEventListener("input", () => {
  clearStatus();
  if (!emailInput.value.trim()) {
    clearError(emailInput, emailError);
    return;
  }

  const message = validateEmail(emailInput.value);
  if (message) {
    setError(emailInput, emailError, message);
  } else {
    clearError(emailInput, emailError);
  }
});

passwordInput.addEventListener("input", () => {
  clearStatus();
  if (!passwordInput.value) {
    clearError(passwordInput, passwordError);
    return;
  }

  const message = validatePassword(passwordInput.value);
  if (message) {
    setError(passwordInput, passwordError, message);
  } else {
    clearError(passwordInput, passwordError);
  }
});

togglePasswordButton.addEventListener("click", () => {
  const showPassword = passwordInput.type === "password";
  passwordInput.type = showPassword ? "text" : "password";
  togglePasswordButton.textContent = showPassword ? "Hide" : "Show";
  togglePasswordButton.setAttribute("aria-label", showPassword ? "Hide password" : "Show password");
  togglePasswordButton.setAttribute("aria-pressed", String(showPassword));
  passwordInput.focus();
});

form.addEventListener("submit", async event => {
  event.preventDefault();
  clearStatus();

  if (!validateForm()) return;

  if (!window.SkillSwapAPI) {
    formStatus.textContent = "The SkillSwap API helper did not load. Refresh the page and try again.";
    formStatus.classList.add("is-error");
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "Signing in…";
  try {
    await window.SkillSwapAPI.login({
      email: emailInput.value.trim(),
      password: passwordInput.value
    });
    window.location.assign("marketplace.html?v=1");
  } catch (error) {
    formStatus.textContent = error instanceof Error ? error.message : "Sign-in failed.";
    formStatus.classList.add("is-error");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Continue";
  }
});
