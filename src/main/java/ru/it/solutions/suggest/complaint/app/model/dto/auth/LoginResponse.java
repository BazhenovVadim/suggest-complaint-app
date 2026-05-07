package ru.it.solutions.suggest.complaint.app.model.dto.auth;

import ru.it.solutions.suggest.complaint.app.model.dto.user.UserResponseDto;

import java.util.UUID;

public record LoginResponse(
        String accessToken,
        String refreshToken,
        UserResponseDto user,
        long accessTokenExpiresInSeconds) {
}
