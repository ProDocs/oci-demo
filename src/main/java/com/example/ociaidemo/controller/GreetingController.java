package com.example.ociaidemo.controller;

import com.example.ociaidemo.repository.GreetingRepository;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public final class GreetingController implements HttpHandler {

    private final GreetingRepository greetingRepository = new GreetingRepository();

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            exchange.sendResponseHeaders(405, -1);
            return;
        }

        String name = extractName(exchange.getRequestURI().getRawQuery());
        String prefix = greetingRepository.findGreetingPrefix(name);
        String response = "{\"message\":\"" + prefix + ", " + name + "!\"}";
        byte[] payload = response.getBytes(StandardCharsets.UTF_8);

        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(200, payload.length);
        try (OutputStream outputStream = exchange.getResponseBody()) {
            outputStream.write(payload);
        }
    }

    private String extractName(String rawQuery) {
        if (rawQuery == null || rawQuery.isBlank()) {
            return "OCI DevOps";
        }

        return Arrays.stream(rawQuery.split("&"))
                .map(pair -> pair.split("=", 2))
                .filter(parts -> parts.length == 2 && "name".equals(parts[0]))
                .map(parts -> URLDecoder.decode(parts[1], StandardCharsets.UTF_8))
                .findFirst()
                .orElse("OCI DevOps");
    }
}

