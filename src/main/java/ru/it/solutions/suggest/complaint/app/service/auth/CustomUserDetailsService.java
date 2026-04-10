package ru.it.solutions.suggest.complaint.app.service.auth;

import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import ru.it.solutions.suggest.complaint.app.model.entity.UserEntity;
import ru.it.solutions.suggest.complaint.app.repository.UserRepository;

import java.util.ArrayList;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    public CustomUserDetailsService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        return userRepository.findByEmail(email.toLowerCase())
                .map(user -> new User(
                        user.getEmail(),
                        user.getPasswordHash(),
                        new ArrayList<>()// нет ролей, пустой список authorities
                ))
                .orElseThrow(() -> new UsernameNotFoundException("User not found: " + email));
    }
}