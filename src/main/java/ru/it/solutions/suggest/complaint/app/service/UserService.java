package ru.it.solutions.suggest.complaint.app.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserResponseDto;
import ru.it.solutions.suggest.complaint.app.model.mappers.UserMapper;
import ru.it.solutions.suggest.complaint.app.repository.UserRepository;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

@Service
@Slf4j
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final UserMapper userMapper;

    @Value("${app.registration-url:http://localhost:8080/register}")
    private String registrationUrl;

    public UserResponseDto existsByVkUserId(String vkUserId) {
        return userMapper.toResponseDto(userRepository.findByVkUserId(vkUserId).orElseThrow(() ->
                new UsernameNotFoundException("user not found")));
    }

    public UserResponseDto existsByTelegramUserId(String telegramUserId) {
        return userMapper.toResponseDto(userRepository.findByTelegramUserId(telegramUserId).orElseThrow(() ->
                new UsernameNotFoundException("user not found")));
    }

    public String buildRegistrationLink(String vkUserId, String tgUserId) {
        StringBuilder url = new StringBuilder(registrationUrl);
        String separator = registrationUrl.contains("?") ? "&" : "?";

        if (vkUserId != null) {
            url.append(separator).append("vkUserId=").append(URLEncoder.encode(vkUserId.toString(), StandardCharsets.UTF_8));
            separator = "&";
        }
        if (tgUserId != null) {
            url.append(separator).append("tgUserId=").append(URLEncoder.encode(tgUserId.toString(), StandardCharsets.UTF_8));
        }

        return url.toString();
    }
}
