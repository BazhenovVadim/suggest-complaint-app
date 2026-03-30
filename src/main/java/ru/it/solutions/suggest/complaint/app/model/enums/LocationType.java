package ru.it.solutions.suggest.complaint.app.model.enums;

public enum LocationType {
    STUDENT_CAMPUS("Студгородок"),
    DORMITORY("Общежитие"),
    ACADEMIC_BUILDING("Учебный корпус"),
    LIBRARY("Библиотека"),
    CANTEEN("Столовая"),
    SPORTS_COMPLEX("Спорткомплекс"),
    MEDICAL_CENTER("Медпункт");

    private final String description;

    LocationType(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}
