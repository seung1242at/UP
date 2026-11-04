# 블소 381VM 런처 - GitHub 업데이트 배포 가이드

이 저장소는 **BNS 전용 런처(v1.4.1+)의 게임 클라이언트 패치 배포용**입니다. 게임 서버 연결 없이 GitHub Releases의 최신 패치를 확인합니다.

## 런처에 등록되는 업데이트 주소

```text
https://github.com/seung1242at/UP/releases/latest/download/manifest.json
```

릴리스가 공개되기 전에는 위 주소가 404를 반환할 수 있습니다. 이 경우 런처는 업데이트를 확인하지 못하지만 기존 게임 실행은 가능합니다.

## 1. 변경 파일 준비

PC에 `D:\BNS_PATCH` 폴더를 만들고, **블소 게임 폴더를 기준으로 한 상대 경로**를 그대로 유지합니다.

```text
D:\BNS_PATCH\
  bin64\
    sample.dll
  contents\
    Local\
      NCSoft\
        data\
          xml.dat
          xml64.dat
```

이 경로는 예시입니다. 실제 사용하는 381VM 클라이언트의 하위 경로를 정확히 확인하세요. `bin64\sample.dll`은 게임 폴더의 `bin64\sample.dll`을 대체합니다.

**중요:** 최신 Release의 패치 폴더에는 **기준 버전 이후 변경된 파일을 누적해서** 넣으세요. 런처가 최신 릴리스만 확인하므로, v1.0.1에서 수정한 파일은 이후 릴리스에도 유지해야 이전 패치를 건너뛴 사용자도 업데이트됩니다. 변경되지 않은 파일은 SHA-256 검사 후 재다운로드되지 않습니다.

## 2. 로컬 패치 파일 만들기

런처 ZIP에 들어 있는 `GitHub_패치만들기.bat`를 실행하거나 Python 3에서 다음 명령을 사용합니다.

```bat
python GitHub_업데이트_배포파일_생성.py --repo seung1242at/UP --tag v1.0.1 --patch "D:\BNS_PATCH" --output "D:\BNS_RELEASE_101"
```

결과 폴더 안에 `manifest.json`과 `p_...` 파일들이 생성됩니다. `manifest.json`에는 설치 상대 경로(`path`), 내려받을 URL(`url`), SHA-256, 크기 등이 기록됩니다. **manifest.json을 손으로 만들어 입력할 필요는 없습니다.**

## 3. GitHub Release 게시

1. [Releases](https://github.com/seung1242at/UP/releases) → **Draft a new release** 선택
2. 새 태그 `v1.0.1` 입력 (배포 파일 생성기의 `--tag`와 일치)
3. 해당 결과 폴더의 **manifest.json 및 p_로 시작하는 모든 파일** 첨부
4. **Publish release** 클릭 (Draft 상태는 일반 런처에서 검색 불가)

기존 릴리스 파일을 덮어쓰는 대신 `v1.0.2`, `v1.0.3`처럼 새 버전을 게시하세요. GitHub Releases의 'latest' 주소는 최신 정식 릴리스를 가리키도록 사용합니다. Prerelease로 게시하면 latest에 표시되지 않을 수 있습니다.

## 4. 런처 동작

- 시작 시 위 manifest 주소를 자동 검색
- 버전이 바뀌면 **게임시작 → 업데이트** 버튼 전환
- 업데이트 버튼을 누르면 필요한 파일만 다운로드 및 SHA-256 검증 후, 게임 폴더의 해당 상대 경로에 배치
- 업데이트 완료 시 게임시작 버튼 복귀
- 게임 파일이 아예 없으면 ZIP으로 최초 설치 가능
- **`내 문서\BnS\ClientConfiguration.xml` 같은 개인 환경설정은 배포 대상에서 제외**
- 실행 중인 게임 파일은 덮어쓰지 않도록 게임 종료 후 업데이트 진행

## 주의사항

- 저장소는 **공개(Public)**입니다. 개인 자료나 계정 정보, 배포 권한 없는 게임 파일을 업로드하지 마세요.
- 런처 자체 EXE 업데이트는 별도 업데이터가 있어야 하며 이 방식은 **게임 클라이언트 파일** 업데이트용입니다.
- 신규 배포 전 테스트용 클라이언트에서 경로와 복구 가능 여부를 점검하세요.
- GitHub 릴리스에 `manifest.json`이 없으면 자동 업데이트는 작동하지 않습니다.
