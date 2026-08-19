"""API và cơ chế provenance.

Nhóm test quan trọng nhất ở đây là nhóm `provenance`: nó giữ lời hứa trung tâm của
`PRODUCT.md` — số giả lập không bao giờ được ra khỏi backend mà không mang nhãn.
"""

from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

import numpy as np
import pytest
from src.data.taxonomy import CLASS_NAMES, MALIGNANT_INDICES, NUM_CLASSES

fastapi = pytest.importorskip(
    "fastapi", reason="lớp serve chưa cài; xem webapp/backend/requirements.txt"
)
nib = pytest.importorskip("nibabel", reason="lớp serve chưa cài")
pytest.importorskip("PIL", reason="lớp serve chưa cài")

from fastapi.testclient import TestClient  # noqa: E402
from webapp.backend import inference  # noqa: E402
from webapp.backend.config import DEFAULT_DEFER_THRESHOLD, RUO_NOTICE  # noqa: E402
from webapp.backend.main import app  # noqa: E402
from webapp.backend.phases import PHASES  # noqa: E402
from webapp.backend.schemas import Provenance, ProvenanceSource  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _prediction(probs: np.ndarray | None = None) -> dict[str, object]:
    """Một `PredictResult` đã serialise, dựng thuần từ vector xác suất.

    Trước S-197 các khẳng định dưới đây chạy qua endpoint ca demo, mà endpoint đó cần
    dữ liệu bệnh nhân trong `data/` (bị .gitignore) nên chúng **skip ở mọi máy**. Hợp
    đồng cần giữ là hợp đồng của payload, không phải của đường lấy dữ liệu — dựng
    thẳng từ `assemble_result` thì nó chạy thật.
    """
    if probs is None:
        probs = np.array([0.02, 0.05, 0.03, 0.10, 0.05, 0.05, 0.70])
    return inference.assemble_result(
        case_id="MR-test",
        probs=probs,
        provenance=Provenance(
            source=ProvenanceSource.LIVE, model_version="test", note="Suy luận kiểm thử"
        ),
    ).model_dump(mode="json")


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


def test_every_prediction_carries_provenance() -> None:
    """Không có phản hồi suy luận nào được ra khỏi backend mà thiếu `provenance`."""
    body = _prediction()
    assert "provenance" in body
    assert body["provenance"]["source"] in {s.value for s in ProvenanceSource}
    assert body["provenance"]["note"].strip()


def test_bao_dung_co_trong_so_hay_khong() -> None:
    """`runs/` bị .gitignore nên máy khác clone về sẽ không có trọng số. Phải trả lời
    được câu đó thay vì nổ."""
    from webapp.backend import live_inference

    assert isinstance(live_inference.is_available(), bool)


# ------------------------------------------------------------------ kết quả suy luận


def test_probs_cover_seven_classes_and_sum_to_one() -> None:
    body = _prediction()
    probs = body["probs"]
    assert len(probs) == 7
    assert [p["class_name"] for p in probs] == [CLASS_NAMES[i] for i in range(7)]
    assert sum(p["probability"] for p in probs) == pytest.approx(1.0, abs=1e-4)


def test_malignant_prob_is_sum_of_malignant_classes() -> None:
    body = _prediction()
    expected = sum(p["probability"] for p in body["probs"] if p["class_index"] in MALIGNANT_INDICES)
    assert body["malignant_prob"] == pytest.approx(expected, abs=1e-6)


def test_pred_class_is_argmax() -> None:
    body = _prediction()
    leader = max(body["probs"], key=lambda p: p["probability"])
    assert body["pred_class_index"] == leader["class_index"]
    assert body["confidence"] == pytest.approx(leader["probability"], abs=1e-6)


def test_uncertainty_chi_bao_dai_luong_do_duoc() -> None:
    """Không bịa đại lượng chưa đo. Bản bolt hiển thị cả epistemic lẫn aleatoric với
    thanh phần trăm riêng; ta chỉ có `epistemic` (đo bằng MC-dropout) và `entropy`.

    Đổi so với trước: dự án GIỜ có phân rã epistemic (`src/eval/selective.py`), nên
    trường đó hợp lệ. `aleatoric` vẫn không được báo vì không dùng tới ở đâu cả.
    """
    body = _prediction()
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
            provenance=Provenance(source=ProvenanceSource.OOF, note="prediction OOF"),
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
        provenance=Provenance(source=ProvenanceSource.OOF, note="prediction OOF"),
        defer_threshold=threshold,
    )
    assert result.defer is expect_defer
    assert result.defer_threshold == threshold


def test_default_defer_threshold_is_exposed(client: TestClient) -> None:
    """Frontend phải vẽ được ngưỡng, không chỉ kết quả so ngưỡng."""
    assert client.get("/api/meta").json()["default_defer_threshold"] == DEFAULT_DEFER_THRESHOLD


# ------------------------------------------------------------------------- upload


def _zip_upload(
    names: list[str], *, with_source_nifti: bool = False
) -> dict[str, tuple[str, bytes, str]]:
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        for index, name in enumerate(names):
            content = b"nifti-placeholder"
            if with_source_nifti and name.lower().endswith((".nii", ".nii.gz")):
                data = np.full((12, 13, 6), index + 1, dtype=np.float32)
                if "/masks/" in name:
                    data.fill(0)
                    data[4:9, 5:10, 2:4] = 1
                content = nib.Nifti1Image(data, np.eye(4)).to_bytes()
            archive.writestr(name, content)
    return {"archive": ("MR-1.zip", payload.getvalue(), "application/zip")}


def test_upload_validates_eight_phases_any_order_without_prediction(client: TestClient) -> None:
    names = [f"images/MR-1_1_{phase.file_token}_0000.nii.gz" for phase in PHASES][::-1]
    response = client.post("/api/validate-upload", files=_zip_upload(names))
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["inference_ready"] is False
    assert [phase["state"] for phase in body["phases"]] == ["ready"] * 8
    assert [phase["mask_state"] for phase in body["phases"]] == ["missing"] * 8
    assert "prediction" not in body
    assert "uncertainty" not in body


def test_upload_rejects_missing_phase(client: TestClient) -> None:
    names = [f"images/MR-1_1_{phase.file_token}_0000.nii" for phase in PHASES[:-1]]
    response = client.post("/api/validate-upload", files=_zip_upload(names))
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["phases"][-1]["state"] == "missing"


def test_upload_rejects_unknown_phase(client: TestClient) -> None:
    names = [f"images/MR-1_1_{phase.file_token}_0000.nii" for phase in PHASES[:-1]]
    names.append("images/MR-1_1_ADC.nii")
    response = client.post("/api/validate-upload", files=_zip_upload(names))
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"]


def test_upload_rejects_duplicate_phase(client: TestClient) -> None:
    names = [f"images/MR-1_1_{phase.file_token}_0000.nii" for phase in PHASES]
    names.append("images/MR-1_1_C+V_copy.nii")
    response = client.post("/api/validate-upload", files=_zip_upload(names))
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    portal_phase = next(phase for phase in body["phases"] if phase["file_token"] == "C+V")
    assert portal_phase["state"] == "duplicate"


def test_upload_rejects_zip_without_nifti(client: TestClient) -> None:
    response = client.post("/api/validate-upload", files=_zip_upload(["README.txt"]))
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert "NIfTI" in body["errors"][0]


def test_predict_upload_never_runs_without_all_masks(client: TestClient) -> None:
    names = [f"images/MR-1_1_{phase.file_token}_0000.nii" for phase in PHASES]
    response = client.post("/api/predict-upload", files=_zip_upload(names))
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["inference_ready"] is False
    assert body["prediction"] is None


def test_predict_upload_uses_complete_mri_and_mask_contract(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The route only calls inference after all 16 recognised files are present."""
    from webapp.backend import live_inference
    from webapp.backend.schemas import Provenance, ProvenanceSource

    names = [
        f"{folder}/MR-1_1_{phase.file_token}_0000.nii"
        for folder in ("images", "masks")
        for phase in PHASES
    ]
    called: dict[str, object] = {}

    monkeypatch.setattr(live_inference, "is_available", lambda: True)

    def fake_predict(archive_name, image_paths, mask_paths):
        called["archive_name"] = archive_name
        called["images"] = image_paths
        called["masks"] = mask_paths
        return inference.assemble_result(
            case_id="MR-1",
            probs=np.full(7, 1 / 7),
            provenance=Provenance(
                source=ProvenanceSource.LIVE, model_version="test", note="Suy luận kiểm thử"
            ),
            defer_available=False,
        )

    monkeypatch.setattr(live_inference, "predict_uploaded", fake_predict)
    response = client.post("/api/predict-upload", files=_zip_upload(names, with_source_nifti=True))
    assert response.status_code == 200
    body = response.json()
    assert body["inference_ready"] is True
    assert body["prediction"]["provenance"]["source"] == "live"
    assert len(called["images"]) == len(called["masks"]) == 8
    assert body["upload_view"]["volumes"][0]["shape"] == [12, 13, 6]
    assert body["upload_view"]["volumes"][0]["n_slices"] == 6
    upload_id = body["upload_view"]["upload_id"]
    plain = client.get(f"/api/uploads/{upload_id}/slice", params={"phase": "C-pre", "z": 2})
    overlay = client.get(
        f"/api/uploads/{upload_id}/slice", params={"phase": "C-pre", "z": 2, "mask": "true"}
    )
    assert plain.status_code == overlay.status_code == 200
    assert plain.headers["cache-control"] == "no-store"
    assert plain.content != overlay.content
    expired = client.get("/api/uploads/khong-co/slice", params={"phase": "C-pre", "z": 0})
    assert expired.status_code == 404


def test_health(client: TestClient) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok"


def test_khong_con_endpoint_ca_demo(client: TestClient) -> None:
    """Đường ca demo đã gỡ ở S-197 — nó cần dữ liệu bệnh nhân mà repo không mang theo.

    Chốt lại ở đây để không ai thêm lại một nửa: route sống lại mà `demo_cases` thì
    không, hoặc ngược lại, đều cho ra 500 thay vì 404.
    """
    assert client.get("/api/cases").status_code == 404
    assert client.post("/api/cases/MR-1/predict").status_code == 404
