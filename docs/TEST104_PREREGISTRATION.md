# Pre-registration — chạm test-104 official

> File này append-only theo lần chạm. §A = lần 1 (đã chạy). §B = lần 2 (đã khoá).
> **Không sửa mục của lần đã chạy** — nó là hồ sơ chứng minh quyết định có TRƯỚC kết quả.

---

# §A. Chạm lần thứ nhất — ĐÃ CHẠY 2026-08-07 (WORKLOG S-110)

> **Trạng thái:** ĐÃ KHOÁ, chưa chạy.
> **Ngày khoá:** 2026-08-07 · **Người duyệt:** người dùng (yêu cầu trực tiếp, 2026-08-07)
> **Điều kiện:** file này phải được **commit trước** khi bất kỳ dòng code nào đọc `splits/test_official.txt` để suy luận.

Test-104 là held-out khoá kín, chạm **đúng một lần** (AGENTS.md §3.4, §10). File này ghi lại **mọi lựa chọn** trước khi nhìn thấy một con số nào của tập test. Sau khi chạm, không được đổi bất cứ thứ gì trong danh sách dưới đây dựa trên kết quả test.

Lý do chạm bây giờ: cần một con số **so sánh được với văn liệu** cho báo cáo tiến độ. Mọi con số nội bộ tới giờ đều là val out-of-fold, không so trực tiếp được với bảng test-104 của challenge và của CGHNet.

---

## 1. Cấu hình được khoá

| khoản | giá trị | căn cứ |
|---|---|---|
| config train | `configs/baseline_3dpatch.yaml` | khoá bởi `tests/test_protocol_conformance.py` |
| cache | E4: `crop_mode=lesion_tight` · `target_size=[112,112,32]` · `align_phases=per_phase` | E4 − E1 = +0.126 [+0.033, +0.230] P=0.009 |
| **không** dùng E6b | — | E6b − E4 = −0.0022 [−0.0423, +0.0363] **P=0.92** trên 394 ca; luật chốt trước là "CI chứa 0 thì giữ E4" (WORKLOG S-107) |
| **không** dùng TTA | — | trên 394 ca: −0.0150 [−0.0347, +0.0038]; bản 4 lượt trong mặt phẳng −0.0133 [−0.0280, −0.0003] **P=0.048**, âm có ý nghĩa (WORKLOG S-108) |
| **không** dùng EMA / pretrained | — | E7, E8 chưa chạy. Không chờ chúng; nếu chạy sau và muốn có số test thì đó là **lần chạm thứ hai**, phải xin phép lại |

### Checkpoint — sha256 ghim sẵn

Năm file `best_fold_N.pt`, đo ở máy local, đối chiếu với WORKLOG S-081:

```
fold 1  2e1f3e1ad477ad59      fold 4  3fe18f1eb3de4431
fold 2  30a8eb9ee221d453      fold 5  d61cc7ed94b8ebf0
fold 3  00c133e031bdf8fe
```

Lệch một mã băm ⇒ **dừng**, không chạy tiếp.

---

## 2. Bộ dự đoán chính: ensemble 5 fold

**Trung bình softmax của 5 model**, trọng số bằng nhau.

Hai lý do, cả hai đều phải đúng thì lựa chọn này mới hợp lệ:

1. **Hợp lệ về leakage.** Không model nào trong 5 cái từng thấy 104 ca này — cả 5 chỉ train trên tập con của 394 ca trainval, và `Splits.validate()` khẳng định `val_fold_i ∩ test = ∅` với mọi `i`. Đây là chỗ **duy nhất** ensemble 5 fold hợp lệ; trên out-of-fold thì cấm (AGENTS.md §3, cảnh báo sau luật 10).
2. **So sánh đúng đối tượng.** Bảng CGHNet (AGENTS.md §5) dùng đúng protocol "5 model từ 5 fold, báo trên test-104 official". Nếu ta báo một model đơn thì đang so lệch loại.

**Báo kèm nhưng KHÔNG phải số chính:** 5 model đơn lẻ trên test-104, và trung bình ± SD của chúng. Mục đích là cho thấy độ phân tán, không phải để chọn cái tốt nhất. **Cấm** báo model đơn tốt nhất như một kết quả.

---

## 3. Hiệu chỉnh xác suất

`T` fit trên **394 ca out-of-fold** bằng `fit_temperature_min_ece`, rồi áp **mù** lên test. Không bao giờ fit trên test.

Vì sao dùng `min_ece` chứ không `min_nll`: trên out-of-fold, `T` tối ưu NLL bắn quá sang thiếu tự tin (0.606 so với accuracy 0.703) và làm MCE *xấu đi* 0.678 → 0.803 (WORKLOG S-079).

⚠️ **Một điểm yếu phải ghi rõ trong báo cáo, không được giấu:** `T` học từ phân bố xác suất của **model đơn**, nhưng được áp lên xác suất của **ensemble**, mà ensemble vốn đã bớt tự tin hơn. Nhiều khả năng `T` này **hiệu chỉnh quá tay** trên ensemble. Vì vậy:

- hàng ensemble báo **cả hai** cột: chưa hiệu chỉnh và đã hiệu chỉnh
- hàng 5 model đơn thì `T` khớp phân bố, nên đọc được bình thường
- **không** được fit lại `T` trên test để chữa việc này

---

## 4. Selective prediction

**Điểm xếp hạng defer đã chốt: `−epistemic` của ensemble** — mức bất đồng giữa 5 model, tính bằng `uncertainty_decomposition` (mutual information).

Chốt trước vì trên out-of-fold, đại lượng tương ứng (epistemic của MC-dropout) đánh bại max-prob có ý nghĩa thống kê: AURC −0.0346 [−0.0648, −0.0080] P=0.013, F1@80% +0.0350 [+0.0039, +0.0647] P=0.030 (WORKLOG S-087).

Trên test-104 đây là **deep ensemble thật**, không phải MC-dropout, nên mọi thành viên đều là model mạnh — kỳ vọng tốt hơn, nhưng đó là kỳ vọng, không phải kết luận.

**Dòng đối chứng bắt buộc:** cùng dự đoán ensemble, xếp hạng bằng `max-prob`. Dòng này mang cả lập luận: nếu max-prob cũng cho mức tăng tương đương thì kết luận "phải dùng bất đồng" sụp.

**Coverage báo cáo:** 100%, 90%, 80%, 70%. Chốt bốn mức này trước; **không** thêm mức nào sau khi nhìn số.

---

## 5. Danh sách metric — chốt trước, không thêm không bớt

**Phân loại:** macro-F1 · Cohen's κ · balanced accuracy · accuracy · F1 từng lớp · ma trận nhầm lẫn.

**Calibration:** ECE (adaptive, 15 bin) · MCE · Brier · NLL · tự tin trung bình kèm độ lệch so với accuracy.

**Selective:** AURC · macro-F1 tại 4 mức coverage ở §4 · coverage tại mức rủi ro ≤ 10%.

Mọi metric ở mức tập kèm **CI95 bootstrap phân tầng mức bệnh nhân, 2000 lần**, seed 20260727 (AGENTS.md §3.5).

**Metric chính, dùng để so với văn liệu: macro-F1.** Các metric khác là mô tả, không phải để chọn ra cái đẹp nhất mà báo.

---

## 6. Mốc đối chiếu — ghi trước để khỏi hợp lý hoá sau

Cùng tập test-104 official, cùng `sklearn.f1_score(average='macro')`:

| | macro-F1 |
|---|---|
| baseline official (UniFormer-S 3D, from scratch) | 0.6083 |
| hạng 20–24 của challenge | 0.5047 – 0.6076 |
| ResNet3D trong bảng CGHNet | 0.709 ± 0.021 |
| CGHNet | 0.818 ± 0.012 |
| đội nhất challenge | 0.8322 |

**Ước lượng của ta trước khi chạy:** out-of-fold cho 0.6851, trong đó có thiên lệch chọn epoch **+0.079** (đo trên fold 2–5: `best` 0.6824 so với `last` 0.6038). Hai lực ngược chiều:

- ensemble 5 model **có thể** nâng, thường +0.02…+0.04
- thiên lệch chọn epoch **biến mất** trên test, kéo xuống

Nên khoảng hợp lý là **0.62 – 0.72**, và tôi không đoán được nó rơi vào đâu trong đó. Ghi lại con số này ở đây để sau không thể nói "đúng như dự đoán" với bất kỳ kết quả nào.

**Cách đọc kết quả, chốt trước:**

| kết quả | kết luận được phép rút |
|---|---|
| ≥ 0.6083 | vượt baseline official; nói được |
| trong 0.62–0.72 | khớp ước lượng từ out-of-fold; thiên lệch chọn epoch đã được ensemble bù lại phần nào |
| < 0.60 | out-of-fold đã ước lượng quá lạc quan hơn cả phần +0.079 đo được; phải nói rõ trong báo cáo |
| bất kỳ giá trị nào | **không** được đổi config/checkpoint/`T`/ngưỡng rồi chạy lại |

---

## 7. Điều bị cấm sau khi chạm

1. Đổi config, checkpoint, `T`, ngưỡng defer, hay bộ dự đoán **vì** con số test.
2. Chạy lại test với một cấu hình khác mà không xin phép và không viết pre-registration mới. Lần đó là **chạm thứ hai**, và phải báo cáo là chạm thứ hai.
3. Báo model đơn tốt nhất trong 5 thay cho ensemble.
4. Fit `T` hoặc chọn coverage trên test.
5. Thêm metric sau khi đã nhìn số.

## 8. Điều được phép sau khi chạm

- Chạy lại **phần báo cáo** từ file `test_probs.npz` đã lưu, bao nhiêu lần cũng được — nó không đọc lại ảnh và không đổi dự đoán.
- Phân tích lỗi định tính (xem ca nào sai, Grad-CAM trên ca sai) — miễn là không dùng nó để chỉnh model rồi báo lại số test.

---

# §B. Pre-registration — chạm test-104 official, **LẦN THỨ HAI**

> **Trạng thái:** ĐÃ KHOÁ, chưa chạy.
> **Ngày khoá:** 2026-08-14 · **Người duyệt:** người dùng (yêu cầu trực tiếp, 2026-08-14)
> **Điều kiện:** phần này phải được **commit trước** khi bất kỳ dòng code nào đọc `splits/test_official.txt` để suy luận. `src/eval/test_once.py` kiểm điều đó bằng `git log`, không bằng sự tồn tại của file.

⚠️ **ĐÂY LÀ LẦN CHẠM THỨ HAI.** Lần thứ nhất: 2026-08-07, cấu hình E4, kết quả macro-F1 0.6162 (WORKLOG S-110). Mọi báo cáo dùng số của lần này **bắt buộc** nói rõ đây là lần chạm thứ hai và tập test đã bị nhìn một lần trước đó (AGENTS.md §3.4, §10).

**Lý do chạm:** UniFormer-S + Kinetics đã đủ 5 fold và vượt E4 trên out-of-fold **+0.1296 [+0.0778, +0.1809] P<0.001** (WORKLOG S-169) — mức chênh lớn hơn mọi can thiệp dự án từng đo. Cấu hình chính đã đổi, nên con số so được với văn liệu cũng phải đo lại trên cấu hình mới. Việc chọn cấu hình này được quyết **hoàn toàn trên out-of-fold**, không dùng một thông tin nào của test.

---

## B1. Cấu hình được khoá

| khoản | giá trị |
|---|---|
| config train | `configs/uniformer_s.yaml`, **không sửa gì** |
| kiến trúc | UniFormer-S 3D · `patch_embed1_stride [1,2,2]` · `head_dropout 0.0` |
| trọng số khởi tạo | Kinetics-400 `uniformer_small_k400_16x8.pth` |
| cache | lưới `128×128×16` của `configs/preprocess_cghnet.yaml`, cắt giữa còn `112×112×14` |
| `--pin-set` | `uniformer` |
| **không** TTA | trên E4 đã đo âm; chưa đo trên cấu hình này ⇒ không dùng |
| **không** EMA, **không** intra-class mixup | `uniformer_s_intra_mixup.yaml` chưa chạy fold nào |
| **không** ensemble với E4 hay CGHNet | trên 394 ca làm tệ đi ở **mọi** trọng số (S-169) |

### Checkpoint — sha256 ghim sẵn

Năm file `runs/Uniformer3D/fold_N/uniformer3D_best_N.pt`, đo ở máy local 2026-08-14:

```
fold 1  62948396cdccd5a4      fold 4  1b44f40bf97d3b30
fold 2  0d36a6cd52fde563      fold 5  8edf4fbc07f181b2
fold 3  bc023a9a7662d38e
```

Lệch một mã băm ⇒ **dừng**, không chạy tiếp. Đã kiểm không mã nào trùng với bộ của lần chạm 1.

---

## B2. Bộ dự đoán chính: ensemble 5 fold, trung bình softmax, trọng số bằng nhau

Giữ nguyên lựa chọn và lập luận của §2. Hai điều kiện vẫn đúng: không model nào từng thấy 104 ca này, và bảng CGHNet dùng đúng protocol "5 model từ 5 fold".

**Báo kèm nhưng KHÔNG phải số chính:** 5 model đơn, và trung bình ± SD của chúng. **Cấm** báo model đơn tốt nhất — lần chạm 1 đã gặp đúng cám dỗ này (fold 2 đạt 0.6308, cao hơn ensemble 0.6162).

---

## B3. Hiệu chỉnh xác suất — ⚠️ ĐỔI so với lần chạm 1, và lý do nằm ở out-of-fold

**Số chính là bản CHƯA hiệu chỉnh.** Bản temperature-scaled báo kèm.

Đây là thay đổi có chủ đích so với §3, và căn cứ **hoàn toàn từ 394 ca out-of-fold** (S-169), không có gì của test:

| trên out-of-fold | ECE | MCE | tự tin (lệch so accuracy 0.8376) |
|---|---|---|---|
| chưa hiệu chỉnh | **0.1073** | **0.4233** | 0.903 (+0.065) |
| temp-scaled, fit ECE | 0.0943 | **0.7376** | 0.8165 (−0.021) |

`T` chỉ 1.45–1.53 (E4 cần 2.05–3.26) — model **gần calibrated sẵn**. Hiệu chỉnh hạ ECE chút ít nhưng **làm MCE xấu đi 74%** và đẩy sang thiếu tự tin. Với một model đã gần đúng thì temperature scaling là lợi bất cập hại, và đó là một kết quả có nội dung chứ không phải bước bị bỏ qua.

`T` vẫn fit trên 394 ca out-of-fold bằng `fit_temperature_min_ece` rồi áp **mù**. **Không bao giờ fit trên test.**

⚠️ Cảnh báo của §3 vẫn nguyên giá trị và đã ứng nghiệm ở lần 1: `T` học từ phân bố *model đơn* áp lên *ensemble* thì hiệu chỉnh quá tay. Lần này nó là thêm một lý do để lấy bản chưa hiệu chỉnh làm số chính.

---

## B4. Selective prediction

**Điểm xếp hạng chính đã chốt: `max-prob` của ensemble.**
**Dòng đối chứng bắt buộc: `−epistemic`** (bất đồng giữa 5 model, `uncertainty_decomposition`).

⚠️ **Đây là ĐẢO vai trò so với §4 của lần chạm 1**, và có căn cứ đo được từ hai nguồn:

1. **Lần chạm 1 đã bác luận điểm của S-087.** Trên test-104, hai cách xếp hạng không khác nhau (AURC +0.0009 **P=0.90**), và max-prob một mình cho +0.070 **P=0.016**. Lý do nhất quán: với 5 model độc lập thật, softmax của trung bình đã là tín hiệu bất định tốt.
2. **Trên out-of-fold của chính cấu hình này**, max-prob là thứ duy nhất đo được (MC-dropout vô nghĩa vì `head_dropout: 0.0` ⇒ không có lớp Dropout nào).

**Coverage báo cáo: 100%, 90%, 80%, 70%.** Bốn mức, chốt trước, **không** thêm sau khi nhìn số.

### Dự đoán chốt trước — có thể bị bác

Trên 394 ca out-of-fold, mức tăng khi từ chối ca **không đạt ý nghĩa thống kê** ở mọi mức: @90% +0.001 P=0.72 · @80% +0.017 P=0.29 · @70% +0.026 P=0.22. Cơ chế đo được: **0/64 lỗi có biên < 0.10** — model sai một cách tự tin.

**Dự đoán: trên test-104 selective cũng KHÔNG đạt ý nghĩa thống kê ở mức 80%.** Nếu nó đạt, dự đoán này sai và phải ghi rõ là sai — không được diễn giải ngược thành "đúng như mong đợi".

---

## B5. Latency — bắt buộc đo và báo cáo

`predict_members` đo sẵn và ghi vào `test_run_meta.json`. Hai con số phải vào báo cáo:

- `per_case_1model_ms` — so được với văn liệu
- `per_case_ensemble_ms` — thứ hệ thống thật phải trả, và là con số web app phải hiển thị

Kèm ngữ cảnh đo: thiết bị, `batch_size`, `amp`. ⚠️ Đo trên **T4 của Kaggle** với batch của config, **không phải** đo một ca một. Latency thật của web app (một ca, một lần) sẽ **cao hơn** con số này vì không có lợi thế theo lô — phải nói rõ, không được trình bày `per_case` như độ trễ một ca đơn lẻ.

Lần chạm 1 đã bỏ lỡ phép đo này và không truy lại được (WORKLOG S-116) — test chạm một lần nên không chạy lại để đo được.

---

## B6. Danh sách metric — y hệt §5, không thêm không bớt

Phân loại · calibration · selective như §5. CI95 bootstrap phân tầng mức bệnh nhân, 2000 lần.

**Metric chính: macro-F1.**

**Thêm một phép so, và nó hợp lệ:** UniFormer so E4 **ghép cặp trên đúng 104 ca**, dùng `test_probs.npz` của lần chạm 1 đã lưu ở `runs/test104`. Đọc lại file đã lưu **không phải** một lần chạm mới. Phép so này hợp lệ vì cấu hình UniFormer được chọn trên out-of-fold, không dùng thông tin nào của test.

---

## B7. Mốc đối chiếu và ước lượng — ghi trước để khỏi hợp lý hoá sau

| | macro-F1 test-104 |
|---|---|
| **E4, lần chạm 1 của chính dự án** | **0.6162** |
| baseline official (UniFormer-S, from scratch) | 0.6083 |
| ResNet3D trong bảng CGHNet | 0.709 ± 0.021 |
| Uniformer trong bảng CGHNet | 0.719 ± 0.022 |
| đội hạng 2 (recipe đang tái lập) | 0.8078 |
| CGHNet | 0.818 ± 0.012 |
| đội hạng 1 | 0.8322 |

**Ước lượng trước khi chạy.** Out-of-fold 0.8147, thiên lệch chọn epoch đo được **+0.0797**. Trên E4, mức hụt out-of-fold → test là **−0.069**, gần trùng khít với thiên lệch +0.079 của nó. Áp cùng mức hụt: **0.8147 − 0.069 ≈ 0.746**.

Khoảng hợp lý: **0.72 – 0.79**. Tôi không đoán được nó rơi vào đâu trong đó. Ghi ở đây để sau không thể nói "đúng như dự đoán" với bất kỳ kết quả nào.

### Cách đọc kết quả, chốt trước

| kết quả | kết luận được phép rút |
|---|---|
| **≥ 0.75** | vượt rõ mọi mốc dưới SOTA; so được với `Uniformer 0.719` của bảng CGHNet |
| **0.72 – 0.75** | khớp ước lượng; mức hụt out-of-fold→test tái lập đúng như đo trên E4 |
| **0.65 – 0.72** | hụt sâu hơn phần thiên lệch đã đo ⇒ out-of-fold lạc quan vì lý do khác nữa, **phải điều tra và ghi rõ** |
| **< 0.65** | nghi **lỗi triển khai** hơn kết luận khoa học (cache sai hình học, checkpoint lệch) ⇒ đọc lại meta trước khi kết luận gì |
| bất kỳ giá trị nào | **không** được đổi config/checkpoint/`T`/ngưỡng rồi chạy lại |

⚠️ **Dù kết quả bao nhiêu cũng KHÔNG được viết "ta ngang đội hạng 2 / ngang CGHNet"** trừ khi CI95 loại được mốc đó — và với n=104 thì CI rộng khoảng ±0.09, nên gần như chắc chắn là không loại được.

---

## B8. Điều bị cấm sau khi chạm — như §7, cộng thêm

6. **Không** được chọn giữa bản hiệu chỉnh và chưa hiệu chỉnh **sau khi** nhìn số. B3 đã chốt bản chưa hiệu chỉnh là chính.
7. **Không** được đổi điểm xếp hạng defer sau khi nhìn số. B4 đã chốt `max-prob` là chính.
8. Lần chạm **thứ ba** cần xin phép lại và một pre-registration §C mới.
