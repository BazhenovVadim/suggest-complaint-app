import { defineStore } from "pinia";

export const useUserStore = defineStore("user", {
  state: () => ({
    profile: null,
    accessToken: null,
    refreshToken: localStorage.getItem("refreshToken") || null,
  }),
  actions: {
    async register({ email, password }) {
      const response = await axios.post("/api/auth/register", {
        email: email.value,
        password: password.value,
      });
      this.accessToken = response.data.accessToken;
      this.refreshToken = response.data.refreshToken;
      localStorage.setItem("refreshToken", this.refreshToken);
    },
    async login({ email, password }) {
      const response = await axios.post("/api/auth/login", {
        email: email.value,
        password: password.value,
      });
      this.accessToken = response.data.accessToken;
      this.refreshToken = response.data.refreshToken;
      localStorage.setItem("refreshToken", this.refreshToken);
    },
    logout() {
      this.profile = null;
      this.accessToken = null;
      this.refreshToken = null;
      localStorage.removeItem("token");
    },
    async fetchProfile() {
      const response = await fetch("/api/user/profile", {
        headers: { Authorization: `Bearer ${this.refreshToken}` },
      });
      this.profile = await response.json();
    },
  },
});
