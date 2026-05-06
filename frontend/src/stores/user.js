import { defineStore } from "pinia";
import api from '@/api'

export const useUserStore = defineStore("user", {
  state: () => ({
    profile: null,
    accessToken: localStorage.getItem("accessToken") || null,
    userId: localStorage.getItem("userId") || null,
    refreshToken: localStorage.getItem("refreshToken") || null,
    accessTokenExpiresInSeconds: localStorage.getItem("accessTokenExpiresInSeconds")
      ? Number(localStorage.getItem("accessTokenExpiresInSeconds"))
      : null,
  }),
  actions: {
    saveAuthTokens({ accessToken, refreshToken, userId, accessTokenExpiresInSeconds }) {
      if (accessToken) {
        this.accessToken = accessToken;
        localStorage.setItem("accessToken", accessToken);
      } else {
        this.accessToken = null;
        localStorage.removeItem("accessToken");
      }

      if (refreshToken) {
        this.refreshToken = refreshToken;
        localStorage.setItem("refreshToken", refreshToken);
      } else {
        this.refreshToken = null;
        localStorage.removeItem("refreshToken");
      }

      if (userId) {
        this.userId = userId;
        localStorage.setItem("userId", userId);
      } else {
        this.userId = null;
        localStorage.removeItem("userId");
      }

      if (accessTokenExpiresInSeconds != null) {
        this.accessTokenExpiresInSeconds = accessTokenExpiresInSeconds;
        localStorage.setItem("accessTokenExpiresInSeconds", accessTokenExpiresInSeconds);
      } else {
        this.accessTokenExpiresInSeconds = null;
        localStorage.removeItem("accessTokenExpiresInSeconds");
      }
    },

    clearAuthTokens() {
      this.accessToken = null;
      this.refreshToken = null;
      this.userId = null;
      this.accessTokenExpiresInSeconds = null;
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("userId");
      localStorage.removeItem("accessTokenExpiresInSeconds");
    },

    async register({ email, password }) {
      const response = await api.register({ email, password });
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
    },
  },
});
