package ru.it.solutions.suggest.complaint.app.model.dto.appeal;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import ru.it.solutions.suggest.complaint.app.model.enums.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AppealUpdateDto {

    private AppealType type;
    private LocationType campusLocation;
    private ProblemCategory problemCategory;
    private Timeframe timeframe;
    private String description;
    private String filePath;
    private String fileName;
    private String contactName;
    private String contactPhone;
    private String contactEmail;
    private Boolean personalDataConsent;
    private AppealStatus status;
}