package ru.it.solutions.suggest.complaint.app.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserResponseDto;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;
import ru.it.solutions.suggest.complaint.app.model.enums.UserRole;
import ru.it.solutions.suggest.complaint.app.model.mappers.UserMapper;
import ru.it.solutions.suggest.complaint.app.repository.UserRepository;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.UUID;

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
                new UsernameNotFoundException("Пользователь не найден")));
    }

    public Optional<UserResponseDto> findByVkUserId(String vkUserId) {
        return userRepository.findByVkUserId(vkUserId).map(userMapper::toResponseDto);
    }

    public UserResponseDto findUserId(UUID Id){
        return userMapper.toResponseDto(userRepository.findById(Id).orElseThrow(() ->
                new UsernameNotFoundException("Пользователь не найден")));
    }

    public UserEntity getUserById(UUID Id){
        return userRepository.findById(Id).orElseThrow(() ->
                new UsernameNotFoundException("Пользователь не найден"));
    }

    public UserResponseDto existsByTelegramUserId(String telegramUserId) {
        return userMapper.toResponseDto(userRepository.findByTelegramUserId(telegramUserId).orElseThrow(() ->
                new UsernameNotFoundException("Пользователь не найден")));
    }

    public Optional<UserResponseDto> findByTelegramUserId(String telegramUserId) {
        return userRepository.findByTelegramUserId(telegramUserId).map(userMapper::toResponseDto);
    }

    @Transactional
    public UserResponseDto linkVkUser(UUID userId, String vkUserId) {
        if (vkUserId == null || vkUserId.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Не передан VK ID");
        }

        UserEntity user = getUserById(userId);
        userRepository.findByVkUserId(vkUserId).ifPresent(existingUser -> {
            if (!existingUser.getId().equals(user.getId())) {
                throw new ResponseStatusException(HttpStatus.CONFLICT, "Пользователь ВКОНТАКТЕ уже привязан");
            }
        });
        user.setVkUserId(vkUserId);
        return userMapper.toResponseDto(userRepository.save(user));
    }

    @Transactional
    public UserResponseDto linkTgUser(UUID userId, String tgUserId) {
        if (tgUserId == null || tgUserId.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Не передан TG ID");
        }

        UserEntity user = getUserById(userId);
        userRepository.findByTelegramUserId(tgUserId).ifPresent(existingUser -> {
            if (!existingUser.getId().equals(user.getId())) {
                throw new ResponseStatusException(HttpStatus.CONFLICT, "Пользователь телеграм уже привязан");
            }
        });
        user.setTelegramUserId(tgUserId);
        return userMapper.toResponseDto(userRepository.save(user));
    }

    @Transactional
    public UserResponseDto updateRole(UUID userId, UserRole role, UserEntity currentUser) {
        if (currentUser.getRole() != UserRole.ADMIN) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Менять роли пользователей может только администратор");
        }

        UserEntity user = getUserById(userId);
        user.setRole(role);
        return userMapper.toResponseDto(userRepository.save(user));
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
