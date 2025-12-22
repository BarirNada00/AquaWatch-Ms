package com.aquawatch.notification.service;

import com.aquawatch.notification.dto.AlertRequest;
import com.aquawatch.notification.dto.AnomalyAlertRequest;
import com.aquawatch.notification.model.Alert;
import com.aquawatch.notification.repository.AlertRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@Slf4j
public class AlertService {
    
    private final AlertRepository alertRepository;
    private final SmsService smsService;
    private final EmailService emailService;
    
    @Value("${alert.default.phone:}")
    private String defaultPhone;
    
    @Value("${alert.default.email:}")
    private String defaultEmail;
    
    @Value("${alert.enable.sms:true}")
    private boolean enableSms;
    
    @Value("${alert.enable.email:true}")
    private boolean enableEmail;
    
    public AlertService(AlertRepository alertRepository, 
                       SmsService smsService, 
                       EmailService emailService) {
        this.alertRepository = alertRepository;
        this.smsService = smsService;
        this.emailService = emailService;
    }
    
    public Alert createAlert(AlertRequest request) {
        Alert alert = new Alert();
        alert.setId(UUID.randomUUID().toString());
        alert.setAlertType(request.getAlertType());
        alert.setSeverity(request.getSeverity());
        alert.setTitle(request.getTitle());
        alert.setMessage(request.getMessage());
        alert.setSensorId(request.getSensorId());
        alert.setAnomalyId(request.getAnomalyId());
        alert.setTimestamp(LocalDateTime.now());
        
        String phone = request.getRecipientPhone() != null && !request.getRecipientPhone().isEmpty()
            ? request.getRecipientPhone() : defaultPhone;
        String email = request.getRecipientEmail() != null && !request.getRecipientEmail().isEmpty()
            ? request.getRecipientEmail() : defaultEmail;
        
        alert.setRecipientPhone(phone);
        alert.setRecipientEmail(email);
        
        // Send notifications based on configuration
        if (enableSms && phone != null && !phone.isEmpty()) {
            String smsMessage = formatSmsMessage(alert);
            boolean smsSent = smsService.sendSms(phone, smsMessage, alert.getId());
            alert.setSentSms(smsSent);
            alert.setSmsStatus(smsSent ? "SUCCESS" : "FAILED");
        } else {
            alert.setSentSms(false);
            alert.setSmsStatus("SKIPPED");
        }
        
        if (enableEmail && email != null && !email.isEmpty()) {
            String emailSubject = formatEmailSubject(alert);
            String emailBody = formatEmailBody(alert);
            boolean emailSent = emailService.sendEmail(email, emailSubject, emailBody, alert.getId());
            alert.setSentEmail(emailSent);
            alert.setEmailStatus(emailSent ? "SUCCESS" : "FAILED");
        } else {
            alert.setSentEmail(false);
            alert.setEmailStatus("SKIPPED");
        }
        
        alert = alertRepository.save(alert);
        log.info("Alert created: {} - {}", alert.getId(), alert.getTitle());
        
        return alert;
    }
    
    public Alert createAlertFromAnomaly(AnomalyAlertRequest request) {
        AlertRequest alertRequest = new AlertRequest();
        alertRequest.setAlertType("ANOMALY");
        alertRequest.setSeverity(determineSeverity(request.getType()));
        alertRequest.setTitle("Anomaly Detected: " + request.getType());
        alertRequest.setMessage(formatAnomalyMessage(request));
        alertRequest.setSensorId(request.getSensorId());
        alertRequest.setAnomalyId(request.getId());
        alertRequest.setRecipientPhone(request.getRecipientPhone());
        alertRequest.setRecipientEmail(request.getRecipientEmail());
        
        Alert alert = createAlert(alertRequest);
        
        // Preserve the original anomaly timestamp
        if (request.getTimestamp() != null) {
            alert.setTimestamp(request.getTimestamp().toLocalDateTime());
        }
        
        return alert;
    }
    
    public List<Alert> getAllAlerts() {
        return alertRepository.findAll();
    }
    
    public List<Alert> getAlertsBySensor(String sensorId) {
        return alertRepository.findBySensorId(sensorId);
    }
    
    public List<Alert> getAlertsBySeverity(String severity) {
        return alertRepository.findBySeverity(severity);
    }
    
    public Alert getAlertById(String id) {
        return alertRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Alert not found: " + id));
    }
    
    private String determineSeverity(String anomalyType) {
        switch (anomalyType.toUpperCase()) {
            case "SPIKE":
                return "HIGH";
            case "DRIFT":
                return "MEDIUM";
            case "DROPOUT":
                return "CRITICAL";
            default:
                return "MEDIUM";
        }
    }
    
    private String formatSmsMessage(Alert alert) {
        return String.format("[%s] %s: %s", 
            alert.getSeverity(), 
            alert.getTitle(), 
            alert.getMessage());
    }
    
    private String formatEmailSubject(Alert alert) {
        return String.format("[AquaWatch] %s - %s", 
            alert.getSeverity(), 
            alert.getTitle());
    }
    
    private String formatEmailBody(Alert alert) {
        StringBuilder body = new StringBuilder();
        body.append("<html><body>");
        body.append("<h2>").append(alert.getTitle()).append("</h2>");
        body.append("<p><strong>Severity:</strong> ").append(alert.getSeverity()).append("</p>");
        body.append("<p><strong>Message:</strong> ").append(alert.getMessage()).append("</p>");
        if (alert.getSensorId() != null) {
            body.append("<p><strong>Sensor ID:</strong> ").append(alert.getSensorId()).append("</p>");
        }
        if (alert.getAnomalyId() != null) {
            body.append("<p><strong>Anomaly ID:</strong> ").append(alert.getAnomalyId()).append("</p>");
        }
        body.append("<p><strong>Timestamp:</strong> ").append(alert.getTimestamp()).append("</p>");
        body.append("</body></html>");
        return body.toString();
    }
    
    private String formatAnomalyMessage(AnomalyAlertRequest request) {
        StringBuilder message = new StringBuilder();
        message.append("Anomaly Type: ").append(request.getType()).append("\n");
        message.append("Parameter: ").append(request.getParameter()).append("\n");
        if (request.getValue() != null) {
            message.append("Value: ").append(request.getValue()).append("\n");
        }
        message.append("Message: ").append(request.getMessage()).append("\n");
        if (request.getLatitude() != null && request.getLongitude() != null) {
            message.append("Location: ").append(request.getLatitude())
                   .append(", ").append(request.getLongitude()).append("\n");
        }
        return message.toString();
    }
}


