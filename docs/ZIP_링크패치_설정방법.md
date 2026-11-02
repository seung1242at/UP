# ZIP 파일 링크로 자동 업데이트 등록하기 (블레이드&소울 회상 런처 v1.8 이상)

**기존 파일별 업데이트는 그대로 유지**하면서 큰 패치를 ZIP 파일 하나로 배포할 수 있습니다.

## 운영 순서

1. 패치할 파일을 실제 게임 폴더와 **같은 하위 경로**로 ZIP 파일에 넣습니다.
2. ZIP을 HTTPS 직접 다운로드가 가능한 저장소에 업로드합니다.
3. 배포용 PC에서 런처 ZIP에 포함된 **ZIP_등록정보_만들기.bat**를 실행합니다.
4. ZIP 파일을 선택하고 다운로드 URL을 입력하면 SHA-256과 size(바이트)가 자동 계산됩니다.
5. [patch_links.json](../patch_links.json)의 JSON 객체에 `archives` 항목을 추가하고, 만들어진 등록 정보를 붙여 넣습니다.
6. **Commit changes**를 누르면 [Actions](https://github.com/seung1242at/UP/actions)가 새 Release의 `manifest.json`을 만듭니다.
7. 업데이트를 받아야 하는 이용자는 **v1.8 이상 런처**를 실행하고, 업데이트 버튼을 누릅니다.

## ZIP 안의 폴더 구조

```text
update.zip
  bin64/
    example.dll
  contents/
    local/
      NCSoft/
        data/
          localfile64.bin
```

런처는 `update.zip`이라는 파일을 게임 폴더에 넣지 않습니다. ZIP 내부 각 파일을 게임 폴더 기준 같은 상대 경로에 풀어 배치합니다.

## 실제 JSON 형식

`patch_links.json`의 기존 `files`는 남겨두고 **`archives` 배열을 추가**합니다.

```json
{
  "files": [
    {
      "path": "contents/local/NCSoft/data/localfile64.bin",
      "url": "기존에 등록한 파일별 주소",
      "sha256": "기존 64자리 값",
      "size": 16439567
    }
  ],
  "archives": [
    {
      "name": "update.zip",
      "url": "https://example.com/update.zip",
      "sha256": "64자리 실제 ZIP SHA-256",
      "size": 123456
    }
  ]
}
```

위 `archives` 값은 설명용이며 그대로 게시하면 실패합니다. **실제 ZIP URL/해시/크기를 사용하세요.** ZIP 내부 상대경로가 기존 단일 파일 패치와 겹치면 v1.8 런처에서는 ZIP 내용이 우선합니다.

## 확인 및 주의사항

- 링크가 다운로드 버튼 또는 HTML 보기 페이지라면 런처에서 실패할 수 있습니다. 특히 Google Drive 공유 `/view` 링크는 직접 다운로드 주소가 아닙니다.
- SHA-256과 size는 **압축을 풀지 않은 ZIP 파일 자체**를 기준으로 계산합니다. 수정된 ZIP은 반드시 다시 계산해야 합니다.
- ZIP 내 파일 변경은 GitHub가 자동 감지하지 못합니다. 새로운 ZIP을 올린 뒤 `patch_links.json`의 URL, SHA-256 및 size를 변경하고 저장해야 새 릴리스가 발행됩니다.
- ZIP을 등록해도 이전 v1.7.2 런처에서는 **자동 압축 해제가 지원되지 않습니다.** 이용자에게 v1.8 이상 런처를 먼저 배포해야 합니다.
- 이전 버전을 설치한 이용자에게도 누적 적용될 수 있도록 ZIP에는 필요한 변경 파일 전체를 계속 포함하세요.
- 허가받은 게임 파일만 배포하고, `ClientConfiguration.xml`과 런처 설정 파일은 넣지 마세요.
- 업데이트는 기존 파일을 임시 백업한 뒤 교체하며, 파일 교체에 실패하면 되돌립니다. 영구 백업이 필요한 경우 업데이트 전에 게임 폴더를 별도 복사해 두세요.
- 런처의 ZIP 검증·압축 해제는 Windows 환경에서 최종 확인이 필요하며, 먼저 게임 폴더 사본에서 테스트하세요.
