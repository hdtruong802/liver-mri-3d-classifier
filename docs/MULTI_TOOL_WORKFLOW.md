# Giao thức làm việc đa tool

> Ngữ cảnh dự án ở [`../AGENTS.md`](../AGENTS.md). Lịch sử phiên ở [`../WORKLOG.md`](../WORKLOG.md).
> File này chỉ trả lời một câu hỏi: **làm sao 4 tool AI coding luân phiên trên cùng repo mà không giẫm chân nhau.**

Tool trong vòng luân phiên: **Claude Code · Google Antigravity · OpenAI Codex · Cursor**. Một người dùng, một máy.

---

## 1. Luật nền: một tay lái tại một thời điểm

Không có cơ chế khoá kỹ thuật nào ép được điều này — nó là kỷ luật, và nó là thứ giữ cho mọi luật còn lại có nghĩa.

- **Đúng một tool được "cầm lái"** tại một thời điểm. Tool đang cầm lái là tool ghi entry mở trong `WORKLOG.md`.
- **Đóng hẳn tool cũ trước khi mở tool mới.** Không để Cursor mở sẵn workspace trong khi Claude Code sửa file ở terminal — cả hai đều có file watcher và cơ chế auto-save, và tool nền có thể ghi đè bản trên đĩa bằng buffer cũ trong editor. Đây là nguồn mất code âm thầm nhất trong toàn bộ setup này.
- **Git là ranh giới bàn giao.** Việc chưa commit = việc chưa bàn giao. Rời tool mà để việc ngoài git là vi phạm giao thức.

---

## 2. Checklist rời tool

Chạy đủ, theo thứ tự. Không bỏ bước nào vì "phiên này ngắn".

```bash
# 1. Cây làm việc phải sạch hoặc được commit hết
git status --short

# 2. Quality gate (nếu phiên có đụng UI: webapp / slides / reports)
# Windows PowerShell (không cần WSL):
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1
# Bash thật (macOS/Linux/Git Bash):
sh scripts/quality-gate.sh

# 3. Test (khi đã có test)
pytest -q

# 4. Ghi entry WORKLOG — BẮT BUỘC, template ở đầu WORKLOG.md
#    Trường "Điểm vào phiên sau" không được để trống.

# 5. Commit gộp cả việc lẫn entry WORKLOG
git add -A
git commit -m "<type>(<scope>): <mô tả>"

# 6. Đẩy lên remote — đây mới là điểm bàn giao thật
git push

# 7. Xác nhận không còn gì sót
git status --short   # phải trắng
```

Nếu bước 1 cho thấy có thay đổi bạn **không nhận là của mình** → dừng, không commit đè. Đó là dấu hiệu tool trước rời đi không sạch. Ghi entry WORKLOG mô tả tình trạng, rồi hỏi người dùng.

---

## 3. Checklist vào tool mới

```bash
# 1. Lấy trạng thái mới nhất
git pull --ff-only

# 2. Xác nhận sạch
git status --short   # phải trắng

# 3. Đọc điểm bàn giao
tail -n 80 WORKLOG.md
```
```powershell
# PowerShell tương đương bước 3
Get-Content WORKLOG.md -Tail 80
```

4. Đọc `AGENTS.md` (Claude Code/Cursor tự nạp qua cầu nối; Codex/Antigravity đọc trực tiếp).
5. Nếu `git pull --ff-only` **thất bại** → có commit local chưa push từ phiên trước. Không `--rebase` bừa; xem log, xác định phiên nào bỏ sót bước 6, ghi WORKLOG rồi mới xử lý.

---

## 4. Ma trận sở hữu file — ai được sửa gì

Quy tắc gốc: **tool chỉ sửa file cấu hình của chính nó.** Vi phạm phổ biến nhất là một agent "dọn dẹp giúp" file config của tool khác rồi tool đó ghi đè lại ở phiên sau, tạo ping-pong diff vô tận.

| Đường dẫn | Chủ sở hữu | Ghi chú |
|---|---|---|
| `AGENTS.md` | **Mọi tool** | Nguồn sự thật chung. Sửa phải kèm entry WORKLOG. |
| `WORKLOG.md` | **Mọi tool** | Chỉ append cuối file. |
| `docs/`, `src/`, `webapp/`, `slides/`, `reports/`, `configs/`, `scripts/` | **Mọi tool** | Vùng làm việc chung. |
| `PRODUCT.md`, `DESIGN.md` | **Mọi tool** | Impeccable sinh ra, sau đó là tài liệu chung. Sửa tay được. |
| `CLAUDE.md` | Chỉ **Claude Code** | Tool khác đọc được, không sửa. |
| `.claude/` | Chỉ **Claude Code** | Kể cả khi Impeccable ghi vào đây — xem §8.3. |
| `.cursor/` | Chỉ **Cursor** | Bao gồm `rules/` và `hooks.json`. |
| `.codex/` | Chỉ **Codex** | |
| File/thư mục do **Antigravity** sinh | Chỉ **Antigravity** | Xem §9. |
| `.impeccable/config.json`, `design.json` | **Tool nào chạy `/impeccable init`** | Sau đó coi như read-only, sửa qua lệnh Impeccable chứ không sửa tay. |
| `.gitignore` | **Mọi tool**, nhưng chỉ được **thêm** dòng | Bỏ ignore một thư mục dữ liệu = phải hỏi người dùng (AGENTS.md §10). |
| `splits/` | **Đã khoá** | Không sinh lại, không commit đè. Xem §5.4. |

---

## 5. Những điểm xung đột thật

Đây là danh sách trung thực. Ba trong số này **không loại bỏ được hoàn toàn**, chỉ giảm thiểu — được đánh dấu ⚠️.

### 5.1 Hai tool cùng mở repo → ghi đè âm thầm
Editor (Cursor, hoặc VS Code chạy Antigravity) giữ buffer trong bộ nhớ. Nếu Claude Code sửa file dưới terminal trong lúc đó, một thao tác save ở editor sẽ ghi đè bằng nội dung cũ, **không hề báo conflict**.
**Phòng:** đóng hẳn tool cũ trước khi mở tool mới (§1). Nếu buộc phải mở song song, sau khi tool khác sửa file thì `git diff` để xác nhận nội dung trên đĩa đúng trước khi commit.

### 5.2 Mỗi tool tự ghi đè file cấu hình của nó
Cursor viết lại `.cursor/`, Codex viết `.codex/hooks.json`, Antigravity sinh cấu hình riêng. Nếu tool khác từng "sửa giúp", thay đổi đó sẽ bị nuốt.
**Phòng:** ma trận §4. Nếu thấy diff lạ trong thư mục của tool khác → `git checkout -- <path>` thay vì cố gộp.

### 5.3 ⚠️ Impeccable ghi hook vào `.claude/settings.local.json`
`npx impeccable install --providers=claude,...` cài hook Claude Code vào **`.claude/settings.local.json`** — file mà theo quy ước Claude Code là *local, không commit*. Với Cursor và Codex nó ghi vào `.cursor/hooks.json` và `.codex/hooks.json`, hai file này commit được bình thường.
**Hệ quả:** hook Impeccable của Claude Code không được chia sẻ qua git, và **sẽ mất** nếu bạn clone repo sang máy khác hoặc reset thư mục `.claude/`.
**Giảm thiểu:** repo này chỉ có một người, một máy → tác động thấp. Khi setup máy mới, chạy lại `npx impeccable install` là xong. Ghi nhận trong WORKLOG rằng hook Claude Code là *máy-cục-bộ*, đừng đi tìm nó trong git rồi tưởng mất. **Không** commit `.claude/settings.local.json` — nó có thể chứa cả cấu hình cá nhân/đường dẫn máy.

### 5.4 `splits/` bị sinh lại
Bất kỳ agent nào chạy lại `make_splits` rồi commit đè sẽ **phá tính so sánh** của mọi kết quả CV đã có, mà diff nhìn rất vô hại.
**Phòng:** quality gate (§10) chặn commit nếu `splits/` bị sửa mà không có biến môi trường `ALLOW_SPLIT_CHANGE=1`.

### 5.5 Notebook Kaggle mang theo output
Notebook export từ Kaggle chứa cả output (ảnh base64, log) → diff hàng nghìn dòng, conflict gần như không giải được, và repo phình.
**Phòng:** chỉ commit notebook đã strip output.
```bash
pip install nbstripout && nbstripout --install   # cài filter một lần cho repo
```
Notebook chỉ là lớp mỏng gọi vào `src/` (AGENTS.md §4) — nếu diff notebook lớn, đó là dấu hiệu logic đang bị copy-paste vào notebook thay vì để trong `src/`.

### 5.6 Lockfile / `node_modules`
Frontend thuần nhưng vẫn có thể cần vài package (ví dụ Chart.js). Nếu hai tool ở hai thời điểm chạy `npm install` với version npm khác nhau, `package-lock.json` sẽ churn vô nghĩa.
**Phòng:** ưu tiên **không có `package.json`** cho frontend — nhúng thư viện dưới dạng file tĩnh trong `webapp/frontend/vendor/`. Nếu buộc phải có, thì commit lockfile và chỉ cài bằng `npm ci`, không `npm install`.
`npx impeccable` không tạo `package.json` trong repo (nó chạy từ cache npx) → không ảnh hưởng.

### 5.7 File ephemeral của Impeccable
`.impeccable/hook.cache.json`, `.impeccable/hook.pending.json`, ảnh screenshot `*.png`, toàn bộ `.impeccable/live/` sinh liên tục trong lúc làm việc. Một lệnh `git add -A` sẽ nuốt hết vào commit.
**Phòng:** khối `.gitignore` ở §8.4 — phải có **trước** khi chạy `npx impeccable install` lần đầu.

### 5.8 ⚠️ Memory nội bộ của Antigravity drift khỏi `AGENTS.md`
Antigravity có hệ memory riêng, lưu ngoài repo, không được git theo dõi và không ai review. Nó sẽ ghi nhớ quyết định cũ và tiếp tục dùng sau khi `AGENTS.md` đã đổi.
**Giảm thiểu:** §9.2. Không có cách nào loại bỏ hoàn toàn.

### 5.9 ⚠️ Impeccable không hỗ trợ Antigravity
Antigravity không nằm trong danh sách provider của Impeccable → **không có lệnh `/impeccable`** ở đó. UI do Antigravity sinh ra không đi qua cùng quy trình như ba tool kia.
**Giảm thiểu:** §9.3 — CLI `detect` làm quality gate chung, chạy được cho mọi tool. Nhưng phần *sinh* thiết kế (shape/craft) thì Antigravity vẫn yếu thế hơn; khuyến nghị **không giao việc dựng UI mới cho Antigravity**, chỉ giao sửa lỗi logic/backend.

---

## 6. Branch & commit

Mở rộng từ `AGENTS.md` §9.

- Việc ngắn (< 1 phiên) làm thẳng trên `main` cũng được — dự án một người. Việc dài hơn một phiên hoặc **có thể phải bỏ** thì tách nhánh: `feat/` `fix/` `exp/` `docs/`.
- **Nhánh `exp/` cho thí nghiệm train.** Kết quả xấu thì bỏ nhánh, nhưng **vẫn ghi WORKLOG** — thí nghiệm thất bại là dữ liệu, không phải rác.
- **Một phiên tool ≥ một commit.** Không gộp nhiều phiên vào một commit khổng lồ ở cuối ngày; ranh giới commit nên trùng ranh giới phiên để `git log` và `WORKLOG.md` đọc song song được.
- Trong message commit, ghi kèm mã phiên khi hữu ích: `exp(fusion): phase-attention v1 (S-014)`.
- Không `--force` lên `main`.

---

## 7. Impeccable — cài đặt

[github.com/pbakaus/impeccable](https://github.com/pbakaus/impeccable) — design skill đa harness, dùng cho **cả ba loại deliverable có mặt người dùng**: web app, HTML slide, HTML report.

**Trước khi cài:** đảm bảo khối `.gitignore` ở §8.4 đã có trong repo (§5.7).

```bash
# Cài skill cho 3 tool có hỗ trợ. Antigravity không có trong danh sách provider.
npx impeccable install --providers=claude,codex,cursor --scope=project
```

Lệnh này chép **nguyên bộ skill vào ba chỗ**: `.claude/skills/`, `.cursor/skills/`, `.agents/skills/` (payload cho Codex) — 377 file, ~8.7MB, ba bản y hệt nhau. Chúng đã được `.gitignore`; máy mới chỉ cần chạy lại lệnh trên. Hook cài vào `.cursor/hooks.json`, `.codex/hooks.json` (commit được) và `.claude/settings.local.json` (§5.3).

> ⚠️ **Skill mới cài chưa dùng được trong session Claude Code đang mở.** Registry skill nạp lúc khởi động — phải **khởi động lại Claude Code** thì `/impeccable` mới nhận.

### 7.1 `init` sinh cái gì — và không sinh cái gì

**`/impeccable init` chỉ viết `PRODUCT.md`.** Nó **không** viết `DESIGN.md`, và cố ý **không hỏi gì về thẩm mỹ** (màu, font, phong cách). Đây là điểm rất dễ hiểu nhầm.

`DESIGN.md` được tạo ở bước sau, theo một trong hai đường:
- **`new-work`** — tự động chạy bên trong `/impeccable shape` hoặc `/impeccable craft` khi việc bạn yêu cầu thực sự cần một thế giới thị giác. Đây là đường đi bình thường của dự án này.
- **`/impeccable document`** — ghi lại design system của một giao diện **đã có sẵn**. Chỉ dùng nếu bạn đã tự dựng UI trước rồi mới muốn khai báo nó.

Hệ quả về thứ tự: **đừng đi tìm `DESIGN.md` ngay sau `init`.** Nó sẽ xuất hiện lần đầu khi bạn chạy `/impeccable shape <bề mặt>`.

### 7.2 Ràng buộc thiết kế nằm ở đâu

Vì `init` không nhận đầu vào thẩm mỹ, ràng buộc giọng và thị giác của dự án được giữ ở **hai chỗ, cả hai đều commit**:

- [`../PRODUCT.md`](../PRODUCT.md) — mục **Product Principles**, **Brand Commitments** và **Accessibility & Inclusion** đã ghi các ràng buộc cứng: mức bất định luôn đi kèm số, `defer` là kết quả hợp lệ, RUO trên mọi bề mặt, thông tin không bao giờ chỉ mã hoá bằng màu, tiếng Việt có dấu. Impeccable đọc file này khi dựng thế giới thị giác.
- [`../AGENTS.md`](../AGENTS.md) §12 — 8 ràng buộc thiết kế áp cho **mọi tool**, kể cả tool không có `/impeccable` (§9.1).

**Khi `DESIGN.md` xuất hiện lần đầu: đọc kỹ và sửa tay** chỗ nào lạc giọng. Đây là công cụ y tế research, không phải landing page — không gradient rực rỡ, không hiệu ứng khoe kỹ thuật, không micro-interaction vui vẻ. Từ lúc đó, `DESIGN.md` chi phối cả ba deliverable.

---

## 8. Impeccable — dùng lệnh nào, lúc nào

Nguyên tắc: **`shape` trước khi code, `critique`/`audit` trước khi chốt.** Chạy `polish` khi chưa `shape` là đánh bóng một cấu trúc sai.

### 8.1 Web app demo (`webapp/`)

| Giai đoạn | Lệnh | Mục đích |
|---|---|---|
| Trước khi viết dòng UI đầu tiên | `/impeccable shape` | Chốt luồng: upload → xử lý → kết quả. Quyết định cái gì nổi bật (probs, uncertainty, defer). |
| Dựng UI | `/impeccable craft` | Dựng có vòng lặp thị giác, bám `DESIGN.md`. |
| Có slice-viewer + biểu đồ xác suất | `/impeccable layout` | Nhịp thị giác, khoảng cách, tương quan viewer ↔ panel số liệu. |
| Trạng thái lỗi & biên | `/impeccable harden` | File sai định dạng, thiếu pha, volume quá lớn, timeout. **Quan trọng với app y tế.** |
| Lần chạy đầu của người dùng | `/impeccable onboard` | Empty state, ca demo dựng sẵn, giải thích `defer` nghĩa là gì. |
| Trước khi chốt | `/impeccable critique` → `/impeccable audit` | `critique`: phân cấp thông tin, độ rõ. `audit`: a11y, performance, responsive. |
| Chốt | `/impeccable polish` | Đồng bộ design system, sẵn sàng trình diễn. |

Cân nhắc thêm: `/impeccable clarify` cho chữ trong UI — từ ngữ về mức bất định rất dễ gây hiểu nhầm ở ngữ cảnh lâm sàng, đáng chạy riêng một lượt.
**Tránh:** `bolder`, `delight`, `overdrive`, `colorize`. Sai giọng cho dự án y tế.

### 8.2 HTML slide (`slides/`) và report (`reports/`)

| Giai đoạn | Lệnh | Mục đích |
|---|---|---|
| Trước khi dựng | `/impeccable shape` | Mạch kể: vấn đề → khoảng trống SOTA → phương pháp → kết quả có CI → hạn chế. |
| Chữ nghĩa | `/impeccable typeset` | Font, phân cấp, cỡ chữ. Quan trọng nhất với slide (đọc từ xa) và report (đọc lâu). |
| Bố cục | `/impeccable layout` | Lưới, khoảng trắng, vị trí bảng/biểu đồ. |
| Slide, nếu cần | `/impeccable animate` | Chỉ chuyển cảnh có mục đích. Không hiệu ứng trang trí. |
| Trước khi chốt | `/impeccable critique` → `/impeccable audit` → `/impeccable polish` | Như trên. |

Slide và report **dùng chung `DESIGN.md` với web app** — ba deliverable phải nhìn như một hệ thống. Nếu đã trích được token/component dùng chung, chạy `/impeccable extract` để đưa vào design system thay vì chép CSS qua lại.

### 8.3 File Impeccable — commit hay ignore

**Commit** (đây là ngữ cảnh thiết kế dùng chung cho cả 4 tool, mất là mất trí nhớ thiết kế):
```
PRODUCT.md
DESIGN.md                      (xuất hiện lần đầu khi chạy shape/craft — §7.1)
.impeccable/config.json
.impeccable/design.json
.impeccable/critique/*.md
.impeccable/live/config.json
.cursor/hooks.json
.codex/hooks.json
```

**Không commit:**
- `.claude/settings.local.json` — §5.3.
- **Payload skill: `.claude/skills/impeccable/`, `.cursor/skills/impeccable/`, `.agents/skills/impeccable/`** — 377 file × 3 bản, ~8.7MB. Cài lại bằng `npx impeccable install`. Đánh đổi: version Impeccable **không được pin trong git**; nếu cần khoá, ghi số version vào WORKLOG chứ đừng commit 8.7MB.
- Toàn bộ khối ephemeral ở §8.4.

`.impeccable/critique/*.md` **phải commit** — đó là biên bản review thiết kế, sẽ dùng lại khi viết phần Limitations của report.

### 8.4 Khối `.gitignore` cho Impeccable

Đã có trong [`../.gitignore`](../.gitignore). Bản chuẩn để đối chiếu:

```gitignore
# Impeccable — ephemeral
.impeccable/config.local.json
.impeccable/hook.cache.json
.impeccable/hook.pending.json
.impeccable/*.png
.impeccable/detect-report.json
.impeccable/live/server.json
.impeccable/live/sessions/
.impeccable/live/previews/
.impeccable/live/annotations/
.impeccable/live/cache/
.impeccable/live/*.png
```

---

## 9. Xử lý riêng cho Antigravity

Antigravity **không có** `/impeccable`. Bù lại bằng ba việc.

### 9.1 Ràng buộc thiết kế qua `AGENTS.md`

`AGENTS.md` §12 buộc mọi tool đọc `DESIGN.md` + `PRODUCT.md` trước khi đụng UI. Antigravity đọc `AGENTS.md` natively → nó nhận cùng ràng buộc thiết kế như ba tool kia, chỉ là không có lệnh hỗ trợ.

### 9.2 Chống drift của memory nội bộ

Mỗi khi Antigravity nói điều gì mâu thuẫn với `AGENTS.md` / `DESIGN.md`:
1. **`AGENTS.md` thắng, luôn luôn.**
2. Xoá hoặc ghi đè memory sai đó ngay trong phiên.
3. Ghi vào entry WORKLOG, mục **Cảnh báo cho tool sau**.

Đầu mỗi phiên Antigravity, nói thẳng: *"Bỏ qua memory nội bộ nếu mâu thuẫn với AGENTS.md và DESIGN.md trong repo. Đọc lại hai file đó trước."*

### 9.3 Quality gate chung — mọi tool bị soi bằng cùng bộ detector

CLI Impeccable chạy độc lập với provider → dùng được cho **cả Antigravity**. Đây là cách duy nhất để đầu ra UI của cả 4 tool đi qua cùng một bộ luật. Gate Windows gọi binary Impeccable cục bộ trực tiếp, tránh `npx` tự tải lại package.

```powershell
# Windows PowerShell — đường chuẩn trên máy này, không cần WSL.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1
```

```bash
# macOS/Linux/Git Bash có Bash thật.
sh scripts/quality-gate.sh
```

Cài hook để không phụ thuộc trí nhớ — **chạy một lần**, hook được commit nên áp cho mọi tool:

```bash
git config core.hooksPath .githooks
```

Hook `pre-commit` chặn commit khi: (a) detector báo lỗi trên `webapp/frontend`, `slides`, `reports`; hoặc (b) `splits/` bị sửa mà không có `ALLOW_SPLIT_CHANGE=1` (§5.4).

Bỏ qua hook khi thật sự cần — nhưng phải ghi lý do vào WORKLOG:
```bash
git commit --no-verify -m "..."
```

**Giới hạn trung thực:** detector bắt được lỗi *xác định được bằng máy* (tương phản, thang cỡ chữ, spacing tuỳ tiện, a11y cơ bản). Nó **không** bắt được phân cấp thông tin sai hay giọng lạc — đó là việc của `critique`, mà Antigravity không chạy được. Nên: **UI mới thì để Claude Code / Codex / Cursor dựng**, Antigravity nhận việc backend, xử lý dữ liệu, sửa lỗi logic.

---

## 10. Quality gate — nội dung

Scripts: [`../scripts/quality-gate.ps1`](../scripts/quality-gate.ps1) (Windows) và [`../scripts/quality-gate.sh`](../scripts/quality-gate.sh) (Bash thật). Hook: [`../.githooks/pre-commit`](../.githooks/pre-commit).

Gate hiện kiểm:
1. **Impeccable detect** trên `webapp/frontend/`, `slides/`, `reports/` (bỏ qua thư mục chưa tồn tại).
   Đã kiểm chứng 2026-07-24 trên HTML lỗi cố ý: `detect` trả **exit 0 khi sạch, exit 2 khi có finding**, và `--json` in ra mảng phẳng các object `{antipattern, name, description, severity, category, file, line, snippet}`. Gate dựa vào exit code này, hiện **fail trên mọi severity** — cách nới lỏng (chỉ chặn `error`) ghi trong comment của script.
2. **`splits/` bất biến** — chặn nếu bị sửa mà không có `ALLOW_SPLIT_CHANGE=1`.
3. **Không lọt file cấm** — `.nii`, `.nii.gz`, `.dcm`, `.pt`, `.pth` trong vùng staged.

Thêm về sau khi có code: `ruff check`, `pytest -q`, test chống leakage ở mức bệnh nhân.

---

## 11. Bảng tra nhanh

| Tình huống | Làm gì |
|---|---|
| Bắt đầu phiên | `git pull --ff-only` → `git status` → `tail -n 80 WORKLOG.md` |
| Kết thúc phiên | quality gate → viết entry WORKLOG → commit → push → `git status` trắng |
| `git status` bẩn mà không phải việc của mình | Dừng. Ghi WORKLOG. Hỏi người dùng. Không commit đè. |
| Thấy diff lạ trong `.cursor/` `.codex/` `.claude/` | `git checkout -- <path>`. Không gộp tay. |
| Antigravity mâu thuẫn với AGENTS.md | AGENTS.md thắng. Ghi đè memory. Ghi WORKLOG. |
| Sắp dựng UI mới | `/impeccable shape` trước. Nếu đang ở Antigravity → đổi tool. |
| Sắp chốt một deliverable UI | `critique` → `audit` → `polish` → quality gate phù hợp shell (`quality-gate.ps1` trên Windows) |
| Cần đổi `splits/` | Hỏi người dùng. Ghi WORKLOG. `ALLOW_SPLIT_CHANGE=1 git commit ...` |
| Muốn đổi ngữ cảnh dự án | Sửa `AGENTS.md`, không sửa CLAUDE.md hay `.cursor/rules/`. |

---

*Cập nhật lần cuối: 2026-07-24. Thay đổi file này phải kèm một entry trong `WORKLOG.md`.*
