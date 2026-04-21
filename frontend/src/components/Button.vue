<script setup></script>

<template>
    <button class="button">
        <div>
            <slot name="icon" />
        </div>
        <slot />
    </button>
</template>

<style scoped>
.button {
    border: none;
    border-radius: 16px;
    font-family: var(--font-text);
    font-size: 23px;
    background: var(--color-accent);
    color: var(--color-main);
    padding: 15px;
    font-weight: 600;
    width: 100%;
    height: 75px;
    transition: background 0.2s ease;
    cursor: pointer;
}

.button:hover {
    background: #50b377;
}

@media (min-width: 768px) {
    .button {
        font-size: 30px;
    }
}
</style>
