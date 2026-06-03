package com.paypal.api_gateway.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import java.security.Key;

public class JwtUtil {

    // Read from JWT_SECRET env var in production; falls back to the dev default
    // so local runs work unchanged. Must match the user-service secret.
    private static final String SECRET = System.getenv().getOrDefault(
            "JWT_SECRET", "secret123secret123secret123secret123secret123secret123");

    private static Key getSigningKey() {
        return Keys.hmacShaKeyFor(SECRET.getBytes());
    }

    public static Claims validateToken(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(getSigningKey())
                .build()
                .parseClaimsJws(token)
                .getBody();
    }
}