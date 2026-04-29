<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import Input from "../components/Input.vue";
import Button from "../components/Button.vue";

const email = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);
const router = useRouter();

const handleSubmit = async () => {
    loading.value = true;
    error.value = '';
    
    try {
        const response = await axios.post('http://localhost:8080/api/auth/login', {
            email: email.value,
            password: password.value,
        });
        localStorage.setItem('accessToken', response.data.accessToken);
        localStorage.setItem('refreshToken', response.data.refreshToken);
        router.push('/');
    } catch (err) {
        error.value = `Ошибка: ${err.response?.data?.message || 'Неизвестная ошибка'}`;
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <main class="main">
        <img src="../assets/prof.jpg" class="logo" />
        <h1>Вход в систему</h1>
        <form class="form" @submit.prevent="handleSubmit">
            <div class="field-group">
                <h2>Email</h2>
                <Input
                    class="email"
                    v-model="email"
                    type="email"
                    placeholder="Email"
                    required
                />
            </div>
            <div class="field-group">
                <h2>Пароль</h2>
                <Input
                    class="password"
                    v-model="password"
                    type="password"
                    placeholder="Пароль"
                    required
                />
            </div>
            <Button type="submit" :disabled="loading">Войти</Button>
        </form>
        <p v-if="error">{{ error }}</p>

        <div class="toggle-login">
            Нет аккаунта?
            <router-link to="/register">
                Зарегистрироваться
            </router-link>
        </div>
    </main>
</template>


<style scoped>
.main {
    border: 1px solid var(--color-border);
    border-radius: 36px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    box-sizing: border-box;
    box-shadow: 0px 0px 5px rgba(0,0,0,0.1); 
    gap: 20px;
}

.logo {
    max-width: 300px;
    height: auto;
}

.form {
    display: flex;
    flex-direction: column;
    gap: 15px;
    width: 100%;
}

.field-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.field-group h2 {
    margin: 0;
}

.email, .password {
    width: 100%;
}

.toggle-login {
    text-align: center;
}

h1 {
    font-family: var(--font-header);
    font-size: 30px;
    color: var(--color-main-inverted);
}

h2 {
    color: var(--color-font);
    font-size: 20px;
    font-weight: bold;
}

a {
    text-decoration: none;
    color: var(--color-accent-second);
    transition: color 0.2s ease;
}

a:hover {
    color: #33724c;
}

@media (min-width: 768px) {
    .main {
        padding: 35px;
        min-width: 600px;
        width: 35vw;
    }
    h1 {
        font-size: 44px;
    }
    h2 {
        font-size: 26px;
    }
}
</style>