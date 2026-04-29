<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import Input from "../components/Input.vue";
import Button from "../components/Button.vue";
import Checkbox from "../components/Checkbox.vue";

const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const consent = ref(false);
const error = ref('');
const loading = ref(false);
const router = useRouter();

const handleSubmit = async () => {
    loading.value = true;
    error.value = '';
    
    if (password.value !== confirmPassword.value) {
        error.value = 'Пароли не совпадают';
        loading.value = false;
        return;
    }
    
    if (!consent.value) {
        error.value = 'Необходимо согласие на обработку персональных данных';
        loading.value = false;
        return;
    }
    
    try {
        const response = await axios.post('http://localhost:8080/api/auth/register', {
            email: email.value,
            password: password.value,
        });
        alert('Регистрация успешна! Теперь войдите.');
        router.push('/login');
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
        <h1>Регистрация</h1>
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
            <div class="field-group">
                <h2>Подтверждение пароля</h2>
                <Input
                    class="confirm-password"
                    v-model="confirmPassword"
                    type="password"
                    placeholder="Подтвердите пароль"
                    required
                />
            </div>
            <Checkbox
                v-model="consent"
                label="Я согласен на обработку персональных данных"
            />
            <Button type="submit" :disabled="loading">Зарегистрироваться</Button>
        </form>
        <p v-if="error">{{ error }}</p>

        <div class="toggle-login">
            Уже есть аккаунт?
            <router-link to="/login">
                Войти
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

.email, .password, .confirm-password {
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
