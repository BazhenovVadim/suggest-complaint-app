package ru.it.solutions.suggest.complaint.app.service.auth;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.RegisterRequest;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;
import ru.it.solutions.suggest.complaint.app.model.enums.UserRole;
import ru.it.solutions.suggest.complaint.app.model.mappers.UserMapper;
import ru.it.solutions.suggest.complaint.app.repository.UserRepository;

import java.time.Instant;
import java.util.Locale;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {
    private final UserRepository userRepository;
    private final UserMapper userMapper;
    private final BCryptPasswordEncoder passwordEncoder;
    private final JWTService jwtService;
    private final EmailService emailService;

    @Value("${app.admin.emails:}")
    private String adminEmails;

    @Value("${app.jwt.refresh-token-ttl-seconds:2592000}")
    private long refreshTokenTtlSeconds;

    @Transactional
    public UUID register(RegisterRequest request, String vkUserId, String tgUserId) {
        String email = request.email();
        String password = request.password();

        if (!PasswordPolicy.validate(password)) {
            throw new IllegalArgumentException("Пароль не соответствует правилам");
        }
        userRepository.findByEmail(email.toLowerCase()).ifPresent(u -> {
            throw new IllegalArgumentException("Данная почта уже используется");
        });
        if (vkUserId != null) {
            userRepository.findByVkUserId(vkUserId).ifPresent(u -> {
                throw new IllegalArgumentException("Пользователь ВКОНТАКТЕ уже привязан");
            });
        }
        if (tgUserId != null) {
            userRepository.findByTelegramUserId(tgUserId).ifPresent(u -> {
                throw new IllegalArgumentException("Пользователь Telegram уже привязан");
            });
        }
        String hashed = passwordEncoder.encode(password);
        UserEntity user = UserEntity.register(email, hashed);
        applyConfiguredAdminRole(user);
        userMapper.updateEntity(user, request);
        user.setVkUserId(vkUserId);
        user.setTelegramUserId(tgUserId);
        user.confirm();
        userRepository.save(user);
        return user.getId();
    }

    @Transactional
    public AuthResult authenticate(String email, String password) {
        Optional<UserEntity> ou = userRepository.findByEmail(email.toLowerCase());
        if (ou.isEmpty()) throw new IllegalArgumentException("Неверные данные для входа");
        UserEntity user = ou.get();
        if (!passwordEncoder.matches(password, user.getPasswordHash())) {
            throw new IllegalArgumentException("Неверные данные для входа");
        }
        applyConfiguredAdminRole(user);
        return issueTokens(user, Instant.now());
    }

    @Transactional
    public void requestPasswordReset(String email) {
        Optional<UserEntity> ou = userRepository.findByEmail(email.toLowerCase());
        if (ou.isEmpty()) {
            return;
        }
        UserEntity user = ou.get();
        Instant now = Instant.now();
        // rate limit: 5 minutes between reset requests
        if (user.getLastResetRequestedAt() != null && now.isBefore(user.getLastResetRequestedAt().plusSeconds(60 * 5))) {
            throw new IllegalStateException("Слишком много запросов на сброс. Попробуйте позже");
        }
        String token = UUID.randomUUID().toString();
        String tokenHash = passwordEncoder.encode(token);
        user.setResetToken(tokenHash, now.plusSeconds(60 * 60), now); // 1 hour expiry
        userRepository.save(user);
        // send email with token (in plain token form)
        emailService.sendPasswordReset(email, token);
    }

    @Transactional
    public AuthResult resetPassword(String email, String token, String newPassword) {
        Optional<UserEntity> ou = userRepository.findByEmail(email.toLowerCase());
        if (ou.isEmpty()) throw new IllegalArgumentException("Недействительный токен или адрес электронной почты");
        UserEntity user = ou.get();
        Instant now = Instant.now();
        String tokenHash = user.getResetTokenHash();
        if (tokenHash == null || !passwordEncoder.matches(token, tokenHash)) {
            throw new IllegalArgumentException("Недействительный токен");
        }
        // verify not expired handled in domain verifyResetToken
        boolean ok = user.verifyResetToken(tokenHash, now);
        if (!ok) throw new IllegalArgumentException("Недействительный или просроченный токен");
        if (!PasswordPolicy.validate(newPassword)) throw new IllegalArgumentException("Политика использования паролей");
        String newHash = passwordEncoder.encode(newPassword);
        user.setPassword(newHash);
        userRepository.save(user);
        // auto-login after reset
        return issueTokens(user, now);
    }

    @Transactional
    public AuthResult refreshTokens(UUID userId, String refreshToken) {
        if (userId == null || refreshToken == null || refreshToken.isBlank()) {
            throw new IllegalArgumentException("Refresh-токен не передан");
        }

        UserEntity user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("Недействительный refresh-токен"));
        Instant now = Instant.now();
        if (!isRefreshTokenValid(user, refreshToken, now)) {
            user.clearRefreshToken();
            userRepository.save(user);
            throw new IllegalArgumentException("Недействительный или просроченный refresh-токен");
        }

        applyConfiguredAdminRole(user);
        return issueTokens(user, now);
    }

    @Transactional
    public void logout(UUID userId, String refreshToken) {
        if (userId == null) {
            return;
        }

        userRepository.findById(userId).ifPresent(user -> {
            if (refreshToken == null
                    || refreshToken.isBlank()
                    || isRefreshTokenValid(user, refreshToken, Instant.now())) {
                user.clearRefreshToken();
                userRepository.save(user);
            }
        });
    }

    private AuthResult issueTokens(UserEntity user, Instant now) {
        String access = jwtService.generateAccessToken(user.getId(), user.getEmail());
        String refresh = jwtService.generateRefreshToken();
        user.setRefreshToken(passwordEncoder.encode(refresh), now.plusSeconds(refreshTokenTtlSeconds));
        userRepository.save(user);
        return new AuthResult(access, refresh, user.getId(), jwtService.getAccessTokenTtlSeconds());
    }

    private boolean isRefreshTokenValid(UserEntity user, String refreshToken, Instant now) {
        return user.getRefreshTokenHash() != null
                && user.getRefreshTokenExpiry() != null
                && !now.isAfter(user.getRefreshTokenExpiry())
                && passwordEncoder.matches(refreshToken, user.getRefreshTokenHash());
    }

    private void applyConfiguredAdminRole(UserEntity user) {
        if (isConfiguredAdmin(user.getEmail())) {
            user.setRole(UserRole.ADMIN);
        }
    }

    private boolean isConfiguredAdmin(String email) {
        if (adminEmails == null || adminEmails.isBlank() || email == null) {
            return false;
        }

        String normalizedEmail = email.toLowerCase(Locale.ROOT);
        for (String adminEmail : adminEmails.split(",")) {
            if (normalizedEmail.equals(adminEmail.toLowerCase(Locale.ROOT).trim())) {
                return true;
            }
        }
        return false;
    }

    private UserEntity findByEmail(String email) {
        return userRepository.findByEmail(email.toLowerCase()).orElseThrow(
                () -> new IllegalArgumentException("Пользователь не найден")
        );
    }

    public static class AuthResult {
        public final String accessToken;
        public final String refreshToken;
        public final UUID userId;
        public final long accessTokenExpiresInSeconds;

        public AuthResult(String access, String refresh, UUID userId, long accessTokenExpiresInSeconds) {
            this.accessToken = access;
            this.refreshToken = refresh;
            this.userId = userId;
            this.accessTokenExpiresInSeconds = accessTokenExpiresInSeconds;
        }
    }
}
