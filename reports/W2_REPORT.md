# Báo cáo W2: nền dữ liệu, baseline đầu tiên và 5 lần train có kiểm soát

**Người thực hiện:** Hoàng Đức Trường
**Ngày tổng hợp:** 31/07/2026
**Kỳ báo cáo:** 24/07 – 31/07/2026
**Trạng thái:** Research Use Only (RUO); không dùng để chẩn đoán hay thay thế bác sĩ.

## Tóm tắt

Đầu W2 dự án chưa có `src/`, chưa tải LLD-MMRI, chưa có một dòng code chạy được. Cuối W2 có một pipeline hoàn chỉnh từ MRI thô đến bảng metric: reader 8 thì, gate hình học chạy trên dữ liệu thật, split chính thức 316/78/104 đã tái lập và khoá, cache tiền xử lý 498 ca đẩy lên Kaggle Dataset, vòng train có checkpoint/resume, và bộ eval gồm bootstrap CI, calibration và selective prediction. 245 test xanh, trong đó có test chống leakage.

Về kết quả, số mốc đầu tiên là macro-F1 val **0,2725**. 5 lần train có kiểm soát sau đó đưa con số lên **0,7001** (E4), và **toàn bộ mức tăng đến từ thay đổi về dữ liệu, không một hyperparam nào bị đụng tới**: cắt patch bám sát tổn thương (+0,15) rồi căn từng thì về tổn thương của chính nó (+0,13, 95% CI [+0,033; +0,230]). Hai lần train còn lại cho kết quả âm hoặc bị huỷ, trong đó giả thuyết "tỉ lệ trục là nút thắt" bị bác bỏ sạch.

Phần lớn thời gian W2 bị tiêu vào một chuỗi bốn chẩn đoán sai, được ghi lại đầy đủ ở §4, vì bài học phương pháp rút ra từ đó có giá trị lâu dài hơn bất kỳ con số nào ở §3.

## 1. Mục tiêu W2 và trạng thái Definition of Done

Mục tiêu W2: đưa LLD-MMRI vào một pipeline tái lập được, có file split khoá mức bệnh nhân, và một con số baseline đầu tiên làm mốc so sánh cho các tuần sau.

| Definition of Done (theo `docs/W2_plan.md`) | Trạng thái | Bằng chứng |
|---|---|---|
| EDA notebook: phân bố 7 lớp, spacing, shape, thiếu pha | Đạt | `notebooks/01_eda.ipynb`, `scripts/kaggle_geometry_report.py` |
| Preprocessing v0 cache thành Kaggle Dataset có version | Đạt | 498 `.npz`, `marcohoang/lld-mmri-3` v1, private |
| `splits/` official 12 file đã commit, bất biến, validate | Đạt | `labels_trainval.txt` 394 + `test_official.txt` 104 = 498 |
| `pytest` leakage test pass (giao tập bệnh nhân mọi cặp fold = ∅) | Đạt | 245 passed, 17 skipped |
| Baseline **3D-patch** chạy 1 fold, ra macro-F1 val | Đạt | 0,2725 → **0,7001** sau các thí nghiệm |
| Baseline **2.5D** chạy 1 fold, ra macro-F1 val | **Không đạt** | Bị cắt có chủ ý |
| Cập nhật bảng lệnh `AGENTS.md` §6 | Đạt | mọi entrypoint đều có dòng lệnh tương ứng |

**Về mục không đạt.** Baseline 2.5D nằm ở vị trí thứ hai trong danh sách "task cắt được nếu trễ" của chính `docs/W2_plan.md`. Nó bị cắt theo đúng thứ tự đã định trước, không phải bỏ quên. Bằng chứng ngoài (§4.2) sau đó cho thấy quyết định này không gây thiệt hại: trong bảng so sánh cùng protocol của CGHNet, ResNet3D (0,709) thắng ResNet2D (0,684), nên nhánh 3D vẫn là hướng đúng.

**Hai lệch so với kế hoạch, cả hai đều nên ghi rõ.**

- **Giao sớm hơn kế hoạch:** `src/eval/bootstrap.py` (thuộc W3), `src/eval/calibration.py` và `src/eval/selective.py` (thuộc W5), `src/eval/run.py`. Bộ eval đã sẵn sàng trước khi có model đáng đánh giá.
- **Tràn sang địa hạt W3/W4:** 5 thí nghiệm E0–E4 là công việc so sánh kiến trúc/dữ liệu, vốn thuộc W3–W4. Đây là scope creep có ý thức: baseline dừng ở 0,26 trong khi baseline chính thức của challenge đạt 0,6083, nên tiếp tục sang W3 với một pipeline chưa rõ có lành hay không là rủi ro lớn hơn.

## 2. Nền dữ liệu: từ MRI thô đến cache train-ready

Dataset là bản dump nguyên si của `wanglab/LLD-MMRI-MedSAM2`: 498 bệnh nhân × 8 thì = 3.984 volume `.nii.gz`, cộng `LLD_MMRI_Annotation.json` giữ nhãn 7 lớp và bbox 2D theo từng slice. Phân bố lớp: HCC 157 · u máu 79 · ICC 58 · áp-xe 54 · nang 53 · di căn 51 · FNH 46. Mất cân bằng vừa phải (3,4:1), không phải long-tail.

### 2.1. Split official được tái lập và verify

Bản wanglab không kèm split. Quyết định ban đầu là tự chia 5-fold stratified; quyết định đó đã bị đảo sau khi tìm được `labels_trainval.txt` (394 ca) trong repo của một đội dự thi, từ đó suy ra test-104 = 498 − 394. Phân bố lớp của bản tái lập khớp PDF official **7/7 lớp**, nên split 316/78/104 được coi là khôi phục thành công.

Đây là quyết định đắt giá nhất về mặt phương pháp trong cả tuần: nó khôi phục khả năng so benchmark trực tiếp với leaderboard của challenge. Tự chia thì mọi con số sau này chỉ so được với chính mình. 12 file được commit vào `splits/` và quality gate chặn mọi thay đổi lên thư mục đó.

### 2.2. Gate hình học chạy trên dữ liệu thật trước khi crop

Rủi ro cụ thể: bản MedSAM2 có thể đã resample/reorient ảnh trong khi bbox vẫn ở toạ độ gốc. Nếu vậy thì mọi patch cắt theo bbox đều lệch, và không có gì trong quá trình train báo hiệu điều đó.

Gate đối chiếu `spacing` trong header ảnh so với `pixel_spacing`/`slice_spacing` trong annotation, cộng kiểm `slice_idx` và bbox có nằm trong biên không. Kết quả: **PASS 3.984/3.984 phase-check**. Ảnh không bị resample, toạ độ bbox dùng thẳng được.

Gate cũng lộ ra hai chuyện chưa lường trước:

- **8 thì của cùng một bệnh nhân không cùng lưới voxel.** Ví dụ MR-398189: pha động 512×512×88 @2,6mm, T2WI 512×512×24 @9mm, DWI 256×256×24. Mọi code giả định 8 thì `stack` thẳng được đều sai.
- **Nhóm In/Out Phase không cố định.** Ở phần lớn ca chúng đi cùng pha động; ở một số ca lại đi cùng nhóm T2WI. Thiết kế fusion tách "structural so với dynamic" vì thế không hardcode nhóm được.

### 2.3. Phán quyết thứ tự trục, và một bẫy phép đo

Annotation không nói rõ `2D_box` là `(x, y)` hay `(y, x)`. Ảnh đều vuông (512², 256², 384²) nên bbox lọt cả hai cách hiểu, không đoán được bằng mắt, và đoán sai thì mọi patch lệch 90°.

Cách giải: annotation có bbox riêng cho từng thì, mà cùng một tổn thương vật lý thì 8 tâm phải hội tụ trong toạ độ thế giới. Cách hiểu sai làm chúng tán ra.

Lần đo đầu tiên trả về `inconclusive`: 83/90 phiếu (92%) cho `xy` nhưng độ tán trung vị 26,3mm vượt ngưỡng. Phân rã theo trục cho thấy lỗi nằm ở phép đo, không ở dữ liệu:

| Cách hiểu | X | Y | Z |
|---|---|---|---|
| `xy` | **7,4** | 10,3 | 23,3 |
| `yx` | 13,9 | 11,2 | 23,3 |

Trục Z giống hệt nhau ở cả hai cách hiểu (hoán vị trục chỉ đụng X/Y), và 23,3mm chính là biên độ chuyển động hô hấp của gan: 8 thì được chụp ở các lần nín thở khác nhau. Đưa Z vào vừa đẩy tổng độ tán vượt ngưỡng vừa làm loãng tín hiệu phân biệt.

Sau khi chỉ đo in-plane: **180/498 ca có sức phân biệt (gấp đôi), `xy` được 166 phiếu (92%), độ tán 12,4mm**. Chốt `axis_order = xy`.

Con số 23,3mm này được ghi lại và về sau trở thành cơ sở của thí nghiệm E4 (§3.3).

### 2.4. Cắt trong không gian mm, không phải voxel

Vì 8 thì khác lưới, bbox voxel của thì này vô nghĩa với thì kia. Nhưng cả 8 chung hệ toạ độ bệnh nhân. Cách làm: đổi tâm bbox sang mm → dựng một lưới đích chung 96×96×48 @1,5×1,5×3,0mm quanh tâm đó → lấy mẫu cả 8 thì lên lưới ấy.

Đây đồng thời là một phép căn thô, nên registration riêng được hoãn sang W3 làm ablation. Chuẩn hoá dùng thống kê của chính volume bệnh nhân đó, không gộp xuyên bệnh nhân, nên không vi phạm nguyên tắc chống leakage.

`build_cache` từ chối chạy khi `axis_order` để trống; thà dừng còn hơn cắt sai trục rồi mọi kết quả sau đều vô nghĩa.

### 2.5. Cache

Build hoàn tất 498/498 ca, bỏ qua 0, lỗi 0, trong 24 phút. Kiểm nghiệm thu: 498 file `.npz`, shape đồng nhất `(8, 96, 96, 48)`, không NaN/Inf. DataLoader dựng được train=312 / val=82 cho fold 1.

Cache được đẩy lên Kaggle Dataset `marcohoang/lld-mmri-3` version 1 (2,71 GB), để private vì license CC BY-NC-ND cấm phát tán bản phái sinh. Reproducibility pack ở W6 vì thế chỉ chia code + split ID + config.

> Phần diễn giải dài hơn về dataset, thuật ngữ và rủi ro dữ liệu nằm ở [`reports/W2_LLD_MMRI_DATA_AUDIT.md`](W2_LLD_MMRI_DATA_AUDIT.md), không lặp lại ở đây.

**Một đính chính về nguồn gốc mask.** Bộ mask trong `lld/labels` từng được ghi là "MedSAM2 sinh tự động, không phải chuẩn vàng". Tra lại hai nguồn thì mô tả đó quá phủ định: repo official ghi "March 2025: LLD-MMRI dataset now includes segmentation labels" và ghi công Dr. Jun Ma; bản HuggingFace ghi rõ "annotated all the 3984 lesions with MedSAM2 in a human-in-the-loop pipeline". Tức đây chính là nhãn segmentation official, và có người trong vòng lặp. Vẫn giữ một dè dặt có cơ sở: mức can thiệp của người không được nói rõ, nên dùng làm mục tiêu giám sát phụ thì hợp lý, còn báo cáo chất lượng segmentation như một kết quả thì phải nêu giới hạn.

## 3. Baseline và 5 thí nghiệm có kiểm soát

### 3.1. Số mốc đầu tiên, và việc dừng tune

Run đầu tiên: DenseNet121-3D, 8 kênh vào → 7 lớp (early concat), 11.403.463 tham số, fold 1, seed 1337.

```
best macro-F1 val = 0,2725 @ epoch 11 · early stop @ epoch 26 · ~20s/epoch
train loss: 1,961 (ep1) → 1,774 (ep11) → 1,641 (ep26)
val loss:   1,989 (ep1) → 2,471 (ep11) → 2,589 (ep26)
```

Ngẫu nhiên với 7 lớp là macro-F1 ≈ 0,10 và CE = ln 7 = 1,946. Model có học, nhưng train loss chỉ nhích 0,32 dưới mức đoán bừa sau 26 epoch, tức chưa fit nổi tập train. Ba lần thử sửa bằng hyperparam đều thất bại (§4.1); con số ổn định quanh 0,26–0,27 ở hai cấu hình khác nhau.

Thay vì đoán tiếp, dự án chuyển sang **tái lập nguyên khối recipe của baseline chính thức** (`LMMMEng/LLD-MMRI2023`, macro-F1 0,6083 trên test-104). Bảng đối chiếu cho thấy sai khác lớn hơn nhiều so với hình dung ban đầu:

| | Baseline chính thức | Cấu hình của ta trước đó |
|---|---|---|
| epochs | 300, best @ 216 | 60, early stop @ 26 |
| early stopping | không có | patience 15 |
| learning rate | 1e-4 | 3e-4 |
| **weight decay** | **0,05** | **1e-5** (chênh 5.000 lần) |
| warmup | 5 epoch, warmup-lr 1e-6 | không có |
| loss | CrossEntropy trần | CE + class weights |
| batch hiệu dụng | 8 | 4 |
| augment | flip x/y/z · xoay ±10° · random crop | flip x/y · rot90 · nhiễu cường độ |
| chuẩn hoá | min-max [0,1] | percentile clip + z-score |
| input | 112×112×14 | 96×96×48 |

Recipe được áp nguyên khối, mỗi dòng config kèm trích nguồn, và khoá bằng `tests/test_protocol_conformance.py` để không trôi về sau. Weight decay 0,05 chỉ đúng khi loại bias và tham số norm khỏi decay, nên `build_param_groups()` được thêm cùng lúc.

Trước khi tốn GPU, một gate đo thời gian thật 2 epoch rồi ngoại suy 300 epoch. Nó chặn lại ở lần chạy đầu: 56,5s/epoch → 4,71 giờ/fold → 23,5 giờ cho 5 fold, gần hết quota tuần. Đọc kỹ thì ~36s trong 56,5s là augmentation chạy trên CPU trong khi GPU ngồi chờ. Sửa bằng `num_workers` 2→4, `persistent_workers` và `prefetch_factor`, thuần tối ưu hoá kỹ thuật, không đụng một phép toán nào trong recipe.

### 3.2. Bảng kết quả 5 thí nghiệm

| | Thay đổi so với run trước | macro-F1 val [95% CI] | κ | AURC | ECE thô → sau T | Trạng thái |
|---|---|---|---|---|---|---|
| **E0** | recipe official + cache `fixed_mm` 96×96×48 | 0,4244 [0,314–0,530] | 0,276 | 0,5395 | 0,3218 → 0,1455 | xong |
| **E1** | cache `lesion_tight` (cắt bám tổn thương) | **0,5740** [0,455–0,678] | 0,520 | **0,2753** | 0,2935 → 0,2505 | xong |
| **E2** | Siamese đa pha, trọng số dùng chung | ~0,35 – 0,49 @ ep100 | — | — | — | **huỷ** |
| **E3** | hình học 112×112×32 theo văn liệu | 0,5566 | — | — | — | xong, **âm** |
| **E4** | căn từng thì theo tổn thương của chính nó | **0,7001** [0,599–0,793] | **0,646** | **0,2033** | 0,2458 → 0,1489 | xong, **thắng rõ** |

> **Mọi số trong bảng là val fold 1, 82 bệnh nhân, 1 seed.** Không phải kết quả báo cáo được: chưa có CV 5-fold, và ở n=82 bề rộng CI vào khoảng ±0,10. Chúng dùng để sàng lọc giữa các phương án, không để công bố.

**E1 so với E0, can thiệp duy nhất từng ăn tiền.** Hai run dùng đúng cùng một config (đã diff `config_used.json`: không khác một khoá nào), cùng seed, cùng 82 bệnh nhân val. Khác biệt duy nhất là cache. Bootstrap ghép cặp trên cùng tập bệnh nhân: chênh lệch **+0,1496**, 95% CI **[−0,005; +0,295]**, P(E1 > E0) = 0,973.

Luật quyết định đã chốt trước khi chạy: E0 rơi vào dải 0,35–0,50 nên *protocol giải thích phần lớn khoảng cách, pipeline lành*; E1 − E0 vượt xa ngưỡng +0,05 nên *lesion-tight thành mặc định*. Cả hai phán quyết được đọc theo luật đó, không diễn giải hậu nghiệm.

Đáng chú ý: **giả thuyết cơ chế thì sai dù can thiệp đúng.** Dự đoán trước run là cắt sát sẽ ăn tiền nhờ giảm overfitting, kèm 4 chỉ báo cụ thể. Ba trong bốn chỉ báo trượt: `val_loss` vẫn chạm đáy ở epoch 9 (E0: epoch 10), gap train/val cuối vẫn +2,5 (E0: +2,8). Cơ chế thật là cắt sát làm tín hiệu phân biệt mạnh hơn, chứ không làm model bớt học thuộc. Hai chuyện độc lập.

**E2 bị huỷ vì một biến gây nhiễu đã được cảnh báo trước.** Siamese chạy backbone 8 lượt nên chi phí ~8×; để lọt ngân sách phải hạ mẫu đầu vào, và DenseNet121-3D lại yêu cầu ≥32 voxel ở mọi chiều (nó hạ mẫu 5 lần), nên chỉ hạ được trong mặt phẳng: 96 → 48. Trong khi mọi phương pháp công bố dùng in-plane 112–128, tức E2 chạy ở mức thấp hơn 2,3–2,7 lần. E2 vì thế là *Siamese ở in-plane 48* so với *early-concat ở in-plane đủ*, không phải phép thử kiến trúc sạch. Điều này đã được ghi rõ trước khi chạy, kèm luật: E2 thắng thì kết luận mạnh, E2 thua thì không kết luận được. E2 thua, nên không có kết luận nào về Siamese; hướng này vẫn chưa từng được thử công bằng.

**E3 là một kết quả âm sạch.** Giả thuyết: tỉ lệ trục của ta lệch văn liệu (Z=48 so với 14–16, in-plane 96 so với 112–128) và đó là nút thắt. E3 đổi hình học sang 112×112×32, giữ nguyên mọi thứ khác. Kết quả 0,5566 so với E1 0,5740, chênh **−0,017**, nằm sâu trong nhiễu. **Ba hình học khác nhau đều dừng ở trần ~0,57 với cùng kiểu overfit**, nên giả thuyết tỉ lệ trục bị bác bỏ.

Kết quả âm này nhất quán với, chứ không mâu thuẫn, giả thuyết misalignment: nếu bản thân các thì không khớp nhau thì đổi khung hình không giải quyết gì.

### 3.3. E4: giả thuyết đã được xác nhận

Con số 23,3mm đo ở §2.3 chưa từng được nối với chất lượng model. Nối vào thì nó lớn hơn hình dung:

| Trục | Độ tán tâm tổn thương giữa 8 thì | Cửa sổ cắt E3 | Tỉ lệ |
|---|---|---|---|
| In-plane | 12,4mm | 53,8mm | 23% |
| **Z (đầu-chân)** | **23,3mm** | **43,6mm** | **53%** |

Early concat có một tiền đề ngầm: voxel `(x, y, z)` của kênh `c` là cùng một điểm giải phẫu ở mọi thì. Lệch 53% chiều sâu thì tiền đề đó vỡ, và lớp conv đầu tiên đang trộn mô không liên quan với nhau. Đội hạng 2 của challenge lấy chính việc sửa registration làm đóng góp trọng tâm.

E4 căn từng thì về tâm tổn thương của chính nó, dùng bbox có sẵn trong annotation; chi phí chỉ là một lần build cache, không cần thuật toán registration. Spacing và trường nhìn tính một lần từ thì tham chiếu, chỉ đổi tâm, nên 8 khối giữ cùng kích thước vật lý và khác nhau đúng một phép tịnh tiến.

Gate quan trọng nhất chạy trước khi train: `max_shift_mm` phải khác 0 và trung vị trên 3mm. Nếu phép căn không có hiệu lực thì cache E4 giống hệt E3 và train sẽ ra lại đúng 0,5566 sau 4 giờ mà đường cong không hé lộ gì.

Giới hạn phải ghi vào báo cáo cuối: E4 không phải phép sửa trung tính. Nó chỉ khử tịnh tiến, không khử xoay hay biến dạng; và mô xung quanh sẽ thôi khớp giữa các thì, chỉ tổn thương khớp. Với bài phân loại tổn thương thì đó có thể là điều mong muốn, nhưng nó là một thay đổi ngữ nghĩa dữ liệu.

**Kết quả: 0,7001, mức tăng lớn nhất và là mức tăng duy nhất có ý nghĩa thống kê của cả loạt.**

Gate chạy trước train đã qua: cả 498 ca cắt theo mask, không ca nào phải lùi về tâm tham chiếu, `max_shift_mm` trung vị **19,65mm** (min 2,80 · max 111,0). Phép căn có hiệu lực thật, nên kết quả bên dưới không phải trùng lặp của E3.

| So cặp (bootstrap trên hiệu, phân tầng, 2000 lần) | Δ macro-F1 | 95% CI | P |
|---|---|---|---|
| E4 − E1 | **+0,1261** | **[+0,033; +0,230]** | 0,009 |
| E4 − E0 | +0,2757 | [+0,145; +0,415] | <0,001 |
| E1 − E0 | +0,1496 | [+0,007; +0,289] | 0,040 |

E4 − E1 là lần đầu tiên trong cả loạt có một khoảng tin cậy **nằm hẳn về một phía của 0** với biên rộng rãi. Lưu ý E4 khác E1 ở *hai* khoá (hình học và phép căn), nên phép so một biến sạch là **E4 − E3 = +0,1435**, cùng hình học 112×112×32, chỉ đổi `align_phases`. Vì E3 − E1 = −0,017 (hình học không có tác dụng), toàn bộ mức tăng quy về phép căn.

**Ba chỉ báo cơ chế lần này đều trúng**, khác hẳn E1 (§3.2, nơi can thiệp đúng nhưng cơ chế giải thích sai):

| | E1 | E4 |
|---|---|---|
| `val_loss` chạm đáy ở epoch | 9 | **100** |
| Gap train/val ở epoch cuối | +2,55 | **+1,50** |
| macro-F1 trung bình 50 epoch cuối | 0,512 | **0,607** |
| Số epoch cuối đạt ≥ 0,60 | 0/50 | **29/50** |
| NLL thô so với đoán mò (1,946) | 3,32 (tệ hơn đoán mò) | **1,72 (tốt hơn)** |
| Temperature cross-fit | 5,010 | **2,570** |

Hai dòng cuối quan trọng nhất. Ở E0 và E1, xác suất thô có NLL cao hơn mức đoán mò đều, tức phần "độ tin cậy" của model là nhiễu có hại, phải hạ nhiệt gấp 5 lần mới dùng được. E4 là run đầu tiên mà xác suất thô mang thông tin thật.

Điều này cũng giải thích luôn chứng overfit kinh niên bị ghi nhận suốt E0–E3: `val_loss` chạm đáy ở epoch 9–10 rồi model chỉ còn học thuộc. Nguyên nhân không nằm ở recipe train mà ở đầu vào: khi 8 thì không khớp voxel-với-voxel thì lớp conv đầu tiên không có đặc trưng liên-thì nào để học, nên nó quay sang ghi nhớ. Sửa phép căn đẩy đáy từ epoch 9 sang epoch 100.

F1 tăng ở 5/7 lớp, mạnh nhất ở đúng những lớp trước đây yếu nhất: u máu +0,27, nang +0,26, áp-xe +0,25, di căn +0,16. Hai lớp giảm nhẹ (ICC −0,09 n=10, FNH −0,05 n=8) đều ở cỡ mẫu quá nhỏ để đọc.

**Vẫn phải nói rõ điều này:** 0,7001 đo trên val fold 1 (82 ca), còn 0,709 của `ResNet3D` trong bảng CGHNet đo trên test-104. **Hai tập khác nhau, không được viết là ngang nhau.** Bề rộng CI ở đây là ±0,10, đủ để một chênh lệch hệ thống 0,03–0,05 ẩn trong đó.

### 3.4. Số trustworthiness đầu tiên

Đây là đóng góp headline của dự án, nên phần này quan trọng hơn các con số phân loại ở trên.

**Xác suất thô của model gần như vô dụng.** NLL thô của E1 là 3,3182, tệ hơn đoán mò (ln 7 = 1,9459). Sau temperature scaling mới về 1,5205. Nhiệt độ tìm được `T ≈ 5,0` là mức cực đoan; E0 cũng ở mức 4,15. Nói cách khác, E1 phân loại giỏi hơn E0 nhưng đồng thời tự tin thái quá hơn. Temperature scaling vì thế là bước bắt buộc, không phải tuỳ chọn cuối pipeline.

**Cách fit temperature ảnh hưởng tới con số nhiều hơn dự kiến.** Fit ngay trên tập đánh giá cho ECE 0,1011; cross-fit 5 phần cho **0,1455**. Chênh 44%. Chỉ số cross-fit được dùng; số in-sample không vào báo cáo.

**Một metric đã phải đổi.** Mục tiêu ban đầu là "macro-F1 ≥ 0,90 ở coverage 80%". Ở n=82 nó không tính được có nghĩa: tại coverage 50%, một lớp hiếm chỉ còn 1–2 ca, F1 của lớp đó do một bệnh nhân quyết định rồi chiếm 1/7 trọng số macro. Quan sát thực tế trên E1: macro-F1 nhảy loạn (0,5740 → 0,5559 → 0,5816 → 0,5211) trong khi accuracy tăng đều và đơn điệu (0,6098 → 0,7561). Metric headline của selective prediction vì thế đổi sang risk–coverage / AURC, và phải tính trên tập gộp out-of-fold 394 ca thay vì một fold. Theo AURC thì E1 (0,2753) tốt hơn E0 (0,5395) gần gấp đôi, và E4 (0,2033) tốt hơn E1 thêm một bậc nữa.

## 4. Bài học phương pháp

Mục này ghi lại phần tốn kém nhất của W2. Nó nằm trong báo cáo vì các cơ chế sinh ra từ đây (§4.5) là tài sản thật của dự án.

### 4.1. Ba chẩn đoán sai liên tiếp, ba run GPU

| # | Giả thuyết | Cách bác bỏ | Chi phí |
|---|---|---|---|
| 1 | "BatchNorm với batch 2 làm val loss phân kỳ" | Đổi sang InstanceNorm → macro-F1 đứng yên 0,0668 qua 4 epoch, train loss ≈ ln 7 | 1 run |
| 2 | "InstanceNorm sập vì global average pooling xoá mất tín hiệu" | Phép thử overfit 8 mẫu → InstanceNorm đạt accuracy 1,00, chỉ chậm hơn ~60 lần | 1 run |
| 3 | "Model thiếu bước cập nhật (~20 bước/epoch)" | Gấp 4 lần số bước → 0,2647 so với 0,2725, chênh nằm gọn trong nhiễu | 1 run |

Cả ba đều là suy luận từ đường cong, và cả ba đều tốn một run để bác bỏ. Hai lỗi cụ thể đáng ghi:

- **Bê lập luận từ segmentation sang classification.** InstanceNorm hợp với nnU-Net vì nnU-Net không có global average pooling; DenseNet thì có. Sự khác biệt đó tốn một run.
- **Chẩn đoán từ 4 epoch khi mỗi epoch chỉ có 20 bước cập nhật.** Số bước = mẫu / (batch × accum). Không tính con số đó trước khi diễn giải bất kỳ đường cong nào là gốc của cả ba lần sai.

### 4.2. Nguyên nhân chung: debug mà không biết ngưỡng đạt được

PDF của challenge nằm sẵn trong `docs/` từ đầu tuần và không được tra. Trong đó có leaderboard official:

| | macro-F1 (test-104) | κ |
|---|---|---|
| Đội nhất | 0,8322 | 0,7801 |
| **Baseline chính thức** (UniFormer-S 3D, from scratch) | **0,6083** | 0,5414 |
| Hạng 20–24 | 0,5047 – 0,6076 | |

Metric của họ là `sklearn.f1_score(average='macro')` và `cohen_kappa_score`, khớp `src/eval/metrics.py`, đã thêm test đối chiếu trực tiếp.

Sang W2 muộn hơn, một nguồn còn hữu ích hơn xuất hiện: bảng so sánh cùng protocol của CGHNet (Comput Med Imaging Graph 132, 2026), mọi hàng dùng đúng một cách tiền xử lý và đều báo trên test-104 official:

```
ViT3D 0,645 · ResNet2D 0,684 · ConvNeXt2D 0,696 · ResNet3D 0,709
Swin3D 0,709 · 3D UX-Net 0,709 · Uniformer 0,719 · SDR-Former 0,791
STM-Former 0,793 · RadioFormer 0,806 · CGHNet 0,818
```

Con số đắt nhất trong bảng: **một `ResNet3D` trần đạt 0,709**, vượt baseline chính thức 0,10 điểm, chỉ nhờ hình học đầu vào 16×128×128 → crop 14×112×112. Đây là bằng chứng mạnh nhất cho hướng "dữ liệu quan trọng hơn kiến trúc" mà E0→E1 đã xác nhận bằng thực nghiệm.

Bảng ablation huấn luyện của họ cũng cho ba đòn bẩy cụ thể: Focal Loss 81,8 so với CE 79,9; **bỏ random-crop mất 8,8 điểm** (biến augmentation nặng nhất); lr 1e-4 tốt hơn cả 1e-3 lẫn 1e-5.

Luật đã được ghi vào `AGENTS.md` §5: **ai định debug chất lượng model đều phải đối chiếu bảng này trước.**

Một đính chính trong chính quá trình đọc paper: bản in từ trang web ScienceDirect làm mất các bảng số, dẫn tới việc đọc nhầm một bảng ablation nội bộ (hai nhánh khác kiến trúc) thành phép thử 2D-vs-3D, và kết luận sai rằng nhánh 2.5D nên được nâng lên ứng viên chính. Đọc lại PDF gốc thì phép thử sạch nằm ở bảng khác và cho kết quả ngược: ResNet3D 0,709 thắng ResNet2D 0,684. Đề xuất đã bị rút lại.

### 4.3. Một sai sót so sánh chưa được sửa hết

Suốt E0 → E3, số của dự án là **val fold 1 (82 bệnh nhân)** trong khi số văn liệu là **test-104**. Hai tập khác nhau.

Các so sánh nội bộ (E0 với E1, E1 với E3) vẫn sạch: cùng tập, cùng seed, cùng config. Nhưng mọi câu dạng "E1 còn cách baseline chính thức 0,034" là **không có cơ sở vững**. Con số 0,5740 không được đặt cạnh 0,6083 như thể chúng cùng thang đo. Điều này ảnh hưởng tới cách đọc tiến độ, không tới tính hợp lệ của các quyết định thí nghiệm đã ra.

### 4.4. Thiên lệch chọn epoch

Đường cong macro-F1 val của run baseline dao động không xu hướng qua 26 epoch:

```
0,141 0,163 0,146 0,115 0,159 0,164 0,149 0,159 0,189 0,147 [0,265] 0,216
0,145 0,175 0,234 0,219 0,186 0,208 0,236 0,192 0,191 0,215 0,209 0,193 0,239 0,255
```

Epoch 11 không phải cực trị thật, nó là **lần bốc may nhất trong 26 lần**. Chọn epoch tốt nhất theo macro-F1 trên 82 ca val là chọn nhiễu, cùng bệnh lý với "best-of-many-seeds" mà nguyên tắc dự án cấm, chỉ khác là best-of-many-epochs. Pipeline nay lưu thêm `val_probs_last.npz` mỗi epoch để W3 đo được chính độ lệch này.

### 4.5. Những cơ chế đã dựng để không tái diễn

| Cơ chế | Bắt được gì |
|---|---|
| Phép thử overfit 8 mẫu (`src/train/sanity.py`) | Phân biệt "bài toán khó" với "pipeline hỏng" trong 30 giây |
| Gate đo thời gian trước khi train | Chặn một run 23,5 giờ trước khi tốn quota |
| `run_dir` băm theo khối `model:` | Hai kiến trúc không bao giờ dùng chung thư mục, không resume đè nhau |
| Gate đối chiếu nhãn cache ↔ `splits/` | Rủi ro nặng nhất còn sót: nhãn lệch thì train vẫn trơn, metric vẫn ra số, kết quả vô nghĩa |
| Gate dừng khi quét ra 0 mask | Bắt được lỗi khiến 20/20 ca lặng lẽ rơi về bbox mà build vẫn báo "hoàn tất" |
| `tests/test_protocol_conformance.py` | Khoá config theo recipe official, fail nếu trôi |
| **Luật quyết định chốt trước khi chạy** | Chống hợp lý hoá hậu nghiệm — đã dùng để đọc E0/E1 và E3 |
| 245 test / 17 skip | Trong đó test chống leakage cố ý không phụ thuộc torch, luôn chạy được |

Một quy trình cũng được thiết lập: **trước khi bàn giao thứ gì tốn GPU, rà hết đường chạy; thứ nào không kiểm được ở local thì tải source thư viện về đọc, hoặc biến thành assert rẻ tiền chạy trước phần tốn kém.** Lần áp dụng đầu tiên bắt được 5 lỗi mà không tốn một phút GPU nào, trong đó có một lỗi im lặng: `InstanceNorm3d` của PyTorch mặc định `affine=False`, tức bản sửa trước đó đã bỏ mất scale/shift học được ở mọi lớp norm.

## 5. Trạng thái và giới hạn

| Hạng mục | Trạng thái | Bằng chứng | Nhận xét |
|---|---|---|---|
| Split official + khoá + leakage test | Hoàn thành | 12 file `splits/`, 245 test xanh | Khôi phục khả năng so benchmark trực tiếp. |
| Gate hình học trên dữ liệu thật | Hoàn thành | PASS 3.984/3.984 | Điều kiện tiên quyết cho crop theo bbox. |
| Cache v0 `fixed_mm` | Hoàn thành | 498 `.npz`, Kaggle Dataset v1 | Đã bị E1 thay thế làm mặc định. |
| Cache `lesion_tight` | Hoàn thành | E1 chạy trên nó | Đã bị cache E4 thay thế làm mặc định. |
| Baseline 3D-patch, 1 fold | Hoàn thành | **0,7001** val fold 1 (E4) | Chưa có CV, chưa phải số báo cáo. |
| Baseline 2.5D | **Bị cắt** | — | Đúng thứ tự cắt đã định; bằng chứng ngoài ủng hộ. |
| Fusion Siamese (E2) | **Chưa kết luận** | run bị huỷ vì biến gây nhiễu | Phải chạy lại ở hình học đúng mới đánh giá được. |
| Ablation hình học (E3) | Hoàn thành, kết quả âm | 0,5566 so với 0,5740 | Bác bỏ giả thuyết tỉ lệ trục. |
| Căn từng thì (E4) | **Hoàn thành, thắng rõ** | 0,7001; Δ so E1 +0,126 CI [+0,033; +0,230] | **Cấu hình chốt.** Gate `max_shift_mm` đã qua (trung vị 19,65mm, 0 ca fallback). |
| Calibration + selective | Code xong, số mới 1 fold | ECE/AURC/T của E0, E1, E4 | Cần gộp out-of-fold 394 ca. |
| CV 5-fold + CI bootstrap | Đã dựng notebook, chưa chạy | `notebooks/07_e4_cv_folds.ipynb` | Việc đầu tiên của W3; ~3,9h/fold, 2 fold mỗi session. |
| Registration thật (rigid) | Chưa bắt đầu | — | E4 cho thấy hướng này đáng đầu tư, nhưng xếp sau CV. |
| External / OOD | Chưa bắt đầu | — | Theo kế hoạch W3. |
| **test-104** | **Chưa chạm** | không có đường code nào tới nó | Đúng quy trình; chỉ chạm một lần ở W5. |

**Giới hạn phải nói rõ với người đọc:**

1. **Mọi con số của dự án là 1 fold, 82 bệnh nhân val, 1 seed.** Không có CI cho phần lớn chúng, và ở n=82 bề rộng CI khoảng ±0,10, đủ để nuốt trọn chênh lệch giữa E1 và E3.
2. **Không so trực tiếp được với văn liệu** (§4.3). Số văn liệu là test-104.
3. **Ngay cả khi có kết quả tốt, việc chứng minh vượt SOTA là bất khả thi ở cỡ mẫu này.** Bootstrap ở n=104 cho bề rộng CI ±0,077 tại mức 0,8322 và ±0,061 tại 0,90; hai CI chồng nhau. (So hai CI biên là phép bảo thủ; kiểm định ghép cặp mạnh hơn. Nhưng thông điệp không đổi: định vị của dự án phải là trustworthiness, không phải leaderboard.)
4. **Overfitting đã nhẹ đi nhiều nhưng chưa hết.** `val_loss` chạm đáy ở epoch 9–10 ở E0/E1/E3; ở E4 là epoch 100 và gap cuối giảm từ +2,55 xuống +1,50. Nguyên nhân gốc hoá ra là lệch pha ở đầu vào chứ không phải recipe train, nên các hướng chỉnh dropout/weight-decay trước đây đều là nhắm sai chỗ.
5. **`deterministic: true` không cho tái lập bit-exact**. DenseNet `spatial_dims=3` là non-deterministic trên CUDA. Seed cố định cho phép lặp lại *thí nghiệm*, không phải lặp lại từng chữ số. Đây là một lý do nữa để mọi số đều kèm CI.

## 6. Công việc tiếp theo theo thứ tự ưu tiên

Thứ tự này đổi so với luật chốt trước ở §3.3, vốn nói E4 đạt ≥0,62 thì đi tiếp sang rigid registration rồi Siamese. Lý do: nút thắt bây giờ không còn là tìm cấu hình tốt hơn mà là chưa có con số nào báo cáo được, và bất định epistemic cần đủ 5 model của 5 fold mới đo được.

1. Chạy đủ 5-fold cho cấu hình E4, dựng bảng CV macro-F1/κ kèm CI bootstrap mức bệnh nhân; notebook đã sẵn ở `notebooks/07_e4_cv_folds.ipynb`.
2. Gộp out-of-fold 394 ca, tính lại calibration và risk–coverage trên cỡ mẫu đó.
3. Dựng deep ensemble từ 5 checkpoint để đo bất định epistemic; đây là điều kiện của đóng góp headline.
4. Chạy registration rigid thật; E4 mới chỉ khử tịnh tiến, chưa khử xoay và biến dạng.
5. Đổi backbone sang 3D ResNet ở đúng 14×112×112; DenseNet121-3D không chịu được Z=14.
6. Thử Focal Loss và ablation augmentation theo bảng ablation CGHNet.
7. Đánh giá lại fusion Siamese ở hình học đúng; E2 chưa từng được thử công bằng.
8. Audit và tải external + Duke OOD; việc chạy trên CPU nên song song được với mục 1.
9. Khoá protocol, threshold và temperature trên validation trước khi chạm test-104 đúng một lần.

## 7. Timeline

| Thời điểm | Mốc |
|---|---|
| 24/07/2026 | Lập plan W2 chi tiết; review dataset LLD-MMRI trên Kaggle; **tái lập + verify split chính thức 316/78/104**; scaffold `src/utils`, `src/data`; test chống leakage đầu tiên. |
| 24/07/2026 (tối) | Dựng pipeline chạy trên Kaggle; **gate hình học PASS trên dữ liệu thật**. |
| 27/07/2026 | Pipeline tiền xử lý trong không gian mm; phán quyết `axis_order = xy`; build cache 498 ca; baseline ra **số mốc đầu tiên 0,2725**; ba chẩn đoán sai; tra leaderboard và **áp nguyên khối recipe official**; hạ tầng bootstrap CI. |
| 28/07/2026 | Cache `lesion_tight`; `calibration.py` + `selective.py`; tính bề rộng CI ở n=104. |
| 29/07/2026 | **E0 = 0,4244 · E1 = 0,5740**; phân tích calibration và selective; dựng E2 Siamese. |
| 30/07/2026 | Đọc CGHNet (bảng so sánh cùng protocol); huỷ E2; **E3 = 0,5566, kết quả âm**; dựng E4 và notebook. |
| 31/07/2026 | Tổng hợp báo cáo W2; **E4 = 0,7001, mức tăng duy nhất có ý nghĩa thống kê** (Δ so E1 +0,126, CI [+0,033; +0,230]); chốt cấu hình E4; dựng notebook CV 5-fold. |

## Kết luận cho mentor

Về hạ tầng, pipeline từ MRI thô đến bảng metric đã chạy được và tái lập được, với mọi gate an toàn khoa học đứng vững: split khoá ở mức bệnh nhân và đã commit, test chống leakage pass, thống kê chuẩn hoá không xuyên bệnh nhân, và test-104 chưa bị chạm một lần nào. Về kết quả, con số tốt nhất hiện tại là macro-F1 **0,7001** trên val fold 1; nó chưa so trực tiếp được với văn liệu vì khác tập đánh giá, chưa có CV, và chưa nên coi là kết quả cuối. Điều đáng nói không phải bản thân con số mà là cách nó tăng: toàn bộ mức tăng từ 0,26 lên 0,70 đến từ tái lập recipe và hai thay đổi về cách chuẩn bị dữ liệu, không một dòng nào của kiến trúc model bị đụng tới. Ba hướng đi theo kiến trúc hoặc hình học đều không cho gì.

Về trustworthiness, đóng góp headline của dự án đã có số thật và chúng cho thấy vấn đề vừa có thật vừa cải thiện được: NLL thô đi từ chỗ tệ hơn đoán mò (3,32 so với 1,95) xuống 1,72, nhiệt độ cần thiết giảm từ 5,0 còn 2,57, AURC từ 0,540 xuống 0,203. Nhưng đóng góp này vẫn chưa đo được đầy đủ, vì bất định epistemic cần 5 model của 5 fold mà hiện mới có một; đó là lý do việc đầu tiên của W3 là chạy nốt CV chứ không phải thử thêm ý tưởng. Bài học lớn nhất của W2 lại là về phương pháp chứ không về mô hình: bốn chẩn đoán sai đều sinh ra từ việc debug mà không biết ngưỡng đạt được là bao nhiêu, và luật "đối chiếu mốc ngoài trước khi debug chất lượng model" nay đã được ghi vào tài liệu ngữ cảnh của dự án cùng một bộ gate tự động.

---

*Research Use Only. Mọi số trong báo cáo này là kết quả sàng lọc trên tập validation, chưa qua cross-validation và chưa có khoảng tin cậy đầy đủ; chúng không phải kết quả nghiên cứu được công bố và không được dùng để suy diễn về hiệu năng lâm sàng.*
