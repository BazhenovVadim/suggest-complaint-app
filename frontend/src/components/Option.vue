<script setup>
const props = defineProps({
    label: String,
    selected: Boolean,
});
const emit = defineEmits(["select"]);
</script>

<template>
    <button
        class="option"
        :class="{ selected: props.selected }"
        @click="emit('select')"
    >
        <div>
            <slot name="icon" />
        </div>
        {{ props.label }}
    </button>
</template>

<style scoped>
.option {
    background: var(--color-bg-option);
    border: 1px solid var(--color-border);
    border-radius: 16px;
    padding: 12px 0px;
    font-family: var(--font-text);
    font-size: 16px;
    color: var(--color-font-option);
    transition: background 0.2s ease;

    display: flex;
    flex-grow: 1;
    justify-content: center;
}

.option:hover {
    background: var(--color-bg-option-hover);
}

.option.selected {
    background: var(--color-bg-option-selected);
    color: var(--color-font-option-selected);
}

@media (min-width: 768px) {
    .option {
        border-radius: 20px;
        padding: 20px;
        font-size: 20px;
    }
}
</style>
