<script setup>
const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/heic",
        "application/pdf",
    ];
    const maxSize = 10 * 1024 * 1024; // 10 MB

    if (!allowedTypes.includes(file.type)) {
        alert("Недопустимый тип файла. Разрешены: JPEG, HEIC, PNG, PDF.");
        event.target.value = "";
        return;
    }

    if (file.size > maxSize) {
        alert("Файл слишком большой. Максимальный размер: 10 Мб.");
        event.target.value = "";
        return;
    }

    console.log("Selected file:", file.name);
};
</script>

<template>
    <label class="file-upload">
        <input
            type="file"
            accept="image/jpeg,image/png,image/heic,application/pdf"
            @change="handleFileChange"
        />
        <span>Прикрепить файл</span>
    </label>
</template>

<style scoped>
.file-upload {
    background: var(--color-bg-option-hover);
    border: 1px solid var(--color-border);
    border-radius: 16px;
    padding: 15px;
    padding-bottom: 12px;
    margin-bottom: 10px;
    font-family: var(--font-text);
    font-weight: 500;
    font-size: 16px;
    color: #2f2f2f;
    cursor: pointer;
    display: inline-block;
    min-width: 170px;
    transition: background 0.2s ease;
}

.file-upload:hover {
    background: var(--color-bg-option-selected);
}

input[type="file"] {
    display: none;
}

@media (min-width: 768px) {
    .file-upload {
        font-size: 20px;
    }
}
</style>
