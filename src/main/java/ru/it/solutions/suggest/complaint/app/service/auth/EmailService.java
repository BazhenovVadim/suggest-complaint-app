package ru.it.solutions.suggest.complaint.app.service.auth;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class EmailService {
    public void sendPasswordReset(String to, String token) {
        // in prod -> send real email. Here log.
        log.info("Sending password reset to {}: token={}", to, token);
    }
}
