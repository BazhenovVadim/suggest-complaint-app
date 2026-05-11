<script setup>
</script>

<template>
    <main class="main">
        <div class="content">
            <button @click="$router.back()" class="back-btn">← Назад</button>
            <h1>Согласие на обработку персональных данных</h1>
            
            <div class="privacy-text">
                <p>Здесь будет располагаться официальный текст согласия на обработку персональных данных...</p>
                <p>1. Общие положения...</p>
                <p>2. Цели обработки...</p>
                <p>3. Права пользователя...</p>
                <p>4. Купил мужик шляпу, а она ему как раз...</p>
                <p>5. Идёт медведь по лесу, видит - машина горит. Сел в неё. И сгорел...</p>
                <p>6. Идёт Штирлиц по улице, тут ему на голову упал кирпич. "Вот те раз..." - подумал Штирлиц. "Вот те два!" - подумал Мюллер и скинул второй кирпич... </p>
                <p>7. Заходит улитка в бар... а нет нельзя, дальще маты...</p>
                </div>
        </div>
    </main>
</template>

<style scoped>
.main {
    display: flex;
    justify-content: center;
    padding: 15px;
}

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

.back-btn:hover {
    background: var(--color-bg-option-hover);
}

h1 {
    font-family: var(--font-header);
    font-size: 26px;
    color: var(--color-main-inverted);
    margin: 0;
}

.privacy-text {
    font-family: var(--font-text);
    color: var(--color-font);
    line-height: 1.6;
    width: 100%;
}

.privacy-text p {
    margin-bottom: 15px;
}

@media (min-width: 768px) {
    .main {
        padding: 30px;
    }
    .content {
        padding: 35px;
    }
    h1 {
        font-size: 36px;
    }
}
</style>