---
name: new
description: Use when user asks to create a release, cut a release, or publish a version. Auto-detects GitHub vs GitLab vs Gitea, calculates semantic version, generates release notes from PRs/MRs or commits, shows preview for confirmation before publishing.
allowed-tools: view_file, write_to_file, replace_file_content, find_by_name, grep_search, run_command, invoke_subagent, ask_question
---

# Release Workflow

Creates GitHub, GitLab, or Gitea releases with auto-versioning and release notes generation.

## Activation Triggers

- "create release", "cut release", "new release"
- "publish version", "bump version", "new version"
- "tag and release"

## Scripts

Helper scripts in skill's `scripts/` directory (use `~/.gemini/config/plugins/release-tools` for path resolution):
- `detect-platform.sh` - outputs `github`, `gitlab`, or `gitea`
- `calc-version.sh <type>` - outputs new version (e.g., `v1.2.3`)
- `get-notes.sh <platform>` - outputs release notes (PRs/MRs or commits)

Every helper exits non-zero and prints the reason on stderr. If any of Steps 2, 5 or 6
fails, report that text to the user and **abort the workflow** - do not continue with an
empty value. `get-notes.sh` in particular fails when the forge CLI is missing,
unauthenticated or rate-limited; continuing there publishes a release whose notes list
none of its PRs.

On Gitea, `get-notes.sh` collects no PRs and returns commit-derived notes with a warning
on stderr, because `tea pr list` exposes neither a merged flag nor a merge timestamp. That warning
is not a failure - show it to the user with the preview in Step 8 and carry on.

## Workflow

### Step 1: Ask Release Type

Use ask_question tool to get release type:

```json
{
  "questions": [{
    "question": "What type of release is this?",
    "header": "Version",
    "options": [
      "Hotfix - Bug fixes (1.2.3 → 1.2.4)",
      "Minor - New features (1.2.3 → 1.3.0)",
      "Major - Breaking changes (1.2.3 → 2.0.0)"
    ],
    "is_multi_select": false
  }]
}
```

### Step 2: Detect Platform

```bash
platform=$(bash ~/.gemini/config/plugins/release-tools/skills/new/scripts/detect-platform.sh)
```

### Step 3: Validate Prerequisites

```bash
# working tree must be clean
if [ -n "$(git status --porcelain)" ]; then
    echo "error: uncommitted changes - commit or stash first"
fi

# sync with remote (--tags ensures all remote tags are fetched)
git fetch origin --tags
```

### Step 4: Get Current Version

```bash
last_tag=$(git describe --tags --abbrev=0 --match "v*" 2>/dev/null || echo "none")
```

### Step 5: Calculate New Version

```bash
new_version=$(bash ~/.gemini/config/plugins/release-tools/skills/new/scripts/calc-version.sh <release_type>)
```

Verify tag doesn't already exist:
```bash
if git rev-parse "$new_version" &>/dev/null; then
    echo "error: tag $new_version already exists"
fi
```

### Step 6: Generate Release Notes

```bash
notes=$(bash ~/.gemini/config/plugins/release-tools/skills/new/scripts/get-notes.sh "$platform")
```

Script logic:
1. Collects PRs/MRs merged after last tag (with author)
2. Collects commits since last tag (with hash)
3. Categorizes by conventional commit prefix (feat/fix/refactor/etc.)
4. Groups into: New Features, Improvements, Bug Fixes, Other
5. Strips prefix from description for cleaner output

**Post-processing (Claude must do this before presenting):**
- Deduplicate entries with same description (PRs and their commits often duplicate)
- Prefer PR entries over commit entries when duplicated (PR has #number and @author)
- Compare descriptions after stripping conventional prefix

Output format:
```
**New Features**
- add user authentication #45 @username
- implement caching d41d3ad

**Improvements**
- refactor auth module abc1234
- update dependencies #47 @contributor

**Bug Fixes**
- resolve login timeout #46 @username
- handle nil pointer def5678
```

### Step 7: Check and Update CHANGELOG

```bash
# detect actual changelog filename (case-sensitive filesystem!)
changelog=""
for f in CHANGELOG.md changelog.md CHANGELOG; do
    [ -f "$f" ] && changelog="$f" && break
done
```

If changelog exists:
1. **CRITICAL**: Use the exact detected filename (`$changelog`) for all operations - do not hardcode "CHANGELOG.md"
2. Read the file to understand its format (Keep a Changelog, simple list, etc.)
3. Add new version section at the top (after any header/intro)
4. Use the generated release notes
5. Match the existing format and style
6. Commit the changelog update using the detected filename:
```bash
git add "$changelog"
git commit -m "docs: update changelog for $new_version"
```

Common formats to detect:
- **Keep a Changelog**: Has `## [Unreleased]` section, versions as `## [X.Y.Z] - YYYY-MM-DD`
- **Simple list**: Just version headers like `## X.Y.Z` or `# X.Y.Z`
- **Date-based**: Versions with dates in various formats

### Step 8: Preview and Confirm

Show the release preview to user:

```
=== Release Preview ===
Platform: GitHub/GitLab
Current version: v1.2.3
New version: v1.3.0
Title: Version 1.3.0
CHANGELOG: <detected filename> will be updated (or "none found")

Release Notes:
--------------
**New Features**
- add user authentication #45 @username

**Improvements**
- refactor auth module abc1234

**Bug Fixes**
- resolve login timeout #46 @contributor
--------------
```

Use ask_question tool to confirm:

```json
{
  "questions": [{
    "question": "Proceed with creating this release?",
    "header": "Release",
    "options": [
      "(Recommended) Yes, publish - Create tag and publish release",
      "Cancel - Abort release"
    ],
    "is_multi_select": false
  }]
}
```

**Wait for user confirmation before creating release.**

### Step 9: Create Release

Only after user confirms:

Create an annotated tag locally and push it before calling the forge. Forge release
commands create lightweight tags when the tag is absent; a lightweight tag has no
release time of its own, so the next release would use the target commit's older
committer date as its PR cutoff and re-list already released PRs.

```bash
git tag -a "$new_version" -m "Version ${new_version#v}"
git push origin "$new_version"
```

If either command fails, report the error and abort before creating the release. If the
forge release command below fails after the push, report that the annotated tag already
exists remotely and retry only that release command after the problem is resolved. Do
not recreate or delete the tag.

**GitHub:**
```bash
gh release create "$new_version" \
    --title "Version ${new_version#v}" \
    --notes "$notes"
```

**GitLab:**
```bash
glab release create "$new_version" \
    --name "Version ${new_version#v}" \
    --notes "$notes"
```

**Gitea:**
```bash
tea release create \
    --tag "$new_version" \
    --title "Version ${new_version#v}" \
    --note "$notes"
```

### Step 10: Report Result

After successful creation:
- Show new version
- Show release URL
- Confirm release was published

## Edge Cases

| Case | Handling |
|------|----------|
| No previous tags | Default version based on type |
| Pre-release tag (v1.2.3-rc1) | Strip suffix, use base version |
| No PRs/MRs found | Show commits only (still with hashes) |
| Tag already exists | Error and abort |
| No CHANGELOG file | Skip changelog update |
| Unknown CHANGELOG format | Ask user or use simple `## vX.Y.Z` format |

## Notes

- Tag format: `vX.Y.Z`
- Title format: `Version X.Y.Z`
- Entry format: `- description #123 @author` (PRs) or `- description abc1234` (commits)
- PRs use `#123` (GitHub/Gitea) or `!123` (GitLab)
- Grouped by type: New Features (feat), Improvements (refactor/perf/chore/docs), Bug Fixes (fix), Other
- Conventional commit prefix stripped from description for cleaner output
- Always show preview and get confirmation before publishing
