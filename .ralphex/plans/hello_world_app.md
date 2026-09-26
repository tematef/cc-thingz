# Implementation Plan: Java Hello World Application

Build a clean, production-grade Java CLI "Hello World" application located in `apps/hello-java`, leveraging modern Java features, Gradle Kotlin DSL build configuration, JUnit 5 testing, and runnable JAR distribution.

## Implementation Steps

### Task 1: Project Scaffolding & Build Configuration
- [ ] Create directory tree `apps/hello-java/src/main/java/com/example/hello` and `apps/hello-java/src/test/java/com/example/hello`.
- [ ] Create `apps/hello-java/settings.gradle.kts` with project name configuration.
- [ ] Create `apps/hello-java/build.gradle.kts` with application plugin, java toolchain, JUnit 5 dependencies, and executable JAR task.

### Task 2: Greeting Domain Service
- [ ] Implement `GreetingService.java` in `com.example.hello` with `formatGreeting(String name)` method.
- [ ] Implement JUnit 5 test suite in `GreetingServiceTest.java` with default and parameterized tests.
- [ ] Run `gradle test` to verify domain logic passes.

### Task 3: CLI Application Entrypoint
- [ ] Implement `App.java` with argument parsing (`--help`, `-h`, custom names).
- [ ] Implement `AppTest.java` capturing standard output for CLI execution tests.
- [ ] Run test suite to verify 100% test coverage for CLI parsing and output.

### Task 4: Packaging & End-to-End Verification
- [ ] Build executable JAR using `gradle jar` or `gradle assemble`.
- [ ] Verify execution with `java -jar build/libs/hello-java.jar`.
- [ ] Verify custom greeting execution: `java -jar build/libs/hello-java.jar "Antigravity Developer"`.
- [ ] Verify help text: `java -jar build/libs/hello-java.jar --help`.
