package com.aquawatch.notification.controller;

import com.aquawatch.notification.model.NotificationLog;
import com.aquawatch.notification.repository.NotificationLogRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/logs")
@Slf4j
public class NotificationLogController {
    
    private final NotificationLogRepository logRepository;
    
    public NotificationLogController(NotificationLogRepository logRepository) {
        this.logRepository = logRepository;
    }
    
    @GetMapping
    public ResponseEntity<List<NotificationLog>> getAllLogs() {
        return ResponseEntity.ok(logRepository.findAll());
    }
    
    @GetMapping("/type/{type}")
    public ResponseEntity<List<NotificationLog>> getLogsByType(@PathVariable String type) {
        return ResponseEntity.ok(logRepository.findByNotificationType(type));
    }
    
    @GetMapping("/status/{status}")
    public ResponseEntity<List<NotificationLog>> getLogsByStatus(@PathVariable String status) {
        return ResponseEntity.ok(logRepository.findByStatus(status));
    }
    
    @GetMapping("/alert/{alertId}")
    public ResponseEntity<List<NotificationLog>> getLogsByAlert(@PathVariable String alertId) {
        return ResponseEntity.ok(logRepository.findByAlertId(alertId));
    }
}


