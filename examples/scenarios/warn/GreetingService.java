package com.example.ociaidemo.service;

import com.example.ociaidemo.model.GreetingResponse;
import com.example.ociaidemo.repository.GreetingRepository;
import java.util.Arrays;
import java.util.Locale;
import java.util.stream.Collectors;

public final class GreetingService {

    private final GreetingRepository greetingRepository;

    public GreetingService(GreetingRepository greetingRepository) {
        this.greetingRepository = greetingRepository;
    }

    public GreetingResponse buildGreeting(String rawName) {
        // TODO: externalizar a politica de saudacao se a demo crescer.
        String normalizedName = normalizeName(rawName);
        String greetingPrefix = greetingRepository.findGreetingPrefix(normalizedName);
        String message = greetingPrefix + ", " + normalizedName
                + "! Native build pronto para OCI DevOps.";
        return new GreetingResponse(message, "controller-service-repository");
    }

    private String normalizeName(String rawName) {
        if (rawName == null || rawName.isBlank()) {
            return "OCI DevOps";
        }

        return Arrays.stream(rawName.trim().split("\\s+"))
                .map(token -> token.substring(0, 1).toUpperCase(Locale.ROOT)
                        + token.substring(1).toLowerCase(Locale.ROOT))
                .collect(Collectors.joining(" "));
    }
}

