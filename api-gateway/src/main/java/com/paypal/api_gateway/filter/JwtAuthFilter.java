package com.paypal.api_gateway.filter;

import com.paypal.api_gateway.util.JwtUtil;
import io.jsonwebtoken.Claims;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.List;

@Component
public class JwtAuthFilter implements GlobalFilter, Ordered {

    private static final List<String> PUBLIC_PATHS = List.of(
            "/auth/signup",
            "/auth/login"
    );

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getPath().value();
        String normalizedPath = path.replaceAll("/+$", "");

        // Let CORS preflight requests through untouched
        if (exchange.getRequest().getMethod() == HttpMethod.OPTIONS) {
            return chain.filter(exchange);
        }

        // Skip JWT check for public paths
        if (PUBLIC_PATHS.contains(normalizedPath)) {
            return chain.filter(exchange);
        }

        String authHeader = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);

        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            System.err.println("❌ Missing or invalid Authorization header for " + normalizedPath);
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }

        try {
            String token = authHeader.substring(7);
            Claims claims = JwtUtil.validateToken(token);

            String email = claims.getSubject();
            Object userId = claims.get("userId");
            Object role = claims.get("role");

            // Forward identity to downstream services. NOTE: the mutated
            // request must be applied to the exchange, otherwise the headers
            // are silently dropped.
            ServerHttpRequest.Builder requestBuilder = exchange.getRequest().mutate();
            if (email != null) {
                requestBuilder.header("X-User-Email", email);
            }
            if (userId != null) {
                requestBuilder.header("X-User-Id", String.valueOf(userId));
            }
            if (role != null) {
                requestBuilder.header("X-User-Role", String.valueOf(role));
            }
            ServerWebExchange mutatedExchange = exchange.mutate()
                    .request(requestBuilder.build())
                    .build();

            System.out.println("✅ JWT validated for " + email + " (userId=" + userId + ") → " + normalizedPath);
            return chain.filter(mutatedExchange);

        } catch (Exception e) {
            System.err.println("❌ JWT validation failed: " + e.getMessage());
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
    }

    @Override
    public int getOrder() {
        return -1;
    }
}
