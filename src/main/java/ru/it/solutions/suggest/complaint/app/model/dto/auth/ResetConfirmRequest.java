package ru.it.solutions.suggest.complaint.app.model.dto.auth;

public record ResetConfirmRequest(String email, String token, String newPassword) {
}
