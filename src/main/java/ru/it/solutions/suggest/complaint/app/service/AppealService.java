package ru.it.solutions.suggest.complaint.app.service;

import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealCreateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealUpdateDto;
import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import ru.it.solutions.suggest.complaint.app.model.enums.AppealStatus;
import ru.it.solutions.suggest.complaint.app.model.mappers.AppealMapper;
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
    private final AppealMapper appealMapper;

    @Transactional
    public AppealResponseDto createAppeal(AppealCreateDto createDto) {
        log.info("Создание нового обращения");

        if (createDto.getPersonalDataConsent() == null || !createDto.getPersonalDataConsent()) {
            throw new IllegalArgumentException("Необходимо согласие на обработку персональных данных");
        }

        Appeal appeal = appealMapper.toEntity(createDto);
        appeal.setStatus(AppealStatus.NEW);

        Appeal savedAppeal = appealRepository.save(appeal);
        log.info("Обращение создано с id: {}", savedAppeal.getId());

        return appealMapper.toResponseDto(savedAppeal);
    }

    public List<AppealResponseDto> getAllAppeals() {
        return appealRepository.findAll().stream()
                .map(appealMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    public AppealResponseDto getAppealById(UUID id) {
        Appeal appeal = appealRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Обращение не найдено с id: " + id));
        return appealMapper.toResponseDto(appeal);
    }

    @Transactional
    public AppealResponseDto patchAppeal(UUID id, AppealUpdateDto updateDto) {
        log.info("Обновление обращения с id: {}", id);

        Appeal appeal = appealRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Обращение не найдено с id: " + id));

        appealMapper.updateEntity(appeal, updateDto);

        Appeal updatedAppeal = appealRepository.save(appeal);

        return appealMapper.toResponseDto(updatedAppeal);
    }

    @Transactional
    public void deleteAppeal(UUID id) {
        log.info("Удаление обращения с id: {}", id);

        if (!appealRepository.existsById(id)) {
            throw new RuntimeException("Обращение не найдено с id: " + id);
        }
        appealRepository.deleteById(id);
    }
}