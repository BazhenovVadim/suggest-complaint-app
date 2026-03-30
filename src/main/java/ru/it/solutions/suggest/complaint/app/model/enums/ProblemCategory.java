package ru.it.solutions.suggest.complaint.app.model.enums;

public enum ProblemCategory {
    ACCOMMODATION("Расселение"),
    BATHROOM("Санузел"),
    ELECTRICITY("Электричество"),
    HEATING("Отопление"),
    CLEANLINESS("Чистота"),
    NOISE("Шум"),
    PLUMBING("Сантехника"),
    FURNITURE("Мебель"),
    INTERNET("Интернет"),
    OTHER("Другое");

    private final String description;

    ProblemCategory(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}
