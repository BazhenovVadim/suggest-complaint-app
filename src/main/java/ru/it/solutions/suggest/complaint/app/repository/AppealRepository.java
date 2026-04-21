package ru.it.solutions.suggest.complaint.app.repository;

import org.springframework.data.jpa.repository.Query;
import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.UUID;

@Repository
public interface AppealRepository extends JpaRepository<Appeal, UUID> {
    @Query(value = "SELECT nextval('appeal_number_seq')::int", nativeQuery = true)
    Integer getNextAppealNumber();

}