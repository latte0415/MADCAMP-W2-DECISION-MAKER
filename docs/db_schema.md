# Database Schema

## User Defined Type

### event_status_type
- NOT_STARTED
- IN_PROGRESS
- PAUSED
- FINISHED

### proposal_status_type
- PENDING
- ACCEPTED
- REJECTED
- DELETED

### proposal_category_type
- CREATION
- MODIFICATION
- DELETION

## Tables

### users
- id: uuid, PK
- (기타 사용자 필드들은 auth 모듈에서 정의)

### decisions
- id: uuid, PK
- subject: text, NOT NULL
- assumption_is_auto_approved_by_votes: boolean, default true, NOT NULL
- criteria_is_auto_approved_by_votes: boolean, default true, NOT NULL
- assumption_min_votes_required: integer, NULL
- criteria_min_votes_required: integer, NULL
- event_status: event_status_type(UDT), NOT NULL
- created_at: timestamp with time zone, NOT NULL
- updated_at: timestamp with time zone, NULL
- admin_id: uuid, FK(users.id), NOT NULL

**제약 조건:**
- CHECK: assumption_is_auto_approved_by_votes = true → assumption_min_votes_required IS NOT NULL
- CHECK: criteria_is_auto_approved_by_votes = true → criteria_min_votes_required IS NOT NULL

**설명:**
- decision은 방(room) 역할을 함 (1:1 매칭이므로 별도 rooms 테이블 불필요)
- admin_id는 해당 decision의 관리자
- 권한 체크는 서비스 레이어에서 처리

### answers
- id: uuid, PK
- decision_id: uuid, FK(decisions.id), NOT NULL
- content: text, NOT NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL
- updated_at: timestamp with time zone, NULL

**제약 조건:**
- admin만 추가/수정 가능 (서비스 레이어에서 체크)

**참고:**
- vote_cnt는 제거됨 → COUNT(*)로 계산 (동시성 문제 방지)
- 실제 투표 수는 answer_votes 테이블에서 COUNT(*)로 조회

### assumptions
- id: uuid, PK
- decision_id: uuid, FK(decisions.id), NOT NULL
- content: text, NOT NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL
- updated_at: timestamp with time zone, NULL
- updated_by: uuid, FK(users.id), NULL

### criterion
- id: uuid, PK
- decision_id: uuid, FK(decisions.id), NOT NULL
- content: text, NOT NULL
- conclusion: text, NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL
- updated_at: timestamp with time zone, NULL
- updated_by: uuid, FK(users.id), NULL

**설명:**
- conclusion: 각 criterion에 대한 최종 승인된 결론/요약 텍스트
- 각 criterion 별로 conclusion이 있어야 최종 결정에 합리적
- conclusion은 conclusion_proposals에서 승인된 것을 반영

### assumption_proposals
- id: uuid, PK
- decision_id: uuid, FK(decisions.id), NOT NULL
- assumption_id: uuid, FK(assumptions.id), NULL
- proposal_status: proposal_status_type, DEFAULT 'PENDING', NOT NULL
- proposal_category: proposal_category_type, NOT NULL
- proposal_content: text, NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL
- accepted_at: timestamp with time zone, NULL
- applied_at: timestamp with time zone, NULL
- applied_target_id: uuid, FK(assumptions.id), NULL

**제약 조건:**
- CHECK: proposal_category = 'CREATION' → assumption_id IS NULL
- CHECK: proposal_category != 'CREATION' → assumption_id IS NOT NULL
- CHECK: proposal_category = 'DELETION' → proposal_content IS NULL
- CHECK: proposal_category != 'DELETION' → proposal_content IS NOT NULL
- UNIQUE: (assumption_id, created_by) - 사용자당 동일 assumption에 대한 중복 제안 방지

**설명:**
- accepted_at: 이 제안을 채택하기로 결정한 시점 (정책/합의)
- applied_at: 실제 assumption 테이블에 적용된 시점 (실행/반영)
- applied_target_id:
  - CREATION: 새로 생성된 assumption.id
  - MODIFICATION/DELETION: 기존 assumption_id와 동일
- vote_cnt 제거됨 → COUNT(*)로 계산 (assumption_proposal_votes 테이블에서)

### criteria_proposals
- id: uuid, PK
- decision_id: uuid, FK(decisions.id), NOT NULL
- criteria_id: uuid, FK(criterion.id), NULL
- proposal_status: proposal_status_type, DEFAULT 'PENDING', NOT NULL
- proposal_category: proposal_category_type, NOT NULL
- proposal_content: text, NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL
- accepted_at: timestamp with time zone, NULL
- applied_at: timestamp with time zone, NULL
- applied_target_id: uuid, FK(criterion.id), NULL

**제약 조건:**
- CHECK: proposal_category = 'CREATION' → criteria_id IS NULL
- CHECK: proposal_category != 'CREATION' → criteria_id IS NOT NULL
- CHECK: proposal_category = 'DELETION' → proposal_content IS NULL
- CHECK: proposal_category != 'DELETION' → proposal_content IS NOT NULL
- UNIQUE: (criteria_id, created_by) - 사용자당 동일 criterion에 대한 중복 제안 방지 

**설명:**
- accepted_at: 이 제안을 채택하기로 결정한 시점 (정책/합의)
- applied_at: 실제 criterion 테이블에 적용된 시점 (실행/반영)
- applied_target_id:
  - CREATION: 새로 생성된 criterion.id
  - MODIFICATION/DELETION: 기존 criteria_id와 동일
- vote_cnt 제거됨 → COUNT(*)로 계산 (criterion_proposal_votes 테이블에서)

### assumption_proposal_votes
- id: uuid, PK
- assumption_proposal_id: uuid, FK(assumption_proposals.id, ON DELETE CASCADE), NOT NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL

**제약 조건:**
- UNIQUE: (assumption_proposal_id, created_by) - 중복 투표 방지

**설명:**
- 동일 사용자가 동일 proposal에 중복 투표 불가
- ON DELETE CASCADE: proposal 삭제 시 투표도 함께 삭제

### criterion_proposal_votes
- id: uuid, PK
- criterion_proposal_id: uuid, FK(criterion_proposals.id, ON DELETE CASCADE), NOT NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL

**제약 조건:**
- UNIQUE: (criterion_proposal_id, created_by) - 중복 투표 방지

**설명:**
- 동일 사용자가 동일 proposal에 중복 투표 불가
- ON DELETE CASCADE: proposal 삭제 시 투표도 함께 삭제

### answer_votes
- id: uuid, PK
- answer_id: uuid, FK(answers.id, ON DELETE CASCADE), NOT NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL

**제약 조건:**
- UNIQUE: (answer_id, created_by) - 중복 투표 방지

**설명:**
- 동일 사용자가 동일 answer에 중복 투표 불가
- ON DELETE CASCADE: answer 삭제 시 투표도 함께 삭제

### conclusion_proposals
- id: uuid, PK
- criterion_id: uuid, FK(criterion.id, ON DELETE CASCADE), NOT NULL
- proposal_status: proposal_status_type, DEFAULT 'PENDING', NOT NULL
- proposal_content: text, NOT NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL
- accepted_at: timestamp with time zone, NULL
- applied_at: timestamp with time zone, NULL

**제약 조건:**
- UNIQUE: (criterion_id, created_by) - 사용자당 동일 criterion에 대한 중복 conclusion 제안 방지

**설명:**
- 각 criterion에 대한 conclusion 제안
- accepted_at: 이 제안을 채택하기로 결정한 시점
- applied_at: 실제 criterion 테이블의 conclusion 필드에 적용된 시점
- proposal_content가 승인되면 criterion.conclusion에 반영됨
- 기각되면 새로운 제안을 다시 생성하는 방식

### conclusion_proposal_votes
- id: uuid, PK
- conclusion_proposal_id: uuid, FK(conclusion_proposals.id, ON DELETE CASCADE), NOT NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL

**제약 조건:**
- UNIQUE: (conclusion_proposal_id, created_by) - 중복 투표 방지

**설명:**
- conclusion_proposals에 대한 투표
- 동일 사용자가 동일 proposal에 중복 투표 불가
- ON DELETE CASCADE: proposal 삭제 시 투표도 함께 삭제

### criterion_priorities
- id: uuid, PK
- criterion_id: uuid, FK(criterion.id, ON DELETE CASCADE), NOT NULL
- created_by: uuid, FK(users.id), NOT NULL
- priority_rank: integer, NOT NULL
- created_at: timestamp with time zone, NOT NULL
- updated_at: timestamp with time zone, NULL

**제약 조건:**
- UNIQUE: (criterion_id, created_by) - 사용자당 각 criterion에 하나의 우선순위만 가능
- CHECK: priority_rank > 0

**설명:**
- 최종 투표 시 사용자가 각 criterion에 부여한 우선순위
- 한 사용자는 각 criterion마다 하나의 우선순위만 부여 가능
- priority_rank: 숫자가 낮을수록 높은 우선순위 (예: 1, 2, 3, ...)
- **정규화**: criterion_id만 사용 (criterion이 이미 decision_id를 포함하므로 중복 방지)

### comments
- id: uuid, PK
- criterion_id: uuid, FK(criterion.id, ON DELETE CASCADE), NOT NULL
- content: text, NOT NULL
- created_at: timestamp with time zone, NOT NULL
- created_by: uuid, FK(users.id), NOT NULL
- updated_at: timestamp with time zone, NULL

**설명:**
- criterion에 대한 댓글/의견
- 각 criterion 별로 토론할 수 있도록 함

## 데이터 타입 및 규칙

### timestamp
- 모든 datetime 필드는 `timestamp with time zone` 사용 (PostgreSQL 기준)
- created_at, updated_at 등은 자동으로 현재 시각 설정

### uuid
- 모든 PK는 uuid 사용
- PostgreSQL의 gen_random_uuid() 함수 사용 권장

### 제약 조건 우선순위
1. **DB 제약 (UNIQUE/CHECK/FK)** - 최종 방어선
2. **서비스 레이어 권한 체크** - 비즈니스 로직
3. RLS는 나중에 "DB 직접 접근하는 클라이언트가 늘 때" 도입 고려

### 동시성 고려사항
- vote_cnt 같은 계산된 값은 테이블에 저장하지 않고 COUNT(*)로 계산
- 트랜잭션 내에서 투표 생성/삭제 시 UNIQUE 제약으로 중복 방지