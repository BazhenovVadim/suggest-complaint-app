<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import IconMdiAccountCircle from '~icons/mdi/account-circle'

const router = useRouter();
const showDropdown = ref(false);
const isAuthenticated = computed(() => !!localStorage.getItem('accessToken'));
const containerRef = ref(null);

const toggleDropdown = () => {
    showDropdown.value = !showDropdown.value;
};

const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    showDropdown.value = false;
    router.push('/login');
};

const goToStatuses = () => {
    alert('Статусы заявок');
    showDropdown.value = false;
};

const goToLogin = () => {
    router.push('/login');
    showDropdown.value = false;
};

onMounted(() => {
  document.addEventListener("click", (e) => {
    if (showDropdown.value && !containerRef.value.contains(e.target)) showDropdown.value = false;
  });
});
</script>

<template>
    <div class="profile-container" ref="containerRef">
        <IconMdiAccountCircle class="profile-icon" @click="toggleDropdown" />
        <transition name="dropdown">
            <div v-if="showDropdown" class="dropdown">
                <a v-if="!isAuthenticated" href="#" @click.prevent="goToLogin">Войти</a>
                <template v-else>
                    <a href="#" @click.prevent="goToStatuses">Статусы заявок</a>
                    <a href="#" @click.prevent="logout">Выйти</a>
                </template>
            </div>
        </transition>
    </div>
</template>

<style scoped>
.profile-container {
    position: relative;
}

.profile-icon {
    width: 60px;
    height: auto;
    margin-top: 6px;
    color: #00ad53;
    cursor: pointer;
    transition: color 0.2s ease;
}

.profile-icon:hover {
    color: var(--color-accent);
}

.dropdown {
    position: absolute;
    top: 90%;
    right: 0;
    background: white;
    padding: 10px;
    border: 1px solid var(--color-border);
    border-radius: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    z-index: 10;
    min-width: 150px;
    margin-top: 5px;
}

.dropdown a {
    display: block;
    padding: 10px 10px;
    text-decoration: none;
    font-size: 20px;
    color: var(--color-main-inverted);
    border-radius: 14px;
    transition: background 0.2s ease;
}

.dropdown a:hover {
    background: #f5f5f5;
}

.dropdown-enter-active,
.dropdown-leave-active {
      transition: opacity 0.2s ease, transform 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-10px) scale(0.95);
}

@media (min-width: 768px) {
    .profile-icon {
        width: 70px;
    }
    .dropdown {
        padding: 16px 12px;
        min-width: 200px;
    }
    .dropdown a {
    font-size: 22px;
    }
}
</style>
