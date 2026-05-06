import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('accessToken')

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  return config
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status !== 401 || originalRequest?._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const newAccessToken = await refreshAccessToken();
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      clearAuthTokens();
      window.location.href = "/login";
      return Promise.reject(refreshError);
    }
  },
);

const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refreshToken');
  const userId = localStorage.getItem('userId');

  if (!refreshToken || !userId) {
    throw new Error("Refresh token is missing");
  }

  const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
    userId,
    refreshToken,
  });
}

export default {
  login(data) {
    return api.post('api/auth/login', data)
  },

  register(data) {
    return api.post('api/auth/register', data)
  },

  logout() {
    return api.post('api/auth/logout')
  },

  refresh() {
    return api.post('api/auth/refresh')
  },

  submitAppeal(data) {
    return api.post('/api/appeals', data, {
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
}
