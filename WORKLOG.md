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


## S-005 · 2026-07-24 14:30 · claude-code

**Mục tiêu phiên:** Dựng `slides/overview.html` — bộ slide tổng quan dự án, qua `/impeccable craft`, có xác minh nguồn cho mọi con số.

**Nhánh / commit:** `main` · `17675ff` → *(commit đang chờ)*

**Đã đụng file:**
- `slides/overview.html` — **mới**, 13 slide, 36.5 KB, một file tự chứa, 0 tham chiếu ngoài.
- `DESIGN.md` — **mới**. Thế giới thị giác đầu tiên của dự án; chi phối cả web app và report sau này.
- `PRODUCT.md` — thêm cam kết thương hiệu thứ 3 (quy ước hội nghị là lựa chọn thường trực).
- `.impeccable/config.json` — 2 ngoại lệ detector kèm lý do.

**Quyết định & lý do:**
- **Người dùng chọn canon (standing exit)** thay vì hướng được roll (bản khắc atlas giải phẫu, grounded #5, seed `b8275583`). Theo luật của Impeccable, chọn canon = quy ước trở thành cam kết, thực thi ở mức cao nhất, không cài cắm quirk. Thanh chuẩn người dùng chốt: **talk MICCAI/MIDL**.
- **Nền sáng**, chọn từ cảnh dùng thật (phòng họp còn bật đèn để ghi chú; máy chiếu xử lý nền sáng ổn định hơn nền tối bị nhạt màu), không phải từ thói quen thể loại.
- **Một họ chữ hệ thống duy nhất.** Ràng buộc quyết định: slide phải mở ngoại tuyến bằng double-click và hiển thị đủ dấu tiếng Việt ở cỡ nhỏ → không CDN, không webfont.
- **Thiết bị phân biệt hai loại số:** nét đứt + nhãn chữ = "chưa có dữ liệu"; nét liền + nhãn nguồn `[Tác giả, Năm]` + `n=` = số đã công bố của người khác. Ghi thành `The Two-Number Rule` trong DESIGN.md.

**Kết quả / số liệu:** quality gate PASS. 13/13 slide có dải RUO và nhãn nguồn. 0 tham chiếu ngoài.

**Detector bắt được 35 finding ở bản dựng đầu — 4 loại, tất cả đều đúng:**
1. **`all-caps-body` ×31**, chuỗi in hoa dài tới 108 ký tự. Đây là lỗi riêng của tiếng Việt mà tôi đã bỏ sót: dấu thanh chồng lên chữ hoa (Ế, Ữ, Ậ) bị chèn ép ở cỡ nhỏ và mất khi chiếu. **Đã bỏ `text-transform:uppercase` khỏi toàn bộ hệ thống** và ghi thành `The No-Uppercase Rule`.
2. **`low-contrast` 4.4:1** — màu `#6B7480` thiếu chuẩn AA. Đổi sang `#656E7A` (4.8:1). Đã ghi cả giá trị hỏng vào DESIGN.md để phiên sau không làm nhạt lại.
3. **`design-system-font`** — CSS khai stack khác DESIGN.md. Đây là **drift thật**, đã sửa file thiết kế cho khớp code chứ không tắt cảnh báo.
4. **`em-dash-overuse` 46 lần** — nhịp văn máy. Giảm còn 8 bằng cách viết lại prose dùng dấu phẩy, hai chấm, ngoặc đơn.

Hai ngoại lệ đăng ký kèm lý do (`single-font`, `overused-font=arial`): cả hai bị ràng buộc ngoại tuyến + tiếng Việt ép, không phải lựa chọn thẩm mỹ. Ghi rõ trong DESIGN.md: **đừng thêm font thứ hai chỉ để tắt cảnh báo**.

**Ba chỗ Spec Sheet lệch so với nguồn gốc — CẦN NGƯỜI DÙNG SỬA:**
> Spec Sheet §1 và §2 ghi *"SOTA trên LLD-MMRI đã bão hòa quanh 85% acc / 85% macro-F1 / 97% macro-AUC"*. Đối chiếu nguồn gốc thì **cả ba số đều cao hơn thực tế**:
> - **F1 cao nhất xác minh được: 0,8322** (quán quân challenge), không phải 0,85.
> - **Accuracy cao nhất xác minh được: 0,7885** (SDR-Former). Không tìm thấy công bố nào đạt 85% acc.
> - **AUC cao nhất xác minh được: 0,9536** (SDR-Former), không phải 0,97.
> - Thêm nữa: bài SDR-Former **không nói rõ F1 và AUC có macro hay không**, nên chữ "macro-" trong Spec Sheet là suy diễn.
>
> Slide dùng số đã xác minh. **Spec Sheet vẫn đang sai và cần sửa.**

**Một nhận định của Spec Sheet bị tìm kiếm bác bỏ một phần:**
> Spec Sheet nói SOTA *"chỉ báo accuracy/F1/AUC"* và calibration/selective prediction là chỗ bỏ trống. Thực tế **[Wang et al., 2021] arXiv:2110.08817 đã làm uncertainty + cơ chế từ chối** trên MRI gan đa pha (F1 0,62→0,71 khi chỉ xét 70% ca tự tin nhất).
> Khoảng trống vẫn còn nhưng **hẹp hơn**, và phải phát biểu chính xác hơn: công trình đó dùng **dữ liệu riêng tư 400 bệnh nhân**, chỉ **3 lớp ác tính**, và **không báo chỉ số calibration nào**. Trên chính LLD-MMRI (công khai, 7 lớp, có leaderboard) thì vẫn chưa có công bố nào báo calibration hay selective prediction — đã kiểm toàn văn SDR-Former, không có từ nào về uncertainty.
> Slide 9 phát biểu theo bản đã hiệu chỉnh này. **Định vị của dự án vẫn đứng vững, nhưng câu chữ trong Spec Sheet đang quá mạnh.**

**Dang dở:**
- [ ] **Chưa xem render thật** — phiên này không có công cụ trình duyệt/screenshot. Đã kiểm cấu trúc, chưa kiểm thị giác.
- [ ] Chưa chạy `impeccable-finish-reviewer` (subagent) vì người dùng không yêu cầu spawn agent.
- [ ] Spec Sheet chưa được sửa theo 2 mục trên (cần người dùng duyệt — AGENTS.md §10 cấm agent tự đổi Spec Sheet).

**Điểm vào phiên sau:**
1. Mở `slides/overview.html` bằng trình duyệt, bấm qua 13 slide, kiểm tràn nội dung ở màn hình thật và thử in ra PDF.
2. Duyệt và sửa `MRI_Classification_Spec_Sheet.md` theo hai mục lệch ở trên.
3. Sprint 1 vẫn chưa bắt đầu.

**Cảnh báo cho tool sau:**
- `DESIGN.md` giờ là ràng buộc cho **cả web app và report**, không riêng slide. Đọc trước khi đụng UI.
- **Không có con số nào của dự án này trên slide** và phải giữ nguyên như vậy cho tới khi có kết quả thật.
- `.body` dùng `overflow:auto` có chủ ý: nếu nội dung tràn thì hiện thanh cuộn để người trình bày thấy khi tập dượt, thay vì nuốt mất một dòng ngay giữa buổi báo cáo. Đừng đổi lại thành `hidden`.


## S-006 · 2026-07-24 15:40 · claude-code

**Mục tiêu phiên:** Lưu prompt ra file để đọc được, và dựng thêm một bản slide theo phong cách khác để người dùng so sánh.

**Nhánh / commit:** `main` · `54513ac` → *(commit đang chờ)*

**Đã đụng file:**
- `prompt/slides_overview.md` — **mới**. Prompt đã dùng để sinh `slides/overview.html`, kèm ghi chú sau lần chạy đầu. Người dùng không đọc được prompt trong panel hẹp của VS Code nên cần file mở full-width.
- `slides/overview-alt-atlas.html` — **mới**. Bản đối chiếu theo thế giới "bản khắc atlas giải phẫu".
- `slides/README.md` — **mới**. Bảng so sánh hai bản và quy trình phải làm nếu chọn bản atlas.
- `.impeccable/config.json` — thêm ignore file cho `slides/overview-alt-*.html`.

**Quyết định & lý do:**
- **Dựng bản đối chiếu bằng đúng hướng mà Impeccable đã roll trúng** (grounded #5, seed `b8275583`) thay vì bịa ra một phong cách mới. Đó là so sánh có ý nghĩa: quy ước so với thế giới thị giác riêng, và hướng đó đã được cân nhắc đầy đủ ở S-005 nên không phải làm lại từ đầu.
- **Giữ nguyên 100% nội dung và số liệu.** Chỉ khác thế giới thị giác. So sánh mà đổi cả nội dung thì không so được gì.
- **KHÔNG viết đè `DESIGN.md`.** File đó vẫn sở hữu thế giới đã cam kết (canon MICCAI). Bản atlas là artifact đối chiếu, không phải bản thay thế. Ghi rõ điều này ở đầu file HTML và trong `slides/README.md`.
- **Đăng ký `ignores add-file` cho `slides/overview-alt-*.html`** kèm lý do. Detector báo 9 finding trên file này, **tất cả đều là "outside DESIGN.md"** — tức là nó nói đúng, file này cố tình đi ra ngoài hệ thống. Không có lỗi thật nào (không tương phản kém, không chữ hoa, không em-dash quá tay). Đây là ca dùng đúng của cơ chế ignore-file, khác hẳn việc thêm token để tắt cảnh báo.
- **Bản atlas dùng chú số + chú giải thay cho `[Tác giả, Năm]` viết thẳng.** Chú số và đường dóng là thiết bị gốc của bản khắc giải phẫu, nên hệ trích nguồn mọc ra từ chính ngôn ngữ của thế giới đó chứ không phải dán vào.

**Kết quả / số liệu:** quality gate PASS. Cả hai file đều 13 slide, 0 tham chiếu ngoài, RUO 13/13, không có số nào của dự án.

**Dang dở:**
- [ ] Người dùng chưa chọn bản nào. Bản canon vẫn là bản đã chốt cho tới khi có quyết định khác.
- [ ] Vẫn chưa xem render thật của cả hai bản (phiên này không có công cụ trình duyệt).
- [ ] Chưa push.

**Điểm vào phiên sau:** người dùng mở cả hai file, chọn một. Nếu chọn atlas thì làm đủ 3 bước ghi trong `slides/README.md` — quan trọng nhất là **viết lại `DESIGN.md`** và **gỡ dòng ignore**, vì `DESIGN.md` chi phối cả web app lẫn report.

**Cảnh báo cho tool sau:**
- **Đừng coi bản atlas là chính thức khi ignore vẫn còn.** Giữ ignore rồi xuất bản là tự tắt đèn báo cho một bề mặt thật. Quy trình đúng nằm ở `slides/README.md`.
- Ignore này dùng wildcard `slides/overview-alt-*.html`, nên **mọi file `overview-alt-*` sau này cũng không bị soi**. Nếu thêm bản đối chiếu thứ ba thì vẫn được che; nhớ điều đó khi dọn dẹp.


## S-007 · 2026-07-24 16:20 · claude-code

**Mục tiêu phiên:** Sửa trích dẫn cho đúng chuẩn học thuật có link, và xử lý việc `slides/overview.html` bị xoá khỏi working tree.

**Nhánh / commit:** `main` · `41ae19d` → *(commit đang chờ)*

**Đã đụng file:**
- `slides/overview.html` — bản canon MICCAI **bị người dùng xoá**, và bản atlas được đổi tên vào chỗ đó.
- `DESIGN.md` — **viết lại toàn bộ** theo thế giới bản khắc atlas.
- `PRODUCT.md` — sửa cam kết thương hiệu #3.
- `slides/README.md` — viết lại, giờ chỉ còn một bản.
- `.impeccable/config.json` — gỡ 2 ignore.

**Quyết định & lý do:**
- **Phát hiện `slides/overview.html` bị xoá, đã DỪNG và hỏi thay vì tự khôi phục.** Đúng giao thức `docs/MULTI_TOOL_WORKFLOW.md` §2: thay đổi mình không nhận là của mình thì không được ghi đè. Người dùng xác nhận **cố ý xoá, chọn bản atlas**.
- **Làm đủ 3 bước trong `slides/README.md` thay vì chỉ đổi tên file.** Đổi tên mà giữ nguyên `DESIGN.md` canon sẽ tạo drift ngay ở deliverable đầu tiên, vì `DESIGN.md` chi phối cả web app và report.
- **Gỡ `ignoreFiles: slides/overview-alt-*.html`** — file không còn là artifact đối chiếu, phải chịu detector soi như mọi bề mặt thật.
- **Gỡ luôn `ignoreRules: single-font`** — thế giới atlas dùng **hai** họ chữ (chân phương cho tiêu đề/chú giải, sans cho số liệu), nên ngoại lệ đó không còn lý do tồn tại. Giữ một ignore đã hết hạn là để lại bẫy cho phiên sau.
- **Chỉ giữ `overused-font=arial`** — vẫn đúng, Arial là chốt chặn cuối của stack sans chứ không phải font được chọn.

**Trích dẫn — sửa cái gì:**
> Định dạng cũ `1Taxonomy 7 lớp và 8 thì theo công bố dataset LLD-MMRI, 2023` **không phải trích dẫn**, nó là câu mô tả có kèm năm, dính số, không link.
> Nay theo **kiểu số thứ tự (Vancouver)**: `4. Lou M., et al. SDR-Former. Neural Networks 185 (2025) 107228. arXiv:2402.17246` với mã định danh là link bấm được.
> 14 hyperlink tới nguồn gốc. Khi in ra giấy, link tự hiện URL trong ngoặc qua `@media print` — trên giấy không ai bấm được.
> File vẫn **mở và hiển thị đầy đủ khi ngoại tuyến**; link chỉ cần mạng lúc bấm.

**Kết quả / số liệu:** `impeccable detect slides` → **exit 0, 0 finding**, với ignoreRules và ignoreFiles đều **rỗng**. Đây là lần đầu file slide sạch mà không có gì che.

**Dang dở:**
- [ ] Vẫn chưa xem render thật (phiên này không có công cụ trình duyệt). Nền tối + khung kẻ đôi là thứ cần nhìn mắt thường mới biết có ổn không.
- [ ] Spec Sheet vẫn chưa được sửa theo S-005.
- [ ] Chưa push.

**Điểm vào phiên sau:** mở `slides/overview.html`, bấm qua 13 bản khắc, thử in PDF, và **bấm thử vài link trích dẫn** xem có tới đúng nguồn không.

**Cảnh báo cho tool sau:**
- **Bản canon MICCAI đã bị loại sau khi dựng thành bản chạy được, không phải bị bỏ qua.** Nó còn trong git ở `54513ac`. Đừng đề xuất quay về nó như thể đó là lựa chọn an toàn chưa ai nghĩ tới — đã ghi vào `PRODUCT.md`.
- **Nền tối cần phòng chiếu có giảm sáng.** Đây là đánh đổi đã chấp nhận có ý thức, ghi trong `DESIGN.md` mục Overview. Nếu buổi báo cáo diễn ra trong phòng bật đèn đầy đủ thì đây là rủi ro thật, không phải lỗi thiết kế cần sửa lén.
- `.impeccable/config.json` giờ chỉ còn **một** ignore duy nhất và nó có lý do. Giữ nguyên tình trạng đó: mỗi ignore thêm vào phải kèm `--reason`, và phải gỡ khi hết hiệu lực.


## S-008 · 2026-07-24 17:05 · claude-code

**Mục tiêu phiên:** Xử lý finding `flat-type-hierarchy` do hook Impeccable báo sau khi commit S-007.

**Nhánh / commit:** `main` · `0563e2c` → *(commit đang chờ)*

**Đã đụng file:**
- `slides/overview.html` — dựng lại toàn bộ thang chữ.
- `DESIGN.md` — đồng bộ token, viết lại mục Hierarchy thành bảng, thêm 2 named rule.

**Quyết định & lý do:**
- **Finding là lỗi thật, không phải false positive.** Thang cũ dồn cục ở giữa: `title` 1,3rem — `data` 1,3rem — `body` 1,2rem. Ba bậc trong khoảng 8%. Tệ nhất là **`data` không phân biệt được với `body`**, trong khi `PRODUCT.md` nói số liệu là nhân vật chính. Đây đúng là loại lỗi detector bắt được mà mắt người dựng thì không, vì tôi nhìn từng vai trò riêng lẻ chứ không nhìn cả thang.
- **Dựng lại thang theo tỉ lệ đều ≥1,25**, kiểm ở **cả hai đầu `clamp()`** chứ không chỉ ở giá trị max — bản cũ chỉ đúng ở một đầu.
- **Giảm từ 6 cỡ xuống 5 cỡ.** Hook gợi ý "ít cỡ hơn, tương phản mạnh hơn". Cho `title` và `body` **cùng cỡ**, phân biệt bằng chân phương so với sans cộng màu. Hệ thống đã dùng họ chữ làm kênh phân biệt nên đây không phải thủ thuật mới.
- **Ghi thành `The Data-Outranks-Prose Rule` và `The Family-Not-Size Rule`** trong DESIGN.md, kèm cả con số sai của bản cũ, để phiên sau không vô tình thu hẹp lại.

**Kết quả / số liệu:** thang mới — tỉ lệ giữa các bậc kề nhau: 1,58 · 1,29 · 1,25 · 1,32 ở đầu max, và 1,58 · 1,29 · 1,25 · 1,32 ở đầu min. `detect` 0 finding, gate PASS.

**Bài học quy trình:** CLI `impeccable detect` báo **0 finding** trong khi hook báo `flat-type-hierarchy`. Hai đường soi không trùng nhau hoàn toàn. **Đừng coi `quality-gate.sh` PASS là đủ** — hook sau khi ghi file bắt được thứ CLI bỏ qua. Nếu về sau muốn gate chặt hơn, đây là chỗ cần điều tra.

**Dang dở:**
- [ ] Vẫn chưa xem render thật. Thang chữ vừa đổi khá nhiều, càng cần nhìn mắt thường.
- [ ] Spec Sheet vẫn chưa sửa theo S-005.
- [ ] Chưa push.

**Điểm vào phiên sau:** mở `slides/overview.html` kiểm thang chữ mới, nhất là bảng số ở bản khắc VII và VIII — số giờ to hơn chữ chạy một bậc đầy đủ, cần xem có làm vỡ layout bảng không.

**Cảnh báo cho tool sau:**
- **Đừng thu hẹp khoảng cách giữa Data và Body.** Đã có luật riêng cho nó trong DESIGN.md kèm lý do.
- Viết nội dung có backtick vào file thì **đừng dùng chuỗi nháy kép trong bash** — phiên này bị shell nuốt mất ba đoạn `` ` `` và làm hỏng âm thầm một `.replace()`. Dùng Write/Edit, hoặc heredoc nháy đơn.


## S-009 · 2026-07-24 18:30 · claude-code

**Mục tiêu phiên:** Sửa 2 lỗi người dùng thấy khi mở file: nội dung tràn gây thanh trượt khi F11, và nút Trước/Sau đè số trang.

**Nhánh / commit:** `main` · `8169af0` → *(commit đang chờ)*

**Đã đụng file:**
- `slides/overview.html` — sửa lớn: đơn vị đo, tách bản khắc, vị trí nút, hệ màu bảng.
- `DESIGN.md` — đồng bộ Plate Key Rule.

**Quyết định & lý do:**
- **Lỗi tràn là do sai kiến trúc, không phải chỉnh vặt.** Cỡ chữ chặn trên bằng `rem` trong khi khung slide co theo màn hình → trên màn thấp (1366×768) chữ giữ nguyên cỡ tối đa nên tràn. Sửa gốc: thêm đơn vị khung `--u: min(1vw, 1.778vh)` và cho **mọi** cỡ chữ + khoảng cách đo theo nó. Giờ tỉ lệ giữ nguyên ở mọi độ phân giải 16:9.
- **Bỏ `overflow:auto`, quay lại `overflow:hidden`.** Trước đây tôi để `auto` như một lưới an toàn, nhưng đó chính là thứ sinh ra thanh trượt người dùng thấy. Với nội dung đã đo theo khung thì không cần lưới đó nữa — và không bao giờ được có thanh trượt giữa buổi trình chiếu.
- **Nút điều hướng chuyển xuống giữa dưới + tự ẩn sau 2,2s.** Trước ở góc phải, đè lên số trang. Giờ ở giữa (giữa hai chân), `opacity:0` mặc định, chỉ hiện khi di chuột hoặc bấm phím. Trong lúc trình chiếu không có nút nào nằm trên bản khắc.
- **Tách bản khắc II thành hai** (7 lớp / 8 thì). Đo bằng Puppeteer thấy II chỉ dư 47px trong khi các bản khác dư 200–400px — phân bổ lệch đúng như người dùng nói. Tách ra: 7 lớp là không gian đầu ra, 8 thì là không gian đầu vào, hai ý khác nhau. Deck từ 13 lên **14 bản khắc**, đánh số lại toàn bộ + sửa 3 tham chiếu chéo.
- **Bỏ hoàng thổ khỏi hàng dẫn đầu của bảng số.** Ảnh chụp lộ ra tôi đang dùng hoàng thổ cho 4 việc (chú số, gạch tiêu đề, mốc phần, hàng dẫn đầu) — vi phạm chính `The Plate Key Rule` tôi viết. Hàng dẫn đầu giờ nhấn bằng **độ sáng nét** (Nét Khắc so với Nét Phụ) cộng nhãn chữ. DESIGN.md sửa lại: hoàng thổ có đúng 3 chỗ.

**Đã KIỂM ĐỊNH BẰNG MẮT lần đầu:** tìm thấy Puppeteer + Chrome trong cache npx (`npx impeccable` kéo về), viết script đo overflow từng bản khắc và chụp màn hình. Kết quả đo ở 1366×768 / 1920×1080 / 1280×720: **cả 14 bản khắc vừa khung**, chỗ dư tối thiểu 92px. Nút không đè số trang cũng không đè chú giải (kiểm bằng bounding-box). Đã xem tận mắt bản khắc III, V, IX — render đúng.

**Bẫy phương pháp gặp phải:**
- Phép đo `scrollHeight − clientHeight` cho grid **luôn ra 0**, vô dụng. Phải đo bằng `getBoundingClientRect().bottom` của phần tử thấp nhất so với đáy `.body`.
- Ảnh chụp đầu tiên thấy bản khắc **trống trơn** → tưởng script tách làm hỏng HTML. Thực ra HTML hỏng thật (thiếu một `</div>`, nesting lệch làm trình duyệt nuốt nội dung), **nhưng** ảnh trống còn có nguyên nhân thứ hai chồng lên: chụp trúng lúc animation ở `opacity:0`. Phải `emulateMediaFeatures` reduced-motion mới chụp đúng. Hai lỗi khác nhau che nhau — bài học: khi thấy trống, kiểm cả HTML lẫn thời điểm chụp.
- Tách section bằng regex + comment trùng số (`<!-- 3 -->` hai lần) làm **mất một bản khắc**. Phải lấy lại "câu hỏi nghiên cứu" từ `git show HEAD:` rồi chèn lại. Sau mỗi thao tác regex trên HTML: đếm cân bằng `<div>` cho mọi section.
- Detector **không giải được `max()` trong padding** → đọc thành 0, báo `cramped-padding`. Panel phải dùng padding cố định (22px), không dùng `max(16px, calc(...))`.

**Kết quả / số liệu:** 14 bản khắc, gate PASS, `detect` 0 finding. Đã xem 5 ảnh render.

**Dang dở:**
- [ ] Chưa xem mắt thường 9 bản khắc còn lại (mới xem III, V, IX + đo tự động cả 14).
- [ ] Chưa thử in PDF thật.
- [ ] Spec Sheet vẫn chưa sửa theo S-005.
- [ ] Chưa push.

**Điểm vào phiên sau:** xem nốt các bản khắc chưa chụp (nhất là 7, 8, 10 nhiều chữ) và thử in PDF. Ảnh render lưu ở scratchpad, không commit.

**Cảnh báo cho tool sau:**
- **Có Puppeteer + Chrome trong cache npx** ở `~/AppData/Local/npm-cache/_npx/1a4eb60c8f6b0f89/`. Dùng được để chụp/đo slide. Đây là đường tự kiểm bằng mắt khi phiên không có công cụ trình duyệt sẵn.
- **Mọi cỡ chữ và khoảng cách trong slide đo theo `--u`**, không dùng px cố định (trừ padding panel, vì detector). Đưa `rem` chặn-trên trở lại = tràn nội dung trên màn thấp.
- Deck giờ **14 bản khắc**, không phải 13. Tham chiếu chéo trong bài trỏ tới III (8 thì), VIII (leaderboard), XIV (chú giải).

## S-010 · 2026-07-24 11:58 · codex

**Mục tiêu phiên:** Chỉnh bản khắc III trong `slides/overview.html` để chữ dễ đọc hơn và khối nội dung cân đối như phản hồi người dùng.

**Nhánh / commit:** `main` · `7d80aad` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — tạo layout chuyên biệt cho bản khắc III.
- `WORKLOG.md` — ghi nhận phiên chỉnh giao diện này.

**Quyết định & lý do:**
- Gom tiêu đề, mô tả và hai nhóm thì MRI vào một khối có bề rộng giới hạn, đặt giữa vùng thân bản khắc — phiên bản cũ trải hai cột trên gần hết chiều ngang nên khối phải bị loãng và lệch về góc trên-trái.
- Nâng riêng danh sách thì MRI lên cấp chữ `data`, còn nhãn nhóm dùng cấp `title` — đây là thông tin người xem cần quét nhanh từ xa. Không đổi thang chữ toàn bộ deck vì S-009 đã xác minh những bản dày nội dung cần thang hiện tại để vừa khung.
- Hai cột dùng tỷ lệ 0,9 : 1,1 — nhóm động học có nhãn dài hơn và có ghi chú LI-RADS, nên hai cột không tương đương về độ dài nội dung.

**Kết quả / số liệu:** `detect.mjs --scope layout slides/overview.html` và CLI Impeccable cục bộ trên `slides` đều trả `[]`; `git diff --check` sạch; số thẻ `<div>` mở/đóng đều là 93.

**Dang dở:**
- [ ] Không có việc treo trong mã. `bash scripts/quality-gate.sh` không chạy được vì máy chưa cài WSL distribution; đã chạy phần detector tương đương bằng binary Impeccable trong npm cache.
- [ ] Chrome/Edge headless trên máy này lỗi GPU khi chụp ảnh, nên chưa thể đối chiếu render tự động sau chỉnh sửa.

**Điểm vào phiên sau:** Mở `slides/overview.html#3` trong Chrome, kiểm tra trực quan bản khắc III ở 100% zoom và trình chiếu 16:9; nếu cần, kiểm tra lại các bản dày chữ VII, VIII, X sau khi có môi trường screenshot hoạt động.

**Cảnh báo cho tool sau:** Chỉ bản khắc III mang lớp `phase-slide`; giữ cỡ chữ lớn và độ rộng bị giới hạn ở scope này, không áp dụng mù quáng sang toàn bộ deck vì các bản bảng số liệu cần không gian khác.

## S-011 · 2026-07-24 12:04 · codex

**Mục tiêu phiên:** Rà soát và sửa hệ typography, bố cục của toàn bộ 14 bản khắc trong `slides/overview.html`, không chỉ bản III.

**Nhánh / commit:** `main` · `4c69ab9` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — tăng thang chữ, căn lại toàn bộ vùng thân slide, thêm biến thể mật độ cao cho các bản dày nội dung và điều chỉnh mobile/print.
- `WORKLOG.md` — ghi nhận phiên rà soát deck toàn diện.

**Quyết định & lý do:**
- Tăng sáu token cỡ chữ của toàn deck theo cùng tỉ lệ hierarchy, thay vì phóng một vài bản riêng lẻ — lỗi người dùng thấy là lỗi hệ thống, rõ nhất ở màn 16:9 thấp nơi chữ chạy còn nhỏ.
- Các bản khắc mặc định đặt nội dung vào trục giữa dọc và giới hạn bề rộng 72 đơn vị khung — làm khoảng trống trên/dưới và trái/phải cân hơn, đồng thời giữ tiêu đề, chữ chạy và nhóm nội dung chung một trục đọc.
- Bản VII, X, XI và XIV dùng `dense-slide`, tăng ít hơn để các danh sách dài, ba cột và chú giải vẫn vừa vùng trình chiếu; XIV giữ căn trên vì đây là trang thư mục nguồn, không phải một luận điểm cần đặt giữa.
- Mobile và print trở lại dòng chảy tự nhiên toàn bề rộng — chỉ trình chiếu 16:9 mới dùng khối giới hạn bề rộng/căn giữa.

**Kết quả / số liệu:** Rà 14/14 bản khắc theo cấu trúc và loại nội dung. Detector layout của Impeccable và CLI Impeccable cho toàn thư mục `slides` đều trả `[]`; `git diff --check` sạch; số `<div>` mở/đóng đều là 93.

**Dang dở:**
- [ ] `bash scripts/quality-gate.sh` tiếp tục không chạy vì máy chưa cài WSL distribution; detector tương đương đã chạy trực tiếp từ npm cache.
- [ ] Chrome/Edge headless vẫn lỗi GPU, chưa có ảnh render tự động mới cho 14 bản. Cần kiểm tra mắt thường trong Chrome khi môi trường GPU/screenshot hoạt động.

**Điểm vào phiên sau:** Mở `slides/overview.html`, trình chiếu lần lượt 14 bản ở 1366×768, 1920×1080 và 1280×720; ưu tiên kiểm tra VII, VIII, X, XI, XIV là các bản nhiều chữ/bảng.

**Cảnh báo cho tool sau:** `dense-slide` là biến thể đọc xa nhưng nhiều nội dung, không phải lớp “thu nhỏ chữ”. Giữ khoảng cách đầy đủ giữa `data` và `body` theo DESIGN.md; nếu một bản tràn, sửa cấu trúc/nội dung riêng của bản đó trước khi hạ cả thang chữ.

## S-012 · 2026-07-24 12:19 · codex

**Mục tiêu phiên:** Thêm số liệu giả lập để minh hoạ trực quan trade-off risk–coverage ở bản khắc IV, với nhãn trung thực về trạng thái dữ liệu.

**Nhánh / commit:** `main` · `b97424b` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — thay sơ đồ khái niệm bằng biểu đồ 3 mốc số giả lập.
- `WORKLOG.md` — ghi nhận mục đích và giới hạn của biểu đồ.

**Quyết định & lý do:**
- Dùng mốc `coverage` 50% / 75% / 100% và 5 / 13 / 23 ca sai trên 100 ca giả lập — minh hoạ trực tiếp cho ý nghĩa của selective prediction thay vì chỉ vẽ đường cong trừu tượng.
- Nhãn chip, `aria-label` và chú thích đều ghi “dữ liệu giả lập, không phải kết quả dự án” — đây là điều kiện để số mô phỏng không bị hiểu nhầm là hiệu năng thật.
- Đường dữ liệu dùng Nét Khắc đứt, không dùng Hoàng Thổ — nét đứt có nghĩa “minh hoạ/chưa có dữ liệu” trong DESIGN.md; Hoàng Thổ vẫn dành riêng cho chú số và điều hướng.

**Kết quả / số liệu:** Detector layout của Impeccable và CLI Impeccable cho `slides` đều trả `[]`; `git diff --check` sạch; số thẻ `<div>` mở/đóng đều là 93.

**Dang dở:**
- [ ] Phần thay đổi chữ ở bản I–III (`Bảy/Tám` → `7/8`, rút dòng giới thiệu) là thay đổi chưa commit của người dùng. Đã được người dùng yêu cầu giữ nguyên, nhưng không được stage/commit cùng thay đổi này.
- [ ] `bash scripts/quality-gate.sh` không chạy được vì máy chưa cài WSL distribution; detector tương đương đã chạy trực tiếp từ npm cache.

**Điểm vào phiên sau:** Mở `slides/overview.html#4` và kiểm tra biểu đồ ở 16:9; nếu có kết quả nghiên cứu thật, thay toàn bộ 3 mốc giả lập và cập nhật chú thích/nguồn cùng lúc.

**Cảnh báo cho tool sau:** Không dùng số `5 / 13 / 23` hay biểu đồ này ở bất kỳ bề mặt nào như dữ liệu thật. Đây là mô phỏng được ghi nhãn rõ để giải thích khái niệm, không phải kết quả mô hình.


## S-013 · 2026-07-24 14:28 · codex

**Mục tiêu phiên:** Khắc phục quality gate trên Windows khi `bash.exe` trỏ vào WSL chưa có distro và `npx --yes` bị chặn ở npm cache.

**Nhánh / commit:** `main` · `47566d2` → *(commit đang chờ)*

**Đã động file:**
- `scripts/quality-gate.ps1` — mới; gate PowerShell tương đương bản Bash, không cần WSL.
- `.githooks/pre-commit` — ưu tiên gọi gate PowerShell trên Windows, fallback Bash trên máy có Bash thật.
- `AGENTS.md`, `docs/MULTI_TOOL_WORKFLOW.md` — cập nhật lệnh chuẩn Windows/Bash và đường dẫn hai script.
- `reports/W1_REPORT.md` — mới; báo cáo W1 về pha CT, feedback mentor và scope pivot sang MRI đa lớp.

**Quyết định & lý do:**
- Trên Windows, resolve binary Impeccable theo thứ tự `IMPECCABLE_BIN` → `node_modules/.bin` → npm npx cache và gọi trực tiếp — tránh `npx --yes` cố tải lại package rồi vướng quyền cache/network.
- Giữ `quality-gate.sh` cho macOS/Linux/Git Bash thật; không cài WSL chỉ để chạy một gate của repo.
- Script PowerShell chỉ dùng ASCII ở chuỗi runtime để Windows PowerShell 5 không diễn giải UTF-8 không BOM theo code page cũ.

**Kết quả / số liệu:** `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1` PASS (Impeccable trên `slides` và `reports`); `git hook run pre-commit` PASS ở chế độ staged.

**Dang dở:**
- [ ] Lệnh cũ `bash scripts/quality-gate.sh` trên máy này vẫn không dùng được vì WSL chưa có distro; tài liệu đã đổi sang lệnh PowerShell chuẩn. Không cần cài WSL để làm việc với repo.
- [ ] `slides/overview.html` là thay đổi chưa commit của người dùng; không stage/commit cùng phiên này.

**Điểm vào phiên sau:** dùng `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1` trước commit; nếu cache Impeccable chuyển chỗ, đặt `IMPECCABLE_BIN` tới binary cục bộ rồi chạy lại.

**Cảnh báo cho tool sau:** `reports/W1_REPORT.md` là report tóm tắt; số 5/13/23 trên slide vẫn là mock, không được chép thành kết quả. Không dùng `npx --yes impeccable` làm đường gate chuẩn trên Windows này.


## S-014 · 2026-07-24 14:33 · codex

**Mục tiêu phiên:** Rà soát định dạng `reports/W1_REPORT.md` theo phản hồi người dùng.

**Nhánh / commit:** `main` · `9fa2ba5` → *(commit đang chờ)*

**Đã động file:**
- `reports/W1_REPORT.md` — gộp các đoạn văn bị xuống dòng giữa câu, bỏ toàn bộ dấu gạch ngang dài, thêm tên người thực hiện Hoàng Đức Trường trước ngày chốt.
- `WORKLOG.md` — ghi nhận phiên chỉnh report.

**Quyết định & lý do:**
- Dùng một dòng Markdown cho mỗi đoạn văn để không cắt từ/câu trong file nguồn; trình render vẫn tự ngắt dòng theo khung đọc.
- Dùng dấu hai chấm, chấm phẩy hoặc gạch nối thông thường khi cần thay cho dấu gạch ngang dài theo yêu cầu người dùng.
- Dùng `<br>` sau tên người thực hiện để tên luôn hiển thị trên ngày chốt mà không cần khoảng trắng cuối dòng.

**Kết quả / số liệu:** Không còn ký tự `—` trong W1 report; PowerShell quality gate PASS.

**Dang dở:**
- [ ] `slides/overview.html` vẫn là thay đổi chưa commit của người dùng; không stage/commit cùng phiên này.

**Điểm vào phiên sau:** Tiếp tục cập nhật W1 report khi có kết quả MRI thật; giữ phân biệt rõ số mock và số thực nghiệm.

**Cảnh báo cho tool sau:** Không chèn lại hard-wrap giữa từ trong các đoạn văn của W1 report; không dùng số 5/13/23 như kết quả dự án.


## S-015 · 2026-07-24 14:35 · codex

**Mục tiêu phiên:** Xác nhận và commit các chỉnh sửa nội dung chưa commit trong `slides/overview.html` theo yêu cầu người dùng.

**Nhánh / commit:** `main` · `9fa2ba5` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — stage các chỉnh sửa đã được người dùng xác nhận: đổi cách ghi số lớp/số thì sang chữ số, rút gọn mô tả intro/dataset và nhãn web app.
- `WORKLOG.md` — ghi nhận phạm vi đã được xác nhận.

**Quyết định & lý do:**
- Người dùng đã xác nhận toàn bộ diff slide; thay đổi chỉ rút gọn ngôn ngữ và không thay đổi tuyên bố khoa học, nguồn trích dẫn hay số liệu minh hoạ.

**Kết quả / số liệu:** Quality gate PowerShell đã PASS trước khi stage; slide, W1 report và worklog sẽ được commit/push cùng nhau theo xác nhận người dùng.

**Dang dở:**
- [ ] Không có việc treo cho phạm vi commit này.

**Điểm vào phiên sau:** Mở `slides/overview.html` trong Chrome nếu cần kiểm tra trực quan các câu rút gọn ở bản khắc I–V.

**Cảnh báo cho tool sau:** Các số 5/13/23 trong slide IV vẫn là dữ liệu minh hoạ, không phải kết quả dự án.


## S-016 · 2026-07-24 14:51 · codex

**Mục tiêu phiên:** Bổ sung timeline W1 và commit/push toàn bộ chỉnh sửa đang có theo xác nhận người dùng.

**Nhánh / commit:** `main` · `db522d7` → *(commit đang chờ)*

**Đã động file:**
- `reports/W1_REPORT.md` — thêm mốc 16–18/07/2026: nhận danh sách đề tài, phân tích/lựa chọn đề tài và phân tích ban đầu; giữ toàn bộ chỉnh sửa nội dung hiện có của người dùng.
- `WORKLOG.md` — ghi nhận phạm vi commit tổng hợp.

**Quyết định & lý do:**
- Người dùng yêu cầu commit/push toàn bộ thay đổi hiện tại, nên mọi chỉnh sửa đang có trong W1 report được giữ nguyên và đưa vào cùng commit.
- Mốc 16–18/07 được đặt đầu timeline để trình tự tiến độ bắt đầu từ giai đoạn nhận/lựa chọn đề tài, trước khi dựng pipeline CT.

**Kết quả / số liệu:** Không có số liệu nghiên cứu mới; timeline W1 đầy đủ hơn về các bước khởi đầu.

**Dang dở:**
- [ ] Không có việc treo trong phạm vi commit này.

**Điểm vào phiên sau:** Cập nhật W1 report khi có EDA/baseline MRI thật; giữ rõ ranh giới giữa kế hoạch và kết quả thực nghiệm.

**Cảnh báo cho tool sau:** Chỉ thay số mock trên slide khi có kết quả thực nghiệm thật và nguồn/CI tương ứng.


## S-017 · 2026-07-24 15:39 · claude-code

**Mục tiêu phiên:** Lập kế hoạch chi tiết 5 tuần còn lại + plan làm việc W2, và dọn repo (chuyển Spec Sheet + Plan vào `docs/`).

**Nhánh / commit:** `main` · `db522d7` → *(commit đang chờ)*

**Đã động file:**
- `docs/plan.md` — TẠO: kế hoạch chi tiết W2–W6, tái-định-mốc (W1 thực tế là CT+scope+spec nên nén lộ trình MRI vào 5 tuần); ranh giới sprint chốt lại: Sprint 1=W2, Sprint 2=W3–W4, Sprint 3=W5–W6.
- `docs/W2_plan.md` — TẠO: plan làm việc Tuần 2 theo ngày (GATE data ngày 0 → src/ + EDA + cache + split khoá + leakage test + baseline 1 fold), mỗi task có DoD + cách verify.
- `docs/MRI_Classification_Spec_Sheet.md` — `git mv` từ root (giữ lịch sử).
- `docs/liver_mri_3d_classification_plan.md` — `git mv` từ root (giữ lịch sử).
- `AGENTS.md` — cập nhật link §1, bảng doc-map §2 (thêm dòng `docs/plan.md`, `docs/W2_plan.md`), cây thư mục §4 (2 file giờ nằm dưới `docs/`).
- `PRODUCT.md` — cập nhật 2 link mục *Evidence on Hand* sang `docs/`.

**Quyết định & lý do:**
- **Không xóa Spec Sheet + Plan** — review cho thấy cả hai vẫn là nguồn sự thật (chốt khoa học + project doc chiến lược); `docs/plan.md` chỉ *triển khai* chúng, không thay thế. Theo yêu cầu người dùng, chuyển vào `docs/` để dọn root.
- Đảo quyết định hoãn ở WORKLOG dòng 152 (phiên trước để nguyên ở root vì sợ gãy link) — giờ làm được vì đã cập nhật toàn bộ tham chiếu (AGENTS.md, PRODUCT.md, docs/plan.md) cùng lúc.
- **Không sửa `prompt/`** (slides_overview.md, plan_research.txt) — là prompt gốc lịch sử, giữ path cũ có chủ đích, không phải lỗi.
- **Không tự commit** — `WORKLOG.md` + `reports/W1_REPORT.md` đang là việc staged treo của Codex (S-016, "commit đang chờ"); để người dùng quyết gộp/tách phạm vi.

**Kết quả / số liệu:** Không có số liệu nghiên cứu. Quality gate PowerShell: **PASS** (ruff SKIP — src/ chưa tồn tại).

**Dang dở:**
- [ ] Chưa commit — chờ người dùng quyết cách gộp với việc treo của Codex (S-016).

**Điểm vào phiên sau:** Vào W2 theo `docs/W2_plan.md` — GATE ngày 0: xác nhận quyền truy cập LLD-MMRI trước khi dựng `src/`; nếu chưa có → bàn CT fallback (GNG-1).

**Cảnh báo cho tool sau:** Spec Sheet + Plan **đã chuyển sang `docs/`**, không còn ở root. `prompt/` vẫn trỏ path cũ (lịch sử). `git status` còn việc staged của Codex chưa commit — đừng tưởng là rác.


## S-018 · 2026-07-24 16:05 · claude-code

**Mục tiêu phiên:** Review dataset LLD-MMRI trên Kaggle (`marcohoang/lldmmridataset`) xem đã sẵn sàng cho hướng phân loại mới chưa, và cập nhật `docs/W2_plan.md` theo phát hiện.

**Nhánh / commit:** `main` · `2de3f39` → *(commit đang chờ)*

**Đã động file:**
- `docs/W2_plan.md` — thêm §0 "Kết quả review dataset"; đổi GATE ngày 0 (data access = ✅, gate mới = đủ mảnh cho classification); sửa T1.2 (reader chỉ đọc `images/` + annotation, bỏ `labels/`+`.cache/`), T1.3 (split từ file official), T2.1 (gate geometry ảnh↔annotation), T3.2 (gộp bbox 2D→3D, crop full-volume vì không có patch cắt sẵn), T4.1 (test-104 official khoá kín + 5-fold trên 394); cập nhật DoD + "Điểm phải hỏi" + "Câu hỏi cần chốt".

**Quyết định & lý do:**
- Dataset = bản raw `wanglab/LLD-MMRI-MedSAM2` (HuggingFace) dump lên Kaggle (~83.7GB, private, v1). Đóng gói cho **segmentation** (kèm `labels/` mask MedSAM2) nhưng **giữ nguyên annotation phân loại gốc** `LLD_MMRI_Annotation.json`: 7 lớp + Benign[0,2,4,5]/Malignant[1,3,6] (khớp Spec Sheet 100%) + bbox 2D per-slice.
- **Giữ official 316/78/104** (test-104 khoá kín, 5-fold trên 394) theo khuyến nghị — đúng Spec Sheet §2, so được benchmark SOTA. Phương án đã loại: tự chia hoàn toàn (mất tính so-benchmark) — chỉ dùng làm fallback.
- Xác nhận cơ chế split official (đọc code repo LMMMEng): `data/classification_dataset/labels/{train,val}_fold*.txt` (`np.loadtxt`, `patient_id  class`); `gene_cross_val.py` chỉ sinh fold, KHÔNG định nghĩa official split → file split đến từ bản classification gốc, **không có trong bản wanglab**.

**Kết quả / số liệu:** Không có số liệu nghiên cứu. Đã cài `kaggle` CLI (chỉ để inspect, KHÔNG vào requirements) + tải `README.md`, `__huggingface_repos__.json`, `LLD_MMRI_Annotation.json` về scratchpad (ngoài repo). Quality gate: (chạy sau khi ghi entry).

**Dang dở:**
- [ ] **Định vị file split official** (`train/val/test`) từ bản LLD-MMRI classification gốc — CHẶN test-104 khoá kín.
- [ ] Verify geometry ảnh↔annotation (bản MedSAM2 có thể đã resample) — gate EDA T2.1.

**Điểm vào phiên sau:** Vào W2 ngày 1 — scaffold `src/utils` + `src/data/dataset.py` (đọc `lld/images/` + `LLD_MMRI_Annotation.json`, bỏ `labels/`+`.cache/`). Chờ người dùng chỉ đường dẫn file split official (Câu hỏi #1 trong W2_plan).

**Cảnh báo cho tool sau:** Dataset Kaggle là bản **SEGMENTATION** (wanglab MedSAM2) — TUYỆT ĐỐI không nạp `lld/labels/` (mask) vào classification. Không có **patch cắt sẵn**, chỉ full-volume → crop bằng bbox. bbox là **2D per-slice**, phải gộp theo `slice_idx` thành ROI 3D.


## S-019 · 2026-07-24 16:25 · claude-code

**Mục tiêu phiên:** Xác minh nguồn có official split không, và chốt chiến lược split cho hướng mới.

**Nhánh / commit:** `main` · `e7a6f6c` → *(commit đang chờ)*

**Đã động file:**
- `docs/MRI_Classification_Spec_Sheet.md` — §2 Split: thay "dùng split challenge 316/78/104" bằng **split tự tạo mức bệnh nhân** (nguồn thực nhận không có official split), ghi rõ đánh đổi + đặc điểm bản dữ liệu (chỉ full-volume, kèm mask MedSAM2).
- `docs/W2_plan.md` — flip 7 chỗ (§0 quyết định, GATE, T1.3, T4.1, DoD, "Điểm phải hỏi", "Câu hỏi cần chốt") sang **split tự tạo = primary**; GATE ngày 0 chuyển "ĐÃ THÔNG".

**Quyết định & lý do:**
- **Split tự tạo mức bệnh nhân** (tách ~104 held-out test + 5-fold stratified trên 498, frozen+commit). Lý do: nguồn `wanglab/LLD-MMRI-MedSAM2` **không kèm official split 316/78/104** — xác minh qua **HF API siblings** (chỉ `.gitattributes`, `LLD_MMRI_Annotation.json`, `README.md` + ~4000 nii.gz) và **annotation JSON** (top-key chỉ `Annotation_info`+`Category_info`, không trường split nào); repo LMMMEng cũng không public split (chỉ có `gene_cross_val.py` sinh fold). Người dùng đã chọn phương án này (câu hỏi trực tiếp). Đổi quyết định đã chốt Spec Sheet §2 → có phê duyệt người dùng, đã ghi diff vào Spec Sheet.
- Đánh đổi: **mất so trực tiếp leaderboard test-104**. Chấp nhận vì headline dự án là calibration/selective, không đua accuracy.
- Phương án đã loại: đăng ký bản LLD-MMRI classification gốc để lấy official split — thêm bước + chờ duyệt, không tương xứng khi không đua leaderboard.

**Kết quả / số liệu:** Không có số liệu nghiên cứu. Ghi chú kỹ thuật: `3D_box` trong annotation **null toàn bộ** (0/3984) → vẫn phải gộp `2D_box` per-slice thành ROI 3D (T3.2 giữ nguyên).

**Dang dở:**
- [ ] Verify geometry ảnh↔annotation (bản MedSAM2 có thể đã resample) — gate EDA T2.1.

**Điểm vào phiên sau:** W2 ngày 1 — scaffold `src/utils` + `src/data/dataset.py` (đọc `lld/images/` + `LLD_MMRI_Annotation.json`, bỏ `labels/`+`.cache/`). Khâu data đã hết blocker.

**Cảnh báo cho tool sau:** Split là **TỰ TẠO**, không phải official challenge — KHÔNG báo cáo so với leaderboard test-104 của SOTA. `splits/test_heldout.json` là held-out khoá kín, chạm đúng 1 lần (AGENTS.md §3.4).


## S-020 · 2026-07-24 16:50 · claude-code

**Mục tiêu phiên:** Khai thác PDF challenge (`docs/LiverLesion…pdf`) + repo LMMMEng, cập nhật Spec Sheet + W2_plan.

**Nhánh / commit:** `main` · `45db1c2` → *(commit đang chờ)*

**Đã động file:**
- `docs/MRI_Classification_Spec_Sheet.md` — §2: thêm **phân bố lớp thật** (HCC 157 áp đảo … FNH 46, imbalance vừa phải — đính chính "áp-xe/FNH cực hiếm"); ghi **registration bắt buộc** (các thì khác geometry: non-contrast coronal, DWI thô, đa máy 1.5T/3T); thêm **nhãn = pathology report** + **license CC BY-NC-ND** + note bản wanglab thực nhận.
- `docs/W2_plan.md` — §0 thêm block "Bổ sung từ PDF challenge" (phân bố lớp, geometry, license); T2.1 (đối chiếu phân bố official + kiểm orientation); T4.1 (split tự tạo **cùng protocol official** 316/78/104 + stratified); T3.3 (Kaggle Dataset **private** + không phát tán cache — license).

**Quyết định & lý do:**
- Trả lời câu split: **vẫn tự chia** — PDF cho số/lớp/tập (316/78/104, stratified) nhưng **KHÔNG có patient_id** nên không tái lập official được. Khai thác được: làm split tự tạo **cùng protocol** (sizes + stratified) → so setup, khác patient.
- Đính chính giả định imbalance: HCC áp đảo (157), FNH ít nhất (46), HCC:FNH ≈ 3.4:1 — **vừa phải, không long-tail** → nhẹ lo ngại lớp hiếm ở W4.
- Registration nâng từ "nên" lên **bắt buộc**: PDF xác nhận các thì khác orientation/độ phân giải.
- License **CC BY-NC-ND**: không đẩy cache/bản phái sinh công khai; repro pack chỉ code + split IDs + config.

**Kết quả / số liệu:** Không có số liệu nghiên cứu. Nguồn: PDF challenge 14 trang (trích bằng PyMuPDF vào scratchpad) + repo LMMMEng/LLD-MMRI2023.

**Dang dở:**
- [ ] Verify geometry ảnh↔annotation (gate EDA T2.1) — nay có thêm cảnh báo orientation từ PDF.

**Điểm vào phiên sau:** W2 ngày 1 — scaffold `src/` + reader. Split: tự tạo cùng protocol 316/78/104 stratified.

**Cảnh báo cho tool sau:** Phân bố lớp official ở W2_plan §0 (dùng cho stratify). Split tự tạo **cùng protocol nhưng khác patient** → KHÔNG so trực tiếp leaderboard. License **CC BY-NC-ND** → Kaggle Dataset private, repro pack không kèm ảnh/cache.


## S-021 · 2026-07-24 17:20 · claude-code

**Mục tiêu phiên:** Tìm official split trên internet, tái lập + verify, đảo quyết định sang official split, lưu `splits/`.

**Nhánh / commit:** `main` · `09deaf9` → *(commit đang chờ)*

**Đã động file:**
- `splits/` — **TẠO 12 file** (KHOÁ, bất biến): `labels_trainval.txt` (394), `train_fold{1..5}.txt` + `val_fold{1..5}.txt` (5-fold official), `test_official.txt` (104), `README.md` (provenance + verify + cách map ID).
- `docs/MRI_Classification_Spec_Sheet.md` — §2 Split: **đảo lại sang official 316/78/104 tái lập** (revert quyết định S-019 "tự chia").
- `docs/W2_plan.md` — §0/GATE/T4.1/T1.3/DoD/"Điểm phải hỏi"/"Câu hỏi chốt" → official split tái lập; T4.1 đổi từ "sinh split" thành "nạp + validate".

**Quyết định & lý do:**
- **Dùng official split 316/78/104 (đảo S-019).** Tái lập: `labels_trainval.txt` (394 train+val) từ repo đội thi **ZHEGG/miccai2023** (`data/trainval_labels/`); **test-104 = 498 (annotation JSON) − 394**. Verify: phân bố lớp test + trainval **khớp PDF official 100% (7/7 lớp)**; class ZHEGG vs `Category_info` **0 mismatch**; trainval∩test=∅, union=498.
- Khôi phục **so benchmark trực tiếp với SOTA** — lý do đảo quyết định trước (khi đó tưởng official split không lấy được).
- ID map theo **chữ số** (annotation có 16/498 key dạng `MR-xxxxxx`, còn lại `MRxxxxxx`; label `MRxxxxxx`). Lưu split theo key annotation.

**Kết quả / số liệu:** test_official dist = HCC32/u máu16/ICC12/áp-xe12/di căn11/nang11/FNH10 (=104), khớp PDF. Nguồn: [ZHEGG/miccai2023](https://github.com/ZHEGG/miccai2023).

**Dang dở:**
- [ ] Verify geometry ảnh↔annotation (gate EDA T2.1) — vẫn treo.

**Điểm vào phiên sau:** W2 ngày 1 — scaffold `src/` + reader; `make_splits.py` chỉ **nạp + validate** `splits/` (không sinh ngẫu nhiên).

**Cảnh báo cho tool sau:** `splits/` **KHOÁ** — quality gate chặn thay đổi (cần `ALLOW_SPLIT_CHANGE=1`, chỉ dùng lần tạo đầu này). `splits/test_official.txt` = held-out chạm **đúng 1 lần** (AGENTS.md §3.4). Map ID luôn **chuẩn hoá theo chữ số**.


## S-022 · 2026-07-24 17:55 · claude-code

**Mục tiêu phiên:** Bắt đầu W2 ngày 1 (docs/W2_plan.md) — scaffold `src/utils` + `src/data` (annotation/splits/images/dataset/manifest) + test chống leakage.

**Nhánh / commit:** `main` · `b844c15` → *(commit đang chờ)*

**Đã đụng file:**
- `pyproject.toml` — TẠO: cấu hình ruff (line-length 100, target py311) + pytest.
- `requirements.txt` — TẠO: pin version stack train (numpy/pandas/PyYAML/SimpleITK/nibabel/sklearn/scipy/torch/monai) + ruff/pytest.
- `configs/data.yaml` — TẠO: cấu hình data_root (qua env `LLDMMRI_DATA_ROOT`), map 8 pha (tên annotation ↔ token file), splits_dir.
- `src/utils/{seed,ids,io,logging}.py` — TẠO: `set_seed()` một chỗ duy nhất; `normalize_pid()` chuẩn hoá ID theo chữ số; đọc YAML/JSON/file split; `CsvLogger` flush mỗi dòng (Kaggle session ngắt bất cứ lúc nào).
- `src/data/{taxonomy,annotation,images,splits,dataset,build_manifest}.py` — TẠO: đọc annotation gốc (bỏ `labels/` mask + `.cache/`), gộp bbox 2D→3D theo slice_idx, quét ảnh map `(patient_key, phase_token)→path`, **nạp + validate** (không sinh) split official ở `splits/`, dataset reader (torch import lười), sinh `data/manifest.csv`.
- `tests/{test_ids,test_no_leakage,test_annotation,test_images,test_seed}.py` — TẠO: 27 test, gồm đủ leakage test bắt buộc (trainval∩test=∅, mỗi BN val đúng 1 fold/5, test-104 không lọt fold nào).
- `AGENTS.md` §6 — cập nhật bảng lệnh (validate split, build_manifest, pytest, ruff → "sẵn sàng").

**Quyết định & lý do:**
- `T4.1` đổi vai trò `make_splits` thành **validate-only** — vì split đã official + tái lập (S-021), không còn sinh ngẫu nhiên.
- Tách `dataset.py` thành `load_sample()` thuần numpy/nibabel + `LLDMMRIDataset` (torch import lười trong `__init__`) — cho phép toàn bộ `src/data` import được dù máy chưa cài torch/monai (đã verify).
- `test_annotation.py` dùng **fixture JSON tối giản** (không phải file 18MB thật) — test logic độc lập với việc có data thật trên máy hay không.

**Kết quả / số liệu:** `pytest -q` → **27 passed**. `ruff check` + `ruff format --check` → pass (0 lỗi). `Splits('splits').validate()` chạy trên `splits/` thật → pass (394/104/498, 5 fold, không leak).

**Dang dở:**
- [ ] Chưa test `build_manifest.py` / `load_sample()` end-to-end trên data thật (máy này chưa có `LLDMMRI_DATA_ROOT`) — cần chạy trên Kaggle hoặc máy có mount data.
- [ ] Gate geometry ảnh↔annotation (EDA, T2.1) vẫn treo — việc tiếp theo.
- [ ] `ruff` cài qua pip không nằm trên PATH hệ thống → quality-gate.ps1 tự SKIP bước ruff (không phải FAIL). Đã tự chạy `python -m ruff` thủ công và pass. Cân nhắc thêm Scripts dir vào PATH hoặc sửa gate dùng `python -m ruff` — chưa làm vì ngoài phạm vi phiên.

**Điểm vào phiên sau:** W2 ngày 2 (EDA) — viết `notebooks/01_eda.ipynb`, chạy `build_manifest` trên data thật, và **GATE geometry bắt buộc** (đối chiếu shape/spacing/orientation ảnh thật với annotation, overlay bbox lên slice) trước khi tin ROI-crop.

**Cảnh báo cho tool sau:** `src/data/build_manifest.py` và `LLDMMRIDataset` chưa chạy thử trên data thật — logic đã unit-test qua fixture nhưng chưa end-to-end. `ruff` không trên PATH ở máy này (dùng `python -m ruff`).


## S-023 · 2026-07-24 18:15 · claude-code

**Mục tiêu phiên:** Phát hiện + sửa bug `.gitignore` khiến `src/data/` không bao giờ được commit ở S-022.

**Nhánh / commit:** `main` · `49c2bde` → `9240aa2`

**Đã đụng file:**
- `.gitignore` — neo `data/` → `/data/`, `raw/` → `/raw/` (chỉ khớp thư mục gốc repo).
- `src/data/{__init__,annotation,build_manifest,dataset,images,splits,taxonomy}.py` — **commit lần đầu thật sự** (trước đó bị nuốt).

**Quyết định & lý do:**
- Sau khi push S-022, kiểm `git status` phát hiện **rỗng bất thường** dù `src/data/` có 7 file trên đĩa. Nguyên nhân: `.gitignore` dòng `data/` (không neo `/`) khớp **mọi thư mục tên "data" ở mọi cấp** — nuốt cả `src/data/`. Commit `49c2bde` ("scaffold src/data...") trên thực tế **không hề chứa** `src/data/*.py`, dù message nói có.
- Sửa bằng neo `/data/` + `/raw/` về gốc — đã verify: root `data/` **vẫn ignore tuyệt đối như cũ** (test tạo `data/manifest.csv`, vẫn bị chặn), chỉ dừng lan sang thư mục con trùng tên. Đây là bug fix, không phải "bỏ ignore dữ liệu bệnh nhân" (AGENTS.md §10) — phạm vi bảo vệ dữ liệu bệnh nhân không đổi.
- File không bị mất (vẫn trên đĩa suốt), nhưng đã có nguy cơ thật: nếu máy bị xoá/mất trước khi phiên sau phát hiện, toàn bộ `src/data/` (annotation, splits, images, dataset, build_manifest, taxonomy) sẽ biến mất không dấu vết.

**Kết quả / số liệu:** `git ls-files src/` xác nhận đủ 13 file (`src/__init__.py` + 5 `utils/*` + 7 `data/*`); `tests/` đủ 6 file. `pytest -q` 27 passed, `ruff check`/`ruff format --check` pass. Quality gate PASS.

**Dang dở:** (không có gì mới ngoài các mục đã ghi ở S-022 — EDA/gate geometry vẫn là việc tiếp theo).

**Điểm vào phiên sau:** Không đổi so với S-022 — W2 ngày 2 (EDA + gate geometry).

**Cảnh báo cho tool sau:** **Luôn `git ls-files <dir>` (không chỉ `ls` + `git status`) để xác nhận file thực sự được track**, đặc biệt sau khi tạo thư mục mới trùng tên với rule trong `.gitignore` (data/raw/checkpoints/artifacts...). `git add` không báo lỗi khi ignore âm thầm loại bỏ file — commit "thành công" vẫn có thể thiếu file.


## S-024 · 2026-07-24 18:40 · codex

**Mục tiêu phiên:** Rút `slides/overview.html` thành overview 11 slide độc lập cho hướng MRI 3D đa pha hiện tại.

**Nhánh / commit:** `main` · `39f7568` → *(commit đang chờ)*

**Đã đụng file:**
- `slides/overview.html` — rút 14 xuống 11 bản khắc; gộp taxonomy–phase; thay biểu đồ risk–coverage mock bằng luồng trustworthiness không số; viết lại dataset, protocol, SOTA, đóng góp, đầu ra và nguồn.
- `scripts/quality-gate.{ps1,sh}` — chỉ truyền các thư mục Python đang tồn tại vào `ruff`, tránh fail khi `webapp/` chưa được tạo.
- `WORKLOG.md` — append entry này.

**Quyết định & lý do:**
- Deck chỉ giới thiệu hướng MRI hiện tại: phân loại 7 lớp trên MRI 3D đa pha, calibration và selective prediction — để phù hợp mục đích overview 10 phút, không lẫn lịch sử scope, CT/binary hay feedback mentor.
- Giữ Duke ở vai trò OOD probe không có nhãn loại tổn thương; external coarse-label chỉ là đề xuất cần audit protocol — để không suy diễn thành external classification đã chạy.
- Không giữ số 5/13/23 hay trục risk–coverage giả lập — sơ đồ mới có nét đứt và nhãn “chưa có dữ liệu dự án”.
- Sửa cả PowerShell và Bash gate — cùng một điều kiện lint phải cho kết quả nhất quán khi project chưa có `webapp/`.

**Kết quả / số liệu:** 11 slide; footer liên tục 1/11 đến 11/11; `impeccable detect` và `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1` đều PASS. Không có kết quả train/eval MRI được thêm vào deck.

**Dang dở:**
- [ ] Chưa có screenshot QA trực tiếp tại 1280×720, 1366×768 và 1920×1080: browser automation bị policy chặn mở `file://` local; không dùng workaround. Cấu trúc responsive và detector đã được kiểm tra tĩnh.

**Điểm vào phiên sau:** Mở `slides/overview.html` trong trình duyệt local của người dùng để xác nhận trực quan ba viewport trước khi dùng deck trình bày.

**Cảnh báo cho tool sau:** Đây là overview hướng MRI, không phải progress report: không thêm lịch sử đổi scope, feedback mentor, binary CT, scaffold/code hoặc kết quả chưa xác minh. Mọi số liệu minh hoạ mới phải tránh trục/số mock và được gắn nhãn rõ.


## S-025 · 2026-07-24 18:50 · codex

**Mục tiêu phiên:** Redesign `slides/overview.html` cho mentor/reviewer hỗn hợp: kể câu chuyện bằng MRI đa thì thật và sơ đồ, thay cho deck thiên về chữ và visual atlas.

**Nhánh / commit:** `main` · `39f7568` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — giữ 11 slide nhưng thay toàn bộ visual language sang dark “signal flow”; bổ sung ảnh MRI đa thì công khai, giải thích `defer` bằng ngôn ngữ phổ thông, luồng model, dataset coverage, SOTA, calibration, protocol, đóng góp, ứng dụng second reader, và output dự kiến không số.
- `slides/assets/cmir-8-107-f5.jpg` — TẠO: ảnh MRI đa thì công khai của Nils Albiin, chỉ dùng minh hoạ, không phải dữ liệu LLD-MMRI.
- `slides/assets/ATTRIBUTION.md` — TẠO: nguồn Wikimedia Commons, tác giả, thay đổi khi dùng lại và giấy phép CC BY 2.5.
- `WORKLOG.md` — append entry này.

**Quyết định & lý do:**
- Người xem không có nền tảng AI/y tế cần nhìn thấy quan hệ “nhiều thì MRI → model → các khả năng → cần bác sĩ xem lại” trước khi gặp thuật ngữ calibration và selective prediction. `defer` được định nghĩa ngay tại lần xuất hiện đầu tiên là model chưa đủ chắc để tự trả lời.
- Không dùng ảnh LLD-MMRI vì không nên tái phân phối dữ liệu bệnh nhân. Ảnh công khai được gắn attribution cả trên slide và trong file asset; output/heatmap là minh hoạ bố cục, không phải kết quả dự án.
- Giữ deck ở phạm vi overview hướng MRI hiện tại; không thêm feedback mentor, CT/binary, lịch sử đổi scope hay metric train/eval chưa có.

**Kết quả / số liệu:** 11 slide (01/11–11/11); `impeccable detect slides` và `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1` đều PASS. Quality gate dùng binary Impeccable cache cục bộ 3.3.1 và không còn warning. Không có metric thực nghiệm MRI mới.

**Dang dở:**
- [ ] Chưa có screenshot QA trực tiếp ở 1280×720, 1366×768 và 1920×1080 vì browser automation bị policy chặn mở `file://` local; không dùng workaround. Đã kiểm tra responsive CSS, 11 slide, keyboard/hash/print theo mã tĩnh và detector.

**Điểm vào phiên sau:** Mở `slides/overview.html` bằng trình duyệt local của người dùng để duyệt trực quan ba viewport trước buổi trình bày.

**Cảnh báo cho tool sau:** Ảnh `cmir-8-107-f5.jpg` là asset CC BY 2.5; phải giữ attribution trong `slides/assets/ATTRIBUTION.md` và slide nguồn. Duke chỉ là OOD probe, không là external classification test; mọi output mock phải tiếp tục ghi rõ là minh hoạ không có dữ liệu dự án.


## S-026 · 2026-07-24 19:00 · codex

**Mục tiêu phiên:** Cân lại bố cục `slides/overview.html` để đọc từ xa hơn, sửa va chạm ảnh/chữ ở slide mở đầu và khôi phục mốc phần theo tiến trình thuyết trình.

**Nhánh / commit:** `main` · `a071e00` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — tăng thang chữ và vùng nội dung từ 73 lên 86 đơn vị tỷ lệ; giảm khoảng trống thân slide; thêm 11 thanh mục lục tĩnh; tách hero slide 1 thành hai cột trong CSS grid; thêm ngoại lệ chữ nguồn nhỏ hơn ở slide 11.
- `WORKLOG.md` — append entry này.

**Quyết định & lý do:**
- Thanh mục lục có 5 phần: Bài toán (1–3), Dataset (4), SOTA (5–7), Ứng dụng (8–10), Nguồn (11). Mỗi slide có đúng một mục active, hiển thị bằng nhãn chữ sáng, chữ đậm và đoạn kẻ 2px để không chỉ dựa vào màu.
- Hero không còn dùng ảnh đặt `position:absolute`; copy và MRI được đặt ở hai cột độc lập. Vì vậy ảnh không thể lấn lên tiêu đề ở các viewport trình chiếu.
- Không đổi thông tin khoa học, số liệu công bố, nguồn, attribution, RUO hay các hành vi hash/keyboard/print.

**Kết quả / số liệu:** `impeccable detect --scope layout slides/overview.html` trả về rỗng; quality gate PowerShell PASS; kiểm tra cấu trúc PASS (11 slide, 11 section-nav, 11 `aria-current="step"`, không còn legacy absolute hero).

**Dang dở:**
- [ ] Chrome headless hiện trả mã thoát 0 nhưng không tạo screenshot ở thư mục tạm của môi trường, nên chưa có ảnh render tự động tại 1280×720, 1366×768 và 1920×1080. CSS đã được rà tĩnh theo các breakpoint; cần mở local bằng Chrome thông thường để review quang học cuối nếu muốn chốt cho buổi trình bày.

**Điểm vào phiên sau:** Mở slide 1, 5 và 11 bằng trình duyệt local ở ba viewport để xác nhận trực quan typography và bảng nguồn sau khi tăng cỡ chữ.

**Cảnh báo cho tool sau:** Giữ thanh mục lục tĩnh trong HTML để nó hiện đúng cả khi in; không chuyển sang sinh bằng JavaScript. Nếu sửa mapping, phải duy trì đúng một `aria-current="step"` trên mỗi slide.


## S-027 · 2026-07-24 19:15 · codex

**Mục tiêu phiên:** Rút gọn chú thích minh hoạ thừa ở slide 3/6 và sửa khoảng cách trong hai khối so sánh calibration ở slide 6.

**Nhánh / commit:** `main` · `ffc5cf4` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — bỏ nhãn “Sơ đồ khái niệm, chưa có dữ liệu kết quả của dự án” ở slide 3 và “Minh hoạ khái niệm, không mang số liệu dự án” ở slide 6; đặt badge Model A/B trên dòng riêng, thêm khoảng cách dưới badge và buộc tiêu đề là block riêng.
- `WORKLOG.md` — append entry này.

**Quyết định & lý do:** Hai sơ đồ đã tự diễn đạt đủ bằng tiêu đề, nhãn và nội dung xung quanh nên bỏ chú thích lặp lại. Trong slide 6, badge và tiêu đề trước đây nằm chung inline flow, khiến title chạm badge; layout mới tách ba lớp rõ ràng: badge → tiêu đề → diễn giải.

**Kết quả / số liệu:** `impeccable detect --scope layout slides/overview.html` trả về rỗng; kiểm tra tĩnh xác nhận hai nhãn đã bị xoá và quy tắc layout mới có mặt.

**Cảnh báo cho tool sau:** Giữ `display:block` cho `.compare-item strong` và khoảng cách dưới `.compare-item .tag`; nếu trả chúng về inline, lỗi dính badge/title ở slide 6 sẽ quay lại.


## S-024 · 2026-07-24 19:10 · claude-code

**Mục tiêu phiên:** W2 ngày 2 — dựng EDA + GATE GEOMETRY, và **đường ống Kaggle** (vì máy local không có data 83.7GB).

**Nhánh / commit:** `main` · `39f7568` → *(commit đang chờ)*

**Đã đụng file:**
- `src/data/eda.py` — TẠO: `class_distribution`, `phase_geometry` + `geometry_summary_by_phase`, `bbox_stats` (quy đổi mm), `recommend_crop_size`, `missing_phase_report`.
- `src/data/geometry_gate.py` — TẠO: gate 3 tầng (spacing header vs annotation · bbox trong biên + suy ra axis order · overlay slice cho mắt người). `GateReport.passed` = False khi rỗng (tránh pass giả lúc thiếu data).
- `src/data/annotation.py` — thêm `raw_entries()` + `phase_entry()`; `bbox3d()` refactor dùng `phase_entry` (bỏ vòng lặp trùng).
- `notebooks/01_eda.ipynb` — TẠO: 20 cell (12 code), lớp mỏng gọi `src/`, chạy được cả Kaggle lẫn local, output đã strip.
- `docs/KAGGLE_WORKFLOW.md` — TẠO: quy trình clone repo vào Kaggle → mount data → chạy → **xuất output thành Kaggle Dataset có version** (2 cách), phương án offline, cách tải lẻ file về local, checklist rời phiên.
- `tests/{conftest,test_eda,test_geometry_gate}.py` — TẠO: fixture annotation dùng chung + 19 test mới.

**Quyết định & lý do:**
- **Phần lớn EDA chỉ cần annotation JSON (18MB), không cần ảnh 83.7GB** — phân bố lớp, spacing, bbox, crop size đều tính từ annotation. Chỉ `missing_phase_report` cần chỉ mục file và gate geometry cần đọc header ảnh. Nhờ vậy phần lớn EDA chạy/test được cả khi không có data.
- **Không tải data về local.** 83.7GB, và AGENTS.md §7 đã chốt Kaggle là compute. Thay vào đó dựng `docs/KAGGLE_WORKFLOW.md` — code ở git, chạy trên Kaggle, output nặng đẩy ngược thành Kaggle Dataset versioned cho các bước sau mount lại.
- **Gate geometry thử CẢ HAI axis order** (x↔shape[0] và x↔shape[1]) thay vì giả định — chưa biết ảnh là (x,y,z) hay (y,x,z); `axis_order_verdict()` suy ra từ dữ liệu thật.
- Test gate dùng **NIfTI tổng hợp thật** (nibabel ghi ra tmp_path) chứ không mock — để test đúng đường đọc header, chính chỗ dễ sai khi bản dữ liệu bị resample.
- **KHÔNG commit `reports/W1_REPORT.md`** — có sửa nhỏ (đổi tiêu đề mục 6) không phải của phiên này, để nguyên cho người dùng.

**Kết quả / số liệu:** `pytest` **46 passed** (27 → 46, +19). `ruff check` + `ruff format --check` sạch (24 file). 12/12 code cell trong notebook hợp lệ cú pháp (kiểm bằng `ast.parse`). Chưa có số liệu EDA thật — cần chạy trên Kaggle.

**Dang dở:**
- [ ] **Chạy `notebooks/01_eda.ipynb` trên Kaggle** để có số thật: phân bố lớp (đối chiếu official), spacing/pha, ca thiếu pha, kích thước bbox, và **kết quả GATE GEOMETRY**.
- [ ] T2.2 — chốt tham số tiền xử lý (crop size, spacing đích, N4 on/off, xử lý ca thiếu pha) **sau khi** có số EDA. Bảng trống đã để sẵn ở cuối notebook.

**Điểm vào phiên sau:** Chạy notebook trên Kaggle theo `docs/KAGGLE_WORKFLOW.md` §2. **Gate geometry FAIL ⇒ DỪNG**, không sang tiền xử lý (W2 ngày 3) — vì crop sai chỗ thì mọi kết quả sau đều vô nghĩa.

**Cảnh báo cho tool sau:** Gate geometry **chưa từng chạy trên dữ liệu thật** — mọi giả định về axis order/spacing hiện chỉ là code chờ kiểm chứng. Đừng viết `build_cache` dựa trên giả định bbox đúng khi gate chưa PASS.


## S-025 · 2026-07-24 19:45 · claude-code

**Mục tiêu phiên:** Sửa bug khiến gate geometry báo "BỎ QUA: cần ảnh thật" dù đang chạy trên Kaggle có data.

**Nhánh / commit:** `main` · `4c2cf7d` → *(commit đang chờ)*

**Đã đụng file:**
- `src/data/images.py` — `scan_image_index` nhận **danh sách đuôi**, mặc định `("_0000.nii.gz", "_0000.nii")`; dùng `setdefault` để thứ tự ưu tiên ổn định.
- `configs/data.yaml` — `image_suffix` (một chuỗi) → `image_suffixes` (danh sách 2 đuôi), kèm comment giải thích.
- `src/data/build_manifest.py`, `src/data/dataset.py` — cập nhật theo API mới.
- `notebooks/01_eda.ipynb` — cell mục 3 dùng `CONFIG["image_suffixes"]`.
- `tests/test_images.py` — +4 test: quét `.nii` thuần, thư mục lẫn hai đuôi, ưu tiên khi trùng, nhận chuỗi đơn.

**Quyết định & lý do:**
- **Nguyên nhân gốc:** file thật trên Kaggle là `lld/images/MR-391135_1_C+A_0000.nii` — **`.nii` đã giải nén, không phải `.nii.gz`**. Kaggle giải nén khi upload (khớp việc dataset phình 83.7GB: 3984 file × ~20MB). Config chỉ khai `_0000.nii.gz` ⇒ `scan_image_index` trả rỗng ⇒ `image_index = {}` ⇒ mục 3 và **mục 5 (gate geometry)** đều rơi vào nhánh "BỎ QUA" — **thất bại âm thầm, không báo lỗi**.
- Xác minh bằng Kaggle API: tải `lld/images/..._0000.nii.gz` → **404**; liệt kê thư mục → thấy `..._0000.nii` (18.9MB). Kích thước file cũng khớp mô tả PDF: DWI 1.5MB (thô 132×116), T2WI 6.3MB, các pha T1 ~18-23MB.
- Chọn **nhận cả hai đuôi** thay vì đổi cứng sang `.nii`: repo HF gốc vẫn là `.nii.gz`, ai tải từ HF sẽ có đuôi khác — code phải chạy được cả hai nguồn.
- Thêm test cho `.nii` thuần: **nếu có test này từ đầu thì bug đã không lọt**. Bài học: fixture test dùng đúng một đuôi đã che mất giả định sai.

**Kết quả / số liệu:** `pytest` **50 passed** (46 → 50). ruff sạch. Notebook 12/12 cell hợp lệ, output đã strip.
Kết quả EDA thật người dùng chạy — **phân bố lớp khớp official 7/7 + tổng**: HCC 157 · u máu 79 · ICC 58 · áp-xe 54 · nang 53 · di căn 51 · FNH 46 = 498. ⇒ bản wanglab **không mất/xáo trộn bệnh nhân nào**.

**Dang dở:**
- [ ] **Gate geometry vẫn CHƯA có kết quả thật** — chạy lại mục 3 + 5 sau khi `git pull` bản sửa này.
- [ ] T2.2 chốt tham số tiền xử lý — chờ số từ gate + mục 2/3/4.

**Điểm vào phiên sau:** Trên Kaggle: `!cd /kaggle/working/repo && git pull` rồi Restart & Run All. Mục 3 phải ra số ca thiếu pha, mục 5 phải in `GATE GEOMETRY: PASS/FAIL` + `axis order`.

**Cảnh báo cho tool sau:** Ảnh trên Kaggle là **`.nii` giải nén** (~20MB/file, 3984 file). Cẩn thận I/O khi tiền xử lý — đọc 8 pha/bệnh nhân ≈ 160MB, không cache thô vào RAM. Nhớ dùng `image_suffixes` (số nhiều) trong config, không phải `image_suffix`.


## S-026 · 2026-07-24 20:05 · claude-code

**Mục tiêu phiên:** Sửa đường dẫn data trên Kaggle (`/kaggle/input/datasets/marcohoang/lldmmridataset`).

**Nhánh / commit:** `main` · `bd6b55b` → *(commit đang chờ)*

**Đã đụng file:**
- `src/utils/io.py` — `resolve_data_root()` giờ dò theo thứ tự: env → `data_root_candidates` (**chỉ nhận đường dẫn thật sự chứa annotation**) → `data_root`. Lỗi báo rõ đã thử đường nào.
- `configs/data.yaml` — thêm `data_root_candidates` (path Kaggle mới + path cũ).
- `notebooks/01_eda.ipynb` — bootstrap bỏ hardcode `os.environ[...] = "/kaggle/input/lldmmridataset"`, dùng `resolve_data_root`; in cảnh báo + gợi ý `!ls /kaggle/input` nếu không thấy annotation.
- `docs/KAGGLE_WORKFLOW.md` — cập nhật 3 chỗ hardcode path.
- `tests/test_io.py` — TẠO: 6 test cho logic dò (env thắng, bỏ qua ứng viên thiếu annotation, giữ thứ tự, fallback, lỗi liệt kê path đã thử, config cũ vẫn chạy).

**Quyết định & lý do:**
- **Không chỉ đổi chuỗi path** mà làm dò tự động có xác minh. Lý do: Kaggle đổi sơ đồ mount tuỳ lúc (`/kaggle/input/<slug>` vs `/kaggle/input/datasets/<owner>/<slug>`); hardcode sẽ hỏng lại lần sau.
- **Xác minh bằng sự tồn tại của annotation, không phải `is_dir()`.** Đây đúng là bài học S-025: thư mục rỗng tồn tại vẫn khiến mọi bước sau thất bại âm thầm. Giờ ứng viên nào không chứa annotation thì bị bỏ qua.
- Env `LLDMMRI_DATA_ROOT` vẫn thắng tuyệt đối, không kiểm tra — người dùng chủ động ghi đè thì tôn trọng.

**Kết quả / số liệu:** `pytest` **56 passed** (50 → 56). ruff sạch. Notebook 12/12 cell hợp lệ, bootstrap không còn chuỗi `lldmmridataset` nào.

**Dang dở:**
- [ ] **Gate geometry vẫn chưa có kết quả thật** (hai phiên liên tiếp bị chặn bởi bug hạ tầng: đuôi file S-025, đường dẫn S-026).
- [ ] T2.2 chốt tham số tiền xử lý.

**Điểm vào phiên sau:** Trên Kaggle: `!cd /kaggle/working/repo && git pull` → Restart & Run All. Cell bootstrap giờ in `data root` đã dò được + trạng thái tồn tại của annotation/images; nếu vẫn sai sẽ in hướng dẫn `!ls /kaggle/input`.

**Cảnh báo cho tool sau:** Đường dẫn Kaggle nằm ở `configs/data.yaml: data_root_candidates`, **không hardcode trong code hay notebook**. Mount chỗ mới thì thêm vào list đó (commit là xong) thay vì sửa rải rác.


## S-027 · 2026-07-24 20:30 · claude-code

**Mục tiêu phiên:** Sửa việc `resolve_data_root` vẫn trả path sai dù config đã có path đúng.

**Nhánh / commit:** `main` · `fc9a4eb` → *(commit đang chờ)*

**Đã đụng file:**
- `src/utils/io.py` — `resolve_data_root`: **env cũng bị xác minh**. Thứ tự mới: env-hợp-lệ → ứng viên-hợp-lệ → env-không-xác-minh-được (kèm cảnh báo) → `data_root`.
- `notebooks/01_eda.ipynb` — bootstrap `os.environ.pop("LLDMMRI_DATA_ROOT", None)` trước khi resolve.
- `configs/data.yaml` — sửa comment đầu file còn trỏ path cũ.
- `tests/test_io.py` — tách/thêm 3 test: env hợp lệ thắng ứng viên; **env sót thua ứng viên hợp lệ**; env dùng làm phương án cuối kèm cảnh báo.

**Quyết định & lý do:**
- **Nguyên nhân:** config đã đúng (path Kaggle mới là ứng viên đầu tiên), nhưng notebook CŨ có `os.environ.setdefault("LLDMMRI_DATA_ROOT", "/kaggle/input/lldmmridataset")`. Trong Jupyter, env đó **còn nguyên trong process** sau khi `git pull` — và S-026 cho env quyền tuyệt đối không kiểm tra ⇒ giá trị cũ đè lên config mới.
- Sửa: env cũng phải chứa annotation mới được nhận. Nếu env không xác minh được nhưng cũng không ứng viên nào khớp thì vẫn dùng env **kèm cảnh báo gợi ý Restart kernel** — không fail cứng, vì trong notebook thất bại cứng khó chịu hơn là tự chữa có cảnh báo.
- Đây là **lần thứ ba liên tiếp** cùng một loại lỗi: trạng thái tồn tại nhưng rỗng/sai được tin tưởng mà không xác minh (S-025 thư mục/đuôi file, S-026 thư mục rỗng, S-027 env sót). Nguyên tắc rút ra: **xác minh bằng nội dung thật (annotation tồn tại), không bằng sự tồn tại của biến/thư mục.**

**Kết quả / số liệu:** `pytest` **58 passed** (56 → 58). ruff sạch. Mô phỏng đúng tình huống người dùng (env sót trỏ path cũ + path đúng trong ứng viên) → resolve ra path đúng.

**Dang dở:**
- [ ] **Gate geometry vẫn chưa có kết quả thật** (ba phiên liên tiếp bị chặn bởi lỗi hạ tầng, không phải vấn đề khoa học).
- [ ] T2.2 chốt tham số tiền xử lý.

**Điểm vào phiên sau:** Kaggle: `!cd /kaggle/working/repo && git pull` → **Restart & Run All** (restart quan trọng). Bootstrap giờ tự dọn env sót nên chạy lại cell cũng được.

**Cảnh báo cho tool sau:** Trong Jupyter, `os.environ` **sống dai hơn code** — `git pull` không dọn nó. Đừng dùng `setdefault` cho env đường dẫn trong notebook; và luôn xác minh path bằng file thật bên trong.


## S-028 · 2026-07-24 21:00 · claude-code

**Mục tiêu phiên:** Tìm lý do THẬT khiến 3 phiên sửa path đều không có tác dụng.

**Nhánh / commit:** `main` · `5f1ea4a` → *(commit đang chờ)*

**Đã đụng file:**
- `notebooks/01_eda.ipynb` — bootstrap **luôn `rm -rf` rồi clone lại**; in `repo commit:` để kiểm chứng đang chạy bản nào; chẩn đoán dùng `find /kaggle/input -name LLD_MMRI_Annotation.json`.
- `src/utils/io.py` — thêm `discover_data_root()`: tự lùng annotation dưới `data_root_search` (glob giới hạn độ sâu, không dùng `**` để khỏi duyệt 83.7GB). `resolve_data_root` chèn bước lùng vào giữa (sau ứng viên, trước fallback).
- `configs/data.yaml` — thêm `data_root_search: [/kaggle/input]`.
- `docs/KAGGLE_WORKFLOW.md` — sửa cell bootstrap mẫu (rm -rf + clone + in commit); thay hướng dẫn "git pull" bằng "Restart & Run All" + nhắc kiểm dòng `repo commit`.
- `tests/test_io.py` — +5 test: lùng ở độ sâu 1 và 3, không tìm thấy, search root không tồn tại, và **resolve rơi xuống bước lùng khi mọi ứng viên đều sai**.

**Quyết định & lý do:**
- **NGUYÊN NHÂN GỐC (lỗi của tôi, mất 3 phiên mới thấy):** bootstrap viết `if not REPO.exists(): git clone`. Sau lần chạy đầu, `/kaggle/working/repo` đã tồn tại ⇒ **không bao giờ clone lại, không bao giờ pull**. Toàn bộ bản sửa S-025/026/027 đã push lên GitHub nhưng **chưa từng tới được session Kaggle** — người dùng chạy code cũ suốt. Ba phiên tôi đi sửa triệu chứng (đuôi file, danh sách path, env) trong khi bệnh nằm ở chỗ code mới không bao giờ được nạp.
- Sửa: luôn xoá + clone lại (chắc chắn hơn `git pull` vì tránh mọi trạng thái bẩn), và **in commit hash** — bằng chứng khách quan đang chạy bản nào. Không có dòng này thì không thể phân biệt "sửa sai" với "sửa đúng nhưng chưa nạp".
- **Thôi đoán sơ đồ mount.** Đã đoán sai 2 lần nên thêm `discover_data_root()` tự tìm file annotation. Ai đổi mount kiểu gì cũng chạy.
- Bài học chung cho cả chuỗi S-025→028: **luôn có một dấu hiệu xác nhận môi trường đang chạy đúng bản code/dữ liệu nào** trước khi chẩn đoán bất cứ điều gì khác.

**Kết quả / số liệu:** `pytest` **63 passed** (58 → 63). ruff sạch. Mô phỏng đúng cây thư mục Kaggle thật (`/kaggle/input/datasets/marcohoang/lldmmridataset` + env sót trỏ path cũ) → resolve ra data root đúng, annotation + images đều tồn tại.

**Dang dở:**
- [ ] **Gate geometry vẫn chưa có kết quả thật.**
- [ ] T2.2 chốt tham số tiền xử lý.

**Điểm vào phiên sau:** Kaggle → **Restart & Run All**. Kiểm dòng `repo commit:` đầu output phải khớp commit mới nhất. Rồi lấy output mục 5 (gate geometry).

**Cảnh báo cho tool sau:** Notebook Kaggle **phải clone lại mỗi lần chạy**; `if not exists(): clone` là cái bẫy đã làm mất 3 phiên. Luôn in commit hash ở cell đầu.


## S-029 · 2026-07-24 21:40 · claude-code

**Mục tiêu phiên:** Ghi nhận GATE GEOMETRY **PASS** trên dữ liệu thật; xử lý phần còn treo (thứ tự trục).

**Nhánh / commit:** `main` · `8d098e5` → *(commit đang chờ)*

**KẾT QUẢ GATE GEOMETRY (dữ liệu thật, 5 bệnh nhân × 8 pha):**
```
GATE GEOMETRY: PASS (40/40 phase-check đạt)
axis order: ambiguous
```
- **`spacing_hdr == spacing_ann` ở cả 40 check** ⇒ bản wanglab **KHÔNG resample ảnh**. Toạ độ bbox trong annotation **dùng thẳng được**, không cần map qua affine. Đây là điều kiện tiên quyết cho `build_cache` — nay đã thông.
- `slice_idx` và bbox đều nằm trong biên ⇒ annotation khớp ảnh.

**Hai phát hiện quan trọng từ output (chưa lường trước):**
1. **Số slice khác nhau giữa các pha trong CÙNG một bệnh nhân.** MR-398189: pha động 512×512×**88** @2.6mm, T2WI 512×512×**24** @9mm, DWI 256×256×24 @9mm. MR104842: pha động ×**50** @4mm, T2WI/DWI/In/Out ×**20** @10mm. ⇒ 8 pha **không cùng lưới**; registration + resample về grid chung là **bắt buộc** (đúng như Spec Sheet chốt).
2. **Nhóm In/Out Phase KHÔNG cố định.** 4 ca đầu: In/Out đi cùng pha động (88/72 slice, 2.6mm). MR104842: In/Out đi cùng nhóm T2WI (20 slice, 10mm). ⇒ thiết kế fusion v2 "tách structural vs dynamic" (Spec Sheet §3) **không hardcode nhóm được**, phải suy từ metadata từng ca. Ghi lại để W4 không dẫm.

**Đã đụng file:**
- `src/data/geometry_gate.py` — thêm `disambiguate_axis_order()` + `AxisOrderEvidence`: phân định trục bằng **ảnh không vuông** (khi ảnh vuông thì bbox lọt cả hai chiều nên vô định). Phát hiện mâu thuẫn thì báo `conflict` chứ không đoán.
- `scripts/kaggle_geometry_report.py` — TẠO: báo cáo một lệnh cho T2.2 (phân bố lớp · ca thiếu pha · gate · thứ tự trục · lưới từng pha · kích thước lesion + crop size). Chỉ đọc header, không nạp pixel. Ép stdout UTF-8 để chạy được cả trên console Windows.
- `tests/test_geometry_gate.py` — +4 test: vô định khi ảnh vuông, phân định được `xy` và `yx` bằng ảnh không vuông, báo `conflict`.

**Quyết định & lý do:**
- **`axis order: ambiguous` là kết quả đúng, không phải lỗi** — mọi ảnh mẫu đều vuông (512², 256², 384²) nên bbox lọt cả hai cách hiểu. Không được đoán: crop sai trục sẽ lệch 90°.
- Giải bằng **bằng chứng khách quan** (quét tìm ảnh không vuông) thay vì bắt người dùng nhìn overlay đoán bằng mắt. Nếu toàn bộ 498 ca đều vuông thì mới phải dùng tầng 3 (overlay).

**Kết quả / số liệu:** `pytest` **67 passed** (63 → 67). ruff sạch (26 file).

**Dang dở:**
- [ ] **Thứ tự trục** — chạy `scripts/kaggle_geometry_report.py` để phân định.
- [ ] T2.2 chốt tham số tiền xử lý (chờ output script trên).

**Điểm vào phiên sau:** Trên Kaggle chạy `!cd /kaggle/working/repo && python scripts/kaggle_geometry_report.py --limit 0`, lấy toàn bộ output để chốt T2.2 rồi sang W2 ngày 3 (`build_cache`).

**Cảnh báo cho tool sau:** 8 pha **không cùng lưới** (số slice và spacing khác nhau trong cùng bệnh nhân) — mọi code giả định 8 pha stack thẳng được là SAI. Nhóm In/Out Phase thay đổi theo ca, không hardcode.


## S-030 · 2026-07-27 11:30 · claude-code

**Mục tiêu phiên:** Dọn code đã bị thay thế, rồi dựng pipeline tiền xử lý để dữ liệu sẵn sàng train.

**Nhánh / commit:** `main` · `ccf6f9a` → *(commit đang chờ)*

**Đã đụng file:**
- `src/data/geometry_gate.py` — xoá `disambiguate_axis_order` + `AxisOrderEvidence` (86 dòng code chết: 0/3984 ảnh không vuông nên không bao giờ kết luận được). Giữ nguyên phần lõi đã chạy PASS 3984/3984.
- `src/data/dataset.py` — **viết lại hoàn toàn** thành `CachedLesionDataset` + `build_fold_datasets` + `build_test_dataset`. Bản cũ `np.stack` 8 volume thô, sẽ crash vì 8 pha khác shape.
- `src/preprocess/{geometry,grid,resample,normalize,build_cache}.py` — TẠO.
- `configs/preprocess.yaml` — TẠO; `axis_order` **để trống có chủ ý** (cổng chặn).
- `notebooks/02_build_cache.ipynb` — TẠO: phán quyết trục → xác nhận bằng mắt → thử 3 ca → build 498 ca → kiểm cache → đẩy Kaggle Dataset.
- `tests/{test_preprocess_geometry,test_preprocess_pipeline,test_dataset}.py` — TẠO (+27 test).
- `scripts/kaggle_geometry_report.py` mục 4, `AGENTS.md` §6, `docs/W2_plan.md` T3.2 — cập nhật theo.

**Quyết định & lý do:**
- **Crop trong không gian mm, không phải voxel.** 8 pha khác lưới voxel (pha động 512²×88 @0.78/2.6mm, T2WI 512²×24 @9mm, DWI 256²×24) nên bbox voxel của pha này vô nghĩa với pha kia. Nhưng cả 8 chung hệ toạ độ bệnh nhân DICOM. Cách làm: tâm bbox → mm → dựng **một lưới đích** 96×96×48 @1.5×1.5×3.0mm quanh tâm → `sitk.Resample` Identity transform cho cả 8 pha. **Đây đồng thời là bước căn chỉnh** ⇒ không cần registration riêng ở v0 (đã chốt với người dùng); rigid là ablation W3.
- **Phán quyết thứ tự trục bằng độ hội tụ toạ độ thế giới.** Annotation có bbox riêng cho từng pha; cùng tổn thương vật lý ⇒ 8 tâm phải hội tụ. Cách hiểu sai làm tán ra. Hơn hẳn nhìn mắt và heuristic cường độ.
- **Chỉ tính phiếu từ ca có sức phân biệt thật** (`DECISIVE_MARGIN_MM=5.0`). Đo trên dữ liệu thật: sức phân biệt đến từ `origin_x - origin_y`, trung vị chỉ ~7mm và **200/498 ca dưới 5mm**. Gộp hết vào chỉ thêm nhiễu.
- **`build_cache` TỪ CHỐI chạy khi `axis_order` trống** — thà dừng còn hơn crop sai trục rồi mọi kết quả sau đều vô nghĩa.
- **Chuẩn hoá per-sample** (thống kê từ chính volume của bệnh nhân đó), `scope=volume` để giữ tương phản tổn thương-so-với-nhu-mô. Không gộp thống kê xuyên bệnh nhân ⇒ không vi phạm AGENTS.md §3.3.
- **Test chống leakage cố ý KHÔNG phụ thuộc torch** — thứ quan trọng nhất phải luôn chạy được, kể cả máy chưa cài deep-learning stack.

**Kết quả / số liệu:** `pytest` **87 passed, 3 skipped** (67 → 90 test; 3 skip là các test cần torch). `ruff check` + `format` sạch (35 file). Hai bug bắt được khi tự test: (1) `np.savez_compressed` tự nối `.npz` khiến ghi nguyên tử hỏng; (2) fixture nền phẳng làm p0.5 == p99.5 — code xử lý đúng (trả 0 thay vì NaN) nhưng test thì vô nghĩa, đã sửa fixture cho có nhiễu như MRI thật.

**Dang dở:**
- [ ] **Chạy `notebooks/02_build_cache.ipynb` trên Kaggle**: lấy phán quyết trục → điền `axis_order` vào `configs/preprocess.yaml` → push → build 498 ca → đẩy Kaggle Dataset.
- [ ] Ghi slug + version của Kaggle Dataset vào config + WORKLOG.

**Điểm vào phiên sau:** Sau khi có cache: W2 ngày 5 — baseline DenseNet121-3D đọc `CachedLesionDataset`, checkpoint/resume mỗi epoch.

**Cảnh báo cho tool sau:** `configs/preprocess.yaml: axis_order` để trống là **có chủ ý**, không phải quên — phải chạy phán quyết rồi điền. Nếu phán quyết ra `inconclusive` thì **DỪNG**, xác nhận bằng overlay (mục 2 của notebook), đừng chọn bừa.


## S-031 · 2026-07-27 12:10 · claude-code

**Mục tiêu phiên:** Xử lý kết quả `inconclusive` của phán quyết thứ tự trục trên dữ liệu thật.

**Nhánh / commit:** `main` · `e549b20` → *(commit đang chờ)*

**Kết quả chạy thật (498 bệnh nhân) — bản đo CŨ (có tính trục Z):**
```
AXIS ORDER: inconclusive
  498 so được · 90 ca có sức phân biệt
  xy: 83 phiếu (92%) · độ tán trung vị 26.3 mm
  yx:  7 phiếu ( 8%) · độ tán trung vị 30.0 mm
```
Phiếu **đã vượt** ngưỡng 90%; bị gắn `inconclusive` chỉ vì 26.3mm > ngưỡng 25mm.

**Chẩn đoán — lỗi phép đo của tôi, không phải lỗi dữ liệu.** Phân rã độ tán theo trục:

| Cách hiểu | X | Y | Z |
|---|---|---|---|
| `xy` | **7.4** | 10.3 | 23.3 |
| `yx` | 13.9 | 11.2 | 23.3 |

- **Z giống hệt nhau ở cả hai cách hiểu** — tất nhiên, vì hoán vị trục chỉ đụng X/Y.
- 85% số ca có Z tán nhất; Z trung vị 23.3mm = đúng biên độ **chuyển động hô hấp của gan** (y văn 10–25mm theo trục đầu-chân), do 8 pha chụp ở các lần nín thở khác nhau.
- Đưa Z vào phép đo vừa **đẩy tổng độ tán vượt ngưỡng**, vừa **làm loãng tín hiệu** phân biệt.

**Đã đụng file:**
- `src/preprocess/geometry.py` — `_spread_mm` chỉ đo **trong mặt phẳng** (bỏ trục Z); `CONVERGENCE_TOL_MM` 25 → 20 và định nghĩa lại là ngưỡng trong-mặt-phẳng; summary nói rõ đã bỏ Z và vì sao.
- `tests/test_preprocess_geometry.py` — +3 test khoá hành vi: chênh thuần Z không tính vào độ tán; đo đúng khoảng cách trong mặt phẳng; ca thật (166/14, 12.4mm) phải kết luận được.
- `configs/preprocess.yaml` — điền `axis_order: xy` kèm toàn bộ bằng chứng.

**Kết quả sau khi sửa (tính lại trên 498 ca):**
```
180/498 ca có sức phân biệt (gấp đôi 90 ca trước đó)
xy: 166 phiếu (92%) · độ tán trong mặt phẳng 12.4 mm
yx:  14 phiếu ( 8%) · độ tán trong mặt phẳng 17.8 mm
```
⇒ **`axis_order = "xy"`**. Bỏ Z không làm đổi tỉ lệ phiếu (92%) nhưng **tăng gấp đôi số ca dùng được**, nên bằng chứng mạnh hơn nhiều (166 vs 14).

`pytest` **90 passed, 3 skipped** (87 → 90 test). ruff sạch.

**Dang dở:**
- [ ] Xác nhận bằng overlay (notebook 02 mục 2) trước khi build cả mẻ — bằng chứng số đã mạnh nhưng đây là kiểm chứng độc lập, rẻ.
- [ ] Build cache 498 ca + đẩy Kaggle Dataset.

**Điểm vào phiên sau:** Kaggle → Restart & Run All notebook 02. Mục 1 giờ phải ra `xy` (không còn `inconclusive`); xem mục 2 xác nhận hộp trúng tổn thương; rồi chạy mục 4.

**Cảnh báo cho tool sau:** Chuyển động hô hấp giữa các pha là **~23mm theo trục Z** — con số này giải thích vì sao rigid registration nằm trong kế hoạch W3 làm ablation. Đừng coi độ tán theo Z là dấu hiệu hình học hỏng.


## S-032 · 2026-07-27  · codex

**Mục tiêu phiên:** Tạo snapshot audit W2 giải thích LLD-MMRI, rủi ro dữ liệu và pipeline tiền xử lý trước train.

**Nhánh / commit:** `main` · `8f23196` → *(commit đang chờ)*

**Đã đụng file:**
- `reports/W2_LLD_MMRI_DATA_AUDIT.md` — MỚI; audit snapshot tiếng Việt có giải thích thuật ngữ, số liệu đã đo, giới hạn, 3 sơ đồ Mermaid và link nguồn hình MRI thực tế.
- `WORKLOG.md` — append entry S-032.

**Quyết định & lý do:**
- Audit là **snapshot W2**, không phải tài liệu sống — cache/train sau đó phải ghi vào WORKLOG hoặc report W6 để không trộn dữ kiện trước train với kết quả hậu nghiệm.
- Chỉ dùng sơ đồ tự vẽ và link/citation hình MRI bên ngoài — không xuất hay nhúng ảnh, crop hoặc cache LLD-MMRI vì đó là dữ liệu/bản phái sinh bị hạn chế phát tán.

**Kết quả / số liệu:** `git diff --check` sạch; quality gate PowerShell PASS (Impeccable detect slides/reports PASS, splits không đổi). `pytest -q`, `python -m pytest -q` và `.venv\\Scripts\\python.exe -m pytest -q` đều không chạy được vì pytest chưa được cài trong các Python hiện có, dù `requirements.txt` đã pin `pytest==8.3.3`; không cài thêm dependency trong phiên tài liệu này.

**Dang dở:**
- [ ] Notebook 02 trên Kaggle: xác nhận overlay `xy`, build/kiểm 498 cache files, tạo Kaggle Dataset private và ghi slug/version.
- [ ] Test suite local cần được chạy lại sau khi cài môi trường từ `requirements.txt`.

**Điểm vào phiên sau:** Hoàn tất notebook 02 trên Kaggle; khi nhận output cache, ghi slug/version vào config + WORKLOG rồi dựng baseline DenseNet121-3D trên `CachedLesionDataset`.

**Cảnh báo cho tool sau:** Audit W2 cố ý nói cache **chưa nghiệm thu**; đừng sửa nó để tuyên bố train-ready chỉ vì build đã bắt đầu. Nếu có kết quả cache, ghi vào WORKLOG/report W6 theo quyết định snapshot.


## S-033 · 2026-07-27 · codex

**Mục tiêu phiên:** Ghi định danh cache LLD-MMRI đã tạo trên Kaggle vào cấu hình tái lập.

**Nhánh / commit:** `main` · `fb1698e` → *(commit đang chờ)*

**Đã đụng file:**
- `configs/preprocess.yaml` — ghi `kaggle_dataset_slug: "marcohoang/lld-mmri-3"` và `kaggle_dataset_version: 1`.
- `WORKLOG.md` — append entry S-033.

**Quyết định & lý do:**
- Lưu slug/version dưới dạng YAML thật, không chỉ comment — notebook/train sau này có thể đọc được; dataset được quan sát là Private, nên vẫn phù hợp ràng buộc không phát tán cache.

**Kết quả / số liệu:** Trang Kaggle `LLD-MMRI-3D` hiển thị Private, Version 1, 2,71 GB và thư mục `cache` có 501 file; số này phù hợp với 498 `.npz` theo bệnh nhân cộng file metadata/log. Việc kiểm no-NaN/shape của toàn bộ cache vẫn dựa vào output notebook 02 mục 5, chưa được thay thế bởi metadata trang web.

**Dang dở:**
- [ ] Lưu/kiểm output notebook 02 mục 2, 3 và 5: overlay `xy`, shape/finiteness smoke test, 498 cache files và không lỗi.
- [ ] Test suite local cần được chạy lại sau khi cài môi trường từ `requirements.txt` (pytest hiện chưa có).

**Điểm vào phiên sau:** Dùng `marcohoang/lld-mmri-3` version 1 làm Kaggle input cho notebook baseline, mount cache rồi dựng `CachedLesionDataset` theo fold 1.

**Cảnh báo cho tool sau:** Version 1 xác nhận cache tồn tại nhưng không tự chứng minh mọi tensor không NaN/Inf; chỉ gọi data train-ready sau tiêu chí notebook 02 mục 5.


## S-034 · 2026-07-27 15:05 · claude-code

**Mục tiêu phiên:** Data đã xong (cache 498 ca nghiệm thu) → dựng nốt mảnh còn thiếu của W2: model baseline + vòng train + metric.

**Nhánh / commit:** `main` · `f0b7162` → *(commit đang chờ)*

**Nghiệm thu cache — đọc từ notebook Kaggle đã chạy** (`notebooks/notebookf104ced082.ipynb`, untracked, bản 02 có output):
```
axis order  : xy (không còn inconclusive) · 166/180 phiếu (92%) · tán trong mặt phẳng 12.4mm
build       : HOÀN TẤT xong 498, bỏ qua 0, LỖI 0 · 24 phút
cache       : 498 file .npz · shape (8,96,96,48) · finite=True
DataLoader  : train=312 val=82 (=394) · batch (4,8,96,96,48) float32
```
⇒ Ba mục "dang dở" của S-031/S-032/S-033 (overlay, 498 file, smoke test) **đã đóng**. Cache là train-ready theo đúng tiêu chí notebook 02 mục 5.

**Đã đụng file:**
- `src/models/densenet3d.py`, `src/models/__init__.py` — MỚI; DenseNet121-3D (MONAI) 8 kênh → 7 lớp = early-concat v0; registry `build_model(config)` để W2-ngày-6/W4 thêm biến thể mà không sửa vòng train.
- `src/data/transforms.py` — MỚI; flip/rot90 **chỉ trong mặt phẳng**, nhiễu cường độ per-phase. Torch thuần, không dùng MONAI transform.
- `src/train/loop.py`, `src/train/run.py`, `src/train/__init__.py` — MỚI; vòng train + entrypoint.
- `src/eval/metrics.py`, `src/eval/__init__.py` — MỚI; macro-F1/κ/balanced-acc/confusion, numpy thuần, hàm **thuần** tách khỏi train.
- `src/utils/io.py` — thêm `resolve_cache_dir` + `resolve_output_dir` (chuyển từ `build_cache`, để `src/train` dùng chung mà không phải import qua preprocess).
- `src/preprocess/build_cache.py` — bỏ bản `resolve_cache_dir` cục bộ, import từ `utils.io`, re-export giữ tương thích.
- `configs/baseline_3dpatch.yaml` — MỚI; toàn bộ hyperparam.
- `notebooks/03_train_baseline.ipynb` — MỚI; lớp mỏng gọi `src/`, tự tìm cache bằng `cache_meta.json` thay vì đoán đường mount.
- `tests/test_models.py`, `test_transforms.py`, `test_train_loop.py`, `test_metrics.py` — MỚI (+20 test).
- `AGENTS.md` §6 — điền dòng lệnh train (cùng commit tạo entrypoint, theo §6).

**Quyết định & lý do:**
- **Augment không đụng trục Z.** Z là hướng đầu-chân, lát 3.0mm so với 1.5mm trong mặt phẳng; lật/xoay quanh Z sinh giải phẫu không có thật. Có test khoá bằng khối "giá trị = chỉ số Z".
- **Biến đổi hình học đồng nhất cho cả 8 pha; nhiễu cường độ thì per-phase.** Hình học lệch nhau sẽ phá chính tín hiệu động học cần học; còn dao động cường độ giữa các lần chụp là chuyện máy MRI thật vẫn làm.
- **`class_weights: balanced`, tính CHỈ từ nhãn train.** Áp-xe/FNH quá hiếm, CE trần sẽ bỏ hẳn chúng — mà macro-F1 phạt đúng chỗ đó. Đếm cả val là leakage.
- **Lưu `val_probs_best.npz`** (xác suất, không chỉ nhãn) — W3 bootstrap CI và W5 calibration/selective dùng lại được mà **không phải train lại**.
- **`last.pt` ghi SAU khi xử lý best**, ghi nguyên tử (`.tmp` → `replace`). Kaggle cắt session giữa lúc ghi là chuyện bình thường.
- Loại MONAI dict-transform: ba phép augment này quá đơn giản để cần tới nó, và torch thuần thì test được mà không cần cài MONAI.

**Kết quả / số liệu:** `pytest` **105 passed, 8 skipped** (93 → 113 test; skip = cần torch/monai, máy local chưa cài). `ruff check` sạch, `ruff format` đã chạy. Quality gate PowerShell **PASS** (ruff bị SKIP trong gate vì không thấy binary trên PATH — đã chạy tay qua `python -m ruff`). **Chưa có số train** — chưa chạy trên Kaggle.

**Dang dở:**
- [ ] **Chạy notebook 03 trên Kaggle** để lấy macro-F1 val fold 1 (T5.3). Đây là DoD cuối cùng còn treo của W2.
- [ ] Baseline 2.5D (T6.1) — `src/models/backbone2p5d.py`, tái dùng đúng vòng train này. Cắt được nếu trễ (W2_plan §"Task cắt được").
- [ ] `src/data/transforms.py` chưa từng chạy thật: 9 test của nó bị skip toàn bộ ở local (không có torch). Kaggle sẽ là lần đầu chúng chạy.

**Điểm vào phiên sau:** Kaggle → notebook 03 → Add data `marcohoang/lld-mmri-3` (version 1) → Run All. Mục 1 phải ra `[2,8,96,96,48] → [2,7]`; mục 2 train fold 1; chép số ở mục 3 vào WORKLOG.

**Cảnh báo cho tool sau:**
- `configs/baseline_3dpatch.yaml` là **baseline**, không phải model chính. Model chính chốt ở W4 sau CV 5-fold + CI. Đừng báo số 1-fold như kết quả cuối (AGENTS.md §3.5).
- Vòng train chỉ đọc `train_fold*/val_fold*`. Không có đường nào chạm test-104 — giữ nguyên như vậy.
- `notebooks/notebookf104ced082.ipynb` là bản Kaggle **có output 1.3MB**, cố ý **không commit** (quy ước notebook phải strip output). Số liệu của nó đã được chép vào entry này; xoá file được.


## S-035 · 2026-07-27 15:10 · claude-code

**Mục tiêu phiên:** Chạy baseline fold 1 trên Kaggle — thay vào đó sửa ba lỗi nối tiếp nhau ở khâu bootstrap/đường dẫn.

**Nhánh / commit:** `main` · `7e0b4cf` → `e0c312f` (3 commit)

**Ba lỗi, theo thứ tự vấp phải:**

1. **`7086af3` — thông báo lỗi vô dụng.** Cell bootstrap không thấy cache thì raise `SystemExit("Không thấy cache")`, không nói **đang thấy gì**. Sửa: `find_cache_dir()` + `describe_tree()` trong `src/utils/io.py`; khi hụt thì in nguyên cây `/kaggle/input` (thư mục kèm số file theo đuôi) rồi mới dừng. Notebook trở lại đúng vai lớp mỏng gọi `src/`.

2. **`e65b9b7` — đường dẫn tương đối hiểu theo CWD.** `splits_dir: splits` trong config resolve theo thư mục làm việc; trên Kaggle notebook chạy ở `/kaggle/working` còn code clone vào `/kaggle/working/repo` ⇒ `FileNotFoundError: splits/labels_trainval.txt` ngay dòng đọc split đầu tiên. Sửa: `repo_root()` + `resolve_repo_path()`; mọi đường dẫn tương đối trong config neo vào **gốc repo**. Áp cho `splits_dir`, `cache_dir`, `output_dir`; env override vẫn thắng.
   *Vì sao ẩn lâu:* cell smoke test truyền `splits_dir=REPO/"splits"` tường minh nên chạy được — một chỗ đúng che cho chỗ sai, bug chỉ lộ ở cell train.

3. **`e0c312f` — clone lại code nhưng `sys.modules` giữ bản cũ.** Sau khi sửa (2) và chạy lại, **vẫn y nguyên lỗi cũ**: cell bootstrap xoá thư mục rồi clone bản mới, nhưng module `src.*` đã import từ lần chạy trước vẫn nằm trong `sys.modules`. Dòng `repo commit` in ra commit mới ⇒ **bằng chứng giả**, nó nói về code trên đĩa chứ không phải code đang chạy. Sửa: xoá `src.*` khỏi `sys.modules` ngay sau clone (cả notebook 02 và 03), in thêm `code đang dùng: <repo_root()>` kèm `assert` khớp đường dẫn clone.

**Đã đụng file:**
- `src/utils/io.py` — thêm `find_cache_dir`, `describe_tree`, `repo_root`, `resolve_repo_path`; `resolve_cache_dir`/`resolve_output_dir` đi qua `resolve_repo_path`.
- `src/data/dataset.py` — `build_fold_datasets`/`build_test_dataset` resolve `splits_dir` theo gốc repo.
- `src/train/run.py` — `splits_dir` từ config resolve tương tự.
- `notebooks/02_build_cache.ipynb`, `notebooks/03_train_baseline.ipynb` — bootstrap xoá `sys.modules`, in bằng chứng code đang chạy.
- `tests/test_find_cache.py` (9 test), `tests/test_repo_paths.py` (6 test) — MỚI.

**Quyết định & lý do:**
- **Đường dẫn tương đối = tương đối với gốc repo, không phải CWD.** Cho kết quả giống nhau dù gọi từ notebook, CLI hay test. Phương án đã loại: bắt mọi caller truyền đường dẫn tuyệt đối — đúng nhưng dễ quên, và quên một chỗ là hỏng cả run.
- **Test cho (2) đều đổi CWD ra ngoài repo trước khi gọi** — nếu không thì test chạy ở CWD=repo và pass cả khi code sai, đúng kiểu test không bắt được gì.
- Không dùng `importlib.reload`: thứ tự reload phụ thuộc đồ thị import, xoá sạch `sys.modules` đơn giản và chắc hơn.

**Kết quả / số liệu:** `pytest` **120 passed, 8 skipped** (113 → 135 test). ruff sạch. Quality gate PASS. **Vẫn chưa có số train** — chưa lần nào vòng train chạy tới epoch đầu tiên.

**Dang dở:**
- [ ] Chạy fold 1 trên Kaggle lấy macro-F1 val (T5.3) — DoD cuối cùng còn treo của W2. Chưa xác nhận được lỗi (3) có phải nguyên nhân cuối cùng không; bản sửa có sẵn chẩn đoán để lần chạy tới tự trả lời.
- [ ] Baseline 2.5D (T6.1) — cắt được nếu trễ.
- [ ] `src/data/transforms.py` vẫn chưa từng chạy thật (9 test skip ở local vì không có torch).

**Điểm vào phiên sau:** Kaggle notebook 03 → **Restart & Run All** (bắt buộc restart, không chỉ Run All). Cell 0 phải in `repo commit: e0c312f...` **và** `code đang dùng: /kaggle/working/repo` **và** `có labels_trainval.txt: True`. Ba dòng đó khớp thì cell train mới đáng chạy.

**Cảnh báo cho tool sau:**
- **Dòng `repo commit` KHÔNG chứng minh code nào đang chạy** nếu chưa xoá `sys.modules`. Đây là bẫy đã ăn trọn một vòng sửa-chạy-vẫn-lỗi. Mọi notebook mới phải copy đoạn xoá `sys.modules` từ cell 0 của notebook 03.
- Đừng thêm đường dẫn tương đối mới vào config mà không cho qua `resolve_repo_path`.



## S-036 · 2026-07-27 15:35 · claude-code

**Mục tiêu phiên:** Nhận kết quả baseline fold 1 đầu tiên và đọc nó.

**Nhánh / commit:** `main` · `4858a26` → *(commit đang chờ)*

### SỐ MỐC ĐẦU TIÊN CỦA DỰ ÁN

Chạy trên Kaggle, notebook 03, code tại commit `e0c312f`, `configs/baseline_3dpatch.yaml` **trước** thay đổi của phiên này (`norm` chưa có ⇒ BatchNorm mặc định).

```
fold 1 · seed 1337 · train=312 val=82 · device=cuda · amp=True
densenet121_3d · 11.403.463 tham số
class weights (từ train): [0.891, 1.238, 1.351, 1.393, 1.351, 1.592, 0.446]

best macro-F1 val = 0.2725 @ epoch 11
EARLY STOP ở epoch 26 (15 epoch không cải thiện)
~20s/epoch
```

⚠️ **Đây là số mốc 1-fold/1-seed, KHÔNG có CI, không phải kết quả báo cáo** (AGENTS.md §3.5).

### Đường cong nói gì

| | epoch 1 | epoch 11 (best) | epoch 26 |
|---|---|---|---|
| train loss | 1.961 | 1.774 | 1.641 |
| val loss | 1.989 | 2.471 | 2.589 |
| macro-F1 val | 0.099 | **0.273** | 0.253 |

- Chance của 7 lớp: macro-F1 ≈ 0.10, CE ≈ ln7 = 1.946. Model **có** học (0.27 > 0.10).
- Nhưng train loss chỉ giảm 1.96 → 1.64: **chưa fit nổi tập train**.
- Trong khi đó val loss **tăng 30%**. Đây KHÔNG phải overfit kinh điển — overfit thì train loss phải lao xuống gần 0.

### Chẩn đoán: BatchNorm với batch_size=2

DenseNet121 của MONAI mặc định `norm="batch"`. Với batch 2 mẫu:
- lúc **train**, BN chuẩn hoá bằng thống kê của chính batch → loss trông bình thường;
- lúc **eval**, BN dùng running stats gộp từ hàng trăm batch 2-mẫu → thống kê nhiễu, phân phối lệch hẳn so với lúc train.

Chữ ký khớp chính xác: train ổn / val phân kỳ *dù model chưa fit*. Đây là lý do nnU-Net và phần lớn pipeline 3D y tế dùng InstanceNorm — khối 3D buộc batch phải nhỏ vì VRAM.

**Lỗi thiết kế của phiên S-034:** đặt `batch_size: 2` theo ràng buộc VRAM mà không đổi normalization cho khớp.

**Đã đụng file:**
- `src/models/densenet3d.py` — thêm tham số `norm`, mặc định **`instance`** (không phải `batch`); docstring ghi rõ bằng chứng.
- `configs/baseline_3dpatch.yaml` — `norm: instance`.
- `tests/test_models.py` — test chặn: nếu config đặt `norm: batch` thì bắt buộc `batch_size >= 8`.

**Quyết định & lý do:**
- **Chỉ đổi đúng MỘT biến (`norm`)**, giữ nguyên lr/batch/accum/epochs/augment. Đổi nhiều thứ cùng lúc thì lần chạy tới không nói được cái nào có tác dụng. Phương án đã loại: nâng batch_size lên 8 — cũng chữa được BN nhưng tốn VRAM và làm giảm số optimizer step.
- Giữ effective batch 16 (2 × 8): với 312 mẫu train là ~20 optimizer step/epoch. Ít, nhưng theo dõi trước, chưa đổi.

**Kết quả / số liệu:** `pytest` 120 passed, 8 skipped. ruff sạch. **Chưa chạy lại với `instance`** — chưa biết chẩn đoán có đúng không.

**Dang dở:**
- [ ] Chạy lại fold 1 với `norm: instance` và so với **0.2725**. Rẻ: ~20s/epoch, tối đa 20 phút.
- [ ] Rủi ro chưa kiểm được ở local: không có MONAI để xác minh `DenseNet121(..., norm=...)` đúng tên tham số ở phiên bản MONAI trên Kaggle. Nếu sai sẽ `TypeError` ngay cell smoke test (rẻ, phát hiện sớm).
- [ ] Baseline 2.5D (T6.1) — cắt được nếu trễ.
- [ ] `src/data/transforms.py` giờ ĐÃ chạy thật lần đầu trên Kaggle (fold 1 train xong) nhưng 9 test của nó vẫn skip ở local.

**Điểm vào phiên sau:** Kaggle notebook 03 → Restart & Run All. Cell 1 phải qua (kiểm `norm=instance` hợp lệ), rồi so macro-F1 với 0.2725. Nếu val loss hết phân kỳ ⇒ chẩn đoán đúng, ghi vào WORKLOG rồi mới tính chuyện tune tiếp.

**Cảnh báo cho tool sau:**
- **Đừng so số mới với 0.2725 như một cuộc đua.** 0.2725 là mốc của một cấu hình có lỗi thiết kế đã biết; giá trị của nó là làm chứng cho chẩn đoán BN, không phải làm chuẩn để vượt.
- W2 chỉ cần *một* số mốc. Tune sâu là việc W4 (comparison protocol, Spec Sheet §3). Đừng biến W2 thành cuộc săn hyperparam.



## S-037 · 2026-07-27 16:20 · claude-code

**Mục tiêu phiên:** Người dùng yêu cầu: rà soát toàn bộ đường chạy TRƯỚC khi tốn thêm session GPU, không để lặp lại chuyện "chạy xong mới phát hiện quên sửa".

**Nhánh / commit:** `main` · `b53ff9b` → *(commit đang chờ)*

### 5 lỗi tìm được khi rà, tất cả đều sẽ nổ hoặc âm thầm làm hỏng kết quả

**1. `norm: instance` mất affine — đã tải source MONAI 1.3.2 về đọc để xác nhận.**
`get_norm_layer("instance")` gọi `nn.InstanceNorm3d(num_features=C)`, mà PyTorch mặc định `affine=False`. Nghĩa là bản sửa BatchNorm ở S-036 sẽ bỏ mất scale/shift học được ở **mọi** lớp norm — một suy giảm âm thầm khác. Sửa: `DEFAULT_NORM = ("instance", {"affine": True})`; config viết `norm: ["instance", {affine: true}]`; thêm `normalize_norm_spec()` vì YAML đọc ra **list** còn MONAI ghi hợp đồng là `str | tuple`.

**2. Nhãn cache chưa bao giờ được đối chiếu với `splits/`.** `CachedLesionDataset` lấy nhãn từ split và **bỏ qua** nhãn trong `.npz`. Nếu build cache ghi lệch ID, train vẫn chạy trơn, loss vẫn giảm, metric vẫn ra số — toàn bộ kết quả vô nghĩa mà không có dấu hiệu nào. Đây là rủi ro nặng nhất còn sót. Sửa: `find_label_mismatches()` + cổng chặn trong `train()` (cờ `verify_labels`, mặc định bật) + kiểm ở cell smoke test.

**3. Resume không kiểm kiến trúc.** `last.pt` của run BatchNorm gặp config InstanceNorm sẽ hoặc nổ khó hiểu, hoặc tệ hơn: khôi phục `epochs_without_gain=15` rồi early-stop ngay ở epoch 27 mà không train gì — trông y như "đã chạy xong". Sửa: lưu `model_fingerprint` trong checkpoint, resume mà lệch thì raise kèm cách xử lý.

**4. `RandomRot90InPlane` giả định mặt phẳng vuông.** k=1/3 hoán vị X,Y; crop hiện 96×96 nên vô hại, nhưng kill-switch VRAM trong plan có phương án hạ crop xuống 64×64×32 — lúc đó shape đổi giữa epoch và vỡ collate. Sửa: mặt phẳng không vuông thì chỉ xoay 180°.

**5. Notebook cài `monai` không pin, lại kéo cả dependency.** Sửa: `--no-deps` (pip tuyệt đối không đụng torch/CUDA của Kaggle). **Cố ý không pin version** — pin 1.3.2 có thể không import được với torch mới của Kaggle, và một run chết vì lý do đó tốn hơn là mất tính pin; bù lại version thật được in ra và `train()` ghi `torch X | monai Y` vào log.

### Một chỗ dự án đang tự nhận sai về mình

`deterministic: true` **không** cho tái lập bit-exact: docstring của chính MONAI ghi DenseNet `spatial_dims=3` là non-deterministic trên CUDA. Seed cố định cho phép lặp lại *thí nghiệm*, không phải lặp lại từng chữ số. Đã ghi vào config để báo cáo không tuyên bố quá tay — và là một lý do nữa để mọi số đều kèm CI.

**Đã đụng file:**
- `src/models/densenet3d.py` — `DEFAULT_NORM`, `normalize_norm_spec()`.
- `src/data/dataset.py` — `find_label_mismatches()`.
- `src/data/transforms.py` — guard mặt phẳng không vuông.
- `src/train/run.py` — cổng chặn nhãn, `model_fingerprint` khi resume, log version torch/monai.
- `configs/baseline_3dpatch.yaml` — `norm` dạng tuple, ghi chú về determinism.
- `notebooks/03_train_baseline.ipynb` — cell smoke test giờ kiểm: nhãn, augment (20 lần, shape + finite), loại norm layer thực tế + affine, forward trên GPU rồi giải phóng VRAM.
- `tests/test_label_integrity.py` (4 test) — MỚI; `tests/test_models.py` — +2 test.

**Quyết định & lý do:**
- **Tải source thư viện về đọc thay vì đoán** (`pip download --no-deps monai==1.3.2`). Local không cài được MONAI, nhưng "không kiểm được ở local" không phải lý do để đoán — chính cách này bắt được lỗi affine.
- Những gì vẫn không kiểm được ở local (forward thật, AMP, augment trên tensor thật) thì **chuyển thành assert trong cell smoke test** — chạy trước khi tốn GPU, hỏng thì hỏng trong 1 phút.

**Kết quả / số liệu:** `pytest` **126 passed, 8 skipped** (120 → 134 test). ruff sạch. Quality gate PASS. Chưa chạy lại trên Kaggle.

**Dang dở:**
- [ ] Chạy fold 1 với InstanceNorm(affine=True) và so với mốc **0.2725**.
- [ ] Baseline 2.5D (T6.1).

**Điểm vào phiên sau:** Kaggle notebook 03 → Restart & Run All. Cell 1 phải in `norm layers: {'InstanceNorm3d': N} | affine: {True}` và `nhãn cache vs splits: KHỚP TOÀN BỘ`. Chỉ khi đó cell train mới đáng chạy.

**Cảnh báo cho tool sau:**
- **Đây là quy trình bắt buộc từ nay:** trước khi bàn giao thứ gì tốn GPU, phải rà hết đường chạy; thứ nào không kiểm được ở local thì tải source thư viện về đọc, hoặc biến thành assert rẻ tiền chạy trước phần tốn kém. Người dùng đã nêu yêu cầu này sau khi mất một session vì lỗi BatchNorm.
- Lần chạy tới đổi **hai** thứ so với mốc 0.2725: BatchNorm → InstanceNorm, và affine. Không tách được nữa vì `instance` không affine là cấu hình vô nghĩa, không đáng tốn một run để đo.



## S-038 · 2026-07-27 16:45 · claude-code

**Mục tiêu phiên:** Sửa lỗi resume nạp checkpoint của kiến trúc cũ — lỗ hổng nằm trong chính bản vá S-037.

**Nhánh / commit:** `main` · `1e4d8c2` → *(commit đang chờ)*

**Đã xác nhận chạy được trên Kaggle (torch 2.10.0+cu128 · monai 1.6.0):**
```
nhãn cache khớp splits/ trên toàn bộ 394 ca      <- cổng chặn S-037 hoạt động
model=densenet121_3d | 11.403.463 tham số        <- khớp bản BN (IN affine=True cùng số tham số)
```
Cell smoke test qua ⇒ `norm=("instance", {"affine": True})` **hợp lệ với MONAI 1.6.0**, không chỉ 1.3.2 như bản đã đọc source.

**Lỗi:** `RuntimeError` giữa `model.load_state_dict(state["model"])` — `last.pt` của run BatchNorm (cùng session Kaggle, `/kaggle/working` không bị xoá) bị nạp vào model InstanceNorm.

**Lỗ hổng nằm ở đâu:** chốt kiểm fingerprint thêm ở S-037 viết là
```python
if previous is not None and previous != model_fingerprint:   # <- `is not None`
```
Checkpoint cũ được ghi **trước** khi trường `model_fingerprint` tồn tại ⇒ `previous is None` ⇒ chốt bỏ qua ⇒ lọt thẳng vào `load_state_dict`. Ý định "tương thích ngược với checkpoint đời cũ" chính là chỗ thủng. **Không biết thì phải từ chối, không được mặc định là khớp.**

**Sửa hai lớp:**
1. **Lưới thật (cấu trúc):** `run_dir(config, fold)` = `fold{N}_{sha1(khối model)[:8]}`. Hai kiến trúc khác nhau **không bao giờ dùng chung thư mục**, nên tình huống này không còn phát sinh được. Hash **chỉ** khối `model:` — đổi `lr`/`epochs` vẫn resume được, vì mất tiến trình một run dài trên Kaggle là mất thật. Lợi ích kèm theo: kết quả bản BN và bản IN nằm cạnh nhau, so được, không đè nhau.
2. **Lưới hai (chốt kiểm):** bỏ `is not None` — fingerprint vắng mặt cũng bị coi là không khớp.

**Đã đụng file:**
- `src/train/run.py` — `model_fingerprint()`, `run_dir()`; `train()` dùng `run_dir`; chốt kiểm chặt lại; trả thêm `run_dir` trong kết quả.
- `notebooks/03_train_baseline.ipynb` — cell đọc số dùng `run_dir()`, in kèm mốc cũ 0.2725 để so ngay tại chỗ.
- `tests/test_run_dir.py` — MỚI, 8 test: BN ≠ IN, IN affine ≠ IN không affine, fold khác nhau, đổi lr/epochs vẫn cùng thư mục, hash ổn định và không phụ thuộc thứ tự khoá.

**Quyết định & lý do:**
- **Chặn bằng cấu trúc thay vì bằng kiểm tra.** Một chốt kiểm chỉ tốt bằng người viết ra nó — S-037 là bằng chứng. Tách thư mục theo hash làm cho lỗi không xảy ra được, thay vì bắt nó khi đã xảy ra. Chốt kiểm vẫn giữ làm lưới hai.
- Không hash toàn bộ config: sẽ mất resume mỗi lần chỉnh một hyperparam vặt.

**Kết quả / số liệu:** `pytest` **134 passed, 8 skipped** (126 → 142 test). ruff sạch. Vẫn **chưa có số của bản InstanceNorm**.

**Dang dở:**
- [ ] Chạy fold 1 với InstanceNorm(affine=True), so với mốc 0.2725.
- [ ] Baseline 2.5D (T6.1).

**Điểm vào phiên sau:** Kaggle notebook 03 → Restart & Run All. Run mới sẽ ghi vào `runs/baseline_3dpatch/fold1_<hash>/`, không đụng `fold1/` cũ. Cell cuối in thẳng "mốc cũ / lần này".

**Cảnh báo cho tool sau:**
- `/kaggle/working` **sống xuyên suốt một session**, không phải chạy lại là sạch. Mọi thứ ghi ra đó phải giả định có sẵn bản cũ.
- Thư mục run đời cũ tên `fold1/` (không hash) là của bản BatchNorm S-036. Đừng đọc nhầm số trong đó thành số của bản InstanceNorm.



## S-039 · 2026-07-27 17:30 · claude-code

**Mục tiêu phiên:** Người dùng báo bản InstanceNorm không học. Xác định nguyên nhân và ngừng đoán.

**Nhánh / commit:** `main` · `6c5fb3a` → *(commit đang chờ)*

### Kết quả chạy thật — InstanceNorm SẬP

```
epoch 1/60 | train 1.9496 | val 1.9237 | macro-F1 0.0668 | 25s
epoch 2/60 | train 1.9490 | val 1.9132 | macro-F1 0.0668 | 25s
epoch 3/60 | train 1.9278 | val 1.9121 | macro-F1 0.0668 | 24s
epoch 4/60 | train 1.9291 | val 1.9150 | macro-F1 0.0668 | 24s
```
macro-F1 **y hệt** qua 4 epoch = đoán đúng một lớp cho toàn bộ 82 ca val. train loss ≈ 1.94 = **ln 7** = mức ngẫu nhiên.

So sánh cùng mốc, bản BatchNorm (S-036): 0.099 → 0.115 → 0.183 → 0.205. Rõ ràng đang học.

| norm | macro-F1 val | ghi chú |
|---|---|---|
| batch | **0.2725** @ epoch 11 | chạy thật, fold 1 seed 1337 |
| instance + affine | 0.0668 đứng yên | SẬP |
| group | chưa có số | |

### Nguyên nhân: InstanceNorm ngay trước global average pooling

Đuôi DenseNet là `norm5 → relu → AdaptiveAvgPool(1) → linear`. `InstanceNorm3d` chuẩn hoá **từng kênh, từng mẫu** trên toàn bộ chiều không gian ⇒ mean mỗi kênh bị ép về 0. Global average pooling ngay sau đó lấy đúng đại lượng đó làm đặc trưng phân loại.

nnU-Net dùng InstanceNorm thành công vì nó làm **segmentation** — không có global pooling. Tôi đã bê lập luận từ segmentation sang classification mà không kiểm chỗ khác biệt. GroupNorm không dính lỗi này (chuẩn hoá theo *nhóm* kênh, mean từng kênh trong nhóm vẫn khác nhau và sống sót qua pooling) — đó cũng là lý do GroupNorm mới là khuyến nghị chuẩn cho classification batch nhỏ.

### Và chẩn đoán BatchNorm ở S-036 có thể đã sai

Val loss tăng ở bản BN có thể chỉ là overfit thường gặp của 11M tham số trên 312 mẫu, không phải bệnh lý BatchNorm. Không có bằng chứng nào cho thấy BN là vấn đề; bằng chứng có được lại cho thấy BN là phương án tốt nhất đang có.

### Sửa: ngừng đoán, đo trước khi tốn GPU

- `src/train/sanity.py` — MỚI. `overfit_check()` nhồi 8 mẫu (trải nhiều lớp) vào model vài chục bước: model lành mạnh phải **thuộc lòng** (loss → ~0, acc → 1.0). `verdict()` đọc kết quả thành HỌC ĐƯỢC / CHẬM / SẬP, so với mốc `ln(num_classes)`. `pick_diverse_subset()` bảo đảm tập con trải nhiều lớp — lấy 8 mẫu đầu danh sách có thể trúng toàn một lớp và chứng minh sai.
- `notebooks/03_train_baseline.ipynb` — mục **1b** mới: chạy phép thử cho **cả ba** phương án norm (~30 giây/phương án) và in bảng so sánh. Cổng chặn: nếu `norm` trong config bị xếp SẬP thì **từ chối chạy train**. Cell KHÔNG tự sửa config — config vẫn là nguồn sự thật duy nhất (AGENTS.md §8).
- `configs/baseline_3dpatch.yaml` — trả `norm` về **`batch`**: lựa chọn duy nhất có số thật.
- `src/models/densenet3d.py` — `DEFAULT_NORM = "batch"`; docstring ghi lại cả ba phương án kèm bằng chứng của từng cái.
- `tests/test_models.py` — bỏ luật "BN phải có batch ≥ 8" (nó mã hoá một giả thuyết chưa được chứng minh thành ràng buộc cứng); thay bằng: `norm` phải khai báo tường minh, và instance/group phải có affine=True.
- `tests/test_sanity.py` — MỚI, 10 test.
- Cell smoke test giờ đối chiếu **loại norm thật sự được dựng** với thứ config nói (bắt lỗi chính tả rơi về mặc định của MONAI).

**Quyết định & lý do:**
- **Config theo bằng chứng, không theo lý thuyết.** Hai lần liên tiếp tôi đổi kiến trúc dựa trên lập luận nghe hợp lý và cả hai lần đều tệ hơn. `batch` giữ nguyên cho tới khi bảng 1b nói khác.
- **Phép thử overfit là cổng chặn thường trực, không phải công cụ debug một lần.** Nó phân biệt "bài toán khó" với "pipeline hỏng" trong 30 giây — đúng thứ đáng ra phải có trước khi đổi `norm` lần đầu.
- Không tự sửa config trong notebook dù biết phương án nào thắng: số báo cáo phải tái lập từ config đã commit.

**Kết quả / số liệu:** `pytest` **145 passed, 8 skipped** (134 → 153 test). ruff sạch.

**Dang dở:**
- [ ] Chạy mục 0 → 1b trên Kaggle (~3 phút) lấy bảng so sánh 3 norm. **Chưa chạy train.**
- [ ] Sau khi có bảng: chốt `norm` trong config, rồi chạy train một lần.
- [ ] Nghi vấn còn treo, chưa đụng: 312 mẫu với effective batch 16 = ~20 lần cập nhật trọng số mỗi epoch.

**Điểm vào phiên sau:** Kaggle notebook 03 → Restart & Run, **dừng sau mục 1b**, gửi bảng. Đừng chạy cell train trước khi có bảng đó.

**Cảnh báo cho tool sau:**
- **Đừng bê lập luận từ segmentation sang classification.** InstanceNorm hợp với nnU-Net vì nnU-Net không có global average pooling; DenseNet thì có. Sự khác biệt đó tốn một run 20 phút.
- macro-F1 **đứng yên tuyệt đối** qua nhiều epoch = model đoán một lớp duy nhất, không phải "học chậm". Kèm train loss ≈ ln(số lớp) thì chắc chắn.
- Mốc so sánh hợp lệ hiện tại vẫn là **0.2725 (BatchNorm)**.



## S-040 · 2026-07-27 18:05 · claude-code

**Mục tiêu phiên:** Đọc bảng phép thử overfit và chốt thay đổi cho run kế tiếp bằng bằng chứng.

**Nhánh / commit:** `main` · `c285efa` → *(commit đang chờ)*

### Bảng đo (Kaggle, 8 mẫu trải 7 lớp, 160 bước, lr 1e-3, không augment/class-weight)

```
norm              loss đầu  loss cuối    acc  kết luận
batch                2.225      0.009   1.00  HỌC ĐƯỢC
instance+affine      2.242      0.581   1.00  HỌC ĐƯỢC
group(8)             3.282      0.010   1.00  HỌC ĐƯỢC
```

### Bảng này bác bỏ chẩn đoán của tôi ở S-039

Tôi kết luận InstanceNorm **sập vì global average pooling xoá mất tín hiệu**. Sai: IN đạt accuracy 1.00 trên phép thử. Nó **chậm hơn ~60 lần** (loss cuối 0.581 so với 0.009) chứ không mất khả năng học. Cơ chế tôi mô tả có thể góp phần làm chậm, nhưng "sập" là cách đọc quá tay từ một run 4 epoch.

`batch` và `group` khoẻ **ngang nhau** — phép thử không tách được hai cái này.

### Điều bảng nói to hơn: model đang thiếu BƯỚC CẬP NHẬT, không thiếu khả năng học

Đặt cạnh nhau:

| | số bước | lr | kết quả |
|---|---|---|---|
| phép thử overfit (8 mẫu) | 160 | 1e-3 | loss 0.009, thuộc lòng |
| run thật BatchNorm (312 mẫu) | ~520 (26 epoch × 20) | 3e-4 | loss 1.96 → **1.64** |

Ngẫu nhiên là ln 7 = 1.946. Sau 520 bước, train loss mới nhích được 0.32 — model **mới chỉ khởi động**, chưa hề đến giai đoạn overfit mà tôi đã diễn giải ở S-036. Nguyên nhân số học rất đơn giản: 312 mẫu / (batch 2 × accum 8) = **~20 bước cập nhật mỗi epoch**.

Và bản InstanceNorm "sập" ở 4 epoch = **80 bước**. Với một cấu hình chậm gấp 60 lần, 80 bước chưa nói lên được gì. Cả hai kết luận trước của tôi đều rút ra từ một chế độ tối ưu hoá quá yếu để phán xét bất cứ điều gì.

**Đã đụng file:**
- `configs/baseline_3dpatch.yaml` — `accum_steps` 8 → **2** (hiệu dụng 16 → 4, ~78 bước/epoch, gấp 4). `norm` giữ `batch`. Ghi cả bảng đo vào comment.
- `AGENTS.md` §7 — sửa khuyến nghị: **batch hiệu dụng chọn theo kích thước dataset, không theo VRAM**. VRAM chỉ quyết định `batch_size`; `accum_steps` là lựa chọn tối ưu hoá và tăng nó **không** làm epoch nhanh hơn.
- `tests/test_models.py` — bỏ ràng buộc "hiệu dụng 16–32", thay bằng: trần 32 (VRAM) và **≥ 40 bước cập nhật/epoch**.

**Quyết định & lý do:**
- **Đổi đúng MỘT thứ: `accum_steps`.** Giữ `norm: batch` (có số thật) để lần chạy này so được thẳng với mốc 0.2725. Phương án đã loại: đổi `norm` sang `group` — cũng đáng thử, nhưng gộp hai thay đổi thì không biết cái nào có tác dụng, và bảng đo cho thấy norm không phải nút thắt.
- **Không đổi `lr`.** Cũng là một cách tăng tốc, nhưng thêm biến thứ hai. Nếu 78 bước/epoch vẫn ì thì lr là nút tiếp theo.
- Cùng thời gian mỗi epoch: số lần forward/backward không đổi, chỉ đổi tần suất `optimizer.step()`. Run vẫn ~25 phút.

**Kết quả / số liệu:** `pytest` **145 passed, 8 skipped**. ruff sạch. Chưa chạy run mới.

**Dang dở:**
- [ ] Chạy fold 1 với `accum_steps: 2`, so với **0.2725**.
- [ ] `norm: group(8)` — ứng viên tiếp theo, chạy **riêng** sau khi chốt chế độ tối ưu hoá.
- [ ] Baseline 2.5D (T6.1).

**Điểm vào phiên sau:** Kaggle notebook 03 → Restart & Run All (giờ chạy hết, gồm cả cell train). Run ghi vào thư mục hash mới. Cell cuối in thẳng "mốc cũ 0.2725 / lần này".

**Cảnh báo cho tool sau:**
- **Đừng chẩn đoán từ 4 epoch khi mỗi epoch chỉ có 20 bước cập nhật.** Hai chẩn đoán sai liên tiếp (S-036 "BatchNorm hỏng", S-039 "InstanceNorm sập vì pooling") đều sinh ra từ chỗ này. Số bước cập nhật = mẫu / (batch × accum) — tính nó trước khi diễn giải bất kỳ đường cong nào.
- Phép thử overfit ở mục 1b dùng lr và tần suất cập nhật **khác** run thật (1e-3, step mỗi batch). Nó trả lời "kiến trúc có học nổi không", **không** trả lời "cấu hình train này tốt không". Đừng đọc quá phạm vi đó — đúng lỗi tôi vừa mắc theo chiều ngược lại.



## S-041 · 2026-07-27 18:40 · claude-code

**Mục tiêu phiên:** Đọc kết quả run `accum_steps: 2` và chốt trạng thái baseline W2.

**Nhánh / commit:** `main` · `577f0d1` → *(commit đang chờ)*

### Kết quả

```
{'fold': 1, 'best_macro_f1': 0.26469, 'best_epoch': 11, 'seed': 1337,
 'run_dir': '/kaggle/working/runs/baseline_3dpatch/fold1_4c2cf705'}
```

| run | norm | accum | bước/epoch | macro-F1 val | best epoch |
|---|---|---|---|---|---|
| S-036 | batch | 8 | ~20 | **0.2725** | 11 |
| S-041 | batch | 2 | ~78 | **0.2647** | 11 |

Gấp 4 lần số bước cập nhật ⇒ **không đổi gì**. Chênh 0.008 trên 82 ca val nằm gọn trong nhiễu (thêm nữa DenseNet 3D là non-deterministic trên CUDA). Cùng `best_epoch = 11` ở cả hai run.

### Giả thuyết thứ ba cũng bị bác bỏ

Ba chẩn đoán, ba lần sai:

1. S-036 — "BatchNorm với batch 2 làm val loss phân kỳ" → sai, đổi sang InstanceNorm tệ hơn hẳn.
2. S-039 — "InstanceNorm sập vì global average pooling" → sai, phép thử overfit cho accuracy 1.00.
3. S-040 — "model thiếu bước cập nhật" → sai, gấp 4 lần bước không đổi kết quả.

Điểm chung: cả ba đều là **suy luận từ đường cong**, và cả ba đều tốn một run để bác bỏ. Bài học ghi vào đây để không lặp lại: baseline này ổn định quanh **0.26–0.27** và không bị chặn bởi thứ gì trong đám hyperparam tôi đã thử.

### Và tôi đã kéo dự án ra ngoài phạm vi W2

`docs/W2_plan.md` mục "Không phải việc của W2" ghi rõ: W2 chỉ cần **1 fold ra số mốc**; tune model thuộc W4 (comparison protocol, Spec Sheet §3), CV + CI thuộc W3. Ba run vừa rồi là săn hyperparam ở tuần không dành cho việc đó — scope creep do tôi tạo ra, không phải do người dùng yêu cầu.

Các đòn bẩy thật sự cho chất lượng model đã nằm sẵn trong plan W4: **backbone pretrained** (MedicalNet ResNet-3D / Models Genesis — 312 mẫu train from scratch là điều kiện khó nhất), fusion v1 phase-attention, xử lý lớp hiếm. Không có lý do gì để đoán tiếp ở W2.

**Đã đụng file:**
- `WORKLOG.md` — entry này.
- `configs/baseline_3dpatch.yaml` — giữ `accum_steps: 2` (không tệ hơn, và hiệu dụng 4 hợp với 312 mẫu hơn), ghi rõ hai run cho cùng kết quả.

**Quyết định & lý do:**
- **Chốt baseline W2 ở macro-F1 val ≈ 0.26–0.27 (fold 1, seed 1337) và DỪNG tune.** Hai cấu hình khác nhau cho cùng con số ⇒ đây là mốc ổn định, đủ để làm điểm so cho W3/W4. Phương án đã loại: thử tiếp `lr`, `group`, giảm augment — mỗi cái một run 25 phút, và ba lần trước đã cho thấy tỉ lệ trúng của kiểu đoán này.
- **Sang W3 theo đúng plan:** `src/eval/bootstrap.py` (CI mức bệnh nhân ≥2000 lần), chạy đủ 5-fold, bảng CV có CI. Đó mới là deliverable, và có CI rồi thì mọi so sánh sau này mới có nghĩa — chênh 0.008 như trên hiện không thể phân biệt với nhiễu vì **chưa có CI**.

**Kết quả / số liệu:** macro-F1 val fold 1 = **0.2647** (accum 2) và **0.2725** (accum 8). `pytest` 145 passed, 8 skipped.

**Dang dở:**
- [ ] **Chưa xem đường cong `train_log.csv` của run này.** Cần biết train loss cuối cùng dừng ở đâu để phân biệt underfit / overfit — dữ kiện này thuộc về W4, khi chọn giữa pretrained và giảm capacity.
- [ ] Baseline 2.5D (T6.1) — cắt được, W2_plan xếp nó vào "task cắt được nếu trễ".
- [ ] `norm: group(8)` — ứng viên còn treo, để W4 làm cùng bảng ablation, không chạy lẻ.

**Điểm vào phiên sau:** Bắt đầu W3 — `src/eval/metrics.py` đã có, viết `src/eval/bootstrap.py` (bootstrap mức bệnh nhân, stratified, ≥2000 lần), rồi `src/eval/run.py` đọc `val_probs_best.npz` đã lưu sẵn. Chạy được 5-fold mà **không cần train lại** cho fold 1.

**Cảnh báo cho tool sau:**
- **Đừng tune baseline ở W2.** Ba run đã chứng minh baseline ổn định ~0.27 và không nhạy với các hyperparam đã thử. Đòn bẩy thật (pretrained backbone) nằm ở W4 và đã có trong plan.
- **Không so hai con số khi chưa có CI.** 0.2725 với 0.2647 nhìn khác nhau nhưng trên 82 ca val thì không phân biệt được. Đây chính là lý do AGENTS.md §3.5 bắt mọi số phải kèm CI — và là việc đầu tiên của W3.



## S-042 · 2026-07-27 19:05 · claude-code

**Mục tiêu phiên:** Đọc đường cong đầy đủ của run `accum_steps: 2` (fold1_4c2cf705).

**Nhánh / commit:** `main` · `2f7617d` → *(commit đang chờ)*

### Ba dữ kiện mà con số tóm tắt che mất

**1. Model chưa bao giờ fit nổi tập train.**
```
epoch 1:  train 1.9619    epoch 26: train 1.5820
```
Ngẫu nhiên = ln 7 = 1.946. Sau 26 epoch (~2000 bước với accum 2), train loss mới đi được 0.38 dưới mức đoán bừa. Trong khi phép thử overfit đưa **8 mẫu** về 0.009 chỉ với 160 bước.

⇒ **Bác bỏ dứt điểm chẩn đoán S-036.** Tôi đọc "val loss tăng" thành overfitting; một model chưa fit nổi tập train thì không thể đang overfit theo nghĩa thông thường. Cả hướng suy luận đó sai từ đầu.

**2. Val loss cao hơn mức ngẫu nhiên ngay từ epoch 1** (2.2326 > 1.946), rồi dao động 2.22 – 3.57. Model đoán **sai một cách tự tin** trên val ngay từ đầu: đặc trưng học được không chuyển sang val.

**3. macro-F1 val dao động không xu hướng — và đây là vấn đề nghiêm trọng nhất.**
```
0.141 0.163 0.146 0.115 0.159 0.164 0.149 0.159 0.189 0.147 [0.265] 0.216
0.145 0.175 0.234 0.219 0.186 0.208 0.236 0.192 0.191 0.215 0.209 0.193 0.239 0.255
```
Epoch 11 không phải cực trị thật, nó là **lần bốc may nhất trong 26 lần**.

### Hệ quả về tính hợp lệ: 0.2647 là con số lệch lạc quan

Chọn epoch tốt nhất theo macro-F1 trên **82 ca val** là chọn nhiễu. Đây đúng là bệnh lý mà AGENTS.md §3.5 cấm dưới tên *best-of-many-seeds*, chỉ khác là *best-of-many-epochs*. Cả hai mốc đã ghi (0.2725 và 0.2647) đều mang thiên lệch này, và cả hai đều nằm gọn trong dải dao động của chính chúng — **không có bằng chứng nào cho thấy hai cấu hình đó khác nhau**.

Không phải chuyện hyperparam. Là chuyện con số báo ra có nghĩa gì.

**Đã đụng file:**
- `src/train/run.py` — lưu thêm `val_probs_last.npz` (ghi đè mỗi epoch). Để W3 đối chiếu ước lượng theo best-epoch với ước lượng **không qua chọn lọc**. Không tốn thêm gì; các fold 2–5 của W3 sẽ có sẵn cả hai.
- `WORKLOG.md` — entry này.

**Quyết định & lý do:**
- **Không đề xuất run mới cho fold 1.** Đường cong cho thấy nút thắt không nằm ở hyperparam: model không fit nổi 312 mẫu trong khi fit 8 mẫu dễ dàng. Ứng viên hợp lý nhất là **augmentation quá mạnh** — `rot90` in-plane sinh 4 hướng × 4 tổ hợp lật = 16 biến thể, mà xoay 90° trên lát cắt ngang bụng không phải biến đổi giải phẫu hợp lệ (gan có hướng cố định). Ghi lại làm ứng viên cho **bảng ablation W4**, không chạy lẻ ở W2. Đã đoán sai ba lần, không đoán lần thứ tư.
- Giữ nguyên toàn bộ config. Baseline W2 chốt ở ≈0.27 **kèm cảnh báo thiên lệch chọn lọc**.

**Kết quả / số liệu:** Đường cong đầy đủ ghi ở trên. `pytest` 145 passed, 8 skipped.

**Dang dở:**
- [ ] W3: `src/eval/bootstrap.py` → CI cho fold 1 từ `val_probs_best.npz` đã có (chạy CPU, không tốn GPU).
- [ ] W3: train fold 2–5 (~25 phút/fold) → bảng CV có CI.
- [ ] W4: ablation augmentation (đặc biệt `rot90_prob`), backbone pretrained, `norm: group(8)`.

**Điểm vào phiên sau:** Viết `src/eval/bootstrap.py` và chạy trên `val_probs_best.npz` của fold 1. CI đó sẽ định lượng đúng dải nhiễu vừa quan sát — dự đoán: rất rộng trên 82 bệnh nhân.

**Cảnh báo cho tool sau:**
- **Đừng báo macro-F1 của best-epoch như một điểm ước lượng.** Trên 82 ca val nó là max của vài chục lần bốc nhiễu. Báo kèm CI, và đối chiếu với `val_probs_last.npz`.
- **Train loss so với ln(số lớp) là dữ kiện đầu tiên phải nhìn**, trước mọi diễn giải về overfit. 1.58 so với 1.946 nghĩa là model gần như chưa học được gì trên tập train — mọi câu chuyện về regularization/normalization đều vô nghĩa cho tới khi con số đó xuống thật.



## S-043 · 2026-07-27 20:30 · claude-code

**Mục tiêu phiên:** Người dùng yêu cầu khảo sát/nghiên cứu và lập plan chi tiết trước khi train tiếp, chấm dứt kiểu vừa train vừa sửa.

**Nhánh / commit:** `main` · `fdef36c` → *(commit đang chờ)*

### Phát hiện gốc: có một mốc đối chiếu mà tôi chưa bao giờ tra

PDF của challenge nằm sẵn trong `docs/` từ đầu và tôi chưa đọc. Leaderboard chính thức:

| | macro-F1 (test-104) | Kappa |
|---|---|---|
| Đội nhất | 0.8322 | 0.7801 |
| **Baseline official** | **0.6083** | 0.5414 |
| Hạng 20–24 | 0.5047–0.6076 | |
| **Của ta** | **0.2647** (val fold 1) | |

Metric của họ là `sklearn.f1_score(average='macro')` — **khớp `src/eval/metrics.py`**, đã thêm test đối chiếu trực tiếp. Baseline của họ **không dùng pretrained**.

⇒ Trực giác "có gì đó sai" là đúng, nhưng ba chẩn đoán cụ thể (S-036 BatchNorm, S-039 InstanceNorm, S-040 số bước cập nhật) đều trượt vì tôi debug mà không biết ngưỡng đạt được là bao nhiêu.

### Bảng đối chiếu protocol — đọc từ code baseline official

Nguồn: `LMMMEng/LLD-MMRI2023` (`main/README.md`, `main/train.py`, `main/datasets/`).

| | Official (0.6083) | Của ta trước phiên này |
|---|---|---|
| epochs | **300**, best @ **216** | 60, early stop @ 26 |
| early stopping | không có | patience 15 |
| lr | 1e-4 | 3e-4 |
| **weight decay** | **0.05** | **1e-5** (chênh 5000 lần) |
| warmup | 5 epoch, warmup-lr 1e-6 | không có |
| min_lr cosine | 1e-5 | 0 |
| loss | `nn.CrossEntropyLoss()` trần | CE + class weights |
| batch hiệu dụng | 8 (4 × 2 GPU) | 4 |
| augment | flip x/y/z · xoay **±10°** · random crop | flip x/y · **rot90** · nhiễu cường độ |
| chuẩn hoá | min-max [0,1] | clip pct + z-score |
| input | 112×112×14 (resize patch) | 96×96×48 (ROI mm-space) |

**Chẩn đoán lại toàn bộ chuỗi debug:** mọi đường cong tôi diễn giải đều đến từ model chạy 26/300 epoch, weight decay nhỏ hơn 5000 lần, augmentation sai kiểu. Không đường cong nào trong đó đủ điều kiện kết luận gì về normalization.

**Đã đụng file:**
- `configs/baseline_3dpatch.yaml` — toàn bộ khối `train` + `data.augment` theo recipe official, mỗi dòng kèm trích nguồn. Cũng phát hiện và sửa **khoá `early_stop_patience` bị lặp** (YAML lặng lẽ lấy giá trị cuối).
- `src/data/transforms.py` — `RandomRotateSmall` (±10°, `reshape=False`, `order=1`), `RandomTranslate3D` (thay `random_crop`, giữ nguyên shape), `resolve_axes` cho `flip_axes` cấu hình được. `rot90` và nhiễu cường độ **giữ lại nhưng tắt** để ablate ở W4.
- `src/train/run.py` — `build_param_groups()` **loại bias/norm khỏi weight decay** (bắt buộc khi wd=0.05; timm mặc định làm vậy, thiếu bước này thì decay đè lên tham số affine của BatchNorm); `build_scheduler()` warmup tuyến tính + cosine `SequentialLR`.
- `src/eval/bootstrap.py` — MỚI. Bootstrap **mức bệnh nhân, stratified, ≥2000 lần**, chặn ngay tại API nếu ai đó truyền ít hơn.
- `src/eval/run.py` — MỚI. CLI thuần, CPU: bảng metric ± CI từng fold + **gộp out-of-fold** (394 bệnh nhân thay vì 82) + cột best/last để đo thiên lệch chọn epoch. Có cổng chặn leakage: một bệnh nhân xuất hiện ở val của hai fold thì raise, không âm thầm đếm hai lần.
- `tests/test_protocol_conformance.py` — MỚI. Khoá config theo recipe official, gồm test bắt khoá YAML trùng lặp.
- `tests/test_bootstrap.py`, `test_eval_run.py` — MỚI. `tests/test_metrics.py` +3 test đối chiếu sklearn.
- `tests/test_transforms.py` — +13 test cho transform mới.
- `notebooks/03_train_baseline.ipynb` — mục **1c** mới: đo thật 2 epoch rồi ngoại suy 300 epoch, **raise nếu vượt 4 giờ**.
- `AGENTS.md` §5 — sửa giả định "n≈500 → tránh transformer" + thêm bảng mốc đối chiếu ngoài; §6 — lệnh eval.

**Quyết định & lý do (chốt với người dùng trước khi làm):**
- **Áp nguyên khối recipe official**, không sửa từng biến. Đây không phải đoán mà là tái lập công thức có số công bố; ablate khác biệt của ta *sau* khi đạt mốc.
- **Giữ DenseNet121-3D.** Protocol miễn phí (chỉ config), model tốn ~400 dòng và lệch Spec Sheet. Leaderboard cho thấy hạng 20–24 nằm trong 0.505–0.608 với đủ loại kiến trúc ⇒ ~0.6 không phải đặc quyền của UniFormer.
- **Giữ cache mm-space.** Cách cắt ROI (cửa sổ cố định 144mm³ so với cắt sát bbox rồi resize — tổn thương 20mm chỉ chiếm ~13% bề rộng của ta) là **giả thuyết 2**, có luật kích hoạt rõ ràng.

**Luật quyết định, chốt TRƯỚC khi chạy** (chống hợp lý hoá hậu nghiệm):

| Kết quả run 1 | Kết luận | Việc tiếp theo |
|---|---|---|
| ≥ 0.50 | protocol là nguyên nhân chính | chạy fold 2–5, dựng bảng CV + CI |
| 0.35–0.50 | protocol giải thích phần lớn | chạy nốt 5 fold rồi thử giả thuyết 2 |
| < 0.35 | protocol **không** phải nguyên nhân chính | dừng train, dựng cache lesion-tight |
| train loss > 1.5 sau 100 epoch | model không fit nổi ở mọi chế độ | xét port UniFormer-S 3D |

**Kết quả / số liệu:** `pytest` **177 passed, 8 skipped** (145 → 185 test). ruff sạch. Chưa chạy GPU.

**Dang dở:**
- [ ] Kaggle: chạy mục 0 → 1c lấy ước lượng giây/epoch. Rủi ro chưa đo: `scipy.ndimage.rotate` chạy CPU trên khối lớn gấp 2,5 lần official, nằm trên đường tới hạn.
- [ ] Nếu trong ngân sách → chạy fold 1 (~1,5–2,5 giờ), so với mốc 0.2647 theo luật quyết định.
- [ ] Sau đó fold 2–5, **mỗi session một fold** (300 epoch × 5 có thể vượt 12 giờ).

**Điểm vào phiên sau:** Kaggle notebook 03 → Restart & Run All. Mục 1c là cổng chặn cuối; chỉ chạy cell train khi nó báo trong ngân sách. Trong lúc chờ, `python -m src.eval.run --run-dir <thư mục run>` chạy được ngay trên CPU với output cũ.

**Cảnh báo cho tool sau:**
- **Có mốc đối chiếu ngoài rồi — dùng nó.** Bảng leaderboard nằm ở `AGENTS.md` §5. Đừng debug chất lượng model mà không đối chiếu trước; ba run GPU đã mất vì đúng lỗi đó.
- **`tests/test_protocol_conformance.py` là cố ý cứng.** Nó fail nghĩa là config đã trôi khỏi công thức đã kiểm chứng. Sửa config thì phải sửa cả test kèm lý do, đừng nới test cho qua.
- **weight decay 0.05 chỉ đúng khi có `build_param_groups`.** Bỏ bước loại bias/norm ra thì cùng con số đó cho một chế độ train hoàn toàn khác.
- Cột `best` trong bảng eval **lệch lạc quan** (chọn epoch trên chính tập val); luôn đọc kèm cột `last`.



## S-044 · 2026-07-27 21:10 · claude-code

**Mục tiêu phiên:** Xử lý kết quả cổng chặn đo thời gian ở mục 1c.

**Nhánh / commit:** `main` · `818cc14` → *(commit đang chờ)*

### Cổng chặn hoạt động đúng như thiết kế

```
batch hiệu dụng 8 · ~39 bước/epoch · lr 0.0001 · wd 0.05 · warmup 5 epoch
epoch thử 1: 63.0s | train 1.9618 | val 1.9484 | lr 2.08e-05
epoch thử 2: 56.5s | train 1.9291 | val 1.8963 | lr 4.06e-05
~56.5s/epoch × 300 epoch = 4.71 giờ  -> RuntimeError, chặn lại
```
Lần đầu tiên một vấn đề về ngân sách bị bắt **trước** khi tốn run, không phải sau.

Cũng xác nhận: warmup chạy đúng (lr đi 2.08e-05 → 4.06e-05, tức đang bò lên 1e-4 trong 5 epoch), `build_param_groups` và scheduler mới không nổ.

### Nhưng đọc kỹ con số thì có hai chuyện

**1. Ngưỡng 4 giờ là con số tôi tự bịa, không phải ràng buộc thật.** Ràng buộc thật: Kaggle cắt session ở 12h (AGENTS.md §7) và quota GPU ~30h/tuần. Một fold 4,71h thì **vừa thoải mái**. Vấn đề thật nằm ở chỗ khác: **5 fold × 4,71h ≈ 23,5 giờ**, ăn gần hết quota tuần.

**2. 56,5s/epoch so với ~20s trước đây — GPU đang ngồi chờ CPU.** Phần tính toán GPU vẫn ~20s; ~36s còn lại là augmentation (`scipy.ndimage.rotate` trên khối `[8,96,96,48]`) chạy trong DataLoader worker. Đây là lãng phí thuần tuý, sửa được mà **không đụng một chữ nào trong recipe official**.

**Đã đụng file:**
- `configs/baseline_3dpatch.yaml` — `num_workers` 2 → **4** (Kaggle có 4 vCPU), thêm `persistent_workers: true` và `prefetch_factor: 4`. Mặc định DataLoader **dựng lại toàn bộ worker sau mỗi epoch**; với ~39 bước/epoch thì chi phí đó chiếm tỉ lệ lớn, và recipe là 300 epoch = 300 lần dựng lại.
- `src/train/run.py` — `_build_loaders` → **`build_loaders`** (công khai), thêm hai khoá worker (có guard vì chúng nổ khi `num_workers=0`).
- `notebooks/03_train_baseline.ipynb` mục 1c — dùng thẳng `build_loaders` thay vì tự dựng loader; ngân sách đổi thành **6 giờ/fold** (từ ràng buộc session 12h) kèm cảnh báo riêng cho tổng 5 fold so với quota tuần; thông báo lỗi nêu rõ thứ tự xử lý: **kỹ thuật trước, recipe sau**.
- `tests/test_build_loaders.py` — MỚI, 6 test.

**Quyết định & lý do:**
- **Chỉ tối ưu hoá kỹ thuật, không đụng recipe.** `num_workers`/`persistent_workers`/`prefetch_factor` không thay đổi một phép toán nào trong train. Hạ `rotate_order` hay giảm `epochs` thì có — và chúng nằm ở cuối danh sách, chỉ dùng khi hết cách, kèm ghi WORKLOG.
- **Probe phải dùng đúng `build_loaders` của train thật.** Trước đó cell 1c tự dựng DataLoader; như vậy nó đo một thứ khác với thứ sẽ chạy, mà dự đoán đúng run thật là toàn bộ lý do nó tồn tại.
- **Ngân sách phải truy được về ràng buộc thật.** Một ngưỡng bịa ra sẽ hoặc chặn nhầm (như lần này) hoặc cho qua nhầm.

**Kết quả / số liệu:** `pytest` **177 passed, 9 skipped** (test mới cần torch nên skip ở local). ruff sạch. Ước lượng chưa đo lại — mục 1c sẽ tự trả lời ở lần chạy tới. Dự kiến: phần phụ thuộc CPU giảm khoảng một nửa ⇒ ~38s/epoch ⇒ ~3,2 giờ/fold ⇒ ~16 giờ cho 5 fold.

**Dang dở:**
- [ ] Chạy lại mục 1c để xác nhận đã trong ngân sách.
- [ ] Nếu đạt → chạy fold 1, so với mốc 0.2647 theo luật quyết định ở S-043.
- [ ] Nếu vẫn vượt: `rotate_order` 1 → 0, hoặc `rotate_prob` < 1.0. **Cả hai đều là lệch recipe**, phải ghi WORKLOG.

**Điểm vào phiên sau:** Kaggle notebook 03 → Restart & Run All. Mục 1c in thêm dòng `workers ... persistent ... prefetch ...` để đối chiếu.

**Cảnh báo cho tool sau:**
- **Phân biệt tối ưu hoá kỹ thuật với lệch recipe.** Số worker không đụng phép toán train; số epoch, góc xoay, order nội suy thì có. Chỉ nhóm thứ hai mới cần ghi là sai khác so với baseline official.
- Nếu `num_workers: 4` gây lỗi shared memory trên Kaggle, hạ xuống 3 — đó vẫn là tối ưu hoá kỹ thuật, không phải lệch recipe.

## S-045 · 2026-07-27 17:41 · codex

**Mục tiêu phiên:** Thêm slide recap Input → Output gần cuối deck overview.

**Nhánh / commit:** `main` · `ef1625b` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — thêm slide 11, minh hoạ `MRI_8phase.nii` → model 3D đa pha → output có uncertainty và `defer`; đổi toàn bộ chỉ số deck sang 12 slide.
- `slides/assets/synthetic-mri-8phase-contact-sheet.png` — asset MRI bụng tổng hợp 8 ô, không có dữ liệu hay định danh bệnh nhân.
- `slides/assets/ATTRIBUTION.md` — ghi provenance và giới hạn dùng của asset tổng hợp.

**Quyết định & lý do:**
- Dùng một file NIfTI đa pha mang tên `MRI_8phase.nii` như quy ước minh hoạ trên slide, không thay đổi data loader hay định dạng lưu trữ thật.
- Đặt nhãn phase bằng HTML thay vì trong ảnh raster để các tên C-pre, C+A, C+V, C+Delay, T2WI, DWI, In Phase, Out Phase luôn chính xác và đọc được.
- Asset được gắn nhãn rõ là dữ liệu tổng hợp; không có xác suất, nhãn chẩn đoán hay số kết quả giả lập.

**Kết quả / số liệu:** Quality gate PASS: Impeccable detect cho `slides/` và `reports/`, kiểm tra split, patient-data/checkpoint đều pass. Kiểm tra tĩnh: 12 slide, 12 chỉ số `/ 12`, đủ 8 phase. Browser không cho mở URL `file://`, nên không dùng cách vòng qua chính sách đó.

**Dang dở:**
- Không có việc treo cho phần slide.

**Điểm vào phiên sau:** Mở `slides/overview.html#11` trong trình duyệt local của người dùng nếu cần xem lại bằng mắt trên màn hình/máy chiếu thực tế.

**Cảnh báo cho tool sau:** Notebook chưa theo dõi `notebooks/notebookf104ced082.ipynb` là thay đổi ngoài phạm vi, đã được người dùng yêu cầu giữ nguyên; không stage, commit hay xoá nó.

## S-047 · 2026-07-27 18:07 · codex

**Mục tiêu phiên:** Thêm prototype giao diện output cho slide 11, minh hoạ trạng thái `defer`.

**Nhánh / commit:** `main` · `88ad2d7` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — thay output dạng danh sách ở slide 11 bằng prototype HTML/CSS có viewer heatmap tổng hợp, probability, malignant probability, uncertainty và `defer`.
- `WORKLOG.md` — ghi bàn giao phiên.

**Quyết định & lý do:**
- Dựng prototype bằng HTML/CSS và tái dùng contact sheet MRI tổng hợp — giữ slide dễ đọc, không tạo web app/API hay asset chứa dữ liệu bệnh nhân.
- Chọn trạng thái `defer` và không hiển thị nhãn dự đoán, phần trăm hay giá trị mô hình — uncertainty và việc cần review là luận điểm chính, đồng thời tránh tạo kết quả dự án giả.

**Kết quả / số liệu:** Quality gate PASS; Impeccable detect cho `slides/` và `reports/` đều pass. Kiểm tra tĩnh: 12 slide, 12 chỉ số `/ 12`, không còn `MRI_8phase.nii`; prototype có đủ probability, malignant probability, uncertainty, heatmap và `defer`.

**Dang dở:**
- Không có việc treo cho phần slide.

**Điểm vào phiên sau:** Mở `slides/overview.html#11` trong trình duyệt local nếu cần kiểm tra hiển thị thực tế trên máy chiếu.

**Cảnh báo cho tool sau:** Notebook chưa theo dõi `notebooks/notebookf104ced082.ipynb` là thay đổi ngoài phạm vi, đã được người dùng yêu cầu giữ nguyên; không stage, commit hay xoá nó.

## S-046 · 2026-07-27 17:51 · codex

**Mục tiêu phiên:** Đồng bộ tài liệu và slide recap với input thật: một ca gồm 8 file `.nii`.

**Nhánh / commit:** `main` · `06c85a4` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — slide 11 dùng “1 ca · 8 file .nii”, gắn tên file cho đủ 8 phase và bỏ mô tả một file NIfTI đa pha.
- `PRODUCT.md`, `docs/MRI_Classification_Spec_Sheet.md`, `docs/liver_mri_3d_classification_plan.md`, `docs/plan.md` — ghi contract thiết kế V1: picker đa tệp `.nii`, nhận diện phase theo tên, demo OOF validation, DICOM ZIP là mở rộng sau.

**Quyết định & lý do:**
- V1 được ghi nhận là đúng 8 file `.nii` cho mỗi bệnh nhân, không phải `MRI_8phase.nii` — vì đây là cấu trúc input thực tế đã xác nhận.
- Chỉ sửa slide/tài liệu; không tạo `webapp/`, endpoint, UI, API hay test thực thi — để contract được chốt trước khi triển khai.
- Ca demo được quy định là 3–5 prediction OOF trên validation, không dùng Test-104 và không commit dữ liệu/artefact bệnh nhân — giữ tính hợp lệ nghiên cứu và license.

**Kết quả / số liệu:** Quality gate PASS: Impeccable detect cho `slides/` và `reports/`, kiểm tra split, patient-data/checkpoint đều pass. Kiểm tra tĩnh: 12 slide, 12 chỉ số `/ 12`, đủ 8 nhãn file `.nii`, không còn `MRI_8phase.nii`.

**Dang dở:**
- Không có UI/API để chạy ở phiên này; các contract trên là thiết kế cho Sprint 3.

**Điểm vào phiên sau:** Khi bắt đầu Sprint 3, triển khai từ contract đã chốt trong `PRODUCT.md` và `docs/liver_mri_3d_classification_plan.md` §8.1–8.2.

**Cảnh báo cho tool sau:** Notebook chưa theo dõi `notebooks/notebookf104ced082.ipynb` là thay đổi ngoài phạm vi, đã được người dùng yêu cầu giữ nguyên; không stage, commit hay xoá nó.


## S-048 · 2026-07-27 21:51 · claude-code

**Mục tiêu phiên:** Chỉnh sửa bộ slide overview theo 5 yêu cầu người dùng, gộp slide 8+9, đánh số lại 12→11.

**Nhánh / commit:** `main` · `d101425` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — slide 2 dùng ảnh 8 thì (contact sheet tổng hợp) + đổi attribution; slide 7 viết lại 4 ô protocol cụ thể/đánh số 1–4; gộp slide 8 (Đóng góp) + 9 (Ứng dụng) thành một slide (giữ 4 đóng góp + 1 lane bác sĩ, bỏ lane Mentor/reviewer); slide 9 và 10 thay mockup HTML (`.app-mock`, `.output-prototype`) bằng ô placeholder `.img-slot` nét đứt chờ ảnh; slide 10 input đổi sang placeholder "mỗi .nii = nhiều lát cắt"; đánh số lại toàn bộ 12→11 slide (index/comment/aria); dọn CSS thừa.
- `slides/README.md` — sửa "13 bản khắc" và "RUO 13/13" → 11.
- `slides/assets/ATTRIBUTION.md` — cập nhật usage ảnh tổng hợp (giờ ở slide 2) + thêm 2 stub cho ảnh người dùng sẽ thêm sau.
- `WORKLOG.md` — ghi bàn giao phiên.

**Quyết định & lý do:**
- Ảnh UI output và ảnh input "nhiều lát cắt" **để trống bằng ô placeholder nét đứt** (đúng chuẩn "chưa có dữ liệu" của DESIGN) thay vì tự vẽ — người dùng chốt sẽ tự tạo ảnh rồi thêm sau. Đặt sẵn đường dẫn `assets/ui-output-screen.*` (dùng chung slide 9+10) và `assets/nii-volume-stack.*`, kèm comment swap để thay ảnh chỉ là một dòng. Phương án đã loại: tự vẽ SVG line-art (làm được, đúng thế giới bản khắc) — bị loại vì người dùng muốn tự tạo ảnh.
- Gộp 8+9 giữ đủ 4 đóng góp + 1 lane bác sĩ (người dùng chọn) — luận điểm hợp nhất "cách đo có trách nhiệm để làm người đọc thứ hai". Giữ footnote 3 (Duke) nên đánh số chú thích không đổi.

**Kết quả / số liệu:** Quality gate PASS (Impeccable detect slides/reports, split, patient-data đều pass). Kiểm tra tĩnh: 11 slide, 11 chỉ số `/ 11`, không còn `/ 12`; comment/aria đánh lại 1–11; không còn class mockup cũ (`app-mock`/`output-prototype`/`mock-*`/...); thẻ section/figure cân bằng.

**Dang dở:**
- [ ] Chờ người dùng cung cấp 2 ảnh (`ui-output-screen.*`, `nii-volume-stack.*`) để thay vào 3 ô `.img-slot` (slide 9 output, slide 10 input + output).
- [ ] Chưa mở trình duyệt kiểm tra hiển thị thực tế (mới chỉ static + Impeccable). Nên xem lại layout ô placeholder trên máy chiếu.

**Điểm vào phiên sau:** Khi có ảnh, thay `.img-slot` bằng `<img src="assets/...">` tại 3 điểm đã đánh dấu comment trong `slides/overview.html`; bổ sung nguồn/giấy phép trong `slides/assets/ATTRIBUTION.md`.

**Cảnh báo cho tool sau:** Notebook chưa theo dõi `notebooks/notebookf104ced082.ipynb` là thay đổi ngoài phạm vi, người dùng yêu cầu giữ nguyên; không stage, commit hay xoá nó.

## S-049 · 2026-07-27 22:37 · antigravity

**Mục tiêu phiên:** Tạo ảnh minh hoạ UI output bằng Banana (image generator) thay cho SVG theo lệnh người dùng, chèn ảnh vào slide 9, 10 và cập nhật attribution.

**Nhánh / commit:** `main` · *(commit đang chờ)*

**Đã đụng file:**
- `slides/assets/ui-output-screen.jpg` — mới, ảnh sinh bằng công cụ t-t-i (banana/generate_image).
- `slides/overview.html` — thay placeholder bằng figure img thẻ HTML trỏ tới ảnh JPG.
- `slides/assets/ATTRIBUTION.md` — điền nguồn ảnh JPG là do Antigravity tạo.
- `WORKLOG.md` — nhật ký phiên.

**Quyết định & lý do:**
- Người dùng yêu cầu sử dụng công cụ sinh ảnh bằng AI thay vì SVG line-art cho ảnh minh hoạ màn hình output.
- File ảnh được lưu thành `ui-output-screen.jpg` và thay thế vào các placeholder (img-slot) trên slide 9 và 10. Ô phụ ở slide 10 được gắn `style="object-fit:contain"`.
- Bỏ qua cảnh báo git dirty ban đầu theo chỉ định.

**Kết quả / số liệu:** Quality gate PASS.

**Dang dở:**
- [ ] Chưa xử lý ảnh `nii-volume-stack` cho ô placeholder còn lại.

**Điểm vào phiên sau:** Người dùng kiểm tra render thực tế của `slides/overview.html` và cung cấp/yêu cầu tạo ảnh `nii-volume-stack`.

**Cảnh báo cho tool sau:** Cảnh báo cũ: Notebook chưa theo dõi `notebooks/notebookf104ced082.ipynb` là thay đổi ngoài phạm vi, đã được người dùng yêu cầu giữ nguyên; không stage, commit hay xoá nó.

## S-050 · 2026-07-27 22:47 · claude-code

**Mục tiêu phiên:** Ghép ảnh UI output (do người dùng sinh bằng Antigravity) vào slide 9 + 10.

**Nhánh / commit:** `main` · `d101425` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — slide 9 và ô output slide 10: thay placeholder `.img-slot` bằng `<figure class="image-frame"><img src="assets/ui-output-screen.png" object-fit:contain ...></figure>`, thêm figcaption cảnh báo "số trong ảnh chỉ minh hoạ". Ô input slide 10 (nii-volume-stack) VẪN là placeholder chờ ảnh.
- `slides/assets/ATTRIBUTION.md` — đổi entry sang `.png`, thêm cảnh báo số giả + ghi chú file `.jpg` trùng.
- `slides/assets/ui-output-screen.png` + `.jpg` — người dùng thêm (ngoài phiên này).

**Quyết định & lý do:**
- Người dùng chọn **dùng tạm** ảnh dù đã được cảnh báo 2 lần, kèm yêu cầu "note hình minh hoạ". Đã ghép + thêm figcaption/chip nói rõ đây là minh hoạ bố cục. Phương án đã loại: sinh lại ảnh không số (A) / hybrid nền trống + nhãn HTML (B) — người dùng chọn C.
- Dùng `object-fit:contain` để không cắt mất dải DEFER và RUO trong ảnh.

**Kết quả / số liệu:** Quality gate PASS (Impeccable detect slides/reports). Kiểm tra tĩnh: 2 ref `ui-output-screen.png` (slide 9+10), 3 `figure.image-frame`, còn 1 `.img-slot` (input nii-stack chờ ảnh).

**Dang dở:**
- [ ] Ảnh `ui-output-screen.png` **chứa số phần trăm giả + chữ rác** — mới có figcaption che, chưa sạch. Nên thay bằng bản không số (prompt siết chặt đã đưa) hoặc bản hybrid.
- [ ] Ô input slide 10 vẫn chờ ảnh `nii-volume-stack.*`.
- [ ] File `ui-output-screen.jpg` trùng nội dung, có thể xoá.

**Điểm vào phiên sau:** Khi có bản ảnh UI không số → ghi đè `ui-output-screen.png`, bỏ figcaption cảnh báo. Khi có `nii-volume-stack.*` → thay `.img-slot` trong `.phase-sheet` (slide 10).

**Cảnh báo cho tool sau:** (1) Deck ĐANG hiển thị số giả trong ảnh output slide 9/10 — vi phạm mềm The Two-Number Rule, chỉ được che bằng figcaption; đây là bản tạm theo yêu cầu người dùng, không phải trạng thái chuẩn. (2) Notebook `notebooks/notebookf104ced082.ipynb` ngoài phạm vi, giữ nguyên, không stage/commit/xoá.

## S-051 · 2026-07-27 22:58 · claude-code

**Mục tiêu phiên:** Dùng ảnh 8 thì (contact sheet) làm ảnh input slide 10 thay cho placeholder.

**Nhánh / commit:** `main` · `d101425` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — slide 10 input: thay `.img-slot` placeholder bằng `<img src="assets/synthetic-mri-8phase-contact-sheet.png">` trong `.phase-sheet`, giữ nhãn 8 file + sửa figcaption cho khớp ảnh. Concept "mỗi file = nhiều lát cắt" vẫn ở ô glyph trái.
- `slides/assets/ATTRIBUTION.md` — contact sheet giờ "Dùng ở: Slide 2 và 10"; `nii-volume-stack.*` chuyển thành tuỳ chọn (không còn bắt buộc).

**Quyết định & lý do:** Người dùng chọn tái dùng ảnh 8 thì sẵn có làm input thay vì chờ ảnh stack riêng — nhanh, không cần asset mới.

**Kết quả / số liệu:** Quality gate PASS. Kiểm tra tĩnh: không còn `.img-slot` trong HTML (cả 3 ô ảnh đã đầy); 2 ref contact-sheet (slide 2 + 10).

**Dang dở:**
- [ ] (Đính chính S-050) Input slide 10 KHÔNG còn chờ `nii-volume-stack` — đã dùng contact sheet. Ảnh stack chỉ là cải tiến tuỳ chọn.
- [ ] Ảnh `ui-output-screen.png` vẫn còn số giả (bản tạm, có figcaption che) — nên thay bản không số về sau.
- [ ] `ui-output-screen.jpg` trùng, có thể xoá.

**Điểm vào phiên sau:** Chưa commit — nếu người dùng đồng ý, commit gộp toàn bộ thay đổi slide (S-048→S-051) trong một commit `feat(slides)`.

**Cảnh báo cho tool sau:** Deck vẫn hiển thị số giả trong ảnh output slide 9/10 (bản tạm theo yêu cầu người dùng). Notebook `notebooks/notebookf104ced082.ipynb` giữ nguyên, không stage/commit/xoá.

## S-052 · 2026-07-27 23:20 · claude-code

**Mục tiêu phiên:** Thêm 1 slide metric về macro-F1, minh hoạ bằng chính 7 lớp của LLD-MMRI.

**Nhánh / commit:** `main` · `d101425` → *(commit đang chờ)*

**Đã động file:**
- `slides/overview.html` — chèn slide 5 mới "Macro-F1" (sau Dataset, thuộc section SOTA): strip 7 lớp (HCC/ICC/di căn = ác, đánh dấu ô đặc; nang/u máu/FNH/áp-xe = lành, ô rỗng — hình dạng + nhãn chữ, không dựa màu), công thức macro-F1, và tương phản macro vs micro. Thêm CSS `.class-strip/.class-cell/.formula`. Đánh số lại toàn deck 11→12 (denominator global + first-number/comment/aria slide 5–11 → 6–12).
- `slides/README.md` — 11→12 bản khắc.

**Quyết định & lý do:**
- **Không bịa điểm F1 từng lớp** — DESIGN The Two-Number Rule cấm vẽ số kết quả dự án. Minh hoạ macro-F1 bằng cấu trúc lớp thật + trực giác "lớp hiếm bị bỏ sót kéo điểm xuống", kèm chip "Minh hoạ công thức, chưa có kết quả dự án". Phương án đã loại: worked example có số giả định (rủi ro reviewer tưởng là kết quả).
- Đặt slide ngay sau Dataset (đã giới thiệu 7 lớp 3 ác 4 lành) và trước SOTA leaderboard — "định nghĩa thước đo → xem bảng xếp hạng theo thước đo đó".
- Ác/lành phân biệt bằng ô đặc/rỗng + chữ (a11y), không dùng màu.

**Kết quả / số liệu:** Quality gate PASS. Kiểm tra tĩnh: 12 section, index 01–12/12 đúng thứ tự, comment/aria 1–12, 7 ô lớp.

**Dang dở:**
- [ ] Chưa mở trình duyệt kiểm tra layout strip 7 lớp (mới static + Impeccable). Xem lại trên máy chiếu, đặc biệt tên lớp có dấu cách ("di căn", "áp-xe") có thể wrap.
- [ ] Ảnh `ui-output-screen.png` vẫn còn số giả (bản tạm, figcaption che); `.jpg` trùng có thể xoá.

**Điểm vào phiên sau:** Nếu người dùng muốn số ví dụ cụ thể trên slide macro-F1 → phải là số công bố (Loại A, có nguồn) hoặc worked example dán nhãn giả định rõ ràng; không dùng số dự án.

**Cảnh báo cho tool sau:** Deck vẫn hiển thị số giả trong ảnh output slide 10/11 (bản tạm theo yêu cầu người dùng). Notebook `notebooks/notebookf104ced082.ipynb` giữ nguyên, không stage/commit/xoá.

## S-053 · 2026-07-27 23:45 · claude-code

**Mục tiêu phiên:** Tạo tài liệu khảo sát thị trường AI gan (industry landscape) theo yêu cầu người dùng.

**Nhánh / commit:** `main` · `d101425` → *(commit đang chờ)*

**Đã động file:**
- `docs/industry_landscape.md` — tạo mới. 9 mục: phạm vi + caveat mốc thời gian · tóm tắt điều hành · bản đồ thị trường theo tác vụ · bảng sản phẩm/công trình (input→output) · mảng trustworthiness · rào cản chưa thương mại hoá · input/output thực tế · hàm ý dự án · 19 nguồn có link.
- `WORKLOG.md` — ghi bàn giao.

**Quyết định & lý do:**
- Phạm vi "AI gan rộng (detection→classification, MRI+CT) + trustworthiness", đặt ở `docs/` — người dùng chốt qua hỏi đáp.
- Mọi nhận định/số kèm nguồn (kỷ luật trích dẫn), đánh dấu rõ là khảo sát ngoài + mốc 7/2026, KHÔNG trộn với số dự án. Nghiên cứu web read-only trong plan mode (WebSearch), tái dùng khi execute.
- Kết luận nền: thị trường giỏi detection/định lượng (Perspectum LiverMultiScan, Nanox HealthFLD, Median iBiopsy, Aidoc, EDDA IQQA-Liver); phân loại đa lớp trên MRI đa pha + calibration/`defer` gần như chỉ ở nghiên cứu → đúng khoảng trống dự án.

**Kết quả / số liệu:** Quality gate PASS. File 130 dòng, 19 nguồn/link. Không đụng slides/webapp/code.

**Dang dở:**
- [ ] Tuỳ chọn: thêm 1 dòng trỏ `docs/industry_landscape.md` vào bảng bản đồ tài liệu `AGENTS.md` §2 — CHƯA làm (sửa AGENTS.md cần cân nhắc + ghi WORKLOG). Hỏi người dùng nếu muốn.
- [ ] Ảnh `ui-output-screen.png` (slide 10/11) vẫn còn số giả (bản tạm); `.jpg` trùng có thể xoá.

**Điểm vào phiên sau:** Nếu đưa nội dung này vào report → dùng làm mục related-work/market; verify lại trạng thái FDA/CE của từng sản phẩm (thay đổi theo thời gian) trước khi trích.

**Cảnh báo cho tool sau:** Số trong `docs/industry_landscape.md` là của bên thứ ba (Loại A, có nguồn), KHÔNG phải kết quả dự án — đừng nhầm. Notebook `notebooks/notebookf104ced082.ipynb` giữ nguyên, không stage/commit/xoá.

## S-054 · 2026-07-28 · claude-code

**Mục tiêu phiên:** Soạn prompt để một phiên sau nghiên cứu web + dựng deck 7 slide mới `slides/overview_v2.html`.

**Nhánh / commit:** `main` · `d101425` → *(commit đang chờ)*

**Đã đụng file:**
- `prompt/slides_overview_v2.md` — tạo mới. Prompt 5 phần: (0) danh sách đọc bắt buộc, (1) luật số liệu, (2) chỉ dẫn nghiên cứu web + thứ tự ưu tiên nguồn, (3) nội dung 7 slide, (4) ràng buộc kỹ thuật file, (5) quy trình + checklist nghiệm thu.
- `WORKLOG.md` — entry này.

**Quyết định & lý do:**
- **Đặt ra "Loại C — số mục tiêu/kỳ vọng"** bổ sung cho The Two-Number Rule của `DESIGN.md`. Slide 6 người dùng yêu cầu có "kỳ vọng đạt bao nhiêu", mà hệ thống hiện chỉ có Loại A (số công bố của người khác) và Loại B (số dự án — cấm vẽ). Loại C bị siết bằng ba điều kiện đồng thời: viền nét đứt + chip "Mục tiêu, chưa có kết quả" + **neo vào một số Loại A có nguồn**. Không neo được thì phát biểu định tính. Phương án đã loại: cấm hẳn số mục tiêu (không đáp ứng yêu cầu) và cho tự do ghi mục tiêu (rủi ro reviewer đọc nhầm thành kết quả).
- **v2 là file thứ hai, không sửa `overview.html`.** Hai deck phục vụ hai buổi khác nhau; deck 12 bản khắc vẫn là bản chính thức.
- **Slide 3 dùng lại `docs/industry_landscape.md`** thay vì khảo sát lại — tài liệu đã có 19 nguồn, chỉ yêu cầu verify lại trạng thái FDA/CE.
- **Chèn guard về Vinmec**: cấm logo, cấm mọi câu ngụ ý đã phê duyệt/đã cấp dữ liệu; giai đoạn sau 6 tuần trình bày như đề xuất có điều kiện kèm IRB / data-sharing / de-identification.
- Ước tính hạ tầng GPU phải kèm giả định hiển thị và nằm trong khối nét đứt — là ước tính, không phải số đo.

**Kết quả / số liệu:** Không có. Phiên này chỉ sinh tài liệu prompt, không đụng `slides/`, `src/`, `webapp/`.

**Dang dở:**
- [ ] Deck `slides/overview_v2.html` **chưa được dựng** — prompt mới chỉ là đầu vào.
- [ ] Các mục tồn từ S-050→S-053 vẫn chưa commit (deck v1 + `docs/industry_landscape.md`).

**Điểm vào phiên sau:** Chạy `prompt/slides_overview_v2.md` (dán khối ```text vào tool). Bước 3 của prompt yêu cầu **báo cáo danh sách nguồn trước khi dựng HTML** — đừng bỏ bước đó.

**Cảnh báo cho tool sau:** (1) Slide 6 của deck v2 là chỗ dễ vi phạm The Two-Number Rule nhất — mọi con số kỳ vọng phải neo vào nguồn công bố, không được rơi từ trên trời. (2) Không dùng `ui-output-screen.png` trong v2 (ảnh chứa số phần trăm giả). (3) Notebook `notebooks/notebookf104ced082.ipynb` giữ nguyên, không stage/commit/xoá.

## S-055 · 2026-07-28 12:30 · claude-code

**Mục tiêu phiên:** Chạy prompt `prompt/slides_overview_v2.md` — nghiên cứu web rồi dựng deck 7 slide `slides/overview_v2.html`.

**Nhánh / commit:** `main` · `d101425` → *(commit đang chờ)*

**Đã đụng file:**
- `slides/overview_v2.html` — tạo mới. 7 slide + 1 slide phụ lục nguồn (không đánh số vào 7). Tự chứa, CSS/JS inline, tái dùng hệ thị giác của v1 nhưng viết lại CSS gọn cho bộ component mới (`.dash-list`, `.scope`, `figure.chart`, `.claim`, `.flow-v`, `.quad`, `.trio`, `.target`).
- `slides/README.md` — bảng 2 deck song song + giải thích khác nhau; bảng chú số riêng cho v2 (10 mục); mục "Đã loại có chủ ý".
- `slides/assets/ATTRIBUTION.md` — contact sheet giờ dùng thêm ở `overview_v2.html` slide 1.
- `WORKLOG.md` — entry này.

**Quyết định & lý do:**
- **Chú số Hoàng Thổ được sửa đúng DESIGN.** v1 để `.refs b` và gạch chân link màu Lam Ngọc; v2 chuyển chú số + số chú giải sang Hoàng Thổ, đúng The Plate Key Rule. Kiểm lại: amber chỉ xuất hiện ở 4 chỗ hợp lệ (chú số `sup.ref`, số chú giải `.refs b`, mốc phần active, đường nhấn dưới `h2`) cộng hover/focus của link theo đúng mục Link của DESIGN.
- **Không dùng `.compare-item.warn` kiểu v1.** Ở v1 nó tô amber trong vùng nội dung; v2 tránh hẳn để không làm loãng nghĩa chú số.
- **`<code>` phải được style.** Mặc định trình duyệt là monospace = font thứ ba, vi phạm "Don't thêm font thứ ba". Đã ép về stack sans kèm nền Nền Bản.
- **Nét đứt chỉ còn 2 chỗ:** chip `.concept` và khối `.target`. Ô chú giải ác/lành ở slide 5 ban đầu dùng nét đứt cho đẹp — đã sửa thành viền Kẻ Đậm, vì nét đứt là tín hiệu dành riêng cho "chưa có dữ liệu".
- **Loại C (số mục tiêu) triển khai đúng ba điều kiện** đã đặt ra ở S-054: khối `.target` viền nét đứt + chip "Mục tiêu, chưa có kết quả" + mỗi mục tiêu neo vào số có nguồn (0,6083 baseline; vùng 0,2562–0,8322 của 24 mục leaderboard). Ba mục tiêu còn lại (calibration, selective, an toàn lâm sàng) cố ý phát biểu **định tính**, không gán ngưỡng, vì không neo được vào nguồn nào.
- **Bốn số đã tìm được nhưng bị loại** — lý do ghi trong `slides/README.md`: biểu đồ thời gian chẩn đoán (không có nguồn đo thật), 30,8% báo cáo calibration (MDPI 403, không verify được bản gốc), Hu et al. F1 0,84 (Springer paywall), Median sensitivity 92% (chỉ có thông cáo báo chí — nguồn loại này chỉ dùng cho trạng thái sản phẩm, không dùng cho số hiệu năng).
- **Đếm thiết bị FDA lấy từ JAMA Netw Open thay vì trade press.** Cùng tỷ lệ 76% radiology nhưng là nguồn peer-reviewed, và kèm sẵn bộ số về chất lượng kiểm định (97% qua 510(k), 5% prospective, 29% clinical) — chính là bằng chứng cho rào cản ở slide 3, mạnh hơn một con số đếm đơn thuần.
- **Bối cảnh Việt Nam thay vì chỉ số quốc tế.** Tìm được Vu et al. KJR 2023 nói thẳng về thiếu hụt bác sĩ CĐHA ở Việt Nam → slide 2 mở bằng số trong nước rồi mới dẫn số Hoa Kỳ, thay vì ngoại suy.

**Kết quả / số liệu:** Quality gate PASS (Impeccable detect slides + reports OK). Kiểm tra tĩnh: 8 `<section class="slide">`, 8 dải RUO, chỉ số `01/07`–`07/07` + `Phụ lục`, 0 `text-transform`, 0 `box-shadow`, 0 asset ngoài (không CDN/webfont), 7 `<code>` đã có style. `slides/overview.html` **không bị sửa** (mtime 2026-07-27 23:10, trước phiên này).

**Dang dở:**
- [ ] **Chưa mở trình duyệt kiểm layout.** Mới static + Impeccable. Slide 2 là slide dày nhất (3 số + biểu đồ SVG + khối scope trong một cột) — khả năng tràn dọc cao nhất ở đó. Slide 7 ba cột cũng cần soát.
- [ ] Chưa in thử PDF (kỳ vọng 8 trang ngang).
- [ ] Các mục tồn từ S-050→S-053 vẫn chưa commit.

**Điểm vào phiên sau:** Mở `slides/overview_v2.html` bằng trình duyệt ở đúng 16:9, soát tràn dọc slide 2 và 7 trước. Nếu tràn: cắt bớt chữ trong `span` của `.dash-list`, không giảm cỡ chữ (deck phải đọc được từ cuối phòng họp).

**Cảnh báo cho tool sau:** (1) v2 có **bộ chú số riêng 1–10**, không dùng chung đánh số với v1 — đừng trộn hai bảng. (2) Khối `.target` ở slide 6 và slide 7 là **số mục tiêu**, không phải kết quả; nếu sửa, phải giữ nguyên cả ba tín hiệu (nét đứt + chip + neo nguồn). (3) v2 cố tình **không dùng** `ui-output-screen.png` vì ảnh đó chứa số phần trăm giả. (4) Notebook `notebooks/notebookf104ced082.ipynb` giữ nguyên, không stage/commit/xoá.

**Phụ chú S-055 (sau khi hook Impeccable chạy):** hook `impeccable@1` báo `flat-type-hierarchy` ở L99. **Phân loại: false positive, KHÔNG suppress.** Lý do: L99 là `font-size: var(--small)` trong `.foot`; hook không giải được token dạng `max(<rem>, calc(<n> * var(--u)))` nên thấy nhiều rule cùng đọc một chuỗi và kết luận là phẳng. Đã kiểm bằng số — mọi bậc kề nhau đều ≥1,25 ở cả hai đầu clamp: rem 1,656 / 1,280 / 1,250 / 1,333; fluid 1,800 / 1,308 / 1,303 / 1,451. Thu hẹp bất kỳ bậc nào sẽ vi phạm The Data-Outranks-Prose Rule. Hai detector khác không báo gì: `npx impeccable detect --json` (v3.4.0) trả `[]`, quality gate PASS. **Chưa ghi ignore vào config** — cần người dùng xác nhận trước.

Nhân lúc soát thì tìm ra một chỗ phẳng **thật** mà hook không chỉ tới: chữ trong SVG slide 2 có hai cỡ 11px và 10px (tỉ lệ 1,1), và dòng 10px lặp lại đúng nội dung của figcaption. Đã xoá dòng 10px trong SVG, chuyển nội dung vào figcaption. SVG giờ chỉ còn một cỡ chữ 11px. Quality gate chạy lại: PASS.

## S-056 · 2026-07-28 13:05 · claude-code

**Mục tiêu phiên:** Năm sửa đổi trên `slides/overview_v2.html` theo yêu cầu người dùng.

**Nhánh / commit:** `main` · `d101425` → *(commit đang chờ)*

**Đã đụng file:**
- `slides/overview_v2.html` — (1) xoá hẳn nút điều hướng Trước/Sau: bỏ `<nav class="nav">`, toàn bộ CSS `.nav*`, hai rule `.nav{display:none}` trong media query, và phần `prev/next/wake/timer` trong JS. Điều hướng bàn phím giữ nguyên. (2) Phụ lục và slide không còn trỏ vào file `.md` nào trong repo: chú số 9 giờ liệt kê 6 link ngoài trực tiếp, chú số 10 bỏ trỏ `ATTRIBUTION.md`, link leaderboard đổi chữ hiển thị từ `test_leaderboard.md` sang "Bảng xếp hạng tập test". (3) Slide phụ lục bỏ dải mốc phần, thêm class `.no-nav` để lưới còn 3 hàng. (4) Slide 7 bỏ cột "Hạ tầng huấn luyện" (gồm cả khối ước tính VRAM), `.trio` → `.trio.duo` 2 cột. (5) Mục tiêu macro-F1 đổi sang 0,85–0,90.
- `slides/README.md` — ghi khác biệt điều hướng v1/v2; ghi phụ lục v2 chỉ dẫn link ngoài; thêm cảnh báo về mục tiêu macro-F1.
- `WORKLOG.md` — entry này.

**Quyết định & lý do:**
- **Mục tiêu macro-F1 0,85–0,90 là quyết định của người dùng, không phải đề xuất của agent.** Tôi đã nêu trước khi làm rằng mức này nằm **trên đội nhất** của LLD-MMRI Challenge 2023 (0,8322 / test-104, 24 mục) và **mâu thuẫn với `AGENTS.md` §5 + `PRODUCT.md`** ("không đua accuracy leaderboard"). Người dùng vẫn chốt. Đã làm đúng yêu cầu, và giữ kỷ luật Loại C: con số nằm trong khối nét đứt, có chip "Mục tiêu, chưa có kết quả", neo vào cả 0,6083 lẫn 0,8322, kèm một câu nói thẳng "mức nhắm tới nằm trên đội cao nhất, nên đây là mục tiêu tham vọng chứ không phải mức an toàn". **`AGENTS.md` và `PRODUCT.md` CHƯA được sửa** — sửa file ngữ cảnh cần người dùng duyệt riêng (AGENTS.md §10).
- **Link `test_leaderboard.md` được giữ, chỉ đổi chữ hiển thị.** Đây là nguồn công bố bên ngoài trên GitHub, trùng đuôi `.md` chứ không phải tài liệu nội bộ; yêu cầu của người dùng nhắm vào tài liệu trong repo. Đổi chữ để không ai nhìn nhầm thành file local.
- **Bỏ nút Trước/Sau kéo theo một lỗi gate.** Khối `.nav button` là chỗ **duy nhất** còn lại khai báo stack sans mà parser đọc được; `body` lúc đó dùng shorthand `font: 400 var(--body)/1.5 var(--sans)` và Impeccable không phân giải shorthand. Xoá `.nav` xong detector báo `single-font` ("only font used is cambria"), exit 2, gate FAIL. Sửa bằng cách tách shorthand ở `body` thành `font-family` / `font-size` / `font-weight` / `line-height` rời. Đây là CSS đúng hơn, không phải mẹo qua mặt detector.

**Kết quả / số liệu:** Quality gate PASS. Kiểm tra tĩnh: 8 section, 8 dải RUO, 7 dải mốc phần (phụ lục không có), 0 nút prev/next, 0 tham chiếu file `.md` nội bộ, 0 dấu vết cột hạ tầng.

**Dang dở:**
- [ ] **Vẫn chưa mở trình duyệt kiểm layout** (từ S-055). Slide 7 giờ 2 cột thay vì 3 nên rộng rãi hơn; slide 2 vẫn là chỗ dày nhất.
- [ ] `AGENTS.md` §5 và `PRODUCT.md` đang lệch với mục tiêu 0,85–0,90 ghi trên slide. Cần hỏi người dùng có muốn sửa hai file ngữ cảnh cho khớp không.
- [ ] Hook `flat-type-hierarchy` (S-055) vẫn chưa ghi ignore — chờ người dùng xác nhận.
- [ ] Các mục tồn từ S-050→S-053 vẫn chưa commit.

**Điểm vào phiên sau:** Mở `slides/overview_v2.html` ở 16:9 soát tràn dọc slide 2. Sau đó hỏi người dùng về việc đồng bộ `AGENTS.md` §5 / `PRODUCT.md` với mục tiêu accuracy mới.

**Cảnh báo cho tool sau:** (1) **Deck v2 và AGENTS.md/PRODUCT.md đang mâu thuẫn nhau về định vị accuracy.** Deck nói nhắm 0,85–0,90; hai file ngữ cảnh nói không đua accuracy. Đây là chủ ý của người dùng, không phải drift — đừng "sửa" deck về lại. (2) Đừng khai báo font bằng shorthand `font:` trong deck này, detector không đọc được và sẽ báo `single-font`. (3) Notebook `notebooks/notebookf104ced082.ipynb` giữ nguyên, không stage/commit/xoá.

**Phụ chú S-056:** hook `impeccable@1` lại báo `flat-type-hierarchy`, lần này ở **L50** thay vì L99. Không phải finding mới — cùng một false positive đã phân tích ở phụ chú S-055. Số dòng dịch vì việc tách shorthand `font:` ở `body` thành bốn khai báo rời đã chèn thêm dòng; điểm hook bắt chuyển từ `font-size: var(--small)` trong `.foot` sang `font-size: var(--body)` trong `body`. Thang chữ không đổi (1,656 / 1,280 / 1,250 / 1,333 ở đầu rem). `npx impeccable detect --json slides/overview_v2.html` trả `[]` exit 0; gate PASS. Vẫn **chưa ghi ignore**, vẫn chờ người dùng xác nhận.

## S-057 · 2026-07-28 · claude-code

**Mục tiêu phiên:** Khảo sát data đã xử lý trên Kaggle, tính bề rộng CI ở n=104, và viết code cache bám sát tổn thương.

**Nhánh / commit:** `main` · `0f1dcdf` → *(commit đang chờ)*

**Đã đụng file:**
- `src/preprocess/crop.py` — MỚI. `bbox_extent_voxel`, `mask_center_extent_voxel`, `adaptive_spacing`. Docstring ghi rõ đánh đổi mất kích thước tuyệt đối và hai biện pháp giảm thiểu.
- `src/preprocess/build_cache.py` — thêm `process_patient_with_meta` (trả kèm hình học cửa sổ cắt); `process_patient` giữ nguyên chữ ký cũ làm wrapper nên notebook và test cũ không hỏng. `build_cache` quét thư mục mask khi cần, ghi `lesion_extent_mm`/`fov_mm`/`spacing`/`crop_source` vào từng `.npz`, thêm 2 cột vào `build_log.csv`, đếm và cảnh báo số ca phải rơi về bbox.
- `configs/preprocess.yaml` — thêm `crop_mode` + khối `lesion_tight`; đổi `cache_dir` sang `artifacts/cache_lesion_tight`.
- `configs/data.yaml` — thêm `labels_rel: lld/labels` kèm cảnh báo mask là do MedSAM2 sinh.
- `tests/test_preprocess_pipeline.py` — +11 test.
- `AGENTS.md` §6 — cập nhật dòng lệnh tiền xử lý.

**Quyết định & lý do:**
- **Khảo sát Kaggle (qua API, chỉ liệt kê không tải):** `marcohoang/lld-mmri-3d` = 610 file / 2,52 GiB, trong đó `cache/` có **đủ 498 `.npz`** (cache v0) + `repo/` 109 file. `marcohoang/lldmmridataset` = 15.945 file / 78,24 GiB: `lld/images` 3.984 `.nii`, **`lld/labels` 3.984 `.nii`**, `LLD_MMRI_Annotation.json`, còn lại là rác `.cache` của HuggingFace. ⇒ **mask có đủ 498 ca và có riêng cho từng thì.**
- **Đính chính S-056:** tôi từng gọi mask là "lợi thế mà cả bảng xếp hạng không có". Nói vậy là quá lời. Đây là mask **MedSAM2 sinh tự động**, không phải bác sĩ vẽ. Dùng để **định vị và đo kích thước** thì tốt; dùng làm **nhãn giám sát segmentation** thì đang chưng cất lỗi của MedSAM2. Đã ghi cảnh báo vào `configs/data.yaml`.
- **Giữ `fixed_mm` làm mặc định của code, chỉ đổi mặc định trong config.** Hai chế độ cùng tồn tại để so sánh có kiểm soát; cache mới ghi sang thư mục khác, không đè cache v0.
- **Ghi `lesion_extent_mm` vào cache.** Chế độ lesion_tight làm mất kích thước tuyệt đối của tổn thương — thứ có ý nghĩa chẩn đoán (nang 5mm khác HCC 50mm). Lưu ở cạnh thì model sau dùng lại được làm đặc trưng phụ, chi phí bằng 0.
- **Mask thiếu/rỗng thì rơi về bbox và ghi lại**, không im lặng. Mask rỗng ở `mask_center_extent_voxel` thì raise, vì rơi về tâm ảnh sẽ tạo dữ liệu sai mà không ai biết.

**Kết quả / số liệu:**

Bề rộng CI 95% bootstrap của macro-F1 ở **n=104** (phân bố lớp thật `[16,12,12,11,11,10,32]`, 2000 lần lấy mẫu lại mức bệnh nhân):

| macro-F1 | CI 95% | ± nửa |
|---|---|---|
| 0,60 | [0,498 – 0,694] | ±0,098 |
| 0,70 | [0,615 – 0,784] | ±0,085 |
| 0,80 | [0,713 – 0,881] | ±0,084 |
| 0,8322 | [0,749 – 0,903] | ±0,077 |
| 0,85 | [0,781 – 0,919] | ±0,069 |
| 0,90 | [0,834 – 0,955] | ±0,061 |

⇒ **Không thể chứng minh vượt 0,8322 trên test-104.** CI của 0,8322 kéo tới 0,903, chồng lên cả CI của 0,90. Lưu ý: so hai CI biên là phép **bảo thủ**; kiểm định ghép cặp (McNemar, bootstrap ghép cặp) mạnh hơn vì triệt tiêu độ khó riêng từng ca — CI chồng nhau không đồng nghĩa chắc chắn không khác biệt.

`pytest` **196 passed, 7 skipped**. ruff sạch.

**Dang dở:**
- [ ] **Chưa build cache mới** — cần chạy trên Kaggle, dữ liệu thô 78 GiB không ở máy local.
- [ ] Script tính CI đang ở scratchpad, chưa chuyển thành `scripts/`. Người dùng chọn phương án (a) nên tôi chưa làm.
- [ ] `notebooks/02_build_cache.ipynb` vẫn gọi `process_patient` chữ ký cũ — vẫn chạy được (fixed_mm), nhưng muốn dùng mask thì phải qua CLI hoặc truyền thêm `mask_index`.

**Điểm vào phiên sau:** Chạy trên Kaggle: `LLDMMRI_CACHE_DIR=/kaggle/working/cache python -m src.preprocess.build_cache --config configs/preprocess.yaml --limit 20` để thử 20 ca trước, kiểm cột `crop_source` và `fov_mm` trong `build_log.csv`, rồi mới chạy cả mẻ.

**Cảnh báo cho tool sau:** (1) **Đổi `crop_mode` là đổi dữ liệu, không phải đổi tham số** — mọi so sánh với run cũ chỉ hợp lệ khi cùng crop_mode. (2) Mask LLD-MMRI là MedSAM2 sinh, không phải chuẩn vàng. (3) Notebook `notebooks/notebookf104ced082.ipynb` giữ nguyên, không stage/commit/xoá.

## S-058 · 2026-07-28 · claude-code

**Mục tiêu phiên:** Commit S-057, đánh giá xem có phải xử lý lại dataset từ đầu cho hướng mới, rồi viết `calibration.py` + `selective.py`.

**Nhánh / commit:** `main` · `0f1dcdf` → `df7a858` → *(commit đang chờ)*

**Đã đụng file:**
- `src/eval/calibration.py` — MỚI. ECE · adaptive-ECE · MCE · Brier · NLL · `reliability_curve` · `apply_temperature` · `fit_temperature` · `per_class_calibration_error`.
- `src/eval/selective.py` — MỚI. `predictive_entropy` · `uncertainty_decomposition` (total/aleatoric/epistemic) · `risk_coverage_curve` · `aurc` · `selective_accuracy` · `coverage_at_risk` · `metric_at_coverage`.
- `tests/test_calibration.py` (21 test) · `tests/test_selective.py` (18 test) — MỚI.

**Quyết định & lý do:**
- **Không cần xử lý lại dataset từ đầu.** Split official, phán quyết `axis_order`, và cách resample 8 thì lên một lưới mm chung đều đứng vững — Siamese, phase attention, pretrained backbone không đụng tới chúng. Hướng mới cần đúng **một lần build lại** (lesion-tight), code đã xong ở S-057.
- **Phát hiện một điểm thiết kế:** chuẩn hoá đang bị nướng vào cache (`clip_and_zscore` chạy lúc build, `src/data/` không chuẩn hoá lúc load). Hệ quả: mỗi ablation chuẩn hoá tốn một lần build cả mẻ. Đây là confound thật với baseline official (họ min-max `[0,1]`, ta percentile-clip + z-score). Đề xuất: lần build lesion-tight lưu luôn patch thô, chuẩn hoá lúc load. **Chưa làm** — không được để nó hoãn E0/E1.
- **`apply_temperature` nhận xác suất chứ không phải logit**, vì pipeline chỉ lưu `val_probs_*.npz`. Hợp lệ toán học: `softmax(log(p)/T)` cho đúng kết quả như chia logit gốc, do softmax bất biến với việc cộng hằng số vào logit. Có test khẳng định thứ hạng lớp không đổi ⇒ macro-F1/accuracy/AUROC giữ nguyên.
- **`fit_temperature` dùng tìm kiếm mặt cắt vàng tự cài** thay vì scipy: NLL theo T là hàm một biến trơn, lồi một cực tiểu trên khoảng này. Có test kiểm T tìm được thật sự tối thiểu hoá NLL so với các T khác.
- **`uncertainty_decomposition` raise khi chỉ có 1 thành viên**, không trả 0. Một model đơn lẻ không có epistemic uncertainty theo định nghĩa; trả 0 sẽ bị đọc nhầm thành "model rất chắc chắn".
- **`per_class_calibration_error` bỏ hẳn lớp vắng mặt**, không trả 0 — 0 sẽ bị đọc nhầm là hiệu chỉnh hoàn hảo. Có test riêng cho việc một lớp hỏng nặng mà ECE tổng vẫn đẹp.
- **`metric_at_coverage` là hàm tổng quát**, không phải `accuracy_at_coverage` cố định — con số trung tâm của dự án là **macro-F1 ở coverage 80%**, và hàm này ghép thẳng được với `bootstrap_metric` để ra CI. Docstring cảnh báo: ở coverage thấp một lớp hiếm có thể biến mất khỏi tập giữ lại, khi đó macro-F1 tính trên ít lớp hơn và không so trực tiếp được với coverage 100%.

**Kết quả / số liệu:** `pytest` **227 passed, 9 skipped** (196 → 227). ruff sạch. Quality gate PASS. Chưa có số thật nào — hai module test bằng dữ liệu tổng hợp có tính chất calibration/xếp hạng đã biết trước.

**Dang dở:**
- [ ] **Hai module chưa được gọi ở đâu cả.** `src/eval/run.py` vẫn chỉ in bảng metric cũ. Cần nối vào để calibration + selective tự xuất hiện khi một run kết thúc — nhưng phải cẩn thận: `fit_temperature` chỉ được chạy trên validation, áp mù sang test.
- [ ] Cache lesion-tight vẫn chưa build (cần Kaggle).
- [ ] E0/E1 vẫn chưa chạy — vẫn chưa có kết quả hợp lệ nào của dự án.

**Điểm vào phiên sau:** Nối `calibration` + `selective` vào `src/eval/run.py`, hoặc chạy E0+E1 trên Kaggle trước (ưu tiên cao hơn, vì hai module trên không cần model để test nhưng cần model để có số).

**Cảnh báo cho tool sau:** (1) **`fit_temperature` chỉ gọi trên validation.** Fit trên test là leakage và làm hỏng toàn bộ đánh giá. (2) Brier ở đây dùng dạng tổng bình phương (khoảng `[0,2]`), có tài liệu chia thêm cho K — đừng so nhầm với số của họ. (3) Notebook `notebooks/notebookf104ced082.ipynb` giữ nguyên.

## S-059 · 2026-07-28 · claude-code

**Mục tiêu phiên:** Sửa lỗi quét mask phát hiện khi người dùng chạy thử build cache lesion-tight trên Kaggle.

**Nhánh / commit:** `main` · `b7fd34c` → *(commit đang chờ)*

### Lỗi

Log Kaggle: `Đã quét 0 file mask ở .../lld/labels`, rồi **20/20 ca lặng lẽ rơi về bbox** và build báo "HOÀN TẤT".

Nguyên nhân: bộ dữ liệu theo quy ước nnU-Net, **hai thư mục đặt tên khác nhau**:

```
lld/images/MR-391135_1_C+V_0000.nii    ảnh   — có hậu tố kênh _0000
lld/labels/MR-391135_1_C+V.nii         mask  — KHÔNG có _0000
```

`build_cache` quét mask bằng `image_suffixes` (`_0000.nii*`) nên khớp 0 file. Xác nhận từ danh sách file thật đã tải qua Kaggle API: 3.984 mask, 100% đuôi `.nii` không có `_0000`.

**Lỗi thứ hai, nghiêm trọng hơn:** index rỗng mà build vẫn chạy tiếp. Đường lui về bbox — vốn để chịu vài ca thiếu mask — đã che mất một lỗi cấu hình toàn cục. Cả mẻ 498 ca sẽ build xong trông như thành công trong khi mask chưa từng được dùng, và không có gì trong log tổng kết nói ra điều đó.

**Đã đụng file:**
- `src/data/images.py` — thêm `DEFAULT_LABEL_SUFFIXES = (".nii.gz", ".nii")`; docstring ghi rõ hai quy ước tên.
- `src/preprocess/build_cache.py` — dùng `label_suffixes` khi quét mask; **raise `SystemExit` nếu quét ra 0 mask**, kèm in tên file thật trong thư mục để chẩn đoán ngay từ log.
- `configs/data.yaml` — thêm `label_suffixes: [".nii.gz", ".nii"]`.
- `tests/test_images.py` +2 test · `tests/test_preprocess_pipeline.py` +2 test.

**Quyết định & lý do:**
- **Đường lui phải có giới hạn.** Rơi về bbox cho *một vài ca* thiếu mask là đúng; rơi về bbox cho *tất cả* là dấu hiệu cấu hình sai, phải dừng. Ranh giới đặt ở "index rỗng".
- **Thông báo lỗi in tên file thật.** Lỗi này chẩn đoán được trong 1 giây nếu log nói "đuôi đã thử X, file thật trông như Y" — thay vì phải tải danh sách file về đối chiếu như tôi vừa làm.
- **Tôi viết sai assertion trong test lần đầu**: dùng khoá `"MR391135"` trong khi `normalize_pid` trả về **chỉ phần chữ số** `"391135"`. Test bắt được, đã sửa.

**Kết quả / số liệu:** `pytest` **231 passed, 9 skipped** (227 → 231). ruff sạch.

**Dang dở:**
- [ ] Người dùng cần **`git pull` trên Kaggle** rồi chạy lại `--limit 20`. Cache 20 ca cũ ở `/kaggle/working/cache_lesion_tight` **phải xoá** — chúng build bằng bbox, và `build_cache` có resume nên sẽ bỏ qua chứ không ghi đè.
- [ ] E0/E1 vẫn chưa chạy.

**Điểm vào phiên sau:** Sau khi xoá cache cũ và chạy lại 20 ca, cột `crop_source` phải là `mask` gần hết. Nếu vẫn `bbox` thì lần này build sẽ dừng hẳn với thông báo có tên file — gửi nguyên đoạn đó.

**Cảnh báo cho tool sau:** `build_cache` **có resume** (bỏ qua ca đã có `.npz`). Đổi tham số crop mà không xoá thư mục cache cũ thì mẻ mới sẽ trộn hai loại dữ liệu — không có gì trong file cảnh báo điều đó. Luôn build sang thư mục mới hoặc xoá sạch trước.

## S-060 · 2026-07-29 · claude-code

**Mục tiêu phiên:** Chạy E0/E1, đọc kết quả theo luật đã chốt trước, phân tích calibration + selective.

**Nhánh / commit:** `main` · `e815299` → *(commit đang chờ)*

### Kết quả E0 và E1

Cùng config (đã diff `config_used.json`: **không khác một khoá nào**), cùng seed 1337, cùng fold 1, cùng 82 bệnh nhân val. Chỉ khác cache.

| | E0 `fixed_mm` | E1 `lesion_tight` |
|---|---|---|
| macro-F1 | 0,4244 [0,314, 0,530] | **0,5740** [0,455, 0,678] |
| accuracy | 0,4024 | 0,6098 |
| Cohen's κ | 0,2760 | 0,5202 |
| AURC | 0,5395 | **0,2753** |
| ECE thô → sau T (cross-fit 5 phần) | 0,3218 → 0,1455 | 0,2935 → 0,2505 |
| NLL thô → sau T | 2,7172 → 1,7251 | 3,3182 → **1,5205** |
| T | 4,150 ± 0,43 | 5,010 ± 0,62 |
| epoch `val_loss` đáy | 10 | 9 |
| gap train/val cuối | +2,838 | +2,547 |
| thời gian | 4,11h | 4,09h |

Bootstrap **ghép cặp** (cùng bệnh nhân): chênh lệch macro-F1 **+0,1496**, 95% CI **[−0,005, +0,295]**, P(E1>E0) = 0,973.

**Phán quyết:** E0 = 0,4244 rơi vào dải 0,35–0,50 → *protocol giải thích phần lớn*, pipeline lành. E1 − E0 = +0,1496 ≫ ngưỡng +0,05 → **lesion-tight thành mặc định**. Baseline ban tổ chức 0,6083; E1 còn cách 0,034.

### Quyết định & lý do

- **Giả thuyết cơ chế của tôi SAI, dù can thiệp đúng.** Tôi chốt trước 4 chỉ báo và dự đoán crop ăn tiền bằng cách giảm overfitting. Thực tế **3/4 chỉ báo trượt**: `val_loss` vẫn chạm đáy ở epoch 9 (E0: 10), gap cuối vẫn +2,5 (E0: +2,8). Chỉ macro-F1 đạt, và đạt rất đậm. Cơ chế thật là cắt sát làm **tín hiệu phân biệt** mạnh hơn, không làm model bớt học thuộc. Hai chuyện độc lập. Kết quả rơi vào ô không có trong bảng 4 dòng tôi lập.
- **macro-F1@coverage không dùng được ở n=82.** Ở coverage 50%, lớp hiếm chỉ còn 1–2 ca, F1 của lớp đó do một bệnh nhân quyết định rồi chiếm 1/7 trọng số macro. Nên macro-F1 nhảy loạn (0,5740 → 0,5559 → 0,5816 → 0,5211) trong khi accuracy tăng đều (0,6098 → 0,7561). **Đổi metric headline của selective sang risk–coverage/AURC**, và gộp out-of-fold 5 fold trước khi tính. Mục tiêu "macro-F1 ≥0,90 @ coverage 80%" hiện **chưa đứng vững về mặt thống kê**, cần phát biểu lại.
- **Temperature scaling là bắt buộc, không phải bước cuối tuỳ chọn.** NLL thô của E1 là 3,3182, **tệ hơn đoán mò** (ln 7 = 1,9459); sau hiệu chỉnh mới về 1,5205. E1 giỏi hơn E0 ở phân loại nhưng tự tin thái quá hơn. `T ≈ 5,0` là mức cực đoan.
- **Cross-fit temperature thay vì fit in-sample.** Fit ngay trên tập đánh giá cho ECE 0,1011; cross-fit 5 phần cho **0,1455**. Chênh 44%. Số in-sample không được đưa vào báo cáo.

### Đính chính hai sai sót của tôi trong phiên

1. Tôi nói nhiều lần `src/eval/calibration.py` và `src/eval/selective.py` **"chưa có dòng nào"**. Sai: chúng đã tồn tại đầy đủ từ commit `b7fd34c` (283 + 215 dòng, có sẵn cả `uncertainty_decomposition`). Việc cần làm là **chạy** chúng, không phải viết mới. Sai sót này làm lệch kế hoạch tôi đề xuất trong vài lượt.
2. Tôi báo `runs/` chưa được gitignore. Sai: `.gitignore:39` có `runs/`. Nguyên nhân là tôi nối lệnh bằng `&&`/`||` nên một script lỗi phía trước làm `||` bắn nhầm thông báo.

**Kết quả / số liệu:** Xem bảng trên. Không sửa code trong phiên này.

**Dang dở:**
- [ ] E1 mới 1 fold. Cần 5-fold để có số báo cáo được (Phase 2 theo Spec Sheet §3).
- [ ] Chưa gộp out-of-fold để tính selective trên 394 ca.
- [ ] Overfitting **chưa được xử lý**: `val_loss` chạm đáy ở epoch 9 ở cả hai run.
- [ ] Đòn bẩy kiến trúc (Siamese, +0,074 theo bảng SDR-Former) chưa dùng.

**Điểm vào phiên sau:** Chạy 4 fold còn lại của E1 để có CV đầy đủ, rồi `python -m src.eval.run` gộp out-of-fold và tính lại selective trên 394 ca. Cân nhắc giảm `epochs` 300 → 220 (đỉnh E1 ở epoch 200) để tiết kiệm ~1/4 giờ GPU mỗi fold.

**Cảnh báo cho tool sau:** (1) **Đừng báo cáo macro-F1@coverage tính trên một fold** — lớp hiếm tụt xuống 1–2 ca và con số vô nghĩa. (2) `T` phải cross-fit hoặc học trên fold khác; fit in-sample cho ECE tốt giả tạo ~44%. (3) `run_dir` chỉ băm khối `model:`, nên hai run khác dữ liệu mà cùng model sẽ **dùng chung thư mục và resume đè nhau** nếu không đặt `LLDMMRI_OUTPUT_DIR` riêng.

## S-061 · 2026-07-29 · claude-code

**Mục tiêu phiên:** Dựng E2 — Siamese đa pha (fusion v1) thay cho early-concat v0.

**Nhánh / commit:** `main` · `a736f55` → *(commit đang chờ)*

**Đã đụng file:**
- `src/models/siamese_fusion.py` — mới. Một encoder DenseNet121-3D **dùng chung**, chạy riêng cho từng thì, rồi hợp nhất bằng `attention` | `mean` | `concat`. Kèm `phase_embedding` và `input_downsample`.
- `src/models/__init__.py` — đăng ký `siamese_fusion` vào registry.
- `configs/e2_siamese.yaml` — mới, sinh từ `baseline_3dpatch.yaml`, **chỉ khác khối `model:` và `output_dir`** (có test khoá).
- `tests/test_models.py` — +7 test.

**Quyết định & lý do:**
- **Trọng số dùng chung, không phải 8 encoder riêng.** 316 mẫu train; 8 encoder riêng là 8 lần tham số và gần như chắc chắn overfit. Dùng chung giữ nguyên số tham số so với early-concat. Có test kiểm: đổi `num_phases` 4→8 mà số tham số không đổi.
- **`phase_embedding` là bắt buộc về mặt thiết kế.** Trọng số dùng chung nên encoder không phân biệt được arterial với T2WI. Không có vector nhận dạng thì, fusion `mean` hoàn toàn mù thứ tự thì — trong khi động học ngấm thuốc là tín hiệu chẩn đoán mạnh nhất của bài toán này.
- **`input_downsample: 2` là thoả hiệp bắt buộc, và nó là biến gây nhiễu.** Siamese chạy backbone 8 lượt nên FLOPs ~8×; E1 mất 4,09h/fold nên bản nguyên độ phân giải sẽ ~30h+, vượt cả session 12h lẫn quota tuần. Average-pool 2 cắt voxel đi 8 lần, đưa chi phí về xấp xỉ E1. Mất mát thông tin thấp hơn vẻ ngoài: cache lesion-tight có trung vị fov 53,8mm trên 96 voxel = ~0,56mm/voxel, trong khi pha động chỉ có độ phân giải gốc ~0,78mm (S-029) — **một nửa dataset đang bị nội suy vượt quá thứ máy chụp ghi được**. Nhưng phải nói thẳng: E2 so với E1 giờ là *Siamese ở nửa độ phân giải* so với *early-concat ở đủ độ phân giải*. **E2 thắng → kết luận mạnh. E2 thua → KHÔNG kết luận được**, phải chạy thêm E1 với cùng `input_downsample`.
- **Chỉ dùng API MONAI mà repo đã chạy thành công** (`DenseNet121(spatial_dims, in_channels, out_channels, dropout_prob, norm)`), lấy `out_channels` làm số chiều nhúng thay vì đụng vào nội tại `class_layers`. Đã cân nhắc thêm ResNet18 (hạng 2 challenge dùng nó, đạt 0,8078) nhưng **không thêm**: tôi không kiểm được chữ ký API ở local, và đoán API rồi để người dùng phát hiện sau 4h GPU là đúng kiểu lỗi dự án đã mắc ba lần.
- **Kiểm tham số đặt TRƯỚC `import torch`.** Ban đầu tôi để sau, khiến 2 test validation fail ở local vì thiếu torch. Cấu hình sai phải báo lỗi ngay cả khi chưa cài deep-learning stack.
- **`last_phase_weights` là đầu ra khoa học, không phải chi tiết nội bộ.** Đó là số cho ablation phase-importance ở W4 và để đối chiếu LI-RADS (kỳ vọng arterial/venous nổi bật). Có test kiểm nó là phân bố hợp lệ trên 8 thì.

**Kết quả / số liệu:** `pytest` **234 passed, 15 skipped** (231 → 234; 6 test E2 cần torch nên skip ở local). ruff sạch. **Chưa train.**

**Dang dở:**
- [ ] **Chưa chạy forward pass thật lần nào** — local không có torch (Python 3.13 nhiều khả năng không có wheel cho `torch==2.3.1` đã pin). Phải chạy `pytest tests/test_models.py` trên Kaggle **trước** khi train.
- [ ] Chưa đo thời gian/epoch của E2. Giả định `input_downsample: 2` đưa về ~4h/fold là **tính toán, chưa đo**.
- [ ] E1 mới 1 fold; 4 fold còn lại hoãn lại có chủ ý để sàng lọc kiến trúc trước (Spec Sheet §3 Phase 1).

**Điểm vào phiên sau:** Trên Kaggle: `pytest tests/test_models.py -q` (vài giây) → cell 1c đo thời gian → nếu ≤6h/fold thì `python -m src.train.run --config configs/e2_siamese.yaml --fold 1` với `LLDMMRI_OUTPUT_DIR=/kaggle/working/runs/E2_siamese`, cache **lesion-tight** giống E1.

**Cảnh báo cho tool sau:** (1) `input_downsample` là biến gây nhiễu khi so E2 với E1 — đừng đọc kết quả như so thuần kiến trúc. (2) Con số +0,074 của wrapper SNN được **suy ra từ quy ước đặt tên** trong bảng SDR-Former, chưa đối chiếu phần setup bài báo; kiểm trước khi trích vào report. (3) `run_dir` chỉ băm khối `model:`, mà E2 khác model nên digest tự khác E1 — lần này không cần lo trùng thư mục.

## S-062 · 2026-07-29 · claude-code

**Mục tiêu phiên:** Notebook Kaggle để train E2.

**Nhánh / commit:** `main` · `284f987` → *(commit đang chờ)*

**Đã đụng file:**
- `notebooks/04_train_e2_siamese.ipynb` — mới, 24 cell, output đã strip.

**Quyết định & lý do:**
- **Thêm cổng chặn thứ tư, đặt trước mọi thứ: chạy `pytest tests/test_models.py`.** `siamese_fusion.py` được viết trên máy không có torch nên 6 test của nó đang skip; đây là lần đầu chúng chạy thật. Vài giây, chặn được nguy cơ mất 4h GPU cho một model không dựng nổi.
- **Không cho notebook tự dò cache.** `find_cache_dir` chọn bừa khi mount nhiều cache. Cell 1 liệt kê mọi cache kèm `crop_mode`, người dùng điền tay, và có `assert crop_mode == "lesion_tight"` — E2 phải dùng đúng cache của E1 thì mới so được.
- **Cell xem trọng số attention.** Đây là thứ early-concat không cho được: model tự nói nó dựa vào thì nào. Kỳ vọng theo LI-RADS là arterial/venous nổi bật. Trọng số gần đều 1/8 nghĩa là attention chưa học được gì — một chẩn đoán mà macro-F1 không đưa ra được.
- **Cell calibration cross-fit `T` 5 phần**, không fit in-sample. In kèm mốc E0/E1 để đối chiếu ngay.
- **Cảnh báo in thẳng trong output**: không báo macro-F1@coverage trên một fold (S-060).

**Kết quả / số liệu:** 24 cell, cú pháp hợp lệ, output rỗng. `pytest` 234 passed, 15 skipped. ruff sạch.

**Dang dở:**
- [ ] **Notebook chưa chạy lần nào.** Không kiểm được ở local vì thiếu torch/monai.
- [ ] E2 chưa train.

**Điểm vào phiên sau:** Mở `notebooks/04_train_e2_siamese.ipynb` trên Kaggle, mount cache lesion-tight, chạy tuần tự. Bốn cổng chặn sẽ tự dừng nếu có gì sai.

**Cảnh báo cho tool sau:** `load_checkpoint` nằm ở `src/train/loop.py` (không phải `src/train/checkpoint.py`) và **trả về payload dict**, không tự nạp vào model — phải `model.load_state_dict(payload["model"])`. Tôi đã viết sai chỗ này lần đầu và chỉ phát hiện nhờ đối chiếu chữ ký thật.

## S-063 · 2026-07-29 · claude-code

**Mục tiêu phiên:** Sửa lỗi cổng 0 (pytest trên Kaggle) bắt được ở E2.

**Nhánh / commit:** `main` · `6e30561` → *(commit đang chờ)*

### Lỗi, và vì sao nó quan trọng hơn vẻ ngoài

`pytest tests/test_models.py` trên Kaggle: 5 test fail, tất cả cùng một lỗi:

```
RuntimeError: input image (T: 2 H: 2 W: 1) smaller than kernel size (kT: 2 kH: 2 kW: 2)
AvgPool3d(kernel_size=2, stride=2)
```

**DenseNet121-3D hạ mẫu 5 lần** (conv0 /2, pool0 /2, ba transition mỗi cái /2). Transition thứ ba dùng `AvgPool3d(kernel_size=2)` nên đầu vào của nó phải ≥2 ở mọi chiều — tức **khối vào encoder phải ≥ 32 ở mọi chiều**.

Hai hệ quả, cái thứ hai mới là cái đắt:

1. **Test cũ `test_densenet3d_maps_8_phases_to_7_classes` dùng 32×32×16 và luôn fail.** Nó chưa từng chạy: local không có torch nên nó **luôn skip**. Một test hỏng nằm im trong repo, chỉ lộ ra khi chạy ở nơi có torch.

2. **`input_downsample: 2` của E2 sẽ SẬP trên dữ liệu thật.** 96×96×48 chia đều 2 thành 48×48×24, và 24 không sống nổi qua 5 lần hạ mẫu. Config tôi viết ở S-061 **không thể chạy**. Trục Z chỉ có 48 voxel ngay từ đầu, không còn gì để cắt.

**Đã đụng file:**
- `src/models/siamese_fusion.py` — `input_downsample` nhận 1 số hoặc 3 số, **mặc định đổi thành `(2, 2, 1)`**; thêm `MIN_SPATIAL = 32` và chốt kiểm trong `forward` báo lỗi rõ ràng kèm số đo thật.
- `configs/e2_siamese.yaml` — `input_downsample: [2, 2, 1]`.
- `tests/test_models.py` — sửa mọi khối test lên ≥32 mọi chiều; +4 test.
- `notebooks/04_train_e2_siamese.ipynb` — sinh lại, ngân sách 6h → 9h kèm lý do.

**Quyết định & lý do:**
- **Hạ mẫu bất đẳng hướng `(2, 2, 1)`.** Chỉ cắt trong mặt phẳng, giữ nguyên Z. Cắt trong mặt phẳng an toàn vì cache lesion-tight có trung vị ~0,56mm/voxel trong khi pha động chỉ có độ phân giải gốc ~0,78mm (S-029) — cắt đôi chỉ trả lại phần nội suy. Z thì không có dư địa đó.
- **Chi phí đổi theo, và phải nói lại cho đúng.** `(2,2,1)` giảm voxel **4 lần**, không phải 8. Với 8 lượt forward, E2 tốn ~**2× E1 ≈ 8h/fold**, không phải "xấp xỉ E1" như tôi viết ở S-061. Vẫn lọt session 12h.
- **Ngân sách notebook 6h → 9h.** Con số 6h ở notebook 03 tính cho 5 fold nằm trong quota ~30h/tuần. Đây là run **sàng lọc một fold**, ràng buộc thật là session 12h. Đặt 9h để vẫn bắt được trường hợp lệch hẳn dự đoán.
- **Chốt kiểm đặt trong `forward`, không phải lúc dựng model.** Kích thước đầu vào chỉ biết được lúc chạy. Thông báo in cả kích thước gốc, hệ số, kích thước sau khi hạ mẫu và ngưỡng — đủ để sửa ngay mà không phải đọc code MONAI.

**Kết quả / số liệu:** `pytest` **238 passed, 17 skipped** (234 → 238). ruff sạch. Vẫn **chưa chạy được forward pass ở local** — 4 test mới cần torch nên skip; chúng chạy thật ở cổng 0 trên Kaggle.

**Dang dở:**
- [ ] Chạy lại cổng 0 trên Kaggle để xác nhận 5 test đã xanh.
- [ ] E2 vẫn chưa train.

**Điểm vào phiên sau:** `git pull` trên Kaggle, chạy lại notebook 04 từ cổng 0. Nếu xanh thì đi tiếp cổng 1→2→3. Cổng 3 giờ kỳ vọng ~8h/fold, không phải ~4h.

**Cảnh báo cho tool sau:** (1) **DenseNet121-3D cần ≥32 voxel ở MỌI chiều.** Bất kỳ chỗ nào hạ mẫu hoặc crop nhỏ hơn thế sẽ chết bằng `RuntimeError` sâu trong MONAI, không nói gì về nguyên nhân. (2) **Test skip ở local không có nghĩa là test đúng.** Test 32×32×16 đã nằm im trong repo cho tới khi chạy ở nơi có torch. Mọi thay đổi model phải qua cổng 0 trên Kaggle trước khi tin.

## S-064 · 2026-07-30 · claude-code

**Mục tiêu phiên:** Đọc paper CGHNet, chẩn đoán E2 kém, dựng E3.

**Nhánh / commit:** `main` · `6f15002` → *(commit đang chờ)*

### CGHNet (Comput Med Imaging Graph 132, 2026, doi:10.1016/j.compmedimag.2026.102780)

Đọc từ `papers/`. Ba thứ đáng giá:

**1. Hình học đầu vào.** Nguyên văn: *"all lesion volumes were spatially normalized to a fixed size of **16 × 128 × 128**... Random crops of size **14 × 112 × 112**"*.

| | Z | in-plane | voxel |
|---|---|---|---|
| baseline official | 14 | 112 | 176k |
| CGHNet | 14–16 | 112–128 | 229–262k |
| **E0/E1 của ta** | **48** | **96** | 442k |
| **E2 sau hạ mẫu** | **48** | **48** | 111k |

Ta là ngoại lệ: gấp 3 số lát, ít pixel trong mặt phẳng hơn. Và `input_downsample: (2,2,1)` của tôi đẩy in-plane xuống 48, thấp hơn 2,3–2,7 lần **mọi** phương pháp công bố.

**2. 2D thắng 3D trên chính dataset này** (5-fold CV, F1%): nhánh 2D 74,2 ± 2,1 · nhánh 3D 72,4 ± 1,8 · hybrid concat 76,9 · +ADF 78,5 · +CGFM 80,1 · full 81,8 ± 1,2. Lý do họ đưa ra: *"fine-grained intra-slice semantics are easier to optimize than volumetric features under limited data regimes"*.

**3. Đa pha là bắt buộc:** T2WI một mình 60,5 · ART một mình 63,8 · chỉ DCE 70,2 · đủ 8 thì 81,8.

Recipe của họ: 300 epoch, batch 4, Focal Loss, AdamW, cosine + 5 epoch warmup, 5-fold CV trên train+val gộp, RTX 4090.

### Chẩn đoán E2

Người dùng báo E2 quanh 0,35–0,49 ở epoch 100+. Đối chiếu cùng mốc: E1 đạt **0,5363 @ epoch 112**, và đường cong E1 rất nhiễu (0,283 @ep80 → 0,447 @ep100 → 0,574 @ep200).

**Kết luận: biến gây nhiễu tôi cảnh báo ở S-061 hoá ra là thủ phạm, không phải nhiễu phụ.** E2 chạy in-plane 48 trong khi văn liệu dùng 112–128. Người dùng đã kill E2. Đúng quyết định: kể cả nó phục hồi thì con số cũng không nói được gì về Siamese.

**Đã đụng file:**
- `configs/preprocess_e3.yaml` — mới. Chép từ `preprocess.yaml`, đổi `target_size: [112, 112, 32]` và `cache_dir` riêng.
- `tests/test_models.py` — +3 test khoá ràng buộc hình học.

**Quyết định & lý do:**
- **E3 = sửa hình học, giữ nguyên kiến trúc E1.** Chỉ đổi dữ liệu, đúng kiểu cú E0→E1 vốn đã cho +0,15. Không cần config train mới: dùng lại `baseline_3dpatch.yaml`, chỉ đổi `LLDMMRI_CACHE_DIR` và `LLDMMRI_OUTPUT_DIR`.
- **112 × 112 × 32, không phải 128 × 128 × 16 như CGHNet.** In-plane 112 khớp đúng crop của cả baseline official lẫn CGHNet. **Z=32 là nhượng bộ với DenseNet, không phải con số văn liệu**: Z=16 sẽ sập (sau conv0, pool0, hai transition thì 16 còn 1, transition thứ ba dùng `AvgPool3d(2)` — S-063). CGHNet dùng ViT + CNN nên không vướng. Đã ghi rõ trong config và khoá bằng test để không ai tưởng 32 là số lấy từ paper.
- **Giữ nguyên `translate_voxels: [8, 8, 4]`.** Trên 32 lát thì ±4 là ±12,5% thay vì ±8,3% trên 48 lát, tức augmentation trục Z **mạnh hơn tương đối**. Cố ý không chỉnh: giữ config y hệt E1 làm so sánh sạch hơn, và lệch này nếu có tác dụng thì là **bất lợi cho E3**, nên E3 thắng vẫn là kết luận đúng.
- **`cache_dir` riêng, có test khoá.** Lần đầu tôi viết chuỗi thay thế sai nên `cache_dir` vẫn trỏ vào cache E1 — mà `build_cache` có resume, nên nó sẽ lặng lẽ **trộn hai hình học vào cùng một mẻ**. Thêm `test_preprocess_configs_write_to_separate_caches` để không tái diễn.
- **Không xác minh được con số +0,074 của SDR-Former.** File `papers/1-s2.0-S0893608025002254-main.pdf` hoá ra là một bài Neural Networks khác (Yang et al., về ADF), không phải SDR-Former. Cảnh báo ở S-061 vẫn còn nguyên hiệu lực.

**Kết quả / số liệu:** `pytest` **241 passed, 17 skipped** (238 → 241). ruff sạch. E3 = 401k voxel ≈ **0,91× E1** → ước tính ~3,7h/fold.

**Dang dở:**
- [ ] Chưa build cache E3, chưa train.
- [ ] E1 vẫn mới 1 fold.
- [ ] Siamese chưa được đánh giá công bằng — nếu E3 thắng thì đáng chạy lại Siamese ở hình học đúng.

**Điểm vào phiên sau:** Build cache E3 trên Kaggle (`--limit 20` trước), upload thành dataset, rồi train fold 1 bằng `baseline_3dpatch.yaml` với cache mới.

**Cảnh báo cho tool sau:** (1) **Z=16 của CGHNet không dùng được với DenseNet121-3D.** Muốn theo đúng hình học của họ thì phải đổi backbone. (2) Nhánh 2D của CGHNet **thắng** nhánh 3D trên chính dataset này — nhánh 2.5D trong Spec Sheet nên được nâng từ fallback lên ứng viên chính, không phải phương án dự phòng.

## S-065 · 2026-07-30 · claude-code

**Mục tiêu phiên:** Đọc **bản PDF gốc** của CGHNet (`papers/1-s2.0-S0895611126000832-main.pdf`) và soát lại kết luận ở S-064.

**Nhánh / commit:** `main` · `4396e12` → *(commit đang chờ)*

### Vì sao phải đọc lại

S-064 đọc bản **in từ trang web ScienceDirect** (48 trang, lẫn giao diện). Bản gốc 12 trang có bảng ở dạng text, đọc được chính xác. Kết quả: một kết luận của tôi **sai**, và có thêm dữ liệu quan trọng hơn hẳn.

### Đính chính: tuyên bố "2D thắng 3D" là SAI

S-064 tôi viết "nhánh 2.5D nên nâng từ fallback lên ứng viên chính", dựa trên Bảng 2 của CGHNet (nhánh 2D 74.2 so với nhánh 3D 72.4).

**Đó là so sánh nội bộ giữa hai nhánh của CGHNet, không phải phép thử 2D-vs-3D.** Nhánh 2D của họ là ViT, nhánh 3D là CNN — khác kiến trúc, nên chênh lệch không quy về số chiều được.

Phép thử sạch nằm ở **Bảng 1**, cùng họ kiến trúc, cùng protocol: **ResNet3D 0.709 THẮNG ResNet2D 0.684**. Ngược hẳn kết luận tôi đưa.

Đã sửa comment sai trong `configs/preprocess_e3.yaml`. Đề xuất nâng 2.5D lên ứng viên chính **bị rút lại**.

### Dữ liệu mới, giá trị cao hơn cả bảng leaderboard

Bảng 1 của CGHNet đo **mọi phương pháp trên đúng test-104 official, cùng một protocol** (16×128×128 → crop 14×112×112, Focal loss, AdamW lr 1e-4, wd 1e-5, 300 epoch, batch 4, 5 fold). F1:

```
ViT3D 0.645 · ResNet2D 0.684 · ConvNeXt2D 0.696 · ResNet3D 0.709
Swin3D 0.709 · 3D UX-Net 0.709 · Uniformer 0.719 · SDR-Former 0.791
STM-Former 0.793 · RadioFormer 0.806 · CGHNet 0.818
```

**Con số đắt nhất: `ResNet3D` trần đạt 0.709**, vượt baseline official 0.6083 tới 0.10, chỉ nhờ hình học đầu vào. Đây là bằng chứng mạnh nhất tới giờ cho giả thuyết hình học của E3 — mạnh hơn nhiều so với lập luận 2D/3D sai ở S-064.

Bảng 4 (ablation huấn luyện): **Focal Loss 81.8 so với CE 79.9** · **bỏ random-crop mất 8.8 điểm** (73.0, biến augmentation nặng nhất) · lr 1e-4 tốt hơn 1e-3 (79.3) lẫn 1e-5 (80.8).

**Đã đụng file:**
- `AGENTS.md` §5 — thêm bảng so sánh có kiểm soát + ba điều rút ra. Đặt cạnh bảng leaderboard vì mục này vốn ghi "ai định debug chất lượng model phải đối chiếu bảng này trước", mà bảng cùng-protocol hữu ích hơn hẳn cho việc đó.
- `configs/preprocess_e3.yaml` — thay lập luận 2D/3D sai bằng bảng số thật.

**Quyết định & lý do:**
- **Giữ nguyên E3 như đã thiết kế.** Bằng chứng mới **củng cố** E3 chứ không đổi nó: hình học là biến, kiến trúc 3D vẫn hợp lệ.
- **Không gộp Focal Loss vào E3.** Đáng +1.9 điểm theo Bảng 4, nhưng gộp vào sẽ làm E3 có hai biến. Để riêng thành E4, đo được sạch.
- **Ghi nhận một căng thẳng chưa giải quyết: Z=32 của ta so với Z=14 của văn liệu.** DenseNet121-3D không chịu được Z=14 (S-063), trong khi ResNet3D thì có — và ResNet3D chính là hàng đạt 0.709. Nếu E3 xác nhận hình học là nút thắt thì bước hợp lý tiếp theo là **đổi sang 3D ResNet ở đúng 14×112×112**, tức bám sát văn liệu hoàn toàn. Chưa làm vì chưa kiểm được chữ ký API `monai.networks.nets.resnet18` ở local.
- **SDR-Former 0.791 dưới protocol thống nhất.** Hướng Siamese của E2 không sai về nguyên tắc — hình học mới là chỗ hỏng. Con số +0.074 cho riêng wrapper SNN thì vẫn **chưa xác minh được**, nó nằm trong paper SDR-Former mà ta không có.

**Kết quả / số liệu:** Không train. `pytest` 241 passed, 17 skipped.

**Dang dở:**
- [ ] Chưa build cache E3, chưa train.
- [ ] Chưa đánh giá 3D ResNet ở 14×112×112 — ứng viên mạnh nhất theo bằng chứng hiện có.

**Điểm vào phiên sau:** Build cache E3, train fold 1. Nếu E3 vượt rõ E1 (0.5740) thì cân nhắc E5 = ResNet3D ở đúng 14×112×112.

**Cảnh báo cho tool sau:** (1) **Đừng đọc bảng ablation nội bộ của một paper như thể nó là so sánh có kiểm soát.** Hai nhánh của CGHNet khác kiến trúc; tôi đã kết luận sai vì bỏ qua điều đó. (2) **Bản in từ trang web ScienceDirect làm mất bảng số** — S-064 chỉ đọc được số nhờ chúng lọt vào phần chữ. Luôn tìm PDF gốc.

## S-066 · 2026-07-30 · claude-code

**Mục tiêu phiên:** Notebook chạy E3 trọn gói.

**Nhánh / commit:** `main` · `b65345e` → *(commit đang chờ)*

**Đã đụng file:**
- `notebooks/05_e3_geometry.ipynb` — mới, 23 cell, output đã strip.

**Quyết định & lý do:**
- **Build cache và train trong CÙNG một session, không upload dataset trung gian.** Cache mất ~26 phút, train ~3,7h, tổng ~4,2h — lọt session 12h. Bỏ được hẳn vòng "Save Version → tạo Dataset → mount lại" vốn tốn thêm một lượt chờ. Cache ghi vào `/kaggle/working/cache_e3`, train đọc thẳng từ đó.
- **Bốn cổng chặn**, hai cho cache hai cho train: A1 thử 20 ca (kiểm `crop_source` là `mask`, `fov_mm` co giãn) · A2 xác minh 498 file và shape đúng `(8,112,112,32)` · B1 hợp đồng dataset↔model · B2 đo thời gian, kỳ vọng ~3,7h vì E3 có 0,91× voxel của E1.
- **Dùng lại `configs/baseline_3dpatch.yaml` không sửa một dòng.** E3 chỉ đổi dữ liệu. `LLDMMRI_OUTPUT_DIR` đặt riêng vì `run_dir` chỉ băm khối `model:`, mà E1 và E3 cùng model nên digest trùng — quên là E3 resume đè lên E1 (S-060).
- **Thêm cell soi đường cong overfitting.** E0 và E1 đều có `val_loss` chạm đáy ở epoch 9–10. Nếu E3 đẩy mốc đó ra xa thì hình học còn giúp giảm overfit chứ không chỉ tăng điểm — đó là thông tin cơ chế, ít nhiễu hơn một điểm số trên 82 ca.
- **In sẵn cảnh báo về cỡ mẫu ngay trong output.** CI ở n=82 rộng cỡ ±0,10 nên E3 là sàng lọc, không phải số báo cáo.

**Kết quả / số liệu:** 23 cell, cú pháp hợp lệ, mọi import từ `src/` đã đối chiếu tồn tại thật. `pytest` 241 passed, 17 skipped. ruff sạch. **Chưa chạy.**

**Dang dở:**
- [ ] Notebook chưa chạy lần nào — không kiểm được ở local vì thiếu torch/monai.
- [ ] E3 chưa có số.

**Điểm vào phiên sau:** Mở `notebooks/05_e3_geometry.ipynb` trên Kaggle, mount **dataset thô** `lldmmridataset` (không cần cache nào), chạy tuần tự.

**Cảnh báo cho tool sau:** Notebook này **build cache vào `/kaggle/working`**, tức nó biến mất khi session kết thúc nếu không Save Version. Chấp nhận được vì build chỉ 26 phút, nhưng đừng ngạc nhiên khi mở lại thấy trống.
