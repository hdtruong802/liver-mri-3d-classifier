# Liver MRI 3D Classification - Core Spec Sheet (Chốt kỹ thuật)

> **Research Use Only (RUO)**, chưa kiểm định lâm sàng.
> Bản tóm tắt kỹ thuật:  Phân loại đa lớp u gan trực tiếp trên MRI 3D đa pha. 1 thành viên, 6 tuần, Kaggle, MONAI/PyTorch.

## 1. Problem Scope

- **Bài toán:** phân loại **7 lớp loại tổn thương** gan (lành/ác) mức ROI trên **LLD-MMRI**, làm **trực tiếp trên volume 3D đa pha** (không hạ 2D lát cắt, trừ nhánh ablation).
- **Đóng góp headline (research question, không chỉ task):** **Trustworthiness**, tức model đưa xác suất *đáng tin* (calibrated) và biết **từ chối khi không chắc** (selective prediction) để chuyển bác sĩ. Đây là chỗ SOTA bỏ trống (họ chỉ báo accuracy/F1/AUC).
- **Câu hỏi phụ trợ:**
  > - **Fusion đa pha:** pha nào (trong 8 thì) mang tín hiệu phân biệt lớp, cơ chế hợp nhất nào khai thác tốt nhất động học ngấm thuốc (arterial hyperenhancement, washout theo LI-RADS).
  > - **3D vs 2.5D:** với n≈500 và crop nhỏ, 3D full-volume thắng 2.5D ở đâu, pretrained 3D backbone thu hẹp khoảng cách bao nhiêu.
- **Định vị SOTA:** SOTA trên LLD-MMRI đã bão hòa quanh 85% acc / 85% macro-F1 / 97% macro-AUC (test 104 ca). **Không đua accuracy leaderboard** (test nhỏ, phương sai cao); thắng bằng **rigor thống kê + calibration + selective prediction + external + reproducibility**.
- **Modality:** MRI. CT chỉ là phương án thay thế nếu hết Tuần 1 không xin được quyền truy cập LLD-MMRI. **Không** làm segmentation.

## 2. Dataset Strategy

- **Chính, LLD-MMRI:** 498 bn (1 tổn thương/bn), **8 thì MRI** (pre / arterial / venous / delay / T2WI / DWI / T1 in-phase / T1 out-phase), **7 lớp** (HCC, ICC, di căn, nang, u máu, FNH, áp-xe: 3 ác, 4 lành), có **bbox + patch cắt sẵn + full-volume**. Nhãn = **pathology report** (gold standard: 2 bs 6/8 năm + 1 senior >10 năm duyệt). **License CC BY-NC-ND** (không phát tán bản phái sinh công khai). *Bản thực nhận (`wanglab/LLD-MMRI-MedSAM2`) chỉ có full-volume + annotation, không kèm patch cắt sẵn/split — xem `docs/W2_plan.md §0`.*
- **Split & đánh giá:**
  > - **5-fold stratified patient-level CV** trên 394 train+val để chọn model. **Test-104 official** = held-out **khóa kín, chạm 1 lần**, không dùng để chọn model hay threshold.
  > - **Split official 316/78/104 — ĐÃ TÁI LẬP (2026-07-24, WORKLOG S-021):** bản thực nhận (`wanglab/LLD-MMRI-MedSAM2`) không kèm file split, nhưng lấy `labels_trainval.txt` (394 train+val) từ repo đội thi [ZHEGG/miccai2023](https://github.com/ZHEGG/miccai2023) → test-104 = 498 − 394; **verify phân bố lớp khớp PDF official 100%** (7/7 lớp). Lưu 12 file ở `splits/` (bất biến); 5-fold CV dùng official fold. **So benchmark trực tiếp với SOTA được.** *(Đảo quyết định S-019 "tự chia".)* Chi tiết: `splits/README.md`, `docs/W2_plan.md §0`. Bản thực nhận chỉ có full-volume, không patch cắt sẵn, kèm mask MedSAM2 (không dùng).
- **External validation (nhãn thô + OOD):**
  > - **Nhãn thô:** gộp về **ác/lành** (hoặc HCC vs non-HCC) rồi lấy tập external từ nguồn public thứ 2 (cohort HCC MRI / TCIA). Cho một con số external thật trên task coarse có ý nghĩa lâm sàng, vì không có bộ MRI đa pha public nào cùng taxonomy 7 lớp.
  > - **OOD/domain-shift:** **Duke Liver Dataset** (2146 series/105 bn, có liver mask + series-label, không có nhãn loại tổn thương) làm probe robustness + OOD detection.
- **Mất cân bằng lớp (HCC áp đảo, imbalance vừa phải):** phân bố thật (tổng 498, PDF challenge p.10) — HCC 157 · u máu 79 · ICC 58 · áp-xe 54 · nang 53 · di căn 51 · FNH 46 (HCC:FNH ≈ 3.4:1, **không long-tail**). Xử lý: class-balanced loss (effective number) hoặc Focal + WeightedSampler, augmentation mạnh, **head phân cấp** (ác/lành → 7 lớp), báo cáo song song **taxonomy gộp** 3 đến 4 super-class để có số ổn định thống kê.
- **Preprocessing (chạy 1 lần rồi cache thành Kaggle Dataset):** N4 bias field correction → resample ~1.5 x 1.5 x 3.0 mm → **rigid registration** từng thì về pha portal-venous trong ROI gan (SimpleITK/ANTs), resample DWI/T2 về grid tham chiếu → ROI-crop 96x96x48 quanh lesion → **per-sequence z-score / percentile clip** (MRI không có đơn vị chuẩn như HU của CT). **Registration là bắt buộc, không tuỳ chọn (PDF p.9-10):** các thì khác geometry — non-contrast chụp **coronal**, DWI matrix 132×116 (thô), T1 spacing 2mm vs T2 1mm; đa máy 1.5T/3T (Kangda/GE/Philips) → domain shift nội bộ.
- **Chống leakage (bắt buộc):** split **mức bệnh nhân** tuyệt đối + unit test giao tập bệnh nhân bằng rỗng; thống kê normalization/registration chỉ tính trên train; không để bbox rò rỉ kích thước; CI tính ở mức bệnh nhân.

## 3. Model Selection

> **SOTA có kiểm soát:** n≈500 khiến 3D transformer lớn dễ **overfit**. Chọn backbone 3D *vừa phải* + **pretrain y tế mạnh** + **fusion tốt** hơn là đổi backbone hào nhoáng.

- **Baseline (sàn):** **DenseNet121-3D** (MONAI), mốc tham chiếu để đo lợi ích của fusion/pretrain.
- **Main model (chính):** 3D CNN + **multi-phase fusion**; heatmap độ nhạy chỉ là kiểm tra định tính offline, không phải đóng góp chính.
  > - **Backbone:** MedicalNet ResNet-3D (pretrain 23 bộ y tế) hoặc Models Genesis, transfer mạnh trên dữ liệu nhỏ.
  > - **Fusion levers (giá trị nghiên cứu):** v0 early concat 8 kênh → v1 per-phase encoder + **phase-attention** → v2 tách nhóm structural (T1/T2/DWI) vs dynamic (pre/art/venous/delay), model pha động như chuỗi.
- **Ablation lõi (mỗi cái chứng minh 1 lựa chọn):** fusion variants; **phase-importance** bằng leave-one-phase-out (kỳ vọng arterial/venous nổi bật, nối LI-RADS); dimensionality 2D vs 2.5D vs 3D-patch vs 3D-full-volume (data-efficiency curve); pretrained vs scratch; registered vs unregistered; loss CE vs Focal vs class-balanced.
- **Fallback 2.5D:** stack 3 lát kề hoặc 3 lát trực giao làm kênh, backbone 2D ImageNet-pretrained. Chuyển fallback khi 3D thua 2.5D quá margin **và** vượt ngân sách compute.
- **Training:** AdamW, lr ~1e-4, cosine + warmup, AMP + gradient accumulation (batch 2 đến 4, effective 16 đến 32) + gradient checkpointing, early stopping theo macro-F1 CV, checkpoint/resume mỗi epoch (Kaggle session ≤12h).
- **XAI note:** Dùng heatmap ``|input × gradient|`` trên đúng crop E4 cho lớp model dự đoán. Heatmap phải khớp không gian crop và có thể dùng để kiểm tra model không nhìn nền/gan lành; không phải segmentation hay bằng chứng lâm sàng.

### Comparison Protocol (2 phase)
- **Controlled comparison:** mọi model cùng split/aug/epoch-budget/seed/cách fusion, chỉ đổi **backbone**; fine-tune từ pretrained, không train from scratch.
- **Phase 1 (sàng lọc):** train mỗi model 1 lần (1 seed, 1 fold, early stopping) → xếp hạng theo **macro-F1** trên validation.
- **Phase 2 (nghiêm ngặt):** chỉ **1 đến 2 model top** chạy full **5-fold CV x nhiều seed + bootstrap CI + calibration + selective prediction**.
- **Chốt:** best model → **external nhãn thô + OOD (Duke) 1 lần** + test-104 khóa kín; threshold/temperature khóa trên validation, không đụng test.

## 4. Evaluation Metrics

> Nguyên tắc: mọi con số báo kèm **95% CI**, không bao giờ báo điểm trần.

**4.1. Metric chính (quyết định best model)**
> - **Macro-F1:** F1 là trung bình điều hòa của Precision và Recall; "macro" nghĩa là tính F1 cho từng lớp rồi lấy trung bình đều, nên **lớp hiếm có trọng số ngang lớp phổ biến**. Dùng làm metric chốt vì phản ánh cân bằng "bắt đúng và gọi tên đúng" trên mọi lớp, không bị lớp đa số che lấp.
> - **Cohen's κ:** đo mức đồng thuận giữa dự đoán và nhãn thật **sau khi trừ đi phần trùng do may rủi** (κ=1 hoàn hảo, κ=0 chỉ ngang đoán mò). Dùng vì đây là metric xếp hạng của challenge và công bằng với bài đa lớp mất cân bằng.

**4.2. Metric phụ**
> - **Balanced accuracy:** trung bình Recall của tất cả các lớp. Ý nghĩa: accuracy "công bằng" không để lớp đông làm đẹp số ảo. Dùng để kiểm tra hiệu năng thật khi dữ liệu lệch.
> - **Macro-AUC (one-vs-rest):** diện tích dưới đường ROC, tính từng lớp đấu với phần còn lại rồi lấy trung bình. Ý nghĩa: khả năng **xếp hạng** (xác suất model chấm điểm ca đúng-lớp cao hơn ca không-lớp), **không phụ thuộc ngưỡng**. Dùng để đo năng lực phân biệt thô của model.
> - **Macro AUC-PR (Precision-Recall AUC):** diện tích dưới đường Precision-Recall. Ý nghĩa: tập trung vào lớp hiếm/dương tính, phản ánh trung thực hơn AUC khi mất cân bằng nặng. Dùng bổ sung cho AUC ở các lớp ít mẫu.
> - **Sensitivity (Recall) per-class:** trong tất cả ca thật của một lớp, model bắt được bao nhiêu. Dùng để đo khả năng không bỏ sót, đặc biệt với lớp ác tính.
> - **Specificity per-class:** trong tất cả ca không thuộc lớp đó, model loại đúng bao nhiêu. Dùng để kiểm soát báo động giả.
> - **Confusion matrix (chuẩn hóa):** bảng dự đoán so với nhãn thật. Dùng để thấy **cặp lớp hay nhầm** (ví dụ HCC nhầm ICC), phục vụ failure analysis.

**4.3. An toàn lâm sàng**
> - **Sensitivity ác/lành:** Recall trên bài gộp nhị phân ác vs lành. Dùng để đảm bảo tiêu chí "đừng bỏ sót ung thư".
> - **Cost-weighted error:** lỗi được nhân trọng số theo mức nguy hại lâm sàng (bỏ sót HCC nặng hơn nhiều so với nhầm nang). Dùng để phản ánh thiệt hại thật thay vì đếm lỗi đều nhau.

**4.4. Calibration (độ tin cậy của xác suất, headline)**
> Ý nghĩa chung: nếu model báo 80% ác thì trong 100 ca báo như vậy phải có khoảng 80 ca ác thật.
> - **ECE (Expected Calibration Error):** chia dự đoán theo mức tự tin thành các bin, đo trung bình khoảng cách giữa **độ tự tin** và **accuracy thật** ở mỗi bin. Càng thấp càng tốt. Dùng làm chỉ số tin cậy tổng quát.
> - **Adaptive-ECE / MCE:** adaptive-ECE dùng bin chia đều số mẫu (ổn định hơn); MCE là **khoảng cách tệ nhất** ở một bin (đo trường hợp xấu nhất).
> - **Brier score:** sai số bình phương trung bình giữa xác suất dự đoán và kết cục (0/1). Càng thấp càng tốt. Ý nghĩa: gộp cả độ chính xác lẫn độ hiệu chỉnh của xác suất.
> - **NLL (negative log-likelihood):** phạt rất nặng khi model **tự tin nhưng sai**. Dùng để đánh giá chất lượng xác suất theo hướng probabilistic.
> - **Reliability diagram:** vẽ độ tự tin dự đoán so với accuracy thật; đường hoàn hảo là đường chéo. Dùng để nhìn model **overconfident** (dưới đường chéo) hay **underconfident**.
> - **Temperature scaling:** hiệu chỉnh hậu kỳ bằng cách chia logits cho một hệ số T học trên validation. Dùng để sửa overconfidence mà không cần train lại. So thêm **deep ensemble** vs **MC-dropout** như hai nguồn uncertainty.

**4.5. Selective prediction (từ chối khi không chắc, headline)**
> - **Risk-coverage curve:** khi cho model **được phép từ chối** (giảm coverage), xem sai số (risk) giảm ra sao. Dùng để định lượng lợi ích của việc chuyển ca khó cho bác sĩ.
> - **AURC (area under risk-coverage):** một con số tóm tắt chất lượng selective prediction, càng thấp càng tốt.
> - **Accuracy@coverage / Coverage@fixed-risk:** accuracy khi chỉ quyết trên X% ca tự tin nhất; hoặc tỷ lệ ca model có thể tự quyết trong khi giữ sai số dưới ngưỡng cho phép. Dùng để trả lời câu vận hành: model tự xử được bao nhiêu ca một cách an toàn.

**4.6. External & OOD (chạm 1 lần)**
> - **Δ (domain shift):** hiệu năng internal trừ external. Dùng để đo mức tụt khi đổi nguồn dữ liệu; báo trung thực, không giấu.
> - **AUROC OOD detection:** khả năng dùng điểm uncertainty để tách ca in-distribution với ca lạ (out-of-distribution). Dùng để kiểm tra model có biết cảnh báo dữ liệu lạ không.
> - **ECE dưới shift:** đo calibration ngay trên tập external/Duke. Dùng để xem độ tin cậy còn giữ được khi ra khỏi miền huấn luyện.

**4.7. Thống kê**
> - **95% CI bootstrap (resample mức bệnh nhân, ≥2000 lần):** lấy mẫu lại có hoàn lại trên tập bệnh nhân để ước lượng khoảng dao động của metric nếu áp lên quần thể khác. Dùng để mọi số đều báo `điểm ± CI`.
> - **Mean±std qua 5-fold / nhiều seed:** đo độ ổn định; model tốt không được đổi hiệu năng quá lớn chỉ vì đổi fold hay seed.
> - **DeLong test:** kiểm định khác biệt giữa hai AUC trên cùng dữ liệu. Dùng để khẳng định model A hơn B về AUC có ý nghĩa thống kê hay chỉ ngẫu nhiên.
> - **McNemar test:** kiểm định ghép cặp trên các ca cùng nhau giữa hai model. Dùng để so khác biệt accuracy có ý nghĩa.
> - **Bootstrap/permutation ghép cặp:** để so khác biệt macro-F1 và κ. **Holm correction:** hiệu chỉnh khi so nhiều model để tránh dương tính giả.
> - **Pre-register:** khóa metric/split **trước khi** train model cuối, tránh chỉnh sửa để làm đẹp số (một dạng leakage).

**4.8. Chiến lược ngưỡng (threshold)**
> - **Khóa trên validation, áp mù lên test:** chọn ngưỡng cắt trên tập validation rồi mang y nguyên sang test; chỉnh ngưỡng trên test để đẹp hơn là gian lận (data leakage).
> - **Youden J (Sens + Spec - 1):** cách chọn ngưỡng cân bằng tối ưu giữa bắt bệnh và giảm báo động giả.
> - **Sens-priority:** ngưỡng thiên lâm sàng, chấp nhận thêm báo động giả để tuyệt đối không bỏ sót ca ác.

## 5. Kế hoạch 6 tuần & triển khai (tóm tắt)

- **Sprint 1 (T1 đến T2):** tải data + EDA + preprocessing v0 cache thành Kaggle Dataset + split 5-fold patient-level + baseline 2.5D và 3D-patch + fusion v0; ra **bảng CV macro-F1/κ ± CI** đầu tiên; harmonize external nhãn thô + Duke OOD.
- **Sprint 2 (T3 đến T4):** fusion variants + phase-attention + arm 3D full-volume + pretrained backbones + xử lý mất cân bằng; **calibration + selective prediction**; ablation lõi; so sánh thống kê (DeLong/McNemar/Holm); external + OOD; chạy test-104 một lần.
- **Sprint 3 (T5 đến T6):** **web app tự code** (FastAPI backend + React, **không Streamlit/Gradio**): V1 kiểm tra ZIP có 8 MRI + 8 mask NIfTI cùng lưới để tái tạo crop ROI UniFormer và suy luận `live`; ca demo OOF hiển thị class + probs + uncertainty + malignant_prob + cờ "defer" và heatmap độ nhạy đa thì trên crop E4. DICOM ZIP là mở rộng sau; failure analysis; reproducibility pack (seed/config/notebook công khai/split file/checkpoints); viết báo cáo có CI + limitations.
- **Kill-switch (full ambition có điểm dừng):** chưa có quyền data → CT fallback; 3D thua 2.5D → 2.5D primary; full-volume không kịp → xuống ablation; hụt giờ GPU → ensemble K=5 giảm còn K=3; deep ensemble hụt giờ → MC-dropout; latency cao → rigid-only + crop + K=3.
- **Ưu tiên không bao giờ cắt:** model fusion có CV+CI, calibration + selective prediction, rigor thống kê, web app tối thiểu chạy được, reproducibility pack.

---
**Tiêu chí thành công tổng:** vượt baseline có ý nghĩa thống kê + ổn định qua fold/seed + **calibration & selective prediction là kết quả hạng nhất** + external nhãn thô + OOD phân tích được + protocol đúng (no leakage, threshold khóa từ validation) + demo web app tự code chạy được có uncertainty & heatmap + báo cáo trung thực có CI & limitations. *Không đặt mức AUC/accuracy tuyệt đối tùy tiện.*
