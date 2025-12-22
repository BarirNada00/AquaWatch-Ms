package com.aquawatch.notification.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AlertRequest {
    @NotBlank(message = "Alert type is required")
    private String alertType; // ANOMALY, SYSTEM, CUSTOM
    
    @NotBlank(message = "Severity is required")
    private String severity; // CRITICAL, HIGH, MEDIUM, LOW
    
    @NotBlank(message = "Title is required")
    private String title;
    
    @NotBlank(message = "Message is required")
    private String message;
    
    private String sensorId;
    private String anomalyId;
    private String recipientPhone;
    private String recipientEmail;
}


