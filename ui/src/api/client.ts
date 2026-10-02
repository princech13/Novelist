import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8081",
  headers: { "Content-Type": "application/json" },
});

// Attach the access token from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, clear storage and redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !err.config?.url?.startsWith("/auth/")) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user_id");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);
