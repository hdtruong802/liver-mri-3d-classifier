# Prompt: dựng `slides/overview_v2.html` — deck 7 slide báo cáo nội bộ

Deck thứ hai, **song song** với [`slides/overview.html`](../slides/overview.html) (12 bản khắc, giữ nguyên,
không được sửa). Bản v2 hướng tới buổi báo cáo nội bộ 28/07/2026: ngắn hơn, đi từ *nỗi đau* →
*thị trường* → *khoảng trống* → *kỹ thuật* → *lộ trình*.

**Cách dùng:** dán toàn bộ khối dưới đây vào Claude Code, Codex hoặc Cursor.
Antigravity không có `/impeccable` — xem [`docs/MULTI_TOOL_WORKFLOW.md`](../docs/MULTI_TOOL_WORKFLOW.md) §9.

---

```text
/impeccable craft

Dựng một file HTML slide mới: `slides/overview_v2.html`. Deck 7 slide cho buổi báo cáo
nội bộ ngày 28/07/2026. KHÔNG sửa `slides/overview.html` (12 bản khắc hiện có) — v2 là
file thứ hai, tự chứa, sống song song.

═══════════════════════════════════════════════════════════════════════
PHẦN 0 — ĐỌC TRƯỚC KHI VIẾT DÒNG CODE ĐẦU TIÊN
═══════════════════════════════════════════════════════════════════════

Bắt buộc, theo thứ tự. Đừng bỏ qua file nào rồi đoán nội dung:

1. `AGENTS.md` — nguồn sự thật ngữ cảnh dự án, đặc biệt §3 (nguyên tắc bất di bất dịch),
   §5 (mốc đối chiếu ngoài), §7 (ràng buộc Kaggle), §12 (ràng buộc thiết kế UI).
2. `PRODUCT.md` — Users, Product Purpose, Positioning, Evidence on Hand,
   Product Principles, Accessibility. Đây là ràng buộc, không phải gợi ý.
3. `DESIGN.md` — hệ thống thị giác "The Anatomical Plate". Đọc kỹ mục Named Rules.
4. `docs/MRI_Classification_Spec_Sheet.md` — chốt kỹ thuật: dataset, model, metric, ngưỡng.
5. `docs/liver_mri_3d_classification_plan.md` — kế hoạch 6 tuần, sprint, kill-switch,
   §6 (chi tiết kỹ thuật Kaggle), §8 (triển khai web app).
6. `docs/industry_landscape.md` — khảo sát thị trường đã làm sẵn, 19 nguồn có link.
   Đây là xương sống của Slide 3. KHÔNG khảo sát lại từ đầu; hãy dùng lại và bổ sung.
7. `slides/README.md` + `slides/assets/ATTRIBUTION.md` — hệ trích nguồn và asset đã có.
8. `Get-Content WORKLOG.md -Tail 120` — biết phiên trước dừng ở đâu.
9. `slides/overview.html` — đọc để **tái dùng** CSS inline, JS điều hướng, và cấu trúc
   markup (`.deck`, `.slide`, `.top`, `.section-nav`, `.body`, `.foot`, `.refs`,
   `.table-wrap`, `.chip`, `.image-frame`). Không dựng lại hệ thống từ số không.

Lưu ý trạng thái repo: `git status` hiện KHÔNG sạch (deck v1 và `docs/industry_landscape.md`
đang chờ commit — xem WORKLOG S-050→S-053). Đó là việc đã biết, không phải rác. Đừng
stage/commit/xoá `notebooks/notebookf104ced082.ipynb`.

═══════════════════════════════════════════════════════════════════════
PHẦN 1 — LUẬT VỀ SỐ LIỆU (đọc kỹ, đây là chỗ dễ hỏng nhất)
═══════════════════════════════════════════════════════════════════════

Dự án CHƯA CÓ dữ liệu, CHƯA CÓ model, CHƯA CÓ một con số kết quả nào.

**The Two-Number Rule (DESIGN.md):** hệ thống chỉ có hai loại số.

  • LOẠI A — số đã công bố của người khác. Được phép hiển thị. BẮT BUỘC kèm:
    (a) chú số trên (superscript) dẫn về chú giải, (b) link tới nguồn gốc,
    (c) cỡ mẫu `n=` khi nguồn có nêu, (d) một câu nói rõ đây là số của ai, đo trên tập nào.

  • LOẠI B — số kết quả của dự án này. **KHÔNG TỒN TẠI, và không bao giờ được vẽ ra.**
    Không placeholder trông giống thật. Không "ví dụ minh hoạ 0,82". Không biểu đồ có
    trục số của model chưa train. Vi phạm điều này là lỗi nghiêm trọng nhất có thể mắc:
    người review sẽ tưởng đó là kết quả.

  • LOẠI C — **số mục tiêu / kỳ vọng** (Slide 6 yêu cầu). Đây là loại mới, chưa có trong
    DESIGN.md, nên phải xử lý cực kỳ rõ ràng, theo đúng ba điều kiện sau, cả ba:
    (a) đặt trong khối có **viền nét đứt** — nét đứt là ngôn ngữ dành riêng cho
        "chưa có dữ liệu" trong hệ thống này;
    (b) có chip chữ ghi rõ **"Mục tiêu, chưa có kết quả"** ngay trong khối, không phải
        ở chú thích chân trang;
    (c) mỗi con số mục tiêu phải **neo vào một số Loại A có nguồn** — ví dụ "macro-F1
        mục tiêu ≥ 0,6083 vì đó là baseline official của challenge[n]", chứ không phải
        một con số rơi từ trên trời.
    Nếu không neo được vào nguồn nào thì đừng viết số — viết tiêu chí định tính
    ("vượt baseline có ý nghĩa thống kê", "ECE giảm sau temperature scaling").

**The Plate Key Rule:** Hoàng Thổ (`--amber`) chỉ dùng ở đúng 3 chỗ — chú số/chú giải
nguồn, đường nhấn dưới tiêu đề, mốc phần đang hoạt động. Không có chỗ thứ tư.

**The Never-Colour-Alone Rule:** không thông tin nào chỉ mã hoá bằng màu. Ác/lành,
`defer`, đã-xác-minh/chưa-xác-minh — luôn kèm nhãn chữ, hoặc kiểu nét (liền/đứt),
hoặc hình dạng (đặc/rỗng). Bài kiểm tra: in đen trắng mà vẫn đọc được.

**The Restraint Rule:** Hoàng Thổ + Lam Ngọc là toàn bộ ngân sách màu. Không sắc thứ ba.

**The Assertion Rule:** mỗi `<h2>` phải là một mệnh đề có thể đúng hoặc sai
("Thị trường giỏi phát hiện, né phân loại"), không phải một nhãn ("Tổng quan thị trường").

**The No-Uppercase Rule:** `text-transform: uppercase` bị cấm tuyệt đối — dấu tiếng Việt
trên chữ hoa bị chèn ép và mất khi chiếu.

**The Tabular Rule:** mọi số dùng `font-variant-numeric: tabular-nums`, canh dấu thập phân.

**The No-Shadow Rule:** không `box-shadow` ở bất kỳ đâu.

═══════════════════════════════════════════════════════════════════════
PHẦN 2 — NGHIÊN CỨU: TÌM GÌ, Ở ĐÂU, VÀ CẤM GÌ
═══════════════════════════════════════════════════════════════════════

Được phép và được YÊU CẦU dùng WebSearch/WebFetch. Đây là điểm khác lớn nhất so với deck v1.

**Thứ tự ưu tiên nguồn (cao → thấp), không được đảo:**
  1. Paper gốc peer-reviewed có DOI (PubMed / RSNA / Springer / ScienceDirect / arXiv có bản đăng)
  2. Cơ quan quản lý: FDA 510(k) database, EU MDR/CE, WHO
  3. Hiệp hội chuyên ngành: RSNA, ACR, ESR, ISMRM; báo cáo workforce chính thức
  4. Trang challenge/benchmark chính thức, repo GitHub chính chủ
  5. Thông cáo báo chí của công ty (chỉ để xác nhận trạng thái sản phẩm, KHÔNG lấy số hiệu năng)

**CẤM tuyệt đối làm nguồn:** blog cá nhân, bài tổng hợp SEO, nội dung do AI khác sinh,
Wikipedia (được dùng để tìm đường tới nguồn gốc, không được trích thẳng), quảng cáo
sản phẩm, số liệu không truy được về một tài liệu gốc cụ thể.

**Kỷ luật khi trích:**
  - Mỗi số phải ghi được: ai đo, đo trên bao nhiêu ca (`n=`), năm nào, ở đâu.
  - Nếu là số của một quốc gia/hệ thống y tế cụ thể, phải ghi rõ quốc gia — đừng để
    người xem tưởng đó là số Việt Nam.
  - Trạng thái regulatory (FDA/CE) thay đổi theo thời gian: `docs/industry_landscape.md`
    chốt ở mốc 7/2026. **Verify lại từng sản phẩm trước khi đưa lên slide.**
  - Không tìm được nguồn đủ tin cậy cho một luận điểm → **bỏ con số đó đi**, giữ luận
    điểm ở dạng định tính, hoặc thay bằng sơ đồ khái niệm không có trục số. Thà thiếu
    một con số còn hơn có một con số không truy được.

**Cần tìm gì, theo từng slide:**

  Slide 2 (nỗi đau) — ưu tiên tìm:
    · Tăng trưởng khối lượng ảnh y tế / số ca chụp trên mỗi radiologist theo năm
      (nguồn: RSNA/ACR/JACR workforce studies, hoặc nghiên cứu về "radiologist workload").
    · Tỷ lệ sai sót / bỏ sót trong chẩn đoán hình ảnh — có văn liệu kinh điển về
      retrospective error rate và day-to-day discrepancy rate; tìm bản gốc, không lấy
      con số truyền miệng.
    · Ảnh hưởng của mệt mỏi / cuối ca trực lên độ chính xác đọc phim.
    · Thời gian đọc một ca MRI gan đa thì (nếu có nghiên cứu đo thật). Nếu KHÔNG tìm
      được số đáng tin → **không vẽ biểu đồ thời gian**; thay bằng sơ đồ định tính
      (các bước bác sĩ phải làm khi so 8 thì) — vẫn truyền được nỗi đau mà không bịa số.
    · Bối cảnh Việt Nam nếu có nguồn chính thức (Bộ Y tế, tạp chí y học trong nước).
      Không có thì nói thẳng là số quốc tế, đừng ngoại suy.

  Slide 3 (thị trường) — nền đã có sẵn ở `docs/industry_landscape.md` §2–§7 và 19 nguồn.
    Việc cần làm: chọn lọc xuống mức trình chiếu được, verify lại trạng thái FDA/CE,
    và bổ sung nếu tìm được sản phẩm/nghiên cứu mới hơn 7/2026.

  Slide 4 (SOTA + khoảng trống) — nền đã có ở `AGENTS.md` §5 và deck v1 slide 6.
    Bổ sung: các công trình phân loại tổn thương gan trên MRI đa pha mới nhất, và
    **bằng chứng cho khoảng trống**: có bao nhiêu công trình báo cáo ECE / reliability
    diagram / risk–coverage? Nếu tìm được một review nói thẳng "calibration hiếm khi
    được báo cáo trong medical imaging DL" thì đó là trích dẫn vàng cho slide này.

  Slide 6 (metric) — định nghĩa metric lấy từ Spec Sheet §4, không cần tìm ngoài.
    Cần tìm: mốc tham chiếu để **neo** số mục tiêu (baseline official 0,6083; đội nhất
    0,8322; Hu 2025 F1 0,84 — tất cả đã có nguồn trong repo).

  Slide 7 (hạ tầng) — ước tính VRAM/GPU phải **suy ra từ giả định ghi rõ trên slide**
    (số pha × kích thước patch × batch × precision), không phải một con số khẳng định.
    Thông số GPU (VRAM của T4/P100/A100/H100) lấy từ trang chính thức NVIDIA.
    Ràng buộc Kaggle (session ≤12h, ~30h GPU/tuần, VRAM ~16GB) lấy từ `AGENTS.md` §7
    và `docs/liver_mri_3d_classification_plan.md` §6.

═══════════════════════════════════════════════════════════════════════
PHẦN 3 — NỘI DUNG 7 SLIDE
═══════════════════════════════════════════════════════════════════════

Người xem: hội đồng nội bộ VSF, có nền kỹ thuật nhưng KHÔNG chuyên ảnh y tế. Xem trên
máy chiếu, có người trình bày nói kèm. Slide là chỗ dựa cho lời nói, không phải văn bản
để đọc. Mỗi slide: một luận điểm, tối đa ~40 từ văn xuôi, phần còn lại là cấu trúc thị giác.

────────────────────────────────────────────────────────────
SLIDE 1 — Bìa
────────────────────────────────────────────────────────────
  Tiêu đề: "Ứng dụng AI trong phân loại bất thường gan trực tiếp trên MRI 3D đa thì"
  Người nghiên cứu: Hoàng Đức Trường
  Người hướng dẫn: Nguyễn Hoàng Bảo Lam
  Khối: VSF-KD&VHVMEC-DL&AI
  Ngày báo cáo: 28/07/2026
  Dải RUO bắt buộc ngay từ slide bìa.
  Không logo (dự án không có brand identity — xem PRODUCT.md § Brand Commitments).
  KHÔNG dùng logo Vinmec/VinGroup và không đặt bất cứ dòng nào ngụ ý deck này được
  một tổ chức nào phê duyệt.

────────────────────────────────────────────────────────────
SLIDE 2 — Đặt vấn đề và chốt scope
────────────────────────────────────────────────────────────
  Ba ý, theo thứ tự leo thang:
  (a) Khối lượng ảnh tăng nhanh hơn số người đọc được nó [số Loại A, có nguồn].
  (b) Đọc sai và bỏ sót là chuyện có thật, và mệt mỏi làm nó tệ hơn [số Loại A].
  (c) MRI gan đa thì đặc biệt nặng: bác sĩ phải so **8 thì** của cùng một tổn thương,
      theo dõi động học ngấm thuốc (arterial hyperenhancement, washout — ngôn ngữ LI-RADS).
      Ảnh minh hoạ đã có sẵn: `assets/synthetic-mri-8phase-contact-sheet.png`
      (ảnh tổng hợp, KHÔNG phải ca bệnh — phải ghi rõ trong figcaption).

  Chốt bài toán, viết thành một câu duy nhất, đóng khung:
  **Phân loại 7 lớp tổn thương gan ở mức ROI, trực tiếp trên volume 3D đa pha 8 thì MRI.**
  3 ác: HCC, ICC, di căn · 4 lành: nang, u máu, FNH, áp-xe.
  Phân biệt ác/lành bằng ô đặc/rỗng + nhãn chữ, không bằng màu.

  Scope — nói thẳng cả cái KHÔNG làm, vì đó là điều hội đồng sẽ hỏi:
    trong scope: phân loại đa lớp · calibration · selective prediction (`defer`) ·
                 Grad-CAM 3D · web app demo tự code
    ngoài scope: segmentation · triển khai lâm sàng · dữ liệu bệnh nhân thật ·
                 đua accuracy leaderboard

────────────────────────────────────────────────────────────
SLIDE 3 — Thị trường và rào cản áp dụng
────────────────────────────────────────────────────────────
  Nguồn nội dung: `docs/industry_landscape.md`. Nén xuống còn 4 khối:

  (a) **Có gì trên thị trường** — bản đồ theo loại tác vụ, không phải danh sách công ty:
      detection/triage (chín) · segmentation & định lượng (chín) · LI-RADS scoring
      (prototype) · phân loại đa lớp (gần như chỉ nghiên cứu) ·
      trustworthiness (chưa thành sản phẩm).
      Mỗi hàng: trạng thái + 1 ví dụ đại diện + output điển hình.
  (b) **Kết quả họ đạt được** — chọn 2–3 số mạnh nhất, có nguồn, ghi rõ đo trên tập nào.
  (c) **Rào cản** — chọn 4 trong 6 rào cản ở §6 của tài liệu: regulatory bar cao hơn cho
      kết luận chẩn đoán · MRI đa pha khó chuẩn hoá hơn CT · trust & liability ·
      dữ liệu và lớp hiếm · dataset shift · workflow/chi trả.
  (d) **Khoảng trống** — một câu, đặt nổi bật:
      thị trường trả lời "cái gì / bao nhiêu", chưa trả lời "đáng tin đến đâu / khi nào nên dừng".

  Mọi trạng thái FDA/CE phải verify lại và ghi mốc thời gian kiểm tra ngay trên slide.

────────────────────────────────────────────────────────────
SLIDE 4 — SOTA nghiên cứu và khoảng trống nghiên cứu
────────────────────────────────────────────────────────────
  (a) Bảng leaderboard LLD-MMRI Challenge 2023 (test 104 ca) — số Loại A, đã có trong
      deck v1 slide 6: đội nhất 0,8322 / 0,7801 · baseline official (UniFormer-S 3D,
      from scratch, 300 epoch) 0,6083 / 0,5414. Ghi rõ `n=104`.
      Hàng dẫn đầu nhấn bằng **độ sáng nét**, không phải bằng màu hoàng thổ.
  (b) Một hoặc hai công trình phân loại tiêu biểu ngoài challenge (Hu et al. 2025:
      7 lớp, patient-acc 0,93, F1 0,84 — nhưng ghi rõ đo trên tập test của chính họ,
      **không so trực tiếp được** với test-104).
  (c) **Khoảng trống, là trọng tâm slide này:** các công trình trên báo accuracy / F1 /
      AUC rồi dừng. Chúng không trả lời: khi model nói 80%, có đúng 80% ca là ác không?
      Và khi nào model nên im lặng nhường bác sĩ? → calibration + selective prediction.
      Nếu tìm được review học thuật nói thẳng điều này, trích nó — đó là bằng chứng
      mạnh hơn lời khẳng định của chính mình.
  (d) Định vị dự án: **không đua accuracy**. Thắng bằng rigor thống kê + calibration +
      selective prediction + external/OOD + reproducibility.

────────────────────────────────────────────────────────────
SLIDE 5 — Dữ liệu và huấn luyện
────────────────────────────────────────────────────────────
  Nguồn: Spec Sheet §2 và §3. Đừng bịa thêm.
  (a) **Dataset chính: LLD-MMRI** — 498 bệnh nhân, 1 tổn thương/bn, 8 thì MRI
      (C-pre, C+A, C+V, C+Delay, T2WI, DWI, In Phase, Out Phase), 7 lớp.
      Nhãn = pathology report, duyệt bởi 2 bác sĩ 6–8 năm + 1 senior >10 năm.
      License CC BY-NC-ND. Split official 316/78/104 đã tái lập và khoá trong `splits/`.
      **Test-104 là held-out khoá kín, chạm đúng một lần.**
  (b) **Phân bố lớp thật** (tổng 498): HCC 157 · u máu 79 · ICC 58 · áp-xe 54 · nang 53 ·
      di căn 51 · FNH 46. Tỷ lệ HCC:FNH ≈ 3,4:1 — mất cân bằng vừa phải, **không long-tail**.
      Đây là số Loại A (từ PDF challenge p.10) → cần chú số.
  (c) **Tiền xử lý:** N4 bias field correction → resample ~1,5×1,5×3,0 mm → rigid
      registration từng thì về pha portal-venous → ROI-crop 96×96×48 quanh lesion →
      per-sequence z-score / percentile clip.
      Nói rõ **vì sao registration là bắt buộc**: các thì khác geometry (non-contrast chụp
      coronal, DWI matrix thô 132×116, T1 spacing 2mm vs T2 1mm), đa máy 1,5T/3T
      nhiều hãng → domain shift ngay trong nội bộ dataset.
      MRI không có đơn vị chuẩn như HU của CT → bắt buộc chuẩn hoá theo từng chuỗi.
  (d) **Augmentation & xử lý mất cân bằng:** transform 3D của MONAI; class-balanced loss
      (effective number) hoặc Focal + WeightedSampler; head phân cấp (ác/lành → 7 lớp).
  (e) **Chống leakage** — nêu như một cam kết, không phải chi tiết kỹ thuật:
      split ở mức bệnh nhân tuyệt đối, có unit test kiểm giao tập bệnh nhân = rỗng;
      thống kê normalization chỉ tính trên train; threshold và temperature khoá trên
      validation, áp mù lên test.
  (f) **Model:** baseline DenseNet121-3D (MONAI) → main: 3D CNN + multi-phase fusion
      (early concat → per-phase encoder + phase-attention → tách nhóm structural/dynamic).
      Ghi chú trung thực: UniFormer-S 3D (conv + self-attention) là baseline official của
      challenge và train from scratch được trên chính dataset này — dữ liệu ít KHÔNG
      tự động loại transformer. DenseNet được chọn làm baseline vì đã chạy được và
      MONAI hỗ trợ sẵn, không phải vì transformer bị cấm.

────────────────────────────────────────────────────────────
SLIDE 6 — Metric đánh giá và mức kỳ vọng
────────────────────────────────────────────────────────────
  ĐÂY LÀ SLIDE RỦI RO NHẤT. Đọc lại PHẦN 1 § LOẠI C trước khi viết.

  Chia 4 nhóm, mỗi nhóm 1 dòng giải thích bằng tiếng Việt đời thường:
  (a) **Chính:** macro-F1 (trung bình F1 đều trên 7 lớp → lớp hiếm có trọng số ngang lớp
      phổ biến) · Cohen's κ (đồng thuận sau khi trừ phần trùng do may rủi).
      Hai metric này khớp đúng metric xếp hạng của challenge → so sánh trực tiếp được.
  (b) **Calibration (headline):** ECE · Brier · reliability diagram · temperature scaling.
      Giải thích một câu: nếu model báo 80% thì trong 100 ca như vậy phải có khoảng 80 ca đúng.
  (c) **Selective prediction (headline):** risk–coverage curve · AURC ·
      accuracy@coverage. Giải thích: model được phép từ chối; đo xem nó tự xử được
      bao nhiêu phần ca mà vẫn giữ sai số dưới ngưỡng.
  (d) **Thống kê:** mọi số kèm 95% CI bootstrap ở mức bệnh nhân (≥2000 lần) ·
      DeLong · McNemar · Holm correction. Không bao giờ báo best-of-many-seeds.

  **Khối kỳ vọng** — viền nét đứt, chip "Mục tiêu, chưa có kết quả", và mỗi mục tiêu
  neo vào một số có nguồn. Gợi ý cách diễn đạt an toàn:
    · macro-F1: mục tiêu vượt baseline official 0,6083[n] một cách có ý nghĩa thống kê.
      Vùng tham chiếu của các đội dự thi: 0,50–0,83[n].
    · calibration: ECE sau temperature scaling thấp hơn trước, có ý nghĩa thống kê.
      Không đặt một ngưỡng ECE tuyệt đối — chưa có cơ sở nào để đặt.
    · selective prediction: báo được đường risk–coverage đầy đủ và AURC.
      Nêu dạng câu hỏi vận hành ("model tự quyết được bao nhiêu ca trong khi giữ sai số
      dưới X%"), KHÔNG điền sẵn X và câu trả lời.
    · an toàn lâm sàng: ưu tiên sensitivity trên bài gộp ác/lành (đừng bỏ sót ung thư).
  Nếu thấy một mục tiêu nào không neo được vào nguồn → chuyển sang phát biểu định tính.

  Nếu vẽ minh hoạ reliability diagram hoặc risk–coverage: **sơ đồ khái niệm, không có
  trục số**, nhãn "Minh hoạ khái niệm: chưa có dữ liệu", viền nét đứt. Đường chéo hoàn
  hảo được vẽ vì nó là định nghĩa toán học, không phải kết quả đo.

────────────────────────────────────────────────────────────
SLIDE 7 — Lộ trình và hạ tầng
────────────────────────────────────────────────────────────
  Ba khối rõ ràng, đừng trộn vào nhau:

  (a) **6 tuần nghiên cứu độc lập, dữ liệu public.**
      Input: 8 file `.nii` của cùng một bệnh nhân (volume 3D đa pha), từ LLD-MMRI.
      Output: lớp dự đoán · xác suất từng lớp (đã calibration) · xác suất ác tính ·
              mức bất định (entropy, ensemble std) · cờ `defer` · heatmap Grad-CAM 3D.
      Deliverable: code train/eval chạy trên Kaggle · web app demo FastAPI + frontend
      tự code (không Streamlit, không Gradio) · slide + report có CI và limitations ·
      reproducibility pack.
      Timeline 3 sprint × 2 tuần (Spec Sheet §5): S1 data/tiền xử lý/baseline →
      S2 fusion + trustworthiness + thống kê + test-104 một lần → S3 web app + báo cáo.
      Nêu kill-switch như một điểm mạnh về kỷ luật, không phải điểm yếu:
      chưa có quyền data → CT fallback · 3D thua 2.5D → 2.5D primary · hụt giờ GPU →
      ensemble K=5 giảm K=3 · deep ensemble hụt giờ → MC-dropout.

  (b) **Sau 6 tuần: đường đi tới môi trường thật (làm việc với Vinmec).**
      Trình bày như **đề xuất có điều kiện**, không phải kế hoạch đã được duyệt.
      Input cần có: DICOM series đa pha từ PACS bệnh viện, kèm nhãn pathology report;
      phải qua các bước không thể bỏ: phê duyệt IRB/hội đồng đạo đức · thoả thuận
      chia sẻ dữ liệu · khử định danh (de-identification) · ánh xạ protocol MRI của
      viện sang 8 thì của taxonomy hiện tại.
      Output: kết quả trả về workstation/PACS dưới dạng structured report, kèm xác suất
      đã calibration và cờ `defer`; luôn là hỗ trợ quyết định, không tự kết luận.
      Ghi thẳng khoảng cách còn lại: cần external validation đa trung tâm · cần đo
      calibration dưới domain shift · chưa có gì nói về con đường regulatory.
      **Không viết bất cứ câu nào ngụ ý đã được Vinmec phê duyệt, đã ký kết, hay đã
      có quyền truy cập dữ liệu bệnh viện.** RUO vẫn hiển thị trên slide này.

  (c) **Hạ tầng huấn luyện — ước tính, ghi rõ giả định.**
      Giai đoạn nghiên cứu (thực tế đang dùng): Kaggle Notebook, GPU ~16GB VRAM,
      session ≤12h, ~30h GPU/tuần → bắt buộc checkpoint + resume mỗi epoch, AMP,
      batch 2–4 + gradient accumulation, gradient checkpointing, cache tiền xử lý
      thành Kaggle Dataset có version.
      Nếu trình bày một bảng ước tính VRAM: phải ghi công thức/giả định ngay cạnh
      (số pha × H×W×D × batch × precision × hệ số activation), gọi đúng tên là **ước tính**,
      và đặt trong khối nét đứt. Đừng trình bày như số đo được.
      Giai đoạn mở rộng (nếu scale lên dữ liệu viện): nêu điều kiện kích hoạt
      (kích thước dataset, số fold × số seed, arm full-volume) rồi mới nói tới lớp GPU
      cần thiết — thông số VRAM lấy từ trang chính thức NVIDIA, có link.
      Nhắc: nút thắt lúc **serve** là registration/tiền xử lý, không phải forward pass.

═══════════════════════════════════════════════════════════════════════
PHẦN 4 — RÀNG BUỘC KỸ THUẬT CỦA FILE
═══════════════════════════════════════════════════════════════════════

  · Một file HTML tự chứa: CSS và JS **inline**, không CDN, không webfont, mở được
    ngoại tuyến bằng double-click. Hyperlink tới nguồn thì cần mạng khi bấm, nhưng
    file phải hiển thị đầy đủ khi offline.
  · `lang="vi"`. Toàn bộ nội dung tiếng Việt.
  · **Thuật ngữ giữ nguyên tiếng Anh, không dịch, không viết tắt riêng:**
    `defer`, `coverage`, `calibration`, `ECE`, `Brier`, `macro-F1`, `AUROC`, `AURC`,
    `OOD`, `HCC`, `ICC`, `FNH`, `LI-RADS`.
  · Khung 16:9, `.deck` co theo viewport như `overview.html`. In ra PDF được, mỗi
    slide một trang ngang, URL hiện trong ngoặc (tái dùng `@media print` của v1).
  · Điều hướng: mũi tên trái/phải, Space, PageUp/PageDown, Home/End; nút Trước/Sau;
    đồng bộ `location.hash`. Tái dùng nguyên khối JS của `overview.html`.
  · `.section-nav`: 5 mốc phần của v1 không còn khớp deck 7 slide — thiết kế lại mốc
    phần cho đúng mạch mới (gợi ý: Vấn đề · Bối cảnh · Kỹ thuật · Lộ trình), hoặc bỏ
    hẳn nếu 7 slide đã đủ ngắn để không cần định vị. Đừng để mốc phần sai.
  · Chỉ số slide: `01 / 07` … `07 / 07`.
  · Dải RUO "Research Use Only, chưa kiểm định lâm sàng" trên **7/7** slide, ở vị trí
    không thể bỏ sót.
  · **Chú giải nguồn:** deck chỉ có 7 slide nên không có slide nguồn riêng. Mỗi slide
    mang chú giải rút gọn có link ở `.foot`. Ngoài ra thêm **một slide phụ lục** đặt
    sau slide 7, đánh dấu là "Phụ lục — Nguồn" (KHÔNG đánh số vào 7), chứa danh sách
    đầy đủ theo mẫu `ul.refs` của v1.
  · Biểu đồ: chỉ vẽ khi thật sự cần. Nếu vẽ thì **inline SVG hoặc CSS thuần**, không
    thư viện chart. Tuân thủ ngân sách 2 màu và Never-Colour-Alone (mỗi series phải
    có nhãn chữ trực tiếp, không chỉ dựa vào legend màu).
  · Tương phản tối thiểu WCAG AA; đọc được từ cuối phòng họp trên máy chiếu nhạt màu.
  · Tôn trọng `prefers-reduced-motion`. Motion chỉ để giải thích chuyển trạng thái.
  · `aria-label` cho mọi sơ đồ, mô tả nội dung sơ đồ bằng lời — không chỉ ghi "sơ đồ".

  **Asset:** dùng lại ảnh đã có trong `slides/assets/`. Nếu thêm ảnh mới → bắt buộc
  cập nhật `slides/assets/ATTRIBUTION.md` trong cùng lần sửa.
  Lưu ý đã biết: `ui-output-screen.png` **chứa số phần trăm giả** — nếu dùng lại thì
  bắt buộc có figcaption nói rõ là minh hoạ bố cục, không phải kết quả. Tốt hơn: không
  dùng nó trong deck v2, vì deck này ngắn và không có slide output UI riêng.

═══════════════════════════════════════════════════════════════════════
PHẦN 5 — QUY TRÌNH VÀ NGHIỆM THU
═══════════════════════════════════════════════════════════════════════

Thứ tự làm việc:
  1. Đọc hết PHẦN 0. Đừng viết code trước khi đọc.
  2. Nghiên cứu web theo PHẦN 2. Ghi lại từng nguồn tìm được: URL, ngày truy cập,
     con số lấy ra, cỡ mẫu. Nguồn nào không đạt chuẩn PHẦN 2 → loại, đừng dùng tạm.
  3. **Báo cáo lại danh sách nguồn + số định dùng cho mỗi slide TRƯỚC KHI dựng HTML.**
     Nếu có con số nào không neo được vào nguồn, nói ra ở bước này thay vì âm thầm bịa.
  4. Dựng `slides/overview_v2.html`.
  5. Chạy quality gate:
     `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-gate.ps1`
  6. Cập nhật `slides/README.md` (thêm dòng cho `overview_v2.html`, ghi rõ nó khác v1
     ở đâu và dùng cho buổi nào) và `slides/assets/ATTRIBUTION.md` nếu có asset mới.
  7. Append một entry vào `WORKLOG.md` theo template ở đầu file đó. Chỉ thêm vào cuối.

Checklist nghiệm thu — tự kiểm từng dòng trước khi báo xong:
  [ ] 7 slide + 1 phụ lục nguồn; chỉ số 01/07 … 07/07 đúng thứ tự
  [ ] RUO trên 7/7 slide
  [ ] **Không một con số kết quả nào của dự án này** xuất hiện ở bất kỳ đâu
  [ ] Mọi số Loại A có chú số + link + ghi rõ của ai, đo trên tập nào, `n=` nếu có
  [ ] Mọi số Loại C (mục tiêu) nằm trong khối nét đứt + chip "Mục tiêu, chưa có kết quả"
      + neo vào một số Loại A có nguồn
  [ ] Trạng thái FDA/CE đã verify lại, có ghi mốc thời gian kiểm tra
  [ ] Không có câu nào ngụ ý Vinmec đã phê duyệt / đã cấp dữ liệu / đã kiểm định
  [ ] In đen trắng vẫn đọc được toàn bộ thông tin (Never-Colour-Alone)
  [ ] Không `text-transform: uppercase`, không `box-shadow`, không màu thứ ba
  [ ] Mọi `<h2>` là một mệnh đề, không phải một nhãn
  [ ] Mở offline được; không CDN, không webfont
  [ ] Điều hướng phím + nút hoạt động; in PDF ra 8 trang ngang
  [ ] Quality gate PASS
  [ ] `slides/overview.html` KHÔNG bị sửa (`git diff --stat` để xác nhận)
  [ ] WORKLOG đã append

Nếu gặp mâu thuẫn giữa prompt này và `AGENTS.md` / `DESIGN.md` / `PRODUCT.md`:
**các file trong repo thắng.** Nêu mâu thuẫn ra và ghi vào WORKLOG mục "Quyết định".
```
