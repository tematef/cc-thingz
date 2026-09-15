# Wiki Builder Skill for Antigravity

A global Antigravity skill that ingests raw data files (PDFs, Markdown, Images, text documents), processes them concurrently using research subagents, and compiles them into a structured, indexed Markdown knowledge base in a flat `.wiki/` directory with a master `INDEX.md`.

## Features

- **Multi-Format Ingestion**: Scans and parses diverse raw documentation and assets, including Markdown files, PDFs, images (diagrams, architecture charts), and plain text.
- **Concurrent Subagent Processing**: Leverages Antigravity's `invoke_subagent` tool to spawn parallel `research` subagents for reading and analyzing multiple files simultaneously.
- **Structured Knowledge Base**: Normalizes extracted content into clean, focused Markdown files in a flat `.wiki/` directory.
- **Master Index Generation**: Produces a comprehensive `.wiki/INDEX.md` that serves as the entry point and table of contents for both human developers and other AI agents.

## Installation

### Automated Installation

Run the provided installation script from the project root:

```bash
./contrib/antigravity/skills/wiki-builder/install.sh
```

Or execute it directly from the skill directory:

```bash
cd contrib/antigravity/skills/wiki-builder
./install.sh
```

### Manual Installation

Copy the `SKILL.md` file to your Antigravity global skills directory:

```bash
mkdir -p ~/.gemini/config/skills/wiki-builder
cp contrib/antigravity/skills/wiki-builder/SKILL.md ~/.gemini/config/skills/wiki-builder/SKILL.md
```

## How to Use

Once installed, the `wiki-builder` skill is automatically available in your Antigravity sessions. You can ask Antigravity to build or update a wiki using natural language prompts.

### Example Prompts

- *"Build a wiki from the raw documentation and design files in `./docs`."*
- *"Ingest all PDFs and architecture diagrams in `./resources` into `.wiki/` and generate a master index."*
- *"Scan this project's documentation, convert the contents into structured markdown in `.wiki/`, and create `INDEX.md`."*

## Output Structure

The skill generates knowledge base files in the project's `.wiki/` folder:

```text
.wiki/
├── INDEX.md              # Master entry point, table of contents, and search guide
├── architecture.md       # Extracted architectural overview and system diagrams
├── api-reference.md      # API endpoints, specifications, and interfaces
└── user-guides.md        # Workflows, tutorials, and setup instructions
```
