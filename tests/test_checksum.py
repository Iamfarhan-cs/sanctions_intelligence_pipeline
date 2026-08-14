from sanctions_pipeline.acquisition.checksum import calculate_sha256


def test_calculate_sha256(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_bytes(b"hello sanctions pipeline")

    checksum = calculate_sha256(str(file_path))

    assert checksum == (
        "c206464f523376ce8c5704a4729330832eabaa8a170d1e8ed9f83814f00196d2"
    )