<script setup>
import { ref } from "vue";
import { api } from "../api";

import Option from "../components/Option.vue";
import CategorySelect from "../components/CategorySelect.vue";
import TextBox from "../components/TextBox.vue";
import Input from "../components/Input.vue";
import Button from "../components/Button.vue";
import FileUpload from "../components/FileUpload.vue";
import Checkbox from "../components/Checkbox.vue";
import Toggle from "../components/Toggle.vue";
import ProfileMenu from "../components/ProfileMenu.vue";

const isAuthenticated = ref(!!localStorage.getItem("accessToken"));

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
const message = ref("");
const attachments = ref([]);
const name = ref("");
const phone = ref("");
const email = ref("");
const anonymous = ref(false);
const consent = ref(false);

const handleSubmit = async () => {
    if (!isAuthenticated.value) {
        alert("Необходимо войти в систему для отправки обращения");
        return;
    }

    if (!selectedLocation.value) {
        alert("Выберите место обращения");
        return;
    }

    if (!selectedCategory.value) {
        alert("Выберите категорию проблемы");
        return;
    }

    if (!message.value.trim()) {
        alert("Опишите вашу проблему");
        return;
    }

    if (!consent.value) {
        alert("Необходимо согласие на обработку персональных данных");
        return;
    }

    if (!anonymous.value && (!name.value.trim() || !email.value.trim())) {
        alert("Заполните контактные данные или включите анонимную отправку");
        return;
    }

    try {
        const appealData = {
            type: selectedType.value,
            campusLocation: selectedLocation.value,
            problemCategory: selectedCategory.value,
            timeframe: selectedTimeframe.value || null,
            description: message.value.trim(),
            contactName: anonymous.value ? null : name.value,
            contactPhone: anonymous.value ? null : phone.value,
            contactEmail: anonymous.value ? null : email.value,
            personalDataConsent: consent.value,
        };

        await api.post(
            "/api/appeals",
            appealData,
            {
                headers: {
                    "Content-Type": "application/json",
                },
            },
        );

        // Form cleanup
        selectedType.value = "COMPLAINT";
        selectedLocation.value = null;
        selectedCategory.value = null;
        selectedTimeframe.value = null;
        message.value = "";
        attachments.value = [];
        name.value = "";
        phone.value = "";
        email.value = "";
        anonymous.value = false;
        consent.value = false;
    } catch (error) {
        const errorMessage =
            error.response?.data?.message ||
            error.message ||
            "Ошибка при отправке обращения";
        alert(`Ошибка: ${errorMessage}`);
        console.error("Ошибка при отправке обращения:", error);
    }
};
</script>

<template>
    <main class="main">
        <div class="content">
            <div class="header">
                <img src="../assets/prof.jpg" class="logo" />
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
                        <Option
                            v-for="option in typeOptions"
                            :key="option.value"
                            :label="option.label"
                            :icon="option.icon"
                            :selected="option.value === selectedType"
                            @select="selectedType = option.value"
                        />
                    </div>
                    <div class="categories">
                        <CategorySelect
                            v-model="selectedLocation"
                            :categories="locationOptions"
                            label="Место обращения"
                        />
                        <CategorySelect
                            v-model="selectedCategory"
                            :categories="categoryOptions"
                            label="Категория"
                        />
                        <CategorySelect
                            v-model="selectedTimeframe"
                            :categories="timeframeOptions"
                            label="Сроки решения (опционально)"
                        />
                    </div>
                </div>
                <div class="problem-description">
                    <h2>Описание проблемы</h2>
                    <TextBox v-model="message" />
                    <div class="file-upload">
                        <FileUpload
                            v-model:files="attachments"
                            :max-files="4"
                        />
                        <p class="restrictions">
                            Форматы: JPG, PNG, HEIC, PDF. До 4 файлов, максимум
                            10 МБ каждый.
                        </p>
                    </div>
                </div>
            </div>
            <div class="contacts">
                <div class="contacts-header">
                    <h2 style="margin: 0">
                        Контакты для ответа
                        <span style="color: #999999">(необязательно)</span>
                    </h2>
                    <Toggle v-model="anonymous" label="Отправить анонимно" />
                </div>

                <div class="inputs">
                    <Input
                        class="name"
                        v-model="name"
                        placeholder="Ваше имя"
                        :disabled="anonymous"
                    />
                    <Input
                        v-model="phone"
                        placeholder="Телефон"
                        :disabled="anonymous"
                    />
                    <Input
                        v-model="email"
                        placeholder="E-mail"
                        :disabled="anonymous"
                    />
                </div>
            </div>
            <div class="submit">
                <Checkbox
                    v-model="consent"
                    label="Я согласен на обработку персональных данных"
                />
                <Button @click="handleSubmit">Отправить обращение</Button>
            </div>
        </div>
        <footer>Ну футер там и т.д.</footer>
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
.contacts,
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

.inputs {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
}

.contacts-header {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
    width: 100%;
    margin: 20px 0;
}

.consent {
    margin-bottom: 20px;
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
    .contacts-header {
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
    }
    .categories {
        flex-direction: row;
    }
    .inputs {
        grid-template-columns: 1fr 1fr;
    }
    .name {
        grid-column: span 2;
    }
    h1 {
        font-size: 40px;
    }
    h2 {
        font-size: 26px;
    }
}
</style>
