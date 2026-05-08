package ru.it.solutions.suggest.complaint.app.model.dto.auth;

import java.util.UUID;

public record LogoutRequest(UUID userId, String refreshToken) {
}
