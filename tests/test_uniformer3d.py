"""Test UniFormer-3D và config tái lập đội hạng 2 LLD-MMRI 2023.

Phần lớn file này **không cần torch**, và đó là chủ ý: những thứ đáng neo nhất ở đây là
*cổng chặn* và *hình học*, và cả hai đều đã từng hỏng thầm lặng trên Kaggle sau khi đã tốn
công mount cache:

* **E8** đặt sai ``shortcut_type`` mà tỉ lệ khoá khớp vẫn ~85% — qua ngưỡng phần trăm ngon
  lành (WORKLOG S-118). Cổng phải kiểm *khoá NÀO* thiếu.
* **E2** chạy suốt ở 48 in-plane thay vì 96 mà không có gì báo (WORKLOG S-065). Số token
  phải tính được ở local, không phải phát hiện trên GPU.
* **E13** phát hiện 79 s/epoch *sau khi* đã cam kết cả session (WORKLOG S-120).
"""

from __future__ import annotations

import inspect

import pytest
import yaml
from src.models.uniformer3d import (
    DROPPED_PREFIXES,
    PRETRAINED_FILENAMES,
    UNIFORMER_VARIANTS,
    build_uniformer3d,
    count_flops_proxy,
    stage_token_counts,
    strip_state_dict,
    unexpected_missing_keys,
    variant_spec,
)
from src.utils.io import repo_root

CONFIG = "uniformer_s.yaml"


def _cfg(name: str = CONFIG) -> dict:
    return yaml.safe_load((repo_root() / "configs" / name).read_text("utf-8"))


# --- bảng biến thể: phải khớp file trọng số, nếu không thì nạp vào là rác ------------


def test_small_khop_uniformer_small_cua_sense_x():
    """`depth`/`embed_dim`/`head_dim` phải khớp `uniformer_small()` của Sense-X.

    Lệch một con số là mọi khoá `blocks*` đổi shape ⇒ không nạp được, và `strict=False` sẽ
    **không nói gì**. Nguồn: https://huggingface.co/Sense-X/uniformer_video (`uniformer.py`).
    """
    spec = variant_spec("small")
    assert spec["depth"] == (3, 4, 8, 3)
    assert spec["embed_dim"] == (64, 128, 320, 512)
    assert spec["head_dim"] == 64


def test_base_khop_uniformer_base():
    spec = variant_spec("base")
    assert spec["depth"] == (5, 8, 20, 7)
    assert spec["embed_dim"] == (64, 128, 320, 512)


def test_variant_sai_thi_no_chu_khong_lang_le_chon_mac_dinh():
    with pytest.raises(ValueError, match="model.variant"):
        variant_spec("medium")


def test_moi_variant_co_ten_file_trong_so():
    assert set(PRETRAINED_FILENAMES) == set(UNIFORMER_VARIANTS)
    # Bản small phải là ĐÚNG file repo hạng 2 dùng; bản base là file thay thế 32x4 (bản 16x8
    # của họ chỉ có trên Google Drive) — chỗ lệch này phải cố định, không trôi.
    assert PRETRAINED_FILENAMES["small"] == "uniformer_small_k400_16x8.pth"
    assert "32x4" in PRETRAINED_FILENAMES["base"]


# --- cổng A: khoá nào thiếu, không phải bao nhiêu phần trăm --------------------------


def test_chi_patch_embed1_va_head_duoc_phep_thieu():
    """Hai tiền tố này không khớp được về hình học: 8 kênh MRI ≠ 3 kênh RGB, 7 lớp ≠ 400."""
    assert DROPPED_PREFIXES == ("patch_embed1.", "head.")
    assert (
        unexpected_missing_keys(
            [
                "patch_embed1.proj.weight",
                "patch_embed1.proj.bias",
                "patch_embed1.norm.weight",
                "head.weight",
                "head.bias",
            ]
        )
        == []
    )


def test_khoa_thieu_ngoai_hai_tien_to_bi_bat():
    """Đây LÀ cổng. E8 lọt vì kiểm bằng tỉ lệ: 85% khớp mà vẫn sai kiến trúc."""
    bad = unexpected_missing_keys(
        ["patch_embed1.proj.weight", "head.weight", "blocks3.0.attn.qkv.weight", "norm.weight"]
    )
    assert bad == ["blocks3.0.attn.qkv.weight", "norm.weight"]


def test_cong_la_ham_thuan_khong_can_torch():
    """Một cổng chặn không test được thì hỏng đúng lúc không ai nhìn."""
    assert not any(
        p.annotation is inspect.Parameter.empty
        for p in inspect.signature(unexpected_missing_keys).parameters.values()
    )


# --- bóc checkpoint -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "cho_doi"),
    [
        ({"a": 1}, {"a": 1}),
        ({"model_state": {"b": 2}}, {"b": 2}),
        ({"state_dict": {"c": 3}}, {"c": 3}),
        ({"model": {"d": 4}}, {"d": 4}),
        ({"module.e": 5}, {"e": 5}),
        ({"model_state": {"module.f": 6}}, {"f": 6}),
    ],
)
def test_strip_state_dict_boc_moi_kieu_boc(raw: dict, cho_doi: dict):
    """Code của repo hạng 2 giả định checkpoint luôn phẳng. Giả định đó đúng với MỘT file và
    hỏng lặng lẽ với file khác — tỉ lệ khớp về 0 mà `strict=False` không nói gì."""
    assert strip_state_dict(raw) == cho_doi


def test_strip_state_dict_tu_choi_thu_khong_phai_dict():
    with pytest.raises(TypeError):
        strip_state_dict([1, 2, 3])  # type: ignore[arg-type]


def test_boc_wrapper_chua_thu_khong_phai_dict_thi_coi_nhu_phang():
    """``{"state_dict": [...]}`` không bóc được, nên coi tầng ngoài là state_dict phẳng.

    Không nguy hiểm: khoá ``state_dict`` không có trong model nên nó bị lọc hết ở
    `load_kinetics_weights`, và **cổng A bắt được** vì lúc đó mọi khoá đều thiếu.
    """
    assert strip_state_dict({"state_dict": [1, 2, 3]}) == {"state_dict": [1, 2, 3]}


# --- cổng B: hình học, tính được ở local ----------------------------------------------


def test_hinh_hoc_khop_tinh_tay():
    """14×112×112 với stride (1,2,2) — không hạ mẫu trục lát."""
    assert stage_token_counts((14, 112, 112), (1, 2, 2)) == [
        (14, 56, 56),
        (14, 28, 28),
        (14, 14, 14),
        (14, 7, 7),
    ]


def test_stage3_dat_hon_ban_pretrained_gap_1_75_lan():
    """Con số làm nên cả mục ngân sách. `SABlock` là attention TOÀN CỤC nên 1.75× token là
    ~3× chi phí. Nếu ai sửa mặc định làm nó đổi, test này phải nổ."""
    ta = stage_token_counts((14, 112, 112), (1, 2, 2))[2]
    pretrained = stage_token_counts((16, 224, 224), (2, 4, 4))[2]
    n_ta = ta[0] * ta[1] * ta[2]
    n_pre = pretrained[0] * pretrained[1] * pretrained[2]
    assert (n_ta, n_pre) == (2744, 1568)
    assert n_ta / n_pre == pytest.approx(1.75)


def test_stride_2_2_2_la_duong_thoat_va_re_hon_ca_ban_pretrained():
    """Khoá thoát của cổng C: nếu s/epoch quá cao thì hạ nửa số lát."""
    re = stage_token_counts((14, 112, 112), (2, 2, 2))[2]
    assert re[0] * re[1] * re[2] == 1372  # < 1568 của bản pretrained
    assert count_flops_proxy((14, 112, 112), (2, 2, 2)) < count_flops_proxy(
        (14, 112, 112), (1, 2, 2)
    )


def test_config_dung_2_2_2_va_day_la_CHO_LECH_CO_Y():
    """Cổng C đo thật trên T4: `[1,2,2]` cho **78 s/epoch ⇒ 6.50 h/fold**, tức 5 fold =
    32.5h, **vượt quota 30h/tuần**. Một fold 6.5h vì thế không bao giờ xác nhận được.

    `[2,2,2]` hạ lát 14→7 ⇒ stage 3 còn 1372 token (¼ chi phí attention).

    Test này khoá lại rằng đây là **lựa chọn có ý thức, lệch khỏi repo hạng 2** — ai đổi về
    `[1,2,2]` thì phải sửa test và do đó phải đọc lý do. Và nó có lập luận khoa học thật:
    bản pretrained có T=8 sau `patch_embed1`, nên 7 gần cấu trúc đã học hơn 14 của họ.
    """
    assert _cfg()["model"]["patch_embed1_stride"] == [2, 2, 2]


# --- config: những chỗ sai sẽ chỉ lộ ra giữa một session Kaggle ------------------------


def test_config_dung_cache_cghnet_va_hinh_hoc_khop_cache_do():
    """`crop_size` phải bằng `target_size` của chính cache mà config trỏ tới.

    Đây là test đáng giá nhất file này. Lệch hai con số đó thì `RandomCrop3D` nổ giữa epoch
    đầu, sau khi đã mount cache và tải trọng số — và thông báo lỗi không nói gì về nguyên nhân.
    """
    cfg = _cfg()
    pre = _cfg("preprocess_cghnet.yaml")
    assert cfg["cache_dir"] == pre["cache_dir"], "config không dùng cache CGHNet"
    assert cfg["data"]["crop_size"] == pre["target_size"] == [112, 112, 14]
    # Lưới cache = target_size + 2*lề. Đúng `--img_size 16 128 128` của repo hạng 2.
    luoi = [t + 2 * m for t, m in zip(pre["target_size"], pre["crop_margin_voxels"], strict=True)]
    assert luoi == [128, 128, 16]


def test_config_giu_dung_cac_khoa_cua_repo_hang_2():
    cfg = _cfg()
    assert cfg["model"]["variant"] == "small"
    assert cfg["model"]["drop_path_rate"] == 0.1
    assert cfg["data"]["batch_size"] == 4
    assert cfg["train"]["accum_steps"] == 1
    assert cfg["train"]["lr"] == 0.0001
    assert cfg["train"]["warmup_epochs"] == 5
    assert cfg["train"]["epochs"] == 300
    # `train.sh` không truyền --weight-decay ⇒ mặc định timm 0.05, KHÔNG phải 1e-5 của CGHNet.
    assert cfg["train"]["weight_decay"] == 0.05


def test_config_bat_ca_hai_lop_can_bang_va_dung_la_co_y():
    """`--cb_loss` + `--sampling sqrt` = hai lớp cân bằng cùng lúc.

    Đi ngược chẩn đoán §1 của dự án (ICC dự đoán thừa 1.26×, áp-xe 1.31× trên E4). Test này
    tồn tại để **khoá lại rằng đó là lựa chọn có ý thức**, không phải sơ suất: ai tắt một
    trong hai thì phải sửa test và do đó phải đọc lý do.
    """
    cfg = _cfg()
    assert cfg["loss"]["class_weights"] == "effective_number"
    assert cfg["loss"]["beta"] == 0.9999
    assert cfg["data"]["sampling"] == "sqrt"


def test_config_label_smoothing_0_1_va_focal():
    cfg = _cfg()
    assert cfg["loss"]["name"] == "focal"
    assert cfg["loss"]["label_smoothing"] == 0.1  # `--smoothing 0.1`
    assert cfg["loss"]["deep_supervision"] is False  # một đầu ra, không như CGHNet


def test_config_tat_mixup_vi_train_py_cua_ho_khong_noi_no():
    """`--mixup` có trong `train.sh` nhưng `train.py` KHÔNG có nhánh mixup nào trong vòng
    train. Bật nó là thêm một biến họ không thật sự dùng."""
    assert _cfg()["data"]["mixup_alpha"] == 0.0


def test_config_bat_buoc_rotate_mode_nearest():
    """Lề chỉ 8 voxel trong mặt phẳng mà xoay 10° làm hỏng góc tới ~12 voxel. E12 đo được:
    `constant` để lọt 517 voxel bị lấp 0 ở offset biên, `nearest` cho 0 (WORKLOG S-111)."""
    aug = _cfg()["data"]["augment"]
    assert aug["rotate_mode"] == "nearest"
    assert aug["rotate_prob"] == 1.0  # `rotate()` của họ áp cho MỌI mẫu
    assert aug["translate_voxels"] == [0, 0, 0]  # RandomCrop3D đã lo, bật cả hai sẽ raise


def test_config_xac_suat_ba_augment_loc_khop_cay_quyet_dinh_cua_ho():
    """seed>0.9 edge · >0.8 emboss · >0.4 filter ⇒ 10% / 10% / 40%, và 40% không gì."""
    aug = _cfg()["data"]["augment"]
    assert (aug["edge_prob"], aug["emboss_prob"], aug["filter_prob"]) == (0.10, 0.10, 0.40)
    assert (aug["blur_prob"], aug["sharpen_prob"], aug["unsharp_prob"]) == (0.20, 0.20, 0.10)
    assert aug["filter_spatial_only"] is False  # false = trung thực với họ


def test_config_nga_ra_neu_thieu_trong_so():
    """Một run "pretrained" lặng lẽ chạy from scratch là ĐÚNG cái lỗi mà thí nghiệm này tồn
    tại để tránh — cả giá trị của nó nằm ở chỗ có trọng số Kinetics hay không."""
    cfg = _cfg()
    assert cfg["model"]["require_pretrained"] is True
    assert not cfg["model"]["pretrained_path"], "phải truyền qua LLDMMRI_PRETRAINED_PATH"


def test_output_dir_rieng():
    others = {
        _cfg(n)["output_dir"]
        for n in ("baseline_3dpatch.yaml", "cghnet.yaml", "e14_mixup.yaml", "cghnet_mixup.yaml")
    }
    assert _cfg()["output_dir"] not in others


# --- hành vi thật, cần torch -----------------------------------------------------------


def test_forward_ra_dung_so_lop():
    torch = pytest.importorskip("torch", reason="cần torch")
    model = build_uniformer3d(variant="small", patch_embed1_stride=(2, 2, 2), drop_path_rate=0.0)
    model.eval()
    with torch.no_grad():
        out = model(torch.zeros(2, 8, 112, 112, 14))
    assert tuple(out.shape) == (2, 7)


def test_forward_hoan_vi_truc_nen_cache_XYZ_vao_duoc():
    """Cache là ``[8, X, Y, Z]`` còn model video mong ``[C, D, H, W]`` với D là trục lát.
    `forward` hoán vị bên trong; nếu ai bỏ phép hoán vị đó thì stride sẽ áp nhầm trục và
    hình học sai mà **không có gì báo** — đúng chế độ hỏng của E2."""
    torch = pytest.importorskip("torch", reason="cần torch")
    model = build_uniformer3d(variant="small", patch_embed1_stride=(2, 2, 2), drop_path_rate=0.0)
    model.eval()
    with torch.no_grad():
        # X và Y bằng nhau (112) nhưng Z khác hẳn (14). Nếu hoán vị sai, conv sẽ nhận
        # 112 lát và 14 in-plane -> patch_embed4 không còn đủ chiều và nó sẽ nổ.
        out = model(torch.zeros(1, 8, 112, 112, 14))
    assert tuple(out.shape) == (1, 7)


def test_head_dropout_0_thi_khong_co_lop_dropout_nao():
    """Mặc định trung thực với họ là 0.0, và hệ quả là **MC-dropout vô nghĩa** trên model
    này: notebook 08 sẽ trả K lượt giống hệt nhau mà không nổ. Neo lại để ai định chạy
    MC-dropout phải đọc dòng này trước."""
    pytest.importorskip("torch", reason="cần torch")
    from torch import nn

    khong = build_uniformer3d(variant="small", head_dropout=0.0, drop_rate=0.0)
    assert all(not isinstance(m, nn.Dropout) or m.p == 0 for m in khong.modules())

    co = build_uniformer3d(variant="small", head_dropout=0.2, drop_rate=0.0)
    assert any(isinstance(m, nn.Dropout) and m.p > 0 for m in co.modules())


def test_khong_co_trong_so_ma_require_pretrained_thi_no():
    pytest.importorskip("torch", reason="cần torch")
    with pytest.raises(FileNotFoundError, match="Kinetics"):
        build_uniformer3d(variant="small", pretrained_path=None, require_pretrained=True)


def test_khong_co_trong_so_va_khong_require_thi_van_dung_duoc():
    """Test và cổng B của notebook phải dựng được model mà không cần 100 MB trọng số."""
    pytest.importorskip("torch", reason="cần torch")
    assert build_uniformer3d(variant="small", require_pretrained=False) is not None


def test_nap_trong_so_lech_kien_truc_thi_no_chu_khong_im_lang():
    """Cổng A ở mức hành vi: một checkpoint thiếu `blocks3` phải làm `load` NỔ."""
    torch = pytest.importorskip("torch", reason="cần torch")
    import tempfile
    from pathlib import Path

    from src.models.uniformer3d import load_kinetics_weights

    model = build_uniformer3d(variant="small", require_pretrained=False)
    # Giữ đúng những khoá được phép thiếu, bỏ hẳn blocks3 -> phải bị bắt.
    gia = {k: v for k, v in model.state_dict().items() if not k.startswith("blocks3.")}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "gia.pth"
        torch.save(gia, path)
        with pytest.raises(RuntimeError, match="thiếu ngoài"):
            load_kinetics_weights(model, path)


def test_nap_trong_so_du_thi_chay_va_bao_cao_dung():
    torch = pytest.importorskip("torch", reason="cần torch")
    import tempfile
    from pathlib import Path

    from src.models.uniformer3d import load_kinetics_weights

    model = build_uniformer3d(variant="small", require_pretrained=False)
    day_du = dict(model.state_dict())
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "day_du.pth"
        torch.save(day_du, path)
        bao_cao = load_kinetics_weights(model, path)
    # patch_embed1 và head bị bỏ đi trước khi nạp, nên chúng phải nằm ở "missing".
    assert all(k.startswith(DROPPED_PREFIXES) for k in bao_cao["missing"])
    assert bao_cao["missing"], "phải có khoá patch_embed1/head trong danh sách thiếu"
    assert bao_cao["loaded"], "không nạp được khoá nào"
