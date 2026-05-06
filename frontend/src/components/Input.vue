<script setup>
const model = defineModel();
defineProps({
  placeholder: {
    type: String,
    default: 'Введите текст...'
  },
})
</script>

<template>
    <input
        class="input"
        v-model="model"
        :placeholder="placeholder"
    ></input>
</template>

<style scoped>
.input {
    border: 1px solid var(--color-border);
    border-radius: 16px;
    background: var(--color-main);
    padding: 15px;
    font-family: var(--font-text);
    font-size: 18px;
    color: var(--color-font);
    resize: none;
    box-sizing: border-box;
    min-width: 0;
    transition: opacity 0.3s ease;
}

.input:disabled {
    opacity: 0.5;
}

.input::placeholder {
    color: var(--color-font);
}

@media (min-width: 768px) {
    .input {
        font-size: 26px;
    }
}
</style>
