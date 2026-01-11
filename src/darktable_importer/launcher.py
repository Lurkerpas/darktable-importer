from __future__ import annotations

import atexit
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping, Sequence


class DarktableLauncher:

    def __init__(
        self,
        darktable_binary: str = "darktable",
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.darktable_binary = darktable_binary
        self._env = {**os.environ, **env} if env else None
        self._temp_scripts: set[Path] = set()
        atexit.register(self._cleanup_all_scripts)

    def launch(
        self,
        library_path: str | Path,
        image_paths: Sequence[str | Path],
    ) -> subprocess.Popen[bytes]:
        if not image_paths:
            raise ValueError("image_paths must contain at least one entry")

        lib_path = self._normalize_path(library_path)

        normalized_images = [self._normalize_path(path) for path in image_paths]
        script_path = self._create_lua_import_script(normalized_images)

        command = self._build_command(lib_path, script_path, normalized_images)

        try:
            process = subprocess.Popen(command, env=self._env)
        except Exception:
            self._safe_remove_script(script_path)
            raise

        return process

    def _build_command(
        self,
        lib_path: Path,
        script_path: Path,
        image_paths: Sequence[Path],
    ) -> list[str]:
        command = [
            self.darktable_binary,
            "--library",
            str(lib_path),
            "--luacmd",
            f"dofile({json.dumps(str(script_path))})",
        ]
        command.extend(str(path) for path in image_paths)
        return command

    def _create_lua_import_script(self, image_paths: Sequence[Path]) -> Path:
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as handle:
            handle.write(self._create_lua_import_script_source(image_paths))
            script_path = Path(handle.name)
        self._temp_scripts.add(script_path)
        return script_path

    def _create_lua_import_script_source(self, image_paths: Sequence[Path]) -> str:
        serialized = ",\n".join(f"    {json.dumps(str(path))}" for path in image_paths)
        return "\n".join(
            [
                "local dt = require \"darktable\"",
                "local images = {",
                serialized,
                "}",
                "",
                "for _, image in ipairs(images) do",
                "    dt.database.import(image)",
                "end",
                "",
            ]
        )

    def _cleanup_all_scripts(self) -> None:
        for script in list(self._temp_scripts):
            self._safe_remove_script(script)

    def _safe_remove_script(self, script_path: Path) -> None:
        try:
            script_path.unlink(missing_ok=True)
        except AttributeError:
            try:
                script_path.unlink()
            except FileNotFoundError:
                pass
        self._temp_scripts.discard(script_path)

    @staticmethod
    def _normalize_path(candidate: str | Path) -> Path:
        return Path(candidate).expanduser().resolve()
