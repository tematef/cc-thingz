---
name: wiki-builder
description: Ingests raw data files (PDFs, Markdown, Images, text documents) from a source directory, uses concurrent research subagents to process and analyze files in parallel, and compiles them into a structured, indexed Markdown knowledge base in the .wiki/ directory with a master INDEX.md. Use when the user asks to build a wiki, ingest documents into a knowledge base, or convert raw files into an indexed wiki.
---

# Wiki Builder Skill

This skill teaches you how to ingest raw documentation and data files (PDFs, Markdown, Images, text files), process them efficiently in parallel using subagents, and generate a clean, structured Markdown knowledge base (Wiki) in a flat `.wiki/` directory with a master `INDEX.md`.

## Workflow & Step-by-Step Guide

### 1. Source Discovery & File Scanning
- Identify the source directory specified by the user (or scan the project directory for unstructured documentation and assets).
- Use `find_by_name` or `list_dir` to inventory all candidate files (e.g., `.pdf`, `.md`, `.txt`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, etc.).
- Ensure the output directory `.wiki/` exists at the root of the project workspace.

### 2. Parallel Processing with Subagents
- When processing multiple documents, especially PDFs, images, or large text files, do not process them sequentially in the main conversation.
- Use `invoke_subagent` to spawn concurrent `research` subagents to read and analyze multiple files in parallel.
- For each subagent:
  - Set `TypeName` to `"research"`.
  - Set `Role` to a descriptive role (e.g., `"Document Analyzer - <filename>"`).
  - Set `Prompt` with clear instructions to:
    1. Inspect the target file using `view_file`.
    2. Extract core concepts, structured facts, definitions, diagrams, key takeaways, and relationships.
    3. Return a comprehensive structured Markdown summary formatted for inclusion into the wiki.
- Launch subagents in a single `invoke_subagent` call containing multiple items in the `Subagents` array.
- Collect and synthesize subagent outputs when notifications arrive.

### 3. Structured Markdown Generation
- Convert the extracted information into clean, topic-focused Markdown files placed directly in the flat `.wiki/` directory (e.g., `.wiki/architecture.md`, `.wiki/user-guides.md`, `.wiki/api-spec.md`).
- Ensure consistent page formatting:
  - Page title (`# <Title>`)
  - Executive Overview / Summary
  - Detailed sections with structured headings (`##`, `###`)
  - Cross-references to related topics within `.wiki/` (e.g., `[Topic Name](topic-name.md)`)
  - Source references citing original files

### 4. Master Index Generation (`.wiki/INDEX.md`)
- Create or update the master entry point at `.wiki/INDEX.md`.
- The `INDEX.md` file MUST:
  1. Introduce the knowledge base and describe what information is contained in the wiki.
  2. Provide a structured Table of Contents / Topic Directory linking to all generated wiki pages using relative links (e.g., `- [Architecture Overview](architecture.md) - Summary of system design`).
  3. Include a search and navigation guide for other agents to quickly locate relevant knowledge.
  4. List metadata such as generation timestamp and list of ingested source files.

## Summary Checklist
- [ ] Scan and inventory source files.
- [ ] Concurrently analyze files using `invoke_subagent` with `research` subagents.
- [ ] Generate structured `.md` pages in `.wiki/`.
- [ ] Generate `.wiki/INDEX.md` linking to all created pages.
