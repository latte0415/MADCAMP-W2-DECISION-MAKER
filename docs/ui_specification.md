# IA
## Auth
- Log-in (2-0-0)
- Sign-up (2-1-0)
- Reset_PW (2-2-0)
## 메인 화면
- Home (3-0-0)
- Event_Overview (3-1-0) (Pop-up)
- Event_Creation (3-2-0) (Pop-up)
## 진행 화면 (=상세 화면)
- Event (4-0-0)
- Event_Setting (4-1-0) (Pop-up)
- Event_Vote (4-2-0) (Pop-up)

# UI Framework
## Home (3-0-0)

### 목적

- 현재 들어갈 수 있는 이벤트 확인할 수 있는 리스트
- 새롭게 이벤트 참가할 수 있는 UI 제공

### 구성 요소

- 참여하기 버튼
- 생성하기 버튼
- 로그아웃 버튼
- 코드 입장 팝업 모달
    - 코드 입력 창 (텍스트) → 대소문자 구분 X. 최대 6자
    - 접속 버튼
    - 닫기 버튼
- 이벤트 리스트
    - 이벤트 컴포넌트:
        - 주제(decision_subject)
        - 진행 상태(event_status)
        - 관리자(admin_id → name)
        - 참가 인원(sql 연산 필요)
        - 멤버십 상태: NULL, 승인 대기 중, 관리자, 거절됨
        - 입장 코드(entrance_code)
        - 진행하기 버튼

### 액션

- 로그인 안되어 있으면 Log-in (2-0-0)로 리디렉션
- 참여하기 버튼 클릭 → 코드 입장 모달 팝업
    - 코드 입장 모달
        - 코드 입력창 (텍스트): 대문자 자동 포맷팅
        - 6자 입력 → 접속 버튼 활성화
        - 접속 버튼 클릭 → Event_Overview (3-1-0) (Pop-up) 팝업 활성화
        - 닫기 버튼 클릭 → 팝업 꺼짐
- 생성하기 버튼 클릭 → Event_Creation (3-2-0) (Pop-up)로 이동
- 이벤트 리스트 > 이벤트 컴포넌트 클릭 → Event_Overview (3-1-0) (Pop-up) 팝업 활성화
- 로그아웃 버튼 클릭 → 로그아웃 처리하고, Entrance (1-0-0)으로 이동

### API 설계

- GET /events/all/{user_id}:
    - events: id, decision_subject, event_status, admin_id, entrance_code(event_memebership에서 조인해서 속한 event만)
    - users: name (admin_id으로 조인해서 가져올 예정)
    - 참가 인원: event_memebership에서 id 조인해서 count (ACCPETED만)
    - is_admin: 현재 접속한 user_id 기반으로 admin_id 비교한 boolean 값
    - membership_status: pending 중인지 여부
    - 제안: `GET /events` (현재 사용자 정보는 JWT 토큰에서 추출)

## Event_Overview (3-1-0) (Pop-up)

### 목적

- 홈 화면(Home (3-0-0)에서 뜨는 개요 창
- event 접속을 위해서 반드시 거쳐야 하는 창으로, 현재 membership 상태 처리

### 구성 요소

- 팝업 닫기 버튼
- 정보
    - 주제
    - 선택지
    - 참가 인원
    - 관리자
    - 현재 상태
    - 가입 상태 메시지 + 입장하기 버튼
        - 가입이 거절되었습니다 + 비활성화
        - 승인 대기 중입니다 + 비활성화
        - 가입이 승인되었습니다 + 활성화
    - 입장하기 버튼

### 액션

- 팝업 닫기 버튼 클릭 → 팝업 종료 (Home (3-0-0) 유지)
- 입장하기 버튼 클릭 → Event(4-0-0)으로 이동

### API 설계

- POST /events/entry
    - 입력: users.id, entrance_code
    - 로직
        - event_memebership 추가 안 되어 있으면, PENDING 걸어두고 대기
        - 추가 되어 있는데 PENDING이면 역시나 대기
        - 추가 되어 있는데 ACCPETED면 Event_Overview (3-1-0) (Pop-up)로 이동하기 위한 정보 반환
    - 제안: `POST /events/entry` 또는 `POST /events/join`

## Event_Creation (3-2-0) (Pop-up)

### 목적

- 홈 화면(Home (3-0-0)에서 뜨는 개요 창
- event 생성을 위한 창

### 구성 요소

- 팝업 닫기 버튼
- 입력창
    - 기본 정보 입력
        - 주제: 텍스트
        - 선택지 입력: 최대 5개 텍스트
        - 전제 입력: 최대 10개 텍스트
        - 기준 입력: 최대 10개 텍스트
        - 최대 인원: int
    - 투표 허용 정책
        - 투표로 전제 제안/편집 허용하기: 토글
        - 전제 제안/편집 허용하는 최소 투표 수: int (위 토글 on 일때만)
        - 투표로 기준 제안/편집 허용하기: 토글
        - 기준 제안/편집 허용하는 최소 투표 수: int (위 토글 on 일때만)
        - 결론이 승인되는 최소 동의 투표 퍼센티지: int (1~100)
    - 입장 정책
        - 가입 승인 자동 여부: 토글
        - 입장 코드: 텍스트 (대문자 자동 포맷팅)
            - 코드 랜덤 생성 버튼
            - 코드 사용 가능한지 중복 확인 버튼
- 생성하기 버튼

### 액션

- 팝업 닫기 버튼 클릭 → 팝업 종료 (Home (3-0-0) 유지)
- 생성하기 버튼 클릭 → Event(4-0-0)으로 이동

### API 설계

- POST /events/

## Event (4-0-0)

### 목적

- 실제 의사 결정하는 장소 (추후 구현)

### 구성 요소

- 나가기 버튼
- 투표하기 버튼 (event_status가 IN_PROGRESS일 때만 활성화
- 상태 드롭다운 (admin 한정): 진행 중, 종료, 시작 예정, 일시 정지
- 설정 버튼 (admin 한정)
- 기본 정보 섹션
    - 주제
    - 선택지
- 전제 섹션
    - 전제 컴포넌트 (컴포넌트 정의 참고)
- 기준 섹션
    - 기준 컴포넌트 (컴포넌트 정의 참고)
- 입력창
    - 드롭다운
        - 분류: 전제 OR 기준 (NOT NULL)
        - 번호: 전제/기준 번호 ("추가"일 경우는 NULL)
        - 액션: 추가/수정/삭제/코멘트/결론 (전제일 경우, 코멘트 및 결론 선택 불가)
    - 제안 버튼 (실질적인 등록 액션)
    - 텍스트 입력
        - 내용
        - 이유 (코멘트일 때는 NULL)

### 액션

- 나가기 버튼 클릭 → Home (3-0-0)으로 이동
- 투표하기 버튼 클릭 → Event_Vote (4-2-0) 팝업
- 전제 섹션
    - 추가하기 버튼 클릭 → 드롭다운: 전제/-/추가 로 상태 변환
    - 전제 n번의 수정 버튼 클릭 → 드롭다운: 전제/n/수정 으로 상태 변환
    - 전제 n번의 삭제 버튼 클릭 → 드롭다운: 전제/n/삭제 으로 상태 변환
    - 제안된 내용의 동의 버튼 클릭 → 해당 proposal에 대한 vote 증가 (한번더 클릭하면 다시 취소)
    - 제안된 내용의 승인 버튼 클릭 (admin) → 해당 proposal 승인 상태로 전환
    - 특정 proposal의 vote count가 임계값을 넘으면, 승인 상태로 전환
- 기준 섹션
    - 추가하기 버튼 클릭 → 드롭다운: 기준/-/추가 로 상태 변환
    - 기준 n번의 수정 버튼 클릭 → 드롭다운: 기준/n/수정 으로 상태 변환
    - 기준 n번의 삭제 버튼 클릭 → 드롭다운: 기준/n/삭제 으로 상태 변환
    - 기준 n번 컴포넌트 자체 클릭 → 드롭다운: 기준/n/코멘트 로 상태 변환
        - 더블 클릭하면 기준/n/결론으로 상태 변환
    - 제안된 내용의 동의 버튼 클릭 → 해당 proposal에 대한 vote 증가 (한번더 클릭하면 다시 취소)
    - 제안된 내용의 승인/기각 버튼 클릭 (admin) → 해당 proposal 승인/기각 상태로 전환
    - 특정 proposal의 vote count가 임계값을 넘으면, 승인 상태로 전환(auto approved가 켜져있는 경우 한정. 아닌 경우는 그냥 카운트만 되서 조회만 됨)

### API 설계

- event에 대한 주제, 선택지, 전제, 기준, 각각에 대한 제안 조회하기
  - 제안: `GET /events/{event_id}`
- 전제에 대한 제안 생성하기
  - 제안: `POST /events/{event_id}/assumption-proposals`
- 전제에 대한 제안 투표 생성하기/삭제하기
  - 제안: `POST /events/{event_id}/assumption-proposals/{proposal_id}/votes` (생성)
  - 제안: `DELETE /events/{event_id}/assumption-proposals/{proposal_id}/votes` (삭제)
- 기준에 대한 제안 생성하기
  - 제안: `POST /events/{event_id}/criteria-proposals`
- 기준에 대한 제안 투표 생성하기/삭제하기
  - 제안: `POST /events/{event_id}/criteria-proposals/{proposal_id}/votes` (생성)
  - 제안: `DELETE /events/{event_id}/criteria-proposals/{proposal_id}/votes` (삭제)
- 기준에 대한 결론에 대한 제안 생성하기
  - 제안: `POST /events/{event_id}/criteria/{criterion_id}/conclusion-proposals`
- 기준에 대한 결론에 대한 투표 생성하기/삭제하기
  - 제안: `POST /events/{event_id}/conclusion-proposals/{proposal_id}/votes` (생성)
  - 제안: `DELETE /events/{event_id}/conclusion-proposals/{proposal_id}/votes` (삭제)
- 특정 기준에 대한 코멘트 수 조회하기
  - 제안: `GET /events/{event_id}/criteria/{criterion_id}/comments/count`
- 특정 기준에 대한 코멘트 조회하기
  - 제안: `GET /events/{event_id}/criteria/{criterion_id}/comments`
- 특정 기준에 대한 본인 코멘트 생성/수정/삭제하기
  - 제안: `POST /events/{event_id}/criteria/{criterion_id}/comments` (생성)
  - 제안: `PATCH /events/{event_id}/comments/{comment_id}` (수정)
  - 제안: `DELETE /events/{event_id}/comments/{comment_id}` (삭제)
- (ADMIN) 제안 승인/기각하기
  - 제안: `PATCH /events/{event_id}/assumption-proposals/{proposal_id}/status` (전제 제안)
  - 제안: `PATCH /events/{event_id}/criteria-proposals/{proposal_id}/status` (기준 제안)
  - 제안: `PATCH /events/{event_id}/conclusion-proposals/{proposal_id}/status` (결론 제안)
- (ADMIN) event 상태 변화시키기
  - 제안: `PATCH /events/{event_id}/status`

### 전제 컴포넌트 정의

### 공통 구성

- 전제 내용 텍스트
- 수정/삭제 버튼

### 상태에 따른 변수

1. 삭제가 제안된 전제
    1. 기존 텍스트 아래에 태깅("삭제")
    2. 삭제 제안 이유
    3. 현재 인원 중 동의한 인원(n/m)
    4. 동의 버튼
    5. 승인/기각 버튼 (관리자 한정)
    6. **거부된 제안**: 밑줄 처리된 상태로 표시
2. 수정이 제안된 전제
    1. 기존 텍스트 아래에 태깅("수정")
    2. 제안된 수정 내용
    3. 수정 제안 이유
    4. 현재 인원 중 동의한 인원(n/m)
    5. 동의 버튼
    6. 승인/기각 버튼 (관리자 한정)
    7. **거부된 제안**: 밑줄 처리된 상태로 표시
3. 추가가 제안된 전제
    1. 태깅("추가")
    2. 제안된 추가 내용
    3. 추가 제안 이유
    4. 현재 인원 중 동의한 인원(n/m)
    5. 동의 버튼
    6. 승인/기각 버튼 (관리자 한정)
    7. **거부된 제안**: 밑줄 처리된 상태로 표시
4. **승인된 제안**: 기준/전제에 반영되어 더 이상 제안으로 표시되지 않음

### 기준 컴포넌트 정의

### 기준 관련 (전제 컴포넌트와 동일한 형태, 로직을 따름)
- **승인된 제안**: 기준에 반영되어 더 이상 제안으로 표시되지 않음
- **거부된 제안**: 밑줄 처리된 상태로 표시

### 코멘트 컴포넌트

1. fold 기능 존재. default fold
2. "사용자", "내용", "날짜" 나열
3. 수정/삭제 버튼 (본인 거에 한해서)

### 결론 컴포넌트

1. 결론 내용
2. 현재 인원 중 동의한 인원 (n/m)
3. 동의 버튼
4. 승인/기각 버튼 (관리자 한정)
5. 퍼센티지 바: 현재 퍼센티지 + 동의 기준 퍼센티지

## Event_Setting (4-1-0) (Pop-up)

### 목적

- 이벤트 설정 변경하는 팝업 (관리자용)
- Creation과 유사한 구조의 팝업

### 구성 요소

- 팝업 닫기 버튼
- 입력창
    - 기본 정보
        - 주제: 텍스트
        - 선택지 입력: 최대 5개 텍스트
        - 전제 입력: 최대 10개 텍스트
        - 기준 입력: 최대 10개 텍스트
        - 최대 인원: int
    - 투표 허용 정책
        - 투표로 전제 제안/편집 허용하기: 토글
        - 전제 제안/편집 허용하는 최소 투표 수: int (위 토글 on 일때만)
        - 투표로 기준 제안/편집 허용하기: 토글
        - 기준 제안/편집 허용하는 최소 투표 수: int (위 토글 on 일때만)
        - 결론이 승인되는 최소 동의 투표 퍼센티지: int (1~100)
    - 입장 정책
        - 가입 승인 자동 여부: 토글
        - 입장 코드 (수정 불가)
- 수정하기 버튼

### 액션

- 기본 정보 (except 최대 인원): NOT_STARTED인 경우만 추가/수정/삭제 가능
- 최대 인원: FINISHED 아니면 수정 가능 (현재 인원에 충돌나지 않는 선에서)
- 투표허용정책 + 입장정책(except 입장 코드): FINISHED 아니면 수정 가능

### API 설계

- PATCH /events
    - 제안: `PATCH /events/{event_id}`

## Event_Vote (4-2-0) (Pop-up)

### 목적

- 최종 투표

### 구성 요소

- 팝업 닫기 버튼
- 선택지 버튼
    - 여러 개의 선택지 중 하나만 활성화할 수 있음
- 기준 우선순위 정렬 UI
    - 오른쪽을 꾹 누른상태로 옮기면 순서 바꿀 수 있음
- 투표하기 버튼

### 액션

- 이미 투표했을 경우에는 기존 답변 불러와서, 재제출하면 투표 내용이 수정됨.

### API 설계

- 특정 유저의 특정 이벤트에 대한 투표 내역 조회하기
  - 제안: `GET /events/{event_id}/votes/me`
- 특정 유저가 특정 이벤트에 대한 투표 내역 생성/업데이트하기
  - 제안: `POST /events/{event_id}/votes` (생성)
  - 제안: `PUT /events/{event_id}/votes` 또는 `PATCH /events/{event_id}/votes` (업데이트)