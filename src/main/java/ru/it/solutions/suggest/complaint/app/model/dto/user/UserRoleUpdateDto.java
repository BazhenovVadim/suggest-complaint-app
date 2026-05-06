package ru.it.solutions.suggest.complaint.app.model.dto.user;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import ru.it.solutions.suggest.complaint.app.model.enums.UserRole;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserRoleUpdateDto {
    @NotNull(message = "Роль пользователя обязательна")
    private UserRole role;
}
