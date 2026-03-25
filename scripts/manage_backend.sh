#!/usr/bin/env bash
set -uo pipefail

# ═══════════════════════════════════════════════════════════════════════
#  ECPM Backend Management TUI
#  Interactive terminal interface for auth, data, training, and more.
# ═══════════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
TOKEN_FILE="$PROJECT_ROOT/.ecpm_token"
API_BASE="${ECPM_API_URL:-http://localhost:8000}"

# ── Terminal state ───────────────────────────────────────────────────

TERM_ROWS=0
TERM_COLS=0
SCROLL_OFFSET=0
OUTPUT_LINES=()
CURRENT_MENU=main
SELECTED=0
AUTH_USER=""
AUTH_EXPIRES=""
HAS_TRAINING_TOKEN=false

# ── Colours ──────────────────────────────────────────────────────────

C_RESET=$'\033[0m'
C_BOLD=$'\033[1m'
C_DIM=$'\033[2m'
C_UNDER=$'\033[4m'
C_RED=$'\033[0;31m'
C_GREEN=$'\033[0;32m'
C_YELLOW=$'\033[1;33m'
C_BLUE=$'\033[0;34m'
C_MAGENTA=$'\033[0;35m'
C_CYAN=$'\033[0;36m'
C_WHITE=$'\033[1;37m'
C_BG_BLUE=$'\033[44m'
C_BG_BLACK=$'\033[40m'
C_BG_GRAY=$'\033[48;5;236m'
C_GRAY=$'\033[38;5;245m'
C_ORANGE=$'\033[38;5;208m'

# Box-drawing
BOX_H="─"
BOX_V="│"
BOX_TL="┌"
BOX_TR="┐"
BOX_BL="└"
BOX_BR="┘"
BOX_T="┬"
BOX_B="┴"
BOX_VR="├"
BOX_VL="┤"

# ── Utilities ────────────────────────────────────────────────────────

load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        set -a
        # shellcheck disable=SC1090
        source "$ENV_FILE" 2>/dev/null || true
        set +a
    fi
}

python_cmd() {
    if command -v python3 &>/dev/null; then echo python3; else echo python; fi
}

get_term_size() {
    TERM_ROWS=$(tput lines 2>/dev/null || echo 24)
    TERM_COLS=$(tput cols 2>/dev/null || echo 80)
}

cursor_to()   { printf '\033[%d;%dH' "$1" "$2"; }
clear_line()  { printf '\033[2K'; }
hide_cursor() { printf '\033[?25l'; }
show_cursor() { printf '\033[?25h'; }
save_screen() { printf '\033[?1049h'; }
restore_screen() { printf '\033[?1049l'; }

TUI_ACTIVE=false

cleanup() {
    if $TUI_ACTIVE; then
        show_cursor
        restore_screen
        stty sane 2>/dev/null
    fi
}
trap cleanup EXIT

# Strip ANSI escape codes for length calculation
strip_ansi() { sed 's/\x1b\[[0-9;]*m//g' <<< "$1"; }

# Draw a horizontal line at row $1, from col $2 to col $3
hline() {
    local row=$1 start=$2 end=$3 ch="${4:-$BOX_H}"
    cursor_to "$row" "$start"
    local i
    for (( i=start; i<=end; i++ )); do printf '%s' "$ch"; done
}

# Print text centered on a row
center_text() {
    local row=$1 text=$2
    local plain
    plain=$(strip_ansi "$text")
    local len=${#plain}
    local col=$(( (TERM_COLS - len) / 2 ))
    (( col < 1 )) && col=1
    cursor_to "$row" "$col"
    printf '%s' "$text"
}

# Print text at position, truncating to max width
print_at() {
    local row=$1 col=$2 max=$3 text=$4
    cursor_to "$row" "$col"
    local plain
    plain=$(strip_ansi "$text")
    if (( ${#plain} > max )); then
        printf '%s' "${text:0:$((max-1))}…"
    else
        printf '%s' "$text"
    fi
}

# ── Auth helpers ─────────────────────────────────────────────────────

resolve_token() {
    if [[ -f "$TOKEN_FILE" ]]; then
        cat "$TOKEN_FILE"
        return
    fi
    load_env
    if [[ -n "${TRAINING_TOKEN:-}" ]]; then
        echo "$TRAINING_TOKEN"
        return
    fi
    echo ""
}

refresh_auth_state() {
    AUTH_USER=""
    AUTH_EXPIRES=""
    HAS_TRAINING_TOKEN=false

    if [[ -f "$TOKEN_FILE" ]]; then
        local token
        token=$(cat "$TOKEN_FILE")
        AUTH_USER=$("$(python_cmd)" -c "
import json, base64, datetime, sys
try:
    parts = '$token'.split('.')
    payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload))
    exp = data.get('exp', 0)
    dt = datetime.datetime.fromtimestamp(exp, tz=datetime.timezone.utc)
    print(data.get('sub', ''), end='')
    print('|' + dt.strftime('%Y-%m-%d %H:%M UTC'), end='')
except: pass
" 2>/dev/null || echo "")
        if [[ "$AUTH_USER" == *"|"* ]]; then
            AUTH_EXPIRES="${AUTH_USER#*|}"
            AUTH_USER="${AUTH_USER%%|*}"
        fi
    fi

    load_env
    [[ -n "${TRAINING_TOKEN:-}" ]] && HAS_TRAINING_TOKEN=true
}

api_call() {
    local method="$1" path="$2"
    shift 2
    local url="${API_BASE}${path}"
    local response http_code body

    response=$(curl -s -m 10 -w "\n%{http_code}" "$@" -X "$method" "$url" 2>&1) || {
        echo "ERROR: Connection failed: $url"
        return 1
    }

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        echo "$body"
        return 0
    else
        echo "ERROR: HTTP $http_code"
        if command -v jq &>/dev/null; then
            echo "$body" | jq -r '.detail // .' 2>/dev/null || echo "$body"
        else
            echo "$body"
        fi
        return 1
    fi
}

api_auth_call() {
    local method="$1" path="$2"
    shift 2
    local token
    token=$(resolve_token)
    if [[ -z "$token" ]]; then
        echo "ERROR: No auth token. Log in first or set a training token."
        return 1
    fi
    api_call "$method" "$path" -H "Authorization: Bearer $token" -H "Accept: application/json" "$@"
}

# ── Menu definitions ─────────────────────────────────────────────────

declare -a MENU_ITEMS=()
declare -a MENU_ACTIONS=()
declare -a MENU_ICONS=()
declare -a MENU_TYPES=()  # "action" | "header" | "separator"

build_main_menu() {
    MENU_ITEMS=()
    MENU_ACTIONS=()
    MENU_ICONS=()
    MENU_TYPES=()

    local i=0
    _add_header() { MENU_ITEMS[i]="$1"; MENU_ACTIONS[i]=""; MENU_ICONS[i]=""; MENU_TYPES[i]="header"; ((i++)); }
    _add_sep()    { MENU_ITEMS[i]=""; MENU_ACTIONS[i]=""; MENU_ICONS[i]=""; MENU_TYPES[i]="separator"; ((i++)); }
    _add_item()   { MENU_ITEMS[i]="$1"; MENU_ACTIONS[i]="$2"; MENU_ICONS[i]="$3"; MENU_TYPES[i]="action"; ((i++)); }

    _add_header "AUTHENTICATION"
    _add_item "Login"                  "do_login"           ">"
    _add_item "Logout"                 "do_logout"          "x"
    _add_item "Who Am I"               "do_whoami"          "?"
    _add_item "Generate Training Token" "do_gen_token"      "+"
    _add_item "Generate Admin Hash"    "do_gen_admin_hash"  "#"

    _add_sep
    _add_header "DATA PIPELINE"
    _add_item "Pipeline Status"        "do_status"          "i"
    _add_item "Trigger Data Fetch"     "do_fetch"           "F"
    _add_item "List Series"            "do_series"          "S"

    _add_sep
    _add_header "MODEL TRAINING"
    _add_item "Trigger Training"       "do_train"           "T"
    _add_item "Latest Training Log"    "do_train_log"       "L"

    _add_sep
    _add_header "FORECASTING RESULTS"
    _add_item "Forecasts"              "do_forecasts"       "f"
    _add_item "Regime Detection"       "do_regime"          "r"
    _add_item "Crisis Index"           "do_crisis"          "c"
    _add_item "Backtests"              "do_backtests"       "b"
    _add_item "Indicators Overview"    "do_indicators"      "I"

    _add_sep
    _add_header "CACHE"
    _add_item "Refresh Cache"          "do_cache_refresh"   "R"
    _add_item "Invalidate Cache"       "do_cache_inv"       "X"

    _add_sep
    _add_header "DOCKER"
    _add_item "Start Services"         "do_docker_up"       "^"
    _add_item "Stop Services"          "do_docker_down"     "v"
    _add_item "View Logs"              "do_docker_logs"     "~"
    _add_item "Restart Backend"        "do_restart_be"      "@"
    _add_item "Health Check"           "do_health"          "h"

    # Ensure SELECTED points at a valid action item
    while (( SELECTED < ${#MENU_TYPES[@]} )) && [[ "${MENU_TYPES[$SELECTED]}" != "action" ]]; do
        ((SELECTED++))
    done
}

# Move selection to next/prev action item
select_next() {
    local n=${#MENU_TYPES[@]}
    local s=$(( SELECTED + 1 ))
    while (( s < n )); do
        [[ "${MENU_TYPES[$s]}" == "action" ]] && { SELECTED=$s; return; }
        ((s++))
    done
}

select_prev() {
    local s=$(( SELECTED - 1 ))
    while (( s >= 0 )); do
        [[ "${MENU_TYPES[$s]}" == "action" ]] && { SELECTED=$s; return; }
        ((s--))
    done
}

# ── Drawing ──────────────────────────────────────────────────────────

MENU_WIDTH=32
OUTPUT_START_COL=0
OUTPUT_WIDTH=0
CONTENT_TOP=4
CONTENT_BOTTOM=0

draw_frame() {
    get_term_size
    OUTPUT_START_COL=$(( MENU_WIDTH + 2 ))
    OUTPUT_WIDTH=$(( TERM_COLS - OUTPUT_START_COL - 1 ))
    CONTENT_BOTTOM=$(( TERM_ROWS - 2 ))
    (( OUTPUT_WIDTH < 20 )) && OUTPUT_WIDTH=20

    printf '\033[2J'

    # ── Title bar ──
    cursor_to 1 1
    printf "${C_BG_BLUE}${C_WHITE}${C_BOLD}"
    printf '%*s' "$TERM_COLS" '' | tr ' ' ' '
    center_text 1 "  ECPM Backend Management  "
    printf "${C_RESET}"

    # ── Auth status bar ──
    cursor_to 2 1
    printf "${C_BG_GRAY}"
    printf '%*s' "$TERM_COLS" ''
    cursor_to 2 2
    if [[ -n "$AUTH_USER" ]]; then
        printf "${C_GREEN}● ${C_WHITE}%s${C_GRAY}  exp %s" "$AUTH_USER" "$AUTH_EXPIRES"
    else
        printf "${C_RED}○ ${C_GRAY}not logged in"
    fi
    if $HAS_TRAINING_TOKEN; then
        printf "  ${C_CYAN}⚷ training-token${C_GRAY}"
    fi
    printf "  ${C_DIM}%s${C_RESET}" "$API_BASE"

    # ── Separator under auth bar ──
    cursor_to 3 1
    printf "${C_DIM}"
    local c
    for (( c=1; c<=TERM_COLS; c++ )); do printf '%s' "$BOX_H"; done
    printf "${C_RESET}"

    # ── Vertical separator between menu and output ──
    local r
    for (( r=CONTENT_TOP; r<=CONTENT_BOTTOM; r++ )); do
        cursor_to "$r" "$((MENU_WIDTH + 1))"
        printf "${C_DIM}%s${C_RESET}" "$BOX_V"
    done

    # ── Bottom bar ──
    cursor_to "$TERM_ROWS" 1
    printf "${C_BG_GRAY}"
    printf '%*s' "$TERM_COLS" ''
    cursor_to "$TERM_ROWS" 2
    printf "${C_WHITE} ↑↓${C_GRAY} navigate  ${C_WHITE}Enter${C_GRAY} run  ${C_WHITE}q${C_GRAY} quit  ${C_WHITE}/${C_GRAY} scroll output  ${C_WHITE}PgUp/PgDn${C_GRAY} scroll"
    printf "${C_RESET}"
}

draw_menu() {
    local n=${#MENU_ITEMS[@]}
    local menu_height=$(( CONTENT_BOTTOM - CONTENT_TOP + 1 ))

    # Calculate scroll window for menu if it's too long
    local menu_scroll_start=0
    if (( n > menu_height )); then
        # Keep selected item visible
        if (( SELECTED > menu_scroll_start + menu_height - 3 )); then
            menu_scroll_start=$(( SELECTED - menu_height + 3 ))
        fi
        if (( menu_scroll_start < 0 )); then menu_scroll_start=0; fi
    fi

    local row=$CONTENT_TOP
    local idx
    for (( idx=menu_scroll_start; idx<n && row<=CONTENT_BOTTOM; idx++ )); do
        cursor_to "$row" 1
        clear_line
        # Redraw vertical separator since clear_line nuked it
        cursor_to "$row" "$((MENU_WIDTH + 1))"
        printf "${C_DIM}%s${C_RESET}" "$BOX_V"
        cursor_to "$row" 1

        local type="${MENU_TYPES[$idx]}"
        local item="${MENU_ITEMS[$idx]}"

        case "$type" in
            header)
                printf "  ${C_CYAN}${C_BOLD}%s${C_RESET}" "$item"
                ;;
            separator)
                printf "  ${C_DIM}"
                local s; for (( s=0; s<MENU_WIDTH-3; s++ )); do printf '%s' "·"; done
                printf "${C_RESET}"
                ;;
            action)
                local icon="${MENU_ICONS[$idx]}"
                if (( idx == SELECTED )); then
                    printf "${C_BG_BLUE}${C_WHITE}${C_BOLD}"
                    printf " %s %-*s" "$icon" $(( MENU_WIDTH - 4 )) "$item"
                    printf "${C_RESET}"
                else
                    printf "  ${C_GRAY}%s${C_RESET} %-*s" "$icon" $(( MENU_WIDTH - 5 )) "$item"
                fi
                ;;
        esac

        ((row++))
    done

    # Clear remaining menu rows
    while (( row <= CONTENT_BOTTOM )); do
        cursor_to "$row" 1
        printf '%*s' "$MENU_WIDTH" ''
        cursor_to "$row" "$((MENU_WIDTH + 1))"
        printf "${C_DIM}%s${C_RESET}" "$BOX_V"
        ((row++))
    done
}

draw_output() {
    local total=${#OUTPUT_LINES[@]}
    local visible_height=$(( CONTENT_BOTTOM - CONTENT_TOP + 1 ))

    # Clamp scroll offset
    local max_scroll=$(( total - visible_height ))
    (( max_scroll < 0 )) && max_scroll=0
    (( SCROLL_OFFSET > max_scroll )) && SCROLL_OFFSET=$max_scroll
    (( SCROLL_OFFSET < 0 )) && SCROLL_OFFSET=0

    local row=$CONTENT_TOP
    local line_idx=$SCROLL_OFFSET
    local max_w=$(( OUTPUT_WIDTH - 1 ))

    while (( row <= CONTENT_BOTTOM )); do
        cursor_to "$row" "$OUTPUT_START_COL"
        printf '%*s' "$OUTPUT_WIDTH" ''
        cursor_to "$row" "$OUTPUT_START_COL"

        if (( line_idx < total )); then
            local line="${OUTPUT_LINES[$line_idx]}"
            local plain
            plain=$(strip_ansi "$line")
            if (( ${#plain} > max_w )); then
                # Truncate (naively; good enough for most lines)
                printf ' %s' "${line:0:$((max_w))}"
            else
                printf ' %s' "$line"
            fi
        fi

        ((row++))
        ((line_idx++))
    done

    # Scroll indicator
    if (( total > visible_height )); then
        local pct=$(( (SCROLL_OFFSET * 100) / (max_scroll > 0 ? max_scroll : 1) ))
        cursor_to "$CONTENT_TOP" "$(( TERM_COLS ))"
        printf "${C_DIM}▲${C_RESET}"
        cursor_to "$CONTENT_BOTTOM" "$(( TERM_COLS ))"
        printf "${C_DIM}▼${C_RESET}"
        # Thumb position
        local thumb_row=$(( CONTENT_TOP + 1 + (pct * (visible_height - 3)) / 100 ))
        cursor_to "$thumb_row" "$(( TERM_COLS ))"
        printf "${C_CYAN}█${C_RESET}"
    fi
}

set_output() {
    OUTPUT_LINES=()
    SCROLL_OFFSET=0
    local line
    while IFS= read -r line; do
        OUTPUT_LINES+=("$line")
    done <<< "$1"
    draw_output
}

set_output_running() {
    set_output "${C_YELLOW}⏳ Running: $1...${C_RESET}"
    draw_output
}

# ── Interactive input (drawn inside the output pane) ─────────────────

tui_read() {
    local prompt="$1" default="${2:-}" is_secret="${3:-false}"
    show_cursor

    local total=${#OUTPUT_LINES[@]}
    OUTPUT_LINES+=("${C_CYAN}${prompt}${C_RESET}")
    draw_output

    local input_row=$(( CONTENT_TOP + total ))
    (( input_row > CONTENT_BOTTOM )) && input_row=$CONTENT_BOTTOM
    local input_col=$(( OUTPUT_START_COL + 1 + ${#prompt} + 1 ))

    # Strip ANSI from prompt for accurate col calc
    local plain_prompt
    plain_prompt=$(strip_ansi "$prompt")
    input_col=$(( OUTPUT_START_COL + 1 + ${#plain_prompt} ))

    cursor_to "$input_row" "$input_col"

    local value=""
    if [[ "$is_secret" == "true" ]]; then
        read -rs value
    else
        if [[ -n "$default" ]]; then
            read -r -e -i "$default" value
        else
            read -r value
        fi
    fi
    [[ -z "$value" && -n "$default" ]] && value="$default"

    hide_cursor
    if [[ "$is_secret" == "true" ]]; then
        OUTPUT_LINES+=("${C_DIM}  (hidden)${C_RESET}")
    else
        OUTPUT_LINES+=("  ${value}")
    fi
    echo "$value"
}

tui_confirm() {
    local prompt="$1"
    local result
    result=$(tui_read "$prompt [y/N]: " "" false)
    [[ "${result,,}" == "y" || "${result,,}" == "yes" ]]
}

# ── Actions ──────────────────────────────────────────────────────────

do_login() {
    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}${C_CYAN}Login to ECPM${C_RESET}")
    OUTPUT_LINES+=("")
    draw_output

    local username
    username=$(tui_read "Username: " "admin" false)
    local password
    password=$(tui_read "Password: " "" true)

    if [[ -z "$password" ]]; then
        OUTPUT_LINES+=("")
        OUTPUT_LINES+=("${C_RED}✗ Password cannot be empty.${C_RESET}")
        draw_output
        return
    fi

    OUTPUT_LINES+=("")
    OUTPUT_LINES+=("${C_YELLOW}⏳ Authenticating as ${username}...${C_RESET}")
    draw_output

    local body
    body=$(api_call POST /api/auth/token \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${username}&password=${password}" 2>&1) || true

    if [[ "$body" == ERROR:* ]]; then
        OUTPUT_LINES+=("${C_RED}✗ ${body}${C_RESET}")
        draw_output
        return
    fi

    local access_token=""
    if command -v jq &>/dev/null; then
        access_token=$(echo "$body" | jq -r '.access_token // empty' 2>/dev/null)
    else
        access_token=$(echo "$body" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    fi

    if [[ -z "$access_token" ]]; then
        OUTPUT_LINES+=("${C_RED}✗ Login failed.${C_RESET}")
        if command -v jq &>/dev/null; then
            local detail
            detail=$(echo "$body" | jq -r '.detail // empty' 2>/dev/null)
            [[ -n "$detail" ]] && OUTPUT_LINES+=("  ${detail}")
        fi
        draw_output
        return
    fi

    echo -n "$access_token" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
    refresh_auth_state
    draw_frame
    draw_menu

    OUTPUT_LINES+=("${C_GREEN}✓ Logged in as ${username}.${C_RESET}")
    OUTPUT_LINES+=("${C_DIM}  Token: ${access_token:0:24}...${C_RESET}")
    draw_output
}

do_logout() {
    if [[ -f "$TOKEN_FILE" ]]; then
        rm -f "$TOKEN_FILE"
        refresh_auth_state
        draw_frame
        draw_menu
        set_output "${C_GREEN}✓ Token removed. Logged out.${C_RESET}"
    else
        set_output "${C_DIM}No saved token to remove.${C_RESET}"
    fi
}

do_whoami() {
    refresh_auth_state
    local lines=""
    lines+="${C_BOLD}Authentication State${C_RESET}\n\n"

    if [[ -n "$AUTH_USER" ]]; then
        lines+="${C_GREEN}●${C_RESET} JWT user: ${C_WHITE}${AUTH_USER}${C_RESET}\n"
        lines+="  Expires: ${AUTH_EXPIRES}\n"
    else
        lines+="${C_RED}○${C_RESET} No JWT token saved.\n"
    fi

    lines+="\n"
    if $HAS_TRAINING_TOKEN; then
        lines+="${C_CYAN}⚷${C_RESET} Training token: ${C_GREEN}configured${C_RESET}\n"
    else
        lines+="${C_DIM}⚷ No TRAINING_TOKEN in .env${C_RESET}\n"
    fi

    lines+="\n${C_DIM}API: ${API_BASE}${C_RESET}\n"
    set_output "$(echo -e "$lines")"
}

do_gen_token() {
    local token
    token=$("$(python_cmd)" -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null)

    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}Generated Training Token${C_RESET}")
    OUTPUT_LINES+=("")
    OUTPUT_LINES+=("${C_WHITE}${token}${C_RESET}")
    OUTPUT_LINES+=("")
    draw_output

    if tui_confirm "Write to .env?"; then
        if grep -q '^TRAINING_TOKEN=' "$ENV_FILE" 2>/dev/null; then
            sed -i "s|^TRAINING_TOKEN=.*|TRAINING_TOKEN=$token|" "$ENV_FILE"
        else
            echo "TRAINING_TOKEN=$token" >> "$ENV_FILE"
        fi
        refresh_auth_state
        draw_frame
        draw_menu
        OUTPUT_LINES+=("")
        OUTPUT_LINES+=("${C_GREEN}✓ Written to .env${C_RESET}")
        OUTPUT_LINES+=("${C_YELLOW}  Restart the backend to pick it up.${C_RESET}")
    else
        OUTPUT_LINES+=("")
        OUTPUT_LINES+=("${C_DIM}Not written. Copy the token above manually.${C_RESET}")
    fi
    draw_output
}

do_gen_admin_hash() {
    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}Generate Admin Password Hash${C_RESET}")
    OUTPUT_LINES+=("")
    draw_output

    local password
    password=$(tui_read "New admin password: " "" true)
    local confirm
    confirm=$(tui_read "Confirm password:   " "" true)

    if [[ "$password" != "$confirm" ]]; then
        OUTPUT_LINES+=("")
        OUTPUT_LINES+=("${C_RED}✗ Passwords do not match.${C_RESET}")
        draw_output
        return
    fi

    if (( ${#password} < 12 )); then
        OUTPUT_LINES+=("${C_YELLOW}⚠ Warning: password shorter than 12 chars.${C_RESET}")
    fi

    local hash
    hash=$("$(python_cmd)" -c "
import bcrypt, sys
h = bcrypt.hashpw('''${password}'''.encode(), bcrypt.gensalt()).decode()
print(h)
" 2>/dev/null)

    if [[ -z "$hash" ]]; then
        OUTPUT_LINES+=("${C_RED}✗ Failed to generate hash. Is bcrypt installed?${C_RESET}")
        draw_output
        return
    fi

    OUTPUT_LINES+=("")
    OUTPUT_LINES+=("${C_GREEN}✓ Hash generated:${C_RESET}")
    OUTPUT_LINES+=("  ${C_DIM}${hash}${C_RESET}")
    OUTPUT_LINES+=("")
    draw_output

    if tui_confirm "Write ADMIN_PASSWORD_HASH to .env?"; then
        if grep -q '^ADMIN_PASSWORD_HASH=' "$ENV_FILE" 2>/dev/null; then
            sed -i "s|^ADMIN_PASSWORD_HASH=.*|ADMIN_PASSWORD_HASH='$hash'|" "$ENV_FILE"
        else
            echo "ADMIN_PASSWORD_HASH='$hash'" >> "$ENV_FILE"
        fi
        OUTPUT_LINES+=("${C_GREEN}✓ Written to .env${C_RESET}")
    else
        OUTPUT_LINES+=("${C_DIM}Add to .env manually:${C_RESET}")
        OUTPUT_LINES+=("  ADMIN_PASSWORD_HASH='${hash}'")
    fi
    draw_output
}

run_api_action() {
    local label="$1" method="$2" path="$3" auth="${4:-false}"
    shift 3; shift || true

    set_output_running "$label"

    local body
    if [[ "$auth" == "true" ]]; then
        body=$(api_auth_call "$method" "$path" "$@" 2>&1) || true
    else
        body=$(api_call "$method" "$path" -H "Accept: application/json" "$@" 2>&1) || true
    fi

    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}${label}${C_RESET}")
    OUTPUT_LINES+=("")

    if [[ "$body" == ERROR:* ]]; then
        OUTPUT_LINES+=("${C_RED}✗ ${body}${C_RESET}")
    elif command -v jq &>/dev/null; then
        local formatted
        formatted=$(echo "$body" | jq -C '.' 2>/dev/null || echo "$body")
        while IFS= read -r line; do
            OUTPUT_LINES+=("$line")
        done <<< "$formatted"
    else
        while IFS= read -r line; do
            OUTPUT_LINES+=("$line")
        done <<< "$body"
    fi
    SCROLL_OFFSET=0
    draw_output
}

do_health()        { run_api_action "Health Check" GET /health false; }
do_status()        { run_api_action "Pipeline Status" GET /api/data/status false; }
do_fetch()         { run_api_action "Trigger Data Fetch" POST /api/data/fetch true; }
do_train()         { run_api_action "Trigger Model Training" POST /api/forecasting/train true; }
do_forecasts()     { run_api_action "Forecasts" GET /api/forecasting/forecasts false; }
do_regime()        { run_api_action "Regime Detection" GET /api/forecasting/regime false; }
do_crisis()        { run_api_action "Crisis Index" GET /api/forecasting/crisis-index false; }
do_backtests()     { run_api_action "Backtests" GET /api/forecasting/backtests false; }
do_indicators()    { run_api_action "Indicators Overview" GET "/api/indicators/?methodology=shaikh-tonak" false; }
do_cache_refresh() { run_api_action "Cache Refresh" POST /api/cache/refresh true; }
do_cache_inv()     { run_api_action "Cache Invalidate" POST /api/cache/invalidate true; }

do_series() {
    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}List Series${C_RESET}")
    OUTPUT_LINES+=("")
    draw_output

    local source
    source=$(tui_read "Filter by source (FRED/BEA, blank=all): " "" false)
    local params=""
    [[ -n "$source" ]] && params="?source=${source^^}"

    run_api_action "Series${source:+ (${source^^})}" GET "/api/data/series${params}" false
}

do_train_log() {
    set_output_running "Latest Training Log"

    local body
    body=$(api_call GET /api/forecasting/training/log -H "Accept: application/json" 2>&1) || true

    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}Latest Training Log${C_RESET}")
    OUTPUT_LINES+=("")

    if [[ "$body" == ERROR:* ]]; then
        OUTPUT_LINES+=("${C_RED}✗ ${body}${C_RESET}")
        draw_output
        return
    fi

    if ! command -v jq &>/dev/null; then
        while IFS= read -r line; do OUTPUT_LINES+=("$line"); done <<< "$body"
        draw_output
        return
    fi

    local count
    count=$(echo "$body" | jq -r '.count' 2>/dev/null)
    if [[ "$count" == "0" || -z "$count" ]]; then
        OUTPUT_LINES+=("${C_DIM}No training log available.${C_RESET}")
        OUTPUT_LINES+=("${C_DIM}Training is triggered via the API.${C_RESET}")
        draw_output
        return
    fi

    # Parse entries into formatted lines
    while IFS= read -r entry; do
        local ts name status detail error duration_ms
        ts=$(echo "$entry" | jq -r '.timestamp // ""' 2>/dev/null)
        name=$(echo "$entry" | jq -r '.name // ""' 2>/dev/null)
        status=$(echo "$entry" | jq -r '.status // ""' 2>/dev/null)
        detail=$(echo "$entry" | jq -r '.detail // empty' 2>/dev/null)
        error=$(echo "$entry" | jq -r '.error // empty' 2>/dev/null)
        duration_ms=$(echo "$entry" | jq -r '.duration_ms // empty' 2>/dev/null)

        # Format timestamp
        ts="${ts%%.*}"
        ts="${ts/T/ }"

        # Status colour
        local sc="$C_CYAN"
        case "$status" in
            complete) sc="$C_GREEN" ;;
            error)    sc="$C_RED" ;;
            running)  sc="$C_YELLOW" ;;
        esac

        local msg="${detail:-${error:-${status}}}"
        local dur=""
        if [[ -n "$duration_ms" ]]; then
            dur=$(echo "$duration_ms" | awk '{printf " (%.1fs)", $1/1000}')
        fi

        OUTPUT_LINES+=("${C_DIM}${ts}${C_RESET}  ${sc}${status}${C_RESET}  [${name}]  ${msg}${C_DIM}${dur}${C_RESET}")
    done < <(echo "$body" | jq -c '.entries[]' 2>/dev/null)

    SCROLL_OFFSET=0
    draw_output
}

do_docker_up() {
    set_output_running "Starting services"
    local out
    out=$(cd "$PROJECT_ROOT" && docker compose up -d 2>&1) || true
    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}Docker Compose Up${C_RESET}")
    OUTPUT_LINES+=("")
    while IFS= read -r line; do OUTPUT_LINES+=("$line"); done <<< "$out"
    OUTPUT_LINES+=("")
    OUTPUT_LINES+=("${C_GREEN}✓ Done${C_RESET}")
    draw_output
}

do_docker_down() {
    set_output_running "Stopping services"
    local out
    out=$(cd "$PROJECT_ROOT" && docker compose down 2>&1) || true
    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}Docker Compose Down${C_RESET}")
    OUTPUT_LINES+=("")
    while IFS= read -r line; do OUTPUT_LINES+=("$line"); done <<< "$out"
    OUTPUT_LINES+=("")
    OUTPUT_LINES+=("${C_GREEN}✓ Done${C_RESET}")
    draw_output
}

do_docker_logs() {
    # Temporarily leave TUI to show scrolling logs
    show_cursor
    restore_screen
    stty sane 2>/dev/null
    printf "${C_DIM}(Press Ctrl+C to return to TUI)${C_RESET}\n\n"
    (cd "$PROJECT_ROOT" && docker compose logs -f --tail=80) || true
    # Re-enter TUI
    TUI_ACTIVE=true
    save_screen
    hide_cursor
    stty raw -echo 2>/dev/null
    draw_frame
    draw_menu
    set_output "${C_DIM}Returned from log viewer.${C_RESET}"
}

do_restart_be() {
    set_output_running "Restarting backend"
    local out
    out=$(cd "$PROJECT_ROOT" && docker compose restart backend 2>&1) || true
    OUTPUT_LINES=()
    OUTPUT_LINES+=("${C_BOLD}Restart Backend${C_RESET}")
    OUTPUT_LINES+=("")
    while IFS= read -r line; do OUTPUT_LINES+=("$line"); done <<< "$out"
    OUTPUT_LINES+=("")
    OUTPUT_LINES+=("${C_GREEN}✓ Backend restarted.${C_RESET}")
    draw_output
}

# ── Input loop ───────────────────────────────────────────────────────

read_key() {
    local key
    IFS= read -rsn1 key 2>/dev/null || return 1
    # Escape sequence
    if [[ "$key" == $'\033' ]]; then
        local seq
        IFS= read -rsn1 -t 0.05 seq 2>/dev/null || { echo "ESC"; return; }
        if [[ "$seq" == "[" ]]; then
            IFS= read -rsn1 seq 2>/dev/null
            case "$seq" in
                A) echo "UP" ;;
                B) echo "DOWN" ;;
                C) echo "RIGHT" ;;
                D) echo "LEFT" ;;
                5) IFS= read -rsn1 _ 2>/dev/null; echo "PGUP" ;;
                6) IFS= read -rsn1 _ 2>/dev/null; echo "PGDN" ;;
                H) echo "HOME" ;;
                F) echo "END" ;;
                *) echo "OTHER" ;;
            esac
        else
            echo "ESC"
        fi
    elif [[ "$key" == "" ]]; then
        echo "ENTER"
    elif [[ "$key" == $'\177' || "$key" == $'\b' ]]; then
        echo "BACKSPACE"
    else
        echo "$key"
    fi
}

main_loop() {
    while true; do
        local key
        key=$(read_key) || continue

        case "$key" in
            UP|k)
                select_prev
                draw_menu
                ;;
            DOWN|j)
                select_next
                draw_menu
                ;;
            ENTER)
                local action="${MENU_ACTIONS[$SELECTED]}"
                if [[ -n "$action" ]]; then
                    "$action"
                fi
                ;;
            PGUP)
                (( SCROLL_OFFSET -= 10 ))
                (( SCROLL_OFFSET < 0 )) && SCROLL_OFFSET=0
                draw_output
                ;;
            PGDN)
                (( SCROLL_OFFSET += 10 ))
                draw_output
                ;;
            HOME)
                SCROLL_OFFSET=0
                draw_output
                ;;
            END)
                SCROLL_OFFSET=999999
                draw_output
                ;;
            q|Q)
                return 0
                ;;
            ESC)
                # Reset output
                set_output ""
                ;;
            # Vim-style half-page scroll
            d)
                (( SCROLL_OFFSET += 5 ))
                draw_output
                ;;
            u)
                (( SCROLL_OFFSET -= 5 ))
                (( SCROLL_OFFSET < 0 )) && SCROLL_OFFSET=0
                draw_output
                ;;
        esac
    done
}

# ── Entrypoint ───────────────────────────────────────────────────────

main() {
    # If arguments passed, run in CLI mode for scripting
    if (( $# > 0 )); then
        exec_cli "$@"
        return
    fi

    # Preflight
    command -v curl &>/dev/null || { echo "Error: curl required."; exit 1; }

    load_env
    refresh_auth_state
    build_main_menu

    TUI_ACTIVE=true
    save_screen
    hide_cursor
    stty raw -echo 2>/dev/null

    draw_frame
    draw_menu
    set_output "$(echo -e "${C_BOLD}Welcome to ECPM${C_RESET}\n\n${C_DIM}Select an action from the menu.\nUse ↑↓ or j/k to navigate, Enter to run.\n\nOutput will appear here.\n\nPress q to quit.${C_RESET}")"

    main_loop
}

# ── CLI fallback (for scripting: ./manage_backend.sh train) ──────────

exec_cli() {
    local cmd="$1"; shift || true
    load_env

    case "$cmd" in
        login)              do_cli_login ;;
        logout)             [[ -f "$TOKEN_FILE" ]] && rm -f "$TOKEN_FILE" && echo "Logged out." || echo "No token." ;;
        whoami)             refresh_auth_state; echo "User: ${AUTH_USER:-none}  Expires: ${AUTH_EXPIRES:-n/a}  Training token: $HAS_TRAINING_TOKEN" ;;
        generate-token)     "$(python_cmd)" -c "import secrets; print(secrets.token_urlsafe(48))" ;;
        health)             api_call GET /health -H "Accept: application/json" ;;
        status)             api_call GET /api/data/status -H "Accept: application/json" ;;
        fetch)              api_auth_call POST /api/data/fetch ;;
        train)              api_auth_call POST /api/forecasting/train ;;
        train-log)          api_call GET /api/forecasting/training/log -H "Accept: application/json" ;;
        train-status)       api_auth_call GET "/api/forecasting/train/$1" ;;
        forecasts)          api_call GET "/api/forecasting/forecasts${1:+?indicator=$1}" -H "Accept: application/json" ;;
        regime)             api_call GET /api/forecasting/regime -H "Accept: application/json" ;;
        crisis-index)       api_call GET /api/forecasting/crisis-index -H "Accept: application/json" ;;
        backtests)          api_call GET /api/forecasting/backtests -H "Accept: application/json" ;;
        indicators)         api_call GET "/api/indicators/?methodology=${1:-shaikh-tonak}" -H "Accept: application/json" ;;
        series)             api_call GET "/api/data/series${1:+?source=$1}" -H "Accept: application/json" ;;
        cache-refresh)      api_auth_call POST /api/cache/refresh ;;
        cache-invalidate)   api_auth_call POST /api/cache/invalidate ;;
        up)                 cd "$PROJECT_ROOT" && docker compose up -d ;;
        down)               cd "$PROJECT_ROOT" && docker compose down ;;
        logs)               cd "$PROJECT_ROOT" && docker compose logs -f --tail=100 ${1:-} ;;
        restart)            cd "$PROJECT_ROOT" && docker compose restart "${1:-backend}" ;;
        *)                  echo "Unknown command: $cmd"; exit 1 ;;
    esac
}

do_cli_login() {
    local username password
    read -rp "Username [admin]: " username; username="${username:-admin}"
    read -rsp "Password: " password; echo
    local body
    body=$(api_call POST /api/auth/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=${username}&password=${password}") || exit 1
    local token
    token=$(echo "$body" | jq -r '.access_token // empty' 2>/dev/null || echo "")
    [[ -z "$token" ]] && { echo "Login failed."; exit 1; }
    echo -n "$token" > "$TOKEN_FILE"; chmod 600 "$TOKEN_FILE"
    echo "Logged in. Token saved."
}

main "$@"
