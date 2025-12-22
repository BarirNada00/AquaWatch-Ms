package com.aquawatch.notification.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;

@Document(collection = "notification_logs")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NotificationLog {
    @Id
    private String id;
    
    private String notificationType; // SMS, EMAIL
    private String recipient;
    private String subject;
    private String message;
    private String status; // SUCCESS, FAILED, PENDING
    private String errorMessage;
    private LocalDateTime timestamp;
    private String alertId; // Reference to alert if triggered by alert
}


