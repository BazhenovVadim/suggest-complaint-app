package ru.it.solutions.suggest.complaint.app.model.dto.event;

import lombok.Builder;

import java.time.Instant;
import java.util.UUID;

@Builder
public record AppealStatusChangedEvent(
        UUID appealId,
        Long appealNumber,
        UUID userId,
        String vkUserId,
        String oldStatus,
        String newStatus,
        Instant changedAt
) {}
