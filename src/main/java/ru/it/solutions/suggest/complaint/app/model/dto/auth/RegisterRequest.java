package ru.it.solutions.suggest.complaint.app.model.dto.auth;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;

public record RegisterRequest(
        String email,
        String password,
        @JsonProperty("vk_user_id")
        @JsonAlias("vkUserId")
        String vkUserId,
        @JsonProperty("telegram_user_id")
        @JsonAlias("telegramUserId")
        String telegramUserId,
        String firstName,
        String middleName,
        String lastName,
        String phoneNumber
) {
}
