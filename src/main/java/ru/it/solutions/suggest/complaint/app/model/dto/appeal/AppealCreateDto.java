package ru.it.solutions.suggest.complaint.app.model.dto.appeal;  // ← правильный пакет

import ru.it.solutions.suggest.complaint.app.model.enums.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.ArrayList;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AppealCreateDto {

    @NotNull(message = "Тип обращения обязателен")
    private AppealType type;

    @NotNull(message = "Локация обязательна")
    private LocationType campusLocation;

    @NotNull(message = "Категория проблемы обязательна")
    private ProblemCategory problemCategory;

    private Timeframe timeframe;

    @NotBlank(message = "Описание проблемы обязательно")
    private String description;

    @Builder.Default
    private List<String> attachments = new ArrayList<>();

    private String contactName;
    private String contactPhone;
    private String contactEmail;

    @NotNull(message = "Необходимо согласие на обработку персональных данных")
    private Boolean personalDataConsent;
}