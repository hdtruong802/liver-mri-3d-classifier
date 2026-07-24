# CLAUDE.md

**Ngữ cảnh dự án nằm hoàn toàn ở `AGENTS.md`. File này chỉ nhúng nó vào — KHÔNG chép nội dung sang đây.**

@AGENTS.md

---

## Riêng Claude Code

Những điều dưới đây là cơ chế của Claude Code, không phải nội dung dự án.

**Đầu mỗi phiên, làm đúng thứ tự:**

1. Nội dung `AGENTS.md` đã được nhúng ở trên — đọc nó.
2. Đọc entry cuối của WORKLOG (đừng nhúng cả file vào context, nó chỉ dài thêm):
   ```powershell
   Get-Content WORKLOG.md -Tail 80
   ```
3. `git status` — phải sạch. Nếu bẩn: dừng và hỏi người dùng. Việc dang dở đó có thể là của tool khác.

**Cuối mỗi phiên (bắt buộc, kể cả khi phiên ngắn):** append một entry vào `WORKLOG.md` theo đúng template ở đầu file đó. Chỉ **thêm vào cuối**, không bao giờ sửa hay xoá entry cũ.

**Không sửa các file này** (chúng thuộc về tool khác, xem `docs/MULTI_TOOL_WORKFLOW.md`):
`.cursor/`, `.codex/`, và các file cấu hình do Antigravity sinh ra.

**Khi được yêu cầu "cập nhật ngữ cảnh dự án":** sửa `AGENTS.md`, không sửa file này.
