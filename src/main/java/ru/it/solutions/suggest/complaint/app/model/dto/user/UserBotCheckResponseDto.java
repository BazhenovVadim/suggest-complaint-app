package ru.it.solutions.suggest.complaint.app.model.dto.user;

public record UserBotCheckResponseDto(
        boolean exists,
        String registrationUrl,
        UserResponseDto userResponseDto,
        String accessToken) {
}
