package ru.it.solutions.suggest.complaint.app.model.dto.auth;

import java.util.UUID;

public record LoginResponse(
        String accessToken,
        String refreshToken,
        UUID userId,
        long accessTokenExpiresInSeconds) {
}
