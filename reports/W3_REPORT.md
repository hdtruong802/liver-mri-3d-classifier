# Báo cáo W3: cross-validation có CI, đo trustworthiness, và lần chạm tập test khoá kín

**Người thực hiện:** Hoàng Đức Trường
**Ngày tổng hợp:** 07/08/2026
**Kỳ báo cáo:** 01/08 – 07/08/2026
**Trạng thái:** Research Use Only (RUO); không dùng để chẩn đoán hay thay thế bác sĩ.

## Tóm tắt

W2 kết thúc với macro-F1 **0,7001** trên val fold 1 và hai câu hỏi bỏ ngỏ: con số đó có đứng được khi chạy đủ 5 fold không, và nó tương ứng bao nhiêu trên tập test thật. W3 trả lời cả hai.

Gộp out-of-fold 394 bệnh nhân cho **0,6851** [0,6394; 0,7308]. Tập test-104 khoá kín, sau khi khoá protocol bằng văn bản và chạm đúng một lần, cho **0,6162** [0,5246; 0,7032]. Con số thứ hai ngang mốc baseline của ban tổ chức và còn cách rõ ràng ba đội đầu bảng.

Phần đóng góp headline có số đầy đủ lần đầu: xác suất được hiệu chỉnh và cơ chế từ chối ca không chắc. Bỏ 20% ca mà mô hình ít chắc nhất, macro-F1 trên phần còn lại tăng **+0,070** [+0,015; +0,124], P = 0,016.

Bốn hướng cải tiến thử trong tuần đều không cho kết quả có ý nghĩa thống kê. Chiều thứ Sáu tìm ra một **lỗi thật trong augmentation** tồn tại suốt 12 lần huấn luyện, và nó là giả thuyết mạnh nhất giải thích cả bốn kết quả null đó.

Thời gian xử lý một ca mới, đo end-to-end: **3,46 – 4,9 giây**, trong đó tiền xử lý chiếm khoảng 96%.

## 1. Mục tiêu W3 và trạng thái Definition of Done

Mục tiêu W3 theo `docs/plan.md`: biến baseline 1-fold thành bảng CV 5-fold có CI, thêm fusion v0, và dựng hạ tầng external/OOD.

**Đây là bảng DoD đầu tiên của dự án không toàn "Đạt".**

| Definition of Done | Trạng thái | Bằng chứng |
|---|---|---|
| Baseline 3D-patch đủ 5-fold; bảng macro-F1/κ ± 95% CI | **Đạt** | 0,6851 [0,6394; 0,7308] · κ 0,6419 · 394 bệnh nhân |
| Fusion v0 (early concat 8 kênh) chạy 5-fold, so với baseline | **Không áp dụng** | early concat *chính là* baseline hiện tại; fusion v1 Siamese đã dựng xong, chưa chạy |
| Rigid registration pipeline | **Chưa làm** | E4 chỉ khử tịnh tiến bằng bbox có sẵn, không phải một pipeline registration |
| External nhãn thô harmonized + Duke OOD | **Đã cắt khỏi kế hoạch** | quyết định của người dùng ngày 05/08, ghi ở WORKLOG |
| `src/eval/` thuần (input → metric), tách khỏi train | **Đạt** | chạy lại được trên checkpoint cũ, CPU, không cần GPU |

**Ngoài kế hoạch nhưng đã làm trong tuần:**

- Chạm test-104 (kế hoạch ban đầu là W5), kèm pre-registration đầy đủ.
- Calibration và selective prediction trên đủ 394 ca, không chỉ 1 fold.
- MC-dropout và bất định epistemic.
- Grad-CAM 3D cùng độ nhạy theo thì trên 4 ca minh hoạ.
- Web app chạy số thật out-of-fold thay cho số giả lập.
- Slide báo cáo kết quả (`slides/overview_v3.html`).

Việc đổi thứ tự ưu tiên là có chủ đích: sau khi CV 5-fold cho thấy con số thấp hơn kỳ vọng, giá trị của việc dựng thêm hạ tầng external giảm hẳn so với việc hiểu vì sao con số thấp.

## 2. Từ một fold đến con số báo cáo được

### 2.1. Bảng CV 5-fold

Năm lần huấn luyện, mỗi lần 300 epoch, cùng seed 1337, config giống hệt nhau trừ đúng khoá `fold`. Năm tập val phân hoạch sạch 394 ca trainval, đã kiểm chứng giao mọi cặp bằng rỗng và hợp bằng đúng 394.

| fold | n val | macro-F1 | κ | epoch tốt nhất |
|---|---|---|---|---|
| 1 | 82 | 0,7001 | 0,6465 | 231 |
| 2 | 80 | 0,6771 | 0,6273 | 297 |
| 3 | 78 | 0,7304 | 0,6772 | 104 |
| 4 | 77 | 0,6680 | 0,6548 | 135 |
| 5 | 77 | 0,6618 | 0,6031 | 144 |
| **gộp out-of-fold** | **394** | **0,6851** [0,6394; 0,7308] | **0,6419** [0,5907; 0,6940] | — |

Trung bình 5 fold là 0,6875 ± 0,0281. **Con số báo cáo là bản gộp out-of-fold, không phải trung bình này**: trung bình các fold không có khoảng tin cậy đúng nghĩa, vì mỗi fold là một tập nhỏ khác nhau.

### 2.2. Thiên lệch chọn epoch: +0,079

Checkpoint `best` được chọn theo macro-F1 trên *chính tập val đang được báo*. Đo trên cùng 312 ca (fold 2 đến 5): `best` cho 0,6824 còn `last` (epoch 300) cho 0,6038.

Con số 0,6851 vì thế **lệch lạc quan khoảng 0,079**, và điều này được ghi vào tài liệu ngay khi đo được, trước khi chạm test. Mục 4.3 cho thấy nó dự đoán đúng kết quả test.

### 2.3. Hai lớp yếu, nhất quán ở cả 5 fold

F1 gộp out-of-fold: **di căn 0,488** (n=40) và **ICC 0,519** (n=46). Các lớp còn lại nằm trong khoảng 0,66 đến 0,83.

Ba hướng nhầm lớn nhất trong ma trận gộp: HCC bị đoán thành di căn 15 ca, ICC thành áp-xe 10 ca, HCC thành ICC 9 ca. Đây là chỗ đáng cải thiện, không phải nhiễu của một fold.

## 3. Trustworthiness: đóng góp headline có số đầy đủ

Đây là phần định vị của đề tài, nên nó quan trọng hơn các con số phân loại ở mục 2.

### 3.1. Xác suất chưa hiệu chỉnh thì không dùng được

Nhiệt độ được fit **leave-one-fold-out**: `T` áp lên fold `f` học từ 4 fold còn lại, nên không ca nào được hiệu chỉnh bởi một `T` đã nhìn thấy nó.

| | ECE | MCE | Brier | NLL | tự tin TB (lệch so accuracy) |
|---|---|---|---|---|---|
| chưa hiệu chỉnh | 0,2030 | 0,6775 | 0,5488 | 2,0308 | 0,889 (+0,186) |
| temp-scaled, fit **NLL** | 0,1756 | 0,8026 | 0,5228 | **1,1687** | 0,606 (−0,097) |
| temp-scaled, fit **ECE** | **0,1534** | **0,3510** | **0,5162** | 1,2812 | 0,745 (+0,042) |

*(accuracy thật 0,7030)*

Bốn điều rút ra:

1. **Model tự tin thái quá nghiêm trọng.** Tự tin trung bình 0,889 trong khi chỉ đúng 70,3%; trung vị 0,987 và phân vị 75 là 1,000. Đây là hệ quả trực tiếp của 300 epoch cross-entropy trần không label smoothing.
2. **`T` tối ưu NLL khác `T` tối ưu ECE, và chênh nhau nhiều.** NLL nhỏ nhất ở `T ≈ 3,26`, ECE nhỏ nhất ở `T ≈ 2,05`. Lấy `T` của NLL thì model bắn quá sang thiếu tự tin (0,606 so với accuracy 0,703) và MCE *xấu đi*.
3. **Một scalar là không đủ.** Ngay cả `T` tốt nhất cũng chỉ hạ ECE xuống 0,153.
4. Cách fit temperature ảnh hưởng tới con số nhiều hơn dự kiến, nên chỉ số leave-one-fold-out được dùng, số fit trong mẫu không vào báo cáo.

### 3.2. Cơ chế từ chối ca không chắc

Trên out-of-fold, xếp hạng theo xác suất cao nhất của một model tất định gần như **không có tác dụng**: AURC 0,206 so với điểm ngẫu nhiên 0,296, nhưng macro-F1 tại coverage 80% là 0,6813, tức không hơn 0,6851 ở coverage 100%.

MC-dropout (K=20 lượt trên chính model của từng fold) hạ macro-F1 từ 0,6851 xuống 0,5852, nên **không dùng làm bộ dự đoán**. Nhưng ECE của nó là 0,1216, tốt hơn cả temperature scaling tốt nhất mà không cần fit gì.

Thứ đáng giá là **phép lai**: dự đoán lấy từ model tất định, chỉ điểm xếp hạng defer lấy từ epistemic của MC-dropout.

| điểm xếp hạng defer | AURC | F1@100% | F1@90% | F1@80% | F1@70% |
|---|---|---|---|---|---|
| tất định · max-prob | 0,2059 | 0,6851 | 0,6909 | 0,6799 | 0,7043 |
| **lai · tất định + −epistemic** | **0,1689** | 0,6851 | 0,6923 | **0,7222** | 0,7367 |

Bootstrap ghép cặp trên hiệu, 2000 lần, phân tầng mức bệnh nhân:

| | hiệu | 95% CI | P |
|---|---|---|---|
| F1@80% (epistemic) − F1@100% | **+0,0350** | [+0,0039; +0,0647] | **0,030** |
| AURC (epistemic) − AURC (max-prob) | **−0,0346** | [−0,0648; −0,0080] | **0,013** |
| *đối chứng:* F1@80% (max-prob) − F1@100% | −0,0027 | [−0,0340; +0,0263] | 0,88 |

Dòng đối chứng mang cả lập luận: cùng model, cùng dự đoán, chỉ đổi cách xếp hạng.

> ⚠️ **Kết luận này bị đính chính ở mục 4.3 sau khi có số test-104.** Với 5 model độc lập thật thay vì MC-dropout trên một model, lợi thế của epistemic so với max-prob biến mất. Kết luận đúng được viết lại ở đó.

### 3.3. Giải thích được, kể cả khi sai

Grad-CAM 3D (thực chất dùng HiResCAM, vì các dense block của DenseNet có khoảng 61% đặc trưng âm, vi phạm giả định không-âm của Grad-CAM gốc) chạy trên 4 ca, mỗi ca dùng model của fold chứa nó ở val.

Hai ca đoán đúng có đỉnh chú ý **đúng tâm tổn thương trong mặt phẳng**, tức model nhìn vào tổn thương chứ không vào rìa. Ca `MR127280` thất bại toàn diện: thật là di căn, đoán u máu, đỉnh nằm ở lát biên lệch 32 voxel, **và** bản đồ cho lớp thật suy biến, tức không voxel nào ủng hộ đáp án đúng. Đây là ca đáng đưa vào phần failure analysis.

Độ nhạy theo thì: **In Phase và Out Phase thấp nhất ở cả 4 ca** (0,043 đến 0,092, đều dưới mức đều 0,125). Hợp lý về lâm sàng, vì hai thì chemical-shift chủ yếu để phát hiện mỡ, ít phân biệt được giữa 7 lớp này.

Bốn cảnh báo bắt buộc kèm bộ số này: bản đồ gốc chỉ 7×7×2 nên vị trí theo trục z chỉ nói được nửa trên hay nửa dưới; n = 4 ca nên đây là quan sát chứ không phải kết luận thống kê; đây là saliency chứ không phải ablation nên không nói được bỏ hẳn một thì thì mất bao nhiêu điểm; và mức phân biệt giữa các thì chỉ vừa phải, thì cao nhất chỉ gấp 1,3 đến 1,7 lần mức đều.

## 4. test-104: chạm lần thứ nhất và duy nhất

### 4.1. Protocol được khoá bằng văn bản trước khi chạy

Tập test-104 là held-out khoá kín, chạm đúng một lần. Trước khi chạy, toàn bộ lựa chọn được ghi vào `docs/TEST104_PREREGISTRATION.md` và **commit** (`56baa41`): cấu hình E4, bộ dự đoán chính là ensemble 5 fold, không dùng TTA, `T` fit trên out-of-fold rồi áp mù, danh sách metric, bốn mức coverage, và **ước lượng ghi trước là 0,62 – 0,72**.

Ba cổng chặn được cài trong code: thiếu cờ `--i-know-this-is-final` thì từ chối chạy; pre-registration phải **đã commit**, kiểm bằng `git log` chứ không kiểm sự tồn tại của file; và sha256 của 5 checkpoint phải khớp danh sách ghim sẵn.

Ensemble 5 fold **hợp lệ ở đây** vì không model nào trong 5 cái từng thấy 104 ca đó. Trên out-of-fold thì ngược lại và việc gộp bị cấm.

### 4.2. Kết quả

**macro-F1 = 0,6162** [0,5246; 0,7032] · κ 0,5647 · accuracy 0,6346 · n = 104.

Tất cả các hàng dưới đây đo trên **cùng một tập test-104 official**:

| Phương pháp | macro-F1 | Cohen's κ | Nguồn |
|---|---|---|---|
| Hạng 1 · WorkingisAllyouneed | 0,8322 | 0,7801 | bảng xếp hạng challenge |
| CGHNet | 0,8180 | 0,7820 | CGHNet Bảng 1 |
| Hạng 2 · NPUBXY | 0,8078 | 0,7660 | bảng xếp hạng challenge |
| Hạng 3 · LinGroup | 0,7860 | 0,7435 | bảng xếp hạng challenge |
| **Dự án này** (ensemble 5 fold) | **0,6162** [0,5246; 0,7032] | 0,5647 | đo 07/08/2026 |
| Baseline ban tổ chức | 0,6083 | 0,5414 | bảng xếp hạng challenge |

**Cách đọc đúng:** con số của dự án cao hơn baseline ban tổ chức **đúng 0,0038**, trong khi khoảng tin cậy rộng ±0,09 và phủ trùm con số đó. Phát biểu đúng là *ngang baseline, chưa phân biệt được về mặt thống kê*. Nói "vượt baseline" là đọc sai. Cũng vì lý do đó, mọi khoảng cách trong bảng đều chưa có ý nghĩa thống kê, trừ so với CGHNet và ba đội đầu bảng.

Từng lớp trên test-104: u máu 0,903 · nang 0,762 · HCC 0,679 · FNH 0,640 · áp-xe 0,538 · ICC 0,519 · **di căn 0,273**. Hướng nhầm chính giống hệt out-of-fold: HCC bị đoán thành di căn, 6 trong 32 ca HCC.

Phép tính trần, dùng đúng hai con số của hai lớp yếu: kể cả 5 lớp còn lại đều đạt 0,90 thì macro-F1 cũng chỉ tới **0,756**. Muốn qua mốc đó thì bắt buộc phải chữa hai lớp này.

### 4.3. Ba điều học được, và một đính chính

**Thiên lệch chọn epoch được xác nhận về mặt định lượng.** Out-of-fold cho 0,6851, test-104 cho 0,6162, hụt **0,069**. Thiên lệch đo được *trước khi chạm test* là **+0,079**. Hai con số gần trùng khít, nghĩa là phần lạc quan của out-of-fold đúng bằng phần dự án đã tự chỉ ra và cảnh báo, không có nguồn thổi phồng nào khác lộ ra.

**Ensemble gần như không giúp.** Hiệu so với trung bình 5 model đơn là +0,0162 [−0,0232; +0,0560], **P = 0,43**. Đáng nói hơn: model đơn tốt nhất (fold 2, 0,6308) **cao hơn cả ensemble**. Pre-registration là thứ ngăn việc báo con số đó, vì chọn nó sau khi nhìn test là chọn trên test.

**Đính chính kết luận ở mục 3.2.** Trên test-104, xếp hạng defer theo mức bất đồng giữa 5 model **không hơn** cách đơn giản là lấy xác suất cao nhất: hiệu AURC +0,0009, **P = 0,90**. Nhưng cả hai đều có tác dụng thật so với không từ chối ca nào:

| | hiệu so với F1@100% | 95% CI | P |
|---|---|---|---|
| max-prob @80% | **+0,0696** | [+0,0154; +0,1245] | **0,016** |
| −epistemic @80% | **+0,0970** | [+0,0466; +0,1451] | **<0,001** |
| max-prob @70% | +0,1267 | [+0,0568; +0,1859] | 0,002 |

Giải thích nhất quán cho việc hai kết luận khác nhau: trên out-of-fold, cái gọi là "ensemble" chỉ là MC-dropout trên **một** model tự tin thái quá, nên softmax của nó vô dụng. Với **5 model độc lập thật**, softmax của trung bình đã là một tín hiệu bất định tốt, và số hạng bất đồng riêng không thêm được gì.

Phát biểu đúng để dùng về sau: **từ chối 20% ca khó nâng macro-F1 từ 0,616 lên khoảng 0,68 đến 0,72, và không cần MC-dropout để làm việc đó.**

**Một phát hiện đi kèm về calibration.** Ensemble **chưa hiệu chỉnh** cho ECE 0,1303, tốt hơn cả model đơn *đã* temperature-scaling tốt nhất trên out-of-fold (0,1534). Gộp 5 model là bộ hiệu chỉnh tốt hơn temperature scaling ở bài toán này. Ngược lại, `T = 2,10` fit từ out-of-fold khi áp lên ensemble làm ECE *xấu đi* (0,1902) và bắn sang thiếu tự tin, đúng như pre-registration đã dự đoán trước khi chạy: `T` học từ phân bố của model đơn, áp lên ensemble vốn đã bớt tự tin, thì hiệu chỉnh quá tay.

## 5. Bốn thí nghiệm không hiệu quả, và một lỗi thật

### 5.1. Bảng kết quả âm

Tất cả đo trên val out-of-fold, bootstrap ghép cặp trên cùng bệnh nhân:

| Thí nghiệm | Hiệu macro-F1 | 95% CI | P |
|---|---|---|---|
| Hàm mất mát focal (γ=2) | −0,029 | [−0,105; +0,048] | 0,47 |
| Tăng cường dữ liệu mạnh hơn | −0,014 | [−0,078; +0,052] | 0,68 |
| Bỏ nhiễu cường độ theo thì (E6b) | −0,002 | [−0,042; +0,036] | 0,92 |
| Test-time augmentation bằng phép lật | −0,015 | [−0,035; +0,004] | 0,15 |

Không cái nào đạt ý nghĩa thống kê. Ghi lại vì kết quả âm cũng là kết quả: nó loại bớt hướng cho phần còn lại của dự án.

### 5.2. Ba điều đáng giá nằm dưới các con số null

**Focal loss không cần thiết vì một lý do kỹ thuật cụ thể.** Focal *có* làm model bớt tự tin từ đầu (ECE thô 0,154 so với 0,221 của cross-entropy, và `T` cần nhỏ hơn). Nhưng sau khi hiệu chỉnh đúng cách, hai bên bằng nhau: focal 0,1255 và cross-entropy 0,1281. Lợi thế biến mất qua đúng bước mà pipeline vốn đã làm.

**Bài học về quy trình, quan trọng hơn cả bốn kết quả.** E6b sàng trên 2 fold cho +0,038 và trông rất hứa hẹn; chạy đủ 5 fold cho −0,002. Toàn bộ mức tăng đến từ fold 1, và fold 1 hoá ra là một fold may mắn. **Hai fold đủ để loại một ý tưởng, không đủ để chọn nó.** Dự án đã bỏ hẳn cách sàng trên 2 fold.

**Một chẩn đoán định lượng về overfitting.** Trên cả 10 lần huấn luyện (5 fold × 2 cấu hình), epoch mà `val_loss` chạm đáy dự báo gần trọn vẹn macro-F1 cuối cùng của fold đó: tương quan hạng Spearman **ρ = +0,770, P = 0,0092**. Nút thắt là *thời điểm bắt đầu overfit*. Đây là tương quan trên 10 run và hai đại lượng cùng sinh từ một đường cong huấn luyện, nên là một chẩn đoán tốt chứ chưa phải bằng chứng nhân quả.

### 5.3. Lỗi thật tìm ra chiều 07/08

Kiểm tra vì sao TTA cho kết quả âm thì lộ ra một lỗi tồn tại suốt từ thí nghiệm đầu tiên:

- `RandomTranslate3D` dịch ảnh rồi **đệm 0** vào phần trống, với độ dịch ngẫu nhiên trên cả ba trục.
- `RandomRotateSmall` xoay rồi lấp góc bằng 0, với xác suất áp mặc định là 1,0.

Hệ quả đo được: **khoảng 100% mẫu train mang một dải đen ở rìa, trong khi 0% mẫu val có nó.** Đây là lệch phân bố train/val có hệ thống, xuất hiện ở mọi bước huấn luyện, và khớp với chẩn đoán overfit ở mục 5.2.

Đối chiếu bên ngoài: baseline official và CGHNet đều **không** làm vậy, họ cache rộng hơn rồi cắt ngẫu nhiên. Ablation của CGHNet cho thấy **bỏ random-crop mất 8,8 điểm**, là biến augmentation nặng nhất trong bảng của họ. Biên độ của dự án cũng yếu hơn: ±7,1% trong mặt phẳng so với 12,5% của họ.

Bằng chứng độc lập thứ hai cho cùng chẩn đoán: model **không bất biến với phép lật ảnh**, mất 0,02 đến 0,06 điểm khi ảnh bị lật, dù chính augmentation của nó lật cả ba trục với p = 0,5. Nó học thuộc hướng của ảnh thay vì học đặc trưng bất biến với hướng.

Đã dựng bản sửa (cache có lề dư 136×136×40, cắt ngẫu nhiên lúc train, cắt giữa lúc val), **chưa chạy**. Đây là việc đầu tiên của W4.

## 6. Thời gian xử lý một ca

| Thành phần | Thời gian | Đo trên |
|---|---|---|
| Tiền xử lý: đọc 8 file NIfTI, resample lên lưới chung, căn thì, chuẩn hoá | **3,43s** (trung vị) – **4,74s** (p90) | CPU Kaggle, 498 ca |
| Suy luận, 1 model | **32,9 ms** | GPU Tesla T4 |
| Suy luận, ensemble 5 fold | **164,7 ms** | GPU Tesla T4 |
| **Tổng end-to-end một ca mới** | **3,46 – 4,9 giây** | |

Điểm cần rút: **tiền xử lý chiếm khoảng 96% thời gian chờ, model gần như miễn phí.** Muốn giảm latency thì tối ưu phần tiền xử lý, không phải phần model. Con số này cũng cho thấy việc dùng ensemble 5 model thay vì 1 model chỉ tốn thêm khoảng 130 ms, tức không phải ràng buộc thực tế.

Hai thành phần đo trên hai thiết bị khác nhau trong cùng một pipeline: tiền xử lý chạy trên CPU vì nó là I/O và SimpleITK, suy luận chạy trên GPU.

## 7. Sản phẩm: web app

Backend FastAPI và frontend React chạy được với **số thật out-of-fold của 394 ca**, không phải số minh hoạ; ca nằm ngoài tập đó bị đánh dấu `simulated` bằng hai tín hiệu độc lập.

Ba đường quyết định được tách bạch, đúng theo kết luận kỹ thuật ở mục 3.2: lớp đoán lấy từ model tất định, xác suất hiển thị lấy từ bản đã hiệu chỉnh, còn quyết định defer xếp hạng theo bất định. Bản đồ vùng chú ý hiển thị kèm độ phân giải gốc để người xem không diễn giải quá mức. Dải RUO xuất hiện trên mọi màn hình có kết quả.

## 8. Trạng thái và giới hạn

| Hạng mục | Trạng thái | Bằng chứng | Nhận xét |
|---|---|---|---|
| CV 5-fold + CI bootstrap | Hoàn thành | 0,6851 [0,6394; 0,7308], 394 ca | Con số báo cáo được đầu tiên. |
| Calibration leave-one-fold-out | Hoàn thành | ECE 0,2030 → 0,1534 | Một scalar không đủ, cần vector/matrix scaling. |
| Selective prediction | Hoàn thành | +0,070 @80%, P = 0,016 | Có tác dụng thật trên test. |
| MC-dropout và epistemic | Hoàn thành | AURC 0,1689 trên out-of-fold | Lợi thế không lặp lại trên test, xem mục 4.3. |
| Grad-CAM và độ nhạy theo thì | Hoàn thành, n = 4 | 4 ca minh hoạ | Định tính, không phải bằng chứng thống kê. |
| **test-104** | **Đã chạm, một lần** | 0,6162 [0,5246; 0,7032] | Pre-registration commit trước khi chạy. |
| Web app với số thật | Hoàn thành | 394 ca out-of-fold | Chưa nối kết quả test-104. |
| Bốn thí nghiệm cải tiến | Hoàn thành, đều null | bảng mục 5.1 | Loại được bốn hướng. |
| Lỗi dải đệm trong augmentation | **Đã tìm ra, đã sửa code, chưa chạy** | ~100% mẫu train so với 0% mẫu val | Việc đầu tiên của W4. |
| Fusion v1 Siamese | Đã dựng, chưa chạy | `configs/e2_siamese.yaml` | Hướng còn tiềm năng lớn nhất. |
| Registration rigid | Chưa bắt đầu | — | E4 mới khử tịnh tiến. |
| External và OOD | **Đã cắt** | quyết định 05/08 | Không nằm trong phạm vi nữa. |

**Giới hạn phải nói rõ với người đọc:**

1. **test-104 đã chạm và chỉ còn chạm được một lần nữa.** Mọi cải tiến từ nay phải chốt trên out-of-fold. Muốn có số test cho một cấu hình mới thì đó là lần chạm thứ hai: phải xin phép, viết pre-registration mới, và báo cáo rõ là lần thứ hai.
2. **n = 104 nên khoảng tin cậy rộng ±0,09.** Mọi so sánh với mốc văn liệu đều chưa phân biệt được về thống kê, trừ CGHNet và ba đội đầu bảng.
3. **Con số out-of-fold 0,6851 không phải ước lượng không thiên lệch**, vì nó mang thiên lệch chọn epoch +0,079. Con số trung thực hơn là cột `last`, bằng 0,6038.
4. **Nút thắt nằm ở hai lớp, và trần 0,756 là một ràng buộc số học**, không phải phỏng đoán. Không có đường vòng nào tránh việc phải chữa di căn và ICC.
5. **Bốn kết quả null có thể do bộ đo quá yếu chứ không hẳn do ý tưởng sai.** Bản sàng 2 fold có n = 162 và CI khoảng ±0,08, không đủ lực để phát hiện hiệu ứng cỡ +0,03.
6. **Chưa có external validation và OOD probe.** Hạng mục này đã bị cắt khỏi kế hoạch, nên báo cáo cuối sẽ không có bằng chứng ngoài miền.
7. **Registration rigid thật vẫn chưa làm.** E4 chỉ khử tịnh tiến, không khử xoay và biến dạng, và điều này đã được ghi vào limitations từ W2.

## 9. Công việc tiếp theo theo thứ tự ưu tiên

1. Build cache có lề dư rồi chạy đủ 5 fold để sửa lỗi dải đệm. Đây là hướng có căn cứ mạnh nhất hiện có, và nó phải chạy trước mọi thứ khác vì nó đổi dữ liệu đầu vào.
2. Thử EMA trên cấu hình thắng ở bước 1, nhắm vào đúng đại lượng cho ρ = 0,770.
3. Chạy fusion v1 Siamese kèm phase-attention, có đối chứng cùng độ phân giải. Đây là bước duy nhất còn tiềm năng đưa điểm lên mức 0,75 trở lên.
4. Chạy lại focal loss trên đủ 5 fold, thử backbone pretrained và hình học nông hơn.
5. Phân tích false positive của ICC và di căn ở mức đặc trưng ảnh, để biết nút thắt là do dữ liệu nhập nhằng hay do model chưa dùng hết tín hiệu sẵn có.
6. Hình cho báo cáo, kiểm định thống kê giữa các model, gói tái lập, README.
7. Khoá cấu hình cuối cùng rồi chạm test-104 lần thứ hai.

## 10. Timeline

| Thời điểm | Mốc |
|---|---|
| 01/08/2026 | Chốt thế giới thị giác riêng cho web app; hoàn thiện giao diện đọc kết quả. |
| 04/08/2026 | **CV 5-fold hoàn tất: gộp out-of-fold 0,6851**; đo calibration leave-one-fold-out; đo selective prediction; MC-dropout và phép lai; web app nối số thật thay số giả lập. |
| 05/08/2026 | E5 focal loss null; Grad-CAM và độ nhạy theo thì trên 4 ca; E6 và E6b đều null trên bản sàng; dựng hạ tầng TTA, EMA, backbone pretrained. |
| 06/08/2026 | E6b chạy đủ 5 fold, xác nhận null (P = 0,92); phát hiện tương quan ρ = 0,770 giữa thời điểm bắt đầu overfit và điểm cuối. |
| 07/08/2026 | TTA cho kết quả âm; **chạm test-104 lần thứ nhất: 0,6162**; dựng slide báo cáo kết quả; **tìm ra lỗi dải đệm trong augmentation** và dựng bản sửa; đo latency end-to-end. |

## Kết luận

W3 biến một con số sàng lọc thành một con số **so sánh được trực tiếp với văn liệu**, và con số đó khiêm tốn hơn kỳ vọng: 0,6162 trên test-104, ngang mốc baseline của ban tổ chức, còn cách khoảng 0,20 so với các phương pháp công bố gần đây. Việc chạm test sớm hơn kế hoạch hai tuần là một đánh đổi có ý thức: nó lấy đi khả năng thử nghiệm tự do, đổi lại một mốc thật để định hướng phần còn lại của dự án.

Giá trị lớn nhất của tuần nằm ở phần phương pháp chứ không ở điểm số. Thiên lệch chọn epoch được đo trước và dự đoán đúng gần như chính xác mức hụt khi sang test. Pre-registration ngăn được việc báo model đơn tốt nhất thay cho ensemble, một cám dỗ có thật vì con số đó cao hơn. Bốn kết quả âm loại bỏ bốn hướng và tiết kiệm thời gian cho phần sau. Và một kết luận trước đó về selective prediction đã được đính chính công khai khi dữ liệu mới cho thấy nó chỉ đúng trong điều kiện hẹp hơn.

Về đóng góp headline, cơ chế từ chối ca không chắc đã chứng minh được là có tác dụng thật trên tập test khoá kín: bỏ 20% ca khó nhất nâng macro-F1 từ 0,616 lên khoảng 0,68 đến 0,72, có ý nghĩa thống kê. Xác suất thì vẫn chưa đủ tin: ECE 0,130 là con số tốt nhất đạt được, và nó đến từ việc gộp model chứ không từ temperature scaling.

Điều đáng chú ý nhất lại được tìm ra vào buổi cuối tuần. Bốn thí nghiệm cải tiến đều null, và lời giải thích nhiều khả năng không nằm ở kiến trúc hay hyperparameter mà ở một lỗi trong augmentation khiến gần như mọi mẫu huấn luyện mang một dải đen mà mẫu validation không có. Lỗi này tồn tại suốt 12 lần huấn luyện. Nếu nó đúng là nguyên nhân, thì phần lớn công sức tinh chỉnh của hai tuần qua đã diễn ra trên một nền dữ liệu bị lệch, và việc sửa nó phải đi trước mọi ý tưởng khác.

---

*Research Use Only. Con số trên tập test-104 trong báo cáo này là kết quả của một lần đánh giá duy nhất theo protocol đã khoá trước khi chạy; mọi con số còn lại đo trên tập validation out-of-fold và mang thiên lệch chọn epoch đã nêu rõ ở mục 2.2. Không con số nào trong báo cáo này được dùng để suy diễn về hiệu năng lâm sàng.*
