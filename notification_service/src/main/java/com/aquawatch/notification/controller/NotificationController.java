package com.aquawatch.notification.controller;

import com.aquawatch.notification.dto.EmailRequest;
import com.aquawatch.notification.dto.SmsRequest;
import com.aquawatch.notification.service.EmailService;
import com.aquawatch.notification.service.SmsService;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/notifications")
@Slf4j
public class NotificationController {
    
    private final SmsService smsService;
    private final EmailService emailService;
    
    public NotificationController(SmsService smsService, EmailService emailService) {
        this.smsService = smsService;
        this.emailService = emailService;
    }
    
    @PostMapping("/sms")
    public ResponseEntity<Map<String, Object>> sendSms(@Valid @RequestBody SmsRequest request) {
        log.info("SMS request received: to={}", request.getTo());
        
        boolean success = smsService.sendSms(request.getTo(), request.getMessage(), null);
        
        Map<String, Object> response = new HashMap<>();
        response.put("success", success);
        response.put("message", success ? "SMS sent successfully" : "Failed to send SMS");
        response.put("recipient", request.getTo());
        
        return success 
            ? ResponseEntity.ok(response)
            : ResponseEntity.status(500).body(response);
    }
    
    @PostMapping("/email")
    public ResponseEntity<Map<String, Object>> sendEmail(@Valid @RequestBody EmailRequest request) {
        log.info("Email request received: to={}, subject={}", request.getTo(), request.getSubject());
        
        boolean success = emailService.sendEmail(
            request.getTo(), 
            request.getSubject(), 
            request.getMessage(), 
            null
        );
        
        Map<String, Object> response = new HashMap<>();
        response.put("success", success);
        response.put("message", success ? "Email sent successfully" : "Failed to send email");
        response.put("recipient", request.getTo());
        
        return success 
            ? ResponseEntity.ok(response)
            : ResponseEntity.status(500).body(response);
    }
}


