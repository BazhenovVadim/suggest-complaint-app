package ru.it.solutions.suggest.complaint.app.service.auth;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;
import ru.it.solutions.suggest.complaint.app.repository.UserRepository;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {
    private final UserRepository userRepository;
    private final BCryptPasswordEncoder passwordEncoder;
    private final JWTService jwtService;
    private final EmailService emailService;


    @Transactional
    public UUID register(String email, String password, String vkUserId, String tgUserId) {
        if (!PasswordPolicy.validate(password)) {
            throw new IllegalArgumentException("Password does not meet policy");
        }
        userRepository.findByEmail(email.toLowerCase()).ifPresent(u -> {
            throw new IllegalArgumentException("Email already in use");
        });
        if (vkUserId != null) {
            userRepository.findByVkUserId(vkUserId).ifPresent(u -> {
                throw new IllegalArgumentException("VK user is already linked");
            });
        }
        if (tgUserId != null) {
            userRepository.findByTelegramUserId(tgUserId).ifPresent(u -> {
                throw new IllegalArgumentException("Telegram user is already linked");
            });
        }
        String hashed = passwordEncoder.encode(password);
        UserEntity user = UserEntity.register(email, hashed);
        user.setVkUserId(vkUserId);
        user.setTelegramUserId(tgUserId);
        user.confirm();
        userRepository.save(user);
        return user.getId();
    }

    @Transactional(readOnly = true)
    public AuthResult authenticate(String email, String password) {
        Optional<UserEntity> ou = userRepository.findByEmail(email.toLowerCase());
        if (ou.isEmpty()) throw new IllegalArgumentException("Invalid credentials");
        UserEntity user = ou.get();
        if (!passwordEncoder.matches(password, user.getPasswordHash())) {
            throw new IllegalArgumentException("Invalid credentials");
        }
        String access = jwtService.generateAccessToken(user.getId(), user.getEmail());
        String refresh = jwtService.generateRefreshToken();
        // store hashed refresh token
        String refreshHash = passwordEncoder.encode(refresh);
        user.setRefreshToken(refreshHash, Instant.now().plusSeconds(60 * 60 * 24 * 30)); // 30 days
        userRepository.save(user);
        return new AuthResult(access, refresh, user.getId());
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
            throw new IllegalStateException("Too many reset requests. Try later.");
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
        if (ou.isEmpty()) throw new IllegalArgumentException("Invalid token or email");
        UserEntity user = ou.get();
        Instant now = Instant.now();
        String tokenHash = user.getResetTokenHash();
        if (tokenHash == null || !passwordEncoder.matches(token, tokenHash)) {
            throw new IllegalArgumentException("Invalid token");
        }
        // verify not expired handled in domain verifyResetToken
        boolean ok = user.verifyResetToken(tokenHash, now);
        if (!ok) throw new IllegalArgumentException("Invalid or expired token");
        if (!PasswordPolicy.validate(newPassword)) throw new IllegalArgumentException("Password policy");
        String newHash = passwordEncoder.encode(newPassword);
        user.setPassword(newHash);
        userRepository.save(user);
        // auto-login after reset
        String access = jwtService.generateAccessToken(user.getId(), user.getEmail());
        String refresh = jwtService.generateRefreshToken();
        user.setRefreshToken(passwordEncoder.encode(refresh), now.plusSeconds(60 * 60 * 24 * 30));
        userRepository.save(user);
        return new AuthResult(access, refresh, user.getId());
    }

    private UserEntity findByEmail(String email) {
        return userRepository.findByEmail(email.toLowerCase()).orElseThrow(
                () -> new IllegalArgumentException("User not found")
        );
    }

    public static class AuthResult {
        public final String accessToken;
        public final String refreshToken;
        public final UUID userId;

        public AuthResult(String access, String refresh, UUID userId) {
            this.accessToken = access;
            this.refreshToken = refresh;
            this.userId = userId;
        }
    }
}
