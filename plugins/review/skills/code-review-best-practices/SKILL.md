---
name: code-review-best-practices
description: Provides a structured framework for performing a rigorous best practices review of a code segment or file.
---

# Best Practices Code Review

As an autonomous AI coding assistant, use this skill to perform a rigorous best practices review of a codebase or file. Evaluate the code against the focus areas below.

## Focus Areas

### 1. Code Style & Readability
- Is the code following language/framework conventions?
- Are naming conventions clear and consistent?
- Is the code self-documenting?
- Are comments helpful and up-to-date?
- Is indentation and formatting consistent?

### 2. Code Organization
- Is code properly modularized?
- Is separation of concerns respected?
- Are functions/methods single-purpose?
- Is the file/folder structure logical?
- Is code duplication minimized (DRY principle)?

### 3. Error Handling
- Are errors handled gracefully?
- Are error messages helpful?
- Is there proper logging?
- Are edge cases considered?
- Is defensive programming used appropriately?

### 4. Testing & Testability
- Is the code testable?
- Are dependencies injectable?
- Are side effects isolated?
- Is test coverage adequate?
- Are tests meaningful?

### 5. Maintainability
- Will this code be easy to modify?
- Is technical debt being introduced?
- Are magic numbers/strings avoided?
- Is configuration externalized?
- Is documentation adequate?

### 6. SOLID Principles
- Single Responsibility: Does each unit have one clear purpose?
- Open/Closed: Is code open for extension, closed for modification?
- Liskov Substitution: Are inheritance hierarchies correct?
- Interface Segregation: Are interfaces focused?
- Dependency Inversion: Are abstractions used properly?

### 7. Language/Framework Specific
- Are modern language features used appropriately?
- Are framework best practices followed?
- Are deprecated APIs avoided?
- Are appropriate design patterns used?

### 8. Scalability & Future-Proofing
- Will this code scale with growth?
- Is it flexible for future requirements?
- Are assumptions documented?

## Expected Output

For each issue found, provide the following structured feedback:

1. **Critical Issues**: Must-fix problems
2. **High Priority**: Important improvements
3. **Medium Priority**: Recommended changes
4. **Low Priority**: Nice-to-have enhancements
5. **Code Examples**: Show improved versions following best practices

For each issue, you MUST explain:
- What the problem is
- Why it violates best practices
- What principle/pattern to apply
- How to refactor it
- Benefits of the improvement
