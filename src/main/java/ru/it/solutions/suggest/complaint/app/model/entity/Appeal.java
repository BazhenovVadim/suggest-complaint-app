package ru.it.solutions.suggest.complaint.app.model.entity;

import ru.it.solutions.suggest.complaint.app.model.enums.*;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "appeals")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Appeal {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private AppealType type;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private LocationType campusLocation;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ProblemCategory problemCategory;

    @Enumerated(EnumType.STRING)
    private Timeframe timeframe;

    @Column(nullable = false, length = 5000)
    private String description;

    private String filePath;
    private String fileName;

    private String contactName;
    private String contactPhone;
    private String contactEmail;

    @Column(nullable = false)
    private Boolean personalDataConsent;

    @CreationTimestamp
    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private AppealStatus status = AppealStatus.NEW;
}