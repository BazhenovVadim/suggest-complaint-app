package ru.it.solutions.suggest.complaint.app.model.dto.user;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;
import ru.it.solutions.suggest.complaint.app.model.enums.UserRole;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class UserResponseDto {
    private UUID id;
    private String email;
    private boolean confirmed;
    private String fullName;
    private String firstname;
    private String middlename;
    private String lastname;
    private String vkUserId;
    private String telegramUserId;
    private UserRole role;
}
