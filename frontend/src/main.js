import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import { createPinia } from "pinia";
import App from "./App.vue";
import "./style.css";

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
    // Импортируем store внутри guard, чтобы избежать циклических зависимостей
    import('./stores/user').then(({ useUserStore }) => {
        const userStore = useUserStore();

        if (to.meta.requiresAuth && !userStore.accessToken) {
            next("/login");
        } else if (to.meta.requiresAdmin && userStore.userRole !== "ADMIN") {
            next("/profile");
        } else {
            next();
        }
    });
});

const app = createApp(App);
const pinia = createPinia();

// ВАЖНО: pinia должна быть подключена ДО router!
app.use(pinia);
app.use(router);

// Теперь можно безопасно инициализировать пользователя
import { useUserStore } from "./stores/user";
const userStore = useUserStore();
await userStore.initAuth(); // Раскомментируйте, когда добавите метод getMe на бэкенде

app.mount("#app");