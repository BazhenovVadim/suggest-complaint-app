package ru.it.solutions.suggest.complaint.app.service.auth;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;

import java.util.Collection;
import java.util.Collections;
import java.util.UUID;

@Getter
@RequiredArgsConstructor
public class CustomUserDetails implements UserDetails {

    private final UserEntity userEntity;

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + userEntity.getRoleOrDefault()));
    }

    @Override
    public String getPassword() {
        return userEntity.getPasswordHash();
    }

    @Override
    public String getUsername() {
        return userEntity.getEmail();
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return userEntity.isConfirmed();
    }

    public UUID getId() {
        return userEntity.getId();
    }

    public String getEmail() {
        return userEntity.getEmail();
    }

    public boolean isConfirmed() {
        return userEntity.isConfirmed();
    }
}
