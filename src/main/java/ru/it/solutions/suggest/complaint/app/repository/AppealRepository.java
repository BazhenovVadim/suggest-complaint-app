package ru.it.solutions.suggest.complaint.app.repository;

import ru.it.solutions.suggest.complaint.app.model.entity.Appeal;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.UUID;

@Repository
public interface AppealRepository extends JpaRepository<Appeal, UUID> {
}