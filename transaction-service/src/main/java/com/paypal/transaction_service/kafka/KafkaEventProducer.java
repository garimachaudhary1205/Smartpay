package com.paypal.transaction_service.kafka;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.paypal.transaction_service.entity.Transaction;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

@Component
public class KafkaEventProducer {

    private static final String TOPIC = "txn-initiated";

    private final KafkaTemplate<String, Transaction> kafkaTemplate;
    private final ObjectMapper objectMapper;

    @Autowired
    public KafkaEventProducer(KafkaTemplate<String, Transaction> kafkaTemplate, ObjectMapper objectMapper) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
        // Register module to handle Java 8 date/time serialization
        this.objectMapper.registerModule(new JavaTimeModule());
    }
    public void sendTransactionEvent(String key, Transaction transaction) {
        // Run the whole send on a background thread. kafkaTemplate.send() blocks
        // the calling thread while fetching broker metadata (up to max.block.ms),
        // which would otherwise stall the HTTP response when Kafka is down.
        CompletableFuture.runAsync(() -> {
            System.out.println("📤 Sending to Kafka → Topic: " + TOPIC + ", Key: " + key + ", Message: " + transaction);
            try {
                CompletableFuture<SendResult<String, Transaction>> future = kafkaTemplate.send(TOPIC, key, transaction);
                future.thenAccept(result -> {
                    RecordMetadata metadata = result.getRecordMetadata();
                    System.out.println("✅ Kafka message sent successfully! Topic: " + metadata.topic() + ", Partition: " + metadata.partition() + ", Offset: " + metadata.offset());
                }).exceptionally(ex -> {
                    System.err.println("❌ Failed to send Kafka message: " + ex.getMessage());
                    return null;
                });
            } catch (Exception e) {
                System.err.println("❌ Kafka unavailable, skipping event: " + e.getMessage());
            }
        });
    }
}