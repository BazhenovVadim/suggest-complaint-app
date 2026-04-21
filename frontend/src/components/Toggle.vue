<script setup>
const props = defineProps({
    modelValue: Boolean,
    label: String
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
    <div class="toggle-wrapper">
        <input
        type="checkbox"
        :checked="modelValue"
        @change="emit('update:modelValue', $event.target.checked)"
        class="toggle-input"
        />
        <span class="toggle-slider"></span>
        <label class="toggle-label">{{ label }}</label>
    </div>
</template>

<style scoped>
.toggle-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-direction: row;
}

.toggle-label {
    font-size: 18px;
    color: var(--color-font);
    flex: 1 1 auto;
    min-width: 0;
}

.toggle-input {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 30px;
    min-width: 50px;
    min-height: 30px;
    flex: 0 0 auto;
    appearance: none;
    -webkit-appearance: none;
    background: #e2e5e9;
    border: none;
    border-radius: 30px;
    cursor: pointer;
    transition: background 0.3s ease;
    margin: 0;
    padding: 0;
}

.toggle-input:checked {
    background: var(--color-accent);
}

.toggle-input::before {
    content: '';
    position: absolute;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: white;
    top: 2px;
    left: 2px;
    transition: left 0.3s ease, box-shadow 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-input:checked::before {
    left: 22px;
}

.toggle-slider {
    display: none;
}

@media (min-width: 768px) {
    .toggle-label {
        font-size: 20px;
    }
}
</style>
