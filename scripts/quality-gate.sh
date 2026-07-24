#!/usr/bin/env sh
# Quality gate dùng chung cho MỌI tool (Claude Code, Antigravity, Codex, Cursor).
#
#   bash scripts/quality-gate.sh            # kiểm working tree so với HEAD
#   bash scripts/quality-gate.sh --staged   # kiểm vùng staged (dùng bởi .githooks/pre-commit)
#
# Xem docs/MULTI_TOOL_WORKFLOW.md §10.

set -u

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "quality-gate: không ở trong git repo." >&2
  exit 1
}
cd "$REPO_ROOT" || exit 1

MODE="worktree"
[ "${1:-}" = "--staged" ] && MODE="staged"

FAILED=0
note()  { printf '  %s\n' "$1"; }
fail()  { printf '\033[31mFAIL\033[0m  %s\n' "$1"; FAILED=1; }
pass()  { printf '\033[32mOK\033[0m    %s\n' "$1"; }
skip()  { printf '\033[33mSKIP\033[0m  %s\n' "$1"; }

# Danh sách file đang thay đổi, tuỳ chế độ.
changed_files() {
  if [ "$MODE" = "staged" ]; then
    git diff --cached --name-only --diff-filter=ACMR
  else
    git diff --name-only --diff-filter=ACMR HEAD 2>/dev/null
    git ls-files --others --exclude-standard
  fi
}

echo "quality-gate (chế độ: $MODE)"
echo "---------------------------------------------"

# ---------------------------------------------------------------------------
# 1. Impeccable detect trên các thư mục có UI
#    CLI này chạy độc lập với provider => áp được cho cả Antigravity.
# ---------------------------------------------------------------------------
UI_DIRS="webapp/frontend slides reports"
UI_PRESENT=""
for d in $UI_DIRS; do
  [ -d "$d" ] && UI_PRESENT="$UI_PRESENT $d"
done

if [ -z "$UI_PRESENT" ]; then
  skip "impeccable detect — chưa có thư mục UI nào ($UI_DIRS)"
elif ! command -v npx >/dev/null 2>&1; then
  fail "impeccable detect — không tìm thấy npx. Cài Node.js hoặc chạy với --no-verify và ghi lý do vào WORKLOG."
else
  mkdir -p .impeccable
  for d in $UI_PRESENT; do
    # --json cho output máy đọc được; giữ lại report để soi khi fail.
    # File này là ephemeral, đã nằm trong .gitignore.
    if npx --yes impeccable detect --json "$d" > ".impeccable/detect-report.json" 2>".impeccable/detect-stderr.log"; then
      pass "impeccable detect $d"
    else
      fail "impeccable detect $d"
      note "report: .impeccable/detect-report.json"
      note "stderr: .impeccable/detect-stderr.log"
      note "sửa bằng /impeccable audit + /impeccable polish (Claude/Codex/Cursor),"
      note "hoặc đọc report và sửa tay (Antigravity)."
    fi
  done
  # LƯU Ý: gate này dựa vào exit code của `detect`. Sau lần chạy thật đầu tiên,
  # hãy xác nhận `detect` có trả exit code khác 0 khi phát hiện lỗi hay không.
  # Nếu nó luôn trả 0, đổi sang đếm trong JSON, ví dụ:
  #   COUNT=$(jq '[.. | .issues? // empty | length] | add // 0' .impeccable/detect-report.json)
  #   [ "${COUNT:-0}" -gt 0 ] && fail "..."
  # Ghi lại kết luận vào WORKLOG khi đã kiểm chứng.
fi

# ---------------------------------------------------------------------------
# 2. splits/ là bất biến (AGENTS.md §3.6, MULTI_TOOL_WORKFLOW §5.4)
#    Sinh lại split làm mất tính so sánh của mọi kết quả CV đã có.
# ---------------------------------------------------------------------------
SPLIT_TOUCHED=$(changed_files | grep '^splits/' || true)
if [ -n "$SPLIT_TOUCHED" ]; then
  if [ "${ALLOW_SPLIT_CHANGE:-0}" = "1" ]; then
    pass "splits/ bị sửa — được cho phép qua ALLOW_SPLIT_CHANGE=1"
  else
    fail "splits/ bị sửa. Đây là dữ liệu đã khoá."
    echo "$SPLIT_TOUCHED" | while read -r f; do note "$f"; done
    note "Nếu thực sự cố ý: hỏi người dùng, ghi WORKLOG, rồi"
    note "  ALLOW_SPLIT_CHANGE=1 git commit ..."
  fi
else
  pass "splits/ không đổi"
fi

# ---------------------------------------------------------------------------
# 3. Không lọt dữ liệu bệnh nhân / checkpoint vào git
# ---------------------------------------------------------------------------
BAD=$(changed_files | grep -Ei '\.(nii|nii\.gz|dcm|dicom|pt|pth|ckpt|h5|npz)$' || true)
if [ -n "$BAD" ]; then
  fail "Có file dữ liệu/checkpoint sắp vào git:"
  echo "$BAD" | while read -r f; do note "$f"; done
  note "Không commit dữ liệu bệnh nhân hay checkpoint (AGENTS.md §3.10)."
else
  pass "không có file dữ liệu/checkpoint"
fi

# ---------------------------------------------------------------------------
# 4. Lint Python — chỉ chạy khi ruff đã có
# ---------------------------------------------------------------------------
if command -v ruff >/dev/null 2>&1 && [ -d src ]; then
  if ruff check src webapp scripts 2>/dev/null; then
    pass "ruff check"
  else
    fail "ruff check"
  fi
else
  skip "ruff — chưa cài hoặc chưa có src/"
fi

echo "---------------------------------------------"
if [ "$FAILED" -eq 0 ]; then
  printf '\033[32mquality-gate: PASS\033[0m\n'
else
  printf '\033[31mquality-gate: FAIL\033[0m\n'
  echo "Bỏ qua có chủ đích: git commit --no-verify  (phải ghi lý do vào WORKLOG.md)"
fi
exit "$FAILED"
