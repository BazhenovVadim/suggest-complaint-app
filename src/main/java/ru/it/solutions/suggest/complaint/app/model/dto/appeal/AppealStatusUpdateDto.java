package ru.it.solutions.suggest.complaint.app.model.dto.appeal;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import ru.it.solutions.suggest.complaint.app.model.enums.AppealStatus;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AppealStatusUpdateDto {
    @NotNull(message = "Статус обращения обязателен")
    private AppealStatus status;
}
