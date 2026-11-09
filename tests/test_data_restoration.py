import json
import os
import sys
import tempfile
import unittest
import zipfile

import duckdb
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))
from artifacts import source_record, verified_source, write_json
from download import fetch
from load import main


class DataRestorationTests(unittest.TestCase):
    def test_verified_inputs_require_matching_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / "data.csv"
            source.write_text("x\n1\n")
            write_json(directory / ".source.json", source_record(directory, "test", "test"))
            self.assertTrue(verified_source(directory, "test"))
            source.write_text("x\n2\n")
            self.assertFalse(verified_source(directory, "test"))
            self.assertFalse(verified_source(directory, "other"))

    def test_failed_archive_does_not_create_successful_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            archive = directory / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("../outside.csv", "bad")
            with patch("download.RAW", directory / "raw"):
                with self.assertRaisesRegex(ValueError, "bad path"):
                    fetch("test", archive.as_uri())
                self.assertFalse((directory / "raw" / "test").exists())
                self.assertFalse((directory / "raw" / "outside.csv").exists())

    def test_download_promotes_only_complete_data_and_reuses_verified_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            archive = directory / "good.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("data.csv", "x\n1\n")
            with patch("download.RAW", directory / "raw"):
                fetch("test", archive.as_uri())
                target = directory / "raw" / "test"
                self.assertTrue(verified_source(target, archive.as_uri()))
                metadata = json.loads((target / ".source.json").read_text())
                self.assertIsNotNone(metadata["retrieved_at"])
                archive.unlink()
                fetch("test", archive.as_uri())
                (target / "data.csv").write_text("corrupt")
                with self.assertRaisesRegex(ValueError, "unverified input"):
                    fetch("test", archive.as_uri())

    def test_sql_failure_preserves_previous_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            sql = directory / "sql"
            sql.mkdir()
            (sql / "01.sql").write_text("create or replace table sentinel as select 99 as value")
            (sql / "02.sql").write_text("select * from missing_required_table")
            database = directory / "casechamp.duckdb"
            with duckdb.connect(str(database)) as con:
                con.execute("create table sentinel as select 42 as value")
            original = Path.cwd()
            try:
                with patch("load.ROOT", directory), patch("load.DB", database), patch("load.REQUIRED", {}):
                    with self.assertRaises(duckdb.CatalogException):
                        main()
            finally:
                os.chdir(original)
            with duckdb.connect(str(database)) as con:
                self.assertEqual(con.sql("select value from sentinel").fetchone()[0], 42)


if __name__ == "__main__":
    unittest.main()
