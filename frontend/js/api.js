"use strict";

const API_BASE_URL = window.SkillSwapConfig && window.SkillSwapConfig.API_BASE_URL;
if (!API_BASE_URL) throw new Error("Set API_BASE_URL in js/config.js before loading the API helper.");

async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("skillswap_access_token")
    || sessionStorage.getItem("skillswap_access_token");
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData) && options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (response.status === 401 && token) {
    localStorage.removeItem("skillswap_access_token");
    sessionStorage.removeItem("skillswap_access_token");
    if (document.body.dataset.protected === "true" && !window.skillSwapAuthRedirecting) {
      window.skillSwapAuthRedirecting = true;
      document.body.classList.remove("auth-ready");
      const currentPage = `${window.location.pathname.split("/").pop()}${window.location.search}${window.location.hash}`;
      const loginUrl = new URL("login.html", window.location.href);
      loginUrl.searchParams.set("next", currentPage);
      window.location.replace(loginUrl);
    }
  }
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const message = payload && payload.detail;
    const text = typeof message === "string" ? message : message && message.detail;
    const error = new Error(text || "API request failed");
    error.status = response.status;
    throw error;
  }
  return payload;
}

function queryString(params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  return query.toString();
}

const SkillSwapAPI = {
  request: apiRequest,
  register: (data) => apiRequest("/api/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: async (data, rememberMe = false) => {
    localStorage.removeItem("skillswap_access_token");
    sessionStorage.removeItem("skillswap_access_token");
    const result = await apiRequest("/api/auth/login", { method: "POST", body: JSON.stringify(data) });
    const storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem("skillswap_access_token", result.access_token);
    return result;
  },
  me: () => apiRequest("/api/auth/me"),
  profile: () => apiRequest("/api/users/me/profile"),
  updateProfile: (data) => apiRequest("/api/users/me", { method: "PUT", body: JSON.stringify(data) }),
  categories: (params = {}) => apiRequest(`/api/skills/categories?${queryString(params)}`),
  skills: (params = {}) => apiRequest(`/api/skills?${queryString(params)}`),
  learningPaths: (params = {}) => apiRequest(`/api/learning-paths?${queryString(params)}`),
  learningPath: (slug) => apiRequest(`/api/learning-paths/${encodeURIComponent(slug)}`),
  learningLesson: (id) => apiRequest(`/api/learning-lessons/${id}`),
  submitLearningExercise: (id, response) => apiRequest(`/api/learning-lessons/${id}/exercise`, {
    method: "PUT", body: JSON.stringify({ response }),
  }),
  submitLearningQuiz: (id, answers) => apiRequest(`/api/learning-lessons/${id}/quiz`, {
    method: "POST", body: JSON.stringify({ answers }),
  }),
  createSkill: (data) => apiRequest("/api/skills", { method: "POST", body: JSON.stringify(data) }),
  updateSkill: (id, data) => apiRequest(`/api/skills/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteSkill: (id) => apiRequest(`/api/skills/${id}`, { method: "DELETE" }),
  posts: (params = {}) => apiRequest(`/api/posts?${queryString(params)}`),
  createPost: (data) => apiRequest("/api/posts", { method: "POST", body: JSON.stringify(data) }),
  uploadPostMedia: (id, file) => {
    const form = new FormData();
    form.append("file", file);
    return apiRequest(`/api/posts/${id}/media`, { method: "POST", body: form });
  },
  toggleLike: (id, liked) => apiRequest(`/api/posts/${id}/like`, {
    method: "POST", body: JSON.stringify({ liked })
  }),
  addComment: (id, content) => apiRequest(`/api/posts/${id}/comments`, {
    method: "POST", body: JSON.stringify({ content })
  }),
  comments: (id) => apiRequest(`/api/posts/${id}/comments`),
  exchanges: (path, options = {}) => apiRequest(`/api/exchanges${path}`, options),
  notifications: (params = {}) => apiRequest(`/api/notifications?${queryString(params)}`),
  search: (params = {}) => apiRequest(`/api/search?${queryString(params)}`),
  logout: async () => {
    let logoutError;
    try {
      await apiRequest("/api/auth/logout", { method: "POST" });
    } catch (error) {
      logoutError = error;
    }
    localStorage.removeItem("skillswap_access_token");
    sessionStorage.removeItem("skillswap_access_token");
    window.location.replace("login.html");
    if (logoutError) throw logoutError;
  }
};

window.SkillSwapAPI = SkillSwapAPI;
