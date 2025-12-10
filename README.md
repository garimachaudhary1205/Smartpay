🚀 Smartpay - PayPal Clone – Backend (Microservices Architecture)

A production-style Fintech payment wallet system inspired by PayPal, built using Spring Boot Microservices, following the PayPal Clone Series by Mrunmai Dahare.
This project simulates real-world payment flows: wallet creation, holds, captures, debits, credits, rewards, notifications, and transaction management — all using event-driven architecture with Kafka.

🧩 Microservices Included
Service	Responsibility
User Service	User registration, login, JWT authentication
Wallet Service	Wallet creation, credit, debit, hold & capture flow
Transaction Service	Stores transaction history & interacts with Wallet
Reward Service	Reward points logic for successful payments
Notification Service	Sends email/notification events
API Gateway	Single-entry routing, authentication, service forwarding
Discovery Service (Optional)	Eureka/Service registry
Kafka	Event-driven communication between services
🏗 Tech Stack

Java 17

Spring Boot 3+

Spring Security + JWT

Spring Cloud (OpenFeign, Gateway)

Spring Kafka

Spring Data JPA / Hibernate

MySQL / H2

Docker Compose

Lombok

Maven

🔥 Core Features
✅ User Service:

Register/Login with encrypted passwords

JWT Token generation

Validate tokens inside other services via Feign Client

✅ Wallet Service:

Create wallet for user

Add money (credit)

Pay money (debit)

Payment Hold Funding + Capture workflow

Scheduler to auto-expire unused holds

✅ Transaction Service:

Save transaction records

Fetch user transaction history

Verify authenticity using JWT

✅ Reward Service:

Points earned on transactions

Bonus points on certain conditions

Kafka consumer for "transaction-success" events

✅ Notification Service:

Kafka consumer for sending notifications

Email/SMS template structure

✅ API Gateway:

Token validation

Routes requests to respective microservices

Central entry point of the whole system

🧱 Architecture Overview
              <img width="822" height="697" alt="image" src="https://github.com/user-attachments/assets/52d5d947-4ef8-4a34-a171-374a5b4e2948" />

 
              Kafka ←──────────── Event Bus ───────────→ Kafka

🐳 Running with Docker Compose
docker-compose up --build


This starts:
MySQL
Zookeeper
Kafka

All microservices

📌 How to Run Locally (Without Docker)
Start Zookeeper + Kafka
Start API Gateway
Start User, Wallet, Transaction, Reward, Notification services
Test using Postman / Curl

📚 API Endpoints Summary
🔐 User Service
Method	Endpoint	Description
POST	/auth/register	Register new user
POST	/auth/login	Login & receive JWT
💰 Wallet Service
Method	Endpoint	Description
POST	/wallet/create	Create wallet
POST	/wallet/credit	Add money
POST	/wallet/debit	Deduct money
POST	/wallet/hold	Create hold
POST	/wallet/capture	Capture an existing hold
🧾 Transaction Service
Method	Endpoint
GET	/transactions/user/{id}
🧪 Test Coverage

JUnit + Mockito

Embedded H2 database for integration tests

🎯 Future Enhancements
UI Dashboard (React)
Fraud detection service
More Kafka events
Refund processing

## 💡 Author
**Garima Chaudhary**

[![GitHub](https://img.shields.io/badge/GitHub-Profile-black?style=for-the-badge&logo=github)](https://github.com/garimachaudhary1205)  
[![Gmail](https://img.shields.io/badge/Email-garimachaudhary1205@gmail.com-red?style=for-the-badge&logo=gmail)](mailto:garimachaudhary1205@gmail.com)  

📌 **Role:** Backend Developer
