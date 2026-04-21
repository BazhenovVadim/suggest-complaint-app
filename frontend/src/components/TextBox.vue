<script setup>
const model = defineModel();
</script>

<template>
    <textarea
        class="textbox"
        v-model="model"
        placeholder="Опишите здесь вашу проблему. Чем подробнее вы опишете проблему, тем проще будет её решить."
    ></textarea>
</template>

<style scoped>
.textbox {
    border: 1px solid var(--color-border);
    border-radius: 20px;
    background: var(--color-main);
    padding: 15px;
    font-family: var(--font-text);
    font-size: 18px;
    color: var(--color-font);
    resize: none;
    box-sizing: border-box;
    width: 100%;
    height: 180px;
}

.textbox::placeholder {
    color: var(--color-font);
}

@media (min-width: 768px) {
    .textbox {
        font-size: 26px;
    }
}
</style>
