import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

const api = axios.create({
    baseURL: API_BASE_URL,
});

const saveAuthTokens = ({ accessToken, refreshToken, userId, accessTokenExpiresInSeconds }) => {
    localStorage.setItem("accessToken", accessToken);
    localStorage.setItem("refreshToken", refreshToken);
    localStorage.setItem("userId", userId);
    if (accessTokenExpiresInSeconds) {
        localStorage.setItem("accessTokenExpiresInSeconds", accessTokenExpiresInSeconds);
    }
};

const clearAuthTokens = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("userId");
    localStorage.removeItem("accessTokenExpiresInSeconds");
};

const refreshAccessToken = async () => {
    const refreshToken = localStorage.getItem("refreshToken");
    const userId = localStorage.getItem("userId");

    if (!refreshToken || !userId) {
        throw new Error("Refresh token is missing");
    }

    const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
        userId,
        refreshToken,
    });

    saveAuthTokens(response.data);
    return response.data.accessToken;
};

api.interceptors.request.use((config) => {
    const accessToken = localStorage.getItem("accessToken");
    if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
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

const logout = async () => {
    const refreshToken = localStorage.getItem("refreshToken");
    const userId = localStorage.getItem("userId");

    try {
        if (userId) {
            await axios.post(`${API_BASE_URL}/api/auth/logout`, {
                userId,
                refreshToken,
            });
        }
    } finally {
        clearAuthTokens();
    }
};

export { API_BASE_URL, api, clearAuthTokens, logout, saveAuthTokens };
