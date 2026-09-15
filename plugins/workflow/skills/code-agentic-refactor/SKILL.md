---
name: code-agentic-refactor
description: Advanced, industry-standard refactoring skill that leverages AST-awareness and surgical diffing to safely restructure code.
---

# Agentic Refactoring Protocol

As an autonomous AI coding assistant, use this skill when executing complex refactorings or rewriting structural components. This protocol ensures changes are robust, verifiable, and do not introduce regressions.

## 1. Abstract Syntax Tree (AST) & Dependency Analysis
Before modifying any file, you MUST build a mental map of its dependencies:
- Use search tools (e.g., `grep_search`, `find_by_name`) to locate all references to the functions/classes you are about to change.
- Identify all incoming dependencies (what calls this code) and outgoing dependencies (what this code calls).
- If the language supports it, prefer structural analysis over simple string matching to ensure you don't break downstream consumers.

## 2. Test Coverage Verification
- Check if tests exist for the target code.
- If test coverage is missing or inadequate, **PAUSE** and propose writing characterization tests first to lock in existing behavior.
- Run the test suite before making any modifications to ensure a clean baseline.

## 3. Surgical Diffing Strategy
Do not rewrite entire files unless absolutely necessary. Instead, use targeted edit tools:
- Identify the precise line ranges `[StartLine, EndLine]` that need modification.
- Make minimal, contiguous replacements.
- Preserve existing whitespace, comments, and structure around the modification.
- Avoid formatting-only changes unless explicitly requested.

## 4. Multi-Agent Validation (Optional but Recommended)
For high-risk changes, consider invoking subagents to simulate a "Debate" or "Review" phase:
- **Implementer**: Drafts the refactoring plan and executes the code changes.
- **Reviewer**: Critiques the diffs against SOLID principles, checking for edge cases and regressions before finalizing.

## 5. Safe Execution Sequence
When proposing or executing the refactor, adhere to this sequence:
1. **Analyze**: Map out all callsites and dependencies.
2. **Verify**: Ensure the baseline test suite passes.
3. **Draft**: Create the implementation plan with precise file modification steps.
4. **Isolate**: Refactor in small, verifiable chunks (e.g., extract a method, run tests, rename a variable, run tests).
5. **Execute**: Apply the surgical replacements.
6. **Validate**: Re-run tests and linters to confirm the system's behavior remains unchanged.

## Expected Output
When using this skill, present your plan and results using this format:

### Refactoring Blueprint
- **Target**: The file, class, or function being refactored.
- **Objective**: The specific technical debt or smell being addressed.
- **Dependencies Affected**: List of files/callsites that will be impacted.

### Execution Log
- [x] Initial test baseline confirmed
- [x] Applied change: [Description of surgical edit]
- [x] Post-change test run confirmed

### Final Summary
- Summary of the structural improvements and evidence that behavior is preserved.
