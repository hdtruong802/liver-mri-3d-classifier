# Báo cáo W1: tiến độ và thay đổi scope dự án AI nghiên cứu u gan

**Người thực hiện:** Hoàng Đức Trường<br>
**Ngày chốt:** 24/07/2026
**Trạng thái:** Research Use Only (RUO); không dùng để chẩn đoán hay thay thế bác sĩ.

## Tóm tắt điều hành

Dự án khởi đầu bằng một pipeline CT dạng *detection/triage proxy*: phân loại lát cắt có tổn thương gan hay gan bình thường, sau đó tổng hợp theo bệnh nhân. Pha này đã tạo được bằng chứng kỹ thuật ban đầu: data audit, chia tập theo bệnh nhân, CI bootstrap, kiểm tra Grad-CAM và một lần đánh giá external trên 3D-IRCADb-01. Tuy nhiên, nhãn LiTS được suy ra từ segmentation và bài toán nhị phân chỉ trả lời một proxy cho phát hiện tổn thương, chưa trả lời trực tiếp bài toán phân loại loại u gan. Sau feedback của mentor và rà soát lại mức độ phù hợp giữa câu hỏi nghiên cứu, dữ liệu public và đóng góp khoa học, dự án chọn hướng **phân loại đa lớp u gan trên MRI 3D đa pha**. Scope mới dùng LLD-MMRI, gồm 7 lớp tổn thương và 8 chuỗi/thì MRI, đồng thời lấy **calibration** và **selective prediction** làm đóng góp chính thay vì chạy đua accuracy.

## 1. Bối cảnh ban đầu và feedback mentor

### Bối cảnh CT ban đầu

Pha đầu trong `HCC-TACE-Assist` dùng LiTS để suy nhãn ở mức lát cắt CT: lát có diện tích u đủ ngưỡng là positive, lát gan không đủ ngưỡng là negative. Xác suất lát cắt được gộp lên mức bệnh nhân; vì vậy đây là công cụ *detection/triage proxy*, không phải bộ phân loại mô bệnh học hay phân loại đa lớp u.

### Feedback và quyết định

Mentor ghi nhận báo cáo, lộ trình và điều kiện chọn model có giải thích rõ ràng. Tuy nhiên, scope/output ban đầu dù phù hợp để tích hợp và demo vẫn chưa có đủ tính mới cho ứng dụng thực tế và ý nghĩa khoa học của một hướng nghiên cứu còn hạn chế. Mentor đề xuất khảo sát thêm public dataset để tìm một cách tiếp cận mới, hoặc giữ binary classification và thêm heatmap vùng tổn thương; đồng thời đưa ra lựa chọn giữa binary và đa lớp.

Quyết định của dự án là **chọn phân loại đa lớp ung thư/tổn thương gan**. Đây là lựa chọn chủ động sau khi cân nhắc binary kèm heatmap, không phải kết luận rằng hướng binary không có giá trị. Feedback giúp phân biệt rõ hai mức mục tiêu: một pipeline demo chạy được và một câu hỏi nghiên cứu có đóng góp rõ ràng.

Chuỗi thay đổi scope là: **feedback mentor → rà soát độ phù hợp nhãn/dataset → nhận diện giới hạn của binary CT proxy → khảo sát dataset public → chọn LLD-MMRI đa pha, 7 lớp → tập trung vào MRI 3D đa lớp, calibration và selective prediction.**

## 2. Vấn đề dataset và lý do đổi scope

| Vấn đề | Bằng chứng | Tác động khoa học | Quyết định |
|---|---|---|---|
| Nhãn LiTS là segmentation | Nhãn slice được suy từ mask u với `τ_area=20`, không phải nhãn bệnh học đa lớp. | Model chỉ học proxy “có tổn thương” ở mức lát cắt. | Giữ pha CT như nền tảng kỹ thuật, không diễn giải thành phân loại loại u. |
| Taxonomy CT không khớp mục tiêu mới | LiTS có HCC và di căn; không cung cấp nhãn lành/ác hay 7 loại tổn thương đáng tin ở mức ROI. | Không thể trả lời trực tiếp “đây là loại u gì?” hoặc đánh giá 7 lớp. | Chuyển bài toán chính sang LLD-MMRI. |
| Negative bệnh nhân khan hiếm | LiTS có 118/131 bệnh nhân có u và chỉ 13/131 không u. | Specificity mức bệnh nhân có CI rộng; patient-level metric dễ nhiễu. | Ưu tiên slice-level có cluster bootstrap, và dùng external CT để kiểm tra generalization. |
| Dataset khớp câu hỏi hơn | LLD-MMRI có 498 bệnh nhân, 7 lớp tổn thương, 8 chuỗi/thì MRI và ROI/bbox. | Có nhãn trực tiếp cho phân loại đa lớp lesion-level. | Chọn MRI 3D đa pha làm scope nghiên cứu chính. |

Đổi scope vì vậy là tăng độ khớp giữa dữ liệu, nhãn và câu hỏi khoa học; nó không phủ nhận giá trị của pipeline CT đã hoàn thành.

## 3. Công việc đã hoàn thành

### 3.1. Pha CT trong HCC-TACE-Assist

**Dữ liệu và đánh giá.** Đã audit 131 volume LiTS, tạo 19.094 lát có gan, chốt `τ_area=20 px`, lưu split ở mức bệnh nhân và kiểm tra leakage đạt. Protocol train/eval được config hoá, có bootstrap CI theo bệnh nhân và tránh dùng test để chọn threshold/model.

**Sàng lọc backbone.** Ở Phase 1 trên fold 0, ConvNeXt V2 Nano đứng đầu với slice-AUROC **0,882 [0,815–0,921]**, tiếp theo là FastViT 0,874, ResNet-50 0,837 và EfficientNet-B0 0,826. Kết quả này là tín hiệu lựa chọn model, chưa phải kết quả cuối 5-fold/đa seed.

**Interpretability và external.** Grad-CAM đã qua sanity check định tính theo báo cáo; đây là bằng chứng rằng cần tiếp tục kiểm tra vùng chú ý, không phải chứng minh lâm sàng tuyệt đối. External 3D-IRCADb-01 được chạy một lần với threshold khóa từ validation nội bộ: 20 ca, 2.068 lát có gan, slice-AUROC **0,807 [0,678–0,902]**, sensitivity/specificity **0,74/0,71**. Kết quả hỗ trợ generalization ở mức lát cắt, còn patient-level vẫn nhiễu do cohort nhỏ.

**Bàn giao MRI từ repo cũ.** Repo cũ cũng đã có ingestion/QC và scaffold train/eval LLD-MMRI cho 7 lớp. Đây là tài sản kỹ thuật có thể tái sử dụng, nhưng không được suy diễn thành kết quả hiệu năng MRI đã xác nhận cho repo mới.

### 3.2. Pha MRI trong liver-mri-3d-classifier

Scope mới đã được đặc tả là phân loại 3D đa pha cho 7 lớp tổn thương trên LLD-MMRI. Các nguyên tắc đã khóa gồm: split tuyệt đối theo bệnh nhân, test-104 giữ kín và chỉ dùng một lần, mọi metric kèm bootstrap CI mức bệnh nhân (tối thiểu 2.000 lần), không leakage, và demo bằng FastAPI cùng frontend tự code.

Về đánh giá ngoài miền, kế hoạch tách hai vai trò: cohort external có nhãn thô HCC-vs-non-HCC và Duke Liver Dataset làm OOD/domain-shift probe. Duke không có nhãn loại tổn thương nên không được dùng để báo external classification accuracy hay calibration có giám sát. OpenSwissHCC là **đề xuất cần audit metadata và formalize protocol**, chưa được tải hoặc chạy.

Deliverable truyền thông hiện có là `slides/overview.html` gồm 14 slide, đã rà typography/layout và trích dẫn. Biểu đồ risk–coverage với các mốc 5/13/23 là **minh hoạ giả lập có gắn nhãn**, không phải kết quả dự án. Chưa có kết quả train/eval MRI nào được xác minh trong repo mới.

## 4. Kết quả, nhận xét và bài học

| Hạng mục | Trạng thái | Bằng chứng | Nhận xét |
|---|---|---|---|
| Pipeline CT, data audit và split đúng | Hoàn thành | LiTS 131 volume; leakage test pass | Nền tảng tái lập tốt. |
| So sánh backbone CT | Hoàn thành một fold | Phase 1 có AUROC + CI | Cần CV/đa seed nếu tiếp tục dùng làm kết quả cuối. |
| Grad-CAM sanity CT | Hoàn thành | Báo cáo sanity check | Là kiểm tra định tính, không thay thế validation. |
| External CT trên 3D-IRCADb-01 | Hoàn thành một lần | Slice-AUROC 0,807 [0,678–0,902] | Có bằng chứng external cho proxy CT; cohort nhỏ. |
| Scope MRI 3D đa lớp và protocol tin cậy | Đã thiết kế | Spec sheet, plan, slide | Phù hợp nghiên cứu hơn, chưa phải kết quả mô hình. |
| External MRI có nhãn | Chưa bắt đầu | OpenSwissHCC mới ở mức đề xuất | Cần audit mapping HCC-vs-non-HCC trước khi dùng. |
| Duke OOD | Chưa bắt đầu | Dataset phù hợp domain shift, không có lesion label | Không được đánh đồng với external supervised test. |
| Demo MRI với model thật | Chưa bắt đầu | Chỉ có định hướng FastAPI/HTML | Phụ thuộc baseline/checkpoint đã khóa. |

Pha CT chứng minh nhóm có thể xây pipeline với split đúng, CI, external test và kiểm tra interpretability. Hạn chế nằm ở độ khớp của dataset với câu hỏi phân loại đa lớp, không nằm ở việc thiếu một demo kỹ thuật. MRI 3D đa pha khớp hơn với mục tiêu lâm sàng-nghiên cứu nhưng tăng rủi ro về truy cập dữ liệu, registration, mất cân bằng lớp, compute Kaggle và harmonize nhãn external. Điểm mạnh cần chứng minh của scope mới là **độ đáng tin cậy của xác suất và quyết định defer**, không phải một con số accuracy cao đơn lẻ.

## 5. Công việc tiếp theo theo thứ tự ưu tiên

1. Chốt quyền truy cập, audit LLD-MMRI và frozen split mức bệnh nhân.
2. Dựng baseline 2.5D và 3D đa pha với cross-validation và CI.
3. So sánh fusion/phase-importance, đồng thời xử lý mất cân bằng lớp hiếm.
4. Thực hiện calibration, selective prediction, reliability diagram và risk–coverage/AURC.
5. Audit mapping OpenSwissHCC trước external HCC-vs-non-HCC; tách Duke thành OOD probe.
6. Khóa protocol/model/threshold trước khi chạy test-104 đúng một lần.
7. Nối model thật vào FastAPI/web app, failure analysis, reproducibility pack và báo cáo cuối.

## 6. Timeline và nguồn nội bộ

| Thời điểm | Mốc |
|---|---|
| 20–21/07/2026 | Thiết lập pipeline CT, audit LiTS, cache/manifest, split theo bệnh nhân và baseline. |
| 21/07/2026 | Sàng lọc 4 backbone CT; ConvNeXt V2 Nano là finalist. |
| 22/07/2026 | Grad-CAM sanity và external 3D-IRCADb-01; bắt đầu chuẩn bị phân loại LLD-MMRI 7 lớp. |
| 24/07/2026 | Scope MRI 3D đa pha/trustworthiness được đặc tả trong repo riêng; hoàn thiện slide truyền thông. |

Nguồn nội bộ chính:

- [AGENTS: HCC-TACE-Assist](../../HCC-TACE-Assist/HCC-TACE-Assist/AGENTS.md)
- [DATA_CARD: LiTS](../../HCC-TACE-Assist/HCC-TACE-Assist/DATA_CARD.md)
- [Phase 1 backbone report](../../HCC-TACE-Assist/HCC-TACE-Assist/report/T3_W2_Phase1.md)
- [External 3D-IRCADb report](../../HCC-TACE-Assist/HCC-TACE-Assist/report/T3_W3_External_IRCADb.md)
- [Grad-CAM sanity report](../../HCC-TACE-Assist/HCC-TACE-Assist/report/T3_W3_GradCAM_Sanity.md)
- [HCC-TACE worklog](../../HCC-TACE-Assist/HCC-TACE-Assist/docs/WORKLOG.md)
- [MRI specification](../MRI_Classification_Spec_Sheet.md)
- [MRI six-week plan](../liver_mri_3d_classification_plan.md)
- [MRI worklog](../WORKLOG.md)

## Kết luận cho mentor

Thay đổi scope có cơ sở về dữ liệu và khoa học: binary CT đã là một nền tảng kỹ thuật được kiểm chứng, nhưng không đủ khớp với mục tiêu phân loại loại u gan. Hướng chính tiếp theo là MRI 3D đa pha, đa lớp, với calibration và selective prediction là bằng chứng trọng tâm cần hoàn thành. Mọi kết quả MRI và external validation chỉ được báo cáo sau khi protocol, mapping nhãn và đánh giá đã được khóa đúng quy trình.
