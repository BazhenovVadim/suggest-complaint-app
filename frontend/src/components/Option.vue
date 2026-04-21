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
    border-radius: 20px;
    background: var(--color-bg-option);
    padding: 20px;
    font-family: var(--font-text);
    font-size: 20px;
    color: var(--color-font-option);
    transition: 0.2s ease;
}

.option:hover {
    background: var(--color-bg-option-hover);
}

.option.selected {
    background: var(--color-bg-option-selected);
    color: var(--color-font-option-selected);
}
</style>
