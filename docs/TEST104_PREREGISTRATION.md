# Pre-registration — chạm test-104 official, lần thứ nhất

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
