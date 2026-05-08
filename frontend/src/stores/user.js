import { defineStore } from "pinia";
import api from '@/api';

export const useUserStore = defineStore("user", {
  state: () => {
    let savedProfile = null;
    try {
      const rawProfile = localStorage.getItem("profile");
      if (rawProfile) savedProfile = JSON.parse(rawProfile);
    } catch (e) {
      console.error("Failed to parse profile from localStorage");
    }

    return {
      profile: savedProfile,
      accessToken: localStorage.getItem("accessToken") || null,
      userId: localStorage.getItem("userId") || null,
      refreshToken: localStorage.getItem("refreshToken") || null,
      accessTokenExpiresInSeconds: localStorage.getItem("accessTokenExpiresInSeconds")
        ? Number(localStorage.getItem("accessTokenExpiresInSeconds"))
        : null,
      userRole: localStorage.getItem("userRole") || null,
    };
  },
  getters: {
    isAuthenticated: (state) => !!state.profile
  },
  actions: {
    saveAuthTokens({ accessToken, refreshToken, profile, user, userId, accessTokenExpiresInSeconds }) {
      const resolvedProfile = profile ?? user;

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

      if (resolvedProfile !== undefined) {
        this.profile = resolvedProfile;
        if (resolvedProfile) localStorage.setItem('profile', JSON.stringify(resolvedProfile));
        else localStorage.removeItem('profile');

        // ВНИМАНИЕ: Проверьте, что ваш бэк возвращает userRole, а не role.
        // Если возвращает role, замените resolvedProfile.userRole на resolvedProfile.role
        const role = resolvedProfile?.userRole || resolvedProfile?.role;

        if (role) {
          this.userRole = role;
          localStorage.setItem('userRole', role);
        } else {
          this.userRole = null;
          localStorage.removeItem('userRole');
        }
      }

      const resolvedUserId = userId ?? resolvedProfile?.id;
      if (resolvedUserId !== undefined) {
        this.userId = resolvedUserId;
        if (resolvedUserId) localStorage.setItem('userId', resolvedUserId);
        else localStorage.removeItem('userId');
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
      this.profile = null;

      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("userId");
      localStorage.removeItem("accessTokenExpiresInSeconds");
      localStorage.removeItem("profile"); // Исправлено с userProfile на profile
      localStorage.removeItem("userRole");
    },

    async register(registerData) {
      const response = await api.register(registerData);
      this.saveAuthTokens(response.data);
    },

    async login({ email, password }) {
      const response = await api.login({ email, password });
      this.saveAuthTokens(response.data);
    },

    async logout() {
      try {
        await api.logout({ userId: this.userId, refreshToken: this.refreshToken });
      } catch (_) { }
      this.clearAuthTokens();
    },

    async fetchMe() {
      const res = await api.getMe();
      this.profile = res.data;
      // Если getMe возвращает роль, стоит обновить ее тут
      if (res.data.userRole || res.data.role) {
        this.userRole = res.data.userRole || res.data.role;
        localStorage.setItem('userRole', this.userRole);
      }
    },

    async initAuth() {
      try {
        if (this.accessToken) {
          await this.fetchMe();
        }
      } catch (error) {
        this.profile = null;
        this.clearAuthTokens();
      }
    }
  },
});
