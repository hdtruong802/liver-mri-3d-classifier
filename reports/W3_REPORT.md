# Báo cáo W3: cross-validation, độ tin cậy của xác suất, và đánh giá trên tập test

**Người thực hiện:** Hoàng Đức Trường
**Ngày tổng hợp:** 07/08/2026
**Kỳ báo cáo:** 01/08 – 07/08/2026
**Trạng thái:** Research Use Only (RUO); không dùng để chẩn đoán hay thay thế bác sĩ.

## Tóm tắt

W2 kết thúc với macro-F1 0,7001 trên tập validation của một fold. W3 trả lời hai câu hỏi còn bỏ ngỏ: con số đó có đứng được trên đủ 5 fold không, và nó tương ứng bao nhiêu trên tập test thật.

Gộp out-of-fold 394 bệnh nhân cho **0,6851** [0,6394; 0,7308]. Tập test 104 ca giữ kín, sau khi khoá protocol và đánh giá đúng một lần, cho **0,6162** [0,5246; 0,7032], ngang mốc baseline của ban tổ chức challenge.

Phần đóng góp chính có số đầy đủ lần đầu: xác suất được hiệu chỉnh và cơ chế từ chối ca không chắc. Bỏ 20% ca mà mô hình ít chắc nhất, macro-F1 trên phần còn lại tăng **+0,070** [+0,015; +0,124], P = 0,016.

Bốn hướng cải tiến thử trong tuần đều không có ý nghĩa thống kê. Cuối tuần phát hiện một lỗi trong khâu tăng cường dữ liệu, tồn tại suốt 12 lần huấn luyện, và đây là giả thuyết mạnh nhất giải thích cả bốn kết quả đó.

Thời gian xử lý một ca mới, đo end-to-end: **3,46 – 4,9 giây**.

## 1. Mục tiêu tuần và mức hoàn thành

Mục tiêu W3: biến baseline một fold thành bảng cross-validation có khoảng tin cậy, thêm biến thể fusion, và dựng hạ tầng đánh giá ngoài miền.

| Mục tiêu | Mức hoàn thành | Bằng chứng |
|---|---|---|
| Baseline 3D chạy đủ 5-fold, bảng macro-F1 và κ kèm 95% CI | **Đạt** | 0,6851 [0,6394; 0,7308] · κ 0,6419 · 394 bệnh nhân |
| Fusion v0 (ghép 8 thì thành 8 kênh) so với baseline | **Không áp dụng** | cách ghép này chính là baseline hiện tại; biến thể dùng chung encoder cho từng thì đã dựng xong nhưng chưa chạy |
| Rigid registration | **Chưa làm** | cách căn hiện tại chỉ khử tịnh tiến, chưa khử xoay và biến dạng |
| Dữ liệu ngoài miền và OOD probe | **Đã cắt khỏi phạm vi** | không đủ thời gian trong tuần, và giá trị giảm sau khi có kết quả test |
| Bộ đánh giá thuần, tách khỏi vòng huấn luyện | **Đạt** | chạy lại được trên checkpoint cũ, chỉ cần CPU |

Ngoài kế hoạch, tuần này còn hoàn thành: đánh giá trên tập test (dự kiến ban đầu là W5), đo calibration và selective prediction trên đủ 394 ca, MC-dropout, Grad-CAM 3D, và web app demo chạy số thật out-of-fold thay cho số giả lập.

## 2. Cross-validation 5-fold

Năm lần huấn luyện, mỗi lần 300 epoch, cùng seed, cấu hình giống hệt nhau trừ chỉ số fold. Năm tập validation phân hoạch sạch 394 ca, đã kiểm chứng giao mọi cặp bằng rỗng.

| Fold | n | macro-F1 | κ |
|---|---|---|---|
| 1 | 82 | 0,7001 | 0,6465 |
| 2 | 80 | 0,6771 | 0,6273 |
| 3 | 78 | 0,7304 | 0,6772 |
| 4 | 77 | 0,6680 | 0,6548 |
| 5 | 77 | 0,6618 | 0,6031 |
| **Gộp out-of-fold** | **394** | **0,6851** [0,6394; 0,7308] | **0,6419** [0,5907; 0,6940] |

Trung bình 5 fold là 0,6875 ± 0,0281. Con số báo cáo là bản gộp out-of-fold chứ không phải trung bình này, vì trung bình các fold không có khoảng tin cậy đúng nghĩa khi mỗi fold là một tập nhỏ khác nhau.

**Thiên lệch do cách chọn checkpoint: +0,079.** Checkpoint tốt nhất được chọn theo macro-F1 trên chính tập validation đang báo. Đo trên cùng 312 ca, checkpoint tốt nhất cho 0,6824 còn epoch cuối cho 0,6038. Con số 0,6851 vì thế lệch lạc quan khoảng 0,079, và điều này được ghi nhận ngay khi đo được, trước khi đánh giá trên test.

**Hai lớp yếu, nhất quán ở cả 5 fold:** di căn 0,488 (n=40) và ICC 0,519 (n=46); các lớp còn lại từ 0,66 đến 0,83. Ba hướng nhầm lớn nhất: HCC thành di căn 15 ca, ICC thành áp-xe 10 ca, HCC thành ICC 9 ca.

## 3. Độ tin cậy của xác suất và cơ chế từ chối

### 3.1. Calibration

Nhiệt độ được fit theo kiểu leave-one-fold-out: giá trị *T* áp lên một fold học từ 4 fold còn lại, nên không ca nào được hiệu chỉnh bởi một *T* đã nhìn thấy nó.

| | ECE | MCE | Brier | NLL | Tự tin trung bình |
|---|---|---|---|---|---|
| Chưa hiệu chỉnh | 0,2030 | 0,6775 | 0,5488 | 2,0308 | 0,889 (+0,186) |
| Hiệu chỉnh, fit theo NLL | 0,1756 | 0,8026 | 0,5228 | **1,1687** | 0,606 (−0,097) |
| Hiệu chỉnh, fit theo ECE | **0,1534** | **0,3510** | **0,5162** | 1,2812 | 0,745 (+0,042) |

*(accuracy thật 0,7030; cột cuối kèm độ lệch so với accuracy)*

Ba nhận xét:
- Thứ nhất, mô hình tự tin thái quá nghiêm trọng: tự tin trung bình 0,889 trong khi chỉ đúng 70,3%, trung vị 0,987.
- Thứ hai, giá trị *T* tối ưu theo NLL khác hẳn *T* tối ưu theo ECE, và chọn nhầm sẽ đẩy mô hình sang thiếu tự tin.
- Thứ ba, một tham số vô hướng là không đủ: ngay cả *T* tốt nhất cũng chỉ hạ ECE xuống 0,153.

### 3.2. Cơ chế từ chối ca không chắc

Xếp hạng theo xác suất cao nhất của một mô hình đơn gần như không có tác dụng trên out-of-fold: macro-F1 tại coverage 80% là 0,6813, không hơn 0,6851 ở coverage 100%.

MC-dropout với 20 lượt mỗi ca hạ macro-F1 xuống 0,5852 nên không dùng làm bộ dự đoán, nhưng ECE của nó là 0,1216, tốt hơn cả temperature scaling. Cách dùng có giá trị là phép lai: dự đoán lấy từ mô hình tất định, còn thứ tự từ chối lấy từ mức bất đồng giữa các lượt.

| Cách xếp hạng | AURC | F1@100% | F1@90% | F1@80% | F1@70% |
|---|---|---|---|---|---|
| Xác suất cao nhất | 0,2059 | 0,6851 | 0,6909 | 0,6799 | 0,7043 |
| **Mức bất đồng** | **0,1689** | 0,6851 | 0,6923 | **0,7222** | 0,7367 |

Bootstrap ghép cặp 2000 lần, phân tầng ở mức bệnh nhân:

| | Hiệu | 95% CI | P |
|---|---|---|---|
| F1@80% theo bất đồng, so với F1@100% | **+0,0350** | [+0,0039; +0,0647] | **0,030** |
| AURC theo bất đồng, so với xác suất cao nhất | **−0,0346** | [−0,0648; −0,0080] | **0,013** |
| Đối chứng: F1@80% theo xác suất cao nhất | −0,0027 | [−0,0340; +0,0263] | 0,88 |

Dòng đối chứng mang cả lập luận: cùng mô hình, cùng dự đoán, chỉ đổi cách xếp hạng.

### 3.3. Khả năng giải thích

Heatmap trên 4 ca minh hoạ. Hai ca đoán đúng có đỉnh chú ý nằm đúng tâm tổn thương, tức mô hình nhìn vào tổn thương chứ không vào rìa ảnh. Một ca đoán sai cho thấy cả hai dấu hiệu thất bại cùng lúc: đỉnh chú ý nằm ở lát biên, lệch 32 voxel khỏi tâm, và bản đồ ứng với lớp đúng bị suy biến, tức không vùng nào ủng hộ đáp án đúng. Hai thì chemical-shift có độ nhạy thấp nhất ở cả 4 ca, phù hợp với lâm sàng vì chúng chủ yếu để phát hiện mỡ.

Cần nói rõ giới hạn: bản đồ ở độ phân giải gốc chỉ 7×7×2, cỡ mẫu là 4 ca, và đây là phân tích độ nhạy chứ không phải ablation, nên không kết luận được bỏ hẳn một thì thì mất bao nhiêu điểm.

## 4. Đánh giá trên tập test khoá kín

### 4.1. Protocol

Tập test 104 ca được giữ kín và chỉ đánh giá một lần. Trước khi chạy, toàn bộ lựa chọn được ghi thành văn bản và khoá lại: cấu hình mô hình, bộ dự đoán là ensemble 5 fold, không dùng test-time augmentation, nhiệt độ *T* fit trên out-of-fold rồi áp mù, danh sách metric, các mức coverage.

Ensemble 5 fold hợp lệ ở đây vì không mô hình nào trong 5 mô hình từng nhìn thấy 104 ca này; trên out-of-fold thì cách gộp đó bị cấm.

### 4.2. Kết quả

**macro-F1 = 0,6162** [0,5246; 0,7032] · κ 0,5647 · accuracy 0,6346 · n = 104.

Tất cả các hàng dưới đây đo trên cùng một tập test 104 ca:

| Phương pháp | macro-F1 | κ |
|---|---|---|
| Hạng 1 challenge | 0,8322 | 0,7801 |
| CGHNet (2026) | 0,8180 | 0,7820 |
| Hạng 2 challenge | 0,8078 | 0,7660 |
| Hạng 3 challenge | 0,7860 | 0,7435 |
| **Nghiên cứu này** (ensemble 5 fold) | **0,6162** [0,5246; 0,7032] | 0,5647 |
| Baseline ban tổ chức | 0,6083 | 0,5414 |

Con số của nghiên cứu cao hơn baseline ban tổ chức đúng 0,0038, trong khi khoảng tin cậy rộng ±0,09 và phủ trùm con số đó. Phát biểu đúng là **ngang baseline, chưa phân biệt được về mặt thống kê**.

Kết quả từng lớp: u máu 0,903 · nang 0,762 · HCC 0,679 · FNH 0,640 · áp-xe 0,538 · ICC 0,519 · **di căn 0,273**. Hướng nhầm chính giống hệt out-of-fold: HCC bị đoán thành di căn, 6 trong 32 ca HCC. Ngay cả khi 5 lớp còn lại đều đạt 0,90, macro-F1 cũng chỉ tới **0,756**; muốn vượt mốc đó thì bắt buộc phải cải thiện hai lớp yếu.

### 4.3. Ba kết quả đáng chú ý

**Thiên lệch chọn checkpoint được xác nhận về mặt định lượng.** Out-of-fold cho 0,6851, test cho 0,6162, hụt 0,069. Thiên lệch đo được trước khi đánh giá test là +0,079. Hai con số gần trùng khít, nghĩa là phần lạc quan của out-of-fold đúng bằng phần đã được chỉ ra, không có nguồn thổi phồng nào khác.

**Ensemble gần như không giúp:** hiệu so với trung bình 5 mô hình đơn là +0,0162 [−0,0232; +0,0560], P = 0,43. Mô hình đơn tốt nhất đạt 0,6308, cao hơn cả ensemble; con số đó không được dùng làm kết quả vì chọn nó sau khi nhìn tập test là chọn trên tập test.

**Cơ chế từ chối có tác dụng, nhưng không cần đến MC-dropout.** Trên test, xếp hạng theo mức bất đồng giữa 5 mô hình không hơn cách lấy xác suất cao nhất (hiệu AURC +0,0009, P = 0,90), trong khi cả hai đều hiệu quả thật:

| | Hiệu so với F1@100% | 95% CI | P |
|---|---|---|---|
| Xác suất cao nhất, coverage 80% | **+0,0696** | [+0,0154; +0,1245] | **0,016** |
| Mức bất đồng, coverage 80% | **+0,0970** | [+0,0466; +0,1451] | **<0,001** |
| Xác suất cao nhất, coverage 70% | +0,1267 | [+0,0568; +0,1859] | 0,002 |

Khác biệt so với kết quả ở mục 3.2 đến từ chỗ này: trên out-of-fold, "ensemble" chỉ là MC-dropout trên một mô hình tự tin thái quá nên xác suất của nó vô dụng, còn với 5 mô hình độc lập thì trung bình xác suất đã là tín hiệu bất định tốt. Phát biểu đúng: **từ chối 20% ca khó nâng macro-F1 từ 0,616 lên khoảng 0,68 đến 0,72.**

Một phát hiện đi kèm về calibration: ensemble **chưa hiệu chỉnh** cho ECE 0,1303, tốt hơn cả mô hình đơn đã temperature scaling tốt nhất trên out-of-fold (0,1534). Ngược lại, áp *T* = 2,10 học từ out-of-fold lên ensemble làm ECE xấu đi (0,1902), đúng như đã dự đoán khi khoá protocol.

## 5. Các hướng đã thử không hiệu quả

Tất cả đo trên out-of-fold, bootstrap ghép cặp trên cùng bệnh nhân:

| Thí nghiệm | Hiệu macro-F1 | 95% CI | P |
|---|---|---|---|
| Focal loss (γ=2) | −0,029 | [−0,105; +0,048] | 0,47 |
| Tăng cường dữ liệu mạnh hơn | −0,014 | [−0,078; +0,052] | 0,68 |
| Bỏ nhiễu cường độ theo thì | −0,002 | [−0,042; +0,036] | 0,92 |
| Test-time augmentation bằng phép lật | −0,015 | [−0,035; +0,004] | 0,15 |

Ba điểm rút ra:

**Focal loss không cần thiết vì một lý do cụ thể:** Nó có làm mô hình bớt tự tin từ đầu (ECE thô 0,154 so với 0,221), nhưng sau khi hiệu chỉnh đúng cách thì hai bên bằng nhau: 0,1255 và 0,1281. Lợi thế biến mất qua đúng bước mà pipeline vốn đã làm.

**Sàng lọc trên 2 fold là không đủ:** Thí nghiệm bỏ nhiễu cường độ cho +0,038 khi chạy 2 fold, rồi −0,002 khi chạy đủ 5 fold; toàn bộ mức tăng đến từ một fold may mắn. Từ nay mọi thí nghiệm chạy đủ 5 fold trước khi kết luận.

**Nút thắt là thời điểm mô hình bắt đầu học thuộc:** Trên cả 10 lần huấn luyện, epoch mà hàm mất mát trên validation chạm đáy dự báo gần trọn vẹn macro-F1 cuối cùng của fold đó: tương quan hạng Spearman ρ = +0,770, P = 0,0092. Đây là tương quan trên 10 lần chạy và hai đại lượng cùng sinh từ một đường cong, nên là một chẩn đoán tốt chứ chưa phải bằng chứng nhân quả.

**Lỗi phát hiện chiều 07/08:** Trong khâu tăng cường dữ liệu, phép tịnh tiến lấp phần trống bằng giá trị 0 và phép xoay lấp góc bằng 0. Hệ quả: khoảng 100% mẫu huấn luyện mang một dải đen ở rìa, trong khi 0% mẫu validation có. Đây là lệch phân bố train/validation có hệ thống, xuất hiện ở mọi bước huấn luyện, và khớp với chẩn đoán ở trên. Cách làm chuẩn của baseline ban tổ chức và của CGHNet là cắt ngẫu nhiên từ một khối rộng hơn, không đệm; ablation của CGHNet cho thấy bỏ phép cắt ngẫu nhiên làm mất 8,8 điểm. Có một bằng chứng độc lập cùng hướng: mô hình mất 0,02 đến 0,06 điểm khi ảnh bị lật, dù chính augmentation của nó lật cả ba trục. Bản sửa đã dựng xong, chưa chạy.

## 6. Thời gian xử lý một ca

| Thành phần | Thời gian | Thiết bị |
|---|---|---|
| Tiền xử lý: đọc 8 chuỗi ảnh, resample lên lưới chung, căn thì, chuẩn hoá | 3,43s (trung vị) – 4,74s (p90) | CPU |
| Suy luận, 1 mô hình | 32,9 ms | GPU Tesla T4 |
| Suy luận, ensemble 5 fold | 164,7 ms | GPU Tesla T4 |
| **Tổng end-to-end một ca mới** | **3,46 – 4,9 giây** | |

Tiền xử lý chiếm khoảng 96% thời gian chờ, nên muốn giảm độ trễ thì phải tối ưu khâu này chứ không phải khâu mô hình. Việc dùng ensemble 5 mô hình thay vì 1 chỉ tốn thêm khoảng 130 ms, tức không phải ràng buộc thực tế.

## 7. Giới hạn

1. **Con số out-of-fold 0,6851 không phải ước lượng không thiên lệch**, vì nó mang thiên lệch chọn checkpoint +0,079. Con số trung thực hơn là 0,6038.
2. **Trần 0,756 là ràng buộc số học**, không phải phỏng đoán: không có cách nào vượt nó mà không cải thiện hai lớp di căn và ICC.
3. **Bốn kết quả âm có thể do bộ đo quá yếu chứ không hẳn do ý tưởng sai.** Bản sàng 2 fold có n = 162 và khoảng tin cậy khoảng ±0,08, không đủ lực phát hiện hiệu ứng cỡ +0,03.
4. **Cách căn các thì hiện tại chỉ khử tịnh tiến**, không khử xoay và biến dạng.

## 8. Công việc tiếp theo

1. Sửa lỗi tăng cường dữ liệu, build lại cache và chạy đủ 5 fold. Việc này phải đi trước vì nó đổi dữ liệu đầu vào.
2. Thử làm trơn trọng số theo thời gian trên cấu hình thắng ở bước 1.
3. Chạy biến thể fusion dùng chung encoder cho từng thì kèm cơ chế chú ý theo thì, có đối chứng cùng độ phân giải. Đây là hướng còn tiềm năng nhất để vượt mức 0,75.
4. Chạy lại focal loss trên đủ 5 fold; thử backbone tiền huấn luyện và hình học đầu vào nông hơn.
5. Phân tích false positive của ICC và di căn để biết nút thắt do dữ liệu nhập nhằng hay do mô hình chưa dùng hết tín hiệu.
6. Hình cho báo cáo, kiểm định thống kê giữa các mô hình, gói tái lập.
7. Khoá cấu hình cuối cùng rồi đánh giá trên tập test lần thứ hai.

## 9. Timeline

| Thời điểm | Mốc |
|---|---|
| 01/08/2026 | Hoàn thiện giao diện đọc kết quả của web app demo. |
| 04/08/2026 | Cross-validation 5-fold hoàn tất, gộp out-of-fold 0,6851; đo calibration và selective prediction; MC-dropout và phép lai; web app nối số thật. |
| 05/08/2026 | Focal loss không hiệu quả; bản đồ vùng chú ý và độ nhạy theo thì trên 4 ca; hai thí nghiệm augmentation đều không hiệu quả trên bản sàng. |
| 06/08/2026 | Xác nhận kết quả null trên đủ 5 fold; phát hiện tương quan ρ = 0,770 giữa thời điểm bắt đầu học thuộc và điểm cuối. |
| 07/08/2026 | Test-time augmentation cho kết quả âm; **đánh giá trên tập test: 0,6162**; phát hiện lỗi trong khâu tăng cường dữ liệu; đo thời gian xử lý một ca. |

## Kết luận

W3 biến một con số sàng lọc thành một con số so sánh được trực tiếp với benchmark, và con số đó khiêm tốn hơn kỳ vọng: 0,6162 trên tập test, ngang mốc baseline của ban tổ chức, còn cách khoảng 0,20 so với các phương pháp công bố gần đây.

Về đóng góp chính, cơ chế từ chối ca không chắc đã chứng minh được là có tác dụng thật trên tập test giữ kín: bỏ 20% ca khó nhất nâng macro-F1 từ 0,616 lên khoảng 0,68 đến 0,72, có ý nghĩa thống kê. Xác suất thì vẫn chưa đủ tin cậy, với ECE tốt nhất là 0,130, và nó đến từ việc gộp mô hình chứ không từ temperature scaling.

Bốn hướng cải tiến đều không hiệu quả, và lời giải thích nhiều khả năng không nằm ở kiến trúc hay siêu tham số mà ở một lỗi trong khâu tăng cường dữ liệu khiến gần như mọi mẫu huấn luyện mang một dải đen mà mẫu validation không có.
