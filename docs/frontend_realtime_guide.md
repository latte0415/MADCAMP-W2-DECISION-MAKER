# 프론트엔드 실시간 동기화 가이드

이벤트의 Proposal 투표 수, 승인/기각 상태 변경, 새로운 Proposal 생성, 코멘트 추가 등을 실시간으로 받아오는 방법을 설명합니다.

## 개요

백엔드는 **Server-Sent Events (SSE)**를 통해 실시간 업데이트를 제공합니다. SSE는 단방향 통신(서버 → 클라이언트)이며, WebSocket보다 간단하고 HTTP 기반입니다.

### 지원하는 이벤트 타입

- `proposal.created.v1`: Proposal 생성
- `proposal.vote.created.v1`: Proposal 투표 생성
- `proposal.vote.deleted.v1`: Proposal 투표 삭제
- `proposal.approved.v1`: Proposal 승인
- `proposal.rejected.v1`: Proposal 거부
- `comment.created.v1`: 코멘트 생성

---

## 기본 사용법

### 1. EventSource를 사용한 연결

```typescript
// SSE 연결 생성
const eventSource = new EventSource(
  `/v1/events/${eventId}/stream`,
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    }
  }
);

// 이벤트 수신
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received event:', data);
  
  // 이벤트 타입별 처리
  switch (data.event_type) {
    case 'proposal.created.v1':
      handleProposalCreated(data);
      break;
    case 'proposal.vote.created.v1':
      handleVoteCreated(data);
      break;
    case 'proposal.vote.deleted.v1':
      handleVoteDeleted(data);
      break;
    case 'proposal.approved.v1':
      handleProposalApproved(data);
      break;
    case 'proposal.rejected.v1':
      handleProposalRejected(data);
      break;
    case 'comment.created.v1':
      handleCommentCreated(data);
      break;
  }
};

// 에러 처리
eventSource.onerror = (error) => {
  console.error('SSE connection error:', error);
  // 연결 재시도는 EventSource가 자동으로 처리
};

// 연결 종료
eventSource.close();
```

**주의**: 기본 `EventSource`는 커스텀 헤더를 지원하지 않습니다. Fetch API를 사용한 커스텀 구현이 필요합니다.

---

## Fetch API를 사용한 커스텀 구현

### 1. 기본 SSE 클라이언트 구현

```typescript
class SSEClient {
  private eventSource: ReadableStreamDefaultReader<Uint8Array> | null = null;
  private lastEventId: string | null = null;
  private controller: AbortController | null = null;
  
  constructor(
    private url: string,
    private options: {
      headers?: HeadersInit;
      onMessage?: (data: any) => void;
      onError?: (error: Error) => void;
      onOpen?: () => void;
    }
  ) {}
  
  async connect() {
    try {
      // 마지막 이벤트 ID가 있으면 헤더에 포함
      const headers = new Headers(this.options.headers);
      if (this.lastEventId) {
        headers.set('Last-Event-ID', this.lastEventId);
      }
      
      this.controller = new AbortController();
      
      const response = await fetch(this.url, {
        method: 'GET',
        headers,
        signal: this.controller.signal,
      });
      
      if (!response.ok) {
        throw new Error(`SSE connection failed: ${response.status}`);
      }
      
      if (!response.body) {
        throw new Error('Response body is null');
      }
      
      this.options.onOpen?.();
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 마지막 불완전한 줄은 버퍼에 보관
        
        let eventData: any = {};
        let eventType = 'message';
        let eventId: string | null = null;
        
        for (const line of lines) {
          if (line.startsWith('id:')) {
            eventId = line.substring(3).trim();
            this.lastEventId = eventId;
          } else if (line.startsWith('event:')) {
            eventType = line.substring(6).trim();
          } else if (line.startsWith('data:')) {
            const data = line.substring(5).trim();
            if (data) {
              try {
                eventData = JSON.parse(data);
              } catch (e) {
                // JSON 파싱 실패 시 문자열로 처리
                eventData = data;
              }
            }
          } else if (line.startsWith('retry:')) {
            const retryMs = parseInt(line.substring(6).trim(), 10);
            // 재시도 간격 설정 (필요시 구현)
          } else if (line.trim() === '' && Object.keys(eventData).length > 0) {
            // 빈 줄은 이벤트 구분자
            if (eventType === 'message' || eventType === '') {
              this.options.onMessage?.(eventData);
            }
            eventData = {};
            eventType = 'message';
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // 연결 종료 (정상)
        return;
      }
      this.options.onError?.(error as Error);
    }
  }
  
  disconnect() {
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }
    if (this.eventSource) {
      this.eventSource.cancel();
      this.eventSource = null;
    }
  }
  
  getLastEventId(): string | null {
    return this.lastEventId;
  }
  
  setLastEventId(eventId: string) {
    this.lastEventId = eventId;
  }
}
```

### 2. React Hook 구현

```typescript
import { useEffect, useRef, useState } from 'react';

interface SSEEvent {
  id: string;
  event_type: string;
  payload: {
    proposal_id?: string;
    proposal_type?: string;
    comment_id?: string;
    criterion_id?: string;
    [key: string]: any;
  };
  created_at: string;
}

interface UseEventStreamOptions {
  eventId: string;
  accessToken: string;
  enabled?: boolean;
  onMessage?: (event: SSEEvent) => void;
  onError?: (error: Error) => void;
}

export function useEventStream(options: UseEventStreamOptions) {
  const {
    eventId,
    accessToken,
    enabled = true,
    onMessage,
    onError,
  } = options;
  
  const [isConnected, setIsConnected] = useState(false);
  const [lastEventId, setLastEventId] = useState<string | null>(null);
  const clientRef = useRef<SSEClient | null>(null);
  
  useEffect(() => {
    if (!enabled) {
      return;
    }
    
    // 재연결을 위해 마지막 이벤트 ID를 URL에 포함
    const url = lastEventId
      ? `/v1/events/${eventId}/stream?last_event_id=${lastEventId}`
      : `/v1/events/${eventId}/stream`;
    
    const client = new SSEClient(url, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      onOpen: () => {
        setIsConnected(true);
      },
      onMessage: (data: SSEEvent) => {
        setLastEventId(data.id);
        onMessage?.(data);
      },
      onError: (error) => {
        setIsConnected(false);
        onError?.(error);
        
        // 에러 발생 시 5초 후 재연결 시도
        setTimeout(() => {
          if (enabled) {
            // 재연결 시도
            const retryUrl = lastEventId
              ? `/v1/events/${eventId}/stream?last_event_id=${lastEventId}`
              : `/v1/events/${eventId}/stream`;
            
            const retryClient = new SSEClient(retryUrl, {
              headers: {
                'Authorization': `Bearer ${accessToken}`,
              },
              onOpen: () => setIsConnected(true),
              onMessage: (data: SSEEvent) => {
                setLastEventId(data.id);
                onMessage?.(data);
              },
              onError: (error) => {
                setIsConnected(false);
                onError?.(error);
              },
            });
            
            clientRef.current = retryClient;
            retryClient.connect();
          }
        }, 5000);
      },
    });
    
    clientRef.current = client;
    client.connect();
    
    return () => {
      client.disconnect();
      setIsConnected(false);
    };
  }, [eventId, accessToken, enabled, lastEventId, onMessage, onError]);
  
  return {
    isConnected,
    lastEventId,
    reconnect: () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
      }
      // useEffect가 재실행되도록 상태 업데이트
      setLastEventId(lastEventId);
    },
  };
}
```

### 3. 사용 예시

```typescript
function EventDetailPage({ eventId }: { eventId: string }) {
  const { accessToken } = useAuth();
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  
  // SSE 연결
  const { isConnected } = useEventStream({
    eventId,
    accessToken,
    onMessage: (event: SSEEvent) => {
      switch (event.event_type) {
        case 'proposal.created.v1':
          // Proposal 생성 이벤트 처리
          // payload에서 proposal_id를 가져와서 상세 정보 재조회
          fetchProposalDetails(event.payload.proposal_id).then(proposal => {
            setProposals(prev => [...prev, proposal]);
          });
          break;
          
        case 'proposal.vote.created.v1':
        case 'proposal.vote.deleted.v1':
          // 투표 수 변경 이벤트 처리
          // payload에서 proposal_id를 가져와서 해당 proposal의 vote_count 재조회
          updateProposalVoteCount(event.payload.proposal_id);
          break;
          
        case 'proposal.approved.v1':
        case 'proposal.rejected.v1':
          // Proposal 상태 변경 이벤트 처리
          updateProposalStatus(
            event.payload.proposal_id,
            event.event_type === 'proposal.approved.v1' ? 'ACCEPTED' : 'REJECTED'
          );
          break;
          
        case 'comment.created.v1':
          // 코멘트 생성 이벤트 처리
          fetchCommentDetails(event.payload.comment_id).then(comment => {
            setComments(prev => [...prev, comment]);
          });
          break;
      }
    },
    onError: (error) => {
      console.error('SSE connection error:', error);
      // 에러 알림 표시
    },
  });
  
  return (
    <div>
      {isConnected ? (
        <div>실시간 동기화 연결됨</div>
      ) : (
        <div>연결 중...</div>
      )}
      {/* 나머지 UI */}
    </div>
  );
}
```

---

## 이벤트 처리 가이드

### 1. Proposal 생성 이벤트 (`proposal.created.v1`)

**Payload**:
```json
{
  "proposal_id": "uuid",
  "proposal_type": "assumption" | "criteria" | "conclusion"
}
```

**처리 방법**:
- `proposal_id`를 사용하여 Proposal 상세 정보를 재조회
- 새로운 Proposal을 목록에 추가

```typescript
async function handleProposalCreated(event: SSEEvent) {
  const proposal = await fetch(`/v1/events/${eventId}/assumption-proposals/${event.payload.proposal_id}`);
  setProposals(prev => [...prev, proposal]);
}
```

### 2. 투표 생성/삭제 이벤트 (`proposal.vote.created.v1`, `proposal.vote.deleted.v1`)

**Payload**:
```json
{
  "proposal_id": "uuid",
  "proposal_type": "assumption" | "criteria" | "conclusion"
}
```

**처리 방법**:
- `proposal_id`를 사용하여 해당 Proposal의 `vote_count` 재조회
- UI에서 투표 수만 업데이트

```typescript
async function handleVoteCreated(event: SSEEvent) {
  // 해당 proposal만 재조회
  const proposal = await fetchProposalDetails(event.payload.proposal_id);
  updateProposalInList(proposal.id, { vote_count: proposal.vote_count });
}
```

### 3. Proposal 승인/거부 이벤트 (`proposal.approved.v1`, `proposal.rejected.v1`)

**Payload**:
```json
{
  "proposal_id": "uuid",
  "proposal_type": "assumption" | "criteria" | "conclusion",
  "event_id": "uuid",
  "approved_by": "uuid" | null
}
```

**처리 방법**:
- Proposal 상태를 업데이트
- 자동 승인된 경우 `approved_by`가 `null`

```typescript
function handleProposalApproved(event: SSEEvent) {
  updateProposalStatus(event.payload.proposal_id, 'ACCEPTED');
}
```

### 4. 코멘트 생성 이벤트 (`comment.created.v1`)

**Payload**:
```json
{
  "comment_id": "uuid",
  "criterion_id": "uuid"
}
```

**처리 방법**:
- `comment_id`를 사용하여 코멘트 상세 정보를 재조회
- 새로운 코멘트를 목록에 추가

```typescript
async function handleCommentCreated(event: SSEEvent) {
  const comment = await fetch(`/v1/events/${eventId}/criteria/${event.payload.criterion_id}/comments`);
  setComments(prev => [...prev, comment]);
}
```

---

## 재연결 처리

SSE 연결이 끊어졌을 때 자동으로 재연결하는 것이 중요합니다. `Last-Event-ID`를 사용하여 마지막으로 받은 이벤트 이후부터 다시 받아올 수 있습니다.

### 재연결 전략

1. **마지막 이벤트 ID 저장**: 각 이벤트의 `id` 필드를 로컬 스토리지나 상태에 저장
2. **재연결 시 Last-Event-ID 전달**: URL 쿼리 파라미터 또는 헤더로 전달
3. **자동 재시도**: 에러 발생 시 5초 후 자동 재연결

```typescript
// 로컬 스토리지에 마지막 이벤트 ID 저장
function saveLastEventId(eventId: string) {
  localStorage.setItem(`last_event_id_${eventId}`, eventId);
}

function getLastEventId(eventId: string): string | null {
  return localStorage.getItem(`last_event_id_${eventId}`);
}

// 재연결 시 사용
const lastEventId = getLastEventId(eventId);
const url = lastEventId
  ? `/v1/events/${eventId}/stream?last_event_id=${lastEventId}`
  : `/v1/events/${eventId}/stream`;
```

---

## Heartbeat 처리

서버는 30초마다 `: ping` 형태의 heartbeat를 전송합니다. 이것은 프록시/로드밸런서의 idle timeout을 방지하기 위한 것입니다.

**처리 방법**:
- Heartbeat는 무시해도 됩니다 (연결 유지용)
- Heartbeat를 받지 못하면 연결이 끊어진 것으로 간주

```typescript
// SSE 클라이언트에서 heartbeat 처리
if (line.startsWith(':')) {
  // Heartbeat - 무시
  continue;
}
```

---

## 주의사항

1. **인증 토큰**: 모든 SSE 요청은 `Authorization` 헤더가 필요합니다.
2. **멤버십 검증**: ACCEPTED 멤버십만 SSE 연결 가능합니다.
3. **재연결**: 네트워크 오류 시 자동으로 재연결됩니다.
4. **메모리 관리**: 컴포넌트 언마운트 시 연결을 반드시 종료하세요.
5. **중복 처리 방지**: 같은 이벤트를 여러 번 처리하지 않도록 주의하세요.

---

## API 참조

자세한 API 스펙은 [`api_spec.md`](./api_spec/api_spec.md)를 참고하세요.

### GET /v1/events/{event_id}/stream

**쿼리 파라미터**:
- `last_event_id` (선택): 마지막으로 받은 이벤트 ID

**헤더**:
- `Authorization: Bearer <access_token>` (필수)
- `Last-Event-ID: <event_id>` (재연결 시, 쿼리 파라미터보다 우선)

**응답 형식**: `text/event-stream`

**이벤트 형식**:
```
id: <event_id>
data: {"id": "...", "event_type": "...", "payload": {...}, "created_at": "..."}

```

---

## 예제 코드

전체 예제는 프로젝트 저장소를 참고하세요.
