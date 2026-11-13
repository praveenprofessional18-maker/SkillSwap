// SkillSwap frontend API helper.
// Set this to your backend URL. Do not put secrets or passwords in this file.
const API_BASE_URL = "http://127.0.0.1:8000";

async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("skillswap_access_token");
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData) && options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new Error(payload.detail || payload.message || "API request failed");
  }
  return payload;
}

const SkillSwapAPI = {
  register: (data) => apiRequest("/api/register", {
    method: "POST", body: JSON.stringify(data)
  }),
  login: async (data) => {
    const result = await apiRequest("/api/login", {
      method: "POST", body: JSON.stringify(data)
    });
    localStorage.setItem("skillswap_access_token", result.access_token);
    return result;
  },
  profile: () => apiRequest("/api/profile"),
  posts: () => apiRequest("/api/posts"),
  createPost: (data) => apiRequest("/api/posts", {
    method: "POST", body: JSON.stringify(data)
  }),
  createExchange: (data) => apiRequest("/api/exchanges", {
    method: "POST", body: JSON.stringify(data)
  }),
  exchanges: () => apiRequest("/api/exchanges")
};

window.SkillSwapAPI = SkillSwapAPI;
