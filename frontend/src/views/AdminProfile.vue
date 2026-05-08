<script setup>
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import api from "@/api.js";
import { useUserStore } from "@/stores/user.js";
import {
    translate,
    TYPE_TRANSLATIONS,
    LOCATION_TRANSLATIONS,
    CATEGORY_TRANSLATIONS,
    STATUS_TRANSLATIONS,
} from "@/utils/translations";


import IconMdiAccountCircle from "~icons/mdi/account-circle";
import AppealItem from "@/components/AppealItem.vue";

const router = useRouter();
const userStore = useUserStore();

const activeTab = ref("unprocessed");
const tabs = [
    { id: "unprocessed", label: "Необработанные заявки" },
    { id: "processing", label: "Обрабатываемые заявки" },
    { id: "completed", label: "Завершенные заявки" },
];

function selectTab(id) {
    activeTab.value = id;
}

const appeals = ref([]);

const searchQuery = ref("");
const currentPage = ref(1);
const itemsPerPage = 10;

// moving bar
const tabsEl = ref(null);
const activeLeft = ref(0);
const activeWidth = ref(0);
const hoverLeft = ref(0);
const hoverWidth = ref(0);
const isHovering = ref(false);

const tabsStyle = computed(() => ({
    "--indicator-left": activeLeft.value + "px",
    "--indicator-width": activeWidth.value + "px",
    "--hover-left": hoverLeft.value + "px",
    "--hover-width": (isHovering.value ? hoverWidth.value : 0) + "px",
}));

function updateIndicator() {
    if (!tabsEl.value) return;
    const activeBtn = tabsEl.value.querySelector('.tab.active');
    if (activeBtn) {
        const btnRect = activeBtn.getBoundingClientRect();
        const containerRect = tabsEl.value.getBoundingClientRect();
        activeLeft.value = Math.max(0, btnRect.left - containerRect.left);
        activeWidth.value = btnRect.width;
    } else {
        activeLeft.value = 0;
        activeWidth.value = 0;
    }
}

function onTabHover(e) {
    if (!tabsEl.value) return;
    const btn = e.currentTarget;
    if (!btn) return;
    const btnRect = btn.getBoundingClientRect();
    const containerRect = tabsEl.value.getBoundingClientRect();
    const left = Math.max(0, btnRect.left - containerRect.left);
    const width = Math.min(btnRect.width, Math.max(0, containerRect.width - left));
    hoverLeft.value = left;
    hoverWidth.value = width;
    isHovering.value = true;
}

function onTabLeave() {
    isHovering.value = false;
}

const logout = async () => {
    await userStore.logout();
    router.push("/login");
};

onMounted(async () => {
    try {
        const response = await api.getAppeals();
        appeals.value = response.data;
    } catch (e) {
        console.error(e);
    }

    await nextTick();
    updateIndicator();
    window.addEventListener("resize", updateIndicator);
});

watch(activeTab, () => {
    nextTick(updateIndicator);
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', updateIndicator);
});

const unprocessedAppeals = computed(() =>
    appeals.value.filter(appeal => appeal.status === 'NEW')
);
const processingAppeals = computed(() =>
    appeals.value.filter(appeal => appeal.status === 'IN_PROGRESS')
);
const completedAppeals = computed(() =>
    appeals.value.filter(appeal => appeal.status === 'RESOLVED' || appeal.status === 'REJECTED')
);

const filteredAppeals = computed(() => {
    let list = [];
    if (activeTab.value === "unprocessed") list = unprocessedAppeals.value;
    else if (activeTab.value === "processing") list = processingAppeals.value;
    else list = completedAppeals.value;

    if (!searchQuery.value) return list;
    const q = searchQuery.value.toLowerCase();
    return list.filter((a) => {
        const typeRu = translate(a.type, TYPE_TRANSLATIONS, "").toLowerCase();
        const locationRu = translate(a.campusLocation ?? a.location, LOCATION_TRANSLATIONS, "").toLowerCase();
        const categoryRu = translate(a.problemCategory ?? a.category, CATEGORY_TRANSLATIONS, "").toLowerCase();
        const statusRu = translate(a.status, STATUS_TRANSLATIONS, "").toLowerCase();

        return (
            String(a.appealNumber ?? a.number ?? "")
                .toLowerCase()
                .includes(q) ||
            (a.description && a.description.toLowerCase().includes(q)) ||
            (a.contactName && a.contactName.toLowerCase().includes(q)) ||
            (a.contactEmail && a.contactEmail.toLowerCase().includes(q)) ||
            (a.contactPhone && a.contactPhone.toLowerCase().includes(q)) ||
            (a.title && a.title.toLowerCase().includes(q)) ||
            (a.excerpt && a.excerpt.toLowerCase().includes(q)) ||
            typeRu.includes(q) ||
            locationRu.includes(q) ||
            categoryRu.includes(q) ||
            statusRu.includes(q)
        );
    });
});

const totalPages = computed(() => {
    return Math.ceil(filteredAppeals.value.length / itemsPerPage);
});

const currentAppeals = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredAppeals.value.slice(start, end);
});

const pagerButtons = computed(() => {
    const buttons = [];
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage.value - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages.value, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
        buttons.push(i);
    }

    return buttons;
});

function onView(appeal) {
    console.log("Посмотреть заявку:", appeal);
}

function onStatusUpdated(updatedAppeal) {
    const index = appeals.value.findIndex(a => a.id === updatedAppeal.id);
    if (index !== -1) {
        appeals.value[index] = updatedAppeal;
    }
}

function goToPage(page) {
    if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page;
    }
}

function goToPreviousPage() {
    if (currentPage.value > 1) {
        currentPage.value--;
    }
}

function goToNextPage() {
    if (currentPage.value < totalPages.value) {
        currentPage.value++;
    }
}

watch(activeTab, () => {
    currentPage.value = 1;
});

watch(searchQuery, () => {
    currentPage.value = 1;
});
</script>

<template>
    <main class="profile">
        <aside class="sidebar" aria-label="Профиль">
            <div class="brand">
                <img src="@/assets/prof.jpg" class="logo" />
            </div>

            <div class="user">
                <IconMdiAccountCircle class="avatar" />
                <div class="user-info">
                    <div class="name">{{ userStore.profile.firstname + " " + userStore.profile.lastname }}</div>
                    <div class="email">{{ userStore.profile.email }}</div>
                    <div class="contacts">VK: {{ userStore.profile.vkUserId || "—" }}</div>
                    <div class="contacts">TG: {{ userStore.profile.telegramUserId || "—" }}</div>
                    <button class="logout" @click="logout">Выйти</button>
                </div>
            </div>

            <div class="sidebar-spacer"></div>
        </aside>

        <section class="main">
            <header class="main-header">
                <h1 class="title">Заявки</h1>
                <div class="header-actions">
                    <input v-model="searchQuery" type="search" class="search" placeholder="Поиск по заявкам"
                        aria-label="Поиск по заявкам" />
                    <button class="btn-new-appeal" @click="router.push('/')">Написать заявку</button>
                </div>
            </header>

            <nav class="tabs" role="tablist" aria-label="Типы заявок" ref="tabsEl" :style="tabsStyle">
                <button v-for="tab in tabs" :key="tab.id" :id="`tab-${tab.id}`" class="tab"
                    :class="{ active: activeTab === tab.id }" role="tab" :aria-selected="activeTab === tab.id"
                    @click="selectTab(tab.id)" @mouseenter="onTabHover" @mouseleave="onTabLeave" :data-tab="tab.id">
                    {{ tab.label }}
                </button>
                <div class="hoverbar" aria-hidden></div>
                <div class="indicator" aria-hidden></div>
            </nav>

            <div class="table-headers" aria-hidden>
                <div class="col id">ID</div>
                <div class="col type">Тип обращения</div>
                <div class="col category">Категория</div>
                <div class="col desc">Описание</div>
                <div class="col author">Автор</div>
                <div class="col date">Дата поступления</div>
                <div class="col status">Статус</div>
            </div>

            <section class="content">
                <div v-if="currentAppeals.length === 0" class="empty">
                    Нет заявок для отображения :(
                </div>
                <div class="appeals">
                    <AppealItem v-for="appeal in currentAppeals" :key="appeal.appealNumber ?? appeal.number"
                        :appeal="appeal" @view="onView" @status-updated="onStatusUpdated" />
                </div>
                <footer class="pagination">
                    <div class="showing">
                        Показано {{ currentAppeals.length }} из
                        {{ filteredAppeals.length }} заявок
                    </div>
                    <div class="pager">
                        <button class="pbtn" :disabled="currentPage === 1" @click="goToPreviousPage">◀</button>
                        <button v-for="page in pagerButtons" :key="page" class="pbtn"
                            :class="{ active: currentPage === page }" @click="goToPage(page)">
                            {{ page }}
                        </button>
                        <button class="pbtn" :disabled="currentPage === totalPages" @click="goToNextPage">▶</button>
                    </div>
                </footer>
            </section>
        </section>
    </main>
</template>

<style scoped>
.profile {
    display: flex;
    min-height: 100vh;
    background: var(--color-main, #ffffff);
    color: var(--color-text, #222);
}

/* Sidebar */
.sidebar {
    width: 280px;
    flex: 0 0 280px;
    background: var(--color-bg-option, #f5f5f5);
    border-right: 1px solid var(--color-border, #e6e6e6);
    padding: 28px 20px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}

.brand {
    margin-bottom: 28px;
}

.logo {
    max-width: 150px;
    height: auto;
}

.user {
    display: flex;
    gap: 12px;
    align-items: center;
}

.avatar {
    width: 60px;
    height: auto;
    color: #00ad53;
}

.user-info {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.user-info .name {
    font-weight: 600;
}

.user-info .email {
    font-size: 13px;
    color: var(--color-font);
}

.user-info .contacts {
    font-size: 13px;
    color: var(--color-font);
}

.logout {
    appearance: none;
    -webkit-appearance: none;
    background: transparent;
    border: 1px solid var(--color-border, #dcdcdc);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 13px;
    cursor: pointer;
    font-family: var(--font-text);
}

.sidebar-spacer {
    flex: 1 1 auto;
}

/* Main area */
.main {
    flex: 1 1 auto;
    padding: 28px 36px;
    box-sizing: border-box;
}

.main-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 18px;
}

.title {
    font-size: 30px;
    margin: 0;
    font-weight: 700;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}

.header-actions .search {
    width: 280px;
    max-width: 40vw;
    padding: 12px 14px;
    border-radius: 10px;
    border: 1px solid var(--color-border, #e6e6e6);
    font-family: var(--font-text);
    font-weight: 500;
}

.btn-new-appeal {
    appearance: none;
    -webkit-appearance: none;
    background: var(--color-accent, #2a9d8f);
    color: #fff;
    border: none;
    padding: 12px 20px;
    border-radius: 10px;
    font-family: var(--font-text);
    font-weight: 600;
    font-size: 15px;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity 0.2s ease;
}

.btn-new-appeal:hover {
    opacity: 0.9;
}

.tabs {
    display: flex;
    margin: 10px 0 30px 0;
    align-items: center;
    position: relative;
    padding-bottom: 12px;
}

.tabs::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 4px;
    background: var(--color-border, #e6e6e6);
    border-radius: 4px;
    z-index: 1;
}

.tab {
    background: transparent;
    border: none;
    padding: 12px 18px;
    border-radius: 8px;
    cursor: pointer;
    font-family: var(--font-text);
    font-weight: 600;
    font-size: 20px;
    color: var(--color-text, #222);
    position: relative;
}

.tab:hover {
    background: rgba(0, 0, 0, 0.02);
}

.tab.active {
    color: var(--color-accent, #2a9d8f);
}

.tabs .hoverbar {
    position: absolute;
    bottom: 0;
    left: var(--hover-left, 0);
    width: var(--hover-width, 0);
    height: 4px;
    background: var(--color-accent, #2a9d8f);
    opacity: 0.4;
    border-radius: 4px;
    z-index: 2;
    transition: left 200ms ease, width 200ms ease, opacity 160ms ease;
    pointer-events: none;
}

.tabs .indicator {
    position: absolute;
    bottom: 0;
    left: var(--indicator-left, 0);
    width: var(--indicator-width, 0);
    height: 4px;
    background: var(--color-accent, #2a9d8f);
    border-radius: 4px;
    z-index: 3;
    transition: left 350ms cubic-bezier(0.2, 0.8, 0.2, 1), width 350ms cubic-bezier(0.2, 0.8, 0.2, 1);
    pointer-events: none;
}

.table-headers {
    display: none;
    margin-bottom: 8px;
    color: var(--color-font);
    font-size: 14px;
    justify-content: center;
}

.content {
    margin-top: 8px;
}

.empty {
    padding: 40px 16px;
    color: var(--color-font);
}

.appeals {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.pagination {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 24px;
    color: var(--color-font, #7c7c7c);
}

.pager {
    display: flex;
    gap: 8px;
}

.pbtn {
    width: 40px;
    height: 36px;
    border-radius: 8px;
    border: 1px solid var(--color-border, #dcdcdc);
    background: transparent;
    cursor: pointer;
}

.pbtn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.pbtn.active {
    background: var(--color-accent, #cfeee0);
}

@media (max-width: 1024px) {
    .sidebar {
        display: none;
    }

    .profile {
        display: block;
    }

    .main {
        padding: 16px;
    }

    .tabs {
        overflow-x: auto;
    }

    .table-headers {
        display: none;
    }
}

@media (min-width: 1025px) {
    .table-headers {
        display: grid;
        grid-template-columns: 60px 140px 220px minmax(150px, 1fr) 140px 160px 330px;
        gap: 12px;
        font-weight: 600;
        padding: 0 18px;
    }
}
</style>
