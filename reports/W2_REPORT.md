# Báo cáo W2: xử lý dữ liệu, xây dựng baseline đầu tiên và tiến hành các lần train có kiểm soát

**Người thực hiện:** Hoàng Đức Trường
**Ngày tổng hợp:** 31/07/2026
**Kỳ báo cáo:** 24/07 – 31/07/2026
**Trạng thái:** Research Use Only (RUO); không dùng để chẩn đoán hay thay thế bác sĩ.

## Tóm tắt

Đầu W2 dự án chưa tải LLD-MMRI và chưa có một dòng code chạy được. Cuối W2 có một pipeline hoàn chỉnh từ MRI thô đến bảng metric: reader 8 thì, gate hình học chạy trên dữ liệu thật, split chính thức 316/78/104 đã tái lập và khoá, cache tiền xử lý 498 ca đẩy lên Kaggle Dataset, vòng train có checkpoint và resume, và bộ eval gồm bootstrap CI, calibration, selective prediction. 245 test xanh, trong đó có test chống leakage.

Về kết quả, số mốc đầu tiên là macro-F1 val **0,2725**. 5 lần train có kiểm soát sau đó đưa con số lên **0,7001** (E4), và **toàn bộ mức tăng đến từ thay đổi về dữ liệu, không một hyperparam nào bị đụng tới**: cắt patch bám sát tổn thương (+0,15) rồi căn từng thì về tổn thương của chính nó (+0,13, 95% CI [+0,033; +0,230]). Hai lần train còn lại đều không cho kết luận: một bị huỷ vì biến gây nhiễu, một bị chủ động dừng sớm.

## 1. Mục tiêu W2 và trạng thái Definition of Done

Mục tiêu W2: đưa LLD-MMRI vào một pipeline tái lập được, có split khoá ở mức bệnh nhân, và một con số baseline đầu tiên làm mốc so sánh cho các tuần sau.

| Definition of Done | Trạng thái | Bằng chứng |
|---|---|---|
| Khảo sát dữ liệu: phân bố 7 lớp, spacing, kích thước, thiếu thì | Đạt | chạy trên toàn bộ 498 bệnh nhân |
| Tiền xử lý v0 cache thành Kaggle Dataset có đánh phiên bản | Đạt | 498 khối, 2,71 GB, private |
| Split chính thức đã khoá, bất biến, có kiểm chứng | Đạt | 394 trainval + 104 test = 498 |
| Test chống leakage pass (giao tập bệnh nhân mọi cặp fold rỗng) | Đạt | 245 test xanh, 17 skip |
| Baseline **3D-patch** chạy 1 fold, ra macro-F1 val | Đạt | 0,2725 → **0,7001** sau các lần train |

## 2. Nền dữ liệu: từ MRI thô đến cache sẵn sàng train

Dataset gồm 498 bệnh nhân × 8 thì = 3.984 volume, kèm nhãn 7 lớp và bbox 2D theo từng slice. Phân bố lớp: HCC 157 · u máu 79 · ICC 58 · áp-xe 54 · nang 53 · di căn 51 · FNH 46. Mất cân bằng vừa phải (3,4:1), không phải long-tail.

### 2.1. Split chính thức được tái lập và kiểm chứng

Bản dataset đang dùng không kèm split. Quyết định ban đầu là tự chia 5-fold stratified; quyết định đó đã bị đảo sau khi tìm được danh sách 394 ca trainval từ tài liệu của challenge của bản dataset này, từ đó suy ra test-104 = 498 − 394. Phân bố lớp của bản tái lập khớp tài liệu chính thức **7/7 lớp**, nên split 316/78/104 đã khôi phục thành công.

Đây là quyết định quan trọng nhất về mặt phương pháp: nó khôi phục khả năng so benchmark trực tiếp với leaderboard của challenge. Tự chia thì mọi con số sau này chỉ so được với chính mình. Split đã được commit và khoá lại, mọi thay đổi lên nó đều bị chặn tự động.

### 2.2. Gate hình học và phán quyết thứ tự trục

Rủi ro cụ thể: bản dataset có thể đã resample hoặc reorient ảnh trong khi bbox vẫn ở toạ độ gốc. Nếu vậy thì mọi patch cắt theo bbox đều lệch, và không có gì trong quá trình train báo hiệu điều đó. Gate đối chiếu spacing trong header ảnh với spacing khai trong annotation, cộng kiểm chỉ số slice và bbox có nằm trong biên không. Kết quả: **đạt 3.984/3.984**. Ảnh không bị resample, toạ độ bbox dùng thẳng được.

Gate cũng lộ ra hai chuyện chưa lường trước. Thứ nhất, **8 thì của cùng một bệnh nhân không cùng lưới voxel**: có ca thì động là 512×512×88 @2,6mm còn T2WI là 512×512×24 @9mm. Thứ hai, **nhóm In/Out Phase không cố định**, phần lớn ca đi cùng thì động nhưng một số ca lại đi cùng nhóm T2WI, nên thiết kế fusion không cố định nhóm được.

Một vấn đề khác nặng hơn: annotation không nói rõ bbox là `(x, y)` hay `(y, x)`. Ảnh đều vuông nên bbox lọt cả hai cách hiểu và đoán sai thì mọi patch lệch 90°. Cách giải: cùng một tổn thương vật lý thì tâm bbox của 8 thì phải hội tụ trong toạ độ thế giới, cách hiểu sai làm chúng tán ra. Phân rã độ tán theo trục:

| Cách hiểu | X | Y | Z |
|---|---|---|---|
| `xy` | **7,4** | 10,3 | 23,3 |
| `yx` | 13,9 | 11,2 | 23,3 |

Trục Z giống hệt nhau ở cả hai cách hiểu vì hoán vị trục chỉ đụng X/Y, nên đưa Z vào chỉ làm loãng tín hiệu phân biệt. Chỉ đo in-plane thì phán quyết rõ: **166/180 phiếu (92%) cho `xy`, độ tán 12,4mm**, và thứ tự trục được chốt là `xy`.

Con số 23,3mm ở trục Z không phải lỗi đo mà là biên độ **chuyển động hô hấp của gan**, vì 8 thì được chụp ở các lần nín thở khác nhau. Nó được ghi lại và về sau trở thành cơ sở của lần train E4.

### 2.3. Cắt trong không gian mm, và cache

Vì 8 thì khác lưới, bbox tính theo voxel của thì này vô nghĩa với thì kia; nhưng cả 8 chung hệ toạ độ bệnh nhân. Cách làm: đổi tâm bbox sang mm, dựng một lưới đích chung 96×96×48 @1,5×1,5×3,0mm quanh tâm đó, rồi lấy mẫu cả 8 thì lên lưới ấy. Đây đồng thời là một phép căn thô, nên registration riêng được hoãn sang W3 làm ablation. Chuẩn hoá dùng thống kê của chính volume bệnh nhân đó, không gộp xuyên bệnh nhân, nên không vi phạm nguyên tắc chống leakage.

Build hoàn tất 498/498 ca, cho ra tập huấn luyện 312 ca và tập val 82 ca ở fold 1. Cache được đẩy lên Kaggle Dataset 2,71 GB, để private vì license CC BY-NC-ND cấm phát tán bản phái sinh.

**Một đính chính về nguồn gốc mask.** Bộ mask kèm dataset từng được ghi là "MedSAM2 sinh tự động, không phải chuẩn vàng". Tra lại nguồn thì mô tả đó quá phủ định: đây chính là nhãn segmentation chính thức của LLD-MMRI, bổ sung tháng 3/2025, gán bằng MedSAM2 trong một quy trình human-in-the-loop. Vẫn giữ một dè dặt có cơ sở: mức can thiệp của người không được nói rõ, nên dùng làm mục tiêu giám sát phụ thì hợp lý, còn báo cáo chất lượng segmentation như một kết quả thì phải nêu giới hạn.

## 3. Baseline và 5 lần train có kiểm soát

### 3.1. Số mốc đầu tiên, và việc dừng tune

Lần train đầu tiên dùng DenseNet121-3D, 8 kênh vào cho 7 lớp theo kiểu early concat, 11,4 triệu tham số, fold 1: macro-F1 val tốt nhất **0,2725** ở epoch 11, dừng sớm ở epoch 26. Đoán ngẫu nhiên với 7 lớp cho macro-F1 khoảng 0,10 và loss bằng ln 7 = 1,946; model có học, nhưng train loss chỉ nhích 0,32 dưới mức đoán bừa sau 26 epoch, tức chưa fit nổi tập train. Ba lần thử sửa bằng hyperparam đều thất bại; con số ổn định quanh 0,26–0,27 ở hai cấu hình khác nhau.

Thay vì đoán tiếp, dự án chuyển sang **tái lập nguyên khối recipe của baseline chính thức** (macro-F1 0,6083 trên test-104). Bảng đối chiếu cho thấy sai khác lớn hơn nhiều so với hình dung ban đầu:

| | Baseline chính thức | Cấu hình của ta trước đó |
|---|---|---|
| epochs | 300, best @ 216 | 60, dừng sớm @ 26 |
| early stopping | không có | patience 15 |
| learning rate | 1e-4 | 3e-4 |
| **weight decay** | **0,05** | **1e-5** (chênh 5.000 lần) |
| warmup | 5 epoch, lr 1e-6 | không có |
| loss | CrossEntropy trần | CE + class weights |
| batch hiệu dụng | 8 | 4 |
| augment | flip x/y/z · xoay ±10° · random crop | flip x/y · rot90 · nhiễu cường độ |
| chuẩn hoá | min-max [0,1] | percentile clip + z-score |
| input | 112×112×14 | 96×96×48 |

Recipe được áp nguyên khối, mỗi dòng cấu hình kèm trích nguồn, và được khoá bằng một test để không trôi về sau. Một gate đo thời gian chạy trước khi tốn GPU đã chặn lại ngay lần đầu: 56,5s/epoch tương đương 23,5 giờ cho 5 fold, gần hết quota tuần. Nguyên nhân là augmentation chạy trên CPU trong khi GPU ngồi chờ, sửa được thuần bằng tối ưu kỹ thuật mà không đụng phép toán nào trong recipe.

### 3.2. Bảng kết quả 5 lần train

| | Thay đổi so với lần train trước | macro-F1 val [95% CI] | κ | AURC | ECE thô → sau T | Trạng thái |
|---|---|---|---|---|---|---|
| **E0** | recipe chính thức + cửa sổ mm cố định 96×96×48 | 0,4244 [0,314–0,530] | 0,276 | 0,5395 | 0,3218 → 0,1455 | xong |
| **E1** | cache cắt bám sát tổn thương | **0,5740** [0,455–0,678] | 0,520 | **0,2753** | 0,2935 → 0,2505 | xong |
| **E2** | Siamese đa thì, trọng số dùng chung | ~0,35 – 0,49 @ ep100 | — | — | — | **huỷ** |
| **E3** | hình học 112×112×32 theo văn liệu | 0,5566 @ ep145 | — | — | — | **dừng sớm** |
| **E4** | căn từng thì theo tổn thương của chính nó | **0,7001** [0,599–0,793] | **0,646** | **0,2033** | 0,2458 → 0,1489 | xong, **thắng rõ** |

> **Mọi số trong bảng là val fold 1, 82 bệnh nhân, 1 seed.** Không phải kết quả báo cáo được: chưa có CV 5-fold, và ở n=82 bề rộng CI vào khoảng ±0,10. Chúng dùng để sàng lọc giữa các phương án, không để công bố.

### 3.3. E4: giả thuyết đã được xác nhận

Con số 23,3mm đo ở phần nền dữ liệu chưa từng được nối với chất lượng model. Nối vào thì nó lớn hơn hình dung:

| Trục | Độ tán tâm tổn thương giữa 8 thì | Cửa sổ cắt E3 | Tỉ lệ |
|---|---|---|---|
| In-plane | 12,4mm | 53,8mm | 23% |
| **Z (đầu-chân)** | **23,3mm** | **43,6mm** | **53%** |

Early concat có một tiền đề ngầm: cùng một vị trí voxel ở mọi kênh phải là cùng một điểm giải phẫu. Lệch 53% chiều sâu thì tiền đề đó vỡ, và lớp conv đầu tiên đang trộn mô không liên quan với nhau. Đội hạng 2 của challenge lấy chính việc sửa registration làm đóng góp trọng tâm.

E4 căn từng thì về tâm tổn thương của chính nó, dùng bbox có sẵn trong annotation; chi phí chỉ là một lần build cache, không cần thuật toán registration. Spacing và trường nhìn tính một lần từ thì tham chiếu, chỉ đổi tâm, nên 8 khối giữ cùng kích thước vật lý và khác nhau đúng một phép tịnh tiến. Đây không phải phép sửa trung tính: nó chỉ khử tịnh tiến, không khử xoay hay biến dạng, và mô xung quanh sẽ thôi khớp giữa các thì, chỉ tổn thương khớp. Với bài phân loại tổn thương thì đó có thể là điều mong muốn, nhưng nó là một thay đổi ngữ nghĩa dữ liệu và phải ghi vào báo cáo cuối.

**Kết quả: 0,7001, mức tăng lớn nhất và là mức tăng duy nhất có ý nghĩa thống kê của cả loạt.**

Một gate chạy trước khi train đã kiểm rằng phép căn thật sự có hiệu lực, nếu không thì cache E4 sẽ giống hệt E3 và train sẽ lặp lại đúng kết quả của E3 sau 4 giờ mà đường cong không hé lộ gì. Gate qua: cả 498 ca cắt theo mask, không ca nào phải lùi về tâm tham chiếu, độ dịch giữa các thì có trung vị **19,65mm** (nhỏ nhất 2,80, lớn nhất 111,0).

| So cặp (bootstrap trên hiệu, phân tầng, 2000 lần) | Δ macro-F1 | 95% CI | P |
|---|---|---|---|
| E4 − E1 | **+0,1261** | **[+0,033; +0,230]** | 0,009 |
| E4 − E0 | +0,2757 | [+0,145; +0,415] | <0,001 |
| E1 − E0 | +0,1496 | [+0,007; +0,289] | 0,040 |

E4 − E1 là lần đầu tiên trong cả loạt có một khoảng tin cậy **nằm hẳn về một phía của 0** với biên rộng rãi. Lưu ý E4 khác E1 ở *hai* khoá, hình học và phép căn. Phép so một biến lẽ ra là E4 với E3, vì hai lần train đó cùng hình học 112×112×32 và chỉ khác cách căn; nhưng E3 đã bị dừng ở epoch 145 nên không gánh được vai trò này. Nói cho đúng: **mức tăng +0,126 là chắc chắn, còn việc quy nó cho phép căn thay vì cho hình học thì chưa.** Muốn tách hai biến phải chạy lại E3 đủ 300 epoch.

**Ba chỉ báo cơ chế lần này đều trúng**, khác hẳn E1: ở đó can thiệp ăn tiền nhưng ba trong bốn chỉ báo dự đoán trước đều trượt, tức chọn đúng việc mà giải thích sai lý do.

| | E1 | E4 |
|---|---|---|
| Val loss chạm đáy ở epoch | 9 | **100** |
| Gap train/val ở epoch cuối | +2,55 | **+1,50** |
| macro-F1 trung bình 50 epoch cuối | 0,512 | **0,607** |
| Số epoch cuối đạt ≥ 0,60 | 0/50 | **29/50** |
| NLL thô so với đoán mò (1,946) | 3,32 (tệ hơn đoán mò) | **1,72 (tốt hơn)** |
| Temperature cross-fit | 5,010 | **2,570** |

Hai dòng cuối quan trọng nhất. Ở E0 và E1, xác suất thô có NLL cao hơn mức đoán mò đều, tức phần "độ tin cậy" của model là nhiễu có hại, phải hạ nhiệt gấp 5 lần mới dùng được. E4 là lần train đầu tiên mà xác suất thô mang thông tin thật.

Điều này cũng giải thích luôn chứng overfit kinh niên bị ghi nhận suốt E0 đến E3, khi val loss chạm đáy ở epoch 9–10 rồi model chỉ còn học thuộc. Nguyên nhân không nằm ở recipe train mà ở đầu vào: khi 8 thì không khớp nhau tới từng voxel thì lớp conv đầu tiên không có đặc trưng liên-thì nào để học, nên nó quay sang ghi nhớ. Sửa phép căn đẩy đáy từ epoch 9 sang epoch 100.

F1 tăng ở 5/7 lớp, mạnh nhất ở đúng những lớp trước đây yếu nhất: u máu +0,27, nang +0,26, áp-xe +0,25, di căn +0,16. Hai lớp giảm nhẹ (ICC −0,09 với n=10, FNH −0,05 với n=8) đều ở cỡ mẫu quá nhỏ để đọc.

**Vẫn phải nói rõ điều này:** 0,7001 đo trên val fold 1 (82 ca), còn 0,709 của ResNet3D trong bài CGHNet đo trên test-104. **Hai tập khác nhau, không được viết là ngang nhau.** Bề rộng CI ở đây là ±0,10, đủ để một chênh lệch hệ thống 0,03–0,05 ẩn trong đó.

### 3.4. Số trustworthiness đầu tiên

Đây là đóng góp headline của dự án, nên phần này quan trọng hơn các con số phân loại ở trên.

**Xác suất thô của model gần như vô dụng.** NLL thô của E1 là 3,3182, tệ hơn đoán mò (ln 7 = 1,9459), và chỉ về 1,5205 sau temperature scaling. Nhiệt độ tìm được khoảng 5,0 là mức cực đoan; E0 cũng ở mức 4,15. Nói cách khác, E1 phân loại giỏi hơn E0 nhưng đồng thời tự tin thái quá hơn. Temperature scaling vì thế là bước bắt buộc, không phải tuỳ chọn ở cuối pipeline.

**Cách fit temperature ảnh hưởng tới con số nhiều hơn dự kiến.** Fit ngay trên tập đánh giá cho ECE 0,1011; cross-fit 5 phần cho **0,1455**. Chênh 44%. Chỉ số cross-fit được dùng, số in-sample không vào báo cáo.

**Một metric đã phải đổi.** Mục tiêu ban đầu là macro-F1 ≥ 0,90 ở coverage 80%. Ở n=82 nó không tính được có nghĩa: tại coverage 50%, một lớp hiếm chỉ còn 1–2 ca, F1 của lớp đó do một bệnh nhân quyết định rồi chiếm 1/7 trọng số macro. Quan sát thực tế trên E1: macro-F1 nhảy loạn (0,5740 → 0,5559 → 0,5816 → 0,5211) trong khi accuracy tăng đều và đơn điệu (0,6098 → 0,7561). Metric headline của selective prediction vì thế đổi sang risk–coverage và AURC, và phải tính trên tập gộp out-of-fold 394 ca thay vì một fold. Theo AURC thì E1 (0,2753) tốt hơn E0 (0,5395) gần gấp đôi, và E4 (0,2033) tốt hơn E1 thêm một bậc nữa.

## 4. Trạng thái và giới hạn

| Hạng mục | Trạng thái | Bằng chứng | Nhận xét |
|---|---|---|---|
| Split chính thức, khoá, test chống leakage | Hoàn thành | 245 test xanh | Khôi phục khả năng so benchmark trực tiếp. |
| Gate hình học trên dữ liệu thật | Hoàn thành | đạt 3.984/3.984 | Điều kiện tiên quyết cho việc cắt theo bbox. |
| Cache cửa sổ mm cố định | Hoàn thành | 498 khối, Kaggle Dataset v1 | Đã bị E1 thay thế làm mặc định. |
| Cache cắt bám tổn thương | Hoàn thành | E1 chạy trên nó | Đã bị cache E4 thay thế làm mặc định. |
| Baseline 3D-patch, 1 fold | Hoàn thành | **0,7001** val fold 1 (E4) | Chưa có CV, chưa phải số báo cáo. |
| Fusion Siamese (E2) | **Chưa kết luận** | lần train bị huỷ vì biến gây nhiễu | Phải chạy lại ở hình học đúng mới đánh giá được. |
| Ablation hình học (E3) | **Dừng sớm** | 0,5566 ở epoch 145/300 | Chưa kết luận được: dừng trước vùng epoch mà cả ba lần train chạy hết mới đạt đỉnh. |
| Căn từng thì (E4) | **Hoàn thành, thắng rõ** | 0,7001; Δ so E1 +0,126 CI [+0,033; +0,230] | **Cấu hình chốt.** Gate căn pha đã qua (trung vị 19,65mm, 0 ca fallback). |
| Calibration và selective | Xong phần code, số mới 1 fold | ECE, AURC, T của E0, E1, E4 | Cần gộp out-of-fold 394 ca. |
| CV 5-fold và CI bootstrap | Đã chuẩn bị, chưa chạy | ước tính 3,9h mỗi fold | Việc đầu tiên của W3. |
| Registration rigid | Chưa bắt đầu | — | E4 cho thấy hướng này đáng đầu tư, nhưng xếp sau CV. |
| External và OOD | Chưa bắt đầu | — | Theo kế hoạch W3. |
| **test-104** | **Chưa chạm** | không có đường code nào tới nó | Đúng quy trình; chỉ chạm một lần ở W5. |

**Giới hạn phải nói rõ với người đọc:**

1. **Mọi con số của dự án là 1 fold, 82 bệnh nhân val, 1 seed.** Không có CI cho phần lớn chúng, và ở n=82 bề rộng CI khoảng ±0,10, đủ để nuốt trọn một chênh lệch cỡ 0,02 đến 0,03.
2. **Không so trực tiếp được với văn liệu**, vì số văn liệu đo trên test-104.
3. **Ngay cả khi có kết quả tốt, việc chứng minh vượt SOTA là bất khả thi ở cỡ mẫu này.** Bootstrap ở n=104 cho bề rộng CI ±0,077 tại mức 0,8322 và ±0,061 tại 0,90; hai CI chồng nhau. Định vị của dự án vì thế phải là trustworthiness, không phải leaderboard.
4. **Overfitting đã nhẹ đi nhiều nhưng chưa hết.** Val loss chạm đáy ở epoch 9–10 ở E0, E1, E3; ở E4 là epoch 100 và gap cuối giảm từ +2,55 xuống +1,50. Nguyên nhân gốc hoá ra là lệch thì ở đầu vào chứ không phải recipe train, nên các hướng chỉnh dropout hay weight decay trước đây đều nhắm sai chỗ.
5. **Chế độ tất định không cho tái lập tới từng bit**, vì DenseNet 3D không tất định trên CUDA. Seed cố định cho phép lặp lại *lần train*, không phải lặp lại từng chữ số. Đây là một lý do nữa để mọi số đều kèm CI.

## 5. Công việc tiếp theo theo thứ tự ưu tiên

E4 là cấu hình chốt. Mọi việc dưới đây đều cải tiến từ nó, không quay lại các nhánh đã dừng.

1. Chạy đủ 5-fold cho cấu hình E4, dựng bảng CV macro-F1 và κ kèm CI bootstrap mức bệnh nhân.
2. Gộp out-of-fold 394 ca, tính lại calibration và risk–coverage trên cỡ mẫu đó.
3. Dựng deep ensemble từ 5 checkpoint để đo bất định epistemic; đây là điều kiện của đóng góp headline.
4. Chạy registration rigid thật; E4 mới chỉ khử tịnh tiến, chưa khử xoay và biến dạng.
5. Đổi backbone sang ResNet3D ở đúng 14×112×112; dưới protocol thống nhất của CGHNet, một ResNet3D trần đạt 0,709 trên test-104. DenseNet121-3D không chịu được Z=14 nên đây là đổi kiến trúc, không chỉ đổi cấu hình.
6. Thử Focal Loss và ablation augmentation; theo ablation của CGHNet, Focal Loss hơn CrossEntropy 1,9 điểm và bỏ random crop mất 8,8 điểm.
7. Audit và tải external cùng Duke OOD (Option*).
8. Khoá protocol, threshold và temperature trên validation trước khi chạm test-104 đúng một lần.

## 6. Timeline

| Thời điểm | Mốc |
|---|---|
| 24/07/2026 | Lập kế hoạch W2; khảo sát dataset LLD-MMRI; tái lập và kiểm chứng split chính thức 316/78/104; test chống leakage đầu tiên. Dựng pipeline chạy trên Kaggle; gate hình học đạt trên dữ liệu thật. |
| 27/07/2026 | Tiền xử lý trong không gian mm; chốt thứ tự trục; build cache 498 ca; baseline ra **số mốc đầu tiên 0,2725**; ba chẩn đoán sai; tra leaderboard và **áp nguyên khối recipe chính thức**; hạ tầng bootstrap CI. |
| 28/07/2026 | Cache cắt bám tổn thương; bộ đo calibration và selective; tính bề rộng CI ở n=104. |
| 29/07/2026 | **E0 = 0,4244 · E1 = 0,5740**; phân tích calibration và selective; dựng E2 Siamese. |
| 30/07/2026 | Đọc CGHNet; huỷ E2; **E3 dừng sớm ở epoch 145 với 0,5566**; dựng E4. |
| 31/07/2026 | Tổng hợp báo cáo W2; **E4 = 0,7001, mức tăng duy nhất có ý nghĩa thống kê** (Δ so E1 +0,126, CI [+0,033; +0,230]); chốt cấu hình E4; chuẩn bị CV 5-fold. |

## Kết luận

Về hạ tầng, pipeline từ MRI thô đến bảng metric đã chạy được và tái lập được, với mọi gate an toàn khoa học đứng vững: split khoá ở mức bệnh nhân, test chống leakage pass, thống kê chuẩn hoá không xuyên bệnh nhân, và test-104 chưa bị chạm một lần nào. Về kết quả, con số tốt nhất hiện tại là macro-F1 **0,7001** trên val fold 1; nó chưa so trực tiếp được với văn liệu vì khác tập đánh giá, chưa có CV, và chưa nên coi là kết quả cuối. Điều đáng nói không phải bản thân con số mà là cách nó tăng: toàn bộ mức tăng từ 0,26 lên 0,70 đến từ tái lập recipe và hai thay đổi về cách chuẩn bị dữ liệu, không một dòng nào của kiến trúc model bị đụng tới. Hai hướng đi theo kiến trúc và hình học đều chưa cho gì, và cả hai đều chưa được thử đến nơi.

Về trustworthiness, đóng góp headline của dự án đã có số thật và chúng cho thấy vấn đề vừa có thật vừa cải thiện được: NLL thô đi từ chỗ tệ hơn đoán mò (3,32 so với 1,95) xuống 1,72, nhiệt độ cần thiết giảm từ 5,0 còn 2,57, AURC từ 0,540 xuống 0,203. Nhưng đóng góp này vẫn chưa đo được đầy đủ, vì bất định epistemic cần 5 model của 5 fold mà hiện mới có một; đó là lý do việc đầu tiên của W3 là chạy nốt CV chứ không phải thử thêm ý tưởng. Bài học lớn nhất của W2 lại là về phương pháp chứ không về mô hình: bốn lần chẩn đoán sai trong tuần đều sinh ra từ cùng một chỗ, là debug khi chưa biết mức nào mới là đạt. Luật đối chiếu mốc ngoài trước khi debug nay đã được ghi vào tài liệu ngữ cảnh của dự án.

---

*Research Use Only. Mọi số trong báo cáo này là kết quả sàng lọc trên tập validation, chưa qua cross-validation và chưa có khoảng tin cậy đầy đủ; chúng không phải kết quả nghiên cứu được công bố và không được dùng để suy diễn về hiệu năng lâm sàng.*
