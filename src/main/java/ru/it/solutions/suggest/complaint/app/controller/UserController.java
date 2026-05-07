package ru.it.solutions.suggest.complaint.app.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserBotCheckResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserRoleUpdateDto;
import ru.it.solutions.suggest.complaint.app.service.UserService;
import ru.it.solutions.suggest.complaint.app.service.auth.CustomUserDetails;
import ru.it.solutions.suggest.complaint.app.service.auth.JWTService;

import java.util.UUID;

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;
    private final JWTService jwtService;

    @GetMapping("/check")
    public ResponseEntity<UserBotCheckResponseDto> checkUser(@RequestParam(required = false) String vkUserId,
                                                             @RequestParam(required = false) String tgUserId) {
        if (vkUserId == null && tgUserId == null) {
            return ResponseEntity.badRequest().build();
        }
        UserResponseDto exists = vkUserId != null
                ? userService.existsByVkUserId(vkUserId)
                : userService.existsByTelegramUserId(tgUserId);

        String registrationUrl = exists == null ? null : userService.buildRegistrationLink(vkUserId, tgUserId);
        String accessToken = exists == null ? null : jwtService.generateAccessToken(exists.getId(), exists.getEmail());
        return ResponseEntity.ok(new UserBotCheckResponseDto(true, registrationUrl, exists, accessToken));
    }

    @PatchMapping("/{id}/role")
    public ResponseEntity<UserResponseDto> updateRole(@AuthenticationPrincipal CustomUserDetails currentUser,
                                                      @PathVariable UUID id,
                                                      @Valid @RequestBody UserRoleUpdateDto request) {
        return ResponseEntity.ok(userService.updateRole(id, request.getRole(), currentUser.getUserEntity()));
    }

    @GetMapping("/{id}")
    public UserResponseDto getUserInfo(@PathVariable("id") UUID userId) {
        return userService.findUserId(userId);
    }

    @GetMapping("/me")
    public ResponseEntity<UserResponseDto> getMe(@AuthenticationPrincipal CustomUserDetails currentUser) {
        if (currentUser == null) {
            return ResponseEntity.status(401).build();
        }
        return ResponseEntity.ok(userService.findUserId(currentUser.getId()));
    }
}
