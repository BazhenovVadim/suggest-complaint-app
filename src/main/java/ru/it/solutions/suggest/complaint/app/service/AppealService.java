package ru.it.solutions.suggest.complaint.app.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealCreateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealUpdateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.event.AppealStatusChangedEvent;
import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;
import ru.it.solutions.suggest.complaint.app.model.enums.AppealStatus;
import ru.it.solutions.suggest.complaint.app.model.enums.UserRole;
import ru.it.solutions.suggest.complaint.app.model.mappers.AppealMapper;
import ru.it.solutions.suggest.complaint.app.repository.AppealRepository;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class AppealService {

    private final AppealRepository appealRepository;
    private final AppealMapper appealMapper;
    private final UserService userService;
    private final AppealEventPublisher appealEventPublisher;

    @Transactional
    public AppealResponseDto createAppeal(AppealCreateDto createDto, UserEntity user) {
        log.info("Создание нового обращения пользователем: {}", user.getId());

        if (createDto.getPersonalDataConsent() == null || !createDto.getPersonalDataConsent()) {
            throw new IllegalArgumentException("Необходимо согласие на обработку персональных данных");
        }

        Appeal appeal = appealMapper.toEntity(createDto);
        appeal.setAppealNumber(appealRepository.getNextAppealNumber());
        appeal.setStatus(AppealStatus.NEW);
        appeal.setUser(user);

        Appeal savedAppeal = appealRepository.save(appeal);
        log.info("Обращение создано с id: {}", savedAppeal.getId());

        return appealMapper.toResponseDto(savedAppeal);
    }

    public List<AppealResponseDto> getAvailableAppeals(UserEntity currentUser) {
        if (isAdmin(currentUser)) {
            log.info("Администратор {} получает все обращения", currentUser.getId());
            return getAllAppeals();
        }

        return getAllAppealsByUserId(currentUser.getId());
    }

    public List<AppealResponseDto> getAllAppeals() {
        log.info("Получение всех обращений");
        return appealRepository.findAll().stream()
                .map(appealMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    public List<AppealResponseDto> getAllAppealsByUserId(UUID userId) {
        log.info("Получение всех обращений пользователя: {}", userId);

        UserEntity user = userService.getUserById(userId);
        return appealRepository.findByUser(user).stream()
                .map(appealMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    public AppealResponseDto getAppealById(UUID id, UserEntity currentUser) {
        log.info("Получение обращения по id: {} пользователем: {}", id, currentUser.getId());

        Appeal appeal = getAppealEntityById(id);
        checkAppealAccess(appeal, currentUser);
        return appealMapper.toResponseDto(appeal);
    }

    @Transactional
    public AppealResponseDto patchAppeal(UUID id, AppealUpdateDto updateDto, UserEntity currentUser) {
        log.info("Обновление обращения с id: {} пользователем: {}", id, currentUser.getId());

        Appeal appeal = getAppealEntityById(id);
        checkAppealAccess(appeal, currentUser);
        appealMapper.updateEntity(appeal, updateDto);

        Appeal updatedAppeal = appealRepository.save(appeal);

        return appealMapper.toResponseDto(updatedAppeal);
    }

    @Transactional
    public AppealResponseDto updateAppealStatus(UUID id, AppealStatus status, UserEntity currentUser) {
        log.info("Изменение статуса обращения {} на {} администратором {}", id, status, currentUser.getId());

        if (!isAdmin(currentUser)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN,
                    "Менять статус обращения может только администратор");
        }

        Appeal appeal = getAppealEntityById(id);
        AppealStatus oldStatus = appeal.getStatus();
        appeal.setStatus(status);
        Appeal updatedAppeal = appealRepository.save(appeal);
        if (oldStatus != status) {
            appealEventPublisher.publishAppealStatusChanged(AppealStatusChangedEvent.builder()
                    .appealId(updatedAppeal.getId())
                    .appealNumber(updatedAppeal.getAppealNumber())
                    .userId(updatedAppeal.getUser() != null ? updatedAppeal.getUser().getId() : null)
                    .vkUserId(updatedAppeal.getUser() != null ? updatedAppeal.getUser().getVkUserId() : null)
                    .telegramUserId(updatedAppeal.getUser() != null ? updatedAppeal.getUser().getTelegramUserId() : null)
                    .oldStatus(oldStatus != null ? oldStatus.name() : null)
                    .newStatus(status != null ? status.name() : null)
                    .changedAt(Instant.now())
                    .build());
        }
        log.info("Обращение {} обновлено пользователем {}", id, currentUser.getId());
        return appealMapper.toResponseDto(updatedAppeal);
    }

    @Transactional
    public void deleteAppeal(UUID id, UserEntity currentUser) {
        log.info("Удаление обращения с id: {} пользователем: {}", id, currentUser.getId());

        Appeal appeal = getAppealEntityById(id);
        checkAppealAccess(appeal, currentUser);

        appealRepository.deleteById(id);

        log.info("Обращение {} удалено пользователем {}", id, currentUser.getId());
    }

    private Appeal getAppealEntityById(UUID id) {
        return appealRepository.findById(id)
                .orElseThrow(
                        () -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Обращение не найдено с id: " + id));
    }

    private void checkAppealAccess(Appeal appeal, UserEntity currentUser) {
        if (isAdmin(currentUser)) {
            return;
        }

        if (appeal.getUser() == null || !appeal.getUser().getId().equals(currentUser.getId())) {
            log.warn("Попытка доступа к обращению {} пользователем {}, не являющимся автором",
                    appeal.getId(), currentUser.getId());
            throw new ResponseStatusException(HttpStatus.FORBIDDEN,
                    "Доступ запрещен. Вы не являетесь автором обращения");
        }
    }

    private boolean isAdmin(UserEntity user) {
        return user.getRole() == UserRole.ADMIN;
    }
}
