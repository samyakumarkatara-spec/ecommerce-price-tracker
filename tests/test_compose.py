from pathlib import Path


def test_compose_has_required_services():
    compose = Path("docker-compose.yml").read_text()

    for service in ("postgres:", "minio:", "airflow:", "dashboard:"):
        assert service in compose


def test_compose_does_not_contain_hardcoded_credentials():
    compose = Path("docker-compose.yml").read_text()

    assert "POSTGRES_PASSWORD: airflow" not in compose
    assert "MINIO_ROOT_PASSWORD: password123" not in compose
    assert "${POSTGRES_PASSWORD:-airflow}" in compose
    assert "${MINIO_ROOT_PASSWORD:-password123}" in compose
