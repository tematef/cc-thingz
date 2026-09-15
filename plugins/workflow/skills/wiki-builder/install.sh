#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.gemini/config/skills/wiki-builder"

echo "Installing Antigravity wiki-builder skill..."

mkdir -p "${TARGET_DIR}"
cp "${SKILL_DIR}/SKILL.md" "${TARGET_DIR}/SKILL.md"

echo "✅ wiki-builder skill successfully installed to ${TARGET_DIR}"
echo "You can now ask Antigravity to build or update a wiki from source documents!"
