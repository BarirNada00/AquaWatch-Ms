package com.aquawatch.notification.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;

@Document(collection = "alerts")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Alert {
    @Id
    private String id;
    
    private String alertType; // ANOMALY, SYSTEM, CUSTOM
    private String severity; // CRITICAL, HIGH, MEDIUM, LOW
    private String title;
    private String message;
    private String sensorId;
    private String anomalyId; // Reference to anomaly from anomaly_detector
    private LocalDateTime timestamp;
    private boolean sentSms;
    private boolean sentEmail;
    private String smsStatus;
    private String emailStatus;
    private String recipientPhone;
    private String recipientEmail;
}


