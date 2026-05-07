import { defineStore } from "pinia";
import api from '@/api'

export const useUserStore = defineStore("user", {
  state: () => ({
    profile: localStorage.getItem("profile") || null,
    accessToken: localStorage.getItem("accessToken") || null,
    userId: localStorage.getItem("userId") || null,
    refreshToken: localStorage.getItem("refreshToken") || null,
    accessTokenExpiresInSeconds: localStorage.getItem("accessTokenExpiresInSeconds")
      ? Number(localStorage.getItem("accessTokenExpiresInSeconds"))
      : null,
    userRole: localStorage.getItem("userRole") || null,
  }),
  actions: {
    saveAuthTokens({ accessToken, refreshToken, userId, accessTokenExpiresInSeconds, userRole }) {
      if (accessToken !== undefined) {
        this.accessToken = accessToken;
        if (accessToken) localStorage.setItem('accessToken', accessToken);
        else localStorage.removeItem('accessToken');
      }

      if (refreshToken !== undefined) {
        this.refreshToken = refreshToken;
        if (refreshToken) localStorage.setItem('refreshToken', refreshToken);
        else localStorage.removeItem('refreshToken');
      }

      if (userId !== undefined) {
        this.userId = userId;
        if (userId) localStorage.setItem('userId', userId);
        else localStorage.removeItem('userId');
      }

      if (accessTokenExpiresInSeconds !== undefined) {
        this.accessTokenExpiresInSeconds = accessTokenExpiresInSeconds;
        if (accessTokenExpiresInSeconds != null) localStorage.setItem('accessTokenExpiresInSeconds', accessTokenExpiresInSeconds);
        else localStorage.removeItem('accessTokenExpiresInSeconds');
      }

      if (userRole !== undefined) {
        this.userRole = userRole;
        if (userRole) localStorage.setItem('userRole', userRole);
        else localStorage.removeItem('userRole');
      }
    },

    clearAuthTokens() {
      this.accessToken = null;
      this.refreshToken = null;
      this.userId = null;
      this.accessTokenExpiresInSeconds = null;
      this.userRole = null;
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("userId");
      localStorage.removeItem("accessTokenExpiresInSeconds");
      localStorage.removeItem("userProfile");
      localStorage.removeItem("userRole");
    },

    async register(registerData) {
      const response = await api.register(registerData);
      this.saveAuthTokens(response.data);
    },

    async login({ email, password }) {
      const response = await api.login({ email, password })
      this.saveAuthTokens(response.data);
    },

    async logout() {
      try {
        await api.logout({ userId: this.userId, refreshToken: this.refreshToken })
      } catch (_) { };

      this.clearAuthTokens();
    },

    async fetchProfile() {
      if (!this.accessToken) {
        this.profile = null;
        return;
      }

      const response = await fetch("/api/user/profile", {
        headers: { Authorization: `Bearer ${this.accessToken}` },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }

      this.profile = await response.json();
      localStorage.setItem('profile', JSON.stringify(this.profile));
    },
  },
});
