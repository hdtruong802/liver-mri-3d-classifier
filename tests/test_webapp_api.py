"""API và cơ chế provenance.

Nhóm test quan trọng nhất ở đây là nhóm `provenance`: nó giữ lời hứa trung tâm của
`PRODUCT.md` — số giả lập không bao giờ được ra khỏi backend mà không mang nhãn.
"""

from __future__ import annotations

import numpy as np
import pytest
from src.data.taxonomy import CLASS_NAMES, MALIGNANT_INDICES, NUM_CLASSES

fastapi = pytest.importorskip(
    "fastapi", reason="lớp serve chưa cài; xem webapp/backend/requirements.txt"
)
pytest.importorskip("nibabel", reason="lớp serve chưa cài")
pytest.importorskip("PIL", reason="lớp serve chưa cài")

from fastapi.testclient import TestClient  # noqa: E402
from webapp.backend import demo_cases, inference  # noqa: E402
from webapp.backend.config import DEFAULT_DEFER_THRESHOLD, RUO_NOTICE  # noqa: E402
from webapp.backend.main import app  # noqa: E402
from webapp.backend.phases import PHASES  # noqa: E402
from webapp.backend.schemas import ProvenanceSource  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# --------------------------------------------------------------------------- meta


def test_meta_exposes_seven_project_classes(client: TestClient) -> None:
    """Bảy lớp, đúng taxonomy dự án.

    Bản bolt khai 6 lớp kèm một lớp "gan khoẻ mạnh" và thiếu ICC lẫn áp-xe. Test này
    tồn tại để lỗi đó không quay lại qua bất kỳ đường nào.
    """
    payload = client.get("/api/meta").json()
    names = [c["name"] for c in payload["classes"]]
    assert len(names) == NUM_CLASSES == 7
    assert names == [CLASS_NAMES[i] for i in range(NUM_CLASSES)]
    assert not any("healthy" in n.lower() or "normal" in n.lower() for n in names)
    assert "Intrahepatic_cholangiocarcinoma" in names  # ICC
    assert "Hepatic_abscess" in names  # áp-xe


def test_meta_marks_exactly_three_malignant_classes(client: TestClient) -> None:
    payload = client.get("/api/meta").json()
    malignant = [c["index"] for c in payload["classes"] if c["malignant"]]
    assert set(malignant) == set(MALIGNANT_INDICES)
    assert len(malignant) == 3


def test_meta_carries_ruo_notice(client: TestClient) -> None:
    payload = client.get("/api/meta").json()
    assert payload["ruo_notice"] == RUO_NOTICE
    assert "Research Use Only" in payload["ruo_notice"]


def test_meta_lists_eight_phases(client: TestClient) -> None:
    payload = client.get("/api/meta").json()
    assert [p["file_token"] for p in payload["phases"]] == [p.file_token for p in PHASES]


# --------------------------------------------------------------------- provenance


def test_every_prediction_carries_provenance(client: TestClient) -> None:
    """Không có phản hồi suy luận nào được ra khỏi backend mà thiếu `provenance`."""
    response = client.post(f"/api/cases/{demo_cases.DEMO_CASES[0].case_id}/predict")
    assert response.status_code == 200
    body = response.json()
    assert "provenance" in body
    assert body["provenance"]["source"] in {s.value for s in ProvenanceSource}
    assert body["provenance"]["note"].strip()


def test_simulated_result_declares_itself_simulated() -> None:
    result = inference.simulate_result("bất kỳ ca nào")
    assert result.provenance.source is ProvenanceSource.SIMULATED
    assert result.provenance.model_version is None, "không được bịa chuỗi phiên bản model"
    assert "chưa có model" in result.provenance.note


def test_simulated_result_is_deterministic() -> None:
    """Cùng ca phải cho cùng màn hình mỗi lần mở.

    Số nhảy giữa hai lần tải sẽ khiến người xem tưởng model không ổn định.
    """
    first = inference.simulate_result("MR-391135_1")
    second = inference.simulate_result("MR-391135_1")
    assert first.model_dump() == second.model_dump()
    assert inference.simulate_result("một ca khác").probs != first.probs


def test_no_model_loaded_yet() -> None:
    """Chốt chặn: chưa có checkpoint nào ở W3. W5 mới nạp."""
    assert inference.model_is_loaded() is False


# ------------------------------------------------------------------ kết quả suy luận


def test_probs_cover_seven_classes_and_sum_to_one(client: TestClient) -> None:
    body = client.post(f"/api/cases/{demo_cases.DEMO_CASES[0].case_id}/predict").json()
    probs = body["probs"]
    assert len(probs) == 7
    assert [p["class_name"] for p in probs] == [CLASS_NAMES[i] for i in range(7)]
    assert sum(p["probability"] for p in probs) == pytest.approx(1.0, abs=1e-4)


def test_malignant_prob_is_sum_of_malignant_classes(client: TestClient) -> None:
    body = client.post(f"/api/cases/{demo_cases.DEMO_CASES[0].case_id}/predict").json()
    expected = sum(p["probability"] for p in body["probs"] if p["class_index"] in MALIGNANT_INDICES)
    assert body["malignant_prob"] == pytest.approx(expected, abs=1e-6)


def test_pred_class_is_argmax(client: TestClient) -> None:
    body = client.post(f"/api/cases/{demo_cases.DEMO_CASES[0].case_id}/predict").json()
    leader = max(body["probs"], key=lambda p: p["probability"])
    assert body["pred_class_index"] == leader["class_index"]
    assert body["confidence"] == pytest.approx(leader["probability"], abs=1e-6)


def test_uncertainty_chi_bao_dai_luong_do_duoc(client: TestClient) -> None:
    """Không bịa đại lượng chưa đo. Bản bolt hiển thị cả epistemic lẫn aleatoric với
    thanh phần trăm riêng; ta chỉ có `epistemic` (đo bằng MC-dropout) và `entropy`.

    Đổi so với trước: dự án GIỜ có phân rã epistemic (`src/eval/selective.py`), nên
    trường đó hợp lệ. `aleatoric` vẫn không được báo vì không dùng tới ở đâu cả.
    """
    body = client.post(f"/api/cases/{demo_cases.DEMO_CASES[0].case_id}/predict").json()
    assert set(body["uncertainty"]) == {"entropy", "epistemic", "ensemble_std"}
    assert "aleatoric" not in body["uncertainty"]
    # `epistemic` và `ensemble_std` là hai đại lượng khác nhau; không được điền lẫn.
    assert body["uncertainty"]["ensemble_std"] is None, "chưa chạy deep ensemble thật"


def test_entropy_matches_distribution() -> None:
    uniform = np.full(NUM_CLASSES, 1.0 / NUM_CLASSES)
    assert inference.shannon_entropy(uniform) == pytest.approx(float(np.log(NUM_CLASSES)))

    certain = np.zeros(NUM_CLASSES)
    certain[0] = 1.0
    assert inference.shannon_entropy(certain) == pytest.approx(0.0, abs=1e-9)


def test_assemble_result_rejects_non_normalised_probs() -> None:
    with pytest.raises(ValueError, match="tổng bằng 1"):
        inference.assemble_result(
            case_id="x",
            probs=np.full(NUM_CLASSES, 0.5),
            provenance=inference.simulate_result("x").provenance,
        )


# -------------------------------------------------------------------------- defer


@pytest.mark.parametrize(
    ("leader_prob", "threshold", "expect_defer"),
    [(0.90, 0.55, False), (0.40, 0.55, True), (0.55, 0.55, False), (0.5499, 0.55, True)],
)
def test_defer_fires_below_threshold(
    leader_prob: float, threshold: float, expect_defer: bool
) -> None:
    rest = (1.0 - leader_prob) / (NUM_CLASSES - 1)
    probs = np.full(NUM_CLASSES, rest)
    probs[0] = leader_prob
    result = inference.assemble_result(
        case_id="x",
        probs=probs,
        provenance=inference.simulate_result("x").provenance,
        defer_threshold=threshold,
    )
    assert result.defer is expect_defer
    assert result.defer_threshold == threshold


def test_default_defer_threshold_is_exposed(client: TestClient) -> None:
    """Frontend phải vẽ được ngưỡng, không chỉ kết quả so ngưỡng."""
    assert client.get("/api/meta").json()["default_defer_threshold"] == DEFAULT_DEFER_THRESHOLD


def test_heatmap_empty_until_gradcam_exists(client: TestClient) -> None:
    body = client.post(f"/api/cases/{demo_cases.DEMO_CASES[0].case_id}/predict").json()
    assert body["heatmap_slices"] == [], "Grad-CAM thuộc W5; rỗng ⇒ frontend vẽ vùng chưa khảo sát"


# ------------------------------------------------------------------------- upload


def _upload_files(tokens: list[str]) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("files", (f"MR-1_1_{t}_0000.nii", b"x", "application/octet-stream")) for t in tokens]


def test_upload_accepts_eight_phases_any_order(client: TestClient) -> None:
    tokens = [p.file_token for p in PHASES][::-1]
    response = client.post("/api/predict", files=_upload_files(tokens))
    assert response.status_code == 200
    assert response.json()["provenance"]["source"] == "simulated"


def test_upload_rejects_missing_phase(client: TestClient) -> None:
    tokens = [p.file_token for p in PHASES][:-1]
    response = client.post("/api/predict", files=_upload_files(tokens))
    assert response.status_code == 422
    assert "thiếu" in response.json()["detail"]


def test_upload_rejects_unknown_phase(client: TestClient) -> None:
    tokens = [p.file_token for p in PHASES][:-1] + ["ADC"]
    response = client.post("/api/predict", files=_upload_files(tokens))
    assert response.status_code == 422


# --------------------------------------------------------------------------- ca demo


def test_cases_endpoint_reports_availability(client: TestClient) -> None:
    """`data/` bị gitignore nên máy khác không có dữ liệu. App phải xuống thang tử tế."""
    cases = client.get("/api/cases").json()
    assert len(cases) >= 1
    assert cases[0]["case_id"] == demo_cases.DEMO_CASES[0].case_id
    assert isinstance(cases[0]["available"], bool)


def test_unknown_case_is_404(client: TestClient) -> None:
    assert client.get("/api/cases/không-có-ca-này").status_code == 404
    assert client.post("/api/cases/không-có-ca-này/predict").status_code == 404


def test_health(client: TestClient) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is False


# --- endpoint mask ----------------------------------------------------------


def _case_voi_mask() -> tuple[str, str] | None:
    """(case_id, file_token) đầu tiên có mask trên máy này, hoặc None."""
    for case in demo_cases.DEMO_CASES:
        if not demo_cases.case_is_available(case):
            continue
        for volume in demo_cases.get_case_detail(case.case_id).volumes:
            if volume.has_mask:
                return case.case_id, volume.file_token
    return None


def test_xin_mask_cho_ca_khong_co_thi_404_chu_khong_tra_anh_tran(client: TestClient) -> None:
    """Im lặng trả ảnh trần sẽ bị đọc thành 'không tìm thấy tổn thương nào'."""
    case = demo_cases.DEMO_CASES[0]
    response = client.get(
        f"/api/cases/{case.case_id}/slice",
        params={"phase": "KHONG-TON-TAI", "z": 0, "mask": "true"},
    )
    assert response.status_code == 404


def test_mask_tra_ve_PNG_khac_ban_khong_mask(client: TestClient) -> None:
    found = _case_voi_mask()
    if found is None:
        pytest.skip("máy này không có ca nào kèm mask")
    case_id, token = found

    tran = client.get(f"/api/cases/{case_id}/slice", params={"phase": token, "z": 20})
    phu = client.get(
        f"/api/cases/{case_id}/slice", params={"phase": token, "z": 20, "mask": "true"}
    )
    assert tran.status_code == 200 and phu.status_code == 200
    assert phu.headers["content-type"] == "image/png"
    assert tran.content != phu.content


def test_mask_mac_dinh_TAT(client: TestClient) -> None:
    """Không truyền `mask` thì phải ra ảnh trần — mặc định là không diễn giải thêm."""
    found = _case_voi_mask()
    if found is None:
        pytest.skip("máy này không có ca nào kèm mask")
    case_id, token = found
    a = client.get(f"/api/cases/{case_id}/slice", params={"phase": token, "z": 20})
    b = client.get(f"/api/cases/{case_id}/slice", params={"phase": token, "z": 20, "mask": "false"})
    assert a.content == b.content
