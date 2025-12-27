package com.aquawatch.notification.repository;

import com.aquawatch.notification.model.Alert;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface AlertRepository extends MongoRepository<Alert, String> {
    List<Alert> findBySensorId(String sensorId);
    List<Alert> findBySeverity(String severity);
    List<Alert> findByTimestampBetween(LocalDateTime start, LocalDateTime end);
    List<Alert> findByAlertType(String alertType);
}


