<script setup>
import { computed } from "vue";

const props = defineProps({
    modelValue: Boolean,
    label: String,
});

const emit = defineEmits(["update:modelValue"]);

const handleChange = (event) => {
    emit("update:modelValue", event.target.checked);
};

const inputId = computed(() =>
    props.label
        ? "cb-" + props.label.replace(/[^a-zA-Z0-9]/g, "-")
        : "cb-default",
);
</script>

<template>
    <div class="consent">
        <input type="checkbox" :id="inputId" :checked="modelValue" @change="handleChange" />
        <label :for="inputId">
            <slot>{{ label }}</slot>
        </label>
    </div>
</template>

<style scoped>
.consent {
    display: flex;
    align-items: center;
    gap: 10px;
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
    font-size: 16px;
    font-weight: 400;
    color: var(--color-font);
}

@media (min-width: 768px) {
    .consent label {
        font-size: 22px;
    }
}
</style>
