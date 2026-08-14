# Báo cáo W4: huấn luyện và đánh giá model UniFormer-S 3D dùng trọng số pre-trained Kinetics trên tập test, và UI/UX webapp

**Người thực hiện:** Hoàng Đức Trường
**Ngày tổng hợp:** 14/08/2026
**Kỳ báo cáo:** 08/08 - 14/08/2026
**Trạng thái:** Research Use Only (RUO); không dùng để chẩn đoán hay thay thế bác sĩ.

## Tóm tắt

W3 kết thúc ở macro-F1 **0,6162** trên tập test, và bốn hướng cải tiến đều không cải thiện được kết quả:
(1) đổi sang focal loss
(2) tăng cường dữ liệu mạnh hơn
(3) bỏ nhiễu cường độ riêng theo từng thì MRI
(4) test-time augmentation bằng phép lật
Vấn đề của W3 là mô hình không mã hoá được lớp di căn, và mọi cách chỉnh loss function hay tăng cường dữ liệu đều không chạm tới điều đó.

W4 đổi đúng thứ đó. Mô hình chính chuyển sang một kiến trúc lai convolutional và self-attention, khởi tạo từ trọng số học trên video thay vì huấn luyện từ đầu. Trên 394 bệnh nhân out-of-fold, macro-F1 validation đạt **0,8147** [0,7746; 0,8547], hơn cấu hình cũ **+0,1296** [+0,0778; +0,1809], P < 0,001. Đây là can thiệp đầu tiên của dự án vượt cấu hình cũ, và cả 5 fold lẫn cả 7 lớp đều cải thiện.

Tập test 104 ca được đánh giá **lần thứ hai**, sau khi khoá protocol cho kiến trúc mới: **0,7682** [0,6902; 0,8422], hơn lần cấu hình cũ **+0,1520** [+0,0647; +0,2421], P = 0,001.

Về đóng góp chính, độ tin cậy của xác suất cải thiện rõ: ECE **0,0833** khi chưa hiệu chỉnh gì, so với 0,1303 của W3. Cơ chế từ chối ca không chắc nâng macro-F1 từ 0,768 lên **0,842** khi bỏ 20% ca khó nhất, P = 0,027.

Giao diện người dùng được cải thiện. 

Thời gian suy luận đo trong chính lượt đánh giá test: **81,7 ms** cho một mô hình, **408,5 ms** cho ensemble 5 mô hình.


## 1. Mục tiêu tuần và mức hoàn thành

Mục tiêu W4 theo kế hoạch: chốt mô hình chính bằng cross-validation, thử biến thể fusion và backbone tiền huấn luyện, xử lý lớp hiếm.

| Mục tiêu | Mức hoàn thành | Bằng chứng |
|---|---|---|
| Ít nhất một backbone pre-trained, so với train from scatch | **Đạt**, và là kết quả chính của tuần | 0,8147 so với 0,6851; +0,1296 [+0,0778; +0,1809] |
| Mô hình chính chốt theo cross-validation, tái lập được từ config và seed | **Đạt** | 5 fold cùng seed, cấu hình giống hệt nhau trừ chỉ số fold, đã kiểm chứng trực tiếp |
| Xử lý lớp hiếm: trọng số theo số mẫu hiệu dụng và bộ lấy mẫu cân bằng | **Đạt** | cả hai đã nằm trong cấu hình chính |
| Đánh giá trên tập test | **Đạt** | 0,7682 [0,6902; 0,8422] |


## 2. Mô hình chính

### 2.1. Lý do chọn UniFormer-S 3D với trọng số Kinetics-400

W4 chọn **UniFormer-S 3D khởi tạo từ trọng số pre-trained trên Kinetics-400**. Kinetics-400 là tập dữ liệu video; mô hình đã học trên các đoạn ảnh có cấu trúc không gian - thời gian ba chiều, thay vì bắt đầu từ trọng số ngẫu nhiên. Khi chuyển sang MRI 3D, các đặc trưng đã học không phải là kiến thức chẩn đoán trực tiếp, nhưng chúng là một điểm khởi tạo phù hợp hơn để học các mẫu thay đổi theo ba chiều trong thể tích ảnh với số lượng bệnh nhân hạn chế.

Đây là điểm khác biệt quan trọng so với các thử nghiệm trước của dự án. Từ đầu dự án, mô hình hoặc được huấn luyện từ đầu, hoặc dùng trọng số pre-trained trên ImageNet, là dữ liệu ảnh 2D. Pre-training 2D không học trực tiếp quan hệ theo chiều sâu của thể tích, nên không tạo được lợi ích thực nghiệm rõ ràng trong bài toán này. Ngược lại, Kinetics-400 cung cấp một biểu diễn 3D có sẵn; giá trị của lựa chọn này được kiểm chứng bằng đối chứng out-of-fold, thay vì chỉ suy ra từ sự tương đồng hình thức giữa video và MRI.

### 2.2. Cross-validation 5 fold

Năm lần huấn luyện, mỗi lần 300 epoch, cùng seed, cấu hình giống hệt nhau trừ chỉ số fold. Điều này được kiểm chứng trực tiếp bằng cách so từng khoá của năm bản cấu hình đã lưu, **trước khi** đọc kết quả.

| Fold | n | macro-F1 | κ |
|---|---|---|---|
| 1 | 82 | 0,8111 | 0,7664 |
| 2 | 80 | 0,8196 | 0,8304 |
| 3 | 78 | 0,8293 | 0,8238 |
| 4 | 77 | 0,7496 | 0,7474 |
| 5 | 77 | 0,8524 | 0,8397 |
| **Gộp out-of-fold** | **394** | **0,8147** [0,7746; 0,8547] | **0,8010** [0,7600; 0,8418] |

Trung bình 5 fold là 0,8124 ± 0,0383. Con số báo cáo là bản gộp out-of-fold, cùng lý do như W3.

### 2.3. So với cấu hình cũ

Bootstrap ghép cặp trên cùng 394 bệnh nhân, phân tầng theo lớp, 2000 lần:

| | Hiệu macro-F1 | 95% CI | P |
|---|---|---|---|
| Mô hình mới so với cấu hình cũ | **+0,1296** | [+0,0778; +0,1809] | **< 0,001** |

Cả 5 fold đều dương, từ +0,082 đến +0,191. Cả 7 lớp đều dương:

| Lớp | n | Cấu hình cũ | Mô hình mới | Hiệu |
|---|---|---|---|---|
| ICC | 46 | 0,519 | **0,731** | **+0,212** |
| Áp-xe | 42 | 0,660 | 0,814 | +0,154 |
| Nang | 42 | 0,762 | 0,897 | +0,135 |
| FNH | 36 | 0,761 | 0,895 | +0,134 |
| HCC | 125 | 0,776 | 0,878 | +0,103 |
| Di căn | 40 | 0,488 | **0,576** | **+0,088** |
| U máu | 63 | 0,831 | 0,912 | +0,081 |

Một điểm về phương pháp đáng ghi hơn cả con số: đây là **lần đầu trong dự án một hiệu ứng mạnh lên khi tăng cỡ mẫu**. Đo trên riêng fold 1 cho +0,111; gộp đủ 394 ca cho +0,130. Ba lần trước đều đi ngược chiều, trong đó có hai lần một mức tăng khoảng +0,04 đến +0,07 ở cỡ mẫu nhỏ biến mất hoàn toàn khi chạy đủ 5 fold.

## 3. Đánh giá UniFormer-S 3D trên tập test

**macro-F1 = 0,7682** [0,6902; 0,8422]; κ 0,7333; accuracy 0,7788; n = 104.

So với DenseNet121-3D của W3, bootstrap ghép cặp trên đúng 104 ca đó:

| | macro-F1 | Hiệu | 95% CI | P |
|---|---|---|---|---|
| DenseNet121-3D (W3) | 0,6162 | - | - | - |
| **UniFormer-S 3D + Kinetics-400 (W4)** | **0,7682** | **+0,1520** | [+0,0647; +0,2421] | **0,001** |

Phép so này hợp lệ vì UniFormer-S 3D + Kinetics-400 được chọn hoàn toàn trên dữ liệu out-of-fold, không dùng một thông tin nào của tập test; và việc đọc lại tệp xác suất đã lưu của DenseNet121-3D không phải một lần đánh giá mới.

Tất cả các hàng dưới đây đo trên cùng tập test 104 ca:

| Phương pháp | macro-F1 | κ |
|---|---|---|
| Hạng 1 challenge | 0,8322 | 0,7801 |
| CGHNet (2026) | 0,8180 | 0,7820 |
| Hạng 2 challenge | 0,8078 | 0,7660 |
| STM-Former | 0,7930 | 0,7520 |
| Hạng 3 challenge | 0,7860 | 0,7435 |
| Hạng 4 challenge | 0,7807 | 0,7312 |
| **UniFormer-S 3D + Kinetics-400 (W4)** (ensemble 5 fold) | **0,7682** [0,6902; 0,8422] | 0,7333 |
| Hạng 5 challenge | 0,7609 | 0,7084 |
| **DenseNet121-3D (W3)** | 0,6162 | 0,5647 |
| Baseline ban tổ chức | 0,6083 | 0,5414 |



**Ensemble UniFormer-S 3D có tác dụng thật.** Hiệu so với trung bình 5 mô hình đơn là **+0,0380** [+0,0007; +0,0771], P = 0,048, và ensemble vượt **cả 5** thành viên (mô hình đơn tốt nhất đạt 0,7569). Với ensemble DenseNet121-3D ở W3 thì ngược lại: hiệu chỉ +0,0162 với P = 0,43, và mô hình đơn tốt nhất còn cao hơn ensemble. Trung bình 5 mô hình đơn của UniFormer-S 3D là 0,7302 ± 0,0278.

## 4. Độ tin cậy của xác suất và cơ chế từ chối

*T* được fit trên 394 ca out-of-fold rồi áp mù lên tập test, không bao giờ fit trên test.

| | ECE | MCE | Brier | NLL | Tự tin trung bình |
|---|---|---|---|---|---|
| **Chưa hiệu chỉnh** | **0,0833** | 0,3716 | 0,3075 | 0,6804 | 0,820 (+0,042) |
| Hiệu chỉnh, *T* = 1,35 | 0,0985 | **0,2384** | 0,3025 | 0,6656 | 0,749 (−0,030) |

*(accuracy thật 0,7788; cột cuối kèm độ lệch so với accuracy)*

Ba nhận xét:

- **ECE 0,0833 đạt được mà không hiệu chỉnh gì**, so với 0,1303 của ensemble ở W3 và 0,1534 của mô hình đơn tốt nhất sau hiệu chỉnh. Đây là con số mạnh nhất của phần đóng góp chính cho tới nay.
- Mức tự tin thái quá giảm còn **+0,042**, so với +0,115 ở W3 và +0,186 trên out-of-fold của cấu hình cũ.
- Hiệu chỉnh nhiệt độ **làm ECE xấu đi** trong khi làm MCE tốt lên. Đây là một đánh đổi, không phải một cải thiện, và bản chưa hiệu chỉnh đã được chốt làm số chính **trước** khi chạy chứ không phải chọn sau khi nhìn số.

Cơ chế từ chối, cùng dự đoán, chỉ đổi cách xếp hạng:

| Cách xếp hạng | AURC | F1@100% | F1@90% | F1@80% | F1@70% |
|---|---|---|---|---|---|
| **Xác suất cao nhất** | **0,0494** | 0,7682 | 0,8022 | **0,8421** | 0,8911 |
| Mức bất đồng giữa 5 mô hình | 0,0562 | 0,7682 | 0,8082 | 0,8194 | 0,8685 |

*(mốc đối chiếu: xếp ngẫu nhiên 0,1615; xếp hoàn hảo 0,0140)*

Cách đơn giản hơn thắng, đúng như đã chốt trước. Phát biểu dùng được cho báo cáo và cho giao diện: **từ chối 20% ca khó nhất nâng macro-F1 từ 0,768 lên 0,842**, và ở mức chấp nhận sai số dưới 10% thì hệ thống tự quyết được **76,9%** số ca. Con số tương ứng ở W3 là 29%.

## 5. Nút thắt còn lại

Chẩn đoán lớp yếu **đảo chiều** so với W3. Cấu hình cũ dự đoán *thừa* hai lớp yếu, tức vấn đề nằm ở precision. Mô hình mới đã cân sáu lớp, riêng di căn lật hẳn sang *thiếu*:

| Lớp | Số ca thật | Số ca được đoán | Tỉ lệ | Precision | Recall |
|---|---|---|---|---|---|
| **Di căn** | 40 | **26** | **0,65** | 0,731 | **0,475** |
| FNH | 36 | 40 | 1,11 | 0,850 | 0,944 |
| Nang | 42 | 45 | 1,07 | 0,867 | 0,929 |
| Áp-xe | 42 | 44 | 1,05 | 0,795 | 0,833 |
| HCC | 125 | 130 | 1,04 | 0,862 | 0,896 |
| ICC | 46 | 47 | 1,02 | 0,723 | 0,739 |
| U máu | 63 | 62 | 0,98 | 0,919 | 0,905 |

Mô hình giờ quá dè dặt khi gọi tên di căn: nói ra thì thường đúng, nhưng bỏ sót hơn một nửa. Hệ quả về hướng can thiệp cũng đảo theo: trọng số lớp và hiệu chỉnh prior từng bị loại vì đi sai chiều, nay lại đúng chiều **riêng cho lớp này**. Nhưng chúng vẫn bị chặn bởi cùng một bằng chứng như trước, không ca sai nào có biên quyết định đủ hẹp để một phép dịch ngưỡng lật được. Can thiệp còn khớp phải tác động lúc huấn luyện, không phải lúc suy luận.

Trần số học: nếu sáu lớp còn lại đều đạt 0,95 mà di căn giữ nguyên 0,576 thì macro-F1 cũng chỉ tới **0,896**. **Lớp di căn một mình chặn mốc 0,9.** Trên tập test, lớp này đạt 0,500 với n = 11, và ba hướng nhầm lớn nhất đều đổ về ICC.

Đây không phải giới hạn riêng của nghiên cứu này. Lớp yếu nhất của CGHNet ở mức 0,818 cũng là di căn, và bài báo của họ quy cho số mẫu ít cùng biểu hiện hình ảnh không đồng nhất.

## 6. Các hướng đã thử không hiệu quả

| Thí nghiệm | Hiệu macro-F1 | 95% CI | P |
|---|---|---|---|
| Bản tái lập CGHNet, đủ 5 fold | −0,019 | [−0,068; +0,031] | 0,46 |
| Gộp xác suất cấu hình cũ với bản tái lập CGHNet | −0,010 | [−0,039; +0,018] | 0,47 |

Ngoài ra, gộp mô hình mới với cấu hình cũ làm **tệ đi ở mọi trọng số** đã thử, từ 0,7349 khi chia đều tới 0,8129 khi mô hình mới chiếm 90%, đều thấp hơn 0,8147 của mô hình mới đứng một mình.

## 7. Giao diện đọc kết quả

### 7.1. Kiến trúc và luồng làm việc

Giao diện được dựng lại trong tuần thành một **bàn đọc MRI ba cột**: dữ liệu đầu vào bên trái, ảnh ở trung tâm, kết quả mô hình bên phải. Có hai theme sáng và tối; vùng ảnh **luôn giữ nền đen** kể cả khi giao diện đang ở theme sáng.

Luồng làm việc một chiều: thả một tệp ZIP, hệ thống kiểm 8 chuỗi MRI và 8 nhãn vùng tổn thương tương ứng, rồi chạy ensemble 5 mô hình trực tiếp trên máy chủ. Sau khi có kết quả, người dùng xem được đủ 8 thì của ảnh gốc và bật tắt nhãn tổn thương.

### 7.2. Thời gian xử lý một ca

Thời gian dưới đây tính từ khi hệ thống nhận dữ liệu MRI đến khi trả kết quả phân loại cho một ca.

| Môi trường chạy | Phạm vi | Thời gian một ca |
|---|---|---|
| **CPU laptop** | Đọc và kiểm tra dữ liệu, tiền xử lý 8 chuỗi MRI, suy luận ensemble 5 mô hình, trả kết quả phân loại | **khoảng 18 - 22 giây** |
| **GPU Tesla T4** | Toàn bộ pipeline, gồm tiền xử lý trên CPU và suy luận ensemble 5 mô hình trên GPU | **khoảng 3,8 - 5,2 giây** |

## 8. Công việc tiếp theo

1. Hoàn thiện UI/UX của web app: loại bỏ các luồng chức năng không còn dùng, cập nhật giao diện theo kết quả UniFormer-S 3D, và kiểm tra lại toàn bộ trạng thái tải dữ liệu, xử lý và trả kết quả.
2. Chạy thí nghiệm intra-class mixup, tức trộn hai ca thuộc cùng một chẩn đoán trong lúc huấn luyện, rồi so ghép cặp với cấu hình UniFormer-S 3D hiện tại trên out-of-fold.
3. Huấn luyện các biến thể UniFormer lớn hơn, trước hết là UniFormer-Base hoặc UniFormer V2, để kiểm tra liệu năng lực mô hình bổ sung có tiếp tục cải thiện kết quả hay không.

## 9. Timeline

| Thời điểm | Mốc |
|---|---|
| 10/08/2026 | Bộ chẩn đoán lớp yếu chạy trên xác suất đã lưu, loại bảy hướng cải tiến trước khi tốn giờ GPU; dựng hai nhánh train độc lập. |
| 11/08/2026 | Bản tái lập CGHNet đủ 5 fold cho kết quả âm; dựng nhánh mô hình mới. |
| 12/08/2026 | Fold đầu tiên của mô hình mới đạt 0,8111, vượt cấu hình cũ; cải tiến giao diện đọc MRI ba cột và thêm kiểm tra tệp ZIP tải lên. |
| 13/08/2026 | Giao diện chạy suy luận trực tiếp trên bộ ảnh tải lên; cài phép trộn hai ca cùng chẩn đoán. |
| 14/08/2026 | Đủ 5 fold, gộp out-of-fold **0,8147**; khoá protocol và **đánh giá tập test: 0,7682**; đo inference latency. |

## Kết luận

W4 giải được nút thắt mà W3 để lại. Chẩn đoán cuối W3 nói ràng buộc nằm ở biểu diễn đặc trưng chứ không ở siêu tham số, và can thiệp đúng vào chỗ đó đã đưa macro-F1 trên tập test từ 0,6162 lên **0,7682**.

Về đóng góp chính, cả hai nhánh đều mạnh lên. Xác suất đạt ECE 0,0833 mà không cần hiệu chỉnh, tốt hơn mọi con số trước đó kể cả sau hiệu chỉnh. Cơ chế từ chối nâng macro-F1 lên 0,842 khi bỏ 20% ca khó nhất, và tự quyết được 76,9% số ca ở mức chấp nhận sai số dưới 10%.
