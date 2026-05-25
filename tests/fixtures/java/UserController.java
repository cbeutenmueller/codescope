package com.example.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import com.example.repository.UserRepository;
import com.example.service.UserService;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private UserService userService;

    @GetMapping("/profile")
    public UserDto getProfile(Authentication auth) {
        // Smell: fetches user from DB when principal is already available
        User user = userRepository.findByUsername(auth.getName());
        return new UserDto(user);
    }

    @GetMapping("/{id}")
    public UserDto getUser(@PathVariable Long id) {
        return userService.findById(id).map(UserDto::new).orElse(null);
    }
}
