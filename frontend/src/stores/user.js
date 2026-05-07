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
    saveAuthTokens({ accessToken, refreshToken, profile, accessTokenExpiresInSeconds }) {
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

      if (profile !== undefined) {
        this.profile = profile;
        if (profile) localStorage.setItem('profile', JSON.stringify(profile));
        else localStorage.removeItem('profile');

        if (profile?.userRole) {
          this.userRole = profile.userRole;
          localStorage.setItem('userRole', profile.userRole);
        }
        else localStorage.removeItem('userRole');
      }

      if (accessTokenExpiresInSeconds !== undefined) {
        this.accessTokenExpiresInSeconds = accessTokenExpiresInSeconds;
        if (accessTokenExpiresInSeconds != null) localStorage.setItem('accessTokenExpiresInSeconds', accessTokenExpiresInSeconds);
        else localStorage.removeItem('accessTokenExpiresInSeconds');
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

    async fetchMe() {
      const res = await api.getMe()
      this.profile = res.data
    },

    async initAuth() {
      try {
        await this.fetchMe()
      } catch (error) {
        this.profile = null
        this.clearAuthTokens()
      }
    }
  },
});
