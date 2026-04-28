<script setup>
import { ref } from "vue";
import Option from "./Option.vue";
import CategorySelect from "./CategorySelect.vue";
import TextBox from "./TextBox.vue";
import Input from "./Input.vue";
import Button from "./Button.vue";
import FileUpload from "./FileUpload.vue";
import Checkbox from "./Checkbox.vue";
import Toggle from "./Toggle.vue";

const options = ["Жалоба", "Предложение", "Проблема с обучением", "Другое"];
const categories = [
    { id: 1, label: "Общие вопросы", icon: "circle" },
    { id: 2, label: "Тех. поддержка", icon: "gear" },
    { id: 3, label: "Проблема с контентом", icon: "doc" },
    { id: 4, label: "Другое", icon: "more" },
];
const subcategories = [
    { id: 1, label: "Учебный план", icon: "doc" },
    { id: 2, label: "Платформа", icon: "gear" },
    { id: 3, label: "Оплата", icon: "circle" },
    { id: 4, label: "Система оценок", icon: "more" },
];
const selectedType = ref(options[0]);
const selectedCategory = ref(null);
const selectedSubcategory = ref(null);
const message = ref("");
const name = ref("");
const phone = ref("");
const email = ref("");
const anonymous = ref(false);
const consent = ref(false);
</script>

<template>
    <main class="main">
        <div class="header">
            <img src="../assets/prof.jpg" class="logo" />
            <a href="/login">кнопка</a>
        </div>
        <div class="greet">
            <h1>Напишите о своей проблеме</h1>
            <p>
                Расскажите о волнующей вас проблеме, и мы постараемся помочь в ее
                решении
            </p>
        </div>
        <div class="problem">
            <div class="options-wrapper">
                <h2>Тип обращения</h2>
                <div class="options">
                    <Option
                        v-for="option in options"
                        :key="option"
                        :label="option"
                        :selected="option === selectedType"
                        @select="selectedType = option"
                    />
                </div>
                <div class="categories">
                    <CategorySelect
                        v-model="selectedCategory"
                        :categories="categories"
                        label="Категория"
                    />
                    <CategorySelect
                        v-model="selectedSubcategory"
                        :categories="subcategories"
                        label="Подкатегория"
                    />
                </div>
            </div>
            <div class="problem-description">
                <h2>Описание проблемы</h2>
                <TextBox v-model="message" />
                <div class="file-upload">
                    <FileUpload />
                    <p class="restrictions">Форматы: JPG, PNG, PDF до 10 МБ</p>
                </div>
            </div>
        </div>
        <div class="contacts">
            <div class="contacts-header">
                <h2 style="margin: 0;">
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
            <Button>Отправить обращение</Button>
        </div>
    </main>
    <footer>Ну футер там и т.д.</footer>
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
    width: 100%;
    box-shadow: 0px 0px 5px rgba(0,0,0,0.1); 
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
    max-width: 130px;
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
}

footer {
    margin-top: 35px;
}

@media (min-width: 768px) {
    .main {
        padding: 35px;
    }
    p.restrictions {
        font-size: 20px;
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
