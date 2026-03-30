package ru.it.solutions.suggest.complaint.app.controller;

import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import ru.it.solutions.suggest.complaint.app.service.AppealService;
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
    public ResponseEntity<Appeal> create(@RequestBody Appeal appeal) {
        return new ResponseEntity<>(appealService.createAppeal(appeal), HttpStatus.CREATED);
    }

    @GetMapping
    public ResponseEntity<List<Appeal>> getAll() {
        return ResponseEntity.ok(appealService.getAllAppeals());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Appeal> getById(@PathVariable UUID id) {
        return ResponseEntity.ok(appealService.getAppealById(id));
    }

    @PatchMapping("/{id}")
    public ResponseEntity<Appeal> patch(@PathVariable UUID id, @RequestBody Appeal appeal) {
        return ResponseEntity.ok(appealService.patchAppeal(id, appeal));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        appealService.deleteAppeal(id);
        return ResponseEntity.noContent().build();
    }
}