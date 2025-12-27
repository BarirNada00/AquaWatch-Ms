package com.aquawatch.notification.controller;

import com.aquawatch.notification.dto.AlertRequest;
import com.aquawatch.notification.dto.AnomalyAlertRequest;
import com.aquawatch.notification.model.Alert;
import com.aquawatch.notification.service.AlertService;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/alerts")
@Slf4j
public class AlertController {
    
    private final AlertService alertService;
    
    public AlertController(AlertService alertService) {
        this.alertService = alertService;
    }
    
    @PostMapping
    public ResponseEntity<Alert> createAlert(@Valid @RequestBody AlertRequest request) {
        log.info("Alert creation request: type={}, severity={}", request.getAlertType(), request.getSeverity());
        Alert alert = alertService.createAlert(request);
        return ResponseEntity.ok(alert);
    }
    
    @PostMapping("/anomaly")
    public ResponseEntity<Alert> createAlertFromAnomaly(@Valid @RequestBody AnomalyAlertRequest request) {
        log.info("Anomaly alert request: anomalyId={}, type={}", request.getId(), request.getType());
        Alert alert = alertService.createAlertFromAnomaly(request);
        return ResponseEntity.ok(alert);
    }
    
    @GetMapping
    public ResponseEntity<List<Alert>> getAllAlerts() {
        return ResponseEntity.ok(alertService.getAllAlerts());
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<Alert> getAlertById(@PathVariable String id) {
        try {
            Alert alert = alertService.getAlertById(id);
            return ResponseEntity.ok(alert);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    @GetMapping("/sensor/{sensorId}")
    public ResponseEntity<List<Alert>> getAlertsBySensor(@PathVariable String sensorId) {
        return ResponseEntity.ok(alertService.getAlertsBySensor(sensorId));
    }
    
    @GetMapping("/severity/{severity}")
    public ResponseEntity<List<Alert>> getAlertsBySeverity(@PathVariable String severity) {
        return ResponseEntity.ok(alertService.getAlertsBySeverity(severity));
    }
    
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "UP", "service", "notification-service"));
    }
}


