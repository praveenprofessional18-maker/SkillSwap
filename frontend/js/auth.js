"use strict";

const protectedPage = document.body.dataset.protected === "true";
const accessToken = localStorage.getItem("skillswap_access_token")
  || sessionStorage.getItem("skillswap_access_token");

const authState = {
  user: null,
  ready: null
};
window.SkillSwapAuth = authState;

function clearAccessTokens() {
  localStorage.removeItem("skillswap_access_token");
  sessionStorage.removeItem("skillswap_access_token");
}

function redirectToLogin(errorCode) {
  const currentPage = `${window.location.pathname.split("/").pop()}${window.location.search}${window.location.hash}`;
  const loginUrl = new URL("login.html", window.location.href);
  loginUrl.searchParams.set("next", currentPage);
  if (errorCode) loginUrl.searchParams.set("error", errorCode);
  window.location.replace(loginUrl);
}

authState.ready = (async () => {
  if (!protectedPage) return null;
  if (!accessToken) {
    redirectToLogin();
    return null;
  }
  try {
    authState.user = await window.SkillSwapAPI.me();
    if (document.body.dataset.admin === "true" && authState.user.role !== "admin") {
      window.location.replace("dashboard.html");
      return null;
    }
    document.body.classList.add("auth-ready");
    return authState.user;
  } catch (error) {
    if (error.status === 401) {
      clearAccessTokens();
      redirectToLogin();
      return null;
    }
    console.error("Session validation failed:", error);
    redirectToLogin("session_unavailable");
    return null;
  }
})();
