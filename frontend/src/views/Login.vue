<script setup>
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "../stores/user";

import MdiEye from "~icons/mdi/eye";
import MdiEyeOff from "~icons/mdi/eye-off";

import Input from "../components/Input.vue";
import Button from "../components/Button.vue";

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const router = useRouter();
const userStore = useUserStore();

const isEmailError = ref(false);
const isEmailShaking = ref(false);
const isPasswordError = ref(false);
const isPasswordShaking = ref(false);
const showPassword = ref(false);

const Icons = {
    eye: MdiEye,
    eyeOff: MdiEyeOff,
};

watch(email, () => {
    isEmailError.value = false;
    error.value = "";
});

watch(password, () => {
    isPasswordError.value = false;
    error.value = "";
});

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

const handleSubmit = async () => {
    if (!validateEmail(email.value)) {
        triggerError('email', "Введите корректный email адрес");
        return;
    }

    if (!password.value) {
        triggerError('password', "Введите пароль");
        return;
    }

    loading.value = true;
    error.value = "";

    try {
        await userStore.login({ email: email.value, password: password.value });
        router.push("/");
    } catch (err) {
        error.value = `Ошибка: ${err.response?.data?.message || "Неизвестная ошибка"}`;
        isEmailError.value = true;
        isPasswordError.value = true;
        isEmailShaking.value = false;
        isPasswordShaking.value = false;
        setTimeout(() => {
            isEmailShaking.value = true;
            isPasswordShaking.value = true;
        }, 10);
        setTimeout(() => {
            isEmailShaking.value = false;
            isPasswordShaking.value = false;
        }, 600);
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <main class="main">
        <div class="content">
            <img src="../assets/prof.jpg" class="logo" />
            <h1>Вход в систему</h1>
            <form class="form" @submit.prevent="handleSubmit" novalidate>
                <div class="field-group">
                    <h2>Email</h2>
                    <Input class="email" :class="{ 'input-error': isEmailError, 'shake': isEmailShaking }"
                        v-model="email" type="email" placeholder="Email" required />
                </div>
                <div class="field-group">
                    <h2>Пароль</h2>
                    <div class="input-wrapper">
                        <Input class="password" :class="{ 'input-error': isPasswordError, 'shake': isPasswordShaking }"
                            :type="showPassword ? 'text' : 'password'" v-model="password" placeholder="Пароль"
                            required />
                        <button type="button" class="toggle-password-btn" @click="showPassword = !showPassword"
                            :title="showPassword ? 'Скрыть пароль' : 'Показать пароль'">
                            <component :is="showPassword ? Icons.eye : Icons.eyeOff" />
                        </button>
                    </div>
                </div>
                <Button type="submit" :disabled="loading">Войти</Button>
            </form>
            <p v-if="error" class="error-msg">{{ error }}</p>

            <div class="toggle-login">
                Нет аккаунта?
                <router-link to="/register"> Зарегистрироваться </router-link>
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

.input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
}

.toggle-password-btn {
    position: absolute;
    right: 12px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.6;
    transition: opacity 0.2s ease;
    color: var(--color-font);
}

.toggle-password-btn :deep(svg) {
    width: 24px;
    height: 24px;
}

.toggle-password-btn:hover {
    opacity: 1;
}

.email,
.password {
    width: 100%;
}

.input-wrapper :deep(input) {
    padding-right: 40px;
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

.error-msg {
    color: #d32f2f;
    font-weight: bold;
    text-align: center;
    margin: 0;
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

    10%,
    90% {
        transform: translate3d(-2px, 0, 0);
    }

    20%,
    80% {
        transform: translate3d(4px, 0, 0);
    }

    30%,
    50%,
    70% {
        transform: translate3d(-6px, 0, 0);
    }

    40%,
    60% {
        transform: translate3d(6px, 0, 0);
    }
}

.form :deep(button:disabled) {
    background-color: #d3d3d3 !important;
    color: #808080 !important;
    border-color: #d3d3d3 !important;
    cursor: not-allowed !important;
    opacity: 0.7;
    transform: none !important;
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
