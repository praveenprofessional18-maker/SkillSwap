"use strict";

const protectedPage = document.body.dataset.protected === "true";
const accessToken = localStorage.getItem("skillswap_access_token")
  || sessionStorage.getItem("skillswap_access_token");

const authState = {
  user: null,
  ready: null
};
window.SkillSwapAuth = authState;
authState.ready = (async () => {
  if (!protectedPage) return null;
  if (!accessToken) {
    window.location.replace("login.html");
    return null;
  }
  try {
    authState.user = await window.SkillSwapAPI.me();
    if (document.body.dataset.admin === "true" && authState.user.role !== "admin") {
      window.location.replace("dashboard.html");
      return null;
    }
    return authState.user;
  } catch (error) {
    console.error("Session validation failed:", error);
    localStorage.removeItem("skillswap_access_token");
    sessionStorage.removeItem("skillswap_access_token");
    window.location.replace("login.html");
    return null;
  }
})();
