"""LinkedIn connections export normalization (TEST_ONLY CSV)."""

from growthos.integrations.linkedin import parse_connections_csv


def test_parse_connections_csv(tmp_path):
    csv_path = tmp_path / "connections.csv"
    csv_path.write_text(
        "First Name,Last Name,Company,Position,Connected On,Email Address\n"
        "Alex,Doe,BrandCo,Owner,15 Mar 2024,alex@brandco.example\n"
        "Sam,Smith,,Designer,,sam@example.com\n",
        encoding="utf-8",
    )
    rows = parse_connections_csv(csv_path)
    assert len(rows) == 2
    assert rows[0].full_name == "Alex Doe"
    assert rows[0].company == "BrandCo"
    assert rows[0].position == "Owner"
    assert rows[0].email == "alex@brandco.example"
    assert rows[0].connected_at is not None
    assert rows[1].company is None


def test_parse_connections_csv_handles_blank_lines(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("First Name,Last Name\n\n", encoding="utf-8")
    assert parse_connections_csv(csv_path) == []
