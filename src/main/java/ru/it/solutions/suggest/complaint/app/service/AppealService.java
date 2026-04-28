package ru.it.solutions.suggest.complaint.app.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealCreateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealResponseDto;
import ru.it.solutions.suggest.complaint.app.model.dto.appeal.AppealUpdateDto;
import ru.it.solutions.suggest.complaint.app.model.dto.user.UserResponseDto;
import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;
import ru.it.solutions.suggest.complaint.app.model.enums.AppealStatus;
import ru.it.solutions.suggest.complaint.app.model.mappers.AppealMapper;
import ru.it.solutions.suggest.complaint.app.model.mappers.UserMapper;
import ru.it.solutions.suggest.complaint.app.repository.AppealRepository;

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
    private final UserMapper userMapper;

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

    // READ all (для администратора - все обращения)
    public List<AppealResponseDto> getAllAppeals() {
        log.info("Получение всех обращений");
        return appealRepository.findAll().stream()
                .map(appealMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    // READ all by user (получить все обращения конкретного пользователя)
    public List<AppealResponseDto> getAllAppealsByUserId(UUID userId) {
        log.info("Получение всех обращений пользователя: {}", userId);

        // Проверяем, существует ли пользователь

        UserEntity user = userService.getUserById(userId);
        return appealRepository.findByUser(user).stream()
                .map(appealMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    // READ by id (без проверки прав - можно смотреть любое обращение)
    public AppealResponseDto getAppealById(UUID id) {
        log.info("Получение обращения по id: {}", id);

        Appeal appeal = getAppealEntityById(id);
        return appealMapper.toResponseDto(appeal);
    }

    @Transactional
    public AppealResponseDto patchAppeal(UUID id, AppealUpdateDto updateDto, UUID userId) {
        log.info("Обновление обращения с id: {} пользователем: {}", id, userId);

        // 1. Находим обращение
        Appeal appeal = getAppealEntityById(id);

        // 2. ПРОВЕРКА ПРАВ: только автор может редактировать
        checkAppealOwnership(appeal, userId);

        // 3. Обновляем поля
        appealMapper.updateEntity(appeal, updateDto);

        // 4. Сохраняем
        Appeal updatedAppeal = appealRepository.save(appeal);

        log.info("Обращение {} обновлено пользователем {}", id, userId);
        return appealMapper.toResponseDto(updatedAppeal);
    }

    @Transactional
    public void deleteAppeal(UUID id, UUID userId) {
        log.info("Удаление обращения с id: {} пользователем: {}", id, userId);

        // 1. Находим обращение
        Appeal appeal = getAppealEntityById(id);

        // 2. ПРОВЕРКА ПРАВ: только автор может удалить
        checkAppealOwnership(appeal, userId);

        // 3. Удаляем
        appealRepository.deleteById(id);

        log.info("Обращение {} удалено пользователем {}", id, userId);
    }

    // === ПРИВАТНЫЕ МЕТОДЫ ===

    // Получить сущность Appeal по ID (с проверкой существования)
    private Appeal getAppealEntityById(UUID id) {
        return appealRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Обращение не найдено с id: " + id));
    }

    // Проверка прав: может ли пользователь изменять/удалять обращение
    private void checkAppealOwnership(Appeal appeal, UUID userId) {
        // Проверяем, есть ли привязанный пользователь у обращения
        if (appeal.getUser() == null) {
            throw new RuntimeException("У обращения нет привязанного пользователя");
        }

        // Сравниваем ID автора обращения с ID текущего пользователя
        if (!appeal.getUser().getId().equals(userId)) {
            log.warn("Попытка доступа к обращению {} пользователем {}, не являющимся автором",
                    appeal.getId(), userId);
            throw new RuntimeException("Доступ запрещен. Вы не являетесь автором обращения");
        }
    }
}