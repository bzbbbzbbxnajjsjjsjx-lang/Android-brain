# Hilt and product flavor decision rules

Hilt is an official Android DI option. Introduce it when a project has a meaningful dependency graph and Android lifecycle scoping/testing needs that justify compiler/plugin setup; otherwise constructor injection or explicit composition may be simpler. Verify the current Hilt plugin, compiler, KSP/KAPT, AGP, and Kotlin compatibility for that project before configuration.

Product flavors represent genuine product or environment dimensions that need distinct source/configuration. They multiply variants and test/build work. Keep debug/release build types when those are sufficient; do not create placeholder flavors.

**Provenance:** `hilt_android` and `product_flavors`, official Android developer guidance. Current project compatibility remains task-specific.
