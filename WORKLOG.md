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
