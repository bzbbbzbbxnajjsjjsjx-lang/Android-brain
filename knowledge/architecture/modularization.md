# Modularization decision rules

Now in Android presents a learning journey and examples, not a universal module graph. Start from the actual product, ownership boundaries, dependency direction, testability, and build/reuse needs. Add modules when a stable boundary yields concrete ownership, reuse, isolation, or build benefits that outweigh configuration and API maintenance. Avoid reproducing a sample's module count. Reassess using evidence as the project grows.

**Provenance:** `nia_modularization`, retrieved Markdown. Apply as an open-source architecture example alongside the target project's own constraints.
