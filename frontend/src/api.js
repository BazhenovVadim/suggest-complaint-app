import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('accessToken')

  if (accessToken) {
    config.headers = config.headers || {};
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
      originalRequest.headers = originalRequest.headers || {};
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      // Try to clear tokens via Pinia store, fallback to clearing localStorage
      try {
        const module = await import('./stores/user');
        const { useUserStore } = module;
        const userStore = useUserStore();
        userStore.clearAuthTokens();
      } catch (e) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('userId');
        localStorage.removeItem('accessTokenExpiresInSeconds');
      }

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

  const data = response.data || {};
  const newAccessToken = data.accessToken;
  const newRefreshToken = data.refreshToken || refreshToken;
  const newUserId = data.userId || userId;
  const accessTokenExpiresInSeconds = data.accessTokenExpiresInSeconds;

  if (newAccessToken) {
    localStorage.setItem('accessToken', newAccessToken);
  }
  if (newRefreshToken) {
    localStorage.setItem('refreshToken', newRefreshToken);
  }
  if (newUserId) {
    localStorage.setItem('userId', newUserId);
  }
  if (accessTokenExpiresInSeconds != null) {
    localStorage.setItem('accessTokenExpiresInSeconds', accessTokenExpiresInSeconds);
  }

  try {
    const module = await import('./stores/user');
    const { useUserStore } = module;
    const userStore = useUserStore();
    userStore.saveAuthTokens({
      accessToken: newAccessToken,
      refreshToken: newRefreshToken,
      userId: newUserId,
      accessTokenExpiresInSeconds,
    });
  } catch (e) {
  }

  return newAccessToken;
}

export default {
  login(data) {
    return api.post('api/auth/login', data)
  },

  register(data) {
    return api.post('api/auth/register', data)
  },

  logout(data) {
    return api.post('api/auth/logout', data)
  },

  refresh(data) {
    return api.post('api/auth/refresh', data)
  },

  submitAppeal(data) {
    return api.post('/api/appeals', data, {
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },

  async getAppeals() {
    return await api.get('api/appeals')
  },

  updateAppealStatus(appealId, status) {
    return api.patch(`/api/appeals/${appealId}/status`, { status })
  },

  getMe() {
    return api.get('api/user/me')
  }
}
