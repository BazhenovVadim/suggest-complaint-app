<script setup>
import MdiFlag from '~icons/mdi/flag-variant'
import MdiLightbulb from '~icons/mdi/lightbulb-on-outline'
import MdiBook from '~icons/mdi/book-open-blank-variant-outline'
import MdiDotsHorizontal from '~icons/mdi/dots-horizontal'
import MdiCircleMedium  from "~icons/mdi/circle-medium";

const Icons = {
    "mdi-flag": MdiFlag,
    "mdi-lightbulb": MdiLightbulb,
    "mdi-book": MdiBook,
    "mdi-dots-horizontal": MdiDotsHorizontal,
    "mdi-circle-medium": MdiCircleMedium,
}

const props = defineProps({
    label: String,
    selected: Boolean,
    icon: String,
});
const emit = defineEmits(["select"]);
</script>

<template>
    <button
        class="option"
        :class="{ selected: props.selected }"
        @click="emit('select')"
    >
        <component :is="Icons[props.icon] || Icons['mdi-circle-medium']" />
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
    align-items: center;
    gap: 7px;
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
