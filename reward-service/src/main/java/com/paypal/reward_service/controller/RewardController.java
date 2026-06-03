package com.paypal.reward_service.controller;



import com.paypal.reward_service.dto.CreateRewardRequest;
import com.paypal.reward_service.entity.Reward;
import com.paypal.reward_service.repository.RewardRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/rewards/")
public class RewardController {
    private final RewardRepository rewardRepository;

    public RewardController(RewardRepository rewardRepository) {
        this.rewardRepository = rewardRepository;
    }

    // 🔹 Get all rewards
    @GetMapping
    public List<Reward> getAllRewards() {
        return rewardRepository.findAll();
    }

    // 🔹 Get rewards by user ID
    @GetMapping("/user/{userId}")
    public List<Reward> getRewardsByUserId(@PathVariable("userId") Long userId) {
        return rewardRepository.findByUserId(userId);
    }

    // 🔹 Create a reward (called directly by transaction-service after a
    //    successful transfer — decoupled from Kafka). Idempotent per txn.
    @PostMapping
    public ResponseEntity<Reward> createReward(@RequestBody CreateRewardRequest request) {
        if (request.getTransactionId() != null
                && rewardRepository.existsByTransactionId(request.getTransactionId())) {
            // Already rewarded for this transaction — idempotent no-op
            return ResponseEntity.ok().build();
        }

        Reward reward = new Reward();
        reward.setUserId(request.getUserId());
        reward.setPoints(request.getAmount() * 100);
        reward.setSentAt(LocalDateTime.now());
        reward.setTransactionId(request.getTransactionId());
        rewardRepository.save(reward);
        return ResponseEntity.ok(reward);
    }

}