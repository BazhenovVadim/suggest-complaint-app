<script setup>
import { computed } from "vue";
import {
    translate,
    STATUS_TRANSLATIONS,
    TYPE_TRANSLATIONS,
    LOCATION_TRANSLATIONS,
    CATEGORY_TRANSLATIONS,
    TIMEFRAME_TRANSLATIONS,
} from "@/utils/translations";

const props = defineProps({
    appeal: {
        type: Object,
        required: true,
    },
});

const emit = defineEmits(["view"]);

const displayNumber = computed(
    () => props.appeal?.appealNumber ?? "",
);

const rawType = computed(() => props.appeal?.type ?? "");
const displayType = computed(() =>
    translate(rawType.value, TYPE_TRANSLATIONS, rawType.value),
);

const rawCampusLocation = computed(
    () => props.appeal?.campusLocation ?? props.appeal?.location ?? "",
);
const displayCampusLocation = computed(() =>
    translate(rawCampusLocation.value, LOCATION_TRANSLATIONS, rawCampusLocation.value),
);

const rawProblemCategory = computed(
    () => props.appeal?.problemCategory ?? props.appeal?.category ?? "",
);
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

const isStatusNew = computed(() =>
    String(rawStatus.value).toUpperCase() === "NEW",
);

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
</script>

<template>
    <div class="appeal-row" role="article" tabindex="0">
        <div class="col id">#{{ displayNumber }}</div>

        <div class="col type">
            <div class="type-row">
                <span class="flag" aria-hidden>⚑</span>
                <span class="type-label">{{ displayType }}</span>
            </div>
            <div class="location" v-if="rawType === 'COMPLAINT'">{{ displayCampusLocation }}</div>
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
            <button class="btn-outline" @click="$emit('view', appeal)">Просмотр заявки</button>
        </div>
    </div>
</template>

<style scoped>
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
    font-weight: 600;
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
</style>
