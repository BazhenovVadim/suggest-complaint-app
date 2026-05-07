<script setup>
import { ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "../stores/user";

import MdiEye from "~icons/mdi/eye";
import MdiEyeOff from "~icons/mdi/eye-off";

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
const route = useRoute();
const userStore = useUserStore();

const firstname = ref("");
const lastname = ref("");
const middlename = ref("");
const phone = ref("");

const isEmailError = ref(false);
const isEmailShaking = ref(false);
const isPasswordError = ref(false);
const isPasswordShaking = ref(false);
const isFirstnameError = ref(false);
const isFirstnameShaking = ref(false);
const isLastnameError = ref(false);
const isLastnameShaking = ref(false);
const isMiddlenameError = ref(false);
const isMiddlenameShaking = ref(false);
const isPhoneError = ref(false);
const isPhoneShaking = ref(false);
const showPassword = ref(false);
const showConfirmPassword = ref(false);

const Icons = {
    eye: MdiEye,
    eyeOff: MdiEyeOff,
};

watch(email, () => { isEmailError.value = false; error.value = ""; });
watch([password, confirmPassword], () => { isPasswordError.value = false; error.value = ""; });
watch(firstname, () => { isFirstnameError.value = false; error.value = ""; });
watch(lastname, () => { isLastnameError.value = false; error.value = ""; });
watch(middlename, () => { isMiddlenameError.value = false; error.value = ""; });
watch(phone, () => { error.value = ""; });


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
    } else if (field === 'lastname') {
        isLastnameError.value = true;
        isLastnameShaking.value = false;
        setTimeout(() => isLastnameShaking.value = true, 10);
        setTimeout(() => isLastnameShaking.value = false, 600);
    } else if (field === 'firstname') {
        isFirstnameError.value = true;
        isFirstnameShaking.value = false;
        setTimeout(() => isFirstnameShaking.value = true, 10);
        setTimeout(() => isFirstnameShaking.value = false, 600);
    } else if (field === 'middlename') {
        isMiddlenameError.value = true;
        isMiddlenameShaking.value = false;
        setTimeout(() => isMiddlenameShaking.value = true, 10);
        setTimeout(() => isMiddlenameShaking.value = false, 600);
    } else if (field === 'phone') {
        isPhoneError.value = true;
        isPhoneShaking.value = false;
        setTimeout(() => isPhoneShaking.value = true, 10);
        setTimeout(() => isPhoneShaking.value = false, 600);
    }
};


const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
const validatePassword = (password) => /^(?=.*[0-9])(?=.*[A-Z]).{8,}$/.test(password);
const validateName = (name) => /^[а-яА-ЯёЁa-zA-Z\s]+$/.test(name);
const validatePhone = (phone) => /^\+?[0-9\s()-]{7,20}$/.test(phone);

const handleSubmit = async () => {

    if (!consent.value) {
        error.value = "Необходимо согласие на обработку персональных данных";
        return;
    }

    if (!lastname.value.trim()) {
        triggerError('lastname', "Введите фамилию");
        return;
    }

    if (!validateName(lastname.value)) {
        triggerError('lastname', "Фамилия должна содержать только буквы");
        return;
    }

    if (!firstname.value.trim()) {
        triggerError('firstname', "Введите имя");
        return;
    }

    if (!validateName(firstname.value)) {
        triggerError('firstname', "Имя должно содержать только буквы");
        return;
    }
    if (middlename.value && !validateName(middlename.value)) {
        triggerError('middlename', "Отчество должно содержать только буквы");
        return;
    }

    if (phone.value && !validatePhone(phone.value)) {
        triggerError('phone', "Введите корректный номер телефона");
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

    const registerData = {
        email: email.value,
        password: password.value,
        firstname: firstname.value,
        lastname: lastname.value,
        middlename: middlename.value,
        phone: phone.value
    };

    const vkUserId = route.query.vkUserId;
    const tgUserId = route.query.tgUserId;

    if (vkUserId) {
        registerData.vk_user_id = vkUserId;
    }

    if (tgUserId) {
        registerData.telegram_user_id = tgUserId;
    }

    try {
        await userStore.register(registerData);

        // Save profile data locally
        // const profileData = {
        //     firstname: firstname.value,
        //     middlename: middlename.value,
        //     lastname: lastname.value,
        //     email: email.value,
        //     phone: phone.value,
        //     fullName: `${firstname.value} ${middlename.value ? middlename.value + ' ' : ''}${lastname.value}`.trim()
        // };

        await userStore.login({ email: email.value, password: password.value });
        router.push(userStore.userRole === "ADMIN" ? "/admin-profile" : "/profile");
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
                    <h2>Фамилия</h2>
                    <Input class="lastname" :class="{ 'input-error': isLastnameError, 'shake': isLastnameShaking }"
                        v-model="lastname" placeholder="Фамилия" required />
                </div>

                <div class="field-group">
                    <h2>Имя</h2>
                    <Input class="firstname" :class="{ 'input-error': isFirstnameError, 'shake': isFirstnameShaking }"
                        v-model="firstname" placeholder="Имя" required />
                </div>

                <div class="field-group">
                    <h2>Отчество <span class="optional">(если есть)</span></h2>
                    <Input class="middlename"
                        :class="{ 'input-error': isMiddlenameError, 'shake': isMiddlenameShaking }" v-model="middlename"
                        placeholder="Отчество" />
                </div>

                <div class="field-group">
                    <h2>Телефон <span class="optional">(опционально)</span></h2>
                    <Input class="phone" :class="{ 'input-error': isPhoneError, 'shake': isPhoneShaking }"
                        v-model="phone" placeholder="Телефон" />
                </div>

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

                <p class="password-hint">Пароль должен содержать заглавные буквы (A-Z), цифры (0-9) и содержать минимум
                    8 символов.</p>

                <div class="field-group">
                    <h2>Подтверждение пароля</h2>
                    <div class="input-wrapper">
                        <Input class="confirm-password"
                            :class="{ 'input-error': isPasswordError, 'shake': isPasswordShaking }"
                            :type="showConfirmPassword ? 'text' : 'password'" v-model="confirmPassword"
                            placeholder="Подтвердите пароль" required />
                        <button type="button" class="toggle-password-btn"
                            @click="showConfirmPassword = !showConfirmPassword"
                            :title="showConfirmPassword ? 'Скрыть пароль' : 'Показать пароль'">
                            <component :is="showConfirmPassword ? Icons.eye : Icons.eyeOff" />
                        </button>
                    </div>
                </div>

                <Checkbox v-model="consent" label="Я согласен на обработку персональных данных" />


                <Button type="submit" :disabled="loading || !consent">
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
.password,
.confirm-password,
.firstname,
.lastname,
.middlename {
    width: 100%;
}

.input-wrapper :deep(input) {
    padding-right: 40px;
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

.optional {
    opacity: 0.7;
    font-weight: normal;
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
