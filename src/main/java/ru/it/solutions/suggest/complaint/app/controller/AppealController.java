package ru.it.solutions.suggest.complaint.app.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealCreateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealStatusUpdateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealUpdateDto;
import ru.it.solutions.suggest.complaint.app.service.AppealService;
import ru.it.solutions.suggest.complaint.app.service.auth.CustomUserDetails;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/appeals")
@RequiredArgsConstructor
public class AppealController {

    private final AppealService appealService;

    @PostMapping
    public ResponseEntity<AppealResponseDto> create(
            @AuthenticationPrincipal CustomUserDetails currentUser,
            @Valid @RequestBody AppealCreateDto createDto) {
        return new ResponseEntity<>(appealService.createAppeal(createDto, currentUser.getUserEntity()), HttpStatus.CREATED);
    }

    @GetMapping
    public ResponseEntity<List<AppealResponseDto>> getAll(@AuthenticationPrincipal CustomUserDetails currentUser) {
        return ResponseEntity.ok(appealService.getAvailableAppeals(currentUser.getUserEntity()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<AppealResponseDto> getById(@AuthenticationPrincipal CustomUserDetails currentUser,
                                                     @PathVariable UUID id) {
        return ResponseEntity.ok(appealService.getAppealById(id, currentUser.getUserEntity()));
    }

    @PatchMapping("/{id}")
    public ResponseEntity<AppealResponseDto> patch(@AuthenticationPrincipal CustomUserDetails currentUser,
                                                   @PathVariable UUID id,
                                                   @Valid @RequestBody AppealUpdateDto updateDto) {
        return ResponseEntity.ok(appealService.patchAppeal(id, updateDto, currentUser.getUserEntity()));
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<AppealResponseDto> updateStatus(@AuthenticationPrincipal CustomUserDetails currentUser,
                                                          @PathVariable UUID id,
                                                          @Valid @RequestBody AppealStatusUpdateDto updateDto) {
        return ResponseEntity.ok(appealService.updateAppealStatus(id, updateDto.getStatus(), currentUser.getUserEntity()));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@AuthenticationPrincipal CustomUserDetails currentUser,
                                       @PathVariable UUID id) {
        appealService.deleteAppeal(id, currentUser.getUserEntity());
        return ResponseEntity.noContent().build();
    }
}
