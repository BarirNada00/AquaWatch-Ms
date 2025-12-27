package com.aquawatch.notification.repository;

import com.aquawatch.notification.model.NotificationLog;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface NotificationLogRepository extends MongoRepository<NotificationLog, String> {
    List<NotificationLog> findByNotificationType(String notificationType);
    List<NotificationLog> findByStatus(String status);
    List<NotificationLog> findByTimestampBetween(LocalDateTime start, LocalDateTime end);
    List<NotificationLog> findByAlertId(String alertId);
}


