package ru.it.solutions.suggest.complaint.app.model.enums;

public enum Timeframe {
    ONE_DAY("1 день"),
    TWO_DAYS("2 дня");

    private final String description;

    Timeframe(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}
