# Kho lưu kết quả thí nghiệm

> **Đây là HỒ SƠ, không phải căn cứ.** Mọi mục dưới đây đã bị một phép đo trên cỡ mẫu lớn
> hơn thay thế, hoặc thuộc một nhánh đã dừng, hoặc mô tả code đã gỡ khỏi cây làm việc.
> Kết quả đang hiệu lực nằm ở [`AGENTS.md`](../AGENTS.md) §5.
>
> Tách ra ở WORKLOG S-197 để `AGENTS.md` đọc được trong một lượt. **Nội dung giữ nguyên
> văn**, kể cả các cảnh báo "đã bị bác bỏ" viết sẵn trong từng mục — chúng là phần đáng giá
> nhất của hồ sơ này.
>
> Vì sao không xoá hẳn: bốn lần dự án bị một phép sàng cỡ nhỏ đánh lừa đều được ghi ở đây,
> và đó là bằng chứng cho luật "một phép sàng nhỏ chỉ đủ để LOẠI, không đủ để CHỌN".

---

#### ⭐ Bảng thứ ba, và là bảng DUY NHẤT đo một biến về FUSION (SDR-Former, đọc bài 2026-08-17)

Nguồn: Lou và cs., arXiv:2402.17246, Bảng 1 phần "MR (8-phase)". **Nhóm này chính là nhóm phát hành LLD-MMRI.** Họ bọc **cùng một backbone** vào khung Siamese của SDR-Former và đo lại — §5.1 nói thẳng các hàng `SNN-*` là những backbone đó *"integrated into the SDR-Former's weight-sharing network framework"*, nên đây **là** phép so một biến:

| backbone | image-level (8 pha = 8 kênh) | Siamese (encoder dùng chung) | hiệu |
|---|---|---|---|
| ResNet-50 | 0.6898 | 0.7168 | +0.027 |
| DenseNet-121 | 0.7171 | 0.7394 | +0.022 |
| MCSCNN | 0.7089 | 0.7409 | +0.032 |
| BoTNet-50 | 0.7139 | 0.7572 | +0.043 |
| **UniFormer-S** | 0.7123 | **0.7639** | **+0.052** |
| H2Former | 0.7342 | 0.7745 | +0.040 |
| **SDR-Former** (đủ bộ: DR-Former + BCIM + APSM) | — | **0.7910** | +0.027 nữa |

**6/6 đều dương**, trung bình **+0.036**, và transformer hưởng lợi hơn CNN (+0.045 so +0.027).

Vì sao bảng này đáng giá **ngay bây giờ**: hai trục đã cạn về mặt thực nghiệm — UniFormer-**Base** (dung lượng lớn hơn) và UniFormerV2-B/16 (nguồn pretrain khác) đều **không** vượt `uniformer_s`. Trục "8 pha được **kết hợp** thế nào" là trục thứ ba, và dự án **chưa từng thử** (mọi thí nghiệm từ E0 tới nay đều đưa 8 pha vào làm 8 kênh). `configs/sdrformer.yaml` + `notebooks/25_sdrformer.ipynb` là bản tái lập.

⚠️⚠️ **Nhưng SDR-Former train FROM SCRATCH.** Ta đang cân nhắc bỏ pretrained — can thiệp *duy nhất* từng thắng có ý nghĩa thống kê (+0.130, P<0.001). Đặt kỳ vọng cho đúng: 0.7910 của họ chỉ hơn **0.7682** của ta trên test-104 đúng **+0.023**, nằm gọn trong CI ±0.09. **Không phải một cấu hình chắc chắn tốt hơn.** Và nếu nó thua thì **không kết luận được** "Siamese fusion vô ích" — phép so gộp hai biến (fusion *và* pretrained).

⚠️ **ĐÍNH CHÍNH hai câu sai trong `src/models/siamese_fusion.py`** (đã sửa tại chỗ 2026-08-17):
1. Docstring cũ viết *"+0.074 chỉ do đổi sang SNN"*, lấy hiệu giữa `ResNet-50` (0.6898) và `SNN-UniFormer-S` (0.7639) — hai hàng khác nhau **cả backbone lẫn fusion**. Hiệu một biến thật là **+0.022…+0.052**. Đừng trích con số cũ.
2. Docstring cũ viết *"hạng 2 của challenge dùng ResNet18"* — sai, hạng 2 (`NPUBXY`) dùng UniFormer-S + Kinetics.

---

---

### 🔒 TEST-104 OFFICIAL — lần chạm 1 (2026-08-07, WORKLOG S-110)

> **Test-104 ĐÃ BỊ CHẠM MỘT LẦN.** Mục này là kết quả của lần đó, cấu hình E4.
>
> ✅ **Lần chạm 2 ĐÃ CHẠY** (2026-08-14, WORKLOG S-173) — UniFormer ensemble 5 fold, **0.7682**. Xem mục ngay trên. Mục này giữ nguyên làm hồ sơ lần 1.
>
> Lần chạm **thứ ba** lại cần xin phép và một pre-registration §C mới (AGENTS.md §3.4, §10). Protocol lần 1 khoá ở cùng file, mục §A, commit `56baa41`.

Cấu hình: E4 (`baseline_3dpatch.yaml` + cache lesion-tight · 112×112×32 · per-phase) · **ensemble 5 fold**, trung bình softmax · không TTA · không EMA/pretrained.

| | macro-F1 | κ | accuracy |
|---|---|---|---|
| **ensemble 5 fold (số chính)** | **0.6162 [0.5246, 0.7032]** | 0.5647 | 0.6346 |
| trung bình 5 model đơn | 0.6001 ± 0.0204 | — | — |

⚠️ **Cao hơn baseline official (0.6083) đúng 0.0038, trong khi CI rộng ±0.09.** CI chứa 0.6083 rất thoải mái, nên **KHÔNG được viết "ta vượt baseline official"**. Câu đúng: *ngang baseline official, không phân biệt được về thống kê*. Định vị: trên phần lớn nhóm hạng 20–24, còn cách rõ ràng so với SOTA công bố (ResNet3D 0.709 · CGHNet 0.818).

⚠️ **Model đơn tốt nhất (fold 2, 0.6308) CAO HƠN ensemble.** Không được báo nó — chọn nó sau khi nhìn test là chọn trên test. Ensemble đã chốt trước là số chính. Ensemble − trung bình thành viên = +0.0162 [−0.0232, +0.0560] **P=0.43**, tức gộp 5 model gần như không giúp.

#### Thiên lệch chọn epoch đã được xác nhận về mặt định lượng

| | macro-F1 |
|---|---|
| out-of-fold (394 ca) | 0.6851 |
| **test-104 (104 ca)** | **0.6162** |
| hụt | **−0.069** |

Thiên lệch chọn epoch đo trước trên out-of-fold là **+0.079** (`best` 0.6824 so với `last` 0.6038, cùng 312 ca). Mức hụt thực tế 0.069 **gần trùng khít**. Nghĩa là 0.6851 lạc quan đúng bằng phần dự án đã tự chỉ ra và cảnh báo, không có nguồn thổi phồng nào khác lộ ra. Đây là điểm mạnh của phần phương pháp luận, nên đưa vào báo cáo.

#### Calibration: ensemble tự nó hiệu chỉnh tốt hơn temperature scaling

| | ECE | MCE | NLL | tự tin (lệch so acc) |
|---|---|---|---|---|
| ensemble, **chưa** hiệu chỉnh | **0.1303** | 0.4459 | 1.2050 | 0.750 (+0.115) |
| ensemble, T=2.10 fit từ OOF | 0.1902 | 0.3674 | 1.0441 | 0.581 (−0.054) |

**Pre-registration §3 dự đoán trước điều này và nó đã xảy ra:** `T` học từ phân bố *model đơn* mà áp lên *ensemble* vốn đã bớt tự tin, nên hiệu chỉnh quá tay — ECE xấu đi và bắn sang thiếu tự tin. Không được fit lại `T` trên test.

**Phát hiện đi kèm:** ensemble **chưa hiệu chỉnh** cho ECE 0.1303, tốt hơn cả model đơn *đã* temperature-scaling tốt nhất trên out-of-fold (0.1534). **Gộp 5 model là bộ hiệu chỉnh tốt hơn temperature scaling** ở bài toán này. Tự tin thái quá giảm từ +0.186 (OOF) xuống +0.115.

#### ⚠️ Selective: có tác dụng, nhưng luận điểm cũ của S-087 KHÔNG lặp lại

| xếp hạng | AURC | F1@100% | F1@90% | F1@80% | F1@70% |
|---|---|---|---|---|---|
| max-prob (đối chứng) | 0.1298 | 0.6162 | 0.6468 | 0.6844 | 0.7527 |
| −epistemic (bất đồng 5 model) | 0.1305 | 0.6162 | 0.6530 | 0.7239 | 0.7526 |

Hiệu giữa hai cách xếp hạng: AURC **+0.0009 P=0.90** · F1@80% +0.0286 **P=0.26**. **Không khác gì nhau.**

Nhưng cả hai đều có tác dụng thật so với không từ chối ca nào (bootstrap ghép cặp, 2000 lần):

| | hiệu so với F1@100% | CI95 | P |
|---|---|---|---|
| max-prob @80% | **+0.0696** | [+0.0154, +0.1245] | **0.016** |
| −epistemic @80% | **+0.0970** | [+0.0466, +0.1451] | **<0.001** |
| max-prob @70% | +0.1267 | [+0.0568, +0.1859] | 0.002 |

**ĐÍNH CHÍNH kết luận của S-087.** Trên out-of-fold, dòng đối chứng max-prob cho +0.000 (P=0.88), và dự án đã kết luận *"selective chỉ chạy được khi tín hiệu đến từ bất đồng, không phải từ softmax"*. **Trên test-104 điều đó sai:** max-prob cho +0.070 có ý nghĩa thống kê. Giải thích nhất quán: trên OOF "ensemble" chỉ là MC-dropout trên **một** model tự tin thái quá nên softmax của nó vô dụng; với **5 model độc lập thật**, softmax của trung bình đã là tín hiệu bất định tốt.

Phát biểu đúng để dùng trong báo cáo: **từ chối 20% ca khó nâng macro-F1 từ 0.616 lên 0.68–0.72, và không cần MC-dropout để làm việc đó.**

#### Từng lớp — hai lớp yếu tụt sâu hơn

| lớp | n | out-of-fold | test-104 | hiệu |
|---|---|---|---|---|
| u máu | 16 | 0.831 | **0.903** | +0.072 |
| nang | 11 | 0.762 | 0.762 | 0.000 |
| ICC | 12 | 0.519 | 0.519 | 0.000 |
| HCC | 32 | 0.776 | 0.679 | −0.097 |
| FNH | 10 | 0.761 | 0.640 | −0.121 |
| áp-xe | 12 | 0.660 | 0.538 | −0.122 |
| **di căn** | 11 | 0.488 | **0.273** | **−0.215** |

Hướng nhầm chính y hệt out-of-fold: **HCC → di căn 6/32 ca**, HCC → FNH 5/32, di căn → ICC 4/11.

Phép tính trần, **dùng đúng số của test-104** (di căn 0.273, ICC 0.519): kể cả 5 lớp còn lại đều đạt 0.90 thì macro-F1 cũng chỉ tới **0.756**. ⚠️ Đừng lẫn với con số **0.771** ở mục E6b bên dưới — cái đó tính từ F1 *out-of-fold* của E6b (0.455 và 0.444). Hai phép tính dùng hai tập khác nhau nên không thay thế nhau được.

⚠️ n mỗi lớp chỉ 10–16 ca, đừng diễn giải sâu từng con số.

---

### ⚠️ ENSEMBLE E4 ⊕ CGHNet — KẾT LUẬN ĐÃ BỊ BÁC BỞI 5 FOLD (2026-08-11, WORKLOG S-127)

> **Giữ lại làm hồ sơ, KHÔNG dùng làm căn cứ.** Mục này từng kết luận ensemble E4 ⊕ CGHNet là
> "hướng có kỳ vọng cao nhất hiện tại" dựa trên **1 fold**. Đủ 5 fold (394 ca) thì:
>
> | | hiệu | CI95 | P |
> |---|---|---|---|
> | **gộp 50/50 − E4** | **−0.0102** | [−0.0388, +0.0181] | **0.47** |
> | CGHNet − E4 | −0.0185 | [−0.0683, +0.0314] | 0.46 |
>
> Gộp out-of-fold: E4 **0.6851** · CGHNet **0.6673** · gộp 50/50 **0.6748**.
> **Fold 1 là fold duy nhất ensemble có tác dụng** (+0.065); bốn fold kia −0.054, −0.020,
> −0.018, −0.034. Quét trọng số cho cực đại ở w(E4)=0.9 → 0.6867, tức **gần đúng bằng E4 một
> mình**. **E4 vẫn là cấu hình gốc.**
>
> 🐛 Và mọi con số CGHNet ở đây là của **bản CÓ LỖI** (`pos_embed` không bao giờ được học,
> S-126). Đã sửa; muốn có mốc CGHNet đúng thì phải train lại 5 fold.
>
> **Đây là lần thứ BA dự án bị một phép sàng cỡ nhỏ lừa:** E6b +0.038 ở 2 fold → −0.002 ở 5
> fold (S-107); ensemble này +0.065 ở 1 fold → −0.010 ở 5 fold. Quy tắc rút ra không đổi:
> **một phép sàng nhỏ chỉ đủ để LOẠI, không đủ để CHỌN.**

#### Phần vẫn đúng và vẫn đáng giá: hai kiến trúc hỏng theo HAI CHIỀU NGƯỢC NHAU

Trên đủ 394 ca, `weak_classes` §1 cho hai bức tranh đối xứng:

| lớp | E4 đoán/thật | CGHNet đoán/thật |
|---|---|---|
| ICC | **1.26** (thừa) | **0.89** (thiếu) |
| áp-xe | **1.31** (thừa) | **0.76** (thiếu) |
| di căn | 1.05 | **0.80** (thiếu) |
| HCC | **0.86** (thiếu) | **1.13** (thừa) |

Ba hướng nhầm lớn nhất cũng đảo chiều: E4 là **HCC → di căn 15 · ICC → áp-xe 10 · HCC → ICC 9**
(lớp đa số rò VÀO lớp yếu); CGHNet là **ICC → HCC 14 · di căn → HCC 13 · áp-xe → HCC 11**
(lớp yếu sập VÀO lớp đa số).

Hệ quả đo được:

| | trùng lặp lỗi | oracle |
|---|---|---|
| E4 so E6b (chỉ khác augmentation) | 74% | 0.782 |
| **E4 so CGHNet** (khác kiến trúc *và* hình học) | **58%** (kỳ vọng 36 nếu độc lập) | **0.8123** |

**Có 12.7 điểm dư địa (0.812 so với 0.685 đạt được), và trung bình xác suất đơn thuần không
lấy được một điểm nào.** Giải thích nhất quán với bảng trên: E4 nói "di căn" đầy tự tin,
CGHNet nói "HCC" đầy tự tin; trung bình hai thiên lệch ngược chiều chỉ chọn bên nào tự tin
hơn, không sửa được bên nào. Muốn khai thác 12.7 điểm đó thì cần một bộ phối hợp **học được**
(stacking trên out-of-fold), không phải phép trung bình cố định.

⚠️ Thiên lệch chọn epoch của CGHNet là **+0.104** trung bình (0.6673 so 0.5692), lớn hơn hẳn
+0.079 của E4. Cả 5 fold đều chạm đáy `val_loss` ở epoch **15–40**, và `train_loss` về
**0.0000** từ khoảng epoch 180 — model thuộc lòng 312 ca train.

#### Hồ sơ: con số fold 1 từng làm cơ sở cho kết luận đã bị bác

⛔ **Mọi con số trong tiểu mục này đã bị 5 fold bác bỏ — xem bảng ở đầu mục. Đừng trích dẫn
nó như kết quả.** Giữ lại đúng một lý do: để thấy một phép sàng 1 fold trông thuyết phục đến
mức nào, kể cả khi kèm sẵn cảnh báo về cỡ mẫu.

*(Nguyên văn kết luận cũ, nay đã sai: "hướng có kỳ vọng cao nhất hiện tại, và nó gần như
miễn phí".)*

CGHNet fold 1: macro-F1 **0.6935** (epoch 112), so với E4 fold 1 0.7001. Ngang nhau
(−0.0066, CI95 [−0.119, +0.107], P=0.94). Nhưng **hai model sai ở những ca KHÁC nhau**:

| | trùng lặp lỗi | oracle |
|---|---|---|
| E4 so **E6b** (chỉ khác augmentation) | **74%** | 0.782 |
| E4 so **CGHNet** (khác kiến trúc *và* hình học) | **50%** | 0.854 |

Và gộp xác suất 50/50 trên 82 ca của fold 1:

| | macro-F1 | ICC | áp-xe | di căn |
|---|---|---|---|---|
| E4 | 0.7001 | 0.500 | 0.941 | 0.526 |
| CGHNet | 0.6935 | 0.588 | 0.588 | 0.444 |
| **gộp 50/50** | **0.7651** | **0.632** | 0.941 | **0.588** |

**+0.065 so với E4, và nó nâng đúng hai lớp yếu.** Quét trọng số cho w(E4)=0.50 là tối ưu,
tức 50/50 **không phải giá trị được chọn trên tập đánh giá** — nó là mặc định không thiên vị.

⚠️ **Phép gộp này HỢP LỆ**, khác hẳn cái bị cấm ở §3: cả hai model train trên **đúng 312 ca**
của fold 1 và đánh giá trên **đúng 82 ca val** mà không model nào thấy. Cái bị cấm là gộp 5
checkpoint của 5 fold rồi báo số out-of-fold.

⚠️ **1 fold, n=82, CI mỗi fold ~±0.19.** E6b sàng 2 fold cho +0.038 rồi 5 fold cho −0.002.
Cần CGHNet đủ 5 fold (1,6 h/fold ⇒ 8h) mới kết luận được. Nhưng khác E6b ở một điểm quan
trọng: đây **không phải cấu hình train mới**, và cơ chế (50% so với 74% trùng lặp) đo được
trực tiếp, không suy từ điểm số.

⚠️ CGHNet `val_loss` chạm đáy ở **epoch 16** (E4 fold 1: epoch 100). Theo ρ=0.770 của S-107
thì đó là dấu hiệu overfit rất sớm, vậy mà nó vẫn đạt 0.6935 — một ngoại lệ đáng ghi.

---

---

### 📁 HỒ SƠ · UniFormer fold 1 = 0.8111 (2026-08-12, WORKLOG S-129) — ĐÃ BỊ BẢN 5 FOLD THAY

> **Giữ làm hồ sơ, KHÔNG trích làm kết quả.** Mục 5 fold ở trên là bản chính thức. Ba con
> số phụ trợ ở đây (thiên lệch +0.042 · di căn top-2 = 1.000 · động học từ `val_loss` đáy)
> **không sống sót** qua 394 ca — xem bảng đính chính ở mục trên.

**Con số cao nhất dự án từng có, và lần đầu một can thiệp vượt E4 có ý nghĩa thống kê.**
Cấu hình đúng `configs/uniformer_s.yaml` không sửa gì (`patch_embed1_stride [1,2,2]` trung
thực, `require_pretrained: true`).

| cùng 82 ca fold 1 | macro-F1 | accuracy |
|---|---|---|
| E4 (DenseNet) | 0.7001 | 0.7073 |
| CGHNet | 0.6935 | 0.7073 |
| **UniFormer + Kinetics** | **0.8111** | **0.8049** |

Bootstrap **ghép cặp** trên hiệu (phân tầng theo lớp, 2000 lượt):

| | hiệu | CI95 | P |
|---|---|---|---|
| UniFormer − E4 | **+0.1133** | [+0.0053, +0.2221] | **0.036** |
| UniFormer − CGHNet | **+0.1205** | [+0.0013, +0.2365] | **0.048** |

#### ⭐ Vì sao đây KHÁC ba lần bị fold 1 lừa trước đó

E6b (+0.066 ở fold 1) và ensemble E4⊕CGHNet (+0.065 ở fold 1) đều chỉ có **điểm số**. Lần này
**hai dấu hiệu cơ chế chốt trước ở plan S-125 đã được kiểm, và một cái bắn rất mạnh:**

| di căn (n=8, fold 1) | top-1 | top-2 |
|---|---|---|
| E4 | 0.625 | 0.625 ← **bằng nhau** |
| CGHNet | 0.500 | 0.625 |
| **UniFormer** | **0.875** | **1.000** |

§4 của chẩn đoán nói: *"trong 20 ca sai không một ca nào có di căn ở hạng hai — biểu diễn
không mã hoá được lớp này"*, và kết luận ràng buộc **là biểu diễn**. Pretrained là can thiệp
duy nhất đổi được biểu diễn, và **giờ mọi ca di căn đều nằm trong top-2**. Đây là dự đoán ra
trước, không phải giải thích sau.

⚠️ Dấu hiệu thứ hai **KHÔNG** đổi: vẫn **0/16 lỗi có biên < 0.10**. Tầng quyết định vẫn không
cứu được gì — §3 giữ nguyên. Số lỗi giảm 24 → 16, nhưng lỗi còn lại vẫn tự tin sai.

#### Từng lớp — lớp yếu tăng nhiều nhất

| lớp | n | E4 | UniFormer | hiệu |
|---|---|---|---|---|
| nang | 9 | 0.625 | 0.889 | **+0.264** |
| **di căn** | 8 | 0.526 | **0.737** | **+0.211** |
| FNH | 8 | 0.750 | 0.941 | +0.191 |
| **ICC** | 10 | 0.500 | **0.667** | **+0.167** |
| HCC | 25 | 0.776 | 0.826 | +0.051 |
| u máu | 13 | 0.783 | 0.818 | +0.036 |
| áp-xe | 9 | 0.941 | 0.800 | −0.141 |

áp-xe là lớp duy nhất giảm, và 0.941 của E4 ở fold 1 là ngoại lệ (E4 gộp 394 ca chỉ 0.660).

#### Động học lành mạnh hơn hẳn — bằng chứng chống "epoch may"

| | `val_loss` đáy | best @epoch | thiên lệch best−last | TB 50 epoch cuối |
|---|---|---|---|---|
| E4 | 100 | 231 | +0.071 | 0.607 |
| CGHNet | 16 | 112 | +0.069 | 0.627 |
| **UniFormer** | **48** | **259** | **+0.042** | **0.777** |

**Trung bình 50 epoch cuối của UniFormer (0.777) cao hơn epoch tốt nhất của E4 (0.700).**
Thiên lệch chọn epoch cũng nhỏ nhất trong ba. Không phải một đỉnh may mắn.

#### ⚠️ Gộp với E4/CGHNet làm TỆ ĐI — đừng ensemble

| | macro-F1 |
|---|---|
| UniFormer một mình | **0.8111** |
| gộp 50/50 với E4 | 0.7563 |
| gộp cả ba | 0.7820 |

Trùng lặp lỗi UniFormer so E4 chỉ **50%** và oracle 0.895, nhưng trung bình xác suất vẫn kéo
xuống — vì gộp một model mạnh với hai model yếu hơn 0.11 điểm thì phần yếu thắng. Cùng bài
học S-127: **trùng lặp lỗi thấp không bảo đảm ensemble ăn.**

#### ✅ ĐỦ 5 FOLD — bar đã vượt, xem mục ngay dưới

Bar chốt trước là **gộp 2 fold ≥ 0.78** ⇒ chạy đủ 5 fold và thành cấu hình chính. Đã đủ 5 fold
(S-169): gộp out-of-fold **0.8147**. Bar đã vượt.

⚠️ **Ba con số ở mục fold-1 phía trên KHÔNG sống sót qua 5 fold** — chúng là hiện vật cỡ mẫu
nhỏ, và mục dưới đây đính chính từng cái. Đừng trích mục fold-1 làm kết quả.

---

---

### ⭐ UNIFORMER + KINETICS — thiết kế và các chỗ lệch (2026-08-11, WORKLOG S-125)

Tái lập recipe của **đội hạng 2** LLD-MMRI 2023: [`ZHEGG/miccai2023`](https://github.com/ZHEGG/miccai2023).
Code: `src/models/uniformer3d.py` · `configs/uniformer_s.yaml` · `notebooks/20_uniformer.ipynb`.
**Chưa chạy fold nào.**

⚠️ **Là hạng 2 (`NPUBXY`, 0.8078), KHÔNG phải hạng 1** (`WorkingisAllyouneed`, 0.8322).
README của repo tự ghi *"second-place solution"*. Đừng viết nhầm trong báo cáo.

#### Vì sao hướng này khác bảy hướng đã bị loại

**Baseline official của challenge CHÍNH LÀ UniFormer-S 3D, from scratch → 0.6083.** Repo này
dùng **đúng kiến trúc đó** và `train.sh` của họ bật `--pretrained`, nạp
`uniformer_small_k400_16x8.pth` — trọng số học trên **video Kinetics-400**.

| | macro-F1 test-104 |
|---|---|
| UniFormer-S, **from scratch** (baseline official) | 0.6083 |
| UniFormer + **Kinetics** + cb_loss + sqrt sampling + smoothing 0.1 + drop-path 0.1 + 3 aug lọc | **0.8078** |

Cùng kiến trúc, chênh **~0.20**. Không mốc đối chiếu nào khác trong văn liệu của dataset này
tách được một cụm biến với biên độ như vậy.

**Chẩn đoán §5 không loại được nó.** Bảy hướng bị loại đều là chỉnh loss/ngưỡng/augment **trên
cùng một biểu diễn**; §4 nói thẳng ràng buộc *là* biểu diễn (di căn không vào nổi top-2).
Pretrained là can thiệp duy nhất đổi được biểu diễn. Dự án chưa từng thử đúng cách: E8 dùng
MedicalNet (pretrain segmentation, yếu hơn nhiều) và vướng lỗi `shortcut_type`; bản tái lập
CGHNet train ViT from scratch — đúng theo bài CGHNet, nhưng nghĩa là chưa có backbone pretrained mạnh.

⚠️ Chênh 0.20 **không phải phép thử một biến sạch** — nó gộp 6 thứ. Tái lập cả cụm thì chỉ quy
kết được cho **cả cụm**. Không được viết "pretrained cho +0.20".

#### Repo đã có gần hết — phần lớn là YAML

| của họ | ta có sẵn |
|---|---|
| `--img_size 16 128 128 --crop_size 14 112 112` | **`configs/preprocess_cghnet.yaml`** — khớp chính xác, **không build cache mới** |
| `--cb_loss` (Cui và cs., β=0.9999) | `losses.py::effective_number_weights`, cùng công thức `1−β^n` |
| `--smoothing 0.1` · flip · rotate · random_crop · mixup | đã có hết |

Mới: `uniformer3d` (đăng ký trong `_BUILDERS`), `RandomAppearance`, `data.sampling`.
**Không thêm dependency nào** — `timm` không cần (`DropPath` ~10 dòng, `trunc_normal_` có trong torch).

#### Ba con số phải biết trước khi chạy

1. **Ngân sách đi ngược trực giác.** `patch_embed1` stride `(1,2,2)` **không hạ mẫu trục lát**:

   | | bản pretrained 16×224×224 | của ta 14×112×112 |
   |---|---|---|
   | stage 3 (SABlock ×8, attention **toàn cục**) | 8×14×14 = **1568** token | 14×14×14 = **2744** token |

   1.75× token ⇒ ~3× chi phí stage 3, tức **đắt hơn** CGHNet (209 GFLOPs, 1.6 h/fold đo thật).

   **Cổng C ĐO THẬT trên T4 (2026-08-11): 0.869 s/batch · 78 s/epoch · 6.50 h/fold.**
   1 fold lọt một session 12h; **5 fold = 32.5h, vượt quota 30h/tuần** ⇒ phải trải qua hai
   tuần quota. ⚠️ **Người dùng đã chốt GIỮ NGUYÊN `[1,2,2]` của họ**, không đổi sang `[2,2,2]`
   dù rẻ hơn ~2–3×: tái lập trung thực recipe đạt 0.8078 quan trọng hơn tiết kiệm quota.
   32.5h là bài toán **kế hoạch**, không phải lý do đổi kiến trúc. Đừng "tối ưu" lại khoá đó.
   ⚠️ **Không suy giờ từ GFLOPs** — ước lượng kiểu đó cho CGHNet đã sai xa (S-123).

2. **Trọng số: bản `small` có ĐÚNG file, bản `base` thì không.**
   [`Sense-X/uniformer_video`](https://huggingface.co/Sense-X/uniformer_video) có
   `uniformer_small_k400_16x8.pth` (đúng của họ) nhưng chỉ có `uniformer_base_k600_**32x4**.pth`;
   bản `16x8` của base chỉ trên Google Drive. Đã chốt **chỉ làm small** — là 3/6 thành viên
   ensemble của họ. Không tham số nào có shape phụ thuộc số frame (đã kiểm), nên 32x4 vẫn nạp
   được nếu sau này cần base, và đó là một chỗ lệch phải ghi.

3. **⚠️ Recipe của họ bật HAI lớp cân bằng cùng lúc, đi ngược chẩn đoán §1.**
   `--cb_loss` (trọng số lớp trong loss) **và** `--sampling sqrt` (lấy mẫu lại). §1 đo ICC bị
   dự đoán **thừa** 1.26× và áp-xe 1.31× trên E4 — đẩy thêm là sai chiều. Không mâu thuẫn: §1
   đo trên **DenseNet from scratch**, biểu diễn khác có cán cân khác. **Tái lập trung thực
   trước, chẩn đoán sau** — cổng D + `weak_classes` sau fold 1; vượt 1.4× thì
   `data.sampling: instance` là ablation một khoá.

#### Bốn chỗ CỐ Ý lệch khỏi họ (đều phải vào báo cáo)

| chỗ | ta làm gì | vì sao |
|---|---|---|
| focal loss | **softmax** (`losses.py`) | của họ là **sigmoid** CB-focal. Chỗ lệch đáng kể nhất |
| `emboss`/`sharpen` | kernel + `scale` của PIL, **bỏ offset 128 và clip** | cache ta là **z-score**, của họ là [0,1] qua `uint8`. Đổi lại ta không mất mát lượng tử hoá |
| xoay | `rotate_mode: nearest` | họ xoay `mode='constant'` nên có dải 0 ở góc — đúng lỗi E12 đã đo (S-111). Đây là chỗ ta tốt hơn họ |
| `--mixup` | **CHƯA CÀI ĐƯỢC** (`mixup_alpha: 0`) | ⚠️ xem đính chính ngay dưới bảng |

⚠️ Và một chỗ **họ làm mà ta giữ nguyên dù nó đáng ngờ**: `blur`/`unsharp` của họ gọi
`ndimage.gaussian_filter` trên mảng **4 chiều** nên σ broadcast ra cả trục pha ⇒ **trộn 8 pha**.
Gần như chắc chắn ngoài ý định của họ. `filter_spatial_only: true` là ablation một khoá.

#### ⚠️ ĐÍNH CHÍNH S-128 — `--mixup` KHÔNG phải cờ chết, và nó là phép ta CHƯA CÓ

S-125 ghi *"cờ có trong `train.sh` nhưng `train.py` không nối nhánh mixup nào"* — **sai**, vì
tôi chỉ đọc `train.py`. Mixup của họ nằm trong **dataset**:
`mp_liver_dataset.py::__getitem__` gọi `self.mixup(image, label)` khi `args.mixup and label != 6`.

Và nó là một phép **khác hẳn** loại `data.mixup_alpha` của ta. Chú thích của chính họ là
`类内mixup` — **mixup TRONG CÙNG LỚP**:

```python
alpha = 1.0
index = random.choice([i for i, x in enumerate(self.lab_list) if int(x) == label])
lam = np.random.beta(alpha, alpha)              # Beta(1,1) = Uniform(0,1)
image = lam * image + (1 - lam) * load(self.img_list[index])
# NHÃN GIỮ NGUYÊN — không trộn nhãn
```

| | mixup của ta (`data.mixup_alpha`) | mixup của họ |
|---|---|---|
| trộn với | ca **bất kỳ** trong batch | ca **cùng lớp** trong toàn tập train |
| nhãn | trộn `λ·y + (1−λ)·y'` | **giữ nguyên** |
| λ | Beta(0.2, 0.2), lệch về hai đầu | Beta(1,1) = **đều** |
| phạm vi | mọi lớp | **loại HCC** (lớp 6) — chỉ 6 lớp thiểu số |
| xác suất | mỗi batch | **mọi mẫu** đủ điều kiện |

Bảng lớp của họ **trùng đúng thứ tự và đúng số ca** với `src/data/taxonomy.py`
(63/46/42/40/42/36/125 = 394), nên `label != 6` chắc chắn là loại HCC.

**Vì sao nó ăn khớp với `--sampling sqrt`:** lấy mẫu lại *có hoàn lại* sinh ra **bản sao y hệt**
của ca hiếm; mixup trong cùng lớp biến mỗi bản sao thành một nội suy mới. Không có nó thì
`sqrt` chỉ lặp lại đúng những ảnh cũ. Đây là mảnh thứ ba mà mục "hai lớp cân bằng" ở trên
bỏ sót — và nó là mảnh làm cho phép lấy mẫu lại **thêm thông tin** thay vì chỉ nhân bản.

**Vì sao nó khớp chẩn đoán §4 hơn mixup chuẩn:** di căn (n=40) không vào nổi top-2 ⇒ thiếu
biểu diễn. Nội suy trong cùng lớp sinh biến thiên mới **đúng cho các lớp hiếm**, mà không tạo
ra nhãn mềm chéo lớp — thứ mà §3 (0/117 lỗi sát sao) nói là không cứu được gì.

✅ **ĐÃ CÀI (2026-08-13, WORKLOG S-166).** `data.intra_class_mixup` ở tầng **dataset**
(`src/data/dataset.py::CachedLesionDataset`), không phải `run_epoch` — vì nó phải bốc một ca
cùng lớp từ **toàn tập train**, mà batch chỉ có 4 mẫu nên phần lớn batch không chứa hai ca
cùng một lớp hiếm. `data.mixup_alpha` là mixup chéo lớp có trộn nhãn, **không** thay thế được;
`tests/test_intra_class_mixup.py` chốt rằng hai khoá không được bật cùng lúc.

Chạy bằng `notebooks/21_intra_mixup.ipynb` + `configs/uniformer_s_intra_mixup.yaml` (khác
`uniformer_s.yaml` đúng hai khoá khoa học). **Chưa chạy fold nào.**

Ba tính chất của bản cài, cần biết khi đọc kết quả:

1. **Lớp bị loại được suy từ nhãn train của chính fold**, không ghi cứng số lớp. Trên cả 5
   fold của split này lớp đa số là HCC với đúng 100 ca train (lớp kế tiếp 50) nên phép suy là
   tất định — đã kiểm trực tiếp trên `splits/`.
2. **Ca đối tác có thể là chính nó** (pool gồm cả mẫu đang xét), khi đó phép trộn là đồng nhất
   bất kể λ. Xác suất `1/n_c`, tức 2–3% ở các lớp hiếm. Giữ như vậy để phân bố đúng nghĩa
   "bốc đều trong lớp".
3. **Đọc đĩa gấp đôi** cho mọi mẫu đủ điều kiện (6/7 số lớp). Cổng C của notebook đo `s/epoch`
   bằng chính loader của config nên con số nó in ra **đã bao gồm** chi phí này.

⚠️ **Phần cài đặt chưa xác nhận được trên máy local:** máy phát triển không có torch nên 8/13
test của phép này **skip**, gồm cả phép kiểm số học của tổ hợp lồi. Chỗ xác nhận thật là **cổng
F** trên Kaggle — nó giải ngược λ từ voxel và đọc file gốc bằng `np.load` độc lập với dataset.
Đừng bỏ cổng F vì thấy "đã có test".

⚠️ **Một chi tiết của họ ta không đọc được: thứ tự trộn so với augment.** Bản của ta trộn ảnh
**thô** rồi mới augment (một lần, cho ảnh đã trộn). Hai crop đều bám tổn thương nên nội suy
còn nghĩa giải phẫu, và cách này rẻ hơn. Nếu họ làm ngược thì chỗ lệch là một lượt augment
độc lập nữa — phải ghi vào báo cáo là chi tiết không xác định được.

#### Cây quyết định của ba augment lọc — 60% mẫu KHÔNG bị phép nào

Chúng **loại trừ nhau** (`elif`), nên gộp vào một lớp `RandomAppearance` là cách duy nhất giữ
đúng phân bố: edge 10% · emboss 10% · blur 8% · sharpen 8% · unsharp 4% · **không gì 60%**.
Nhẹ hơn nhiều so với "bật cả ba". Mọi phép áp **cùng tham số cho cả 8 pha** — đúng như họ, và
đúng bài học E6 (S-102).

#### Bar quyết định, chốt trước khi chạy (fold 1+2)

| gộp 2 fold | kết luận |
|---|---|
| **≥ 0.78** | pretrained là đòn bẩy thật ⇒ chạy đủ 5 fold, thành cấu hình chính |
| **0.73–0.78** | có tác dụng, chưa tới 0.8 ⇒ 5 fold, và ensemble với E4 ⊕ CGHNet |
| **0.69–0.72** | ngang E4 (0.6879 cùng 2 fold) ⇒ **dừng**, ghi thành kết quả âm: ba backbone pretrained độc lập đều không vượt from-scratch |
| **< 0.69** | nghi **lỗi triển khai** hơn kết luận khoa học (E13 cho <0.5 dù cổng A khớp 102/102) ⇒ đọc lại cổng A và B |

⚠️ **2 fold chỉ đủ để LOẠI, không đủ để CHỌN** (E6b: +0.038 ở 2 fold rồi −0.002 ở 5 fold, S-107).

**Ngoài phạm vi, có lý do:** `train_alldata.py` của họ train trên **toàn bộ** trainval nên
không đánh giá out-of-fold được bằng bất kỳ cách nào (chỉ dùng được trên test-104 — lần chạm
thứ hai, cần pre-registration mới); `json_refine.py` hợp nhất dự đoán trên test; ensemble 6
model của họ chọn fold nào lấy model nào **sau khi nhìn điểm val**, tức chọn trên tập đánh giá.

---

### E6 augmentation mạnh hơn — null trên trung bình, nhưng hai fold đi NGƯỢC nhau (2026-08-05, WORKLOG S-102)

Cùng 162 ca (fold 1+2). Khác baseline **chỉ trong `data.augment`**: xoay 10°→15° (áp 80% ảnh), tịnh tiến 8→12 voxel trong mặt phẳng, và **bật nhiễu cường độ** (baseline tắt).

| fold | n | E4 | E6 | hiệu | epoch tốt nhất |
|---|---|---|---|---|---|
| 1 | 82 | 0.7001 | **0.7580** | **+0.058** | 231 → 267 |
| 2 | 80 | 0.6771 | **0.5922** | **−0.085** | 297 → 110 |
| gộp | 162 | 0.6879 | 0.6739 | −0.014 | — |

Bootstrap ghép cặp 2000 lần: macro-F1 **−0.014** [−0.078, +0.052] P=0.68 · accuracy −0.007 P=0.75 · ECE +0.005 P=0.91. **Không có ý nghĩa thống kê.**

**Nhưng đừng đọc đây là "augmentation vô ích" — có hai hiệu ứng ngược chiều triệt tiêu nhau.**

**Bằng chứng 1 — fold 1 là con số tốt nhất dự án từng có, và nó ổn định.** Trung bình macro-F1 **50 epoch cuối**: E6 **0.701** so với E4 0.607. Không phải một đỉnh may mắn. Khoảng cách train/val cũng hẹp lại (+1.257 so với +1.495).

**Bằng chứng 2 — fold 2 không phải "epoch xấu", cả run sập.** `val_loss` chạm đáy ở **epoch 5** (E4 fold 2: epoch 79). Trung bình 50 epoch cuối 0.535 so với 0.572.

**Bằng chứng 3 — bảng từng lớp có cấu trúc rõ, không phải nhiễu:**

| lớp | n | E4 | E6 | hiệu |
|---|---|---|---|---|
| nang | 18 | 0.727 | 0.857 | **+0.130** |
| FNH | 15 | 0.759 | 0.778 | +0.019 |
| u máu | 26 | 0.833 | 0.840 | +0.007 |
| HCC | 50 | 0.783 | 0.761 | −0.022 |
| áp-xe | 18 | 0.778 | 0.743 | −0.035 |
| **ICC** | 19 | 0.449 | 0.364 | **−0.085** |
| **di căn** | 16 | 0.486 | 0.375 | **−0.111** |

⚠️ **Hai lớp yếu nhất — đúng hai lớp đang kéo macro-F1 xuống — TỆ ĐI nhiều nhất.**

**Giả thuyết (chưa chứng minh):** `RandomIntensity` áp scale/shift **độc lập cho từng pha** (`src/data/transforms.py`, `per_channel`). Chẩn đoán u gan trên MRI đa pha dựa vào cường độ **tương đối giữa các pha** — ngấm rồi thải (HCC), ngấm tiến triển (ICC), viền ngấm (di căn). Xáo mỗi pha ±10% độc lập là đổ nhiễu thẳng lên tín hiệu phân biệt. Khớp bảng trên: hai lớp phụ thuộc động học nhất tụt mạnh nhất, còn **nang** — nhận ra bằng tín hiệu tuyệt đối chứ không bằng động học — tăng nhiều nhất.

`configs/e6b_geom_only.yaml` tách đúng một biến (`intensity_prob: 0`) để trả lời.

⚠️ Giả thuyết cạnh tranh chưa loại được: augmentation mạnh làm **tối ưu hoá bất ổn** ở fold 2 (`val_loss` đáy ở epoch 5). Hai cách giải thích này không loại trừ nhau.

---

### E6b, bản sàng 2 fold — ⚠️ KẾT LUẬN ĐÃ BỊ BÁC BỞI 5 FOLD (2026-08-05, WORKLOG S-104)

> **Giữ lại làm hồ sơ, KHÔNG dùng làm căn cứ.** Mục này kết luận E6b là "cấu hình tốt nhất hiện có" dựa trên 2 fold. Đủ 5 fold thì E6b − E4 = **−0.002, P=0.92** — xem mục ngay dưới. Toàn bộ mức tăng ở đây đến từ fold 1, và fold 1 hoá ra là ngoại lệ.

E6b = E6 với `intensity_prob: 0`. Khác E6 **đúng một khoá**. Cùng 162 ca (fold 1+2).

| | fold 1 | fold 2 | gộp 162 | ECE |
|---|---|---|---|---|
| E4 | 0.7001 | 0.6771 | 0.6879 | 0.2212 |
| E6 | 0.7580 | 0.5922 | 0.6739 | 0.2262 |
| **E6b** | **0.7660** | 0.6611 | **0.7119** | 0.2349 |

Bootstrap ghép cặp: **E6b − E4 = +0.024** [−0.038, +0.083] P=0.44 · **E6b − E6 = +0.038** [−0.021, +0.095] P=0.18. **Không cái nào có ý nghĩa thống kê** — n=162, lực kiểm định thấp.

**Giả thuyết nhiễu cường độ được ỦNG HỘ.** Hai lớp phụ thuộc động học hồi phục đúng như dự đoán khi tắt nó: **ICC +0.091**, **di căn +0.069** (so với E6). Không chứng minh được, nhưng dự đoán ra trước và số liệu đi đúng hướng.

⚠️ **Kết quả KHÔNG khớp gọn dòng nào trong bảng đã chốt trước khi chạy — có HAI vấn đề tách bạch, không phải một:**

1. **Nhiễu cường độ độc-lập-theo-pha gây hại** → đã sửa bằng E6b.
2. **Augmentation hình học mạnh làm tối ưu hoá bất ổn** → **chưa sửa**. `val_loss` chạm đáy ở epoch **10** (E6: 5, E4: 79). Fold 2 của E6b vẫn 0.6611, **thấp hơn E4** 0.6771 — toàn bộ mức tăng của E6b đến từ fold 1.

Từng lớp so với E4: nang **+0.155** · FNH **+0.099** · u máu +0.042 · ICC +0.006 · HCC −0.035 · di căn −0.042 · áp-xe −0.056.

⚠️ **Hai lớp yếu vẫn yếu** (ICC 0.455, di căn 0.444). Mức tăng của E6b đến từ các lớp vốn đã dễ. Với mục tiêu macro-F1 thì đây là giới hạn: không thể tới 0.80 nếu hai lớp này còn ở mức 0.45.

⚠️ **ECE xấu đi** (0.2212 → 0.2349).

`configs/e9_e6b_ema.yaml` = E6b + EMA, nhắm đúng vấn đề 2. ⚠️ **Đã bỏ** — gốc của nó (E6b) không đứng vững trên 5 fold.

---

### E6b đủ 5 fold — NULL, và fold 1 là ngoại lệ. E4 được giữ làm cấu hình gốc (2026-08-06, WORKLOG S-107)

Đủ 394 ca, cùng bệnh nhân cùng thứ tự với E4. Bootstrap ghép cặp 2000 lần:

| | hiệu (E6b − E4) | CI95 | P |
|---|---|---|---|
| macro-F1 | **−0.0022** | [−0.0423, +0.0363] | **0.92** |
| accuracy | −0.0052 | [−0.0431, +0.0330] | 0.75 |
| ECE | +0.0248 | [−0.0199, +0.0705] | 0.29 |

Gộp out-of-fold: E4 **0.6851** · E6b **0.6828**. Theo luật đã chốt trước khi chạy (CI chứa 0 thì giữ E4), **E4 là cấu hình gốc mang sang test-104.**

| fold | E4 | E6b | hiệu |
|---|---|---|---|
| 1 | 0.7001 | **0.7660** | **+0.066** |
| 2 | 0.6771 | 0.6611 | −0.016 |
| 3 | 0.7304 | 0.7311 | +0.001 |
| 4 | 0.6680 | 0.6262 | −0.042 |
| 5 | 0.6618 | 0.6151 | −0.047 |

**Bài học về quy trình, quan trọng hơn kết quả:** sàng 2 fold cho +0.038 và trông rất hứa hẹn; 5 fold cho −0.002. **Hai fold chỉ đủ để LOẠI một ý tưởng, không đủ để CHỌN nó.** Con số 0.7660 từng là cao nhất dự án có được — nó là một fold may mắn.

#### Phát hiện đáng giá nhất của E6b không phải về E6b

Độ phân tán giữa các fold tăng hơn gấp đôi: SD mẫu 0.0280 → **0.0661**, trải 0.069 → 0.151. Ghép với chẩn đoán ổn định thì có một quy luật rất mạnh **trên cả 10 lần train** (5 fold × 2 cấu hình):

> **Epoch mà `val_loss` chạm đáy dự báo gần trọn vẹn macro-F1 cuối cùng của fold đó.** Spearman ρ = **+0.770**, P = **0.0092**.

```
 E4 f4  đáy@ep   3  F1 0.6680      E6b f3  đáy@ep  64  F1 0.7311
E6b f5  đáy@ep   6  F1 0.6151       E4 f2  đáy@ep  79  F1 0.6771
E6b f2  đáy@ep  10  F1 0.6611       E4 f1  đáy@ep 100  F1 0.7001
E6b f4  đáy@ep  12  F1 0.6262      E6b f1  đáy@ep 158  F1 0.7660
 E4 f5  đáy@ep  14  F1 0.6618       E4 f3  đáy@ep 227  F1 0.7304
```

Nút thắt là **thời điểm bắt đầu overfit**, và nó đúng với **cả E4** chứ không riêng E6b: E4 fold 4 và 5 chạm đáy ở epoch 3 và 14, và đúng là hai fold yếu nhất của E4. Augmentation mạnh chỉ làm tệ hơn — trung vị epoch chạm đáy 79 → 12, khoảng cách train/val cuối +1.91 → +2.45.

⚠️ Tương quan trên 10 run, và hai đại lượng cùng sinh từ một đường cong train nên **không tách được nhân quả**. Đây là chẩn đoán tốt, không phải bằng chứng rằng chặn overfit sẽ nâng điểm. Nhưng nó là cơ sở định lượng để ưu tiên **E7 = E4 + EMA**.

#### Giả thuyết nhiễu cường độ: đúng một nửa, không đổi được kết quả

So với E6 trên 162 ca thì cả ICC lẫn di căn đều hồi. Nhưng so với **E4** trên 394 ca thì hai lớp yếu đi ngược nhau và triệt tiêu:

| lớp | n | E4 | E6b | hiệu |
|---|---|---|---|---|
| di căn | 40 | 0.488 | 0.415 | **−0.073** |
| ICC | 46 | 0.519 | 0.547 | +0.028 |
| áp-xe | 42 | 0.660 | 0.689 | +0.029 |
| FNH | 36 | 0.761 | 0.753 | −0.007 |
| nang | 42 | 0.762 | 0.800 | +0.038 |
| HCC | 125 | 0.776 | 0.749 | −0.027 |
| u máu | 63 | 0.831 | 0.826 | −0.004 |

Precision hai lớp yếu: ICC 0.466 → 0.483 (đúng hướng, không đáng kể) · di căn 0.476 → **0.405** (sai hướng). Hướng nhầm chính không suy chuyển: HCC → ICC 9 → 12 ca, HCC → di căn 15 → 14 ca. **Nút thắt không nhúc nhích.**

⚠️ Calibration xấu đi nhất quán: ECE 0.2030 → 0.2344, NLL 2.03 → 2.35. Chưa có ý nghĩa thống kê (P=0.29) nhưng cùng chiều với kết quả trên 162 ca. Với dự án lấy calibration làm đóng góp headline, đây là thêm một lý do không chọn E6b.

Điểm sáng duy nhất, đo trên **cùng fold 2–5**: thiên lệch chọn epoch E4 +0.0787 so với E6b +0.0608. Không đủ để bù.

---

### TTA lật — ÂM, và nó đo được một thứ quan trọng hơn (2026-08-07, WORKLOG S-108)

TTA lật trên 5 checkpoint E4, 8 tổ hợp, 394 ca (notebook đã xoá ở S-176). Lượt 0 là ảnh gốc nên có đối chứng miễn phí — và nó dựng lại đúng macro-F1 lưu trong checkpoint tới 5 chữ số thập phân ở cả 5 fold, tức đường chạy đã được chứng minh đúng.

| | hiệu (TTA − gốc) | CI95 | P |
|---|---|---|---|
| macro-F1 | −0.0150 | [−0.0347, +0.0038] | 0.148 |
| accuracy | −0.0126 | [−0.0305, +0.0051] | 0.123 |
| **NLL** | **−0.2067** | [−0.2964, −0.1208] | **<0.0001** |

Gộp out-of-fold: gốc 0.6851 · TTA 0.6702. **4/5 fold âm.** Bản chỉ lật trong mặt phẳng (4 lượt, bỏ trục z) không cứu được: −0.0133 [−0.0280, −0.0003] **P=0.048**, tức âm *có ý nghĩa thống kê*.

#### Vì sao TTA thất bại: model không bất biến với chính augmentation của nó

| lượt | macro-F1 | so với gốc | đồng thuận với gốc |
|---|---|---|---|
| gốc | 0.6851 | — | 1.000 |
| lật y | 0.6618 | −0.023 | 0.944 |
| lật x | 0.6462 | −0.039 | 0.944 |
| lật z | 0.6456 | −0.040 | 0.878 |
| lật x+y+z | 0.6265 | −0.059 | 0.878 |

`RandomFlip` lật **từng trục độc lập với p=0.5** (`src/data/transforms.py`), nên trong lúc train cả 8 tổ hợp đều xuất hiện, mỗi cái xác suất 1/8 — phân bố train **đối xứng hoàn toàn** với phép lật. Model vẫn mất 0.02–0.06 khi bị lật.

> **Model học thuộc hướng của ảnh thay vì học đặc trưng bất biến với hướng, dù chính augmentation của nó dạy điều ngược lại.**

Đây là bằng chứng thứ ba, độc lập, cho cùng một câu chuyện overfit — và là cái **sạch nhất** trong ba, vì nó đo ở một checkpoint cố định, không dính gì tới chuyện chọn epoch:

1. epoch `val_loss` chạm đáy tương quan ρ=0.77 với macro-F1 cuối (S-107)
2. chênh `best` so với `last` +0.079 (S-078)
3. **không bất biến với phép lật** (mục này)

⚠️ **Phép kiểm nên chạy sau E7 (EMA), chốt trước:** nếu EMA thật sự chữa được overfit thì độ hụt khi lật (hiện 0.023–0.059) **phải co lại**. Đây là phép kiểm EMA độc lập với macro-F1, nói được EMA có tác dụng hay không kể cả khi điểm số đứng yên.

#### Chỗ TTA có ích, và vì sao vẫn không dùng

Sau hiệu chỉnh nhiệt độ leave-one-fold-out: ECE **0.1534 → 0.1131**, tự tin 0.745 → 0.738. Lợi thế này **sống sót** qua temperature scaling, khác với trường hợp focal loss ở E5.

Nhưng nó phải trả bằng macro-F1, mà macro-F1 mới là thứ so được với văn liệu; còn phần defer thì `−epistemic` của TTA (AURC 0.1901) vẫn thua MC-dropout (0.1689). Cộng thêm 8 lần chi phí suy luận. **Kết luận: không đưa TTA vào cấu hình khoá cho test-104.**

⚠️ Một cái bẫy đo được ở đây: điểm xếp hạng "tỉ lệ đồng thuận giữa 8 lượt" cho F1@80% = 0.7115 trông đẹp nhưng AURC 0.2606, **tệ hơn hẳn** max-prob (P=0.011). Tám lượt chỉ sinh 9 giá trị rời rạc nên rất nhiều ca đồng hạng. **Đừng chọn điểm xếp hạng bằng một con số coverage đơn lẻ.**

---

### E5 focal loss — 2/5 fold, chưa kết luận được (2026-08-05, WORKLOG S-094)

Cùng 162 ca (fold 1+2), cùng split, cùng seed. Config khác baseline **đúng 3 khoá**: `loss.name`, `loss.gamma`, `output_dir`.

| | macro-F1 | ECE thô | MCE | Brier | tự tin (lệch) |
|---|---|---|---|---|---|
| E4 (CE) | 0.6879 | 0.2212 | 0.3837 | 0.5585 | 0.903 (+0.206) |
| E5 (focal γ=2) | 0.6601 | **0.1542** | 0.4990 | **0.5033** | 0.833 (+0.136) |

Bootstrap ghép cặp 2000 lần trên cùng bệnh nhân: macro-F1 **−0.029** [−0.105, +0.048] P=0.47 · ECE **−0.050** [−0.123, +0.024] P=0.17. **Không cái nào có ý nghĩa thống kê.**

⚠️ **Phát hiện quan trọng hơn cả hai giả thuyết: sau khi hiệu chỉnh đúng cách, hai bên bằng nhau.**

| | T tối ưu ECE | ECE sau |
|---|---|---|
| E4 (CE) | 2.00 | 0.1281 |
| E5 (focal) | 1.50 | 0.1255 |

Focal *có* làm model bớt tự tin quá mức từ đầu (T cần nhỏ hơn: 1.50 so với 2.00), nhưng **"CE + temperature fit theo ECE" đã đạt 0.128 rồi**. Lợi thế ECE thô 0.154 của focal biến mất sau bước hiệu chỉnh mà dự án vốn đã làm. Đây là lý do kỹ thuật để **không** đổi loss chỉ vì mục tiêu calibration.

⚠️ Dùng `T` fit theo **NLL** cho focal thì ECE *xấu đi* (0.154 → 0.176) — bắn quá sang thiếu tự tin (0.596 so với accuracy 0.698). Với focal bắt buộc dùng `fit_temperature_min_ece`.

⚠️ MCE xấu đi (0.384 → 0.499) và AURC xấu đi nhẹ (0.181 → 0.196). Fold 2 tụt rõ (0.677 → 0.609) còn fold 1 hoà (0.700 → 0.697).

---

### Lưu trữ: Grad-CAM 4 ca demo — kết quả thật (2026-08-05, WORKLOG S-098)

Đây là kết quả lịch sử; module và notebook Grad-CAM đã được gỡ khỏi cây hoạt động ở S-132. Mỗi ca trong phép đo cũ dùng model của fold chứa nó ở val. Demo hiện dùng heatmap `|input × gradient|` đa thì trên crop E4.

| ca | thật | đoán | bản đồ lớp thật | đỉnh (x,y,z) | lệch tâm |
|---|---|---|---|---|---|
| MR113627 | ICC | ICC | không cần | (55, 55, 24) | 8.5 |
| MR170828 | u máu | u máu | không cần | (54, 55, 24) | 8.6 |
| MR207769 | di căn | áp-xe | có | (40, 55, 24) | 17.7 |
| **MR127280** | **di căn** | **u máu** | **SUY BIẾN** | **(55, 87, 0)** | **35.1** |

Crop cắt **bám tổn thương** nên tổn thương nằm giữa khối (tâm 55, 55, 15).

**Hai ca đoán đúng có đỉnh đúng tâm trong mặt phẳng** (55,55) — bằng chứng model nhìn vào tổn thương chứ không vào rìa.

**`MR127280` là ca thất bại toàn diện, và bản đồ nói ra điều đó:** đỉnh ở (55, **87**, **0**) — lệch 32 voxel theo y và nằm ở **lát biên**. Cộng với việc bản đồ cho lớp thật **suy biến** (không voxel nào ủng hộ lớp đúng). Nghĩa là model không chỉ đoán sai — nó nhìn nhầm chỗ và không thấy bằng chứng nào cho đáp án đúng. Đây là ca đáng đưa vào phần failure analysis của báo cáo.

**Độ nhạy theo thì** (tổng = 1; mức đều = 0.125):

| ca | C-pre | C+A | C+V | C+Delay | T2WI | DWI | InPhase | OutPhase |
|---|---|---|---|---|---|---|---|---|
| MR113627 | 0.120 | 0.105 | 0.129 | **0.161** | 0.151 | 0.150 | 0.091 | 0.092 |
| MR127280 | **0.214** | 0.139 | 0.166 | 0.183 | 0.083 | 0.105 | 0.053 | 0.057 |
| MR170828 | 0.125 | 0.124 | 0.194 | **0.201** | 0.186 | 0.072 | 0.046 | 0.053 |
| MR207769 | 0.094 | 0.158 | 0.152 | **0.178** | 0.129 | 0.158 | 0.043 | 0.087 |

**In Phase và Out Phase thấp nhất ở cả 4 ca** (0.043–0.092, đều dưới mức đều). Hợp lý về lâm sàng: hai thì chemical-shift chủ yếu để phát hiện mỡ, ít phân biệt được giữa 7 lớp này; còn các thì có thuốc mang đúng kiểu ngấm thuốc — thứ dẫn dắt chẩn đoán u gan.

⚠️ **Bốn cảnh báo bắt buộc kèm bộ số này:**

1. **Bản đồ gốc chỉ 7×7×2.** Theo Z chỉ có **2 mức** rồi nội suy lên 32 lát — vị trí `z` của đỉnh chỉ nói được "nửa trên hay nửa dưới", không hơn. Trong mặt phẳng mỗi ô gốc phủ 16 voxel, nên lệch đỉnh **dưới ~8 voxel là trong cùng một ô**, đừng diễn giải.
2. **n = 4 ca.** "In/Out Phase luôn thấp nhất" là quan sát trên 4 ca, không phải kết luận thống kê.
3. **Là saliency, không phải ablation.** Không nói bỏ hẳn một thì đi thì mất bao nhiêu điểm.
4. **Mức phân biệt giữa các thì là vừa phải** — thì cao nhất chỉ gấp 1.3–1.7 lần mức đều. Model trải độ nhạy khá rộng, không dựa hẳn vào một thì.

---

### Trustworthiness — calibration & selective (2026-08-04, WORKLOG S-079)

Chạy bằng `python -m src.eval.trust --run-dir runs/E4_cv_results`. Temperature fit **leave-one-fold-out**: `T` áp lên fold `f` học từ 4 fold còn lại, nên không ca nào được hiệu chỉnh bởi một `T` đã nhìn thấy nó.

| | ECE | MCE | Brier | NLL | tự tin TB | macro-F1 |
|---|---|---|---|---|---|---|
| chưa hiệu chỉnh | 0.2030 | 0.6775 | 0.5488 | 2.0308 | 0.889 (+0.186) | 0.6851 |
| temp-scaled, fit **NLL** | 0.1756 | 0.8026 | 0.5228 | **1.1687** | 0.606 (−0.097) | 0.6851 |
| temp-scaled, fit **ECE** | **0.1534** | **0.3510** | **0.5162** | 1.2812 | 0.745 (+0.042) | 0.6851 |

*(accuracy thật 0.7030; cột "tự tin TB" kèm độ lệch so với accuracy)*

Bốn điều rút ra:

1. **Model tự tin quá mức nghiêm trọng.** Tự tin trung bình 0.889 trong khi đúng 70,3%; trung vị 0.987 và phân vị 75 là **1.000**. Đây là hệ quả trực tiếp của 300 epoch CE trần không label smoothing, đúng như `src/eval/calibration.py` mô tả.
2. **`T` tối ưu NLL ≠ `T` tối ưu ECE, và chênh nhau nhiều.** NLL nhỏ nhất ở `T≈3.26`, ECE nhỏ nhất ở `T≈2.05`. Lấy `T` của NLL thì model **bắn quá sang thiếu tự tin** (0.606 so với accuracy 0.703) và MCE *xấu đi* (0.678 → 0.803). Fit theo ECE tốt hơn ở mọi metric calibration, chỉ thua NLL. Có `fit_temperature_min_ece` cho việc này.
3. **Một scalar là không đủ.** Ngay cả `T` tốt nhất cũng chỉ hạ ECE xuống 0.153 — vẫn lớn. Bước tiếp theo hợp lý là vector/matrix scaling hoặc ensemble, không phải chỉnh thêm `T`.
4. **Selective prediction có tác dụng nhưng yếu.** AURC 0.206 so với điểm ngẫu nhiên 0.296 [0.258, 0.335] và oracle 0.049 — tốt hơn ngẫu nhiên rõ rệt, còn xa hoàn hảo. macro-F1@80% = 0.6813 [0.6286, 0.7327], **gần như không hơn** 0.6851 ở coverage 100%. Ở mức sai số ≤10% chỉ tự quyết được **12,9%** số ca.

⚠️ **Hiệu chỉnh xác suất làm selective hơi TỆ đi** (AURC 0.206 → 0.214). Không mâu thuẫn: temperature không thêm thông tin nào, chỉ đổi thang. Kết luận kỹ thuật cho web app: **xếp hạng/defer theo max-prob thô, hiển thị theo xác suất đã hiệu chỉnh.**

⚠️ Giả thuyết "gộp 5 model khác nhau làm hỏng thứ hạng tin cậy" **đã kiểm và bác bỏ**: AURC trung bình trong từng fold 0.2038, gộp 394 ca 0.2059 — như nhau.

---

### MC-dropout & phép lai — selective prediction cuối cùng cũng có tác dụng (2026-08-04, WORKLOG S-087)

MC-dropout K=20 lượt/ca trên chính model của từng fold (notebook đã xoá ở S-176) (nên mọi thành viên đều mù với val của nó). Đọc bằng `python -m src.eval.trust --run-dir runs/E4_per_phase_results --members`.

**MC-dropout hạ macro-F1 0.6851 → 0.5852 (−0.100).** Không dùng làm bộ dự đoán được. Nhưng ECE của nó là **0.1216** — tốt hơn cả temperature scaling tốt nhất (0.1534) mà không cần fit gì.

**Phép lai là thứ đáng giá:** dự đoán lấy từ model tất định, **chỉ điểm xếp hạng defer** lấy từ epistemic của MC-dropout.

| điểm xếp hạng defer | AURC | F1@100% | F1@90% | F1@80% | F1@70% | F1@50% |
|---|---|---|---|---|---|---|
| tất định · max-prob | 0.2059 | 0.6851 | 0.6909 | 0.6799 | 0.7043 | 0.7388 |
| **LAI · tất định + −epistemic** | **0.1689** | 0.6851 | 0.6923 | **0.7222** | 0.7367 | 0.7484 |

Bootstrap **ghép cặp** trên hiệu (2000 lần, phân tầng, mức bệnh nhân):

| | hiệu | CI95 | P |
|---|---|---|---|
| F1@80%(epistemic) − F1@100% | **+0.0350** | [+0.0039, +0.0647] | **0.030** |
| AURC(epistemic) − AURC(max-prob) | **−0.0346** | [−0.0648, −0.0080] | **0.013** |
| *đối chứng:* F1@80%(max-prob) − F1@100% | −0.0027 | [−0.0340, +0.0263] | 0.88 |

**Kết luận cho báo cáo:** selective prediction có tác dụng, nhưng **chỉ khi tín hiệu bất định đến từ mức bất đồng giữa các lượt dự đoán, không phải từ softmax của một lượt tất định.** Dòng đối chứng là thứ mang cả lập luận: cùng model, cùng dự đoán, chỉ đổi cách xếp hạng — max-prob cho +0.000, epistemic cho +0.035.

⚠️ F1@50% (+0.060) **không có ý nghĩa thống kê** (P=0.061), và ở coverage thấp lớp hiếm bắt đầu biến mất. Đừng báo con số 0.7484 như một mức đạt được.

⚠️ Đã xem 5 điểm xếp hạng rồi báo cái tốt nhất. `−epistemic` là lựa chọn có lý do từ trước (nó *là* đại lượng headline), và dòng đối chứng mới là thứ chống đỡ kết luận — nhưng phải ghi rõ điều này trong báo cáo.

⚠️ Đây vẫn là **MC-dropout, không phải deep ensemble thật**. Ensemble nhiều seed (mọi thành viên đều mạnh) nhiều khả năng cho cả nền cao lẫn thứ hạng tốt; MC-dropout phải đánh đổi.

---

---
