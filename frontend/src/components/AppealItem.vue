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
            <div class="desc-title">{{ shortDescription }}</div>
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

            <button class="btn-outline" @click="view">Просмотр заявки</button>
        </div>
    </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from "vue";

const props = defineProps({
    appeal: {
        type: Object,
        required: true,
    },
});

const emit = defineEmits(["view"]);

const displayNumber = computed(
    () => props.appeal?.appealNumber ?? props.appeal?.number ?? "",
);
const displayType = computed(() => {
    const t = props.appeal?.type ?? "";
    return t ? String(t) : "";
});
const displayCampusLocation = computed(
    () => props.appeal?.campusLocation ?? props.appeal?.location ?? "",
);
const displayProblemCategory = computed(
    () => props.appeal?.problemCategory ?? props.appeal?.category ?? "",
);
const displayTimeframe = computed(() => {
    const tf = props.appeal?.timeframe ?? "";
    return tf ? String(tf) : "";
});

const fullDescription = computed(
    () =>
        props.appeal?.description ??
        props.appeal?.excerpt ??
        props.appeal?.title ??
        "",
);
const shortDescription = computed(() => {
    const d = fullDescription.value ?? "";
    if (!d) return "";
    return d.length > 100 ? d.slice(0, 100).trim() + "…" : d;
});

const displayContactName = computed(
    () => props.appeal?.contactName ?? props.appeal?.author ?? "",
);
const displayContactEmail = computed(
    () => props.appeal?.contactEmail ?? props.appeal?.email ?? "",
);
const displayContactPhone = computed(
    () => props.appeal?.contactPhone ?? props.appeal?.phone ?? "",
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
        date: d.toLocaleDateString(),
        time: d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
});

const displayDate = computed(() => dateParts.value.date);
const displayTime = computed(() => dateParts.value.time);

const rawStatus = computed(() => props.appeal?.status ?? "");
const statusText = computed(() => {
    const s = rawStatus.value;
    if (s == null) return "";
    if (typeof s === "object" && s.name) return String(s.name);
    return String(s);
});

const badgeClass = computed(() => {
    const n = statusText.value.toLowerCase();
    if (n.includes("нов") || n.includes("new")) return "badge-new";
    if (
        n.includes("рассмотр") ||
        n.includes("review") ||
        n.includes("processing") ||
        n.includes("inprogress") ||
        n.includes("in_progress") ||
        n.includes("in progress")
    )
        return "badge-processing";
    if (n.includes("заверш") || n.includes("done") || n.includes("completed"))
        return "badge-done";
    return "badge-processing";
});

function view() {
    emit("view", props.appeal);
}
</script>

<style scoped>
.appeal-row {
    box-sizing: border-box;
    display: grid;
    grid-template-columns: 70px 120px 220px 1fr 140px 160px 220px;
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
    min-width: 0; /* allow children to shrink and ellipsis to work */
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

.desc-title {
    font-weight: 600;
    margin-bottom: 6px;
    font-size: 15px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
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
    justify-content: flex-end;
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
    background: #e6f4ea;
    color: #1f8d52;
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

/* Desktop-only adjustments — keep layout fixed for PC as requested */
@media (min-width: 1025px) {
    .appeal-row {
        font-size: 15px;
    }
}
</style>
