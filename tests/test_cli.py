from contextvault.cli import main


def test_qwen_configuration_error_has_controlled_cli_exit(monkeypatch, tmp_path, capsys) -> None:
    for name in ("QWEN_API_KEY", "QWEN_BASE_URL", "QWEN_MODEL"):
        monkeypatch.delenv(name, raising=False)
    result = main([
        "ask", "What should I do?", "--provider", "qwen",
        "--database", str(tmp_path / "memory.db"),
    ])
    output = capsys.readouterr().out
    assert result == 3
    assert "PROVIDER ERROR" in output
    assert "QWEN_API_KEY" in output
    assert "QWEN_BASE_URL" in output
    assert "QWEN_MODEL" in output
