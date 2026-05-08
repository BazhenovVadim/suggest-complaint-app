<template>
    <div class="appeal-row" role="article" tabindex="0">
        <div class="col id">#{{ displayNumber }}</div>

        <div class="col type">
            <div class="type-row">
                <span class="flag" aria-hidden>⚑</span>
                <span class="type-label">{{ displayType }}</span>
            </div>
            <div class="location">{{ displayCampusLocation }}</div>
        </div>

        <div class="col category">
            <div class="cat-title">{{ displayProblemCategory }}</div>
            <div class="cat-sub">{{ displayTimeframe }}</div>
        </div>

        <div class="col desc">
            <div class="excerpt">{{ fullDescription }}</div>
        </div>

        <div class="col author">
            <div class="author-name">{{ displayContactName }}</div>
            <div class="author-contact">{{ displayContactEmail }}</div>
            <div class="author-phone">{{ displayContactPhone }}</div>
        </div>

        <div class="col date">
            <div class="date-day">{{ displayDate }}</div>
            <div class="date-time">{{ displayTime }}</div>
        </div>

        <div class="col status">
            <span class="badge" :class="badgeClass">{{ statusText }}</span>
            <button class="btn-outline" @click="openModal">Просмотр заявки</button>
        </div>
    </div>

    <!-- Modal Overlay    -->
    <Teleport to="body">
        <Transition name="modal">
            <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
                <div class="modal-container">
                    <div class="modal-header">
                        <button class="back-btn" @click="closeModal" aria-label="Назад">
                            <MdiArrowLeft />
                        </button>
                        <h1 class="modal-title">Заявка #{{ displayNumber }}</h1>
                    </div>

                    <div class="modal-card">
                        <div class="detail-row">
                            <div class="detail-icon detail-icon--flag">
                                <MdiFlag />
                            </div>
                            <div class="detail-content">
                                <div class="detail-label">Тип обращения</div>
                                <div class="detail-value">{{ displayType }}</div>
                            </div>
                        </div>

                        <div class="divider" />

                        <div class="detail-row">
                            <div class="detail-icon detail-icon--location">
                                <MdiMapMarker />
                            </div>
                            <div class="detail-content">
                                <div class="detail-label">Локация</div>
                                <div class="detail-value">{{ displayCampusLocation }}</div>
                            </div>
                        </div>

                        <div class="divider" />

                        <div class="detail-row">
                            <div class="detail-icon detail-icon--category">
                                <MdiHome />
                            </div>
                            <div class="detail-content">
                                <div class="detail-label">Категория</div>
                                <div class="detail-value">{{ displayProblemCategory }}</div>
                            </div>
                        </div>

                        <div class="divider" />

                        <div class="detail-row">
                            <div class="detail-icon" :class="statusIconClass">
                                <component :is="statusIcon" />
                            </div>
                            <div class="detail-content">
                                <div class="detail-label" style="padding-left: 6px">Статус</div>
                                <span class="badge badge-modal" :class="badgeClass">{{ statusText }}</span>
                            </div>
                        </div>

                        <div class="divider" />

                        <div class="detail-row">
                            <div class="detail-icon detail-icon--desc">
                                <MdiFileText />
                            </div>
                            <div class="detail-content">
                                <div class="detail-label">Описание обращения</div>
                                <div class="detail-value detail-value--body">{{ fullDescription }}</div>
                            </div>
                        </div>

                        <div class="divider" />

                        <div class="detail-row">
                            <div class="detail-icon detail-icon--author">
                                <MdiAccount />
                            </div>
                            <div class="detail-content">
                                <div class="detail-label">Автор обращения</div>
                                <div class="detail-value">{{ displayContactName }}</div>
                                <div class="detail-value detail-value--sub">
                                    {{ displayContactEmail
                                    }}<span v-if="displayContactEmail && displayContactPhone">, </span>{{
                                        displayContactPhone }}
                                </div>
                            </div>
                        </div>

                        <div class="divider" />

                        <div class="detail-row">
                            <div class="detail-icon detail-icon--date">
                                <MdiCalendar />
                            </div>
                            <div class="detail-content">
                                <div class="detail-label">Дата поступления</div>
                                <div class="detail-value">
                                    {{ displayDate
                                    }}<span v-if="displayTime"> в {{ displayTime }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <Button v-if="showActionButton" @click="updateStatus">
                        {{ actionButtonText }}
                    </Button>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup>
import { defineProps, defineEmits, computed, ref } from "vue";
import api from "@/api";
import {
    translate,
    STATUS_TRANSLATIONS,
    TYPE_TRANSLATIONS,
    LOCATION_TRANSLATIONS,
    CATEGORY_TRANSLATIONS,
    TIMEFRAME_TRANSLATIONS,
} from "@/utils/translations";

import MdiArrowLeft from "~icons/mdi/arrow-left";
import MdiMapMarker from "~icons/mdi/map-marker";
import MdiFlag from "~icons/mdi/flag";
import MdiHome from "~icons/mdi/home";
import MdiClock from "~icons/mdi/clock";
import MdiFileText from "~icons/mdi/file-text";
import MdiAccount from "~icons/mdi/account";
import MdiCalendar from "~icons/mdi/calendar";
import MdiCheckCircle from "~icons/mdi/check-circle";
import MdiAlertCircle from "~icons/mdi/alert-circle";
import MdiClockTimeFour from "~icons/mdi/clock-time-four";

import Button from "@/components/Button.vue";

const props = defineProps({
    appeal: {
        type: Object,
        required: true,
    },
});

const emit = defineEmits(["view", "action", "status-updated"]);

const isModalOpen = ref(false);

function openModal() {
    isModalOpen.value = true;
    document.body.style.overflow = "hidden";
}

function closeModal() {
    isModalOpen.value = false;
    document.body.style.overflow = "";
}

function updateStatus() {
    if (props.appeal.status === "NEW") {
        console.log("updating status to IN_PROGRESS", props.appeal.id);
        api.updateAppealStatus(props.appeal.id, "IN_PROGRESS")
            .then((response) => {
                emit("status-updated", response.data);
                closeModal();
            })
            .catch((error) => alert(error.message));
    } else if (props.appeal.status === "IN_PROGRESS") {
        api.updateAppealStatus(props.appeal.id, "RESOLVED")
            .then((response) => {
                emit("status-updated", response.data);
                closeModal();
            })
            .catch((error) => alert(error.message));
    }
}

const displayNumber = computed(
    () => props.appeal?.appealNumber ?? "",
);
const rawType = computed(() => props.appeal?.type ?? "");
const displayType = computed(() =>
    translate(rawType.value, TYPE_TRANSLATIONS, rawType.value),
);
const rawCampusLocation = computed(() => props.appeal?.campusLocation ?? props.appeal?.location ?? "");
const displayCampusLocation = computed(() =>
    translate(rawCampusLocation.value, LOCATION_TRANSLATIONS, rawCampusLocation.value),
);
const rawProblemCategory = computed(() => props.appeal?.problemCategory ?? props.appeal?.category ?? "");
const displayProblemCategory = computed(() =>
    translate(rawProblemCategory.value, CATEGORY_TRANSLATIONS, rawProblemCategory.value),
);
const rawTimeframe = computed(() => props.appeal?.timeframe ?? "");
const displayTimeframe = computed(() =>
    translate(rawTimeframe.value, TIMEFRAME_TRANSLATIONS, rawTimeframe.value),
);

const fullDescription = computed(
    () => props.appeal?.description ?? "",
);

const displayContactName = computed(
    () => props.appeal?.contactName ?? "",
);
const displayContactPhone = computed(
    () => props.appeal?.contactPhone ?? "",
);
const displayContactEmail = computed(
    () => props.appeal?.contactEmail ?? "",
);

const created = computed(() => props.appeal?.createdAt ?? null);
const dateParts = computed(() => {
    if (!created.value) {
        const date = props.appeal?.date;
        const time = props.appeal?.time;
        if (date || time) return { date: date ?? "", time: time ?? "" };
        return { date: "", time: "" };
    }

    let d;
    try {
        if (
            typeof created.value === "string" ||
            typeof created.value === "number"
        ) {
            d = new Date(created.value);
        } else if (created.value instanceof Date) {
            d = created.value;
        } else {
            d = new Date(String(created.value));
        }
    } catch (e) {
        return { date: String(created.value), time: "" };
    }

    if (Number.isNaN(d.getTime())) {
        const s = String(created.value);
        if (s.includes("/")) {
            const [timePart, datePart] = s.split("/");
            return { date: datePart ?? s, time: timePart ?? "" };
        }
        return { date: s, time: "" };
    }

    return {
        date: d.toLocaleDateString("ru-RU"),
        time: d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }),
    };
});

const displayDate = computed(() => dateParts.value.date);
const displayTime = computed(() => dateParts.value.time);

const rawStatus = computed(() => props.appeal?.status ?? "");
const statusText = computed(() => {
    const s = rawStatus.value;
    if (s == null) return "";
    if (typeof s === "object" && s.name) return String(s.name);
    return translate(String(s), STATUS_TRANSLATIONS, String(s));
});

const isStatusNew = computed(() => {
    const key = String(rawStatus.value).toUpperCase();
    return key === "NEW";
});

const isStatusProcessing = computed(() => {
    const key = String(rawStatus.value).toUpperCase();
    return (
        key === "IN_PROGRESS" ||
        key === "INPROGRESS" ||
        key === "PROCESSING" ||
        key === "REVIEW"
    );
});

const isStatusDone = computed(() => {
    const key = String(rawStatus.value).toUpperCase();
    return key === "RESOLVED" || key === "REJECTED" || key === "DONE" || key === "COMPLETED";
});

const badgeClass = computed(() => {
    if (isStatusNew.value) return "badge-new";
    if (isStatusProcessing.value) return "badge-processing";
    if (isStatusDone.value) return "badge-done";
    return "badge-processing";
});

const statusIcon = computed(() => {
    if (isStatusDone.value) return MdiCheckCircle;
    if (isStatusProcessing.value) return MdiClockTimeFour;
    return MdiAlertCircle;
});

const statusIconClass = computed(() => {
    if (isStatusDone.value) return "detail-icon detail-icon--status-done";
    if (isStatusProcessing.value) return "detail-icon detail-icon--status-processing";
    return "detail-icon detail-icon--status-new";
});

const showActionButton = computed(() => !isStatusDone.value);

const actionButtonText = computed(() => {
    if (isStatusProcessing.value) return "Завершить обработку";
    return "Принять в обработку";
});

function view() {
    emit("view", props.appeal);
}
</script>

<style scoped>
/* List Row */
.appeal-row {
    box-sizing: border-box;
    display: grid;
    grid-template-columns: 60px 140px 220px minmax(150px, 1fr) 140px 160px 330px;
    gap: 12px;
    align-items: start;
    width: 100%;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid var(--color-border, #e6e6e6);
    background: var(--color-bg-option, #fff);
    font-family: var(--font-text);
    font-size: 15px;
}

.col {
    min-width: 0;
}

.id {
    font-weight: 700;
    color: var(--color-font, #666666);
    font-size: 14px;
}

.type-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
}

.type-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 15px;
}

.location {
    font-size: 13px;
    color: var(--color-text-muted, #8a8a8a);
}

.cat-title {
    font-weight: 700;
    font-size: 15px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.cat-sub {
    font-size: 13px;
    color: var(--color-text-muted, #8a8a8a);
}

.excerpt {
    font-size: 14px;
    color: var(--color-text-muted, #6f6f6f);
    line-height: 1.2;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.author-name {
    font-weight: 600;
    font-size: 15px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.author-contact,
.author-phone {
    font-size: 13px;
    color: var(--color-text-muted, #7a7a7a);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.date-day {
    font-weight: 600;
    font-size: 14px;
}

.date-time {
    font-size: 13px;
    color: var(--color-text-muted, #8a8a8a);
}

.status {
    display: flex;
    gap: 30px;
    align-items: center;
    justify-content: space-between;
}

.badge {
    padding: 6px 10px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 13px;
}

.badge-new {
    background: #ffd8b5;
    color: #8a4b00;
}

.badge-processing {
    background: #fef3c7;
    color: #92400e;
}

.badge-done {
    background: #eef6ff;
    color: #1b64b3;
}

.btn-outline {
    appearance: none;
    -webkit-appearance: none;
    border: 1px solid var(--color-border, #cbd5cf);
    background: transparent;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-family: var(--font-text);
    font-size: 14px;
}

@media (min-width: 1025px) {
    .appeal-row {
        font-size: 15px;
    }
}

/* Modal */
.modal-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.modal-container {
    background: #f5f5f5;
    border-radius: 20px;
    width: 100%;
    max-width: 860px;
    max-height: 90vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 28px 32px 32px;
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.18);
}

.modal-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 4px;
}

.back-btn {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    border: 1px solid #e0e0e0;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #333;
    flex-shrink: 0;
    font-size: 20px;
    transition: background 0.15s;
}

.back-btn:hover {
    background: #f0f0f0;
}

.modal-title {
    font-family: var(--font-text, sans-serif);
    font-size: 28px;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0;
}

.modal-card {
    background: #fff;
    border-radius: 16px;
    padding: 8px 24px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.divider {
    height: 1px;
    background: #f0f0f0;
    margin: 0 -24px;
}

.detail-row {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 20px 0;
}

.detail-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
    font-size: 20px;
}

.detail-icon--flag {
    background: #e8f5ee;
    color: #2d9e5f;
}

.detail-icon--location {
    background: #e8f5ee;
    color: #2d9e5f;
}

.detail-icon--category {
    background: #e8f5ee;
    color: #2d9e5f;
}

.detail-icon--status-new {
    background: #ffd8b5;
    color: #d97706;
}

.detail-icon--status-processing {
    background: #fef3c7;
    color: #d97706;
}

.detail-icon--status-done {
    background: #e8f5ee;
    color: #2d9e5f;
}

.detail-icon--desc {
    background: #e8f5ee;
    color: #2d9e5f;
}

.detail-icon--author {
    background: #e8f5ee;
    color: #2d9e5f;
}

.detail-icon--date {
    background: #e8f5ee;
    color: #2d9e5f;
}

.detail-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.detail-label {
    font-size: 13px;
    color: #8a8a8a;
    font-family: var(--font-text, sans-serif);
}

.detail-value {
    font-size: 17px;
    font-weight: 600;
    color: #1a1a1a;
    font-family: var(--font-text, sans-serif);
    line-height: 1.3;
}

.detail-value--title {
    font-size: 17px;
    font-weight: 700;
}

.detail-value--body {
    font-size: 14px;
    font-weight: 400;
    color: #555;
    line-height: 1.55;
    margin-top: 2px;
}

.detail-value--sub {
    font-size: 14px;
    font-weight: 400;
    color: #777;
}

.badge-modal {
    font-size: 14px;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: 600;
    display: inline-block;
    margin-top: 2px;
}

.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.22s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
</style>
