import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["RWTRANSLATE_HOME"] = tempfile.mkdtemp()

from rwtranslate import updater  # noqa: E402

NEW_EXE = b"NEW-EXE-BYTES" * 100
HASH_EXE = hashlib.sha256(NEW_EXE).hexdigest()


def make_mod_zip(extra=None):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("AutoTranslate/About/About.xml", "<ModMetaData><packageId>unknown1210.autotranslate</packageId></ModMetaData>")
        z.writestr("AutoTranslate/1.6/Assemblies/RimWorldAutoTranslate.dll", b"DLL-NEW")
        for name, data in (extra or {}).items():
            z.writestr(name, data)
    return b.getvalue()


MOD_ZIP = make_mod_zip()


def release_json(tag="v9.0", with_hash=True, exe_hash=HASH_EXE):
    notes = f"- Adicionado: algo\n\n### Como instalar\nSHA-256:\n```\n"
    if with_hash:
        notes += f"{exe_hash}  helper-exe/UniversalTranslate-Helper.exe\n{hashlib.sha256(MOD_ZIP).hexdigest()}  mod-zip/UniversalTranslate-Mod.zip\n"
    notes += "```\n"
    return {"tag_name": tag, "body": notes, "assets": [
        {"name": "UniversalTranslate-Helper.exe", "browser_download_url": "https://github.com/x/y/releases/download/v/h.exe", "url": "https://api.github.com/a/1"},
        {"name": "UniversalTranslate-Mod.zip", "browser_download_url": "https://github.com/x/y/releases/download/v/m.zip", "url": "https://api.github.com/a/2"}]}


def fake_fetcher(release, exe_bytes=NEW_EXE, mod_bytes=MOD_ZIP):
    def f(url, accept=None, progress=None):
        if url == updater.API_LATEST:
            return json.dumps(release).encode()
        if url.endswith("h.exe") or url.endswith("/a/1"):
            return exe_bytes
        if url.endswith("m.zip") or url.endswith("/a/2"):
            return mod_bytes
        raise AssertionError("unexpected url " + url)
    return f


class Versions(unittest.TestCase):
    def test_parse_and_compare(self):
        self.assertEqual(updater.parse_version("v0.5"), (0, 5, 0))
        self.assertEqual(updater.parse_version("0.10.2"), (0, 10, 2))
        self.assertGreater(updater.parse_version("v0.10"), updater.parse_version("v0.9"))   # numeric, not text, order
        self.assertEqual(updater.parse_version("garbage"), (0, 0, 0))


class Check(unittest.TestCase):
    def test_newer_available_with_hashes(self):
        c = updater.check(fake_fetcher(release_json("v9.0")))
        self.assertTrue(c.available and c.latest == "v9.0" and not c.error)
        self.assertEqual(c.release.hashes["UniversalTranslate-Helper.exe"], HASH_EXE)

    def test_up_to_date(self):
        c = updater.check(fake_fetcher(release_json("v0.0")))
        self.assertFalse(c.available or c.error)

    def test_errors_are_returned_not_raised(self):
        def boom(url, accept=None, progress=None):
            raise updater.UpdateError("sem internet")
        c = updater.check(boom)
        self.assertEqual((c.available, c.error), (False, "sem internet"))
        c = updater.check(lambda *a, **k: b"not json")
        self.assertTrue(c.error)

    def test_only_github_https_hosts(self):
        for bad in ("http://github.com/x", "https://evil.example/x", "https://github.com.evil.example/x", "ftp://github.com/x"):
            with self.assertRaises(updater.UpdateError):
                updater.fetch(bad)
        self.assertTrue(updater._host_ok("https://objects.githubusercontent.com/z"))
        self.assertTrue(updater._host_ok("https://api.github.com/repos/a/b"))


class Apply(unittest.TestCase):
    def test_helper_swap_keeps_old_and_replaces(self):
        d = Path(tempfile.mkdtemp())
        exe = d / "UniversalTranslate-Helper.exe"
        exe.write_bytes(b"OLD")
        rel = updater.latest_release(fake_fetcher(release_json()))
        updater.update_helper(rel, fake_fetcher(release_json()), exe_path=exe)
        self.assertEqual(exe.read_bytes(), NEW_EXE)
        self.assertEqual((d / (exe.name + ".old")).read_bytes(), b"OLD")
        self.assertFalse((d / (exe.name + ".new")).exists())

    def test_falls_back_to_public_link_when_api_address_fails(self):
        calls = []

        def f(url, accept=None, progress=None):
            calls.append(url)
            if url.endswith("/a/1"):
                raise updater.UpdateError("404")
            return fake_fetcher(release_json())(url, accept, progress)
        rel = updater.latest_release(fake_fetcher(release_json()))
        self.assertEqual(updater.download_verified(rel, updater.HELPER_ASSET, f), NEW_EXE)
        self.assertEqual([c.rsplit("/", 1)[-1] for c in calls], ["1", "h.exe"])

    def test_redirects_leave_github_and_drop_the_token(self):
        import urllib.request as ur
        h = updater._SafeRedirect()
        req = ur.Request("https://api.github.com/a/1", headers={"Authorization": "Bearer SECRET"})
        new = h.redirect_request(req, None, 302, "Found", {}, "https://objects.githubusercontent.com/signed?x=1")
        self.assertFalse(new.has_header("Authorization"))                          # not forwarded to the storage host
        with self.assertRaises(updater.UpdateError):
            h.redirect_request(req, None, 302, "Found", {}, "https://evil.example/steal")

    def test_hash_mismatch_rejected_and_exe_untouched(self):
        d = Path(tempfile.mkdtemp())
        exe = d / "h.exe"
        exe.write_bytes(b"OLD")
        f = fake_fetcher(release_json(), exe_bytes=b"TAMPERED")
        rel = updater.latest_release(f)
        with self.assertRaises(updater.UpdateError) as cm:
            updater.update_helper(rel, f, exe_path=exe)
        self.assertIn("não confere", str(cm.exception))
        self.assertEqual(exe.read_bytes(), b"OLD")

    def test_missing_hash_is_refused(self):
        f = fake_fetcher(release_json(with_hash=False))
        rel = updater.latest_release(f)
        with self.assertRaises(updater.UpdateError) as cm:
            updater.download_verified(rel, updater.HELPER_ASSET, f)
        self.assertIn("hash", str(cm.exception))

    def test_python_install_is_told_to_use_pip(self):
        rel = updater.latest_release(fake_fetcher(release_json()))
        with self.assertRaises(updater.UpdateError) as cm:
            updater.update_helper(rel, fake_fetcher(release_json()))   # not frozen, no exe_path
        self.assertIn("pip", str(cm.exception))

    def test_second_click_after_an_update_that_did_not_restart(self):
        """First click swapped the exe but the old window kept running from name.old (Windows cannot delete a running file).
        The second click must not fail with 'Access denied' on that .old: it sees the new exe is already in place."""
        from unittest import mock
        d = Path(tempfile.mkdtemp())
        exe = d / "UniversalTranslate-Helper.exe"
        exe.write_bytes(b"OLD")
        rel = updater.latest_release(fake_fetcher(release_json()))
        updater.update_helper(rel, fake_fetcher(release_json()), exe_path=exe)
        self.assertEqual(exe.read_bytes(), NEW_EXE)
        running_old = d / "UniversalTranslate-Helper.exe.old"
        self.assertEqual(running_old.read_bytes(), b"OLD")
        got = updater.update_helper(rel, fake_fetcher(release_json()), exe_path=exe)       # same version already installed
        self.assertEqual(got, exe)
        self.assertEqual(exe.read_bytes(), NEW_EXE)

    def test_old_file_that_cannot_be_deleted_does_not_block_a_later_swap(self):
        from unittest import mock
        d = Path(tempfile.mkdtemp())
        exe = d / "UniversalTranslate-Helper.exe"
        exe.write_bytes(b"V1")
        (d / "UniversalTranslate-Helper.exe.old").write_bytes(b"RUNNING")             # a running old program: deleting it is refused
        real_unlink = Path.unlink

        def refuse(self, *a, **k):
            if self.name.endswith(".exe.old"):
                raise PermissionError(5, "Access denied")
            return real_unlink(self, *a, **k)
        with mock.patch.object(Path, "unlink", refuse):
            updater._swap(exe, b"V2")
        self.assertEqual(exe.read_bytes(), b"V2")
        self.assertEqual((d / "UniversalTranslate-Helper.exe.old").read_bytes(), b"RUNNING", "the running copy is left alone")
        self.assertEqual((d / "UniversalTranslate-Helper.exe.old1").read_bytes(), b"V1", "the replaced one is set aside under a new name")

    def test_mod_extracted_over_installation(self):
        d = Path(tempfile.mkdtemp()) / "AutoTranslate"
        (d / "1.6/Assemblies").mkdir(parents=True)
        (d / "1.6/Assemblies/RimWorldAutoTranslate.dll").write_bytes(b"DLL-OLD")
        f = fake_fetcher(release_json())
        n = updater.update_mod(updater.latest_release(f), d, f)
        self.assertEqual(n, 2)
        self.assertEqual((d / "1.6/Assemblies/RimWorldAutoTranslate.dll").read_bytes(), b"DLL-NEW")
        self.assertTrue(updater._is_our_mod(d))

    def test_mod_dll_loaded_by_the_running_game_is_set_aside_not_overwritten(self):
        """Windows refuses to overwrite a DLL the game has loaded ([Errno 22]) but allows renaming it: the old one goes to .old."""
        from unittest import mock
        d = Path(tempfile.mkdtemp()) / "AutoTranslate"
        dll = d / "1.6/Assemblies/RimWorldAutoTranslate.dll"
        dll.parent.mkdir(parents=True)
        dll.write_bytes(b"DLL-OLD")
        real = Path.write_bytes

        def locked(self, data):
            if self.name == "RimWorldAutoTranslate.dll" and self.exists():
                raise OSError(22, "Invalid argument")
            return real(self, data)
        f = fake_fetcher(release_json())
        with mock.patch.object(Path, "write_bytes", locked):
            n = updater.update_mod(updater.latest_release(f), d, f)
        self.assertEqual(n, 2)
        self.assertEqual(dll.read_bytes(), b"DLL-NEW")
        self.assertEqual(dll.with_name(dll.name + ".old").read_bytes(), b"DLL-OLD", "the loaded copy is kept aside")
        updater.update_mod(updater.latest_release(f), d, f)        # next update: the leftover .old is cleaned up
        self.assertFalse(any(d.rglob("*.old")))

    def test_mod_file_that_cannot_be_written_gives_a_clear_message(self):
        from unittest import mock
        d = Path(tempfile.mkdtemp()) / "AutoTranslate"
        f = fake_fetcher(release_json())
        with mock.patch.object(Path, "write_bytes", side_effect=OSError(22, "Invalid argument")):
            with self.assertRaises(updater.UpdateError) as cm:
                updater.update_mod(updater.latest_release(f), d, f)
        self.assertIn("RimWorld", str(cm.exception))

    def test_mod_zip_with_unsafe_paths_rejected(self):
        for evil in ("AutoTranslate/../../escape.txt", "Other/x.txt", "/abs.txt"):
            z = make_mod_zip({evil: b"x"})
            rj = release_json()
            rj["body"] = rj["body"].replace(hashlib.sha256(MOD_ZIP).hexdigest(), hashlib.sha256(z).hexdigest())
            f = fake_fetcher(rj, mod_bytes=z)
            d = Path(tempfile.mkdtemp()) / "AutoTranslate"
            with self.assertRaises(updater.UpdateError):
                updater.update_mod(updater.latest_release(f), d, f)
            self.assertFalse(d.exists() and any(d.rglob("escape.txt")))

    def test_find_mod_dir_in_steam_library(self):
        lib = Path(tempfile.mkdtemp())
        mod = lib / "steamapps/common/RimWorld/Mods/AutoTranslate/About"
        mod.mkdir(parents=True)
        (mod / "About.xml").write_text("<packageId>unknown1210.autotranslate</packageId>")
        self.assertEqual(updater.find_mod_dir(extra_roots=[lib]), lib / "steamapps/common/RimWorld/Mods/AutoTranslate")
        (mod / "About.xml").write_text("<packageId>someone.else</packageId>")       # a different mod with that folder name
        self.assertIsNone(updater.find_mod_dir(extra_roots=[lib]))

    def test_save_mod_zip_when_folder_unknown(self):
        f = fake_fetcher(release_json())
        p = updater.save_mod_zip(updater.latest_release(f), f)
        self.assertTrue(p.exists() and p.read_bytes() == MOD_ZIP)


if __name__ == "__main__":
    unittest.main()
