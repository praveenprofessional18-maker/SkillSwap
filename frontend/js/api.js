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
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const message = payload && payload.detail;
    throw new Error(typeof message === "string" ? message : "API request failed");
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
  login: async (data, rememberMe = true) => {
    const result = await apiRequest("/api/auth/login", { method: "POST", body: JSON.stringify(data) });
    const storage = rememberMe ? localStorage : sessionStorage;
    const other = rememberMe ? sessionStorage : localStorage;
    other.removeItem("skillswap_access_token");
    storage.setItem("skillswap_access_token", result.access_token);
    return result;
  },
  me: () => apiRequest("/api/auth/me"),
  profile: () => apiRequest("/api/users/me/profile"),
  updateProfile: (data) => apiRequest("/api/users/me", { method: "PUT", body: JSON.stringify(data) }),
  categories: (params = {}) => apiRequest(`/api/skills/categories?${queryString(params)}`),
  skills: (params = {}) => apiRequest(`/api/skills?${queryString(params)}`),
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
  notifications: () => apiRequest("/api/notifications"),
  search: (params = {}) => apiRequest(`/api/search?${queryString(params)}`),
  logout: () => {
    localStorage.removeItem("skillswap_access_token");
    sessionStorage.removeItem("skillswap_access_token");
    window.location.href = "index.html";
  }
};

window.SkillSwapAPI = SkillSwapAPI;
