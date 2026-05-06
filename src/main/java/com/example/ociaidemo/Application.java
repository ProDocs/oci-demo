package com.example.ociaidemo;

import com.example.ociaidemo.controller.GreetingController;
import com.example.ociaidemo.repository.GreetingRepository;
import com.example.ociaidemo.service.GreetingService;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;

public final class Application {

    private Application() {
    }

    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        GreetingRepository repository = new GreetingRepository();
        GreetingService greetingService = new GreetingService(repository);

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/api/greetings", new GreetingController(greetingService));
        server.createContext("/health", Application::handleHealthCheck);
        server.setExecutor(Executors.newFixedThreadPool(4));
        Runtime.getRuntime().addShutdownHook(new Thread(() -> server.stop(0)));
        server.start();

        System.out.println("OCI AI review demo listening on port " + port);
    }

    private static void handleHealthCheck(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            exchange.sendResponseHeaders(405, -1);
            return;
        }

        byte[] payload = "{\"status\":\"UP\"}".getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(200, payload.length);
        try (OutputStream outputStream = exchange.getResponseBody()) {
            outputStream.write(payload);
        }
    }
}

