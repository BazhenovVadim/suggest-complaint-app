package ru.it.solutions.suggest.complaint.app.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.ErrorResponse;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.LoginRequest;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.LoginResponse;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.LogoutRequest;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.RefreshTokenRequest;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.RegisterRequest;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.ResetConfirmRequest;
import ru.it.solutions.suggest.complaint.app.model.dto.auth.ResetRequest;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserResponseDto;
import ru.it.solutions.suggest.complaint.app.service.auth.AuthService;

@RestController
@RequestMapping("api/auth")
@RequiredArgsConstructor
public class AuthController {
    private final AuthService authService;

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody RegisterRequest request,
                                      @RequestParam(required = false) String vkUserId,
                                      @RequestParam(required = false, name = "tgUserId") String tgUserId) {
        try {
            String resolvedVkUserId = request.vkUserId() != null ? request.vkUserId() : vkUserId;
            String resolvedTelegramUserId = request.telegramUserId() != null ? request.telegramUserId() : tgUserId;
            UserResponseDto user = authService.register(request,
                    resolvedVkUserId,
                    resolvedTelegramUserId);
            return ResponseEntity.ok(user);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(new ErrorResponse(e.getMessage()));
        }
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        try {
            AuthService.AuthResult result = authService.authenticate(request.email(), request.password());
            return ResponseEntity.ok(toLoginResponse(result));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(401).body(new ErrorResponse(e.getMessage()));
        }
    }

    @PostMapping("/password-reset-request")
    public ResponseEntity<?> requestReset(@RequestBody ResetRequest request) {
        authService.requestPasswordReset(request.email());
        return ResponseEntity.ok().body("If email exists, reset link sent");
    }

    @PostMapping("/password-reset")
    public ResponseEntity<?> resetPassword(@RequestBody ResetConfirmRequest request) {
        try {
            AuthService.AuthResult result = authService.resetPassword(
                    request.email(),
                    request.token(),
                    request.newPassword()
            );
            return ResponseEntity.ok(toLoginResponse(result));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(new ErrorResponse(e.getMessage()));
        }
    }

    @PostMapping("/refresh")
    public ResponseEntity<?> refresh(@RequestBody RefreshTokenRequest request) {
        try {
            AuthService.AuthResult result = authService.refreshTokens(request.userId(), request.refreshToken());
            return ResponseEntity.ok(toLoginResponse(result));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(401).body(new ErrorResponse(e.getMessage()));
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(@RequestBody LogoutRequest request) {
        authService.logout(request.userId(), request.refreshToken());
        return ResponseEntity.noContent().build();
    }

    private LoginResponse toLoginResponse(AuthService.AuthResult result) {
        return new LoginResponse(
                result.accessToken,
                result.refreshToken,
                result.userId,
                result.accessTokenExpiresInSeconds
        );
    }

}
