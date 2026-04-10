package ru.it.solutions.suggest.complaint.app.service;

import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealCreateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealUpdateDto;
import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import ru.it.solutions.suggest.complaint.app.model.enums.AppealStatus;
import ru.it.solutions.suggest.complaint.app.repository.AppealRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class AppealService {

    private final AppealRepository appealRepository;

    // CREATE
    @Transactional
    public AppealResponseDto createAppeal(AppealCreateDto createDto) {
        log.info("Создание нового обращения");

        if (createDto.getPersonalDataConsent() == null || !createDto.getPersonalDataConsent()) {
            throw new IllegalArgumentException("Необходимо согласие на обработку персональных данных");
        }

        Appeal appeal = Appeal.builder()
                .type(createDto.getType())
                .campusLocation(createDto.getCampusLocation())
                .problemCategory(createDto.getProblemCategory())
                .timeframe(createDto.getTimeframe())
                .description(createDto.getDescription())
                .filePath(createDto.getFilePath())
                .fileName(createDto.getFileName())
                .contactName(createDto.getContactName())
                .contactPhone(createDto.getContactPhone())
                .contactEmail(createDto.getContactEmail())
                .personalDataConsent(createDto.getPersonalDataConsent())
                .status(AppealStatus.NEW)
                .build();

        Appeal savedAppeal = appealRepository.save(appeal);
        log.info("Обращение создано с id: {}", savedAppeal.getId());

        return mapToResponse(savedAppeal);
    }

    // READ all
    public List<AppealResponseDto> getAllAppeals() {
        return appealRepository.findAll().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    // READ by id
    public AppealResponseDto getAppealById(UUID id) {
        Appeal appeal = appealRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Обращение не найдено с id: " + id));
        return mapToResponse(appeal);
    }

    // UPDATE (PATCH)
    @Transactional
    public AppealResponseDto patchAppeal(UUID id, AppealUpdateDto updateDto) {
        log.info("Обновление обращения с id: {}", id);

        Appeal appeal = appealRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Обращение не найдено с id: " + id));

        if (updateDto.getType() != null) appeal.setType(updateDto.getType());
        if (updateDto.getCampusLocation() != null) appeal.setCampusLocation(updateDto.getCampusLocation());
        if (updateDto.getProblemCategory() != null) appeal.setProblemCategory(updateDto.getProblemCategory());
        if (updateDto.getTimeframe() != null) appeal.setTimeframe(updateDto.getTimeframe());
        if (updateDto.getDescription() != null) appeal.setDescription(updateDto.getDescription());
        if (updateDto.getFilePath() != null) appeal.setFilePath(updateDto.getFilePath());
        if (updateDto.getFileName() != null) appeal.setFileName(updateDto.getFileName());
        if (updateDto.getContactName() != null) appeal.setContactName(updateDto.getContactName());
        if (updateDto.getContactPhone() != null) appeal.setContactPhone(updateDto.getContactPhone());
        if (updateDto.getContactEmail() != null) appeal.setContactEmail(updateDto.getContactEmail());
        if (updateDto.getPersonalDataConsent() != null) appeal.setPersonalDataConsent(updateDto.getPersonalDataConsent());
        if (updateDto.getStatus() != null) appeal.setStatus(updateDto.getStatus());

        Appeal updatedAppeal = appealRepository.save(appeal);
        return mapToResponse(updatedAppeal);
    }

    // DELETE
    @Transactional
    public void deleteAppeal(UUID id) {
        log.info("Удаление обращения с id: {}", id);

        if (!appealRepository.existsById(id)) {
            throw new RuntimeException("Обращение не найдено с id: " + id);
        }
        appealRepository.deleteById(id);
    }

    // Маппер: Entity -> ResponseDto
    private AppealResponseDto mapToResponse(Appeal appeal) {
        return AppealResponseDto.builder()
                .id(appeal.getId())
                .type(appeal.getType())
                .campusLocation(appeal.getCampusLocation())
                .problemCategory(appeal.getProblemCategory())
                .timeframe(appeal.getTimeframe())
                .description(appeal.getDescription())
                .filePath(appeal.getFilePath())
                .fileName(appeal.getFileName())
                .contactName(appeal.getContactName())
                .contactPhone(appeal.getContactPhone())
                .contactEmail(appeal.getContactEmail())
                .personalDataConsent(appeal.getPersonalDataConsent())
                .createdAt(appeal.getCreatedAt())
                .status(appeal.getStatus())
                .build();
    }
}