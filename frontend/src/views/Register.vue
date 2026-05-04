<script setup>
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";

import Input from "../components/Input.vue";
import Button from "../components/Button.vue";
import Checkbox from "../components/Checkbox.vue";

const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const consent = ref(false);
const error = ref("");
const loading = ref(false);
const router = useRouter();

const isEmailError = ref(false);
const isEmailShaking = ref(false);
const isPasswordError = ref(false);
const isPasswordShaking = ref(false);

watch(email, () => { isEmailError.value = false; error.value = ""; });
watch([password, confirmPassword], () => { isPasswordError.value = false; error.value = ""; });


const triggerError = (field, msg) => {
    error.value = msg;
    if (field === 'email') {
        isEmailError.value = true;
        isEmailShaking.value = false;
        setTimeout(() => isEmailShaking.value = true, 10); 
        setTimeout(() => isEmailShaking.value = false, 600); 
    } else if (field === 'password') {
        isPasswordError.value = true;
        isPasswordShaking.value = false;
        setTimeout(() => isPasswordShaking.value = true, 10);
        setTimeout(() => isPasswordShaking.value = false, 600);
    }
};


const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
const validatePassword = (password) => /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/.test(password);

const handleSubmit = async () => {
   
    if (!consent.value) {
        error.value = "Необходимо согласие на обработку персональных данных";
        return;
    }

    if (!validateEmail(email.value)) {
        triggerError('email', "Введите корректный email адрес");
        return;
    }

    if (!validatePassword(password.value)) {
        triggerError('password', "Пароль не соответствует требованиям безопасности");
        return;
    }

    if (password.value !== confirmPassword.value) {
        triggerError('password', "Пароли не совпадают");
        return;
    }

    loading.value = true;
    error.value = "";

    try {
        const response = await axios.post(
            "http://localhost:8080/api/auth/register",
            {
                email: email.value,
                password: password.value,
            },
        );
        alert("Регистрация успешна! Теперь войдите.");
        router.push("/login");
    } catch (err) {
        error.value = `Ошибка: ${err.response?.data?.message || "Неизвестная ошибка"}`;
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <main class="main">
        <div class="content">
            <img src="../assets/prof.jpg" class="logo" alt="Логотип" />
            <h1>Регистрация</h1>
            <form class="form" @submit.prevent="handleSubmit" novalidate>
                <div class="field-group">
                    <h2>Email</h2>
                    <Input
                        class="email"
                        :class="{ 'input-error': isEmailError, 'shake': isEmailShaking }"
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
                        :class="{ 'input-error': isPasswordError, 'shake': isPasswordShaking }"
                        v-model="password"
                        type="password"
                        placeholder="Пароль"
                        required
                    />
                </div>
                
                <p class="password-hint">Пароль должен содержать строчные и заглавные буквы a-z, цифры 0-9</p>
                
                <div class="field-group">
                    <h2>Подтверждение пароля</h2>
                    <Input
                        class="confirm-password"
                        :class="{ 'input-error': isPasswordError, 'shake': isPasswordShaking }"
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
                
                
                <Button 
                    type="submit" 
                    :disabled="loading || !consent"
                >
                    Зарегистрироваться
                </Button>
            </form>
            
            <p v-if="error" class="error-msg">{{ error }}</p>

            <div class="toggle-login">
                Уже есть аккаунт?
                <router-link to="/login"> Войти </router-link>
            </div>
        </div>
    </main>
</template>

<style scoped>
.main {
    display: flex;
    justify-content: center;
    padding: 15px;
}

.content {
    border: 1px solid var(--color-border);
    border-radius: 36px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    box-sizing: border-box;
    box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
    gap: 20px;
}

.logo {
    max-width: 300px;
    height: auto;
}

.form {
    display: flex;
    flex-direction: column;
    gap: 20px;
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

.email,
.password,
.confirm-password {
    width: 100%;
}

.password-hint {
    font-size: 13px;
    color: var(--color-font);
    opacity: 0.7;
    margin: -10px 0 0 0;
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

.form :deep(button:disabled) {
    background-color: #d3d3d3 !important; 
    color: #808080 !important; 
    border-color: #d3d3d3 !important;
    cursor: not-allowed !important; 
    opacity: 0.7;
    transform: none !important; 
}
.error-msg {
    color: #d32f2f;
    font-weight: bold;
    text-align: center;
    margin: 0;
}

.input-error {
    border-radius: 4;
    box-shadow: 0 0 5px rgba(211, 47, 47, 0.5);
}
:deep(.input-error input),
.input-error {
    border: 1px solid #d32f2f !important;
    outline-color: #d32f2f !important;
    border-radius: 16px !important; 
    box-shadow: 0 0 5px rgba(211, 47, 47, 0.5);
}

.shake {
    animation: shake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
}

@keyframes shake {
    10%, 90% { transform: translate3d(-2px, 0, 0); }
    20%, 80% { transform: translate3d(4px, 0, 0); }
    30%, 50%, 70% { transform: translate3d(-6px, 0, 0); }
    40%, 60% { transform: translate3d(6px, 0, 0); }
}

@media (min-width: 768px) {
    .main {
        padding: 30px;
    }
    .content {
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