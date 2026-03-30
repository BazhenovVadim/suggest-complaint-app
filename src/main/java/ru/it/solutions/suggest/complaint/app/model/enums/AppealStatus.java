package ru.it.solutions.suggest.complaint.app.model.enums;

public enum AppealStatus {
    NEW("Новое"),
    IN_PROGRESS("В обработке"),
    RESOLVED("Решено"),
    REJECTED("Отклонено");

    private final String description;

    AppealStatus(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }

}
