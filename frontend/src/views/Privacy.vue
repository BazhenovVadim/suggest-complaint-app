<script setup>
import { useRouter } from 'vue-router';
import PrivacyContent from '@/components/PrivacyContent.vue';

const router = useRouter();

const handleBack = () => {
    if (window.history.length > 1) {
        router.back();
    } else {
        router.push('/');
    }
};
</script>

<template>
    <main class="main">
        <div class="content">
            <button @click="handleBack" class="back-btn">← Назад</button>
            <h1>Согласие на обработку персональных данных</h1>
            
            <PrivacyContent class="full-page-text" />
        </div>
    </main>
</template>

<style scoped>
.main { display: flex; justify-content: center; padding: 15px; }
.content {
    border: 1px solid var(--color-border);
    border-radius: 36px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    box-sizing: border-box;
    box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
    gap: 20px;
    width: 100%;
    max-width: 900px;
    background: var(--color-bg);
}
.back-btn {
    background: var(--color-bg-option);
    border: none;
    cursor: pointer;
    padding: 14px;
    border-radius: 12px;
    font-family: var(--font-text);
    font-size: 15px;
    color: var(--color-font);
    transition: background 0.3s ease;
}
.back-btn:hover { background: var(--color-bg-option-hover); }
h1 { font-family: var(--font-header); font-size: 26px; color: var(--color-main-inverted); margin: 0; }
.full-page-text { width: 100%; }

@media (min-width: 768px) {
    .main { padding: 30px; }
    .content { padding: 35px; }
    h1 { font-size: 36px; }
}
</style>