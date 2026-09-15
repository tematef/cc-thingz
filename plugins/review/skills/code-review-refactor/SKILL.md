---
name: code-review-refactor
description: Analyzes code to identify and execute refactoring opportunities to improve code quality, maintainability, and performance without changing external behavior.
---

# Code Refactoring Suggestions

As an autonomous AI coding assistant, use this skill to analyze a code segment or file to identify refactoring opportunities. Your goal is to improve code quality, maintainability, and performance without changing the external behavior of the system.

## Focus Areas

### 1. Code Smells
- Long methods/functions
- Large classes
- Duplicated code
- Long parameter lists
- Deeply nested control structures (arrow code)
- Primitive obsession

### 2. Design Patterns
- Opportunities to apply established patterns (e.g., Strategy, Factory, Observer)
- Anti-patterns to remove

### 3. Simplification
- Complex boolean expressions
- Unnecessary variables or logic
- Dead code removal
- Consolidation of conditionals

### 4. Extract & Compose
- Methods that should be extracted
- Classes that should be split
- Modules that should be separated
- Utilities that should be shared
- Constants that should be defined

### 5. Naming Improvements
- Variables with unclear names
- Functions that don't describe what they do
- Classes with vague or misleading names
- Naming inconsistencies

### 6. Dependency Management
- Dependencies that should be inverted
- Coupling that should be reduced
- Cohesion that should be improved
- Circular dependencies to eliminate

### 7. Modern Code Practices
- Legacy patterns to modernize
- Functional programming opportunities
- Async/await over callbacks
- Modern syntax improvements
- Type safety enhancements

### 8. Architecture Improvements
- Layer violations to fix
- Separation of concerns issues
- API design improvements
- State management enhancements

## Expected Output

When presenting your findings or preparing your implementation plan, provide the following structured feedback:

1. **High Impact Refactorings**: Most valuable changes
2. **Medium Impact**: Worthwhile improvements
3. **Low Impact**: Polish and minor enhancements
4. **Before/After Examples**: Show concrete refactoring steps
5. **Step-by-Step Guide**: Safe refactoring sequence
6. **Tests to Write**: What to test before/during refactoring

For each refactoring, you MUST explain:
- What needs to change
- Why it's beneficial
- How to refactor safely
- What tests to have in place
- Expected improvement in maintainability
