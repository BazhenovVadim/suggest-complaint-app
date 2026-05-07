<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const role = computed(() => localStorage.getItem('role') || 'USER');

const logout = () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('role');
  router.push('/login');
};
</script>

<template>
  <main class="main">
    <h1>Админ-панель</h1>
    <p>Вы вошли как: <strong>{{ role }}</strong></p>
    <p>Если вы видите эту страницу, проверка роли сработала корректно.</p>
    <button class="logout" @click="logout">Выйти</button>
  </main>
</template>

<style scoped>
.main {
  border: 1px solid var(--color-border);
  border-radius: 24px;
  padding: 24px;
  box-sizing: border-box;
  width: 100%;
  background: white;
}
.logout {
  margin-top: 12px;
}
</style>
