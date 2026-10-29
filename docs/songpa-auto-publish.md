# 송파구 보도자료 자동 게시 절차

처음 작성 2026-10-21. 교수님 지시: "오타·사실 오류까지 검증하고 그대로 올려", 평일 하루 2번 확인.
예약 작업(scheduled task)이 이 문서를 읽고 그대로 따른다. 절차를 바꿀 때는 이 문서를 고친다.

## 0. 전체 흐름
메일 확인(Gmail 커넥터) → 새 보도자료 고르기 → 사진(Chrome 되면 송파구 사진, 안 되면 인포그래픽 후 나중에 교체) → 기사 쓰기 → 검증 → 빌드·미리보기 → 배포 → 라벨 붙이기(커넥터) → 교수님께 보고

**2026-10-28 변경(교수님 지시 "pc없이도 돌게")**: 예약 작업이 교수님 PC·데스크톱 앱 없이 클라우드에서 돈다. 메일 읽기·라벨은 Gmail 커넥터로 하고, Claude in Chrome은 사진 옮길 때만 "되면 쓰는" 선택 사항이다. Chrome이 안 된다는 이유로 게시를 멈추지 않는다.

## 1. 메일 확인 (Gmail 커넥터)
- 받는 곳: info@newsthehill.com. kj@abanable.com Gmail 메일함에 들어오고, Gmail 커넥터가 이 계정에 연결돼 있다.
- `search_threads` 검색어: `(from:songpa.go.kr OR (from:info@newsthehill.com 송파구)) -label:뉴스더힐-처리 newer_than:14d`
- 본문은 `get_message`(messageFormat `PLAIN_TEXT`)로 읽는다. 첨부 이름(사진 jpg, hwp)도 여기서 확인된다. 첨부 파일 자체는 커넥터로 받지 못한다(`RAW`는 수 MB라 쓰지 않는다).
- 커넥터는 최근 메일을 늦게 보여줄 수 있다. 이번 회차에 안 보인 메일은 라벨이 없으니 다음 회차에 잡힌다. 그래서 놓치지 않는다.
- 대상: 송파구청 홍보담당관(언론팀) 주무관이 보낸 **(송파구 보도자료)** 메일, 또는 교수님이 info@newsthehill.com에서 전달(FW)한 송파구 보도자료.
- 대상 아님: 광고, 행사 초대, 송파구 아닌 기관, 본문 없이 hwp만 있고 내용을 확인할 수 없는 메일, 날짜가 이미 지난 행사 → 게시하지 않고 라벨만 붙이고 보고에 적는다.

## 2. 중복 막기
- 처리한 메일에는 Gmail 라벨 **'뉴스더힐-처리'**를 붙인다(게시한 것과 건너뛴 것 모두).
- 라벨이 없어도 `articles/`에 같은 내용의 기사가 이미 있으면(제목 핵심어·행사명으로 `rg`) 새로 쓰지 않고 라벨만 붙인다.

## 3. 사진 가져오기
작업 컨테이너는 Gmail 첨부를 직접 받을 수 없다. 순서대로 시도한다.

**3-0. 먼저 밀린 사진 교체**: `docs/photo-pending.md`에 남은 기사가 있고 이번 회차에 Chrome이 되면, 새 기사보다 먼저 그 기사들의 인포그래픽을 송파구 사진으로 바꾼다. 바꿀 때는 새 파일 이름(`…-photo1.jpg`)을 쓰고(같은 이름 덮어쓰기는 휴대폰 캐시에 옛 그림이 남는다), 캡션을 `사진=송파구 제공`으로 고치고, 목록에서 지운다.

**3-A. Chrome이 될 때 (송파구 사진)**: `list_connected_browsers`로 연결된 크롬이 있으면 kj@abanable.com과 GitHub(say-gb)가 로그인된 **'직장' 프로필**을 고르고 아래 1~6을 따른다. Gmail 주소는 `https://mail.google.com/mail/?authuser=kj@abanable.com`(직장 프로필에서 보통 /u/0/), 해당 메일은 커넥터 결과의 viewUrl이나 검색으로 연다.

**3-B. Chrome이 안 될 때**: 게시를 미루지 않는다. docs/news-card-style.md 카드로 대표 이미지를 만들어 게시하고, 캡션은 `*그래픽=뉴스더힐(자료: 송파구)*`. 메일에 사진 첨부가 있었으면 `docs/photo-pending.md`에 `- news-…: 메일 제목 / 첨부 사진 이름` 한 줄을 남겨 다음 회차(3-0)에서 송파구 사진으로 바꾼다. 보고에 "사진 교체 대기"라고 적는다.

**3-A 세부 방법 (브라우저 → GitHub 업로드 화면)**
1. Gmail 탭에서 해당 메일을 연다(검색 결과 목록에서 클릭. Gmail은 한 페이지 앱이라 탭 안 이동은 클릭/`history.back()`으로).
2. Gmail 탭에서 GitHub 업로드 창을 연다. `window.open`은 클릭 없이 부르면 팝업 차단으로 `null`이 되므로, 임시 버튼을 만들고 computer 도구로 그 버튼을 클릭한다:
   ```js
   const b=document.createElement('button'); b.textContent='GH'; b.style.cssText='position:fixed;left:10px;top:10px;z-index:999999;width:80px;height:40px';
   b.onclick=()=>{ window.__gh=window.open('https://github.com/say-gb/newsthehill-site/upload/redesign/static/img','_blank'); b.remove(); };
   document.body.appendChild(b);
   ```
   업로드 화면에 "Uploads are disabled"가 뜨면 그 크롬에 GitHub 로그인이 풀린 것이다. 게시하지 말고 교수님께 say-gb 로그인을 요청한다.
3. GitHub 탭(새로 열린 탭 ID는 tabs_context_mcp로 확인)에 수신기를 단다:
   ```js
   window.__files=[]; window.addEventListener('message', e=>{ if(e.origin!=='https://mail.google.com') return;
   for(const f of e.data){ const bin=atob(f.b64); const u=new Uint8Array(bin.length); for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
   window.__files.push(new File([u], f.name, {type:'image/jpeg'})); } });
   ```
4. Gmail 탭에서 첨부 이미지를 가로 최대 1200px JPEG(품질 0.82)로 줄여 보낸다. 첨부 정보는 `[download_url]` 속성에 `mime:파일명:주소` 형태로 있다(주소 문자열을 출력하면 차단되니 출력하지 말 것):
   ```js
   const imgs=[]; for (const e of document.querySelectorAll('[download_url]')){ const v=e.getAttribute('download_url');
   const i1=v.indexOf(':'), i2=v.indexOf(':',i1+1), name=decodeURIComponent(v.slice(i1+1,i2)), url=v.slice(i2+1);
   if(!/\.(jpe?g|png)$/i.test(name)) continue;
   const bmp=await createImageBitmap(await fetch(url,{credentials:'include'}).then(r=>r.blob())); const s=Math.min(1,1200/bmp.width);
   const c=document.createElement('canvas'); c.width=Math.round(bmp.width*s); c.height=Math.round(bmp.height*s);
   c.getContext('2d').drawImage(bmp,0,0,c.width,c.height); imgs.push({orig:name, b64:c.toDataURL('image/jpeg',0.82).split(',')[1]}); }
   window.__gh.postMessage(imgs.map((x,i)=>({name:`news-YYYYMMDDNNNNN-photo${i+1}.jpg`, b64:x.b64})), 'https://github.com');
   ```
   - 대용량 첨부(서울시 메일 bigfile 링크)는 이 방법으로 안 될 수 있다. 일반 첨부 사진만 쓰고, 사진이 하나도 없으면 사진 없이 게시한다.
5. GitHub 탭에서 파일 입력에 넣고 커밋한다:
   ```js
   const inp=document.querySelector('input[type=file]'); const dt=new DataTransfer(); window.__files.forEach(f=>dt.items.add(f));
   inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true}));
   ```
   커밋 메시지 칸(placeholder "Add files via upload")에 `송파구 보도자료 사진 추가(행사명)`을 쓰고 "Commit directly to the redesign branch"가 선택된 상태로 Commit changes.
6. 작업한 탭은 모두 닫는다.

## 4. 기사 쓰기
- 저장소: `say-gb/newsthehill-site`. **원고는 `redesign` 브랜치**, 실제 사이트는 `main` 브랜치(빌드 결과물, GitHub Pages).
- 파일: `articles/YYYY-MM-DD-news-YYYYMMDDNNNNN.md`. 번호는 같은 날 기존 번호 다음(예: 그날 00003까지 있으면 00004).
- 모범: `articles/2026-10-21-news-2026102100001.md`, `…00002.md`, `…00003.md`의 형식과 문체를 그대로 따른다.
- front matter: title, subtitle, `section: local`, `author: 뉴스더힐 편집국`(교수님 10/22 지시: 보도자료 기사는 편집국 명의, 칼럼만 최경집. 10/27: 인터뷰도 편집국 명의), date(게시일), slug, `time: HH:MM`(게시 시각, KST).
- 본문 첫 줄 `입력 YYYY-MM-DD`, 다음에 대표 사진과 이탤릭 캡션 `*…. 사진=송파구 제공*`.
- 보도자료를 그대로 붙이지 않고 뉴스더힐 기사체(~다)로 다시 쓴다. 리드 → "송파구는 N일 보도자료에서 이같이 밝혔다" → 세부 → 일정·방법 → 구청장 인용(원문 그대로) 순서.
- 사진 캡션에는 보도자료나 사진에서 확인되는 것만 쓴다. 누구인지 확인되지 않는 인물을 이름으로 지목하지 않는다. 인물 한 명만 크게 나온 사진은 누구인지 보도자료에 없으면 쓰지 않는다.
- 쓰지 않는 사진 파일은 `static/img`에서 지우고 번호를 1부터 다시 맞춘다.

## 5. 검증 (게시 전에 반드시)
1. **사실 대조**: 기사 속 숫자, 날짜, 요일, 시간, 장소, 기관명, 인명·직함, 인용문을 보도자료 원문과 한 줄씩 대조한다. 원문에 없는 사실을 넣지 않는다.
2. **요일 계산**: 날짜-요일은 `python3 -c "import datetime;print(datetime.date(Y,M,D).strftime('%a'))"`로 확인한다. 원문 요일이 틀렸으면 날짜를 기준으로 고치고 보고에 적는다.
3. **맞춤법·오타**: 띄어쓰기, 조사, 따옴표 짝, 숫자 단위(명·점·곳), 중복 문장을 다시 읽어 고친다.
4. **빌드**: `python3 build.py` 성공, `rg '하남시민뉴스|hanamsiminnews' dist` 0건, 새 기사 페이지의 이미지 경로가 실제 파일과 맞는지 확인.
5. **화면**: `dist`를 로컬 서버로 띄워 Playwright로 첫 화면과 새 기사 페이지를 캡처해 직접 본다(깨진 사진, 제목 잘림, 캡션 위치).
6. 하나라도 판단이 서지 않는 문제(원문끼리 숫자가 다름, 엠바고 표시, 정정 요청 메일 등)가 있으면 **그 기사는 게시하지 않고** 원고만 `draft: true`로 올려 둔 뒤 보고한다.

## 6. 배포
1. 원고 커밋을 `redesign`에 푸시한다. 커밋 메시지 예: `송파구 보도자료 기사 작성: <제목 요약>. 사진=송파구 제공(자동 게시 YYYY-MM-DD HH:MM)`.
2. `main`을 받아 현재 커밋으로 백업 브랜치 `backup/main-<짧은SHA>`를 만든다.
3. `main` 작업 트리에서 `.git`을 뺀 모든 파일을 지우고 `dist/` 내용을 복사한다. **CNAME은 기존 main 파일을 그대로 둔다**(줄바꿈 없는 `newsthehill.com`).
4. 커밋 메시지: `배포: redesign <SHA> 빌드 결과 — <기사 요약>. CNAME 원본 유지. 이전 main <SHA>` 후 푸시.
5. Chrome이 되면 1~2분 뒤 `https://newsthehill.com/`과 새 기사 주소를 열어 반영을 확인한다. 안 되면 WebFetch로 새 기사 주소의 제목이 나오는지 확인한다(작업 컨테이너에서는 사이트에 직접 접속이 안 된다).

## 7. 마무리
- 처리한 메일 모두에 '뉴스더힐-처리' 라벨을 붙인다: Gmail 커넥터 `label_message`(labelIds `["Label_14"]`). 라벨 ID가 다르면 `list_labels`에서 이름 '뉴스더힐-처리'로 찾는다.
- 교수님께 짧게 보고: 게시한 기사 제목과 주소, 건너뛴 메일과 이유, 검증 중 고친 원문 오류. 새 보도자료가 없으면 "새 보도자료 없음" 한 줄.
