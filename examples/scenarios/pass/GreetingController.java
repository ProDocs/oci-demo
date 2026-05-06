package com.example.ociaidemo.controller;

import com.example.ociaidemo.model.GreetingResponse;
import com.example.ociaidemo.service.GreetingService;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public final class GreetingController implements HttpHandler {

    private final GreetingService greetingService;

    public GreetingController(GreetingService greetingService) {
        this.greetingService = greetingService;
    }

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            exchange.sendResponseHeaders(405, -1);
            return;
        }

        String name = extractName(exchange.getRequestURI().getRawQuery());
        GreetingResponse response = greetingService.buildGreeting(name);
        byte[] payload = response.toJson().getBytes(StandardCharsets.UTF_8);

        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(200, payload.length);
        try (OutputStream outputStream = exchange.getResponseBody()) {
            outputStream.write(payload);
        }
    }

    private String extractName(String rawQuery) {
        if (rawQuery == null || rawQuery.trim().isEmpty()) {
            return "OCI DevOps";
        }

        return Arrays.stream(rawQuery.split("&"))
                .map(pair -> pair.split("=", 2))
                .filter(parts -> parts.length == 2 && "name".equals(parts[0]))
                .map(parts -> decode(parts[1]))
                .findFirst()
                .orElse("OCI DevOps");
    }

    private String decode(String value) {
        try {
            return URLDecoder.decode(value, StandardCharsets.UTF_8.name());
        } catch (UnsupportedEncodingException exception) {
            throw new IllegalStateException("UTF-8 should always be available", exception);
        }
    }
}
