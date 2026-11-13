const form = document.getElementById('loginForm');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const togglePasswordButton = document.querySelector('.toggle-password');
const emailError = document.getElementById('emailError');
const passwordError = document.getElementById('passwordError');
const successMessage = document.getElementById('formSuccess');

function setError(input, errorField, message) {
  input.setAttribute('aria-invalid', 'true');
  input.closest('.input-wrap').classList.add('input-error');
  errorField.textContent = message;
}

function clearError(input, errorField) {
  input.setAttribute('aria-invalid', 'false');
  input.closest('.input-wrap').classList.remove('input-error');
  errorField.textContent = '';
}

function validateEmail(value) {
  const trimmed = value.trim();
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!trimmed) {
    return 'Email is required.';
  }

  if (!emailPattern.test(trimmed)) {
    return 'Please enter a valid email address.';
  }

  return '';
}

function validatePassword(value) {
  const trimmed = value.trim();

  if (!trimmed) {
    return 'Password is required.';
  }

  if (trimmed.length < 6) {
    return 'Password must be at least 6 characters long.';
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

emailInput.addEventListener('input', () => {
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

passwordInput.addEventListener('input', () => {
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

togglePasswordButton.addEventListener('click', () => {
  const isPassword = passwordInput.type === 'password';
  passwordInput.type = isPassword ? 'text' : 'password';
  togglePasswordButton.textContent = isPassword ? 'Hide' : 'Show';
  togglePasswordButton.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
  passwordInput.focus();
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  successMessage.textContent = '';

  if (!validateForm()) {
    return;
  }

  successMessage.textContent = 'Demo login successful. This is a front-end-only preview, and no real authentication was performed.';
});
