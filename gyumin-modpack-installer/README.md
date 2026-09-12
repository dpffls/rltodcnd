# GyuminServer Forge Modpack Auto Installer

친구한테 exe 파일 하나만 보내주면, 실행 시 Minecraft Forge 1.20.1 설치 + 아래 모드 4개를
자동으로 받아주는 설치 프로그램입니다.

- Fungal Infection: Spore
- [TaCZ] Timeless and Classics Zero Guns
- Just Enough Items (JEI)
- Traveler's Backpack

---

## 1. 이 폴더를 GitHub 저장소에 올리기

1. github.com에서 새 저장소(Repository) 생성 (이름 예: `gyumin-modpack`, **Public**으로 만들어야 친구가 로그인 없이 다운로드 가능)
2. 이 폴더(`installer.py`, `manifest.json`, `.github/`, `README.md`)를 그대로 업로드/push

## 2. 모드 파일(jar) 준비해서 Release에 올리기

각 모드의 공식 페이지(Modrinth 또는 CurseForge)에서 **Forge 1.20.1용** jar 파일을
직접 다운로드하세요. (저작권 때문에 제가 대신 파일을 올려드릴 순 없어요 — 본인이 받아서
본인 저장소에 재배포하는 형태예요.)

> ⚠️ 참고: 아래 모드들은 대부분 의존 모드(dependency)가 따로 필요합니다.
> 각 모드 페이지의 "Dependencies" 항목을 꼭 확인해서 필요한 라이브러리 모드
> (예: Curios API 등)도 같이 받아서 manifest에 추가하세요.
> 안 넣으면 게임 실행 시 모드가 안 켜지거나 에러가 납니다.

저장소 페이지 → **Releases** → **Create a new release** → 태그 `v1` 생성 →
받아둔 jar 파일들을 그대로 드래그해서 업로드 → Publish.

업로드하면 각 파일의 다운로드 링크가 아래 형식으로 생깁니다:
```
https://github.com/사용자이름/저장소이름/releases/download/v1/파일이름.jar
```

## 3. manifest.json 수정

`manifest.json`을 열어서:
- `forge_version`, `forge_installer_url` : https://files.minecraftforge.net/net/minecraftforge/forge/index_1.20.1.html 에서 최신 Recommended 버전 확인 후 반영 (설치 프로그램이 실행될 때마다 이 파일을 다시 읽으므로, 나중에 버전이 바뀌면 여기만 고치면 됩니다)
- 각 모드의 `url`을 2번에서 만든 실제 Release 다운로드 링크로 교체
- (선택) `sha256`은 비워둬도 동작합니다. 채워두면 파일이 변조/손상됐을 때 다시 받습니다.

`installer.py` 맨 위 `GITHUB_USER`, `GITHUB_REPO`도 본인 계정/저장소 이름으로 바꾸세요.

수정한 뒤 GitHub에 다시 push 하세요.

## 4. exe 자동 빌드 (GitHub Actions)

`installer.py`를 push하면 `.github/workflows/build.yml`이 자동으로 Windows용 exe를 빌드합니다.

1. 저장소의 **Actions** 탭 클릭
2. "Build Installer EXE" 워크플로우가 실행 중/완료 상태로 뜸
3. 완료되면 해당 실행 결과 페이지 하단 **Artifacts** 에서 `GyuminModpackInstaller` 다운로드 (zip 압축된 exe)

## 5. 친구에게 공유

Artifacts에서 받은 `GyuminModpackInstaller.exe`를 압축 풀어서 그대로 친구에게 전달하면 끝입니다.
친구가 더블클릭하면:
1. Java 설치 여부 확인 (없으면 adoptium.net 안내)
2. Forge 1.20.1 자동 설치
3. manifest.json 기준으로 모드 4개 자동 다운로드 (`%APPDATA%\.minecraft\mods`)

나중에 모드를 추가/교체하고 싶으면 **exe를 다시 만들 필요 없이** manifest.json만 고쳐서
push하면, 친구가 프로그램을 다시 실행할 때 알아서 새 모드를 받아옵니다.

---

### 참고: 윈도우 스마트스크린 경고

친구가 실행할 때 "Windows의 PC 보호" 경고가 뜰 수 있어요 (서명 안 된 exe라서 정상입니다).
"추가 정보" → "실행" 을 누르면 됩니다. 친구에게 미리 알려주세요.
