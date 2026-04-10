package ru.it.solutions.suggest.complaint.app.controller;


import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealCreateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealUpdateDto;
import ru.it.solutions.suggest.complaint.app.service.AppealService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/appeals")
@RequiredArgsConstructor
public class AppealController {

    private final AppealService appealService;

    @PostMapping
    public ResponseEntity<AppealResponseDto> create(@Valid @RequestBody AppealCreateDto createDto) {
        return new ResponseEntity<>(appealService.createAppeal(createDto), HttpStatus.CREATED);
    }

    @GetMapping
    public ResponseEntity<List<AppealResponseDto>> getAll() {
        return ResponseEntity.ok(appealService.getAllAppeals());
    }

    @GetMapping("/{id}")
    public ResponseEntity<AppealResponseDto> getById(@PathVariable UUID id) {
        return ResponseEntity.ok(appealService.getAppealById(id));
    }

    @PatchMapping("/{id}")
    public ResponseEntity<AppealResponseDto> patch(@PathVariable UUID id, @Valid @RequestBody AppealUpdateDto updateDto) {
        return ResponseEntity.ok(appealService.patchAppeal(id, updateDto));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        appealService.deleteAppeal(id);
        return ResponseEntity.noContent().build();
    }
}