# Bức tranh thị trường: AI cho tổn thương gan trên ảnh y tế

> **Tài liệu khảo sát bên ngoài, không phải kết quả của dự án này.** Mọi số liệu dưới đây là của bên thứ ba (sản phẩm thương mại, công bố khoa học) và đều kèm nguồn. Dự án hiện *chưa có* model hay kết quả nào; không con số nào ở đây là của dự án.
>
> **Mốc thời gian: tháng 7/2026.** Trạng thái regulatory (FDA/CE), tính năng sản phẩm và số liệu có thể thay đổi — cần kiểm lại nguồn trước khi trích vào report.

---

## 1. Mục đích & phạm vi

Trả lời: (1) thị trường đang có ứng dụng AI gan nào, (2) tình trạng ra sao, (3) kết quả thế nào, (4) nếu ít/chưa có thì vướng gì, (5) nếu có thì làm thế nào — **input gì, output gì**.

**Phạm vi:** AI cho tổn thương gan nói chung — detection/triage · segmentation & định lượng · LI-RADS scoring · phân loại (classification). MRI là trọng tâm (đúng bài toán dự án), nhưng có CT vì phần lớn sản phẩm thương mại nằm ở CT. Kèm mảng **trustworthiness** (calibration + selective prediction / `defer`) — đóng góp headline của dự án.

---

## 2. Tóm tắt điều hành

- **Nghiên cứu rất sôi động, thị trường thương mại thì lệch hẳn về detection/định lượng.** Có > 1.100 thuật toán radiology AI được FDA cấp phép tính đến 3/2026 [S3][S2], nhưng gần như toàn bộ là **phát hiện / phân loại nhị phân / định lượng / triage**, không phải phân loại đa lớp tổn thương.
- **Định lượng mô gan (diffuse) đã thương mại hoá tốt**: cT1, PDFF (fat), iron — vd Perspectum LiverMultiScan (FDA/CE) [S16][S17]; fatty liver trên CT — Nanox HealthFLD (FDA 2024) [S4].
- **Phát hiện HCC** đã có sản phẩm/kết quả mạnh: Median iBiopsy đạt **sensitivity 92%** phát hiện nốt HCC từ 10 mm, so với ~69% của bác sĩ khi không có AI [S5][S6] — nhưng đây là **detection**, không phải phân loại 7 lớp.
- **Phân loại đa lớp tổn thương gan trên MRI đa pha**: hầu như **chỉ ở mức nghiên cứu**. Ví dụ tiêu biểu Hu et al. 2025 phân loại 7 lớp trên MRI đa chuỗi, **patient-acc 0,93 · F1 0,84** [S11]; các model explainable khác [S12][S13]. Sản phẩm thương mại tương đương gần như không có; thứ gần nhất là *decision support* trên **CT đa pha** (EDDA IQQA-Liver, FDA) [S19] và các prototype LI-RADS [S8][S9][S10].
- **Trustworthiness (calibration + selective prediction / `defer`)**: được thừa nhận rộng rãi là **yêu cầu để triển khai lâm sàng**, nhưng vẫn nằm ở tầng nghiên cứu, **chưa thành tính năng sản phẩm** [S14][S15]. Đây chính là khoảng trống dự án nhắm tới.

**Một câu:** thị trường đã giỏi *phát hiện* và *định lượng*; chỗ còn trống là *phân loại đa lớp có xác suất đáng tin và biết từ chối* — đúng định vị của dự án.

---

## 3. Bản đồ thị trường theo loại tác vụ

| Tác vụ | Trạng thái thương mại | Ví dụ | Input điển hình | Output điển hình |
|---|---|---|---|---|
| **Detection / triage** | Chín, nhiều sản phẩm FDA | Median iBiopsy (HCC) [S5][S6]; Aidoc abdominal CT (liver injury...) [S18] | CT (đa số) hoặc MRI series | Cờ/bounding box "có bất thường", ưu tiên đọc (triage flag) |
| **Segmentation & định lượng** | Chín (diffuse), đang lên (lesion) | Perspectum LiverMultiScan [S16][S17]; Nanox HealthFLD [S4] | MRI multiparametric / CT | Chỉ số định lượng: cT1 (ms), PDFF fat (%), iron (mg Fe/g), % steatosis; mask thể tích |
| **LI-RADS scoring** | Chủ yếu prototype/nghiên cứu | Automated CT LI-RADS [S8]; HCC risk map CE-MRI [S10]; review clinical readiness [S9] | CT/MRI đa pha có thuốc | Điểm LI-RADS (LR-1..LR-5), risk map, structured report; thường là *triage/hỗ trợ*, không tự kết luận |
| **Phân loại đa lớp tổn thương** | **Gần như chỉ nghiên cứu** | Hu 2025 (7 lớp, MRI đa chuỗi) [S11]; explainable models [S12][S13]; *decision support* EDDA IQQA-Liver (CT đa pha) [S19] | MRI/CT đa pha quanh tổn thương | Nhãn lớp + (trong nghiên cứu) xác suất; hiếm khi có calibration; **gần như không có cờ `defer`** |
| **Trustworthiness (calibration + `defer`)** | **Chưa thành sản phẩm** | Chủ yếu review/nghiên cứu [S14][S15] | (áp lên bất kỳ tác vụ nào ở trên) | Xác suất đã hiệu chỉnh, mức bất định, ngưỡng từ chối/chuyển bác sĩ |

---

## 4. Một số sản phẩm / công trình tiêu biểu (input → output)

| Tên | Loại | Modality | Input | Output | Trạng thái | Kết quả công bố | Nguồn |
|---|---|---|---|---|---|---|---|
| **Perspectum LiverMultiScan** | Định lượng mô gan | MRI multiparametric | Chuỗi mapping T1/T2*/PDFF | cT1 (ms), fat fraction PDFF (%), iron (mg Fe/g) | FDA 510(k) + CE, cloud SaMD | Được dùng chẩn đoán/theo dõi bệnh gan; cT1 dự báo outcome | [S16][S17] |
| **Nanox HealthFLD** | Fatty liver | CT | CT ngực/bụng thường quy | Định tính + định lượng steatosis gan | FDA 510(k), 2/2024 | Hỗ trợ phát hiện MASLD sớm | [S4] |
| **Median iBiopsy / Eyonis LMS** | Detection HCC | CT | CT đa pha | Phát hiện/định vị nốt HCC (từ ~10 mm) | Sản phẩm đang phát triển/đăng ký | **Sens 92%** vs ~69% bác sĩ (không AI) | [S5][S6] |
| **Aidoc (abdominal CT)** | Multi-triage | CT | 1 lượt CT bụng | Cờ nhiều tình trạng cấp (gồm liver injury) | FDA cleared 1/2026 | Triage nhiều finding trong một workflow | [S18] |
| **EDDA IQQA-Liver** | Decision support tổn thương | Multiphase MDCT | CT đa pha | Đánh giá/định lượng tổn thương gan hỗ trợ bác sĩ | FDA cleared | Diagnostic decision support | [S19] |
| **Automated CT LI-RADS (ML)** | LI-RADS scoring | CT đa pha | CT có thuốc | Điểm LI-RADS tự động | Nghiên cứu đa trung tâm | Đồng thuận với bác sĩ ~89–98% theo từng đặc điểm | [S8] |
| **Hu et al. 2025** | Phân loại 7 lớp | MRI 8 chuỗi | Volume MRI đa chuỗi | Nhãn 1/7 lớp FLL | Nghiên cứu | **patient-acc 0,93 · lesion-acc 0,86 · F1 0,84** | [S11] |
| **Shen et al. 2025 (explainable)** | Phân loại + giải thích | Multiparametric MRI | MRI + segmentation nnU-Net | Nhãn FLL + giải thích | Nghiên cứu (external test) | Model explainable, kiểm định đa trung tâm | [S12] |

> Lưu ý: các số ở cột "Kết quả" đo trên **tập test của chính công trình đó**, không so trực tiếp được với nhau và không phải test-104 của LLD-MMRI.

---

## 5. Mảng trustworthiness: calibration + selective prediction

Đây là chỗ thị trường **hầu như bỏ trống**, dù giới nghiên cứu xem là điều kiện để được chấp nhận lâm sàng:

- Mức chấp nhận DL trên lâm sàng còn **thấp so với số lượng model điểm cao trong paper**, vì bác sĩ ngại tin dự đoán "hộp đen" [S14].
- Uncertainty quantification (Bayesian, MC-dropout, deep ensemble) được đề xuất để **giảm hiệu ứng hộp đen** và tăng khả năng chấp nhận [S14][S15].
- Model có thể **chính xác nhưng calibration kém**, đặc biệt khi có dataset shift; công trình lâm sàng coi calibration là **yêu cầu triển khai** chứ không phải phụ [S15].
- "Biết khi nào không nên hành động" (selective prediction / `defer`) được nêu như năng lực cần có cho hỗ trợ quyết định đáng tin [S15].

Nhưng: những năng lực này **hiếm khi xuất hiện trong output sản phẩm**. Đa số sản phẩm trả nhãn/score/định lượng, không trả **xác suất đã hiệu chỉnh + mức bất định + cờ từ chối**.

---

## 6. Vì sao thị trường chưa đưa "phân loại đa lớp + uncertainty" vào dùng

1. **Rào cản regulatory.** Phân loại tổn thương = một **kết luận chẩn đoán** (SaMD rủi ro cao hơn), bar validation cao hơn hẳn detection/triage. Nhiều tool được cấp phép dưới dạng *triage/notification/CADe* rủi ro thấp; classification tự động khó qua cửa hơn [S1][S9].
2. **MRI đa pha phức tạp.** Cần registration giữa các pha, chịu biến thiên protocol/scanner/timing thuốc — khó chuẩn hoá hơn CT; đó là lý do phần lớn sản phẩm chọn CT [S1].
3. **Trust & liability.** Kết luận đa lớp không kèm mức bất định thì bác sĩ/nhà quản lý không dám giao quyền; trách nhiệm pháp lý khi model sai chưa rõ [S14].
4. **Dữ liệu & lớp hiếm.** Cần dataset đa trung tâm, có nhãn, đủ lớn cho cả lớp hiếm. LLD-MMRI chỉ 498 ca — nhỏ so với nhu cầu sản phẩm [S1][S11].
5. **Generalization / dataset shift.** Calibration và độ chính xác tụt khi đổi máy/viện; external validation còn yếu [S15].
6. **Workflow & chi trả.** Chưa rõ tích hợp PACS/RIS, ROI lâm sàng và cơ chế reimbursement cho một tool "phân loại + từ chối".

Hệ quả: thị trường đi đường an toàn — **phát hiện và định lượng trước**, để phân loại đa lớp cho nghiên cứu.

---

## 7. Sản phẩm đã có đang làm thế nào — input gì, output gì

**Input (thực tế thị trường):**
- Chủ yếu **CT** (một pha hoặc đa pha); MRI thường là multiparametric cho định lượng mô, ít khi là 8-pha lesion-level như LLD-MMRI.
- Nhiều sản phẩm nhận **series DICOM** trực tiếp từ PACS, xử lý trên cloud (vd LiverMultiScan) [S16][S17].

**Output (thực tế thị trường):**
- **Detection/triage:** cờ có/không bất thường, vị trí, mức ưu tiên đọc [S18][S5].
- **Định lượng:** chỉ số vật lý (cT1, PDFF %, iron, % steatosis), mask/thể tích [S17][S4].
- **LI-RADS/decision support:** điểm LR, risk map, structured report — kèm câu chữ "hỗ trợ bác sĩ", không thay quyết định [S8][S9][S19].
- **Rất hiếm:** phân bố xác suất theo nhiều lớp **đã calibration**; **gần như không có** cờ `defer`/mức bất định hiển thị cho người dùng.

Nói cách khác: thị trường trả **"cái gì / bao nhiêu"**, chưa trả **"đáng tin đến đâu / khi nào nên dừng"**.

---

## 8. Hàm ý cho dự án

- Định vị của dự án — **phân loại đa lớp trên MRI đa pha + xác suất đã calibration + selective prediction (`defer`)** — nằm **đúng khoảng trống** giữa nghiên cứu (đã có phân loại nhưng thiếu trustworthiness bài bản) và thị trường (giỏi detection/định lượng, né classification đa lớp).
- Không đua accuracy: các công trình phân loại đã đạt F1 ~0,84 [S11]; giá trị khác biệt là **đo được độ đáng tin** và **biết từ chối**, đúng thứ [S14][S15] nói thị trường còn thiếu.
- Rào cản mục 6 cũng là **giới hạn phải nói thẳng** trong report (RUO, chưa kiểm định lâm sàng, dataset nhỏ, chưa external validation mạnh) — trung thực hơn ấn tượng.

---

## 9. Nguồn

Tất cả là công bố/sản phẩm của bên thứ ba, truy cập 7/2026.

- **[S1]** Systematic Review: AI Applications in Liver Imaging (Segmentation & Detection). <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11856300/>
- **[S2]** AI in Radiology: 2025 Trends, FDA Approvals & Adoption — IntuitionLabs. <https://intuitionlabs.ai/articles/ai-radiology-trends-2025>
- **[S3]** Radiology gets 68 new FDA-cleared algorithms — Radiology Business. <https://radiologybusiness.com/topics/artificial-intelligence/radiology-gets-68-new-fda-cleared-algorithms>
- **[S4]** Nanox HealthFLD FDA 510(k) clearance, 2/2024 (press release, SEC). <https://www.sec.gov/Archives/edgar/data/1795251/000121390024012870/ea193560ex99-1_nanox.htm>
- **[S5]** Median Technologies iBiopsy HCC detection — ESMO 2023 results (92% sensitivity). <https://www.biospace.com/first-results-of-median-technologies-ibiopsy-hcc-detection-ai-model-developed-on-the-phelicar-clinical-data-registry-to-be-presented-at-the-esmo-congress-oct-20-24-2023-madrid-spain>
- **[S6]** Median Technologies — Eyonis / Liver Cancer (very early HCC). <https://mediantechnologies.com/precision-diagnostic-eyonis/liver-cancer-very-early-hcc/>
- **[S7]** The added value of AI to LI-RADS categorization: systematic review — Eur J Radiol 2022. <https://www.ejradiology.com/article/S0720-048X(22)00101-2/abstract>
- **[S8]** Automated CT LI-RADS v2018 scoring using ML: multivendor, multicentre — ScienceDirect. <https://www.sciencedirect.com/science/article/pii/S258955592300188X>
- **[S9]** LI-RADS-aligned AI for liver cancer diagnosis: methods, evidence, clinical readiness — Abdominal Radiology 2025. <https://link.springer.com/article/10.1007/s00261-025-05329-5>
- **[S10]** LI-RADS-based HCC risk mapping using CE-MRI and self-configuring DL — PMC. <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11912691/>
- **[S11]** Hu et al. Automatic Classification of Focal Liver Lesions Based on Multi-Sequence MRI — J Imaging Inform Med 2025 (7 lớp; patient-acc 0,93; F1 0,84). <https://link.springer.com/article/10.1007/s10278-024-01326-0>
- **[S12]** Shen et al. An Explainable Deep Learning Model for Focal Liver Lesion Diagnosis Using Multiparametric MRI — Radiology: AI 2025. <https://pubs.rsna.org/doi/10.1148/ryai.240531>
- **[S13]** Correlation Routing Network for Explainable Lesion Classification in Multi-Parametric Liver MRI — Medical Image Analysis 2025. <https://www.sciencedirect.com/science/article/abs/pii/S1361841525003366>
- **[S14]** Trustworthy clinical AI: a unified review of uncertainty quantification in DL for medical image analysis — Artif Intell Med (ScienceDirect). <https://www.sciencedirect.com/science/article/pii/S0933365724000721>
- **[S15]** Uncertainty Quantification for Machine Learning in Healthcare: A Survey — arXiv 2505.02874. <https://arxiv.org/pdf/2505.02874>
- **[S16]** FDA clears Perspectum Diagnostics' LiverMultiScan — AuntMinnie. <https://www.auntminnie.com/imaging-informatics/advanced-visualization/image-processing/article/15619079/fda-clears-perspectum-diagnostics-livermultiscan>
- **[S17]** LiverMultiScan FAQ (outputs: cT1, PDFF, iron) — Perspectum. <https://perspectum.com/livermultiscan-faq/>
- **[S18]** FDA clears Aidoc tool that detects multiple conditions on a CT scan — STAT, 1/2026. <https://www.statnews.com/2026/01/21/fda-clears-aidoc-tool-detect-multiple-conditions-from-ct-scan/>
- **[S19]** EDDA Technology IQQA-Liver FDA clearance for multiphase MDCT — BioSpace. <https://www.biospace.com/b-edda-technology-b-receives-fda-clearance-for-its-iqqa-r-liver-software-for-multiphase-mdct>
