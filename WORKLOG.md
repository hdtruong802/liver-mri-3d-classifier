# WORKLOG — Nhật ký bàn giao giữa các tool

> **Mục đích:** mở bất kỳ tool nào (Claude Code / Antigravity / Codex / Cursor), đọc **entry cuối cùng** là biết ngay tiếp tục từ đâu.
> Ngữ cảnh dự án **không** nằm ở đây — nó ở [`AGENTS.md`](AGENTS.md). File này chỉ ghi *chuyện gì đã xảy ra*.

---

## Luật của file này

1. **Append-only.** Chỉ thêm entry vào **cuối file**. Không sửa, không xoá, không sắp xếp lại entry cũ. Sai thì viết entry mới đính chính, không tẩy vết.
2. **Một entry = một phiên làm việc** của một tool. Đổi tool = phiên mới.
3. **Mã phiên `S-NNN` tăng dần**, không tái sử dụng. Lấy số của entry cuối + 1.
4. **Timestamp là giờ địa phương +07**, định dạng `YYYY-MM-DD HH:MM`.
5. **Trường `Điểm vào phiên sau` không được để trống.** Nếu thật sự xong sạch thì viết `Không có việc treo. Bước kế tiếp đề xuất: ...`. Đây là trường quan trọng nhất của cả file.
6. **Commit entry cùng với việc đã làm**, trong cùng một commit hoặc commit ngay sau. Không để WORKLOG trôi ngoài git khi rời tool.

### Bắt buộc ghi entry khi

- Kết thúc phiên / chuẩn bị đổi sang tool khác — **luôn luôn**, kể cả phiên ngắn.
- Có quyết định kiến trúc, quyết định khoa học, hoặc từ bỏ một hướng.
- Chạy một thí nghiệm train và có số ra (ghi kèm config + kết quả tóm tắt).
- Sửa `AGENTS.md`, `.gitignore`, cấu trúc thư mục, hoặc bất kỳ file ngữ cảnh nào.
- Để lại việc dang dở, code chưa chạy được, hoặc một cái bẫy mà tool sau dễ dẫm phải.
- Chạm vào test-104 (và phải xin phép người dùng trước — xem AGENTS.md §10).

### Không cần ghi entry khi

- Chỉ đọc code / hỏi đáp, không sửa file nào.
- Sửa typo lặt vặt không đổi hành vi.

### Khi bị conflict git ở file này

Chỉ có thể xảy ra nếu hai tool cùng append mà quên pull. **Cách xử lý duy nhất: giữ CẢ HAI entry**, sắp lại theo timestamp, đánh lại `S-NNN` cho entry sau. Không bao giờ chọn một bên và bỏ bên kia.

---

## Template (copy nguyên khối này)

```markdown
## S-NNN · YYYY-MM-DD HH:MM · <claude-code | antigravity | codex | cursor>

**Mục tiêu phiên:** <một câu, cái bạn định làm khi bắt đầu>

**Nhánh / commit:** `<branch>` · `<sha đầu>` → `<sha cuối>`

**Đã đụng file:**
- `path/to/file` — <làm gì với nó>

**Quyết định & lý do:**
- <quyết định> — vì <lý do>. Phương án đã loại: <gì, vì sao>.

**Kết quả / số liệu:** <bảng hoặc dòng ngắn; hoặc "không có">

**Dang dở:**
- [ ] <việc chưa xong, nêu rõ đang kẹt ở đâu>

**Điểm vào phiên sau:** <bước cụ thể tiếp theo — file nào, hàm nào, lệnh nào>

**Cảnh báo cho tool sau:** <bẫy, giả định mong manh, thứ dễ hiểu nhầm; hoặc "không có">
```

---

## Ví dụ

<details>
<summary>Hai entry mẫu (không phải log thật) — bấm để xem</summary>

```markdown
## S-014 · 2026-08-03 21:40 · codex

**Mục tiêu phiên:** Sinh split 5-fold stratified ở mức bệnh nhân và khoá lại thành file.

**Nhánh / commit:** `feat/splits` · `3f9a1c2` → `b7e04d8`

**Đã đụng file:**
- `src/data/make_splits.py` — mới; StratifiedGroupKFold theo `patient_id`, seed 42.
- `splits/fold_{0..4}.json` — output đã commit.
- `tests/test_splits.py` — assert giao tập patient_id giữa các fold = rỗng.
- `AGENTS.md` — cập nhật §6, đánh dấu lệnh sinh split đã có.

**Quyết định & lý do:**
- Dùng `StratifiedGroupKFold` thay vì `StratifiedKFold` — vì tuy LLD-MMRI mỗi bệnh nhân chỉ 1 tổn thương,
  giữ group theo patient_id để pipeline không hỏng nếu sau này thêm dataset external nhiều tổn thương/bn.
- Commit file split vào git thay vì sinh runtime — bắt buộc theo AGENTS.md §3.6, và để Kaggle notebook
  không phụ thuộc scikit-learn version.

**Kết quả / số liệu:** phân bố lớp lệch ≤2 ca giữa các fold ở mọi lớp; áp-xe chỉ 4–5 ca/fold (đã lường trước).

**Dang dở:**
- [ ] Chưa xử lý 3 bệnh nhân thiếu thì DWI — hiện đang bị loại khỏi split.

**Điểm vào phiên sau:** quyết định xử lý 3 ca thiếu DWI ở `src/data/make_splits.py:71` —
loại hẳn hay cho phép phase-masking. Nghiêng về phase-masking vì web app sẽ gặp ca thiếu pha.

**Cảnh báo cho tool sau:** `splits/` là dữ liệu đã khoá. Đừng chạy lại `make_splits` rồi commit đè —
mọi kết quả CV trước đó sẽ mất tính so sánh. Muốn đổi split phải ghi entry riêng và nêu lý do.


## S-015 · 2026-08-04 09:05 · antigravity

**Mục tiêu phiên:** Dựng khung FastAPI cho web app demo (chưa nối model thật).

**Nhánh / commit:** `feat/webapp-skeleton` · `b7e04d8` → `c1a5f30`

**Đã đụng file:**
- `webapp/backend/main.py` — app + `/health` + `/predict` trả payload giả đúng schema trong plan §8.1.
- `webapp/backend/requirements.txt` — mới, tách khỏi requirements train.
- `webapp/frontend/index.html`, `app.js`, `style.css` — upload widget + slice-viewer canvas rỗng.

**Quyết định & lý do:**
- Chốt schema JSON của `/predict` **trước khi** có model, để frontend làm song song. Schema lấy nguyên
  từ `liver_mri_3d_classification_plan.md` §8.1, không tự chế thêm field.
- Không thêm React — AGENTS.md §3.8. Vanilla JS + module ES6 đủ cho slice-viewer.

**Kết quả / số liệu:** không có (chưa nối model).

**Dang dở:**
- [ ] `/predict` còn trả mock. Chưa có loader checkpoint.
- [ ] Slice-viewer mới vẽ được 1 lát, chưa cuộn được.

**Điểm vào phiên sau:** nối model thật vào `webapp/backend/main.py:48` (`load_model()` đang là stub).
Cần checkpoint từ S-013 ở `artifacts/ckpt/` — file này KHÔNG có trong git, phải tải lại từ Kaggle output.

**Cảnh báo cho tool sau:** memory nội bộ của Antigravity đang giữ một bản schema `/predict` cũ thiếu
field `defer`. Nếu thấy mâu thuẫn thì AGENTS.md + plan §8.1 thắng. Đã ghi đè memory đó.
```

</details>

---

## Nhật ký

## S-001 · 2026-07-24 10:20 · claude-code

**Mục tiêu phiên:** Dựng hệ thống context dùng chung + WORKLOG cho quy trình luân phiên 4 tool AI coding trên cùng repo (bước 1–2 của kế hoạch thiết lập workflow).

**Nhánh / commit:** `main` · repo chưa có commit nào → *(chờ commit đầu tiên)*

**Đã đụng file:**
- `AGENTS.md` — **mới**, nguồn sự thật duy nhất: mục tiêu dự án, bản đồ tài liệu, 10 nguyên tắc bất di bất dịch, cấu trúc thư mục đích, tech stack, bảng lệnh chạy, ràng buộc Kaggle, quy ước code, quy ước git, danh sách "tuyệt đối không tự làm", ghi chú riêng từng tool.
- `CLAUDE.md` — **mới**, chỉ có `@AGENTS.md` + vài quy tắc cơ chế riêng Claude Code. Không chứa nội dung dự án.
- `.cursor/rules/00-project-context.mdc` — **mới**, `alwaysApply: true`, trỏ về `AGENTS.md`. Giữ mỏng.
- `WORKLOG.md` — **mới**, file này.

**Quyết định & lý do:**
- **Chọn `AGENTS.md` làm file gốc** thay vì CLAUDE.md — vì Codex, Cursor và Antigravity đều đọc chuẩn này natively, chỉ Claude Code cần cầu nối. Đặt gốc ở CLAUDE.md sẽ khiến 3/4 tool phải có file cầu nối thay vì 1/4.
- **Cầu nối bằng import/tham chiếu, không copy** — CLAUDE.md dùng `@AGENTS.md`, rule Cursor dùng chỉ dẫn "đọc AGENTS.md". Chép nội dung là con đường chắc chắn dẫn tới drift giữa 4 tool.
- **WORKLOG append-only, entry mới ở cuối file** — để `tail` là thao tác đọc mặc định, và để git diff luôn là "thêm dòng ở cuối" (ít conflict nhất).
- **Không nhúng `WORKLOG.md` vào context tool** (không `@WORKLOG.md` trong CLAUDE.md) — file này chỉ phình ra theo thời gian; nhúng cả file sẽ đốt context vô ích. Thay vào đó chỉ định đọc 80 dòng cuối.
- **Chưa di chuyển `MRI_Classification_Spec_Sheet.md` và `liver_mri_3d_classification_plan.md` vào `docs/`** — cấu trúc thư mục cuối cùng thuộc bước 6, di chuyển sớm sẽ làm hỏng các link vừa viết. Để nguyên ở root, đã link đúng vị trí hiện tại.

**Kết quả / số liệu:** không có (phiên thiết lập).

**Dang dở:**
- [ ] Bước 3 — `docs/MULTI_TOOL_WORKFLOW.md`: giao thức chống xung đột, checklist vào/ra phiên, ai sửa config của tool nào.
- [ ] Bước 4 — tích hợp Impeccable (`npx impeccable install`, `/impeccable init` → PRODUCT.md/DESIGN.md, vòng đời lệnh cho web app / slide / report).
- [ ] Bước 5 — xử lý riêng cho Antigravity (không có `/impeccable`): quality gate qua `npx impeccable detect`.
- [ ] Bước 6 — `.gitignore` gộp cho 4 tool + Impeccable, và chốt cây thư mục cuối.
- [ ] Repo **chưa có commit nào** và **chưa có `.gitignore`** — cần làm trước khi commit lần đầu, tránh lỡ tay add file rác.

**Điểm vào phiên sau:** người dùng duyệt `AGENTS.md` + `WORKLOG.md` trước, rồi mới sang bước 3 (`docs/MULTI_TOOL_WORKFLOW.md`). Đây là nền móng — sai ở đây thì mọi thứ sau lệch theo.

**Cảnh báo cho tool sau:**
- Bảng lệnh chạy ở `AGENTS.md` §6 hiện **toàn dòng "chưa có"**. Tool nào tạo entrypoint đầu tiên phải cập nhật đúng dòng đó trong cùng commit — nếu không bảng này sẽ trở thành tài liệu nói dối, còn tệ hơn không có.
- Chưa có `.gitignore`. **Đừng chạy `git add -A`** cho tới khi bước 6 xong.


## S-002 · 2026-07-24 11:05 · claude-code

**Mục tiêu phiên:** Hoàn tất bước 3–6 của thiết lập workflow: giao thức chống xung đột, tích hợp Impeccable, xử lý riêng Antigravity, `.gitignore` + chốt cây thư mục.

**Nhánh / commit:** `main` · repo vẫn chưa có commit nào → *(chờ commit đầu tiên)*

**Đã đụng file:**
- `docs/MULTI_TOOL_WORKFLOW.md` — **mới**. Luật một-tay-lái, checklist rời/vào tool (lệnh git cụ thể), ma trận sở hữu file, 9 điểm xung đột thật, quy ước branch/commit, cài + vòng đời lệnh Impeccable cho 3 deliverable, xử lý riêng Antigravity, quality gate, bảng tra nhanh.
- `scripts/quality-gate.sh` — **mới**. POSIX sh, hai chế độ (`--staged` / worktree). Kiểm: impeccable detect trên `webapp/frontend|slides|reports`, `splits/` bất biến, không lọt file `.nii/.dcm/.pt/...`, ruff (khi đã cài). Đã smoke-test: PASS, exit 0.
- `.githooks/pre-commit` — **mới**, gọi quality-gate ở chế độ `--staged`. Bật bằng `git config core.hooksPath .githooks`.
- `.gitignore` — **mới**. Gộp: dữ liệu bệnh nhân, artifact train, Python, secret, Node, Impeccable ephemeral, và 4 tool.
- `AGENTS.md` — cập nhật §0 (thêm bước quality gate + link workflow), §2 (bảng tài liệu), §4 (cây thư mục đầy đủ), §6 (thêm lệnh gate + cài Impeccable), §9 (bỏ ghi chú "sẽ tạo"), §11 (Antigravity), và **thêm §12 — ràng buộc thiết kế** áp cho mọi tool kể cả tool không có `/impeccable`.

**Quyết định & lý do:**
- **Đã fetch README của Impeccable để verify thay vì tin giả định.** Kết quả: **58 deterministic detector rule** (detector báo 49 loại vấn đề), không phải 46 như giả định ban đầu — con số 46 đã lỗi thời. Có **23 lệnh slash**, không phải 8. Danh sách provider gồm 13 harness và **xác nhận không có Antigravity**.
- **Bổ sung vào vòng đời web app 3 lệnh mà kế hoạch ban đầu bỏ sót:** `harden` (file sai định dạng, thiếu pha, timeout — quan trọng với app y tế), `onboard` (empty state, giải thích `defer`), `clarify` (chữ về mức bất định rất dễ gây hiểu nhầm ở ngữ cảnh lâm sàng).
- **Liệt kê rõ lệnh cần TRÁNH** (`bolder`, `delight`, `overdrive`, `colorize`) — sai giọng cho dự án y tế, và agent rất dễ với tay vào chúng khi được bảo "làm đẹp hơn".
- **Quality gate đặt ở `.githooks/` + `core.hooksPath`** thay vì `.git/hooks/` — để hook được commit và áp cho mọi tool, kể cả Antigravity. `.git/hooks/` không đi theo git nên vô dụng trong bối cảnh đa tool.
- **Gate chặn cả `splits/`**, không chỉ UI — sinh lại split là lỗi nguy hiểm nhất mà diff nhìn vô hại nhất.
- **Khuyến nghị không giao việc dựng UI mới cho Antigravity.** Detector bắt được lỗi máy kiểm được, nhưng không bắt được phân cấp thông tin sai hay lạc giọng — đó là việc của `critique`, mà Antigravity không chạy được.

**Kết quả / số liệu:** `sh scripts/quality-gate.sh` → PASS (2 SKIP vì chưa có UI và chưa cài ruff).

**Dang dở:**
- [ ] **Chưa chạy `npx impeccable install`** và chưa `/impeccable init` → `PRODUCT.md` / `DESIGN.md` chưa tồn tại. AGENTS.md §12 và workflow §7 đang trỏ tới file chưa có.
- [ ] **Chưa bật hook:** `git config core.hooksPath .githooks`.
- [ ] Repo vẫn **chưa có commit nào**.
- [ ] Khối Antigravity trong `.gitignore` là **phỏng đoán chưa kiểm chứng** (`.antigravity/`, `.agent/`, `.gemini/`).
- [ ] Chưa xác minh `impeccable detect` có trả exit code ≠ 0 khi phát hiện lỗi hay không (xem ghi chú trong `scripts/quality-gate.sh`).

**Điểm vào phiên sau:**
1. `git config core.hooksPath .githooks`
2. `git add -A && git commit` — commit đầu tiên của repo (`.gitignore` đã có nên `add -A` giờ an toàn).
3. `npx impeccable install --providers=claude,codex,cursor --scope=project`
4. `/impeccable init` — trả lời theo định hướng ở `docs/MULTI_TOOL_WORKFLOW.md` §7.1, rồi **đọc lại `DESIGN.md` và sửa tay** chỗ nào lạc giọng y tế.
5. `git status` sau bước 3 — đối chiếu xem `.gitignore` đã phủ đúng những gì Impeccable thực sự sinh ra chưa.

**Cảnh báo cho tool sau:**
- Sau **phiên Antigravity đầu tiên**, chạy `git status` và sửa khối Antigravity trong `.gitignore` cho đúng thực tế. Đừng tin phỏng đoán hiện tại.
- Hook Impeccable cho Claude Code nằm ở `.claude/settings.local.json` — file này **cố ý không commit**. Nếu clone sang máy khác thấy "mất hook", đó là đúng thiết kế, chạy lại `npx impeccable install` là xong. Đừng thêm file đó vào git, nó có thể chứa đường dẫn/cấu hình cá nhân.
- `docs/MULTI_TOOL_WORKFLOW.md` §5 liệt kê 3 điểm xung đột **không loại bỏ được hoàn toàn** (⚠️). Đọc trước khi ngạc nhiên vì chúng.


## S-003 · 2026-07-24 11:50 · claude-code

**Mục tiêu phiên:** Thực thi thật: bật hook, commit đầu tiên, cài Impeccable, chạy `init`, và sửa tài liệu theo những gì quan sát được thay vì giả định.

**Nhánh / commit:** `main` · *(khởi tạo)* → `b2bf8fa` → `377bbad` → *(commit thứ 3 đang chờ)*

**Đã đụng file:**
- `.gitattributes` — **mới**. Ép LF cho `*.sh` và `.githooks/*`; script shell bị checkout CRLF trên Windows sẽ lỗi `bad interpreter`.
- `PRODUCT.md` — **mới**. Viết tay theo đúng schema trong `.claude/skills/impeccable/reference/init.md` (có `<!-- impeccable:product-schema 1 -->`), sau khi hỏi người dùng 3 câu về gap thật.
- `.gitignore` — thêm khối payload skill Impeccable; gỡ `.agent/` khỏi khối phỏng đoán Antigravity.
- `scripts/quality-gate.sh` — thay ghi chú phỏng đoán bằng hành vi đã kiểm chứng của `detect`.
- `docs/MULTI_TOOL_WORKFLOW.md` — sửa §7 (init KHÔNG sinh DESIGN.md), tách §7.1/§7.2, cập nhật §8.3 và §10.
- `AGENTS.md` — §2 tách PRODUCT.md/DESIGN.md, §6 đánh dấu install đã chạy, §12 sửa lại thứ tự file.
- `.codex/hooks.json`, `.cursor/hooks.json` — Impeccable sinh, đã commit.

**Quyết định & lý do:**
- **KHÔNG commit payload skill Impeccable.** `npx impeccable install` chép nguyên bộ vào **3 chỗ** (`.claude/skills/`, `.cursor/skills/`, `.agents/skills/`) — **377 file, ~8.7MB, ba bản y hệt**. Commit sẽ tạo diff khổng lồ ở 3 nơi mỗi lần cài lại, đúng loại churn mà cả giao thức này sinh ra để tránh. Đánh đổi đã chấp nhận và ghi rõ: **version Impeccable không được pin trong git**; nếu sau này cần khoá thì ghi số version vào WORKLOG chứ không commit 8.7MB.
- **Gỡ `.agent/` khỏi khối Antigravity trong `.gitignore`** — nó suýt va với `.agents/` thật của Impeccable (payload cho Codex). Đã thêm cảnh báo tại chỗ để phiên sau không viết lại `.agent*`.
- **Thêm `.gitattributes`** — phát sinh ngoài kế hoạch, do git cảnh báo CRLF ngay khi stage. Không phải cẩn thận thừa: hook và quality-gate là file `sh`, CRLF làm chúng chết trên chính máy này.
- **Viết `PRODUCT.md` bằng tay theo reference thay vì chờ restart.** Skill registry của Claude Code nạp lúc khởi động nên `/impeccable init` chưa dùng được trong session này, nhưng `reference/init.md` đã nằm trên đĩa — đọc và làm theo đúng quy trình 6 bước của nó, gồm cả bước phỏng vấn bắt buộc.

**Kết quả / số liệu:**
- Hook hoạt động: quality gate tự chạy trước cả 2 commit, PASS.
- `.gitignore` có tác dụng: staged giảm từ **377 file xuống 3**.
- **Kiểm chứng `impeccable detect`** trên HTML lỗi cố ý: **exit 0 = sạch, exit 2 = có finding**; `--json` in mảng phẳng `{antipattern, name, description, severity, category, file, line, snippet}`. Cách tiếp cận dựa-vào-exit-code của gate là đúng → đã xoá TODO trong script.

**Ba chỗ tài liệu sai đã sửa (giả định ban đầu ≠ thực tế):**
1. **`/impeccable init` chỉ sinh `PRODUCT.md`, KHÔNG sinh `DESIGN.md`.** DESIGN.md do `new-work` tạo (tự chạy bên trong `shape`/`craft`) hoặc `/impeccable document` cho UI đã có. Cả prompt gốc lẫn README đều nói sai chỗ này.
2. **`init` cố ý KHÔNG hỏi gì về thẩm mỹ** (reference cấm rõ ràng). Nên định hướng giọng/màu đã chuyển vào `PRODUCT.md` (Product Principles / Brand Commitments / Accessibility) và `AGENTS.md` §12.
3. **Codex nhận payload ở `.agents/skills/`, không phải `.codex/skills/`.** `.codex/` chỉ chứa `hooks.json`.

**Câu trả lời của người dùng khi phỏng vấn (đã ghi vào PRODUCT.md):**
- Người dùng chính của web app: **hội đồng / người review nghiên cứu**, không phải bác sĩ đang đọc ca.
- Slide + report: **một bộ dùng chung**, dựng chuẩn hội nghị rồi rút gọn cho nội bộ.
- Ngôn ngữ: **tiếng Việt toàn bộ**, thuật ngữ y khoa/thống kê giữ tiếng Anh.

**Dang dở:**
- [ ] **Chưa push.** Remote `origin` đã có (`github.com/hdtruong802/liver-mri-3d-classifier`) nhưng chưa đẩy — chờ người dùng quyết.
- [ ] `DESIGN.md` chưa tồn tại, và **đúng theo thiết kế** — nó sẽ xuất hiện ở lần `/impeccable shape` đầu tiên (Sprint 3).
- [ ] Khối Antigravity trong `.gitignore` vẫn là phỏng đoán (`.antigravity/`, `.gemini/`).
- [ ] Chưa có `README.md`.

**Điểm vào phiên sau:**
1. **Khởi động lại Claude Code** để `/impeccable` vào registry (skill cài giữa session không dùng được ngay).
2. Quyết định push hay chưa.
3. Việc thật tiếp theo theo plan là **Sprint 1**: xin quyền LLD-MMRI, rồi `src/preprocess/` + `src/data/make_splits.py`. Web app và `/impeccable shape` thuộc Sprint 3 — chưa đụng tới.

**Cảnh báo cho tool sau:**
- **Đừng đi tìm `DESIGN.md` rồi tưởng thiếu.** Xem `docs/MULTI_TOOL_WORKFLOW.md` §7.1.
- **Đừng commit `.claude/skills/`, `.cursor/skills/`, `.agents/skills/`.** Nếu thấy chúng trong `git status`, `.gitignore` đã bị sửa hỏng.
- `PRODUCT.md` mục *Evidence on Hand* nói rõ: **chưa có một con số kết quả nào**. Mọi số xuất hiện trong UI/slide/report trước khi có kết quả thật phải được đánh dấu là dữ liệu giả lập.


## S-004 · 2026-07-24 12:15 · claude-code

**Mục tiêu phiên:** Push lên remote và xử lý `.github/` chưa được theo dõi.

**Nhánh / commit:** `main` · `f179703` → *(commit .gitignore đang chờ)* · đã push, `main` track `origin/main`

**Đã đụng file:**
- `.gitignore` — thêm khối GitHub Copilot.
- `WORKLOG.md` — entry này.

**Quyết định & lý do:**
- **Push thành công.** Remote rỗng trước đó (`git ls-remote` không trả về nhánh nào) nên không đè lên gì.
- **Ignore `.github/copilot-instructions.md` và `.github/instructions/`.** Đọc nội dung trước khi quyết: chỉ là hook trỏ sang hướng dẫn vẽ mermaid, do tool `mermaid-ai-skills` cài, **không chứa ngữ cảnh dự án**, không mâu thuẫn AGENTS.md. Đây là artifact máy-cục-bộ giống payload Impeccable, không phải nội dung dự án. **Cố ý KHÔNG ignore cả `.github/`** — chỗ đó còn để dành cho GitHub Actions.
- Nếu về sau thực sự dùng Copilot: bỏ 2 dòng ignore rồi biến file đó thành **cầu nối trỏ về AGENTS.md**, không chép nội dung — đã ghi hướng dẫn ngay trong `.gitignore`.

**Kết quả / số liệu:** 3 commit đã lên `github.com/hdtruong802/liver-mri-3d-classifier`.

**Dang dở:**
- [ ] Chưa có `README.md` — repo đang PUBLIC mà chưa có RUO disclaimer ở trang đầu.

**Điểm vào phiên sau:** khởi động lại Claude Code để `/impeccable` vào registry, rồi bắt đầu Sprint 1 (xin quyền LLD-MMRI → `src/preprocess/`).

**Cảnh báo cho tool sau:**
- ⚠️ **Repo là PUBLIC.** Đã kiểm: không có dữ liệu bệnh nhân, không có secret, không có checkpoint (quality gate chặn sẵn). Nhưng Spec Sheet và Plan — tức toàn bộ hướng nghiên cứu chưa công bố — **đang công khai**. Nếu không cố ý thì đổi sang private:
  `gh repo edit hdtruong802/liver-mri-3d-classifier --visibility private --accept-visibility-change-consequences`
- Repo public mà chưa có `README.md` nghĩa là **chưa có RUO disclaimer ở nơi người ta nhìn đầu tiên**. Vi phạm AGENTS.md §3.1. Nên viết README sớm.
