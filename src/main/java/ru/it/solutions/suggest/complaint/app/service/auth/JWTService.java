package ru.it.solutions.suggest.complaint.app.service.auth;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import javax.crypto.spec.SecretKeySpec;
import java.security.Key;
import java.security.SignatureException;
import java.time.Instant;
import java.util.Base64;
import java.util.Date;

import java.util.UUID;

@Service
public class JWTService {
    private final Key key;

    public JWTService(org.springframework.core.env.Environment env) {
        String secret = env.getProperty("JWT_SECRET", "defaultsecretforsample");
        byte[] bytes = Base64.getEncoder().encode(secret.getBytes());
        this.key = new SecretKeySpec(bytes, SignatureAlgorithm.HS256.getJcaName());
    }

    public String generateAccessToken(UUID userId, String email) {
        Instant now = Instant.now();
        return Jwts.builder()
                .setSubject(userId.toString())
                .claim("email", email)
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(now.plusSeconds(60*15))) // 15m
                .signWith(key)
                .compact();
    }

    public String generateRefreshToken() {
        return java.util.UUID.randomUUID().toString();
    }

    public String extractEmail(String token) {
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
        return claims.get("email", String.class);
    }

    public UUID extractUserId(String token) {
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
        return UUID.fromString(claims.getSubject());
    }

    public boolean isTokenValid(String token, UserDetails userDetails) {
        String email = extractEmail(token);
        return email.equals(userDetails.getUsername()) && !isTokenExpired(token);
    }

    private boolean isTokenExpired(String token) {
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
        return claims.getExpiration().before(new Date());
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token);
            return true;
        } catch (io.jsonwebtoken.ExpiredJwtException |
                 io.jsonwebtoken.MalformedJwtException | IllegalArgumentException e) {
            return false;
        }
    }
}