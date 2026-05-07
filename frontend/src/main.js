import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import { createPinia } from "pinia";
import { useUserStore } from "./stores/user";

import "./style.css";
import App from "./App.vue";
import Home from "./views/Home.vue";
import Login from "./views/Login.vue";
import Register from "./views/Register.vue";
import Profile from "./views/Profile.vue";
import AdminProfile from "./views/AdminProfile.vue";

const routes = [
  { path: "/", component: Home, meta: { requiresAuth: false } },
  { path: "/login", component: Login, meta: { requiresAuth: false } },
  { path: "/register", component: Register, meta: { requiresAuth: false } },
  { path: "/profile", component: Profile, meta: { requiresAuth: true } },
  { path: "/admin-profile", component: AdminProfile, meta: { requiresAuth: true, requiresAdmin: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const userStore = useUserStore();
  const resolvedRole = userStore.userRole ?? userStore.profile?.role ?? null;

  if (to.meta.requiresAuth && !userStore.accessToken) {
    next("/login");
  } else if (to.meta.requiresAdmin && resolvedRole !== "ADMIN") {
    next("/profile");
  } else {
    next();
  }
});

const pinia = createPinia();
const app = createApp(App);

app.use(pinia);
app.use(router);

const userStore = useUserStore();
// await userStore.initAuth()

app.mount("#app");
