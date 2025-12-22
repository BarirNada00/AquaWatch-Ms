package com.aquawatch.notification.service;

import com.aquawatch.notification.model.NotificationLog;
import com.aquawatch.notification.repository.NotificationLogRepository;
import com.sendgrid.Method;
import com.sendgrid.Request;
import com.sendgrid.SendGrid;
import com.sendgrid.helpers.mail.Mail;
import com.sendgrid.helpers.mail.objects.Content;
import com.sendgrid.helpers.mail.objects.Email;
import jakarta.mail.internet.MimeMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
@Slf4j
public class EmailService {
    
    private final NotificationLogRepository logRepository;
    private final JavaMailSender javaMailSender;
    
    @Value("${sendgrid.api.key:}")
    private String sendGridApiKey;
    
    @Value("${sendgrid.from.email:}")
    private String sendGridFromEmail;
    
    @Value("${spring.mail.host:}")
    private String smtpHost;
    
    @Value("${spring.mail.username:}")
    private String smtpUsername;
    
    @Value("${spring.mail.from:noreply@aquawatch.com}")
    private String smtpFromEmail;
    
    @Value("${email.provider:sendgrid}")
    private String emailProvider; // sendgrid or smtp
    
    public EmailService(NotificationLogRepository logRepository, JavaMailSender javaMailSender) {
        this.logRepository = logRepository;
        this.javaMailSender = javaMailSender;
    }
    
    public boolean sendEmail(String to, String subject, String message, String alertId) {
        NotificationLog log = new NotificationLog();
        log.setNotificationType("EMAIL");
        log.setRecipient(to);
        log.setSubject(subject);
        log.setMessage(message);
        log.setTimestamp(LocalDateTime.now());
        log.setAlertId(alertId);
        
        try {
            if ("sendgrid".equalsIgnoreCase(emailProvider) && 
                sendGridApiKey != null && !sendGridApiKey.isEmpty()) {
                return sendViaSendGrid(to, subject, message, log);
            } else if ("smtp".equalsIgnoreCase(emailProvider) && 
                       smtpHost != null && !smtpHost.isEmpty()) {
                return sendViaSmtp(to, subject, message, log);
            } else {
                // Fallback: log without sending
                log.setStatus("PENDING");
                log.setErrorMessage("Email provider not configured");
                logRepository.save(log);
                
                log.warn("Email provider not configured. Email not sent to {}", to);
                log.info("Email would be sent to {}: Subject: {}, Message: {}", to, subject, message);
                return false;
            }
        } catch (Exception e) {
            log.setStatus("FAILED");
            log.setErrorMessage(e.getMessage());
            logRepository.save(log);
            
            log.error("Failed to send email to {}: {}", to, e.getMessage(), e);
            return false;
        }
    }
    
    private boolean sendViaSendGrid(String to, String subject, String message, NotificationLog log) {
        try {
            SendGrid sg = new SendGrid(sendGridApiKey);
            Request request = new Request();
            
            Email from = new Email(sendGridFromEmail != null && !sendGridFromEmail.isEmpty() 
                ? sendGridFromEmail : smtpFromEmail);
            Email toEmail = new Email(to);
            Content content = new Content("text/html", message);
            Mail mail = new Mail(from, subject, toEmail, content);
            
            request.setMethod(Method.POST);
            request.setEndpoint("mail/send");
            request.setBody(mail.build());
            
            com.sendgrid.Response response = sg.api(request);
            
            if (response.getStatusCode() >= 200 && response.getStatusCode() < 300) {
                log.setStatus("SUCCESS");
                log.setErrorMessage(null);
                logRepository.save(log);
                
                log.info("Email sent successfully via SendGrid to {}", to);
                return true;
            } else {
                log.setStatus("FAILED");
                log.setErrorMessage("SendGrid API returned status: " + response.getStatusCode());
                logRepository.save(log);
                
                log.error("SendGrid API error: Status {}, Body {}", 
                    response.getStatusCode(), response.getBody());
                return false;
            }
        } catch (Exception e) {
            log.setStatus("FAILED");
            log.setErrorMessage(e.getMessage());
            logRepository.save(log);
            throw new RuntimeException("SendGrid error", e);
        }
    }
    
    private boolean sendViaSmtp(String to, String subject, String message, NotificationLog log) {
        try {
            MimeMessage mimeMessage = javaMailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");
            
            helper.setFrom(smtpFromEmail);
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(message, true); // true = HTML content
            
            javaMailSender.send(mimeMessage);
            
            log.setStatus("SUCCESS");
            log.setErrorMessage(null);
            logRepository.save(log);
            
            log.info("Email sent successfully via SMTP to {}", to);
            return true;
        } catch (Exception e) {
            log.setStatus("FAILED");
            log.setErrorMessage(e.getMessage());
            logRepository.save(log);
            throw new RuntimeException("SMTP error", e);
        }
    }
}


