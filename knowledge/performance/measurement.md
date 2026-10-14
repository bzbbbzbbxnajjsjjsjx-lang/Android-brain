# Android performance measurement

Establish a representative user journey and a repeatable baseline before optimizing. Use Macrobenchmark for end-to-end startup or interaction measurements on a suitable target; compare equivalent builds, devices, and test conditions and report distributions/configuration. Use trace/profiling evidence to identify the bottleneck. Add Baseline Profile generation only after benchmark infrastructure and target configuration work; validate the generated profile is packaged and measure its effect. Do not infer gains from compilation, recomposition counts, or an unexecuted benchmark.

Device/runtime availability and release/profileable setup are project-specific prerequisites. If unavailable, mark device measurements BLOCKED and limit claims to static inspection or host tests.

**Provenance:** `macrobenchmark` and `baseline_profiles`, official Android performance documentation.
