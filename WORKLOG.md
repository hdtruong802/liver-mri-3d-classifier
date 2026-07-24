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
