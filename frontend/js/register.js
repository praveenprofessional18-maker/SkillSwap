
"use strict";

const form = document.getElementById("registerForm");

const fullName = document.getElementById("fullName");
const username = document.getElementById("username");
const email = document.getElementById("email");
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirmPassword");
const language = document.getElementById("language");
const terms = document.getElementById("terms");

const nameError = document.getElementById("nameError");
const usernameError = document.getElementById("usernameError");
const emailError = document.getElementById("emailError");
const passwordError = document.getElementById("passwordError");
const confirmPasswordError = document.getElementById("confirmPasswordError");
const languageError = document.getElementById("languageError");
const termsError = document.getElementById("termsError");

const successMessage = document.getElementById("formSuccess");

function setError(input, errorField, message) {
    errorField.textContent = message;

    if (input) {
            input.setAttribute("aria-invalid", "true");

            const wrapper = input.closest(".input-wrap");

        if (wrapper) {
                wrapper.classList.add("input-error");
        } else {
                input.classList.add("input-error");
        }
    }
}

function clearError(input, errorField) {
    errorField.textContent = '';

    if (input) {
        input.setAttribute("aria-invalid", "false");

        const wrapper = input.closest(".input-wrap");

        if (wrapper) {
            wrapper.classList.remove("input-error");
        } else {
            input.classList.remove("input-error");
        }
    }
}

function validateName(value) {
    const trimmed = value.trim();

    if (!trimmed) {
        return "Full name is required.";
    }

    if (trimmed.length < 2) {
        return "Name must contain at least 2 characters.";
    }

    return '';
}

function validateUsername(value) {
    const trimmed = value.trim();
    if (!/^[A-Za-z0-9_.-]{3,40}$/.test(trimmed)) {
        return "Use 3–40 letters, numbers, dots, underscores or hyphens.";
    }
    return "";
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
        return "Password must contain at least 8 characters.";
    }

    return '';
}

function validateConfirmPassword(value) {
    if (!value) {
        return "Please confirm your password.";
    }

    if (value !== password.value) {
        return "Passwords do not match.";
    }

    return '';
}

function validateForm() {
    let isValid = true;

    const nameMessage = validateName(fullName.value);
    const usernameMessage = validateUsername(username.value);
    const emailMessage = validateEmail(email.value);
    const passwordMessage = validatePassword(password.value);
    const confirmMessage = validateConfirmPassword(confirmPassword.value);

    if (nameMessage) {
        setError(fullName, nameError, nameMessage);
        isValid = false;
    } else {
        clearError(fullName, nameError);
    }

    if (usernameMessage) {
        setError(username, usernameError, usernameMessage);
        isValid = false;
    } else {
        clearError(username, usernameError);
    }

    if (emailMessage) {
        setError(email, emailError, emailMessage);
        isValid = false;
    } else {
        clearError(email, emailError);
    }

    if (passwordMessage) {
        setError(password, passwordError, passwordMessage);
        isValid = false;
    } else {
        clearError(password, passwordError);
    }

    if (confirmMessage) {
        setError(confirmPassword, confirmPasswordError, confirmMessage);
        isValid = false;
    } else {
        clearError(confirmPassword, confirmPasswordError);
    }

    if (!language.value) {
        languageError.textContent = 'Please select your language.';
        language.classList.add('input-error');
        isValid = false;
    } else {
        languageError.textContent = '';
        language.classList.remove('input-error');
    }

    if (!terms.checked) {
        termsError.textContent = 'Please accept the terms and conditions.';
        isValid = false;
    } else {
        termsError.textContent = '';
    }

    return isValid;
}

fullName.addEventListener("input", () => {
    const message = validateName(fullName.value);

    if (message) {
        setError(fullName, nameError, message);
    } else {
        clearError(fullName, nameError);
    }
});

username.addEventListener("input", () => {
    const message = validateUsername(username.value);
    if (message) setError(username, usernameError, message);
    else clearError(username, usernameError);
});

email.addEventListener("input", () => {
    const message = validateEmail(email.value);

    if (message) {
        setError(email, emailError, message);
    } else {
        clearError(email, emailError);
    }
});

password.addEventListener("input", () => {
    const message = validatePassword(password.value);

    if (message) {
        setError(password, passwordError, message);
    } else {
        clearError(password, passwordError);
    }

    if (confirmPassword.value) {
        const confirmMessage = validateConfirmPassword(confirmPassword.value);

        if (confirmMessage) {
            setError(confirmPassword, confirmPasswordError, confirmMessage);
        } else {
            clearError(confirmPassword, confirmPasswordError);
        }
    }
});

confirmPassword.addEventListener("input", () => {
    const message = validateConfirmPassword(confirmPassword.value);

    if (message) {
        setError(confirmPassword, confirmPasswordError, message);
    } else {
        clearError(confirmPassword, confirmPasswordError);
    }
});

language.addEventListener("change", () => {
    if (language.value) {
        languageError.textContent = '';
        language.classList.remove('input-error');
    }
});

terms.addEventListener('change', () => {
    termsError.textContent = terms.checked
        ? ''
        : 'Please accept the terms and conditions.';
});

document.querySelectorAll(".toggle-password").forEach(button => {
    button.addEventListener("click", () => {
        const targetId = button.dataset.target;
        const input = document.getElementById(targetId);

        if (!input) {
            return;
        }

        const isPassword = input.type === "password";

        input.type = isPassword ? "text" : "password";
        button.textContent = isPassword ? "Hide" : "Show";

        button.setAttribute(
            "aria-label",
            isPassword ? "Hide password" : "Show password"
        );

        input.focus();
    });
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
    submitButton.textContent = "Creating account...";

    try {
        if (!window.SkillSwapAPI) {
            throw new Error("The SkillSwap API helper could not be loaded.");
        }

        await window.SkillSwapAPI.register({
            username: username.value.trim(),
            full_name: fullName.value.trim(),
            email: email.value.trim(),
            password: password.value,
            language: language.value
        });

        successMessage.textContent =
            "Your account was created. You can now sign in with your email and password.";
        password.value = "";
        confirmPassword.value = "";
        clearError(password, passwordError);
        clearError(confirmPassword, confirmPasswordError);
    } catch (error) {
        successMessage.classList.add("is-error");
        if (error.message.toLowerCase().includes("already registered")) {
            successMessage.textContent =
                "An account with this email already exists. Try signing in instead.";
        } else if (error.message === "Failed to fetch") {
            successMessage.textContent =
                "Could not reach the SkillSwap server. Make sure the backend is running, then try again.";
        } else {
            successMessage.textContent =
                error.message || "Account creation failed. Please try again.";
        }
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Create Account";
    }
});