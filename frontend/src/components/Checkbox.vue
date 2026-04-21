<script setup>
const props = defineProps({
    modelValue: Boolean,
    label: String,
});

const emit = defineEmits(["update:modelValue"]);

const handleChange = (event) => {
    emit("update:modelValue", event.target.checked);
};
</script>

<template>
    <div class="consent">
        <input
            type="checkbox"
            :id="label"
            :checked="modelValue"
            @change="handleChange"
        />
        <label :for="label">{{ label }}</label>
    </div>
</template>

<style scoped>
.consent {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
}

.consent input[type="checkbox"] {
    min-width: 30px;
    height: 30px;
    appearance: none;
    -webkit-appearance: none;
    background: white;
    border: 2px solid var(--color-border);
    border-radius: 5px;
    cursor: pointer;
    position: relative;
    transition:
        background 0.2s ease,
        border-color 0.2s ease;
}

.consent input[type="checkbox"]:checked {
    background: var(--color-accent);
    border-color: var(--color-accent-second);
}

.consent input[type="checkbox"]::after {
    content: "";
    position: absolute;
    left: 7px;
    width: 8px;
    height: 18px;
    border-right: 4px solid white;
    border-bottom: 4px solid white;
    transform: rotate(45deg);
    opacity: 0;
    transition: opacity 0.2s;
}

.consent input[type="checkbox"]:checked::after {
    opacity: 1;
}

.consent label {
    font-size: 18px;
    font-weight: 400;
    color: var(--color-font);
}

@media (min-width: 768px) {
    .consent label {
        font-size: 26px;
    }
}
</style>
