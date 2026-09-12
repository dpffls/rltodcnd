# -*- coding: utf-8 -*-
"""
GyuminServer Forge Modpack Auto Installer
---------------------------------------------
친구 PC에서 더블클릭 한 번으로:
  1) Minecraft Forge를 설치하고
  2) 정해진 모드팩(mods)을 .minecraft/mods 폴더에 받아주는 설치 프로그램.

- 모드 목록/버전은 이 파일 안이 아니라 GitHub에 올려둔 manifest.json 에서 읽어옵니다.
  => 나중에 모드를 추가/교체해도 exe를 다시 만들 필요 없이 manifest.json만 고치면 됩니다.
- 외부 라이브러리 없이 표준 라이브러리(urllib 등)만 사용합니다. (PyInstaller로 exe 빌드가 쉬움)
"""

import os
import sys
import json
import shutil
import hashlib
import tempfile
import subprocess
import urllib.request
import urllib.error

# ============================================================
# 여기만 본인 정보로 바꾸세요
# ============================================================
GITHUB_USER = "dpffls"
GITHUB_REPO = "rltodcnd"
MANIFEST_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/manifest.json"
# ============================================================


def banner(text):
    line = "=" * 60
    print(line)
    print(f" {text}")
    print(line)


def log(msg):
    print(f"  >> {msg}")


def fail(msg):
    print(f"\n[오류] {msg}")
    input("\n엔터를 누르면 창이 닫힙니다...")
    sys.exit(1)


def get_appdata_minecraft_dir():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        fail("APPDATA 환경변수를 찾을 수 없습니다. (윈도우 전용 설치 프로그램입니다)")
    return os.path.join(appdata, ".minecraft")


def check_java():
    log("Java 설치 여부 확인 중...")
    try:
        result = subprocess.run(
            ["java", "-version"], capture_output=True, text=True, timeout=10
        )
        output = (result.stdout or "") + (result.stderr or "")
        log(f"Java 감지됨: {output.splitlines()[0] if output else '알 수 없음'}")
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def download_with_progress(url, dest_path, label):
    """urllib로 다운로드하면서 [####----] 형태 진행률을 출력한다."""
    tmp_path = dest_path + ".part"

    def _report(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 // total_size)
            bar_len = 20
            filled = bar_len * percent // 100
            bar = "#" * filled + "-" * (bar_len - filled)
            mb_down = downloaded / 1_000_000
            mb_total = total_size / 1_000_000
            print(
                f"\r  [{bar}] {percent:3d}% ({mb_down:.1f}MB/{mb_total:.1f}MB) - {label}",
                end="",
                flush=True,
            )

    try:
        urllib.request.urlretrieve(url, tmp_path, _report)
        print()  # 줄바꿈
    except Exception as e:
        print()
        fail(f"'{label}' 다운로드 실패: {e}")

    shutil.move(tmp_path, dest_path)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest():
    log("모드팩 정보(manifest.json) 불러오는 중...")
    try:
        with urllib.request.urlopen(MANIFEST_URL, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
    except urllib.error.URLError as e:
        fail(f"모드팩 정보를 불러오지 못했습니다. 인터넷 연결을 확인하세요.\n({e})")


def install_forge(manifest):
    mc_version = manifest["minecraft_version"]
    forge_version = manifest["forge_version"]
    installer_url = manifest["forge_installer_url"]
    full_version = f"{mc_version}-forge-{forge_version}"
    log(f"Forge {forge_version} (Minecraft {mc_version}) 설치 확인 중...")

    minecraft_dir = get_appdata_minecraft_dir()
    versions_dir = os.path.join(minecraft_dir, "versions")
    # 버전 폴더 이름이 Forge 빌드마다 약간 다를 수 있어 접두어로 느슨하게 확인
    already_installed = False
    if os.path.isdir(versions_dir):
        for name in os.listdir(versions_dir):
            if mc_version in name and "forge" in name.lower():
                already_installed = True
                break

    if already_installed:
        log(f"Forge {forge_version} 은(는) 이미 설치되어 있는 것으로 보입니다. 건너뜁니다.")
        return

    with tempfile.TemporaryDirectory() as tmp:
        installer_path = os.path.join(tmp, "forge-installer.jar")
        download_with_progress(installer_url, installer_path, "Forge 설치파일")

        log("Forge 설치 중 (자동, 몇 분 걸릴 수 있어요)...")
        result = subprocess.run(
            ["java", "-jar", installer_path, "--installClient"],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            fail("Forge 설치 중 문제가 발생했습니다.")
        log("Forge 설치 완료.")


def install_mods(manifest):
    minecraft_dir = get_appdata_minecraft_dir()
    mods_dir = os.path.join(minecraft_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)

    mods = manifest.get("mods", [])
    total = len(mods)
    print(f"\n[모드 다운로드] 총 {total}개")

    for i, mod in enumerate(mods, start=1):
        name = mod["name"]
        filename = mod["filename"]
        url = mod["url"]
        expected_sha = mod.get("sha256")
        dest = os.path.join(mods_dir, filename)

        prefix = f"  [{i}/{total}] {name}"

        if os.path.exists(dest):
            if not expected_sha or sha256_of(dest) == expected_sha:
                print(f"{prefix} : 이미 파일이 존재합니다.")
                continue
            else:
                log(f"{name} 파일이 변경되어 다시 받습니다.")

        download_with_progress(url, dest, name)


def main():
    banner("GyuminServer Forge Modpack Auto Installer")

    if os.name != "nt":
        fail("이 설치 프로그램은 윈도우 전용입니다.")

    if not check_java():
        fail(
            "Java(17 이상)가 설치되어 있지 않습니다.\n"
            "https://adoptium.net 에서 Java를 먼저 설치한 뒤 다시 실행해주세요."
        )

    manifest = load_manifest()

    print(f"\n모드팩: {manifest.get('modpack_name', 'Modpack')}")
    print(f"마인크래프트 버전: {manifest.get('minecraft_version')}")
    print(f"Forge 버전: {manifest.get('forge_version')}\n")

    print("[1/2] Forge 설치")
    install_forge(manifest)

    print("\n[2/2] 모드 다운로드")
    install_mods(manifest)

    print("\n" + "=" * 60)
    print(" 설치가 완료되었습니다!")
    print(" Minecraft 런처 > 설치 관리 에서 'forge-...' 프로필로 실행하세요.")
    print("=" * 60)
    input("\n엔터를 누르면 창이 닫힙니다...")


if __name__ == "__main__":
    main()
