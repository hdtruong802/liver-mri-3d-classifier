# Báo cáo W2: nền dữ liệu, mô hình nền đầu tiên và năm thí nghiệm có kiểm soát

**Người thực hiện:** Hoàng Đức Trường
**Ngày tổng hợp:** 31/07/2026
**Kỳ báo cáo:** 24/07 – 31/07/2026
**Trạng thái:** Research Use Only (RUO); không dùng để chẩn đoán hay thay thế bác sĩ.

> **Quy ước thuật ngữ của báo cáo này.** Viết bằng tiếng Việt. Chỉ giữ nguyên tiếng Anh ở ba nhóm: (1) tên riêng gồm `LLD-MMRI`, `DenseNet121-3D`, `MedSAM2`, Kaggle; (2) tên chỉ số và phương pháp thống kê đã thành ký hiệu như macro-F1, κ, ECE, NLL, AURC, bootstrap; (3) định danh trong mã nguồn, đường dẫn file và khoá cấu hình, luôn đặt trong dấu nháy ngược. Ngoài ba nhóm đó, thuật ngữ nào có cách nói tiếng Việt thì dùng tiếng Việt, và dùng nhất quán một cách trong cả báo cáo.

## Tóm tắt

Đầu W2 dự án chưa có `src/`, chưa tải `LLD-MMRI`, chưa có một dòng mã chạy được. Cuối W2 có một quy trình hoàn chỉnh từ ảnh MRI thô đến bảng chỉ số: bộ đọc 8 thì, cổng kiểm hình học chạy trên dữ liệu thật, bộ chia chính thức 316/78/104 đã tái lập và khoá, bộ nhớ đệm tiền xử lý 498 ca đẩy lên Kaggle Dataset, vòng huấn luyện có lưu và khôi phục tiến trình, và bộ đánh giá gồm khoảng tin cậy bootstrap, hiệu chỉnh xác suất và dự đoán có chọn lọc. 245 kiểm thử xanh, trong đó có kiểm thử chống rò rỉ dữ liệu.

Về kết quả, số mốc đầu tiên là macro-F1 trên tập kiểm định **0,2725**. Năm thí nghiệm có kiểm soát sau đó đưa con số lên **0,7001**, và **toàn bộ mức tăng đến từ thay đổi về dữ liệu, không một siêu tham số nào bị đụng tới**: cắt khối ảnh bám sát tổn thương (+0,15) rồi căn từng thì về tổn thương của chính nó (+0,13, khoảng tin cậy 95% [+0,033, +0,230]). Hai thí nghiệm còn lại cho kết quả âm hoặc bị huỷ, trong đó giả thuyết "tỉ lệ trục là nút thắt" bị bác bỏ sạch.

## 1. Mục tiêu W2 và trạng thái tiêu chí hoàn thành

Mục tiêu W2: đưa `LLD-MMRI` vào một quy trình tái lập được, có bộ chia khoá ở mức bệnh nhân, và một con số nền đầu tiên làm mốc so sánh cho các tuần sau.

| Tiêu chí hoàn thành (theo `docs/W2_plan.md`) | Trạng thái | Bằng chứng |
|---|---|---|
| Notebook khảo sát dữ liệu: phân bố 7 lớp, spacing, kích thước mảng, thiếu thì | Đạt | `notebooks/01_eda.ipynb`, `scripts/kaggle_geometry_report.py` |
| Tiền xử lý v0 lưu thành Kaggle Dataset có đánh phiên bản | Đạt | 498 `.npz`, `marcohoang/lld-mmri-3` v1, để riêng tư |
| `splits/` chính thức 12 file đã commit, bất biến, đã kiểm | Đạt | `labels_trainval.txt` 394 + `test_official.txt` 104 = 498 |
| `pytest` kiểm thử rò rỉ pass (giao tập bệnh nhân mọi cặp fold = ∅) | Đạt | 245 passed, 17 skipped |
| Mô hình nền **3D-patch** chạy 1 fold, ra macro-F1 kiểm định | Đạt | 0,2725 → **0,7001** sau các thí nghiệm |
| Mô hình nền **2.5D** chạy 1 fold, ra macro-F1 kiểm định | **Không đạt** | Bị cắt có chủ ý |
| Cập nhật bảng lệnh `AGENTS.md` §6 | Đạt | mọi điểm vào đều có dòng lệnh tương ứng |

**Về mục không đạt.** Mô hình nền 2.5D nằm ở vị trí thứ hai trong danh sách "việc cắt được nếu trễ" của chính `docs/W2_plan.md`. Nó bị cắt theo đúng thứ tự đã định trước, không phải bỏ quên. Bằng chứng ngoài (§4.2) sau đó cho thấy quyết định này không gây thiệt hại: trong bảng so sánh cùng một quy trình của CGHNet, `ResNet3D` (0,709) thắng `ResNet2D` (0,684), nên nhánh 3D vẫn là hướng đúng.

**Hai lệch so với kế hoạch, cả hai đều nên ghi rõ.**

- **Giao sớm hơn kế hoạch:** `src/eval/bootstrap.py` (thuộc W3), `src/eval/calibration.py` và `src/eval/selective.py` (thuộc W5), `src/eval/run.py`. Bộ đánh giá đã sẵn sàng trước khi có mô hình đáng đánh giá.
- **Tràn sang địa hạt W3/W4:** năm thí nghiệm E0–E4 là công việc so sánh kiến trúc và dữ liệu, vốn thuộc W3–W4. Đây là phình phạm vi có ý thức: mô hình nền dừng ở 0,26 trong khi bản nền chính thức của cuộc thi đạt 0,6083, nên tiếp tục sang W3 với một quy trình chưa rõ có lành hay không là rủi ro lớn hơn.

## 2. Nền dữ liệu: từ ảnh MRI thô đến bộ nhớ đệm sẵn sàng huấn luyện

Dữ liệu là bản sao nguyên si của `wanglab/LLD-MMRI-MedSAM2`: 498 bệnh nhân × 8 thì = 3.984 khối ảnh `.nii.gz`, cộng `LLD_MMRI_Annotation.json` giữ nhãn 7 lớp và khung bao 2D theo từng lát cắt. Phân bố lớp: HCC 157 · u máu 79 · ICC 58 · áp-xe 54 · nang 53 · di căn 51 · FNH 46, mất cân bằng vừa phải (3,4:1), không phải phân bố đuôi dài.

### 2.1. Bộ chia chính thức được tái lập và kiểm chứng

Bản `wanglab` không kèm bộ chia. Quyết định ban đầu là tự chia 5 fold phân tầng; quyết định đó đã bị **đảo** sau khi tìm được `labels_trainval.txt` (394 ca) trong kho mã của một đội dự thi, từ đó suy ra tập kiểm tra 104 ca = 498 − 394. Phân bố lớp của bản tái lập khớp tài liệu chính thức **7/7 lớp**, nên bộ chia 316/78/104 được coi là khôi phục thành công.

Đây là quyết định đắt giá nhất về mặt phương pháp trong cả tuần: nó khôi phục khả năng **so sánh trực tiếp** với bảng xếp hạng của cuộc thi. Tự chia thì mọi con số sau này chỉ so được với chính mình. 12 file được commit vào `splits/` và cổng chất lượng chặn mọi thay đổi lên thư mục đó.

### 2.2. Cổng kiểm hình học chạy trên dữ liệu thật trước khi cắt

Rủi ro cụ thể: bản `MedSAM2` có thể đã lấy mẫu lại hoặc xoay hướng ảnh trong khi khung bao vẫn ở toạ độ gốc. Nếu vậy thì mọi khối ảnh cắt theo khung bao đều lệch, và không có gì trong quá trình huấn luyện báo hiệu điều đó.

Cổng kiểm đối chiếu `spacing` trong phần đầu file ảnh với `pixel_spacing`/`slice_spacing` trong tệp chú giải, cộng kiểm `slice_idx` và khung bao có nằm trong biên không. Kết quả: **đạt 3.984/3.984 lượt kiểm theo thì**. Ảnh không bị lấy mẫu lại, toạ độ khung bao dùng thẳng được.

Cổng kiểm cũng lộ ra hai chuyện chưa lường trước:

- **8 thì của cùng một bệnh nhân không cùng lưới voxel.** Ví dụ MR-398189: thì động 512×512×88 @2,6mm, T2WI 512×512×24 @9mm, DWI 256×256×24. Mọi đoạn mã giả định 8 thì xếp chồng thẳng được đều sai.
- **Nhóm In/Out Phase không cố định.** Ở phần lớn ca chúng đi cùng thì động; ở một số ca lại đi cùng nhóm T2WI. Thiết kế hợp nhất tách "cấu trúc so với động học" vì thế không cố định cứng nhóm được.

### 2.3. Phán quyết thứ tự trục, và một bẫy phép đo

Tệp chú giải không nói rõ `2D_box` là `(x, y)` hay `(y, x)`. Ảnh đều vuông (512², 256², 384²) nên khung bao lọt cả hai cách hiểu, không đoán được bằng mắt, và đoán sai thì mọi khối ảnh lệch 90°.

Cách giải: tệp chú giải có khung bao riêng cho từng thì, mà cùng một tổn thương vật lý thì 8 tâm phải **hội tụ** trong toạ độ thế giới. Cách hiểu sai làm chúng tán ra.

Lần đo đầu tiên trả về "không kết luận được": 83/90 phiếu (92%) cho `xy` nhưng độ tán trung vị 26,3mm vượt ngưỡng. Phân rã theo trục cho thấy lỗi nằm ở phép đo, không ở dữ liệu:

| Cách hiểu | X | Y | Z |
|---|---|---|---|
| `xy` | **7,4** | 10,3 | 23,3 |
| `yx` | 13,9 | 11,2 | 23,3 |

Trục Z giống hệt nhau ở cả hai cách hiểu (hoán vị trục chỉ đụng X/Y), và 23,3mm chính là biên độ **chuyển động hô hấp của gan**: 8 thì được chụp ở các lần nín thở khác nhau. Đưa Z vào vừa đẩy tổng độ tán vượt ngưỡng vừa làm loãng tín hiệu phân biệt.

Sau khi chỉ đo trong mặt phẳng: **180/498 ca có sức phân biệt (gấp đôi), `xy` được 166 phiếu (92%), độ tán 12,4mm**. Chốt `axis_order = xy`.

Con số 23,3mm này được ghi lại và về sau trở thành cơ sở của thí nghiệm E4 (§3.3).

### 2.4. Cắt trong không gian mm, không phải voxel

Vì 8 thì khác lưới, khung bao tính theo voxel của thì này vô nghĩa với thì kia. Nhưng cả 8 chung hệ toạ độ bệnh nhân. Cách làm: đổi tâm khung bao sang mm → dựng **một lưới đích chung** 96×96×48 @1,5×1,5×3,0mm quanh tâm đó → lấy mẫu cả 8 thì lên lưới ấy.

Đây đồng thời là một **phép căn thô**, nên phép căn ảnh riêng được hoãn sang W3 làm khảo sát loại bỏ. Chuẩn hoá dùng thống kê của chính khối ảnh bệnh nhân đó, không gộp xuyên bệnh nhân, nên không vi phạm nguyên tắc chống rò rỉ.

`build_cache` **từ chối chạy** khi `axis_order` để trống: thà dừng còn hơn cắt sai trục rồi mọi kết quả sau đều vô nghĩa.

### 2.5. Bộ nhớ đệm

Dựng hoàn tất 498/498 ca, bỏ qua 0, lỗi 0, trong 24 phút. Kiểm nghiệm thu: 498 file `.npz`, kích thước mảng đồng nhất `(8, 96, 96, 48)`, không có giá trị `NaN`/`Inf`. Bộ nạp dữ liệu dựng được tập huấn luyện 312 ca và tập kiểm định 82 ca cho fold 1.

Bộ nhớ đệm được đẩy lên Kaggle Dataset `marcohoang/lld-mmri-3` phiên bản 1 (2,71 GB), **để ở chế độ riêng tư** vì giấy phép CC BY-NC-ND cấm phát tán bản phái sinh. Gói tái lập ở W6 vì thế chỉ chia sẻ mã nguồn, danh sách mã bệnh nhân của từng tập, và file cấu hình.

> Phần diễn giải dài hơn về dữ liệu, thuật ngữ và rủi ro dữ liệu nằm ở [`reports/W2_LLD_MMRI_DATA_AUDIT.md`](W2_LLD_MMRI_DATA_AUDIT.md), không lặp lại ở đây.

**Một đính chính về nguồn gốc mặt nạ phân vùng.** Bộ mặt nạ trong `lld/labels` từng được ghi là "`MedSAM2` sinh tự động, không phải chuẩn vàng". Tra lại hai nguồn thì mô tả đó quá phủ định: kho mã chính thức ghi "March 2025: LLD-MMRI dataset now includes segmentation labels" và ghi công Dr. Jun Ma; bản trên HuggingFace ghi rõ "annotated all the 3984 lesions with MedSAM2 in a **human-in-the-loop** pipeline". Tức đây **chính là** nhãn phân vùng chính thức, và có người trong vòng lặp. Vẫn giữ một dè dặt có cơ sở: mức can thiệp của người không được nói rõ, nên dùng làm mục tiêu giám sát phụ thì hợp lý, còn báo cáo chất lượng phân vùng như một kết quả thì phải nêu giới hạn.

## 3. Mô hình nền và năm thí nghiệm có kiểm soát

### 3.1. Số mốc đầu tiên, và việc dừng dò siêu tham số

Lần chạy đầu tiên: `DenseNet121-3D`, 8 kênh vào → 7 lớp (ghép kênh sớm), 11.403.463 tham số, fold 1, hạt giống 1337.

```
macro-F1 kiểm định tốt nhất = 0,2725 @ epoch 11 · dừng sớm @ epoch 26 · ~20s/epoch
mất mát huấn luyện: 1,961 (ep1) → 1,774 (ep11) → 1,641 (ep26)
mất mát kiểm định:  1,989 (ep1) → 2,471 (ep11) → 2,589 (ep26)
```

Đoán ngẫu nhiên với 7 lớp cho macro-F1 ≈ 0,10 và mất mát = ln 7 = 1,946. Mô hình có học, nhưng mất mát huấn luyện chỉ nhích 0,32 dưới mức đoán bừa sau 26 epoch, tức **chưa khớp nổi tập huấn luyện**. Ba lần thử sửa bằng siêu tham số đều thất bại (§4.1); con số ổn định quanh 0,26–0,27 ở hai cấu hình khác nhau.

Thay vì đoán tiếp, dự án chuyển sang **tái lập nguyên khối công thức huấn luyện của bản nền chính thức** (`LMMMEng/LLD-MMRI2023`, macro-F1 0,6083 trên tập kiểm tra 104 ca). Bảng đối chiếu cho thấy sai khác lớn hơn nhiều so với hình dung ban đầu:

| | Bản nền chính thức | Cấu hình của ta trước đó |
|---|---|---|
| số epoch | 300, tốt nhất @ 216 | 60, dừng sớm @ 26 |
| dừng sớm | không có | kiên nhẫn 15 |
| tốc độ học | 1e-4 | 3e-4 |
| **suy giảm trọng số** | **0,05** | **1e-5** (chênh 5.000 lần) |
| khởi động | 5 epoch, tốc độ khởi động 1e-6 | không có |
| hàm mất mát | CrossEntropy trần | CrossEntropy + trọng số lớp |
| lô hiệu dụng | 8 | 4 |
| tăng cường dữ liệu | lật x/y/z · xoay ±10° · cắt ngẫu nhiên | lật x/y · `rot90` · nhiễu cường độ |
| chuẩn hoá | min-max [0,1] | cắt theo phân vị + z-score |
| đầu vào | 112×112×14 | 96×96×48 |

Công thức được áp nguyên khối, mỗi dòng cấu hình kèm trích nguồn, và khoá bằng `tests/test_protocol_conformance.py` để không trôi về sau. Suy giảm trọng số 0,05 chỉ đúng khi loại các tham số bias và tham số chuẩn hoá khỏi phép suy giảm, nên `build_param_groups()` được thêm cùng lúc.

Trước khi tốn GPU, một cổng chặn đo thời gian thật 2 epoch rồi ngoại suy 300 epoch. Nó **chặn lại ngay lần chạy đầu**: 56,5s/epoch → 4,71 giờ mỗi fold → 23,5 giờ cho 5 fold, gần hết hạn mức tuần. Đọc kỹ thì ~36s trong 56,5s là phần tăng cường dữ liệu chạy trên CPU trong khi GPU ngồi chờ. Sửa bằng `num_workers` 2→4, `persistent_workers` và `prefetch_factor`, **thuần tối ưu hoá kỹ thuật, không đụng một phép toán nào trong công thức**.

### 3.2. Bảng kết quả năm thí nghiệm

| | Thay đổi so với lần chạy trước | macro-F1 kiểm định [95% CI] | κ | AURC | ECE thô → sau hiệu chỉnh | Trạng thái |
|---|---|---|---|---|---|---|
| **E0** | công thức chính thức + đệm `fixed_mm` 96×96×48 | 0,4244 [0,314 – 0,530] | 0,276 | 0,5395 | 0,3218 → 0,1455 | xong |
| **E1** | đệm `lesion_tight` (cắt bám tổn thương) | **0,5740** [0,455 – 0,678] | 0,520 | **0,2753** | 0,2935 → 0,2505 | xong |
| **E2** | Siamese đa thì, trọng số dùng chung | ~0,35 – 0,49 @ ep100 | — | — | — | **huỷ** |
| **E3** | hình học 112×112×32 theo tài liệu đã công bố | 0,5566 | — | — | — | xong, **âm** |
| **E4** | căn từng thì theo tổn thương của chính nó | **0,7001** [0,599 – 0,793] | **0,646** | **0,2033** | 0,2458 → 0,1489 | xong, **thắng rõ** |

> **Mọi số trong bảng là tập kiểm định fold 1, 82 bệnh nhân, một hạt giống.** Không phải kết quả báo cáo được: chưa có kiểm định chéo 5 fold, và ở n=82 bề rộng khoảng tin cậy vào khoảng ±0,10. Chúng dùng để **sàng lọc** giữa các phương án, không để công bố.

**E1 so với E0, can thiệp đầu tiên ăn tiền.** Hai lần chạy dùng đúng cùng một cấu hình (đã đối chiếu `config_used.json`: không khác một khoá nào), cùng hạt giống, cùng 82 bệnh nhân kiểm định. Khác biệt duy nhất là bộ nhớ đệm. Bootstrap **ghép cặp** trên cùng tập bệnh nhân: chênh lệch **+0,1496**, khoảng tin cậy 95% **[−0,005, +0,295]**, P(E1 > E0) = 0,973.

Luật quyết định đã chốt **trước** khi chạy: E0 rơi vào dải 0,35–0,50 ⇒ *công thức huấn luyện giải thích phần lớn khoảng cách, quy trình lành*; E1 − E0 vượt xa ngưỡng +0,05 ⇒ *cắt bám tổn thương thành mặc định*. Cả hai phán quyết được đọc theo luật đó, không diễn giải sau khi biết kết quả.

Đáng chú ý: **giả thuyết cơ chế thì sai dù can thiệp đúng.** Dự đoán trước khi chạy là cắt sát sẽ ăn tiền nhờ giảm quá khớp, kèm 4 chỉ báo cụ thể. Ba trong bốn chỉ báo trượt: `val_loss` vẫn chạm đáy ở epoch 9 (E0: epoch 10), chênh lệch huấn luyện với kiểm định ở epoch cuối vẫn +2,5 (E0: +2,8). Cơ chế thật là cắt sát làm **tín hiệu phân biệt mạnh hơn**, chứ không làm mô hình bớt học thuộc. Hai chuyện độc lập.

**E2 bị huỷ vì một biến gây nhiễu đã được cảnh báo trước.** Siamese chạy backbone 8 lượt nên chi phí gấp khoảng 8 lần; để lọt ngân sách phải hạ mẫu đầu vào, và `DenseNet121-3D` lại yêu cầu ≥32 voxel ở mọi chiều (nó hạ mẫu 5 lần), nên chỉ hạ được trong mặt phẳng: 96 → 48. Trong khi mọi phương pháp đã công bố dùng độ phân giải trong mặt phẳng 112–128, tức E2 chạy ở mức thấp hơn 2,3–2,7 lần. E2 vì thế là *Siamese ở mặt phẳng 48* so với *ghép kênh sớm ở mặt phẳng đủ*, không phải phép thử kiến trúc sạch. Điều này đã được ghi rõ trước khi chạy, kèm luật: E2 thắng thì kết luận mạnh, E2 thua thì **không kết luận được**. E2 thua, nên không có kết luận nào về Siamese; hướng này vẫn chưa từng được thử công bằng.

**E3 là một kết quả âm sạch.** Giả thuyết: tỉ lệ trục của ta lệch tài liệu đã công bố (Z=48 so với 14–16, mặt phẳng 96 so với 112–128) và đó là nút thắt. E3 đổi hình học sang 112×112×32, giữ nguyên mọi thứ khác. Kết quả 0,5566 so với E1 0,5740, chênh **−0,017**, nằm sâu trong nhiễu. **Ba hình học khác nhau đều dừng ở trần khoảng 0,57 với cùng kiểu quá khớp** ⇒ giả thuyết tỉ lệ trục bị bác bỏ.

Kết quả âm này nhất quán với, chứ không mâu thuẫn, giả thuyết lệch thì: nếu bản thân các thì không khớp nhau thì đổi khung hình không giải quyết gì.

### 3.3. E4: giả thuyết đã được xác nhận

Con số 23,3mm đo ở §2.3 chưa từng được nối với chất lượng mô hình. Nối vào thì nó lớn hơn hình dung:

| Trục | Độ tán tâm tổn thương giữa 8 thì | Cửa sổ cắt E3 | Tỉ lệ |
|---|---|---|---|
| Trong mặt phẳng | 12,4mm | 53,8mm | 23% |
| **Z (đầu-chân)** | **23,3mm** | **43,6mm** | **53%** |

Ghép kênh sớm có một tiền đề ngầm: voxel `(x, y, z)` của kênh `c` là **cùng một điểm giải phẫu** ở mọi thì. Lệch 53% chiều sâu thì tiền đề đó vỡ, và lớp tích chập đầu tiên đang trộn mô không liên quan với nhau. Đội hạng 2 của cuộc thi lấy chính việc sửa phép căn ảnh làm đóng góp trọng tâm.

E4 căn từng thì về tâm tổn thương của chính nó, dùng khung bao có sẵn trong tệp chú giải; chi phí chỉ là một lần dựng lại bộ nhớ đệm, không cần thuật toán căn ảnh. Spacing và trường nhìn tính một lần từ thì tham chiếu, chỉ đổi tâm, nên 8 khối giữ cùng kích thước vật lý và khác nhau đúng một phép tịnh tiến.

Cổng kiểm quan trọng nhất chạy **trước** khi huấn luyện: `max_shift_mm` phải khác 0 và trung vị trên 3mm. Nếu phép căn không có hiệu lực thì bộ đệm E4 giống hệt E3 và huấn luyện sẽ ra lại đúng 0,5566 sau 4 giờ mà đường cong không hé lộ gì.

Giới hạn phải ghi vào báo cáo cuối: E4 **không** phải phép sửa trung tính. Nó chỉ khử tịnh tiến, không khử xoay hay biến dạng; và mô xung quanh sẽ **thôi khớp** giữa các thì, chỉ tổn thương khớp. Với bài phân loại tổn thương thì đó có thể là điều mong muốn, nhưng nó là một thay đổi ngữ nghĩa dữ liệu.

**Kết quả: 0,7001, mức tăng lớn nhất và là mức tăng duy nhất có ý nghĩa thống kê của cả loạt.**

Cổng kiểm chạy trước khi huấn luyện đã qua: cả 498 ca cắt theo mặt nạ phân vùng, **không ca nào** phải lùi về tâm tham chiếu, `max_shift_mm` trung vị **19,65mm** (nhỏ nhất 2,80 · lớn nhất 111,0). Phép căn có hiệu lực thật, nên kết quả bên dưới không phải bản trùng lặp của E3.

| So cặp (bootstrap trên hiệu, phân tầng, 2000 lần) | Δ macro-F1 | Khoảng tin cậy 95% | P |
|---|---|---|---|
| E4 − E1 | **+0,1261** | **[+0,033, +0,230]** | 0,009 |
| E4 − E0 | +0,2757 | [+0,145, +0,415] | <0,001 |
| E1 − E0 | +0,1496 | [+0,007, +0,289] | 0,040 |

E4 − E1 là lần đầu tiên trong cả loạt có một khoảng tin cậy **nằm hẳn về một phía của 0** với biên rộng rãi. Lưu ý E4 khác E1 ở *hai* khoá (hình học và phép căn), nên phép so một biến sạch là **E4 − E3 = +0,1435**, cùng hình học 112×112×32, chỉ đổi `align_phases`. Vì E3 − E1 = −0,017 (hình học không có tác dụng), toàn bộ mức tăng quy về phép căn.

**Ba chỉ báo cơ chế lần này đều trúng**, khác hẳn E1 (§3.2, nơi can thiệp đúng nhưng cơ chế giải thích sai):

| | E1 | E4 |
|---|---|---|
| `val_loss` chạm đáy ở epoch | 9 | **100** |
| Chênh lệch huấn luyện với kiểm định ở epoch cuối | +2,55 | **+1,50** |
| macro-F1 trung bình 50 epoch cuối | 0,512 | **0,607** |
| Số epoch cuối đạt ≥ 0,60 | 0/50 | **29/50** |
| NLL thô so với đoán mò (1,946) | 3,32 (**tệ hơn đoán mò**) | **1,72 (tốt hơn)** |
| Nhiệt độ hiệu chỉnh (cross-fit) | 5,010 | **2,570** |

Hai dòng cuối quan trọng nhất. Ở E0 và E1, xác suất thô có NLL **cao hơn** mức đoán mò đều, tức phần "độ tin cậy" của mô hình là nhiễu có hại, phải hạ nhiệt gấp 5 lần mới dùng được. E4 là lần chạy đầu tiên mà xác suất thô mang thông tin thật.

Điều này cũng **giải thích luôn chứng quá khớp kinh niên** bị ghi nhận suốt E0–E3: `val_loss` chạm đáy ở epoch 9–10 rồi mô hình chỉ còn học thuộc. Nguyên nhân không nằm ở công thức huấn luyện mà ở đầu vào: khi 8 thì không khớp nhau tới từng voxel thì lớp tích chập đầu tiên không có đặc trưng liên-thì nào để học, nên nó quay sang ghi nhớ. Sửa phép căn đẩy đáy từ epoch 9 sang epoch 100.

F1 tăng ở 5/7 lớp, mạnh nhất ở đúng những lớp trước đây yếu nhất: u máu +0,27, nang +0,26, áp-xe +0,25, di căn +0,16. Hai lớp giảm nhẹ (ICC −0,09 với n=10, FNH −0,05 với n=8) đều ở cỡ mẫu quá nhỏ để đọc.

**Vẫn phải nói rõ điều này:** 0,7001 đo trên tập kiểm định fold 1 (82 ca), còn 0,709 của `ResNet3D` trong bảng CGHNet đo trên tập kiểm tra 104 ca. **Hai tập khác nhau, không được viết là ngang nhau.** Bề rộng khoảng tin cậy ở đây là ±0,10, đủ để một chênh lệch hệ thống 0,03–0,05 ẩn trong đó.

### 3.4. Số đo tính đáng tin đầu tiên

Đây là đóng góp trọng tâm của dự án, nên phần này quan trọng hơn các con số phân loại ở trên.

**Xác suất thô của mô hình gần như vô dụng.** NLL thô của E1 là 3,3182, **tệ hơn đoán mò** (ln 7 = 1,9459). Sau hiệu chỉnh nhiệt độ mới về 1,5205. Nhiệt độ tìm được ở mức 5,0 là cực đoan; E0 cũng ở mức 4,15. Nói cách khác, E1 phân loại giỏi hơn E0 nhưng đồng thời **tự tin thái quá hơn**. Hiệu chỉnh nhiệt độ vì thế là bước bắt buộc, không phải tuỳ chọn ở cuối quy trình.

**Cách ước lượng nhiệt độ ảnh hưởng tới con số nhiều hơn dự kiến.** Ước lượng ngay trên tập đánh giá cho ECE 0,1011; ước lượng chéo 5 phần (cross-fit) cho **0,1455**. Chênh 44%. Chỉ số ước lượng chéo được dùng; số ước lượng trong mẫu không vào báo cáo.

**Một chỉ số đã phải đổi.** Mục tiêu ban đầu là "macro-F1 ≥ 0,90 ở độ phủ 80%". Ở n=82 nó không tính được có nghĩa: tại độ phủ 50%, một lớp hiếm chỉ còn 1–2 ca, F1 của lớp đó do một bệnh nhân quyết định rồi chiếm 1/7 trọng số macro. Quan sát thực tế trên E1: macro-F1 nhảy loạn (0,5740 → 0,5559 → 0,5816 → 0,5211) trong khi accuracy tăng đều và đơn điệu (0,6098 → 0,7561). Chỉ số chính của dự đoán có chọn lọc vì thế **đổi sang đường cong rủi ro–độ phủ và AURC**, và phải tính trên tập gộp ngoài fold 394 ca thay vì một fold. Theo AURC thì E1 (0,2753) tốt hơn E0 (0,5395) gần gấp đôi, và E4 (0,2033) tốt hơn E1 thêm một bậc nữa.

## 4. Bài học phương pháp

Mục này ghi lại phần tốn kém nhất của W2. Nó nằm trong báo cáo vì các cơ chế sinh ra từ đây (§4.5) là tài sản thật của dự án.

### 4.1. Ba chẩn đoán sai liên tiếp, ba lần chạy GPU

| # | Giả thuyết | Cách bác bỏ | Chi phí |
|---|---|---|---|
| 1 | "BatchNorm với lô 2 làm mất mát kiểm định phân kỳ" | Đổi sang InstanceNorm → macro-F1 đứng yên 0,0668 qua 4 epoch, mất mát huấn luyện ≈ ln 7 | 1 lần chạy |
| 2 | "InstanceNorm sập vì lớp gộp trung bình toàn cục xoá mất tín hiệu" | Phép thử khớp quá 8 mẫu → InstanceNorm đạt accuracy 1,00, chỉ chậm hơn khoảng 60 lần | 1 lần chạy |
| 3 | "Mô hình thiếu bước cập nhật (~20 bước mỗi epoch)" | Gấp 4 lần số bước → 0,2647 so với 0,2725, chênh nằm gọn trong nhiễu | 1 lần chạy |

Cả ba đều là **suy luận từ đường cong**, và cả ba đều tốn một lần chạy để bác bỏ. Hai lỗi cụ thể đáng ghi:

- **Bê lập luận từ bài toán phân vùng sang bài toán phân loại.** InstanceNorm hợp với nnU-Net vì nnU-Net không có lớp gộp trung bình toàn cục; DenseNet thì có. Sự khác biệt đó tốn một lần chạy.
- **Chẩn đoán từ 4 epoch khi mỗi epoch chỉ có 20 bước cập nhật.** Số bước = số mẫu / (lô × số lần tích luỹ). Không tính con số đó trước khi diễn giải bất kỳ đường cong nào là gốc của cả ba lần sai.

### 4.2. Nguyên nhân chung: gỡ lỗi mà không biết ngưỡng đạt được

Tài liệu của cuộc thi nằm sẵn trong `docs/` từ đầu tuần và không được tra. Trong đó có bảng xếp hạng chính thức:

| | macro-F1 (tập kiểm tra 104 ca) | κ |
|---|---|---|
| Đội nhất | 0,8322 | 0,7801 |
| **Bản nền chính thức** (UniFormer-S 3D, huấn luyện từ đầu) | **0,6083** | 0,5414 |
| Hạng 20–24 | 0,5047 – 0,6076 | |

Chỉ số của họ là `sklearn.f1_score(average='macro')` và `cohen_kappa_score`, khớp `src/eval/metrics.py`, đã thêm kiểm thử đối chiếu trực tiếp.

Sang W2 muộn hơn, một nguồn còn hữu ích hơn xuất hiện: bảng so sánh **cùng một quy trình** của CGHNet (Comput Med Imaging Graph 132, 2026), mọi hàng dùng đúng một cách tiền xử lý và đều báo trên tập kiểm tra 104 ca chính thức:

```
ViT3D 0,645 · ResNet2D 0,684 · ConvNeXt2D 0,696 · ResNet3D 0,709
Swin3D 0,709 · 3D UX-Net 0,709 · Uniformer 0,719 · SDR-Former 0,791
STM-Former 0,793 · RadioFormer 0,806 · CGHNet 0,818
```

Con số đắt nhất trong bảng: **một `ResNet3D` trần đạt 0,709**, vượt bản nền chính thức 0,10 điểm, chỉ nhờ hình học đầu vào 16×128×128 → cắt còn 14×112×112. Đây là bằng chứng mạnh nhất cho hướng "dữ liệu quan trọng hơn kiến trúc" mà E0→E1 đã xác nhận bằng thực nghiệm.

Bảng khảo sát loại bỏ về huấn luyện của họ cũng cho ba đòn bẩy cụ thể: Focal Loss 81,8 so với CrossEntropy 79,9; **bỏ phép cắt ngẫu nhiên mất 8,8 điểm** (biến tăng cường dữ liệu nặng nhất); tốc độ học 1e-4 tốt hơn cả 1e-3 lẫn 1e-5.

Luật đã được ghi vào `AGENTS.md` §5: **ai định gỡ lỗi chất lượng mô hình đều phải đối chiếu bảng này trước.**

Một đính chính trong chính quá trình đọc bài báo: bản in từ trang ScienceDirect làm mất các bảng số, dẫn tới việc đọc nhầm một bảng khảo sát nội bộ (hai nhánh khác kiến trúc) thành phép thử 2D so với 3D, và kết luận sai rằng nhánh 2.5D nên được nâng lên ứng viên chính. Đọc lại bản PDF gốc thì phép thử sạch nằm ở bảng khác và cho kết quả ngược: `ResNet3D` 0,709 thắng `ResNet2D` 0,684. Đề xuất đã bị rút lại.

### 4.3. Một sai sót so sánh chưa được sửa hết

Suốt E0 → E3, số của dự án là **tập kiểm định fold 1 (82 bệnh nhân)** trong khi số của tài liệu đã công bố là **tập kiểm tra 104 ca**. Hai tập khác nhau.

Các so sánh **nội bộ** (E0 với E1, E1 với E3) vẫn sạch: cùng tập, cùng hạt giống, cùng cấu hình. Nhưng mọi câu dạng "E1 còn cách bản nền chính thức 0,034" là **không có cơ sở vững**. Con số 0,5740 không được đặt cạnh 0,6083 như thể chúng cùng thang đo. Điều này ảnh hưởng tới cách đọc tiến độ, không tới tính hợp lệ của các quyết định thí nghiệm đã ra.

### 4.4. Thiên lệch chọn epoch

Đường cong macro-F1 kiểm định của lần chạy nền dao động không xu hướng qua 26 epoch:

```
0,141 0,163 0,146 0,115 0,159 0,164 0,149 0,159 0,189 0,147 [0,265] 0,216
0,145 0,175 0,234 0,219 0,186 0,208 0,236 0,192 0,191 0,215 0,209 0,193 0,239 0,255
```

Epoch 11 không phải cực trị thật, nó là **lần bốc may nhất trong 26 lần**. Chọn epoch tốt nhất theo macro-F1 trên 82 ca kiểm định là chọn nhiễu, cùng bệnh lý với "chọn hạt giống may nhất trong nhiều hạt giống" mà nguyên tắc dự án cấm, chỉ khác là chọn theo epoch. Quy trình nay lưu thêm `val_probs_last.npz` mỗi epoch để W3 đo được chính độ lệch này.

### 4.5. Những cơ chế đã dựng để không tái diễn

| Cơ chế | Bắt được gì |
|---|---|
| Phép thử khớp quá 8 mẫu (`src/train/sanity.py`) | Phân biệt "bài toán khó" với "quy trình hỏng" trong 30 giây |
| Cổng đo thời gian trước khi huấn luyện | Chặn một lần chạy 23,5 giờ **trước** khi tốn hạn mức |
| `run_dir` băm theo khối `model:` | Hai kiến trúc không bao giờ dùng chung thư mục, không khôi phục đè nhau |
| Cổng đối chiếu nhãn trong bộ đệm với `splits/` | Rủi ro nặng nhất còn sót: nhãn lệch thì huấn luyện vẫn trơn, chỉ số vẫn ra số, kết quả vô nghĩa |
| Cổng dừng khi quét ra 0 mặt nạ phân vùng | Bắt được lỗi khiến 20/20 ca lặng lẽ rơi về khung bao mà quá trình dựng đệm vẫn báo "hoàn tất" |
| `tests/test_protocol_conformance.py` | Khoá cấu hình theo công thức chính thức, báo lỗi nếu trôi |
| **Luật quyết định chốt trước khi chạy** | Chống hợp lý hoá sau khi biết kết quả; đã dùng để đọc E0/E1, E3 và E4 |
| 245 kiểm thử / 17 bỏ qua | Trong đó kiểm thử chống rò rỉ cố ý không phụ thuộc torch, luôn chạy được |

Một quy trình cũng được thiết lập: **trước khi bàn giao thứ gì tốn GPU, rà hết đường chạy; thứ nào không kiểm được ở máy cá nhân thì tải mã nguồn thư viện về đọc, hoặc biến thành một phép `assert` rẻ tiền chạy trước phần tốn kém.** Lần áp dụng đầu tiên bắt được 5 lỗi mà không tốn một phút GPU nào, trong đó có một lỗi im lặng: `InstanceNorm3d` của PyTorch mặc định `affine=False`, tức bản sửa trước đó đã bỏ mất phần co giãn và dịch chuyển học được ở mọi lớp chuẩn hoá.

## 5. Trạng thái và giới hạn

| Hạng mục | Trạng thái | Bằng chứng | Nhận xét |
|---|---|---|---|
| Bộ chia chính thức + khoá + kiểm thử rò rỉ | Hoàn thành | 12 file `splits/`, 245 kiểm thử xanh | Khôi phục khả năng so sánh trực tiếp. |
| Cổng hình học trên dữ liệu thật | Hoàn thành | đạt 3.984/3.984 | Điều kiện tiên quyết cho việc cắt theo khung bao. |
| Bộ đệm v0 `fixed_mm` | Hoàn thành | 498 `.npz`, Kaggle Dataset v1 | Đã bị E1 thay thế làm mặc định. |
| Bộ đệm `lesion_tight` | Hoàn thành | E1 chạy trên nó | Đã bị bộ đệm E4 thay thế làm mặc định. |
| Mô hình nền 3D-patch, 1 fold | Hoàn thành | **0,7001** kiểm định fold 1 (E4) | Chưa có kiểm định chéo, chưa phải số báo cáo. |
| Mô hình nền 2.5D | **Bị cắt** | — | Đúng thứ tự cắt đã định; bằng chứng ngoài ủng hộ. |
| Hợp nhất Siamese (E2) | **Chưa kết luận** | lần chạy bị huỷ vì biến gây nhiễu | Phải chạy lại ở hình học đúng mới đánh giá được. |
| Khảo sát hình học (E3) | Hoàn thành, kết quả âm | 0,5566 so với 0,5740 | Bác bỏ giả thuyết tỉ lệ trục. |
| Căn từng thì (E4) | **Hoàn thành, thắng rõ** | 0,7001; Δ so E1 +0,126, CI [+0,033, +0,230] | **Cấu hình chốt.** Cổng `max_shift_mm` đã qua (trung vị 19,65mm, 0 ca lùi về tâm tham chiếu). |
| Hiệu chỉnh xác suất + dự đoán có chọn lọc | Mã xong, số mới 1 fold | ECE/AURC/nhiệt độ của E0, E1, E4 | Cần gộp ngoài fold 394 ca. |
| Kiểm định chéo 5 fold + khoảng tin cậy | Đã dựng notebook, chưa chạy | `notebooks/07_e4_cv_folds.ipynb` | Việc đầu tiên của W3; ~3,9h mỗi fold, 2 fold mỗi phiên. |
| Căn ảnh thật (rigid) | Chưa bắt đầu | — | E4 cho thấy hướng này đáng đầu tư, nhưng xếp sau kiểm định chéo. |
| Ngoại kiểm / dữ liệu ngoài phân phối | Chưa bắt đầu | — | Theo kế hoạch W3. |
| **Tập kiểm tra 104 ca** | **Chưa chạm** | không có đường mã nào dẫn tới nó | Đúng quy trình; chỉ chạm một lần ở W5. |

**Giới hạn phải nói rõ với người đọc:**

1. **Mọi con số của dự án là 1 fold, 82 bệnh nhân kiểm định, một hạt giống.** Không có khoảng tin cậy cho phần lớn chúng, và ở n=82 bề rộng khoảng tin cậy khoảng ±0,10, đủ để nuốt trọn chênh lệch giữa E1 và E3.
2. **Không so trực tiếp được với tài liệu đã công bố** (§4.3). Số của họ đo trên tập kiểm tra 104 ca.
3. **Ngay cả khi có kết quả tốt, việc chứng minh vượt mức tốt nhất hiện nay là bất khả thi ở cỡ mẫu này.** Bootstrap ở n=104 cho bề rộng khoảng tin cậy ±0,077 tại mức 0,8322 và ±0,061 tại 0,90, hai khoảng chồng nhau. (So hai khoảng biên là phép bảo thủ; kiểm định ghép cặp mạnh hơn. Nhưng thông điệp không đổi: định vị của dự án phải là tính đáng tin, không phải bảng xếp hạng.)
4. **Quá khớp đã nhẹ đi nhiều nhưng chưa hết.** `val_loss` chạm đáy ở epoch 9–10 ở E0/E1/E3; ở E4 là epoch 100 và chênh lệch cuối giảm từ +2,55 xuống +1,50. Nguyên nhân gốc hoá ra là lệch thì ở đầu vào chứ không phải công thức huấn luyện, nên các hướng chỉnh tỉ lệ bỏ nơ-ron hay suy giảm trọng số trước đây đều là nhắm sai chỗ.
5. **`deterministic: true` không cho tái lập tới từng bit.** `DenseNet` với `spatial_dims=3` không tất định trên CUDA. Hạt giống cố định cho phép lặp lại *thí nghiệm*, không phải lặp lại từng chữ số. Đây là một lý do nữa để mọi số đều kèm khoảng tin cậy.

## 6. Công việc tiếp theo theo thứ tự ưu tiên

Thứ tự này **đổi so với luật đã chốt ở §3.3**, và lý do phải nói rõ. Luật viết trước khi chạy E4 nói: nếu đạt ≥0,62 thì đi tiếp sang căn ảnh cứng thật rồi Siamese. E4 đạt 0,7001, vượt xa ngưỡng đó, nhưng chính vì vượt xa mà ràng buộc đã đổi. Nút thắt bây giờ không còn là "tìm cấu hình tốt hơn" mà là **chưa có một con số nào báo cáo được**: không kiểm định chéo, không tổ hợp mô hình, khoảng tin cậy rộng ±0,10. Thêm một thí nghiệm sàng lọc nữa chỉ làm kiểm định chéo về sau đắt hơn. Vì vậy:

1. **Chạy đủ 5 fold cho cấu hình E4** → bảng kiểm định chéo macro-F1/κ kèm khoảng tin cậy bootstrap ở mức bệnh nhân (≥2000 lần). Notebook đã dựng: `notebooks/07_e4_cv_folds.ipynb`, khoảng 3,9 giờ mỗi fold, 2 fold mỗi phiên. Đây là sản phẩm chính của W3 và là điều kiện để mọi so sánh sau có nghĩa.
2. **Gộp ngoài fold 394 ca** rồi tính lại hiệu chỉnh xác suất và đường cong rủi ro–độ phủ trên cỡ mẫu đó. Ở 394 ca thì macro-F1 tại một mức độ phủ mới dùng được; ở n=82 nó vô nghĩa (§3.4).
3. **Dựng tổ hợp mô hình sâu (deep ensemble) từ 5 điểm lưu đó.** Đây không phải việc phụ: mức bất định *nhận thức* (epistemic) được đo bằng mức bất đồng giữa các thành viên, nên **toàn bộ đóng góp trọng tâm của đề tài phụ thuộc vào bước 1**. Một mô hình đơn lẻ không đo được nó.
4. **Căn ảnh cứng thật.** E4 mới chỉ khử tịnh tiến theo tâm tổn thương; nó không khử xoay hay biến dạng, và làm mô xung quanh thôi khớp. Việc E4 ăn tiền lớn đến vậy là bằng chứng mạnh rằng phần dư còn lại cũng đáng lấy.
5. **Đổi backbone sang `ResNet3D` ở đúng 14×112×112** (`ResNet3D` trần đạt 0,709 dưới quy trình thống nhất). `DenseNet121-3D` không chịu được Z=14 nên đây bắt buộc là đổi kiến trúc, không chỉ đổi cấu hình.
6. **Focal Loss** (+1,9 điểm theo bảng khảo sát của CGHNet) và khảo sát phần tăng cường dữ liệu.
7. **Đánh giá lại hợp nhất Siamese ở hình học đúng.** E2 chưa từng được thử công bằng, và giờ nó còn có thêm lý do: trên dữ liệu đã căn đúng, bộ mã hoá dùng chung trọng số hợp lý hơn hẳn.
8. **Ngoại kiểm + dữ liệu Duke làm tập ngoài phân phối.** Đây là sản phẩm của Sprint 1 chưa bắt đầu, và là việc chạy trên CPU nên làm song song được, không tranh ngân sách GPU với bước 1.
9. **Khoá quy trình, ngưỡng quyết định và nhiệt độ hiệu chỉnh trên tập kiểm định**, ghi WORKLOG, rồi chạm tập kiểm tra 104 ca đúng một lần.

## 7. Dòng thời gian

| Thời điểm | Mốc |
|---|---|
| 24/07/2026 | Lập kế hoạch W2 chi tiết; xem xét dữ liệu `LLD-MMRI` trên Kaggle; **tái lập và kiểm chứng bộ chia chính thức 316/78/104**; dựng khung `src/utils`, `src/data`; kiểm thử chống rò rỉ đầu tiên. |
| 24/07/2026 (tối) | Dựng đường chạy trên Kaggle; **cổng hình học đạt trên dữ liệu thật**. |
| 27/07/2026 | Quy trình tiền xử lý trong không gian mm; phán quyết `axis_order = xy`; dựng bộ đệm 498 ca; mô hình nền ra **số mốc đầu tiên 0,2725**; ba chẩn đoán sai; tra bảng xếp hạng và **áp nguyên khối công thức chính thức**; hạ tầng khoảng tin cậy bootstrap. |
| 28/07/2026 | Bộ đệm `lesion_tight`; `calibration.py` + `selective.py`; tính bề rộng khoảng tin cậy ở n=104. |
| 29/07/2026 | **E0 = 0,4244 · E1 = 0,5740**; phân tích hiệu chỉnh xác suất và dự đoán có chọn lọc; dựng E2 Siamese. |
| 30/07/2026 | Đọc CGHNet (bảng so sánh cùng quy trình); huỷ E2; **E3 = 0,5566, kết quả âm**; dựng E4 và notebook. |
| 31/07/2026 | Tổng hợp báo cáo W2; **E4 = 0,7001, mức tăng duy nhất có ý nghĩa thống kê** (Δ so E1 +0,126, CI [+0,033, +0,230]); chốt cấu hình E4; dựng notebook kiểm định chéo 5 fold. |

## Kết luận cho người hướng dẫn

**Về hạ tầng:** quy trình từ ảnh MRI thô đến bảng chỉ số đã chạy được và tái lập được. Mọi cổng an toàn khoa học đều đứng: bộ chia khoá ở mức bệnh nhân và đã commit, kiểm thử chống rò rỉ xanh, thống kê chuẩn hoá không xuyên bệnh nhân, và **tập kiểm tra 104 ca chưa bị chạm một lần nào**, không có đường mã nào dẫn tới nó.

**Về kết quả:** con số tốt nhất hiện tại là macro-F1 **0,7001** trên tập kiểm định fold 1. Nó chưa so trực tiếp được với tài liệu đã công bố (khác tập đánh giá), chưa có kiểm định chéo, và chưa nên được coi là kết quả cuối. Điều đáng nói không phải bản thân con số mà là **cách nó tăng**: toàn bộ mức tăng từ 0,26 lên 0,70 đến từ việc tái lập công thức huấn luyện và **hai thay đổi về cách chuẩn bị dữ liệu**: cắt bám tổn thương, rồi căn từng thì về tổn thương của chính nó. **Không một dòng nào của kiến trúc mô hình bị đụng tới.** Ba hướng đi theo kiến trúc hoặc hình học (E2, E3, và các lần chỉnh chuẩn hoá) đều không cho gì.

**Về tính đáng tin**, đóng góp trọng tâm của dự án, đã có số thật, và chúng cho thấy vấn đề vừa có thật vừa cải thiện được. Ở E0 và E1, xác suất thô của mô hình có NLL **tệ hơn đoán mò** (3,32 so với 1,95) và cần hạ nhiệt gấp khoảng 5 lần mới dùng được, tức phần "độ tin cậy" là nhiễu có hại. Ở E4, NLL thô xuống 1,72, tốt hơn đoán mò lần đầu tiên, và nhiệt độ cần thiết giảm còn 2,57. AURC đi từ 0,540 → 0,275 → **0,203**. Một mục tiêu đã phải phát biểu lại vì cỡ mẫu (macro-F1 tại một mức độ phủ cố định không tính được có nghĩa ở n=82; chuyển sang đường cong rủi ro–độ phủ và AURC cho tới khi gộp được ngoài fold 394 ca).

**Điều cần lưu ý nhất khi đọc báo cáo này:** đóng góp trọng tâm vẫn **chưa đo được đầy đủ**, vì mức bất định nhận thức cần 5 mô hình của 5 fold và hiện mới có 1. Đó là lý do việc đầu tiên của W3 là chạy nốt kiểm định chéo chứ không phải thử thêm ý tưởng.

**Bài học lớn nhất của W2** là về phương pháp chứ không về mô hình: bốn chẩn đoán sai đều sinh ra từ việc gỡ lỗi mà không biết ngưỡng đạt được là bao nhiêu. Luật "đối chiếu mốc ngoài trước khi gỡ lỗi chất lượng mô hình" nay đã được ghi vào tài liệu ngữ cảnh của dự án, cùng một bộ cổng chặn tự động để những sai lầm cùng loại tốn 30 giây thay vì một phiên GPU.

---

*Research Use Only. Mọi số trong báo cáo này là kết quả sàng lọc trên tập kiểm định, chưa qua kiểm định chéo và chưa có khoảng tin cậy đầy đủ; chúng không phải kết quả nghiên cứu được công bố và không được dùng để suy diễn về hiệu năng lâm sàng.*
