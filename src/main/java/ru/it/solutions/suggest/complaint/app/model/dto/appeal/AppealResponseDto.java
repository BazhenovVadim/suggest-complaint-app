package ru.it.solutions.suggest.complaint.app.model.dto.appeal;

import ru.it.solutions.suggest.complaint.app.model.enums.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

import java.time.Instant;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AppealResponseDto {
    private UUID id;
    private AppealType type;
    private LocationType campusLocation;
    private ProblemCategory problemCategory;
    private Timeframe timeframe;
    private String description;
    private List<String> attachments;
    private Boolean personalDataConsent;
    private Instant createdAt;
    private AppealStatus status;
    private UUID userId;
    private long appealNumber;
}