package ru.it.solutions.suggest.complaint.app.repository;

import org.springframework.data.jpa.repository.Query;
import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;
import ru.it.solutions.suggest.complaint.app.model.enums.AppealStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface AppealRepository extends JpaRepository<Appeal, UUID> {

    // Получить следующий номер обращения (из sequence)
    @Query(value = "SELECT nextval('appeal_number_seq')", nativeQuery = true)
    Long getNextAppealNumber();

    // Поиск всех обращений пользователя (по Entity)
    List<Appeal> findByUser(UserEntity user);

    // Поиск всех обращений по ID пользователя
    List<Appeal> findByUserId(UUID userId);

    // Поиск обращений по статусу
    List<Appeal> findByStatus(AppealStatus status);

    // Поиск обращений пользователя по статусу
    List<Appeal> findByUserAndStatus(UserEntity user, AppealStatus status);
}