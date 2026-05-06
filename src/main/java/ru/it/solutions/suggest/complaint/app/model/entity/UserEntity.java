package ru.it.solutions.suggest.complaint.app.model.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Enumerated;
import jakarta.persistence.EnumType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import ru.it.solutions.suggest.complaint.app.model.enums.UserRole;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "users", uniqueConstraints = @UniqueConstraint(columnNames = "email"))
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class UserEntity {
    @Id
    private UUID id;
    private String vkUserId;
    private String telegramUserId;
    @Column(nullable = false, unique = true)
    private String email;
    @Column(nullable = false)
    private String passwordHash;
    private boolean confirmed;
    private Instant createdAt;
    private String resetTokenHash;
    private Instant resetTokenExpiry;
    private Instant lastResetRequestedAt;
    private String refreshTokenHash;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private UserRole role = UserRole.USER;
    private Instant refreshTokenExpiry;

    @Column(name = "firstname", length = 100)
    private String firstname;

    @Column(name = "middlename", length = 100)
    private String middlename;

    @Column(name = "lastname", length = 100)
    private String lastname;

    @OneToMany(mappedBy = "user")
    private List<Appeal> appeals;


    private UserEntity(UUID id, String email, String passwordHash) {
        this.id = id;
        this.email = email;
        this.passwordHash = passwordHash;
        this.confirmed = false;
        this.role = UserRole.USER;
        this.createdAt = Instant.now();
    }

    public static UserEntity register(String email, String passwordHash) {
        return new UserEntity(UUID.randomUUID(), email.toLowerCase(), passwordHash);
    }

    public boolean checkPassword(String rawOrHash, java.util.function.BiPredicate<String, String> verifier) {
        return verifier.test(rawOrHash, passwordHash);
    }

    public void setPassword(String newPasswordHash) {
        this.passwordHash = newPasswordHash;
        // invalidate reset token
        this.resetTokenHash = null;
        this.resetTokenExpiry = null;
    }

    public void setResetToken(String tokenHash, Instant expiry, Instant requestAt) {
        this.resetTokenHash = tokenHash;
        this.resetTokenExpiry = expiry;
        this.lastResetRequestedAt = requestAt;
    }

    public boolean verifyResetToken(String tokenHash, Instant now) {
        if (resetTokenHash == null || resetTokenExpiry == null) return false;
        if (now.isAfter(resetTokenExpiry)) return false;
        boolean ok = resetTokenHash.equals(tokenHash);
        if (ok) {
            // consume token (single-use)
            this.resetTokenHash = null;
            this.resetTokenExpiry = null;
        }
        return ok;
    }

    public void setRefreshToken(String refreshTokenHash, Instant expiry) {
        this.refreshTokenHash = refreshTokenHash;
        this.refreshTokenExpiry = expiry;
    }

    public void clearRefreshToken() {
        this.refreshTokenHash = null;
        this.refreshTokenExpiry = null;
    }

    public void confirm() {
        this.confirmed = true;
    }
}