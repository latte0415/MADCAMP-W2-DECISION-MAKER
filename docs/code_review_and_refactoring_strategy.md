# 코드 평가 및 리팩토링 전략 (실전 가이드)

## 📊 현재 코드 상태 평가

### 1. 파일 크기 분석

| 파일 | 라인 수 | 상태 | 우선순위 |
|------|---------|------|----------|
| `proposal_service.py` | **1,377줄** | 🔴 매우 긴 파일 | **최우선** |
| `detail.py` (router) | 350줄 | 🟡 적당함 | 낮음 |
| `setting.py` (router) | 239줄 | 🟢 양호 | 낮음 |
| `membership_service.py` | 386줄 | 🟡 적당함 | 중간 |
| `vote_service.py` | 326줄 | 🟡 적당함 | 중간 |

### 2. 주요 문제점

#### 🔴 Critical Issues

**1. `proposal_service.py`의 과도한 길이 (1,377줄)**
- **문제**: 단일 파일에 너무 많은 책임이 집중됨
- **영향**: 
  - 코드 가독성 저하
  - 유지보수 어려움
  - 테스트 작성 어려움
  - 병렬 작업 시 충돌 가능성 증가

**2. 심각한 코드 중복**
- Assumption, Criteria, Conclusion 세 가지 타입의 Proposal 로직이 거의 동일하게 반복됨
- 각 타입마다 다음 메서드들이 거의 동일한 패턴으로 반복:
  - `create_*_proposal()` (약 80줄씩, 총 240줄)
  - `create_*_proposal_vote()` (약 45줄씩, 총 135줄)
  - `delete_*_proposal_vote()` (약 45줄씩, 총 135줄)
  - `update_*_proposal_status()` (약 110줄씩, 총 330줄)
  - 검증 메서드들 (`_validate_*_proposal_pending`, `_check_duplicate_*_vote` 등)

**3. 단일 책임 원칙(SRP) 위반**
- 하나의 서비스가 세 가지 다른 도메인(Assumption, Criteria, Conclusion)을 모두 처리
- 각 도메인별로 다른 비즈니스 로직이 있을 수 있음

#### 🟡 Medium Issues

**4. 메서드 길이**
- 일부 메서드가 100줄 이상 (예: `update_*_proposal_status`)
- 내부 함수(`_execute_*`)로 분리되어 있지만 여전히 길음

**5. Idempotency 로직 중복**
- 모든 생성/수정 메서드에 동일한 idempotency 패턴이 반복됨

## 🎯 리팩토링 전략 평가

### 현재 전략 평가: 무엇이 좋고, 무엇이 위험한가

#### ✅ 좋은 점

1. **Facade 패턴으로 기존 API 유지**: 라우터 레벨 변경 없이 리팩토링 가능
2. **타입별 특화 지점 분리**: `validate_content_for_proposal`, `apply_proposal` 같은 도메인 특화 로직만 하위 클래스에 유지
3. **점진적 리팩토링 가능**: 한 번에 모든 것을 바꾸지 않고 단계적으로 진행 가능

#### ⚠️ 위험한 점 (중요)

1. **Generic Base Service가 "더 큰 God Class"로 변할 위험**
   - 공통 메서드 범위(생성/투표/상태변경/검증/응답빌더/idem)를 전부 Base로 넣으면
   - 파일은 쪼개졌지만 복잡도는 그대로인 상태가 됨
   - **해결책**: "코어 유스케이스 단위"로만 베이스를 잡고, 검증/응답은 별도 컴포넌트로 분리

2. **Repository 제너릭화 ≠ Service 제너릭화**
   - 서비스는 정책/규칙이 섞여서, 제너릭화는 **핵심 흐름(투표→승인 시도→outbox)** 정도까지만 안전
   - `create_proposal` 같은 건 타입별 분기가 생기기 쉬워서, 무리하게 공통화하면 config가 비대해짐

3. **Idempotency 데코레이터의 부작용**
   - 메서드 시그니처/에러 처리/응답 캐시 정책이 엔드포인트마다 다르면 데코레이터가 오히려 어려워짐
   - **추천**: 데코레이터보다는 `IdempotencyService.run(...)` 형태의 "명시적 래핑"을 먼저 적용

4. **일정의 낙관성**
   - "1~2일에 공통 로직 추출"은 실제로 가장 오래 걸리는 구간
   - 리스크는 기술이 아니라 "변경 범위와 테스트 준비 부족"에서 발생

---

## 🎯 개선된 리팩토링 전략 (성공 확률 높게)

### 전략 1: 코어 유스케이스 중심 분리 (권장)

**목표**: 중복 코드를 제거하되, God Class를 만들지 않도록 책임을 세밀하게 분리

#### 개선된 구조

```
app/services/event/proposal/
├── __init__.py
├── facade.py                      # 기존 ProposalService API 유지 (얇은 Facade)
├── core.py                        # 공통 흐름만 (투표/승인/idem/outbox)
├── configs.py                     # 타입별 설정/훅(callable) 정의
├── types.py                       # Protocol/TypeVar/DTO
├── assumption_service.py          # 얇은 래퍼 + 타입별 검증/적용
├── criteria_service.py
├── conclusion_service.py
├── validators/                    # (선택) 공통/타입별 validator 모음
│   ├── __init__.py
│   ├── common.py
│   └── type_specific.py
└── builders/                      # (선택) 응답 builder
    ├── __init__.py
    └── response_builder.py
```

**핵심 원칙**: `core.py`가 "거대한 베이스 클래스"가 아니라, **유스케이스 함수/클래스** 중심으로 작게 유지

```python
# core.py 예시 구조
class VoteUseCase:
    """투표 생성/삭제 공통 로직"""
    def create_vote(self, ...): ...
    def delete_vote(self, ...): ...

class ApprovalUseCase:
    """승인/거절 상태 변경 공통 로직"""
    def approve_if_pending(self, ...): ...
    def reject_if_pending(self, ...): ...

class IdempotencyWrapper:
    """Idempotency 명시적 래핑"""
    def wrap(self, fn, ...): ...
```

---

### 제너릭화 우선순위 (가장 큰 중복부터, 실패 리스크 낮게)

#### P0: Vote 흐름 제너릭화 (가장 추천, 최우선)

**대상 메서드**:
- `create_*_proposal_vote()` (3개, 각 45줄)
- `delete_*_proposal_vote()` (3개, 각 45줄)
- `_check_duplicate_*_vote()` (3개)
- `_get_user_*_vote_or_raise()` (3개)

**왜 안전한가?**
- 타입 차이가 "vote FK 필드명 + 모델 클래스" 정도라 제너릭화 효과가 크고 안전함
- 비즈니스 로직이 거의 동일함

**예상 효과**: 약 270줄 → 약 100줄 (약 63% 감소)

#### P1: 승인/거절 상태 변경(조건부 UPDATE) 흐름 공통화

**대상 메서드**:
- `update_*_proposal_status()` (3개, 각 110줄)
- `_check_and_auto_approve_*_proposal()` (3개)
- `approve_*_if_pending()` (repository 레벨)
- `reject_*_if_pending()` (repository 레벨)

**왜 안전한가?**
- 조건부 UPDATE 패턴이 동일함
- 상태 전이 검증 로직이 유사함
- P0 완료 후 안정적으로 가능

**예상 효과**: 약 330줄 → 약 150줄 (약 55% 감소)

#### P2: Proposal 생성 공통화는 마지막에 (또는 부분 공통화)

**대상 메서드**:
- `create_*_proposal()` (3개, 각 80줄)
- `_validate_*_proposal_category_fields()` (3개)
- `_validate_*_for_proposal()` (3개)

**왜 마지막인가?**
- 생성은 "도메인 검증/중복 체크/카테고리 필드 규칙/대상 콘텐츠"가 섞여서 타입별 예외가 늘기 쉬움
- 여기까지 제너릭으로 밀면 config가 커지고 유지보수성이 떨어질 수 있음

**추천 접근**:
- 생성은 "공통 뼈대(트랜잭션, idem, pending 중복 체크 프레임)"만 공유
- 나머지는 타입별로 남기기

**예상 효과**: 약 240줄 → 약 180줄 (약 25% 감소, 부분 공통화)

---

### 전략 2/3에 대한 판단

**전략 2 (도메인별 완전 분리)**:
- ❌ 최종 형태로는 좋지만, 지금 단계에서 "7~10일"로 끝내기 어려움
- ❌ 중간에 API 호환성 깨질 확률이 큼
- ✅ 장기적으로는 고려할 만함

**전략 3 (Strategy/Factory)**:
- ❌ 런타임 분기 설계라 타입 안정성/정적 분석 이점이 줄어듦
- ❌ 지금 목표(중복 제거 + 안정 배포)에는 전략 1이 더 적합

---

## 📋 단계별 실행 계획 (우선순위 기반)

### Phase 0: 테스트 준비 (필수, 2-3일)

**목표**: 리팩토링 전후 동일하게 통과해야 할 테스트 고정

#### 반드시 포함할 최소 테스트

1. **Vote 동시성 테스트**
   ```python
   def test_concurrent_vote_creation():
       """동시에 같은 proposal에 투표 시도 시 unique constraint 보장"""
       # 같은 proposal_id, 같은 user_id로 동시 요청
       # 하나만 성공, 나머지는 ConflictError
   ```

2. **Idempotency 테스트**
   ```python
   def test_idempotency_same_key():
       """같은 idempotency_key로 재요청 시 동일 결과 반환"""
       # 첫 요청과 두 번째 요청의 proposal_id가 동일해야 함
   ```

3. **승인 상태 전이 테스트**
   ```python
   def test_concurrent_approval():
       """동시에 같은 proposal 승인 시도 시 1회만 성공"""
       # 조건부 UPDATE로 중복 승인 방지 확인
   ```

4. **Proposal 생성 중복 체크**
   ```python
   def test_duplicate_proposal_prevention():
       """같은 assumption_id + user_id로 PENDING proposal 중복 생성 방지"""
   ```

**이 테스트가 없으면 Phase 1~4에서 리팩토링이 계속 흔들립니다.**

---

### Phase 1: P0 - Vote 흐름 제너릭화 (3-4일)

**목표**: 가장 안전하고 효과가 큰 Vote 로직부터 공통화

#### 작업 단위

1. **`core/vote_usecase.py` 생성** (1일)
   ```python
   class VoteUseCase:
       """투표 생성/삭제 공통 로직"""
       def create_vote(
           self,
           proposal_id: UUID,
           user_id: UUID,
           vote_model_class: Type[TVote],
           get_proposal_fn: Callable,
           create_vote_fn: Callable,
           check_duplicate_fn: Callable,
           auto_approve_fn: Callable,
       ): ...
       
       def delete_vote(...): ...
   ```

2. **타입별 Vote 메서드를 UseCase로 교체** (1-2일)
   - `create_assumption_proposal_vote()` → `VoteUseCase.create_vote()` 호출
   - `create_criteria_proposal_vote()` → `VoteUseCase.create_vote()` 호출
   - `create_conclusion_proposal_vote()` → `VoteUseCase.create_vote()` 호출
   - delete 메서드들도 동일하게 교체

3. **테스트 통과 확인** (0.5일)
   - Phase 0에서 작성한 테스트 모두 통과 확인
   - 기존 통합 테스트도 통과 확인

**체크리스트**:
- [ ] `core/vote_usecase.py` 생성 완료
- [ ] 6개 Vote 메서드(create 3개 + delete 3개)가 UseCase 사용하도록 변경
- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료

---

### Phase 2: P1 - 승인/거절 상태 변경 공통화 (3-4일)

**목표**: 조건부 UPDATE 패턴 공통화

#### 작업 단위

1. **`core/approval_usecase.py` 생성** (1일)
   ```python
   class ApprovalUseCase:
       """승인/거절 상태 변경 공통 로직"""
       def approve_if_pending(
           self,
           proposal_id: UUID,
           approve_fn: Callable,
           apply_fn: Callable,
       ): ...
       
       def reject_if_pending(...): ...
   ```

2. **`core/auto_approval.py` 생성** (1일)
   ```python
   class AutoApprovalChecker:
       """자동 승인 로직 공통화"""
       def check_and_auto_approve(
           self,
           proposal: TProposal,
           event: Event,
           vote_count: int,
           min_votes_required: int | None,
           is_auto_approved: bool,
           approve_fn: Callable,
           apply_fn: Callable,
       ): ...
   ```

3. **타입별 상태 변경 메서드를 UseCase로 교체** (1-2일)
   - `update_*_proposal_status()` → `ApprovalUseCase` 사용
   - `_check_and_auto_approve_*_proposal()` → `AutoApprovalChecker` 사용

4. **테스트 통과 확인** (0.5일)

**체크리스트**:
- [ ] `core/approval_usecase.py` 생성 완료
- [ ] `core/auto_approval.py` 생성 완료
- [ ] 3개 status update 메서드가 UseCase 사용하도록 변경
- [ ] 3개 auto_approve 메서드가 Checker 사용하도록 변경
- [ ] 모든 테스트 통과

---

### Phase 3: Idempotency 명시적 래핑 통일 (2일)

**목표**: 데코레이터 대신 명시적 래핑으로 통일

#### 작업 단위

1. **`core/idempotency_wrapper.py` 생성** (0.5일)
   ```python
   class IdempotencyWrapper:
       """Idempotency 명시적 래핑 헬퍼"""
       def wrap(
           self,
           idempotency_service: IdempotencyService | None,
           idempotency_key: str | None,
           user_id: UUID,
           method: str,
           path: str,
           body: dict,
           fn: Callable,
       ):
           if idempotency_service and idempotency_key:
               return idempotency_service.run(
                   user_id=user_id,
                   key=idempotency_key,
                   method=method,
                   path=path,
                   body=body,
                   fn=fn
               )
           else:
               return fn()
   ```

2. **모든 생성/수정 메서드에 래퍼 적용** (1일)
   - `create_*_proposal()` 메서드들
   - `update_*_proposal_status()` 메서드들
   - 기존 idempotency 로직을 `IdempotencyWrapper.wrap()` 호출로 교체

3. **테스트 통과 확인** (0.5일)

**체크리스트**:
- [ ] `core/idempotency_wrapper.py` 생성 완료
- [ ] 6개 메서드(create 3개 + update 3개)에 래퍼 적용
- [ ] 모든 테스트 통과
- [ ] Idempotency 동작 확인

---

### Phase 4: P2 - Proposal 생성 부분 공통화 (2-3일, 선택)

**목표**: 생성 로직의 공통 뼈대만 공유

#### 작업 단위

1. **`core/proposal_creation.py` 생성** (1일)
   ```python
   class ProposalCreationUseCase:
       """Proposal 생성 공통 뼈대"""
       def create_proposal(
           self,
           event_id: UUID,
           user_id: UUID,
           validate_fn: Callable,
           check_duplicate_fn: Callable,
           create_proposal_fn: Callable,
           build_response_fn: Callable,
       ): ...
   ```

2. **타입별 생성 메서드 리팩토링** (1-2일)
   - 공통 뼈대는 `ProposalCreationUseCase` 사용
   - 타입별 검증/응답 빌더는 각 서비스에 유지

**주의**: 이 단계는 선택사항. P0, P1만으로도 충분한 효과가 있음.

**체크리스트**:
- [ ] `core/proposal_creation.py` 생성 완료
- [ ] 3개 create 메서드가 UseCase 사용하도록 변경 (부분 공통화)
- [ ] 모든 테스트 통과

---

### Phase 5: Facade 패턴 적용 및 최종 정리 (2일)

**목표**: 기존 API 호환성 유지하면서 구조 정리

#### 작업 단위

1. **타입별 서비스 클래스 생성** (1일)
   ```python
   # assumption_service.py
   class AssumptionProposalService:
       """Assumption Proposal 전용 서비스"""
       def __init__(self, db, repos, vote_usecase, approval_usecase, ...):
           self.vote_usecase = vote_usecase
           self.approval_usecase = approval_usecase
           # ...
       
       def create_proposal(self, ...):
           # ProposalCreationUseCase 사용
       # ...
   ```

2. **Facade Service 생성** (0.5일)
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
       # ...
   ```

3. **의존성 주입 업데이트** (0.5일)
   - `app/dependencies/services.py`에서 새로운 구조로 변경
   - 기존 라우터는 변경 없음

4. **최종 테스트 및 문서화** (0.5일)

**체크리스트**:
- [ ] 3개 타입별 서비스 클래스 생성
- [ ] Facade Service 생성 및 기존 인터페이스 유지
- [ ] 의존성 주입 업데이트
- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 문서 업데이트

---

**총 예상 시간**: 약 12-16일 (테스트 포함)

**실제 일정 팁**:
- Phase 0(테스트)는 반드시 먼저 완료
- Phase 1, 2는 순차적으로 진행 (P0 완료 후 P1)
- Phase 3은 Phase 1, 2와 병렬 가능
- Phase 4는 선택사항 (효과 대비 노력 고려)
- Phase 5는 모든 Phase 완료 후 진행

---

## 🔍 구현 세부사항

### 1. Idempotency 명시적 래핑 (데코레이터 금지)

**1단계(권장): 명시적 래핑으로 통일**

```python
# core/idempotency_wrapper.py
class IdempotencyWrapper:
    """Idempotency 명시적 래핑 헬퍼"""
    
    def __init__(self, idempotency_service: IdempotencyService | None):
        self.idempotency_service = idempotency_service
    
    def wrap(
        self,
        idempotency_key: str | None,
        user_id: UUID,
        method: str,
        path: str,
        body: dict,
        fn: Callable[[], dict],
    ) -> dict:
        """Idempotency 래핑"""
        if self.idempotency_service and idempotency_key:
            return self.idempotency_service.run(
                user_id=user_id,
                key=idempotency_key,
                method=method,
                path=path,
                body=body,
                fn=fn
            )
        else:
            return fn()

# 사용 예시
def create_assumption_proposal(self, ..., idempotency_key: str | None = None):
    def _execute_create() -> dict:
        # 실제 로직
        return response.model_dump()
    
    result = self.idempotency_wrapper.wrap(
        idempotency_key=idempotency_key,
        user_id=user_id,
        method="POST",
        path=f"/events/{event_id}/assumption-proposals",
        body=request.model_dump(exclude_none=True),
        fn=_execute_create
    )
    return AssumptionProposalResponse(**result)
```

**2단계(선택, 안정화 후)**: 데코레이터로 올리기
- 데코레이터는 나중에 예외 케이스를 먹고 커지기 쉬워서, 처음부터 도입하면 디버깅이 힘듦
- 명시적 래핑이 안정화된 후 고려

### 2. 검증 로직 분리 (선택사항)

```python
# validators/common.py
class CommonProposalValidator:
    """공통 Proposal 검증 로직"""
    
    @staticmethod
    def validate_proposal_pending(proposal, event_id, operation: str):
        """PENDING 상태 검증 (공통)"""
        if proposal.proposal_status != ProposalStatusType.PENDING:
            raise ValidationError(...)

# validators/type_specific.py
class AssumptionProposalValidator:
    """Assumption 특화 검증"""
    
    @staticmethod
    def validate_category_fields(request, event_id):
        """Assumption 특화 카테고리 필드 검증"""
        # 타입별 특화 로직
```

### 3. 응답 생성 로직 분리 (선택사항)

```python
# builders/response_builder.py
class ProposalResponseBuilder:
    """Proposal 응답 생성"""
    
    @staticmethod
    def build_assumption_response(proposal, user_id, vote_count: int):
        """Assumption Proposal 응답 생성"""
        has_voted = any(vote.created_by == user_id for vote in (proposal.votes or []))
        return AssumptionProposalResponse(
            id=proposal.id,
            # ...
            vote_count=vote_count,
            has_voted=has_voted,
        )
```

---

## ⚠️ 주의사항 및 리스크 관리

### 필수 주의사항

1. **기존 API 호환성 유지**: 라우터 레벨에서는 변경 없이 유지
2. **점진적 리팩토링**: 한 번에 모든 것을 바꾸지 말고 단계적으로 진행
3. **테스트 우선**: Phase 0의 테스트를 먼저 고정하고, 각 Phase마다 테스트 통과 확인
4. **의존성 주입**: 기존 DI 구조를 유지하면서 리팩토링

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

## 📈 예상 효과 (우선순위 기반)

### P0 + P1 완료 시 (Phase 1, 2 완료)

**코드 품질**:
- ✅ 코드 라인 수: **1,377줄 → 약 800-900줄** (약 35-40% 감소)
- ✅ 중복 코드: **약 50-60% 감소** (Vote + Approval)
- ✅ 순환 복잡도: **크게 감소**

**유지보수성**:
- ✅ Vote 로직 버그 수정: 한 곳만 수정하면 모든 타입에 적용
- ✅ 승인 로직 변경: 한 곳만 수정하면 모든 타입에 적용
- ✅ 테스트 작성: 공통 로직은 한 번만 테스트

### P0 + P1 + P2 완료 시 (Phase 1, 2, 4 완료)

**코드 품질**:
- ✅ 코드 라인 수: **1,377줄 → 약 600-700줄** (약 50% 감소)
- ✅ 중복 코드: **약 70% 감소**
- ✅ 순환 복잡도: **크게 감소**

**유지보수성**:
- ✅ 새로운 Proposal 타입 추가 시: UseCase 재사용으로 빠른 개발
- ✅ 버그 수정: 한 곳만 수정하면 모든 타입에 적용
- ✅ 테스트 작성: 공통 로직은 한 번만 테스트

### 개발 생산성

- ✅ 코드 리뷰 시간 단축: 공통 로직은 한 번만 리뷰
- ✅ 병렬 작업 시 충돌 감소: 타입별 서비스로 분리
- ✅ 신규 개발자 온보딩 시간 단축: 구조가 명확해짐

---

## 📝 작업 단위별 체크리스트 및 구현 가이드

### Phase 0: 테스트 준비

- [ ] `test_vote_concurrency()` 작성
- [ ] `test_idempotency_same_key()` 작성
- [ ] `test_concurrent_approval()` 작성
- [ ] `test_duplicate_proposal_prevention()` 작성
- [ ] 모든 테스트 통과 확인

**구현 예시**:
```python
# tests/test_proposal_concurrency.py
def test_vote_concurrency(db_session, event, proposal, user):
    """동시에 같은 proposal에 투표 시도 시 unique constraint 보장"""
    import threading
    
    results = []
    errors = []
    
    def vote():
        try:
            service.create_assumption_proposal_vote(
                event_id=event.id,
                proposal_id=proposal.id,
                user_id=user.id
            )
            results.append("success")
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=vote) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # 하나만 성공, 나머지는 ConflictError
    assert len(results) == 1
    assert len([e for e in errors if "Already voted" in e]) == 2
```

### Phase 1: P0 - Vote 흐름 제너릭화

- [ ] `core/vote_usecase.py` 생성
- [ ] `create_assumption_proposal_vote()` → UseCase 사용
- [ ] `create_criteria_proposal_vote()` → UseCase 사용
- [ ] `create_conclusion_proposal_vote()` → UseCase 사용
- [ ] `delete_assumption_proposal_vote()` → UseCase 사용
- [ ] `delete_criteria_proposal_vote()` → UseCase 사용
- [ ] `delete_conclusion_proposal_vote()` → UseCase 사용
- [ ] 모든 테스트 통과

**구현 예시 - `core/vote_usecase.py`**:
```python
from typing import Callable, TypeVar, Type
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.proposal import ProposalStatusType
from app.exceptions import NotFoundError, ConflictError
from app.utils.transaction import transaction

TProposal = TypeVar('TProposal')
TVote = TypeVar('TVote')

class VoteUseCase:
    """투표 생성/삭제 공통 로직"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID,
        # 타입별 의존성 주입
        vote_model_class: Type[TVote],
        get_proposal_fn: Callable[[UUID, UUID], TProposal],
        create_vote_fn: Callable[[TVote], TVote],
        check_duplicate_fn: Callable[[UUID, UUID], None],
        auto_approve_fn: Callable[[TProposal, Event], None],
        validate_event_fn: Callable[[UUID, str], Event],
        build_response_fn: Callable[[TVote, TProposal], dict],
    ) -> dict:
        """
        투표 생성 공통 로직
        
        Args:
            vote_model_class: Vote 모델 클래스 (AssumptionProposalVote 등)
            get_proposal_fn: proposal 조회 함수 (타입별)
            create_vote_fn: vote 생성 함수 (타입별)
            check_duplicate_fn: 중복 투표 체크 함수 (타입별)
            auto_approve_fn: 자동 승인 체크 함수 (타입별)
            validate_event_fn: 이벤트 검증 함수
            build_response_fn: 응답 생성 함수 (타입별)
        """
        # 1. 이벤트 상태 검증 (IN_PROGRESS)
        event = validate_event_fn(event_id, "create votes")
        
        # 2. 제안 존재 및 상태 검증
        proposal = get_proposal_fn(proposal_id, event_id)
        if proposal.proposal_status != ProposalStatusType.PENDING:
            raise ValidationError(
                message="Proposal not pending",
                detail="create votes can only be performed for PENDING proposals"
            )
        
        # 3. 중복 투표 체크
        check_duplicate_fn(proposal_id, user_id)
        
        # 4. 투표 생성 및 자동 승인 체크
        vote = vote_model_class(
            **{f"{vote_model_class.__name__.lower().replace('proposalvote', '_proposal_id')}": proposal_id},
            created_by=user_id,
        )
        with transaction(self.db):
            created_vote = create_vote_fn(vote)
            self.db.refresh(proposal, ['votes'])
            vote_count = len(proposal.votes) if proposal.votes else 0
            
            # 자동 승인 로직 체크
            auto_approve_fn(proposal, event)
        
        # refresh 후 vote_count 다시 계산
        self.db.refresh(proposal, ['votes'])
        vote_count = len(proposal.votes) if proposal.votes else 0
        
        return build_response_fn(created_vote, proposal, vote_count)
    
    def delete_vote(
        self,
        event_id: UUID,
        proposal_id: UUID,
        user_id: UUID,
        # 타입별 의존성 주입
        get_proposal_fn: Callable[[UUID, UUID], TProposal],
        get_vote_fn: Callable[[UUID, UUID], TVote],
        delete_vote_fn: Callable[[TVote], None],
        auto_approve_fn: Callable[[TProposal, Event], None],
        validate_event_fn: Callable[[UUID, str], Event],
        build_response_fn: Callable[[TVote, TProposal], dict],
    ) -> dict:
        """투표 삭제 공통 로직"""
        # 1. 이벤트 상태 검증
        event = validate_event_fn(event_id, "delete votes")
        
        # 2. 제안 존재 및 상태 검증
        proposal = get_proposal_fn(proposal_id, event_id)
        if proposal.proposal_status != ProposalStatusType.PENDING:
            raise ValidationError(...)
        
        # 3. 투표 존재 및 소유권 검증
        vote = get_vote_fn(proposal_id, user_id)
        if not vote:
            raise NotFoundError(...)
        
        # 4. 투표 삭제 및 자동 승인 재체크
        with transaction(self.db):
            delete_vote_fn(vote)
            self.db.refresh(proposal, ['votes'])
            vote_count = len(proposal.votes) if proposal.votes else 0
            
            auto_approve_fn(proposal, event)
        
        self.db.refresh(proposal, ['votes'])
        vote_count = len(proposal.votes) if proposal.votes else 0
        
        return build_response_fn(vote, proposal, vote_count)
```

**사용 예시 - `assumption_service.py`**:
```python
class AssumptionProposalService:
    def __init__(self, db, repos, vote_usecase):
        self.db = db
        self.repos = repos
        self.vote_usecase = vote_usecase
    
    def create_vote(self, event_id, proposal_id, user_id):
        return self.vote_usecase.create_vote(
            event_id=event_id,
            proposal_id=proposal_id,
            user_id=user_id,
            vote_model_class=AssumptionProposalVote,
            get_proposal_fn=self._get_proposal,
            create_vote_fn=self.repos.proposal.create_assumption_proposal_vote,
            check_duplicate_fn=self._check_duplicate,
            auto_approve_fn=self._check_and_auto_approve,
            validate_event_fn=self._validate_event_in_progress,
            build_response_fn=self._build_vote_response,
        )
    
    def _get_proposal(self, proposal_id, event_id):
        return self.repos.proposal.get_assumption_proposal_by_id(proposal_id)
    
    def _check_duplicate(self, proposal_id, user_id):
        existing = self.repos.proposal.get_user_vote_on_assumption_proposal(proposal_id, user_id)
        if existing:
            raise ConflictError(...)
    
    def _check_and_auto_approve(self, proposal, event):
        # Assumption 특화 자동 승인 로직
        ...
    
    def _build_vote_response(self, vote, proposal, vote_count):
        return AssumptionProposalVoteResponse(
            message="Vote created successfully",
            vote_id=vote.id,
            proposal_id=proposal.id,
            vote_count=vote_count,
        ).model_dump()
```

### Phase 2: P1 - 승인/거절 상태 변경 공통화

- [ ] `core/approval_usecase.py` 생성
- [ ] `core/auto_approval.py` 생성
- [ ] `update_assumption_proposal_status()` → UseCase 사용
- [ ] `update_criteria_proposal_status()` → UseCase 사용
- [ ] `update_conclusion_proposal_status()` → UseCase 사용
- [ ] `_check_and_auto_approve_assumption_proposal()` → Checker 사용
- [ ] `_check_and_auto_approve_criteria_proposal()` → Checker 사용
- [ ] `_check_and_auto_approve_conclusion_proposal()` → Checker 사용
- [ ] 모든 테스트 통과

**구현 예시 - `core/approval_usecase.py`**:
```python
from typing import Callable, TypeVar
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.proposal import ProposalStatusType
from app.exceptions import ConflictError, ValidationError
from app.utils.transaction import transaction

TProposal = TypeVar('TProposal')

class ApprovalUseCase:
    """승인/거절 상태 변경 공통 로직"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_status(
        self,
        event_id: UUID,
        proposal_id: UUID,
        status: ProposalStatusType,
        user_id: UUID,
        # 타입별 의존성 주입
        verify_admin_fn: Callable[[UUID, UUID], Event],
        get_proposal_fn: Callable[[UUID], TProposal],
        validate_proposal_belongs_to_event_fn: Callable[[TProposal, UUID], None],
        approve_if_pending_fn: Callable[[UUID, datetime], TProposal | None],
        reject_if_pending_fn: Callable[[UUID], TProposal | None],
        apply_proposal_fn: Callable[[TProposal, Event], None],
        build_response_fn: Callable[[TProposal, UUID], dict],
    ) -> dict:
        """
        Proposal 상태 변경 공통 로직
        
        Args:
            verify_admin_fn: 관리자 권한 확인 함수
            get_proposal_fn: proposal 조회 함수 (타입별)
            validate_proposal_belongs_to_event_fn: proposal이 event에 속하는지 검증
            approve_if_pending_fn: 조건부 승인 함수 (repository 레벨)
            reject_if_pending_fn: 조건부 거절 함수 (repository 레벨)
            apply_proposal_fn: 제안 적용 함수 (타입별)
            build_response_fn: 응답 생성 함수 (타입별)
        """
        if status not in (ProposalStatusType.ACCEPTED, ProposalStatusType.REJECTED):
            raise ValidationError(
                message="Invalid status",
                detail="Status must be ACCEPTED or REJECTED"
            )
        
        # 1. 관리자 권한 확인
        event = verify_admin_fn(event_id, user_id)
        
        # 2. 제안 조회 및 검증
        proposal = get_proposal_fn(proposal_id)
        if not proposal:
            raise NotFoundError(...)
        
        validate_proposal_belongs_to_event_fn(proposal, event_id)
        
        # 3. 조건부 UPDATE로 상태 변경 (원자성 보장)
        with transaction(self.db):
            if status == ProposalStatusType.ACCEPTED:
                accepted_at = datetime.now(timezone.utc)
                updated_proposal = approve_if_pending_fn(proposal_id, accepted_at)
            else:
                updated_proposal = reject_if_pending_fn(proposal_id)
            
            # 조건부 UPDATE 실패 처리
            if updated_proposal is None:
                self.db.refresh(proposal, ['votes'])
                if proposal.proposal_status == ProposalStatusType.ACCEPTED:
                    raise ConflictError(message="Proposal already accepted", ...)
                elif proposal.proposal_status == ProposalStatusType.REJECTED:
                    raise ConflictError(message="Proposal already rejected", ...)
                else:
                    raise ConflictError(message="Proposal status changed", ...)
            
            # 조건부 UPDATE 성공한 경우에만 후속 처리
            proposal = updated_proposal
            if status == ProposalStatusType.ACCEPTED:
                apply_proposal_fn(proposal, event)
            
            # 응답 생성을 위해 refresh
            self.db.refresh(proposal, ['votes'])
        
        return build_response_fn(proposal, user_id)
```

**구현 예시 - `core/auto_approval.py`**:
```python
from typing import Callable, TypeVar
from app.models.event import Event
from app.models.proposal import ProposalStatusType

TProposal = TypeVar('TProposal')

class AutoApprovalChecker:
    """자동 승인 로직 공통화"""
    
    @staticmethod
    def check_and_auto_approve(
        proposal: TProposal,
        event: Event,
        vote_count: int,
        min_votes_required: int | None,
        is_auto_approved: bool,
        approval_threshold_percent: float | None,  # Conclusion용
        total_members: int | None,  # Conclusion용
        approve_if_pending_fn: Callable[[UUID, datetime], TProposal | None],
        apply_proposal_fn: Callable[[TProposal, Event], None],
        db_refresh_fn: Callable[[TProposal, list], None],
    ) -> None:
        """
        자동 승인 체크 공통 로직
        
        Args:
            proposal: Proposal 객체
            event: Event 객체
            vote_count: 현재 투표 수
            min_votes_required: 최소 투표 수 (Assumption/Criteria용)
            is_auto_approved: 자동 승인 활성화 여부
            approval_threshold_percent: 승인 임계값 퍼센트 (Conclusion용)
            total_members: 전체 멤버 수 (Conclusion용)
            approve_if_pending_fn: 조건부 승인 함수
            apply_proposal_fn: 제안 적용 함수
            db_refresh_fn: DB refresh 함수
        """
        # PENDING 상태가 아니면 자동 승인 로직 적용하지 않음
        if proposal.proposal_status != ProposalStatusType.PENDING:
            return
        
        if not is_auto_approved:
            return
        
        # Assumption/Criteria: 투표 수 기반
        if min_votes_required is not None:
            if vote_count >= min_votes_required:
                accepted_at = datetime.now(timezone.utc)
                approved_proposal = approve_if_pending_fn(proposal.id, accepted_at)
                if approved_proposal:
                    db_refresh_fn(approved_proposal, ['votes', 'assumption'])  # 타입별
                    apply_proposal_fn(approved_proposal, event)
        
        # Conclusion: 비율 기반
        elif approval_threshold_percent is not None and total_members is not None:
            if total_members == 0:
                return
            vote_percent = (vote_count / total_members) * 100
            if vote_percent >= approval_threshold_percent:
                accepted_at = datetime.now(timezone.utc)
                approved_proposal = approve_if_pending_fn(proposal.id, accepted_at)
                if approved_proposal:
                    db_refresh_fn(approved_proposal, ['votes', 'criterion'])
                    apply_proposal_fn(approved_proposal, event)
```

### Phase 3: Idempotency 명시적 래핑

- [ ] `core/idempotency_wrapper.py` 생성
- [ ] `create_assumption_proposal()` → Wrapper 사용
- [ ] `create_criteria_proposal()` → Wrapper 사용
- [ ] `create_conclusion_proposal()` → Wrapper 사용
- [ ] `update_assumption_proposal_status()` → Wrapper 사용
- [ ] `update_criteria_proposal_status()` → Wrapper 사용
- [ ] `update_conclusion_proposal_status()` → Wrapper 사용
- [ ] 모든 테스트 통과

### Phase 4: P2 - Proposal 생성 부분 공통화 (선택)

- [ ] `core/proposal_creation.py` 생성
- [ ] `create_assumption_proposal()` → UseCase 사용 (부분)
- [ ] `create_criteria_proposal()` → UseCase 사용 (부분)
- [ ] `create_conclusion_proposal()` → UseCase 사용 (부분)
- [ ] 모든 테스트 통과

### Phase 5: Facade 패턴 적용

- [ ] `assumption_service.py` 생성
- [ ] `criteria_service.py` 생성
- [ ] `conclusion_service.py` 생성
- [ ] `facade.py` 생성 (기존 ProposalService)
- [ ] `app/dependencies/services.py` 업데이트
- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 문서 업데이트
