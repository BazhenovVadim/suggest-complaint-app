<script setup>
import MdiPaperclip from "~icons/mdi/paperclip";
import MdiCloseCircle from "~icons/mdi/close-circle";
import MdiFilePdfBox from "~icons/mdi/file-pdf-box";
import MdiFileImageOutline from "~icons/mdi/file-image-outline";

const props = defineProps({
    files: {
        type: Array,
        default: () => [],
    },
    maxFiles: {
        type: Number,
        default: 3,
    },
    maxSize: {
        type: Number,
        default: 10 * 1024 * 1024,
    },
});

const emit = defineEmits(["update:files"]);

const allowedTypes = [
    "image/jpeg",
    "image/png",
    "image/heic",
    "application/pdf",
];

const formatSize = (size) => {
    if (size >= 1024 * 1024) {
        return `${(size / (1024 * 1024)).toFixed(1)} МБ`;
    }
    if (size >= 1024) {
        return `${Math.round(size / 1024)} КБ`;
    }
    return `${size} Б`;
};

const fileIcon = (file) => {
    if (file.type === "application/pdf") {
        return MdiFilePdfBox;
    }
    return MdiFileImageOutline;
};

const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files || []);
    if (!selectedFiles.length) return;

    const currentFiles = [...props.files];
    const validFiles = [];

    for (const file of selectedFiles) {
        if (!allowedTypes.includes(file.type)) {
            alert("Недопустимый тип файла. Разрешены: JPEG, HEIC, PNG, PDF.");
            continue;
        }

        if (file.size > props.maxSize) {
            alert("Файл слишком большой. Максимальный размер: 10 Мб.");
            continue;
        }

        const duplicate = currentFiles.some(
            (existing) =>
                existing.name === file.name && existing.size === file.size,
        );
        if (duplicate) {
            continue;
        }

        validFiles.push(file);
    }

    if (!validFiles.length) {
        event.target.value = "";
        return;
    }

    if (currentFiles.length + validFiles.length > props.maxFiles) {
        alert(`Максимум можно загрузить ${props.maxFiles} вложения.`);
        event.target.value = "";
        return;
    }

    emit("update:files", [...currentFiles, ...validFiles]);
    event.target.value = "";
};

const removeFile = (index) => {
    emit(
        "update:files",
        props.files.filter((_, idx) => idx !== index),
    );
};
</script>

<template>
    <div class="file-upload-wrapper">
        <label class="file-upload">
            <input
                type="file"
                accept="image/jpeg,image/png,image/heic,application/pdf"
                multiple
                @change="handleFileChange"
            />
            <span class="upload-button">
                <MdiPaperclip class="clip" />
                <span>Прикрепить файл</span>
            </span>
        </label>

        <aside v-if="props.files.length" class="attachments-list">
            <div class="attachments-header">
                <span>Вложения</span>
                <span>{{ props.files.length }} из {{ props.maxFiles }}</span>
            </div>
            <ul>
                <li
                    v-for="(file, index) in props.files"
                    :key="file.name + file.size"
                >
                    <component :is="fileIcon(file)" class="attachment-icon" />
                    <div class="attachment-meta">
                        <span class="attachment-name">{{ file.name }}</span>
                        <span class="attachment-size">{{
                            formatSize(file.size)
                        }}</span>
                    </div>
                    <button
                        type="button"
                        class="remove-btn"
                        @click="removeFile(index)"
                    >
                        <MdiCloseCircle />
                    </button>
                </li>
            </ul>
        </aside>
    </div>
</template>

<style scoped>
.file-upload-wrapper {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.file-upload {
    background: var(--color-bg-option-hover);
    border: 1px solid var(--color-border);
    border-radius: 18px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    cursor: pointer;
    transition:
        background 0.2s ease,
        border-color 0.2s ease;
    max-width: 220px;
}

.file-upload:hover {
    background: var(--color-bg-option-selected);
    border-color: rgba(0, 0, 0, 0.12);
}

input[type="file"] {
    display: none;
}

.upload-button {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: var(--color-main-inverted);
    font-weight: 500;
}

.clip {
    width: 20px;
    height: 20px;
    transform: rotate(45deg);
}

.upload-subtitle {
    color: #6e6e6e;
    font-size: 14px;
}

.attachments-list {
    background: rgba(239, 239, 239, 0.7);
    border: 1px solid rgba(56, 56, 56, 0.08);
    border-radius: 18px;
    padding: 12px;
}

.attachments-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #4f4f4f;
    margin-bottom: 10px;
}

.attachments-list ul {
    display: grid;
    gap: 8px;
    padding: 0;
    margin: 0;
    list-style: none;
}

.attachments-list li {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 12px;
    background: white;
    border-radius: 14px;
    padding: 10px 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.attachment-icon {
    width: 32px;
    height: 32px;
    color: var(--color-main-inverted);
}

.attachment-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
    overflow: hidden;
}

.attachment-name {
    font-weight: 600;
    color: #252525;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.attachment-size {
    font-size: 13px;
    color: #7a7a7a;
}

.remove-btn {
    border: none;
    background: transparent;
    color: #8f8f8f;
    cursor: pointer;
    padding: 0;
    display: grid;
    place-items: center;
}

.remove-btn:hover {
    color: #ff4d4d;
}

@media (min-width: 768px) {
    .file-upload {
        max-width: 290px;
    }
}
</style>
