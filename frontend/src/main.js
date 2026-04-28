import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import { createPinia } from 'pinia';
import './style.css'
import App from './App.vue';
import Login from './components/Login.vue';
import Home from './components/Home.vue';

const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

const app = createApp(App);
app.use(router);
app.use(createPinia());
app.mount('#app');
