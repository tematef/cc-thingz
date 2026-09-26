#!/bin/bash
# install.sh - Registers local cc-thingz plugins in AGY/Jetski with optional skill filtering

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins"
CONFIG_FILE="$HOME/.gemini/config/plugins.json"
CONFIG_DIR="$(dirname "$CONFIG_FILE")"

usage() {
    cat << 'EOF'
Usage: ./install.sh [OPTIONS]

Options:
  --exclude, -e <skills>   Comma-separated list of skills to disable (moves to .disabled_skills/)
                           Matches skill directory name or 'name:' in SKILL.md.
  --restore, -r [skills]   Restore disabled skills to active state.
                           Use 'all' (default) or comma-separated skill names.
  --list, -l               List all active and disabled skills across all plugins.
  --help, -h               Show this help message.

Examples:
  ./install.sh
  ./install.sh --exclude "wiki-builder,dialectic"
  ./install.sh --restore "wiki-builder,dialectic"
  ./install.sh --restore all
  ./install.sh --list
EOF
}

# Find all active skills (dir_path)
find_active_skills() {
    find "$PLUGIN_DIR" -mindepth 3 -maxdepth 3 -type d 2>/dev/null | while read -r dir; do
        parent="$(basename "$(dirname "$dir")")"
        if [ "$parent" = "skills" ] && [ -f "$dir/SKILL.md" ]; then
            echo "$dir"
        fi
    done
}

# Find all disabled skills (dir_path)
find_disabled_skills() {
    find "$PLUGIN_DIR" -mindepth 3 -maxdepth 3 -type d 2>/dev/null | while read -r dir; do
        parent="$(basename "$(dirname "$dir")")"
        if [ "$parent" = ".disabled_skills" ] && [ -f "$dir/SKILL.md" ]; then
            echo "$dir"
        fi
    done
}

get_skill_name() {
    local dir="$1"
    if [ -f "$dir/SKILL.md" ]; then
        local name
        name="$(grep -E '^name:' "$dir/SKILL.md" | head -n1 | sed -E 's/^name:[[:space:]]*["'"'"']?([^"'"'"']+)["'"'"']?/\1/' | tr -d '\r')"
        if [ -n "$name" ]; then
            echo "$name"
            return
        fi
    fi
    basename "$dir"
}

list_skills() {
    echo "=== cc-thingz Skills Status ==="
    echo ""
    echo "Active Skills:"
    local active_count=0
    while read -r skill_dir; do
        [ -z "$skill_dir" ] && continue
        local sname
        sname="$(get_skill_name "$skill_dir")"
        local sdir
        sdir="$(basename "$skill_dir")"
        local pdir
        pdir="$(basename "$(dirname "$(dirname "$skill_dir")")")"
        echo "  [ACTIVE]   $sname ($pdir/skills/$sdir)"
        active_count=$((active_count + 1))
    done < <(find_active_skills | sort)

    echo ""
    echo "Disabled Skills:"
    local disabled_count=0
    while read -r skill_dir; do
        [ -z "$skill_dir" ] && continue
        local sname
        sname="$(get_skill_name "$skill_dir")"
        local sdir
        sdir="$(basename "$skill_dir")"
        local pdir
        pdir="$(basename "$(dirname "$(dirname "$skill_dir")")")"
        echo "  [DISABLED] $sname ($pdir/.disabled_skills/$sdir)"
        disabled_count=$((disabled_count + 1))
    done < <(find_disabled_skills | sort)

    echo ""
    echo "Total: $active_count active, $disabled_count disabled."
}

disable_skill() {
    local target="$1"
    local found=0

    while read -r skill_dir; do
        [ -z "$skill_dir" ] && continue
        local sname
        sname="$(get_skill_name "$skill_dir")"
        local sdir
        sdir="$(basename "$skill_dir")"
        if [ "$target" = "$sname" ] || [ "$target" = "$sdir" ]; then
            local plugin_dir
            plugin_dir="$(dirname "$(dirname "$skill_dir")")"
            local disabled_dir="$plugin_dir/.disabled_skills"
            mkdir -p "$disabled_dir"
            mv "$skill_dir" "$disabled_dir/$sdir"
            echo "Disabled skill: $sname ($sdir) -> $disabled_dir/$sdir"
            found=1
            break
        fi
    done < <(find_active_skills)

    if [ "$found" -eq 0 ]; then
        # Check if already disabled
        while read -r skill_dir; do
            [ -z "$skill_dir" ] && continue
            local sname
            sname="$(get_skill_name "$skill_dir")"
            local sdir
            sdir="$(basename "$skill_dir")"
            if [ "$target" = "$sname" ] || [ "$target" = "$sdir" ]; then
                echo "Skill already disabled: $sname ($sdir)"
                found=1
                break
            fi
        done < <(find_disabled_skills)
    fi

    if [ "$found" -eq 0 ]; then
        echo "Warning: skill '$target' not found in active or disabled skills."
    fi
}

restore_skill() {
    local target="$1"
    local found=0

    while read -r skill_dir; do
        [ -z "$skill_dir" ] && continue
        local sname
        sname="$(get_skill_name "$skill_dir")"
        local sdir
        sdir="$(basename "$skill_dir")"
        if [ "$target" = "all" ] || [ "$target" = "$sname" ] || [ "$target" = "$sdir" ]; then
            local plugin_dir
            plugin_dir="$(dirname "$(dirname "$skill_dir")")"
            local active_dir="$plugin_dir/skills"
            mkdir -p "$active_dir"
            mv "$skill_dir" "$active_dir/$sdir"
            echo "Restored skill: $sname ($sdir) -> $active_dir/$sdir"
            found=1
            if [ "$target" != "all" ]; then
                break
            fi
        fi
    done < <(find_disabled_skills)

    if [ "$found" -eq 0 ] && [ "$target" != "all" ]; then
        echo "Warning: skill '$target' was not found in disabled skills."
    fi
}

register_plugins() {
    mkdir -p "$CONFIG_DIR"

    if [ ! -f "$CONFIG_FILE" ]; then
        echo '{ "entries": [] }' > "$CONFIG_FILE"
    fi

    if command -v jq >/dev/null 2>&1; then
        # Remove any existing cc-thingz entry (like cc-thingz-master) and add the current PLUGIN_DIR
        jq --arg newpath "$PLUGIN_DIR" '
            .entries = ([.entries[] | select(.path != $newpath and (.path | test("cc-thingz(-master)?/plugins") | not))] + [{"path": $newpath}])
        ' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
    else
        # Fallback if jq is not available
        if grep -q "$PLUGIN_DIR" "$CONFIG_FILE" 2>/dev/null; then
            echo "cc-thingz plugins are already registered in $CONFIG_FILE"
        else
            awk -v path="$PLUGIN_DIR" '
            /\"entries\": \[\s*$/ {
                print $0;
                print "    { \"path\": \"" path "\" },";
                next;
            }
            /\"entries\": \[\s*\]/ {
                sub(/\[\s*\]/, "[\n    { \"path\": \"" path "\" }\n  ]");
                print;
                next;
            }
            {print}
            ' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
        fi
    fi
    mkdir -p "$CONFIG_DIR/plugins"
    for p in "$PLUGIN_DIR"/*; do
        if [ -d "$p" ]; then
            target_link="$CONFIG_DIR/plugins/$(basename "$p")"
            if [ -e "$target_link" ] && [ ! -L "$target_link" ]; then
                echo "Warning: skipping symlink for $(basename "$p") because $target_link exists as a real directory."
            else
                ln -sfn "$p" "$target_link"
            fi
        fi
    done

    # Prune links left behind by plugins removed from this repository
    for link in "$CONFIG_DIR/plugins"/*; do
        [ -L "$link" ] || continue
        [ -e "$link" ] && continue
        case "$(readlink "$link")" in
        "$PLUGIN_DIR"/*)
            rm -f "$link"
            echo "Removed dangling plugin link: $link"
            ;;
        esac
    done

    # The planning plugin's hooks.json registers autonomous-exec-guard. Older installs also
    # wrote a copy into the global hooks.json, and AGY runs both, so every tool call was
    # evaluated twice. Remove that copy; other global hooks are left untouched.
    if [ -f "$CONFIG_DIR/hooks.json" ] && command -v python3 >/dev/null 2>&1; then
        python3 - "$CONFIG_DIR/hooks.json" <<'PY'
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
except Exception as exc:
    print(f"Warning: {path} could not be parsed ({exc}); left unchanged.", file=sys.stderr)
    sys.exit(0)
entry = data.get("autonomous-exec-guard") if isinstance(data, dict) else None
if entry is not None and "autonomous-exec-hook.py" in json.dumps(entry):
    del data["autonomous-exec-guard"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Removed duplicate autonomous-exec-guard from {path} (the planning plugin registers it).")
PY
    fi

    echo "Successfully registered cc-thingz plugins in $CONFIG_FILE and linked them into $CONFIG_DIR/plugins/"
}

# Parse command line options
EXCLUDE_LIST=""
RESTORE_LIST=""
DO_LIST=0

while [ $# -gt 0 ]; do
    case "$1" in
        --exclude|-e)
            if [ -z "${2:-}" ] || [[ "$2" == --* ]]; then
                echo "Error: --exclude requires a comma-separated list of skill names." >&2
                usage
                exit 1
            fi
            EXCLUDE_LIST="$2"
            shift 2
            ;;
        --restore|-r)
            if [ -n "$2" ] && [[ "$2" != --* ]]; then
                RESTORE_LIST="$2"
                shift 2
            else
                RESTORE_LIST="all"
                shift 1
            fi
            ;;
        --list|-l)
            DO_LIST=1
            shift 1
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
done

if [ "$DO_LIST" -eq 1 ]; then
    list_skills
    exit 0
fi

if [ -n "$RESTORE_LIST" ]; then
    IFS=',' read -ra RESTORE_ARRAY <<< "$RESTORE_LIST"
    for item in "${RESTORE_ARRAY[@]}"; do
        item="$(echo "$item" | xargs)"
        [ -z "$item" ] && continue
        restore_skill "$item"
    done
fi

if [ -n "$EXCLUDE_LIST" ]; then
    IFS=',' read -ra EXCLUDE_ARRAY <<< "$EXCLUDE_LIST"
    for item in "${EXCLUDE_ARRAY[@]}"; do
        item="$(echo "$item" | xargs)"
        [ -z "$item" ] && continue
        disable_skill "$item"
    done
fi

register_plugins

echo ""
list_skills
echo ""
echo "AGY/Jetski will now automatically load active skills, rules, and hooks from $PLUGIN_DIR."
