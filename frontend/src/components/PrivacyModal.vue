<script setup>
import { watch, onUnmounted } from 'vue';
import PrivacyContent from './PrivacyContent.vue';

const props = defineProps({
    isOpen: Boolean
});

const emit = defineEmits(['update:isOpen']);

const closeModal = () => {
    emit('update:isOpen', false);
};

const toggleBodyScroll = (isModalOpen) => {
    if (isModalOpen) {
        document.body.style.overflow = 'hidden';
    } else {
        document.body.style.overflow = '';
    }
};

watch(() => props.isOpen, (newVal) => {
    toggleBodyScroll(newVal);
});
onUnmounted(() => {
    document.body.style.overflow = '';
});
</script>

<template>
    <Teleport to="body">
        <Transition name="modal">
            <div v-if="isOpen" class="modal-overlay" @click.self="closeModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Согласие на обработку персональных данных</h2>
                        <button class="close-btn" @click="closeModal">✕</button>
                    </div>
                    
                    <div class="modal-body">
                        <PrivacyContent />
                    </div>
                    
                    <div class="modal-footer">
                        <button class="accept-btn" @click="closeModal">Понятно</button>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>

.modal-body {
    padding: 20px;
    overflow-y: auto;
}
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 20px;
    box-sizing: border-box;
}

.modal-content {
    background: var(--color-bg, #ffffff);
    border-radius: 20px;
    width: 100%;
    max-width: 800px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
    margin: 0;
    font-family: var(--font-header);
    font-size: 22px;
    color: var(--color-main-inverted);
}

.close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: var(--color-font);
    opacity: 0.6;
    transition: opacity 0.2s;
}

.close-btn:hover {
    opacity: 1;
}   

.privacy-text p {
    margin-bottom: 15px;
}

.modal-footer {
    padding: 20px 25px;
    border-top: 1px solid var(--color-border);
    display: flex;
    justify-content: flex-end;
}

.accept-btn {
    background: var(--color-accent-second, #4caf50);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    transition: filter 0.2s;
}

.accept-btn:hover {
    filter: brightness(0.9);
}

.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
    transition: transform 0.3s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
    transform: translateY(-20px);
}
</style>