package com.aquawatch.notification.service;

import com.aquawatch.notification.model.NotificationLog;
import com.aquawatch.notification.repository.NotificationLogRepository;
import com.twilio.Twilio;
import com.twilio.rest.api.v2010.account.Message;
import com.twilio.type.PhoneNumber;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
@Slf4j
public class SmsService {
    
    private final NotificationLogRepository logRepository;
    
    @Value("${twilio.account.sid:}")
    private String accountSid;
    
    @Value("${twilio.auth.token:}")
    private String authToken;
    
    @Value("${twilio.phone.number:}")
    private String fromPhoneNumber;
    
    public SmsService(NotificationLogRepository logRepository) {
        this.logRepository = logRepository;
    }
    
    public boolean sendSms(String to, String message, String alertId) {
        NotificationLog log = new NotificationLog();
        log.setNotificationType("SMS");
        log.setRecipient(to);
        log.setMessage(message);
        log.setTimestamp(LocalDateTime.now());
        log.setAlertId(alertId);
        
        try {
            // Initialize Twilio if credentials are provided
            if (accountSid != null && !accountSid.isEmpty() && 
                authToken != null && !authToken.isEmpty()) {
                Twilio.init(accountSid, authToken);
                
                Message twilioMessage = Message.creator(
                    new PhoneNumber(to),
                    new PhoneNumber(fromPhoneNumber),
                    message
                ).create();
                
                log.setStatus("SUCCESS");
                log.setErrorMessage(null);
                logRepository.save(log);
                
                log.info("SMS sent successfully to {}: Message SID: {}", to, twilioMessage.getSid());
                return true;
            } else {
                // Fallback: log without sending (for development/testing)
                log.setStatus("PENDING");
                log.setErrorMessage("Twilio credentials not configured");
                logRepository.save(log);
                
                log.warn("Twilio credentials not configured. SMS not sent to {}", to);
                log.info("SMS would be sent to {}: {}", to, message);
                return false;
            }
        } catch (Exception e) {
            log.setStatus("FAILED");
            log.setErrorMessage(e.getMessage());
            logRepository.save(log);
            
            log.error("Failed to send SMS to {}: {}", to, e.getMessage(), e);
            return false;
        }
    }
}


