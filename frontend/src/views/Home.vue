<script setup>
import { ref, watch } from "vue";
import api from "@/api.js";
import { useUserStore } from "@/stores/user.js";

import Option from "@/components/Option.vue";
import CategorySelect from "@/components/CategorySelect.vue";
import TextBox from "@/components/TextBox.vue";
import Input from "@/components/Input.vue";
import Button from "@/components/Button.vue";
import FileUpload from "@/components/FileUpload.vue";
import Checkbox from "@/components/Checkbox.vue";
import Toggle from "@/components/Toggle.vue";
import ProfileMenu from "@/components/ProfileMenu.vue";

const userStore = useUserStore();

const typeOptions = [
    { value: "COMPLAINT", label: "Жалоба", icon: "mdi-flag" },
    { value: "SUGGESTION", label: "Предложение", icon: "mdi-lightbulb" },
    { value: "QUESTION", label: "Вопрос", icon: "mdi-book" },
    { value: "REQUEST", label: "Запрос", icon: "mdi-dots-horizontal" },
];

const locationOptions = [
    { id: "STUDENT_CAMPUS", label: "Студгородок", icon: "mdi-school" },
    { id: "DORMITORY", label: "Общежитие", icon: "mdi-home" },
    {
        id: "ACADEMIC_BUILDING",
        label: "Учебный корпус",
        icon: "mdi-office-building",
    },
    { id: "LIBRARY", label: "Библиотека", icon: "mdi-library-books" },
    { id: "CANTEEN", label: "Столовая", icon: "mdi-food-fork-drink" },
    { id: "SPORTS_COMPLEX", label: "Спорткомплекс", icon: "mdi-dumbbell" },
    { id: "MEDICAL_CENTER", label: "Медпункт", icon: "mdi-hospital-box" },
];

const categoryOptions = [
    { id: "ACCOMMODATION", label: "Расселение", icon: "mdi-home" },
    { id: "BATHROOM", label: "Санузел", icon: "mdi-water" },
    { id: "ELECTRICITY", label: "Электричество", icon: "mdi-lightning-bolt" },
    { id: "HEATING", label: "Отопление", icon: "mdi-fire" },
    { id: "CLEANLINESS", label: "Чистота", icon: "mdi-broom" },
    { id: "NOISE", label: "Шум", icon: "mdi-volume-high" },
    { id: "PLUMBING", label: "Сантехника", icon: "mdi-wrench" },
    { id: "FURNITURE", label: "Мебель", icon: "mdi-sofa" },
    { id: "INTERNET", label: "Интернет", icon: "mdi-wifi" },
    { id: "OTHER", label: "Другое", icon: "mdi-dots-horizontal" },
];

const timeframeOptions = [
    { id: "ONE_DAY", label: "1 день" },
    { id: "TWO_DAYS", label: "2 дня" },
    { id: "THREE_DAYS", label: "3 дня" },
    { id: "FIVE_DAYS", label: "5 дней" },
    { id: "ONE_WEEK", label: "1 неделя" },
    { id: "TWO_WEEKS", label: "2 недели" },
    { id: "ONE_MONTH", label: "1 месяц" },
];

const selectedType = ref("COMPLAINT");
const selectedLocation = ref(null);
const selectedCategory = ref(null);
const selectedTimeframe = ref(null);
const errorMessage = ref("");
const successMessage = ref("");
const message = ref("");
const attachments = ref([]);
const consent = ref(false);

watch(selectedLocation, () => {
    errorMessage.value = "";
});

watch(selectedCategory, () => {
    errorMessage.value = "";
});

watch(message, () => {
    errorMessage.value = "";
});

watch(consent, () => {
    errorMessage.value = "";
    successMessage.value = "";
});

const handleSubmit = async () => {
    if (!userStore.isAuthenticated) {
        errorMessage.value =
            "Необходимо войти в систему для отправки обращения";
        return;
    }

    if (selectedType.value === "COMPLAINT") {
        if (!selectedLocation.value) {
            errorMessage.value = "Выберите место обращения";
            return;
        }

        if (!selectedCategory.value) {
            errorMessage.value = "Выберите категорию проблемы";
            return;
        }
    }

    if (!message.value.trim()) {
        errorMessage.value = "Опишите вашу проблему";
        return;
    }

    if (!consent.value) {
        errorMessage.value =
            "Необходимо согласие на обработку персональных данных";
        return;
    }

    try {
        // Get profile data
        const profile = userStore.profile;
        fullName = profile.firstname + " " + profile.lastname

        const appealData = {
            type: selectedType.value,
            campusLocation:
                selectedType.value === "COMPLAINT"
                    ? selectedLocation.value
                    : "STUDENT_CAMPUS",
            problemCategory:
                selectedType.value === "COMPLAINT" ? selectedCategory.value : "OTHER",
            timeframe: selectedTimeframe.value || null,
            description: message.value.trim(),
            contactName: profile.fullName || '',
            contactPhone: profile.phone || '',
            contactEmail: profile.email || '',
            personalDataConsent: consent.value,
        };

        await api.submitAppeal(appealData);

        // Form cleanup
        selectedType.value = "COMPLAINT";
        selectedLocation.value = null;
        selectedCategory.value = null;
        selectedTimeframe.value = null;
        message.value = "";
        attachments.value = [];
        consent.value = false;
        successMessage.value = "Заявка зарегистрирована";
        errorMessage.value = "";
    } catch (error) {
        errorMessage.value =
            error.response?.data?.message ||
            error.message ||
            "Ошибка при отправке обращения";
        errorMessage.value = `Ошибка: ${errorMessage}`;
        console.error("Ошибка при отправке обращения:", error);
    }
};
</script>

<template>
    <main class="main">
        <div class="content">
            <div class="header">
                <img src="@/assets/prof.jpg" class="logo" />
                <ProfileMenu />
            </div>
            <div class="greet">
                <h1>Напишите о своей проблеме</h1>
                <p>
                    Расскажите о волнующей вас проблеме, и мы постараемся помочь
                    в ее решении
                </p>
            </div>
            <div class="problem">
                <div class="options-wrapper">
                    <h2>Тип обращения</h2>
                    <div class="options">
                        <Option v-for="option in typeOptions" :key="option.value" :label="option.label"
                            :icon="option.icon" :selected="option.value === selectedType"
                            @select="selectedType = option.value" />
                    </div>
                    <Transition name="fade">
                        <div v-if="selectedType === 'COMPLAINT'" class="categories">
                            <CategorySelect v-model="selectedLocation" :categories="locationOptions"
                                label="Место обращения" />
                            <CategorySelect v-model="selectedCategory" :categories="categoryOptions"
                                label="Категория" />
                            <CategorySelect v-model="selectedTimeframe" :categories="timeframeOptions"
                                label="Сроки решения (опционально)" />
                        </div>
                    </Transition>
                </div>
                <div class="problem-description">
                    <h2>Описание проблемы</h2>
                    <TextBox v-model="message" />
                    <div class="file-upload">
                        <FileUpload v-model:files="attachments" :max-files="4" />
                        <p class="restrictions">
                            Форматы: JPG, PNG, HEIC, PDF. До 4 файлов, максимум
                            10 МБ каждый.
                        </p>
                    </div>
                </div>
            </div>
            <div class="submit">
                <div class="consent-wrapper">
                    <Checkbox v-model="consent" label="Я согласен на обработку персональных данных" />
                    <router-link to="/privacy" class="privacy-link">
                        (Читать соглашение)
                    </router-link>
                </div>
                <Button :disabled="!consent" @click="handleSubmit">Отправить обращение</Button>
            </div>
            <p v-if="successMessage" class="success-msg">{{ successMessage }}</p>
            <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>
        <footer class="footer">
            <router-link to="/privacy" class="footer-link">Политика конфиденциальности</router-link>
        </footer>
    </main>
</template>

<style scoped>
.main {
    display: flex;
    flex-direction: column;
    align-items: center;
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
    width: 100%;
    box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
    gap: 20px;
}

.header {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.logo {
    max-width: 150px;
    height: auto;
}

.greet {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.problem,
.submit {
    width: 100%;
}

.problem {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.options-wrapper {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.options {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.fade-enter-active,
.fade-leave-active {
    transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(-15px);
}

.problem-description {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.categories {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.consent {
    margin-bottom: 20px;
}

.success-msg {
    color: #2e7d32;
    font-weight: bold;
    text-align: center;
    margin: 0;
}

.error-msg {
    color: #d32f2f;
    font-weight: bold;
    text-align: center;
    margin: 0;
}

h1 {
    font-family: var(--font-header);
    font-size: 22px;
    color: var(--color-main-inverted);
}

h2 {
    color: var(--color-main-inverted);
    font-size: 22px;
    font-weight: bold;
}

p {
    margin: 0;
}

p.restrictions {
    font-size: 14px;
    margin-top: 8px;
    max-width: 240px;
}

footer {
    margin-top: 35px;
}

.consent-wrapper {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
    margin-bottom: 10px;
}

.privacy-link {
    font-size: 13px;
    margin-left: 35px;
    /* Отступ, чтобы выровнять текст ссылки под текстом чекбокса, подстрой по дизайну */
}

@media (min-width: 768px) {
    .main {
        padding: 30px;
    }

    .content {
        padding: 35px;
        max-width: 900px;
    }

    .dropdown a {
        font-size: 20px;
    }

    p.restrictions {
        font-size: 20px;
        max-width: none;
    }

    .categories {
        flex-direction: row;
    }

    h1 {
        font-size: 40px;
    }

    h2 {
        font-size: 26px;
    }
}
</style>
