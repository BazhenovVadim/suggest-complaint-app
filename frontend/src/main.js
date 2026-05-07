import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import { createPinia } from 'pinia';
import './style.css'
import App from './App.vue';
import Home from './views/Home.vue';
import Login from './views/Login.vue';
import Register from './views/Register.vue';
import Admin from './views/Admin.vue';

const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/admin', component: Admin, meta: { requiresAdmin: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

const app = createApp(App);
app.use(router);
app.use(createPinia());
app.mount('#app');


router.beforeEach((to, from, next) => {
  if (!to.meta.requiresAdmin) return next();

  const role = localStorage.getItem('role') || 'USER';
  const token = localStorage.getItem('accessToken');

  if (token && role === 'ADMIN') return next();
  return next('/login');
});
