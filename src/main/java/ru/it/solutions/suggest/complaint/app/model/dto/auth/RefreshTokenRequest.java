package ru.it.solutions.suggest.complaint.app.model.dto.auth;

import java.util.UUID;

public record RefreshTokenRequest(UUID userId, String refreshToken) {
}
