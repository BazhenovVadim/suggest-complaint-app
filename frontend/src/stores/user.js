import { defineStore } from "pinia";
import api from '@/api'

export const useUserStore = defineStore("user", {
  state: () => ({
    profile: null,
    accessToken: null,
    userId: null,
    refreshToken: localStorage.getItem("refreshToken") || null,
    accessTokenExpiresInSeconds: null,
  }),
  actions: {
    saveAuthTokens({ accessToken, refreshToken, userId, accessTokenExpiresInSeconds }) {
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
      localStorage.setItem("refreshToken", this.refreshToken);
      if (accessTokenExpiresInSeconds) {
        localStorage.setItem("accessTokenExpiresInSeconds", accessTokenExpiresInSeconds);
      }
    },

    clearAuthTokens() {
      this.accessToken = null;
      this.refreshToken = null;
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("accessTokenExpiresInSeconds");
    },

    async register({ email, password }) {
      const response = await api.register({ email, password });
      this.saveAuthTokens(response.data);
    },

    async login({ email, password }) {

      const response = await api.login({ email, password })

      saveAuthTokens(response.data);
    },

    async logout() {
      try {
        await api.logout()
      } catch (_) { };

      this.clearAuthTokens();
    },

    async fetchProfile() {
      const response = await fetch("/api/user/profile", {
        headers: { Authorization: `Bearer ${this.refreshToken}` },
      });
      this.profile = await response.json();
    },
  },
});
