package ru.it.solutions.suggest.complaint.app.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;
import ru.it.solutions.suggest.complaint.app.model.dto.event.AppealStatusChangedEvent;

import java.util.UUID;

@Component
@RequiredArgsConstructor
@Slf4j
public class AppealEventPublisher {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Value("${app.kafka.topics.appeal-created:appeal.created}")
    private String appealCreatedTopic;

    @Value("${app.kafka.topics.appeal-status-changed:appeal.status.changed}")
    private String appealStatusChangedTopic;


    public void publishAppealStatusChanged(AppealStatusChangedEvent event) {
        sendEvent(appealStatusChangedTopic, event.userId(), event);
    }

    private void sendEvent(String topic, UUID userId, Object event) {
        String key = userId != null ? userId.toString() : "unknown";
        kafkaTemplate.send(topic, key, event)
                .whenComplete((result, ex) -> {
                    if (ex != null) {
                        log.error("Не удалось опубликовать событие в Kafka topic={} key={}", topic, key, ex);
                        return;
                    }
                    log.info("Событие опубликовано в Kafka topic={} key={} offset={}",
                            topic,
                            key,
                            result.getRecordMetadata().offset());
                });
    }
}
