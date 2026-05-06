package com.example.ociaidemo.model;

public final class GreetingResponse {

    private final String message;
    private final String architecture;

    public GreetingResponse(String message, String architecture) {
        this.message = message;
        this.architecture = architecture;
    }

    public String toJson() {
        return "{\"message\":\"" + escape(message) + "\","
                + "\"architecture\":\"" + escape(architecture) + "\"}";
    }

    private String escape(String value) {
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"");
    }
}
