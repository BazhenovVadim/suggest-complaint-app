package ru.it.solutions.suggest.complaint.app.model.dto.user;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;

public record UserSocialLinkRequestDto(
        @JsonProperty("vk_user_id")
        @JsonAlias("vkUserId")
        String vkUserId,
        @JsonProperty("telegram_user_id")
        @JsonAlias("telegramUserId")
        String telegramUserId
) {
}
