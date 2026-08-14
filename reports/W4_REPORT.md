# Báo cáo W4: mô hình chính, đánh giá lần hai trên tập test, và giao diện đọc kết quả

**Người thực hiện:** Hoàng Đức Trường
**Ngày tổng hợp:** 14/08/2026
**Kỳ báo cáo:** 08/08 – 14/08/2026
**Trạng thái:** Research Use Only (RUO); không dùng để chẩn đoán hay thay thế bác sĩ.

## Tóm tắt

W3 kết thúc ở macro-F1 **0,6162** trên tập test, ngang mốc baseline của ban tổ chức challenge, và bốn hướng cải tiến đều không có ý nghĩa thống kê. Chẩn đoán cuối W3 chỉ ra ràng buộc nằm ở **biểu diễn đặc trưng** chứ không ở siêu tham số: mô hình không mã hoá được lớp di căn, và mọi cách chỉnh hàm mất mát hay tăng cường dữ liệu đều không chạm tới điều đó.

W4 đổi đúng thứ đó. Mô hình chính chuyển sang một kiến trúc lai tích chập và tự chú ý, khởi tạo từ trọng số học trên video thay vì huấn luyện từ đầu. Trên 394 bệnh nhân out-of-fold, macro-F1 đạt **0,8147** [0,7746; 0,8547], hơn cấu hình cũ **+0,1296** [+0,0778; +0,1809], P < 0,001. Đây là can thiệp đầu tiên của dự án vượt cấu hình cũ có ý nghĩa thống kê, và cả 5 fold lẫn cả 7 lớp đều cải thiện.

Tập test 104 ca được đánh giá **lần thứ hai** sau khi khoá protocol mới: **0,7682** [0,6902; 0,8422], hơn lần chạm thứ nhất **+0,1520** [+0,0647; +0,2421], P = 0,001. Con số này vượt baseline ban tổ chức một cách có ý nghĩa thống kê, điều mà W3 chưa nói được.

Về đóng góp chính, độ tin cậy của xác suất cải thiện rõ: ECE **0,0833** khi chưa hiệu chỉnh gì, so với 0,1303 của W3. Cơ chế từ chối ca không chắc nâng macro-F1 từ 0,768 lên **0,842** khi bỏ 20% ca khó nhất, P = 0,027.

Giao diện demo được dựng lại thành một bàn đọc MRI ba cột, chạy suy luận trực tiếp trên bộ ảnh người dùng tải lên. Thời gian suy luận đo trong chính lượt đánh giá test: **81,7 ms** cho một mô hình, **408,5 ms** cho ensemble 5 mô hình.

Một dự đoán được ghi trước khi chạy test đã sai, và mục 3.3 nêu rõ nó sai ở đâu.

## 1. Mục tiêu tuần và mức hoàn thành

Mục tiêu W4 theo kế hoạch: chốt mô hình chính bằng cross-validation, thử biến thể fusion và backbone tiền huấn luyện, xử lý lớp hiếm.

| Mục tiêu | Mức hoàn thành | Bằng chứng |
|---|---|---|
| Ít nhất một backbone tiền huấn luyện, so với huấn luyện từ đầu | **Đạt**, và là kết quả chính của tuần | 0,8147 so với 0,6851; +0,1296 [+0,0778; +0,1809] |
| Mô hình chính chốt theo cross-validation, tái lập được từ config và seed | **Đạt** | 5 fold cùng seed, cấu hình giống hệt nhau trừ chỉ số fold, đã kiểm chứng trực tiếp |
| Xử lý lớp hiếm: trọng số theo số mẫu hiệu dụng và bộ lấy mẫu cân bằng | **Đạt** | cả hai đã nằm trong cấu hình chính |
| Fusion v1 dùng chung encoder cho từng thì kèm cơ chế chú ý theo thì | **Chưa chạy** | đã dựng xong và có cổng kiểm hình dạng, nhưng bị hướng có kỳ vọng cao hơn chiếm chỗ trong ngân sách GPU |
| Arm 3D full-volume với sliding-window | **Đã cắt khỏi phạm vi** | giá trị giảm sau khi biết hình học cắt bám tổn thương mới là yếu tố quyết định |

Ngoài kế hoạch, tuần này còn hoàn thành **đánh giá trên tập test**, vốn dự kiến ở W5. Lý do đẩy sớm: mô hình chính đã chốt xong từ giữa tuần, và một con số so được với văn liệu có giá trị hơn khi nó đến sớm để định hướng hai tuần còn lại.

## 2. Mô hình chính

### 2.1. Vì sao hướng này khác các hướng đã bị loại

Cuối W3 và đầu W4, một bộ chẩn đoán chạy trên xác suất đã lưu của cấu hình cũ đã **loại bảy hướng cải tiến** trước khi tốn một giờ GPU nào. Ba bằng chứng chính:

- Hai lớp yếu nhất đang bị mô hình dự đoán **thừa**, không phải thiếu, nên trọng số lớp và hiệu chỉnh prior đi sai chiều.
- Trong 117 ca sai chỉ có **1 ca** có biên quyết định dưới 0,10, nên ngưỡng và hiệu chỉnh nhiệt độ không lật được ca nào.
- Trong 20 ca di căn bị đoán sai, **không một ca nào** có lớp đúng ở vị trí thứ hai. Tức thông tin để phân biệt lớp này không tồn tại trong biểu diễn, chứ không phải tồn tại mà bị xếp sai hạng.

Điểm thứ ba là điểm quyết định. Nó nói ràng buộc nằm ở biểu diễn, và trong toàn bộ danh mục can thiệp thì **khởi tạo từ trọng số tiền huấn luyện là cách duy nhất đổi được biểu diễn**. Dự án chưa từng thử đúng cách: một lần dùng trọng số từ bài toán segmentation, yếu hơn nhiều và vướng lỗi cấu hình.

Có thêm một mốc đối chiếu ngoài rất mạnh. Baseline chính thức của challenge dùng **đúng kiến trúc này**, huấn luyện từ đầu, đạt 0,6083. Đội xếp hạng hai dùng cùng kiến trúc kèm trọng số video và một cụm kỹ thuật huấn luyện, đạt 0,8078. Cùng kiến trúc, chênh khoảng 0,20 — không mốc nào khác trong văn liệu của bộ dữ liệu này tách được một cụm biến với biên độ như vậy.

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

**Thiên lệch do cách chọn checkpoint: +0,0797** [+0,0419; +0,1213]. Đây là mức gần như giống hệt cấu hình cũ (+0,079). Một kết quả đo trên riêng fold 1 giữa tuần cho +0,042 và đã được ghi là "thấp nhất trong ba cấu hình"; con số đó **không sống sót** qua đủ 394 ca. Ba khẳng định phụ trợ khác rút ra từ một fold cũng không sống sót, và điều này được nêu lại ở mục 9.

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

## 3. Đánh giá trên tập test, lần thứ hai

### 3.1. Protocol và cách chống tự lừa

**Tập test 104 ca đã được nhìn một lần ở W3.** Lần đánh giá này là **lần thứ hai**, được cho phép sau khi mô hình chính đổi, và mọi con số ở mục này phải được đọc kèm điều đó.

Trước khi chạy, toàn bộ lựa chọn được ghi thành văn bản và commit: cấu hình mô hình, mã băm của cả 5 checkpoint, bộ dự đoán là ensemble 5 fold, cách hiệu chỉnh xác suất, điểm dùng để xếp hạng từ chối, danh sách metric, các mức coverage, và một ước lượng bằng số cho kết quả sắp đo.

Điểm khác biệt so với một lời cam kết thông thường: **quan hệ "protocol có trước kết quả" là kiểm được**. Chương trình đánh giá từ chối chạy nếu văn bản protocol chưa được commit, và nó ghi mã commit của văn bản đó vào tệp kết quả. Ai đọc lại về sau đều đối chiếu được hai thứ ấy mà không cần tin vào lời kể.

Hai lựa chọn được **đổi có chủ đích** so với lần chạm thứ nhất, và cả hai chỉ dựa trên dữ liệu out-of-fold:

| | Lần thứ nhất | Lần thứ hai | Căn cứ |
|---|---|---|---|
| Số chính về độ tin cậy xác suất | bản đã hiệu chỉnh | **bản chưa hiệu chỉnh** | mô hình mới chỉ cần *T* = 1,45–1,53 thay vì 2,05–3,26; hiệu chỉnh thêm làm sai số cực đại xấu đi 74% |
| Cách xếp hạng từ chối | mức bất đồng giữa các mô hình | **xác suất cao nhất** | lần chạm thứ nhất đã cho thấy hai cách không khác nhau (P = 0,90) trong khi cách đơn giản hơn vẫn hiệu quả |

### 3.2. Kết quả và vị trí so với văn liệu

**macro-F1 = 0,7682** [0,6902; 0,8422] · κ 0,7333 · accuracy 0,7788 · n = 104.

So với lần chạm thứ nhất, bootstrap ghép cặp trên đúng 104 ca đó:

| | macro-F1 | Hiệu | 95% CI | P |
|---|---|---|---|---|
| Lần thứ nhất | 0,6162 | — | — | — |
| **Lần thứ hai** | **0,7682** | **+0,1520** | [+0,0647; +0,2421] | **0,001** |

Phép so này hợp lệ vì mô hình mới được chọn hoàn toàn trên dữ liệu out-of-fold, không dùng một thông tin nào của tập test; và việc đọc lại tệp xác suất đã lưu của lần trước không phải một lần đánh giá mới.

Tất cả các hàng dưới đây đo trên cùng tập test 104 ca:

| Phương pháp | macro-F1 | κ |
|---|---|---|
| Hạng 1 challenge | 0,8322 | 0,7801 |
| CGHNet (2026) | 0,8180 | 0,7820 |
| Hạng 2 challenge | 0,8078 | 0,7660 |
| STM-Former | 0,7930 | 0,7520 |
| **Nghiên cứu này** (ensemble 5 fold) | **0,7682** [0,6902; 0,8422] | 0,7333 |
| Uniformer trong bảng CGHNet | 0,7190 | 0,6730 |
| ResNet3D trong bảng CGHNet | 0,7090 | 0,6620 |
| Baseline ban tổ chức | 0,6083 | 0,5414 |
| **Nghiên cứu này ở W3** | 0,6162 | 0,5647 |

Hai phát biểu cần viết chính xác:

- **Được phép:** kết quả vượt baseline ban tổ chức một cách có ý nghĩa thống kê, vì cận dưới của khoảng tin cậy là 0,690, cao hơn 0,6083. W3 **không** nói được câu này: hồi đó con số cao hơn baseline đúng 0,0038 với khoảng tin cậy phủ trùm.
- **Không được phép:** nói ngang hạng 2, ngang CGHNet, hay tiệm cận SOTA. Khoảng tin cậy rộng khoảng ±0,09 nên không loại được bất kỳ mốc nào từ 0,709 trở lên. Định vị đúng là: **trên baseline ban tổ chức, dưới các phương pháp công bố gần đây, và với n = 104 thì chưa phân biệt được với nhóm 0,71 đến 0,83.**

### 3.3. Ba điều đáng chú ý

**Ước lượng ghi trước đã trúng, và mức hụt nhỏ hơn dự đoán.** Văn bản protocol ghi khoảng hợp lý là 0,72 đến 0,79, tính bằng cách lấy con số out-of-fold trừ đi mức hụt đã quan sát ở W3.

| | Out-of-fold | Test | Mức hụt |
|---|---|---|---|
| Cấu hình cũ (W3) | 0,6851 | 0,6162 | −0,069 |
| **Mô hình mới** | 0,8147 | **0,7682** | **−0,047** |

Thiên lệch chọn checkpoint của hai bên gần bằng nhau, +0,079 và +0,080, nên phần chênh lệch giữa hai mức hụt không giải thích được bằng nó. Cách đọc thận trọng: **quan sát này phù hợp với giả thuyết mô hình mới khái quát hoá tốt hơn**, nhưng đây là hai điểm đo trên hai cấu hình chứ không phải một phép kiểm định, và chênh lệch 0,022 nằm trong khoảng nhiễu ở n = 104.

**Ensemble lần này có tác dụng thật.** Hiệu so với trung bình 5 mô hình đơn là **+0,0380** [+0,0007; +0,0771], P = 0,048, và ensemble vượt **cả 5** thành viên (mô hình đơn tốt nhất đạt 0,7569). Ở W3 thì ngược lại: hiệu chỉ +0,0162 với P = 0,43, và mô hình đơn tốt nhất còn cao hơn ensemble. Trung bình 5 mô hình đơn lần này là 0,7302 ± 0,0278.

**Một dự đoán ghi trước đã sai, và nó là bài học phương pháp luận quan trọng nhất của tuần.** Văn bản protocol viết: *cơ chế từ chối sẽ không đạt ý nghĩa thống kê ở mức coverage 80%; nếu nó đạt thì dự đoán này sai và phải ghi rõ là sai.* Nó đạt, ở cả ba mức:

| | Hiệu so với coverage 100% | 95% CI | P |
|---|---|---|---|
| Coverage 90% | **+0,0340** | [+0,0015; +0,0688] | **0,044** |
| Coverage 80% | **+0,0739** | [+0,0126; +0,1360] | **0,027** |
| Coverage 70% | **+0,1229** | [+0,0087; +0,2043] | **0,033** |

Căn cứ của dự đoán sai: trên out-of-fold không mức coverage nào đạt ý nghĩa thống kê, và trong 64 ca sai **không ca nào** có biên quyết định dưới 0,10. Từ đó suy ra mô hình sai một cách tự tin nên thứ tự theo xác suất không tách được lỗi. Lập luận nghe chặt và nó sai. Kết luận rút ra: **tỉ lệ lỗi có biên hẹp đo trên out-of-fold không dự báo được hành vi của cơ chế từ chối trên tập test**, và lối suy luận này không được dùng lại.

## 4. Độ tin cậy của xác suất và cơ chế từ chối

Nhiệt độ *T* được fit trên 394 ca out-of-fold rồi áp mù lên tập test, không bao giờ fit trên test.

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

Hai điểm rút ra:

**Một lỗi triển khai được tìm ra trong lúc chẩn đoán.** Ở bản tái lập CGHNet, một tham số vị trí được cấp phát trong hàm forward, tức sau khi bộ tối ưu đã thu thập danh sách tham số. Nó xuất hiện trong tệp checkpoint nên nhìn qua hoàn toàn bình thường, nhưng không nằm trong nhóm nào của bộ tối ưu và **chưa từng được cập nhật** qua 300 epoch. Lỗi đã sửa; mọi con số của bản tái lập đó là của bản có lỗi.

**Trùng lặp lỗi thấp không bảo đảm gộp mô hình có lợi.** Hai kiến trúc sai ở những ca khác nhau tới mức trùng lặp chỉ 58% so với 36% nếu độc lập, và giới hạn trên nếu chọn được mô hình đúng cho từng ca là 0,8123 so với 0,6851 đạt được. Vậy mà phép trung bình xác suất không lấy được một điểm nào. Hai mô hình hỏng theo **hai chiều ngược nhau**, nên trung bình hai thiên lệch ngược chiều chỉ chọn bên nào tự tin hơn. Muốn khai thác dư địa đó cần một bộ phối hợp học được, không phải phép trung bình cố định.

## 7. Giao diện đọc kết quả

### 7.1. Kiến trúc và luồng làm việc

Giao diện được dựng lại trong tuần thành một **bàn đọc MRI ba cột**: dữ liệu đầu vào bên trái, ảnh ở trung tâm, kết quả mô hình bên phải. Có hai theme sáng và tối; vùng ảnh **luôn giữ nền đen** kể cả khi giao diện đang ở theme sáng, vì đó là điều kiện đọc ảnh y tế chứ không phải một lựa chọn thẩm mỹ.

Luồng làm việc một chiều: thả một tệp ZIP, hệ thống kiểm 8 chuỗi MRI và 8 nhãn vùng tổn thương tương ứng, rồi chạy ensemble 5 mô hình trực tiếp trên máy chủ. Sau khi có kết quả, người dùng xem được đủ 8 thì của **ảnh gốc chưa cắt** và bật tắt nhãn tổn thương.

Việc yêu cầu nhãn tổn thương đi kèm là một ràng buộc thật, cần nói rõ: mô hình phân loại tổn thương đã được khoanh, nó **không tự tìm** tổn thương. Nhãn là dữ liệu cần để tái tạo đúng vùng cắt mà mô hình được huấn luyện, không phải đầu ra do ứng dụng sinh ra.

Ba nguyên tắc trình bày được giữ nguyên từ đặc tả sản phẩm: xác suất từng lớp, mức bất định và cờ từ chối là nội dung hạng nhất trên màn hình; thông tin không bao giờ chỉ mã hoá bằng màu mà luôn kèm nhãn chữ; và dòng trạng thái nghiên cứu hiển thị ở khung ứng dụng, có mặt trên mọi màn hình có kết quả.

### 7.2. Thời gian xử lý một ca

| Thành phần | Thời gian | Thiết bị |
|---|---|---|
| Tiền xử lý: đọc 8 chuỗi, resample lên lưới chung, căn thì, chuẩn hoá | 3,43 s (trung vị) – 4,74 s (p90) | CPU |
| Suy luận, 1 mô hình | 81,7 ms | GPU Tesla T4 |
| Suy luận, ensemble 5 mô hình | 408,5 ms | GPU Tesla T4 |
| **Tổng end-to-end một ca mới** | **khoảng 3,8 – 5,2 giây** | |

Con số suy luận được đo **trong chính lượt đánh giá tập test**, không phải một phép đo riêng. Ở W3, phép đo tương ứng đã bị bỏ lỡ và không truy lại được vì tập test chỉ chạm một lần.

Hàng tiền xử lý là **số đo ở W3, mang sang chứ không đo lại tuần này**. Nó vẫn dùng được vì các bước và chi phí chi phối không đổi, chỉ khác lưới đích ở bước cuối; nhưng dòng tổng vì thế là một phép cộng ước lượng, không phải một phép đo end-to-end thật.

Hai điều kiện phải nêu kèm: đây là thời gian đo **theo lô** với batch 4, nên phục vụ từng ca một sẽ chậm hơn; và nó **không** bao gồm thời gian đọc cùng tiền xử lý ảnh. Về mặt thực tế, ensemble đắt gấp 5 lần một mô hình nhưng vẫn chỉ chiếm khoảng 10% tổng thời gian chờ, nên nó không phải ràng buộc — muốn giảm độ trễ thì phải tối ưu khâu tiền xử lý.

### 7.3. Việc còn nợ ở giao diện

Ba chỗ đã rà và ghi lại:

1. **Gỡ phần ca demo và phần bản đồ vùng chú ý.** Đây là quyết định đã chốt: giao diện chỉ phục vụ một mô hình duy nhất. Phần ca demo đã được gỡ khỏi màn hình ngày 13/08 nhưng còn để lại các endpoint và một hàm gọi API không còn ai dùng; bản đồ vùng chú ý còn nút bật tắt trong trình xem trong khi luồng tải lên không sinh ra dữ liệu đó. Đây là **mã chết**, không phải lỗi chạy, nhưng nó làm tài liệu và mã nguồn nói hai chuyện khác nhau.
2. **Tài liệu của ứng dụng nói sai** rằng chỉ có 4 trong 5 mô hình đã hoàn tất. Cả 5 đã có từ 14/08.
3. **Ngưỡng từ chối 0,55 vẫn là giá trị tạm**, chưa được khoá từ đường risk–coverage. Dữ liệu để khoá nó giờ đã có; việc khoá phải làm trên tập out-of-fold, không được chọn theo tập test.

## 8. Hạ tầng

Ba việc không tạo ra con số nhưng đổi khả năng làm việc của các tuần sau:

- **Cài phép trộn hai ca cùng chẩn đoán** ở tầng đọc dữ liệu, kèm cấu hình và notebook riêng. Đây là mảnh cuối còn thiếu của công thức huấn luyện đang tái lập, và nó nhắm đúng lớp hiếm. Chưa chạy fold nào.
- **Gỡ 12 notebook không còn dùng**, từ 20 xuống 8. Tiêu chí là hai câu hỏi kiểm được: tài liệu vận hành có còn trỏ tới nó không, và gỡ đi có mất một năng lực duy nhất nào không. Mọi tham chiếu treo đã được thay bằng lệnh dòng lệnh tương đương.
- **595 test tự động**, trong đó có test chống leakage và các test khoá cấu hình để một thí nghiệm không lặng lẽ đổi hai biến cùng lúc.

## 9. Giới hạn

1. **Con số out-of-fold 0,8147 không phải ước lượng không thiên lệch**, vì nó mang thiên lệch chọn checkpoint +0,080. Con số trung thực hơn là 0,7350.
2. **Với n = 104, khoảng tin cậy rộng khoảng ±0,09**, nên kết quả trên tập test không phân biệt được với bất kỳ phương pháp nào trong nhóm 0,71 đến 0,83. Mọi so sánh với các phương pháp đó chỉ là định vị tương đối, không phải kết luận.
3. **Tập test đã được nhìn hai lần.** Lần thứ ba cần một văn bản protocol mới và phải được nêu là lần thứ ba. Điều này thu hẹp dư địa cho phần còn lại của dự án và là một chi phí có thật của việc đẩy đánh giá test sớm lên W4.
4. **Bản tái lập còn khác công thức gốc ở ba chỗ**: dùng biến thể mô hình nhỏ thay vì lớn, hàm mất mát cùng họ nhưng khác dạng, và chưa có phép trộn hai ca cùng chẩn đoán. Chênh lệch 0,04 so với đội hạng 2 nằm trong khoảng đó cộng nhiễu cỡ mẫu, nên không quy kết được cho một nguyên nhân cụ thể nào.
5. **Bốn khẳng định rút ra từ một fold ở giữa tuần đã không sống sót qua 394 ca.** Kết luận chính vẫn đúng, nhưng các con số phụ trợ dùng để chống đỡ nó thì sai, và lúc viết chúng trông thuyết phục y hệt con số chính. Đây là lần thứ tư cỡ mẫu khoảng 80 dẫn sai đường trong dự án này.
6. **Cách căn các thì vẫn chỉ khử tịnh tiến**, chưa khử xoay và biến dạng, giống như W3.

## 10. Công việc tiếp theo

1. Chạy phép trộn hai ca cùng chẩn đoán trên một fold, so ghép cặp với fold tương ứng của cấu hình chính. Đây là mảnh cuối của công thức và nhắm đúng lớp yếu nhất.
2. Bảng ablation lõi và kiểm định thống kê có hiệu chỉnh đa so sánh. Chỉ cần CPU, chạy từ xác suất đã lưu.
3. Gỡ mã chết của phần ca demo và bản đồ vùng chú ý; khoá ngưỡng từ chối từ đường risk–coverage trên tập out-of-fold; sửa tài liệu ứng dụng.
4. Đo lại độ tin cậy xác suất và cơ chế từ chối cho giao diện, dùng số của mô hình hiện tại thay cho số của cấu hình cũ.
5. Viết `README.md`, báo cáo cuối, bộ slide, và gói tái lập.
6. Phân tích ca sai của lớp di căn để biết nút thắt do dữ liệu nhập nhằng hay do mô hình chưa dùng hết tín hiệu.

## 11. Timeline

| Thời điểm | Mốc |
|---|---|
| 10/08/2026 | Bộ chẩn đoán lớp yếu chạy trên xác suất đã lưu, loại bảy hướng cải tiến trước khi tốn giờ GPU; dựng hai nhánh tái lập độc lập. |
| 11/08/2026 | Bản tái lập CGHNet đủ 5 fold cho kết quả âm; tìm ra lỗi khiến một tham số không bao giờ được cập nhật; dựng nhánh mô hình mới kèm năm cổng kiểm chạy trước khi cam kết ngân sách. |
| 12/08/2026 | Fold đầu tiên của mô hình mới đạt 0,8111, vượt cấu hình cũ có ý nghĩa thống kê; dựng lại giao diện thành bàn đọc MRI ba cột và thêm kiểm tra tệp ZIP tải lên. |
| 13/08/2026 | Giao diện chạy suy luận trực tiếp trên bộ ảnh tải lên; cài phép trộn hai ca cùng chẩn đoán; dọn 12 notebook không còn dùng. |
| 14/08/2026 | Đủ 5 fold, gộp out-of-fold **0,8147**; khoá protocol và **đánh giá tập test lần thứ hai: 0,7682**; đo thời gian suy luận. |

## Kết luận

W4 giải được nút thắt mà W3 để lại. Chẩn đoán cuối W3 nói ràng buộc nằm ở biểu diễn đặc trưng chứ không ở siêu tham số, và can thiệp đúng vào chỗ đó đã đưa macro-F1 trên tập test từ 0,6162 lên **0,7682** — mức tăng có ý nghĩa thống kê, và lần đầu tiên dự án vượt baseline ban tổ chức một cách phân biệt được.

Về đóng góp chính, cả hai nhánh đều mạnh lên. Xác suất đạt ECE 0,0833 mà không cần hiệu chỉnh, tốt hơn mọi con số trước đó kể cả sau hiệu chỉnh. Cơ chế từ chối nâng macro-F1 lên 0,842 khi bỏ 20% ca khó nhất, và tự quyết được 76,9% số ca ở mức chấp nhận sai số dưới 10%.

Hai điều cần giữ đúng phạm vi khi trình bày kết quả này. Thứ nhất, tập test đã được nhìn hai lần, và mọi con số ở trên phải đi kèm điều đó. Thứ hai, với 104 ca thì khoảng tin cậy rộng ±0,09, nên kết quả chưa phân biệt được với nhóm phương pháp công bố gần đây; nói vượt baseline là đúng, nói tiệm cận SOTA là không.

Điều đáng ghi nhất về mặt phương pháp lại không phải một con số mà là một dự đoán sai. Cơ chế từ chối được dự báo là sẽ không hiệu quả, dựa trên một chỉ báo đo được và một lập luận nghe rất chặt; thực tế nó hiệu quả ở cả ba mức. Việc ghi dự đoán ra trước khi chạy là thứ duy nhất khiến sai lầm đó lộ ra thay vì bị hợp lý hoá ngược.
