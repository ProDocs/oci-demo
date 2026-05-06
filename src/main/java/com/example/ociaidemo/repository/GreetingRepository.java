package com.example.ociaidemo.repository;

import java.util.Collections;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

public final class GreetingRepository {

    private final Map<String, String> prefixes;

    public GreetingRepository() {
        Map<String, String> mutablePrefixes = new HashMap<String, String>();
        mutablePrefixes.put("oci", "Hello from OCI DevOps");
        mutablePrefixes.put("graalvm", "Hello from GraalVM EE");
        mutablePrefixes.put("oracle", "Hello from Oracle Generative AI");
        this.prefixes = Collections.unmodifiableMap(mutablePrefixes);
    }

    public String findGreetingPrefix(String normalizedName) {
        return prefixes.getOrDefault(normalizedName.toLowerCase(Locale.ROOT), "Hello");
    }
}
