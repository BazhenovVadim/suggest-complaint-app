package ru.it.solutions.suggest.complaint.app.model.enums;

public enum Timeframe {
    ONE_DAY("1 день"),
    TWO_DAYS("2 дня"),
    THREE_DAYS("3 дня"),
    FIVE_DAYS("5 дней"),
    ONE_WEEK("1 неделя"),
    TWO_WEEKS("2 недели"),
    ONE_MONTH("1 месяц");

    private final String description;

    Timeframe(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}
