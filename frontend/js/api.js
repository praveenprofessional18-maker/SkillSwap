// SkillSwap frontend API helper.
// Set this to your backend URL. Do not put secrets or passwords in this file.
const API_BASE_URL = "http://127.0.0.1:8001";

async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("skillswap_access_token");
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData) && options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers
    });
  } catch (error) {
    const reason = error instanceof Error ? ` ${error.message}` : "";
    throw new Error(`Could not connect to SkillSwap API at ${API_BASE_URL}.${reason}`);
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = payload && typeof payload === "object" ? payload.detail : "";
    const message = Array.isArray(detail)
      ? detail.map(item => item && typeof item === "object" ? item.msg : "").filter(Boolean).join(" ")
      : detail || (payload && payload.message);
    throw new Error(message || `API request failed (${response.status}).`);
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
