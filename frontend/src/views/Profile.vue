<script setup>
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from "vue";

import IconMdiAccountCircle from "~icons/mdi/account-circle";
import AppealItem from "../components/AppealItem.vue";

const activeTab = ref("active");
const tabs = [
    { id: "active", label: "Активные заявки" },
    { id: "completed", label: "Завершенные заявки" },
];

function selectTab(id) {
    activeTab.value = id;
}

const searchQuery = ref("");

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

onMounted(() => {
    nextTick(() => {
        updateIndicator();
        window.addEventListener('resize', updateIndicator);
    });
});

watch(activeTab, () => {
    nextTick(updateIndicator);
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', updateIndicator);
});

// Заглушки в форме DTO (AppealResponseDto). В продакшене данные будут приходить с сервера.
const unprocessedAppeals = ref([
    {
        id: "3f1a7e30-0000-4000-8000-000000000001",
        appealNumber: 1337,
        type: "Жалоба",
        campusLocation: "Студгородок",
        problemCategory: "Общежитие/Комната",
        timeframe: "Срочно",
        description:
            "В комнате холодно, батареи еле тёплые — температура ниже нормы, просьба проверить систему отопления.",
        attachments: [],
        contactName: "Костик В. В.",
        contactPhone: "+79993398485",
        contactEmail: "kostik444@mail.ru",
        personalDataConsent: true,
        createdAt: "2025-11-11T12:45:00Z",
        status: "Новая",
        userId: "e8a1a9f0-0000-4000-8000-000000000011",
    },
    {
        id: "3f1a7e30-0000-4000-8000-000000000002",
        appealNumber: 1334,
        type: "Жалоба",
        campusLocation: "Студгородок",
        problemCategory: "Общежитие/Комната",
        timeframe: "Среднесрочно",
        description:
            "В санузле плохой напор воды, горячая вода отсутствует периодически.",
        attachments: [],
        contactName: "Иванова А. С.",
        contactPhone: "+79990001122",
        contactEmail: "ivanova@mail.ru",
        personalDataConsent: true,
        createdAt: "2025-11-10T09:30:00Z",
        status: "Новая",
        userId: "e8a1a9f0-0000-4000-8000-000000000012",
    },
    {
        id: "3f1a7e30-0000-4000-8000-000000000003",
        appealNumber: 1333,
        type: "Жалоба",
        campusLocation: "Студгородок",
        problemCategory: "Общежитие/Комната",
        timeframe: "Долгосрочно",
        description:
            "Соседи громко ведут себя по ночам, просьба провести профилактическую беседу.",
        attachments: [],
        contactName: "Петров Д. Л.",
        contactPhone: "+79992223344",
        contactEmail: "petrov@mail.ru",
        personalDataConsent: true,
        createdAt: "2025-11-09T23:10:00Z",
        status: "Новая",
        userId: "e8a1a9f0-0000-4000-8000-000000000013",
    },
]);

const processingAppeals = ref([
    {
        id: "3f1a7e30-0000-4000-8000-000000000004",
        appealNumber: 1335,
        type: "Предложение",
        campusLocation: "Учебный корпус",
        problemCategory: "Учебный процесс",
        timeframe: "Среднесрочно",
        description:
            "Предлагаю установить дополнительные вытяжные решётки в старых корпусах.",
        attachments: ["vent-proposal.pdf"],
        contactName: "Витя Д. Д.",
        contactPhone: "+792949398485",
        contactEmail: "ogr34@mail.ru",
        personalDataConsent: true,
        createdAt: "2025-11-10T13:55:00Z",
        status: "На рассмотрении",
        userId: "e8a1a9f0-0000-4000-8000-000000000014",
    },
]);

const completedAppeals = ref([
    {
        id: "3f1a7e30-0000-4000-8000-000000000005",
        appealNumber: 1336,
        type: "Предложение",
        campusLocation: "Кампус B",
        problemCategory: "Благоустройство",
        timeframe: "Долгосрочно",
        description:
            "Предлагаю поставить урны возле входа в корпус для уменьшения мусора.",
        attachments: [],
        contactName: "Сидорова Н. М.",
        contactPhone: "+79998887766",
        contactEmail: "sidorova@mail.ru",
        personalDataConsent: true,
        createdAt: "2025-11-08T15:20:00Z",
        status: "Завершено",
        userId: "e8a1a9f0-0000-4000-8000-000000000015",
    },
]);

const currentAppeals = computed(() => {
    let list = [];
    if (activeTab.value === "active")
        list = [...unprocessedAppeals.value, ...processingAppeals.value];
    else list = completedAppeals.value;

    if (!searchQuery.value) return list;
    const q = searchQuery.value.toLowerCase();
    return list.filter((a) => {
        return (
            String(a.appealNumber ?? a.number ?? "")
                .toLowerCase()
                .includes(q) ||
            (a.description && a.description.toLowerCase().includes(q)) ||
            (a.contactName && a.contactName.toLowerCase().includes(q)) ||
            (a.contactEmail && a.contactEmail.toLowerCase().includes(q)) ||
            (a.contactPhone && a.contactPhone.toLowerCase().includes(q)) ||
            (a.problemCategory &&
                a.problemCategory.toLowerCase().includes(q)) ||
            (a.campusLocation && a.campusLocation.toLowerCase().includes(q)) ||
            (a.title && a.title.toLowerCase().includes(q)) ||
            (a.excerpt && a.excerpt.toLowerCase().includes(q))
        );
    });
});

function onView(appeal) {
    console.log("Посмотреть заявку:", appeal);
}
</script>

<template>
    <main class="profile">
        <aside class="sidebar" aria-label="Профиль">
            <div class="brand">
                <img src="../assets/prof.jpg" class="logo" />
            </div>

            <div class="user">
                <IconMdiAccountCircle class="avatar" />
                <div class="user-info">
                    <div class="name">Пользователь</div>
                    <div class="email">user@profspb.ru</div>
                    <button class="logout">Выйти</button>
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
                        :appeal="appeal" @view="onView" />
                </div>
                <footer class="pagination">
                    <div class="showing">
                        Показано {{ currentAppeals.length }} из
                        {{ currentAppeals.length }} заявок
                    </div>
                    <div class="pager">
                        <button class="pbtn">◀</button>
                        <button class="pbtn active">1</button>
                        <button class="pbtn">▶</button>
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

.user-info .name {
    font-weight: 600;
    margin-bottom: 4px;
}

.user-info .email {
    font-size: 13px;
    color: var(--color-font);
    margin-bottom: 8px;
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

.header-actions .search {
    width: 280px;
    max-width: 40vw;
    padding: 12px 14px;
    border-radius: 10px;
    border: 1px solid var(--color-border, #e6e6e6);
    font-family: var(--font-text);
    font-weight: 500;
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
