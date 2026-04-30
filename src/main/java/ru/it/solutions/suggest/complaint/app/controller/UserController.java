package ru.it.solutions.suggest.complaint.app.controller;

import io.jsonwebtoken.Jwt;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserBotCheckResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserResponseDto;
import ru.it.solutions.suggest.complaint.app.service.UserService;
import ru.it.solutions.suggest.complaint.app.service.auth.JWTService;

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
}
