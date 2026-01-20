# ProposalService 리팩토링 전략 제안서

## 📊 현재 아키텍처 분석

### 현재 구조의 강점

1. **리포지토리 레벨의 제너릭화가 이미 잘 되어 있음**
   - `ProposalRepositoryGeneric`이 공통 메서드 제공
   - 각 타입별 리포지토리(`AssumptionProposalRepository`, `CriteriaProposalRepository`, `ConclusionProposalRepository`)가 제너릭을 상속
   - `ProposalRepository`가 모든 타입을 통합하여 제공
   - **이 패턴을 서비스 레벨에도 적용 가능**

2. **기존 아키텍처 패턴이 일관적**
   - `EventBaseService`를 상속받아 공통 로직 재사용
   - 의존성 주입 패턴 사용 (`app/dependencies/services.py`)
   - IdempotencyService를 주입받아 사용

### 현재 구조의 문제점

1. **서비스 레벨의 중복 코드**
   - `proposal_service.py`가 1,377줄로 과도하게 큼
   - Assumption, Criteria, Conclusion 세 타입의 로직이 거의 동일하게 반복
   - 각 타입마다 동일한 패턴의 메서드가 3번씩 반복:
     - `create_*_proposal()` (각 80줄, 총 240줄)
     - `create_*_proposal_vote()` (각 45줄, 총 135줄)
     - `delete_*_proposal_vote()` (각 45줄, 총 135줄)
     - `update_*_proposal_status()` (각 110줄, 총 330줄)

2. **Idempotency 로직 중복**
   - 모든 생성/수정 메서드에 동일한 패턴 반복
   - 명시적 래핑이지만 코드 중복이 많음

---

## 🎯 권장 전략: **"리포지토리 패턴을 서비스 레벨로 확장"**

### 핵심 아이디어

**리포지토리 레벨에서 이미 성공적으로 적용된 제너릭화 패턴을 서비스 레벨에도 동일하게 적용**

### 전략의 장점

1. **기존 아키텍처와의 일관성**
   - 리포지토리 레벨의 패턴을 그대로 따름
   - 개발자들이 이미 익숙한 패턴
   - 학습 곡선 최소화

2. **점진적 리팩토링 가능**
   - 한 번에 모든 것을 바꾸지 않고 단계적으로 진행
   - 각 단계마다 테스트 가능
   - 리스크 최소화

3. **API 호환성 유지**
   - Facade 패턴으로 기존 인터페이스 유지
   - 라우터 레벨 변경 불필요

---

## 🏗️ 제안하는 아키텍처 구조

```
app/services/event/proposal/
├── __init__.py                    # ProposalService Facade export
├── facade.py                      # 기존 ProposalService (Facade)
├── core/                          # 공통 UseCase 모듈
│   ├── __init__.py
│   ├── vote_usecase.py           # 투표 생성/삭제 공통 로직
│   ├── approval_usecase.py       # 승인/거절 상태 변경 공통 로직
│   ├── auto_approval.py          # 자동 승인 로직 공통화
│   └── idempotency_wrapper.py    # Idempotency 명시적 래핑
├── types/                         # 타입별 서비스
│   ├── __init__.py
│   ├── assumption_service.py     # Assumption 전용 서비스
│   ├── criteria_service.py       # Criteria 전용 서비스
│   └── conclusion_service.py     # Conclusion 전용 서비스
└── configs.py                     # 타입별 설정/훅 정의 (선택)
```

### 구조 설명

#### 1. `core/` 모듈: 공통 UseCase

**리포지토리 레벨의 `ProposalRepositoryGeneric`과 유사한 역할**

- **`vote_usecase.py`**: 투표 생성/삭제 공통 로직
  - 타입별 차이는 함수 인자로 주입받음
  - 리포지토리 패턴과 동일하게 제너릭화

- **`approval_usecase.py`**: 승인/거절 상태 변경 공통 로직
  - 조건부 UPDATE 패턴 공통화
  - 타입별 `apply_proposal` 함수를 주입받음

- **`auto_approval.py`**: 자동 승인 로직 공통화
  - Assumption/Criteria: 투표 수 기반
  - Conclusion: 비율 기반
  - 타입별 차이는 설정으로 처리

- **`idempotency_wrapper.py`**: Idempotency 명시적 래핑
  - 모든 생성/수정 메서드에 일관된 패턴 적용

#### 2. `types/` 모듈: 타입별 서비스

**리포지토리 레벨의 타입별 리포지토리와 유사한 역할**

각 타입별 서비스는:
- Core UseCase들을 조합하여 사용
- 타입별 특화 로직만 구현:
  - 검증 로직 (`_validate_*_for_proposal`)
  - 응답 빌더 (`_build_*_response`)
  - 제안 적용 로직 (`_apply_*_proposal`)

#### 3. `facade.py`: 기존 API 호환성 유지

**리포지토리 레벨의 `ProposalRepository`와 유사한 역할**

- 기존 `ProposalService` 인터페이스 유지
- 내부적으로 타입별 서비스를 호출
- 라우터 레벨 변경 불필요

---

## 📋 단계별 실행 계획 (우선순위 기반)

### Phase 0: 테스트 준비 (필수, 2-3일)

**목표**: 리팩토링 전후 동일하게 통과해야 할 테스트 고정

#### 필수 테스트 시나리오

1. **Vote 동시성 테스트**
   - 같은 proposal에 동시 투표 시도
   - 하나만 성공, 나머지는 ConflictError

2. **Idempotency 테스트**
   - 같은 idempotency_key로 재요청 시 동일 결과

3. **승인 상태 전이 테스트**
   - 동시에 같은 proposal 승인 시도 시 1회만 성공

4. **Proposal 생성 중복 체크**
   - 같은 assumption_id + user_id로 PENDING proposal 중복 생성 방지

---

### Phase 1: Vote UseCase 추출 (3-4일) - **최우선**

**목표**: 가장 안전하고 효과가 큰 Vote 로직부터 공통화

#### 작업 내용

1. **`core/vote_usecase.py` 생성**
   ```python
   class VoteUseCase:
       """투표 생성/삭제 공통 로직"""
       
       def create_vote(
           self,
           event_id: UUID,
           proposal_id: UUID,
           user_id: UUID,
           # 타입별 의존성 주입
           get_proposal_fn: Callable,
           create_vote_fn: Callable,
           check_duplicate_fn: Callable,
           auto_approve_fn: Callable,
           build_response_fn: Callable,
       ) -> dict:
           # 공통 로직 구현
   ```

2. **타입별 Vote 메서드를 UseCase로 교체**
   - `create_assumption_proposal_vote()` → `VoteUseCase.create_vote()` 호출
   - `create_criteria_proposal_vote()` → `VoteUseCase.create_vote()` 호출
   - `create_conclusion_proposal_vote()` → `VoteUseCase.create_vote()` 호출
   - delete 메서드들도 동일하게 교체

**예상 효과**: 약 270줄 → 약 100줄 (약 63% 감소)

---

### Phase 2: Approval UseCase 추출 (3-4일)

**목표**: 조건부 UPDATE 패턴 공통화

#### 작업 내용

1. **`core/approval_usecase.py` 생성**
   ```python
   class ApprovalUseCase:
       """승인/거절 상태 변경 공통 로직"""
       
       def update_status(
           self,
           event_id: UUID,
           proposal_id: UUID,
           status: ProposalStatusType,
           user_id: UUID,
           # 타입별 의존성 주입
           verify_admin_fn: Callable,
           get_proposal_fn: Callable,
           approve_if_pending_fn: Callable,
           reject_if_pending_fn: Callable,
           apply_proposal_fn: Callable,
           build_response_fn: Callable,
       ) -> dict:
           # 공통 로직 구현
   ```

2. **`core/auto_approval.py` 생성**
   ```python
   class AutoApprovalChecker:
       """자동 승인 로직 공통화"""
       
       @staticmethod
       def check_and_auto_approve(
           proposal: TProposal,
           event: Event,
           vote_count: int,
           # 타입별 설정
           min_votes_required: int | None,  # Assumption/Criteria용
           approval_threshold_percent: float | None,  # Conclusion용
           total_members: int | None,  # Conclusion용
           # 타입별 함수
           approve_if_pending_fn: Callable,
           apply_proposal_fn: Callable,
       ) -> None:
           # 공통 로직 구현
   ```

3. **타입별 상태 변경 메서드를 UseCase로 교체**

**예상 효과**: 약 330줄 → 약 150줄 (약 55% 감소)

---

### Phase 3: Idempotency Wrapper 통일 (2일)

**목표**: Idempotency 명시적 래핑으로 통일

#### 작업 내용

1. **`core/idempotency_wrapper.py` 생성**
   ```python
   class IdempotencyWrapper:
       """Idempotency 명시적 래핑 헬퍼"""
       
       def wrap(
           self,
           idempotency_key: str | None,
           user_id: UUID,
           method: str,
           path: str,
           body: dict,
           fn: Callable[[], dict],
       ) -> dict:
           if self.idempotency_service and idempotency_key:
               return self.idempotency_service.run(...)
           else:
               return fn()
   ```

2. **모든 생성/수정 메서드에 래퍼 적용**

**예상 효과**: 코드 중복 제거, 일관된 패턴 적용

---

### Phase 4: 타입별 서비스 분리 (3-4일)

**목표**: 타입별 서비스 클래스 생성 및 Facade 패턴 적용

#### 작업 내용

1. **타입별 서비스 클래스 생성**
   ```python
   # types/assumption_service.py
   class AssumptionProposalService:
       """Assumption Proposal 전용 서비스"""
       
       def __init__(self, db, repos, vote_usecase, approval_usecase, ...):
           self.vote_usecase = vote_usecase
           self.approval_usecase = approval_usecase
           # ...
       
       def create_proposal(self, ...):
           # ProposalCreationUseCase 사용 (또는 직접 구현)
       
       def create_vote(self, ...):
           return self.vote_usecase.create_vote(...)
       
       def update_status(self, ...):
           return self.approval_usecase.update_status(...)
   ```

2. **Facade Service 생성**
   ```python
   # facade.py
   class ProposalService:
       """기존 API와의 호환성을 위한 Facade"""
       
       def __init__(self, ...):
           self.assumption_service = AssumptionProposalService(...)
           self.criteria_service = CriteriaProposalService(...)
           self.conclusion_service = ConclusionProposalService(...)
       
       def create_assumption_proposal(self, ...):
           return self.assumption_service.create_proposal(...)
       
       # ... 기존 인터페이스 유지
   ```

3. **의존성 주입 업데이트**
   - `app/dependencies/services.py`에서 새로운 구조로 변경
   - 기존 라우터는 변경 없음

---

### Phase 5: Proposal 생성 부분 공통화 (선택, 2-3일)

**목표**: 생성 로직의 공통 뼈대만 공유

**주의**: 이 단계는 선택사항. P0, P1만으로도 충분한 효과가 있음.

---

## 📈 예상 효과

### Phase 1 + Phase 2 완료 시

**코드 품질**:
- ✅ 코드 라인 수: **1,377줄 → 약 800-900줄** (약 35-40% 감소)
- ✅ 중복 코드: **약 50-60% 감소** (Vote + Approval)
- ✅ 순환 복잡도: **크게 감소**

**유지보수성**:
- ✅ Vote 로직 버그 수정: 한 곳만 수정하면 모든 타입에 적용
- ✅ 승인 로직 변경: 한 곳만 수정하면 모든 타입에 적용
- ✅ 테스트 작성: 공통 로직은 한 번만 테스트

### Phase 1 + Phase 2 + Phase 4 완료 시

**코드 품질**:
- ✅ 코드 라인 수: **1,377줄 → 약 600-700줄** (약 50% 감소)
- ✅ 중복 코드: **약 70% 감소**
- ✅ 파일 구조: **명확한 책임 분리**

**개발 생산성**:
- ✅ 코드 리뷰 시간 단축: 공통 로직은 한 번만 리뷰
- ✅ 병렬 작업 시 충돌 감소: 타입별 서비스로 분리
- ✅ 신규 개발자 온보딩 시간 단축: 구조가 명확해짐

---

## ⚠️ 리스크 관리

### 주요 리스크 및 대응

1. **리스크: Generic Base가 God Class로 변함**
   - **대응**: 코어 유스케이스(Vote, Approval)만 공통화, 검증/응답은 별도 컴포넌트
   - **검증**: 각 UseCase 클래스가 200줄 이하 유지

2. **리스크: 타입 안전성 손실**
   - **대응**: TypeVar와 Protocol을 적절히 사용, 타입 체크 강화
   - **검증**: mypy/pyright로 타입 체크 통과

3. **리스크: 동시성 버그 발생**
   - **대응**: Phase 0 테스트에서 동시성 시나리오 포함
   - **검증**: 조건부 UPDATE 패턴 유지, unique constraint 확인

4. **리스크: Idempotency 동작 불일치**
   - **대응**: 명시적 래핑으로 통일, 각 메서드별 idempotency 테스트
   - **검증**: 같은 key로 재요청 시 동일 결과 확인

---

## 🎯 왜 이 전략이 가장 적합한가?

### 1. 기존 아키텍처와의 일관성

- 리포지토리 레벨에서 이미 성공적으로 적용된 패턴
- 개발자들이 이미 익숙한 구조
- 학습 곡선 최소화

### 2. 점진적 리팩토링 가능

- 한 번에 모든 것을 바꾸지 않고 단계적으로 진행
- 각 단계마다 테스트 가능
- 리스크 최소화

### 3. API 호환성 유지

- Facade 패턴으로 기존 인터페이스 유지
- 라우터 레벨 변경 불필요
- 배포 리스크 최소화

### 4. 실용적인 우선순위

- P0 (Vote)부터 시작하여 가장 안전하고 효과가 큰 부분부터
- P1 (Approval)로 확장
- 선택적으로 P2 (생성)까지 진행

### 5. 리포지토리 패턴과의 대칭성

- 리포지토리: `ProposalRepositoryGeneric` + 타입별 리포지토리 + `ProposalRepository`
- 서비스: `core/` UseCase + 타입별 서비스 + `ProposalService` Facade
- 구조가 대칭적이어서 이해하기 쉬움

---

## 📝 다음 단계

1. **Phase 0 완료**: 테스트 작성 및 고정
2. **Phase 1 시작**: Vote UseCase 추출
3. **각 Phase마다**: 테스트 통과 확인 후 다음 단계 진행

---

## 🔗 참고

- 기존 리포지토리 구조: `app/repositories/proposal/`
- 기존 서비스 구조: `app/services/event/proposal_service.py`
- 의존성 주입: `app/dependencies/services.py`
