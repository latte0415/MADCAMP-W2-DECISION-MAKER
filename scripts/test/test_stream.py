"""
실시간 동기화 (SSE) API 테스트

테스트 항목:
- GET /v1/events/{event_id}/stream - SSE 스트림 연결
- Proposal 생성 시 이벤트 수신 확인
- Vote 생성/삭제 시 이벤트 수신 확인
- Comment 생성 시 이벤트 수신 확인
- Proposal 승인 시 이벤트 수신 확인
- Last-Event-ID로 재연결 테스트
- Heartbeat 확인
"""

import time
import json
import uuid
import random
import string
import requests
import threading
from typing import List, Dict, Optional
from scripts.test.base import BaseAPITester


class StreamAPITester(BaseAPITester):
    """실시간 동기화 (SSE) API 테스트 클래스"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.received_events: List[Dict] = []
        self.last_event_id: Optional[str] = None
        self.heartbeat_received = False
    
    def _read_sse_stream(self, url: str, headers: Dict, duration: int = 5):
        """SSE 스트림 읽기 (지정된 시간 동안)"""
        self.received_events = []
        self.heartbeat_received = False
        
        try:
            # timeout을 (connect_timeout, read_timeout) 튜플로 설정
            # connect_timeout: 연결 타임아웃 (5초)
            # read_timeout: 읽기 타임아웃 (duration + 10초, heartbeat 대기 여유 포함)
            response = requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=(5, duration + 10)
            )
            
            if response.status_code != 200:
                print(f"  [에러] SSE 연결 실패: {response.status_code} - {response.text[:200]}")
                return
            
            start_time = time.time()
            current_event = {}
            current_event_id = None
            
            # iter_lines()를 사용하여 라인 단위로 읽기
            # duration을 초과하면 반복문을 빠져나가도록 함
            for line in response.iter_lines(decode_unicode=True):
                elapsed = time.time() - start_time
                if elapsed > duration:
                    # 지정된 시간이 지나면 종료
                    break
                
                if not line:
                    # 빈 줄은 이벤트 구분자
                    if current_event and current_event_id:
                        current_event["id"] = current_event_id
                        self.received_events.append(current_event)
                        current_event = {}
                        current_event_id = None
                    continue
                
                if line.startswith('id:'):
                    current_event_id = line[3:].strip()
                    self.last_event_id = current_event_id
                elif line.startswith('data:'):
                    data_str = line[5:].strip()
                    if data_str:
                        try:
                            data = json.loads(data_str)
                            current_event.update(data)
                        except json.JSONDecodeError:
                            pass
                elif line.startswith(':'):
                    # Heartbeat (예: ": ping" 또는 ":ping")
                    line_content = line[1:].strip()
                    if 'ping' in line_content.lower():
                        self.heartbeat_received = True
                        # print(f"  [디버깅] Heartbeat 수신 (elapsed: {elapsed:.1f}s)")
                elif line.startswith('retry:'):
                    # Retry 헤더는 무시
                    pass
            
            # 마지막 이벤트 처리
            if current_event and current_event_id:
                current_event["id"] = current_event_id
                self.received_events.append(current_event)
            
            response.close()
        except requests.exceptions.ReadTimeout as e:
            # 읽기 타임아웃은 정상일 수 있음 (지정된 시간 동안만 읽기)
            # duration 이후에 발생한 timeout은 정상 종료로 간주
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            if elapsed >= duration:
                # duration을 초과한 후 발생한 timeout은 정상 종료
                # 에러 메시지 출력하지 않음
                pass
            else:
                # duration 전에 발생한 timeout은 예상치 못한 상황
                if not self.heartbeat_received and duration >= 30:
                    print(f"  [경고] 읽기 타임아웃 발생 (elapsed: {elapsed:.1f}s, duration: {duration}s), heartbeat 미수신")
        except requests.exceptions.Timeout:
            # 일반 타임아웃도 처리 (에러 메시지 출력하지 않음)
            pass
        except Exception as e:
            # duration 이후에 발생한 ConnectionError/ReadTimeout도 정상 종료로 처리
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            error_str = str(e)
            is_read_timeout = (
                "Read timed out" in error_str or
                "ReadTimeout" in error_str or
                isinstance(e, (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError))
            )
            
            if elapsed >= duration and is_read_timeout:
                # duration 초과 후 Read timeout은 정상 종료 (에러 메시지 출력하지 않음)
                pass
            else:
                print(f"  [에러] SSE 스트림 읽기 실패: {e}")
                import traceback
                traceback.print_exc()
    
    def test_sse_connection(self) -> bool:
        """GET /v1/events/{event_id}/stream - SSE 연결 테스트"""
        self.print_test("SSE 연결 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 설정 및 멤버십 승인
        self.setup_complete_event(start_event=True)
        
        # SSE 연결
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        
        # 별도 스레드에서 SSE 읽기 (3초 동안)
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 3)
        )
        thread.start()
        thread.join(timeout=5)
        
        # 연결 성공 확인
        success = True
        if not self.received_events and not self.heartbeat_received:
            self.print_result(False, "SSE 연결 실패 또는 이벤트/Heartbeat 미수신")
            success = False
        else:
            self.print_result(True, f"SSE 연결 성공 (이벤트: {len(self.received_events)}개, Heartbeat: {self.heartbeat_received})")
        
        return success
    
    def test_proposal_created_event(self) -> bool:
        """Proposal 생성 시 이벤트 수신 테스트"""
        self.print_test("Proposal 생성 이벤트 수신 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 설정 및 멤버십 승인
        self.setup_complete_event(start_event=True)
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        
        # 잠시 대기 후 Proposal 생성
        time.sleep(1)
        
        # Assumption Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "테스트 전제",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # 트랜잭션 커밋 및 SSE 폴링을 위한 충분한 대기 시간
        time.sleep(2.5)
        
        # SSE 스트림 읽기 완료 대기
        thread.join(timeout=12)
        
        # 이벤트 확인
        proposal_created_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.created.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        if not proposal_created_events:
            self.print_result(False, "proposal.created.v1 이벤트를 받지 못함")
            return False
        
        event = proposal_created_events[0]
        assert event["payload"]["proposal_type"] == "assumption", "proposal_type이 assumption이어야 함"
        
        self.print_result(True, f"proposal.created.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_vote_created_event(self) -> bool:
        """Vote 생성 시 이벤트 수신 테스트"""
        self.print_test("Vote 생성 이벤트 수신 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 설정 및 멤버십 승인
        self.setup_complete_event(start_event=True)
        
        # Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "테스트 전제",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        
        # 잠시 대기 후 Vote 생성
        time.sleep(1)
        
        # Vote 생성
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Vote 생성 실패: {response.status_code}")
            return False
        
        # 트랜잭션 커밋 및 SSE 폴링을 위한 충분한 대기 시간
        time.sleep(2.5)
        
        # SSE 스트림 읽기 완료 대기
        thread.join(timeout=12)
        
        # 이벤트 확인
        vote_created_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.vote.created.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        if not vote_created_events:
            self.print_result(False, "proposal.vote.created.v1 이벤트를 받지 못함")
            return False
        
        event = vote_created_events[0]
        assert event["payload"]["proposal_type"] == "assumption", "proposal_type이 assumption이어야 함"
        
        self.print_result(True, f"proposal.vote.created.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_vote_deleted_event(self) -> bool:
        """Vote 삭제 시 이벤트 수신 테스트"""
        self.print_test("Vote 삭제 이벤트 수신 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 설정 및 멤버십 승인
        self.setup_complete_event(start_event=True)
        
        # Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "테스트 전제",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # Vote 생성
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Vote 생성 실패: {response.status_code}")
            return False
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        
        # 잠시 대기 후 Vote 삭제
        time.sleep(1)
        
        # Vote 삭제
        response = requests.delete(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        if response.status_code != 200:
            self.print_result(False, f"Vote 삭제 실패: {response.status_code}")
            return False
        
        # 트랜잭션 커밋 및 SSE 폴링을 위한 충분한 대기 시간
        time.sleep(2.5)
        
        # SSE 스트림 읽기 완료 대기
        thread.join(timeout=12)
        
        # 이벤트 확인
        vote_deleted_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.vote.deleted.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        if not vote_deleted_events:
            self.print_result(False, "proposal.vote.deleted.v1 이벤트를 받지 못함")
            return False
        
        event = vote_deleted_events[0]
        assert event["payload"]["proposal_type"] == "assumption", "proposal_type이 assumption이어야 함"
        
        self.print_result(True, f"proposal.vote.deleted.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_comment_created_event(self) -> bool:
        """Comment 생성 시 이벤트 수신 테스트"""
        self.print_test("Comment 생성 이벤트 수신 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 설정 및 멤버십 승인
        self.setup_complete_event(start_event=True)
        
        # Criterion ID 가져오기
        response = requests.get(
            f"{self.base_url}/v1/events/{self.event_id}",
            headers=self.user_headers
        )
        
        if response.status_code != 200:
            self.print_result(False, f"이벤트 상세 조회 실패: {response.status_code}")
            return False
        
        data = response.json()
        if not data.get("criteria"):
            self.print_result(False, "기준이 없어서 테스트 불가")
            return False
        
        criterion_id = data["criteria"][0]["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        
        # 잠시 대기 후 Comment 생성
        time.sleep(1)
        
        # Comment 생성
        comment_data = {
            "content": "SSE 테스트용 코멘트"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{criterion_id}/comments",
            headers=self.user_headers,
            json=comment_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Comment 생성 실패: {response.status_code}")
            return False
        
        comment_id = response.json()["id"]
        
        # 트랜잭션 커밋 및 SSE 폴링을 위한 충분한 대기 시간
        time.sleep(2.5)
        
        # SSE 스트림 읽기 완료 대기
        thread.join(timeout=12)
        
        # # 디버깅: 받은 이벤트들 출력
        # print(f"  [디버깅] 받은 이벤트 개수: {len(self.received_events)}")
        # print(f"  [디버깅] 받은 이벤트 타입들: {[e.get('event_type') for e in self.received_events]}")
        # print(f"  [디버깅] 생성한 Comment ID: {comment_id}")
        # if self.received_events:
        #     print(f"  [디버깅] 첫 번째 이벤트: {self.received_events[0]}")
        
        # 이벤트 확인
        comment_created_events = [
            e for e in self.received_events
            if e.get("event_type") == "comment.created.v1"
            and e.get("payload", {}).get("comment_id") == comment_id
        ]
        
        if not comment_created_events:
            # Comment ID로만 필터링해서 확인
            comment_events_by_id = [
                e for e in self.received_events
                if e.get("event_type") == "comment.created.v1"
            ]
            # if comment_events_by_id:
            #     print(f"  [디버깅] comment.created.v1 이벤트는 있지만 ID가 일치하지 않음")
            #     print(f"  [디버깅] Comment 이벤트들: {comment_events_by_id}")
            self.print_result(False, "comment.created.v1 이벤트를 받지 못함")
            return False
        
        event = comment_created_events[0]
        assert event["payload"]["criterion_id"] == criterion_id, "criterion_id가 일치해야 함"
        
        self.print_result(True, f"comment.created.v1 이벤트 수신 확인 (comment_id: {comment_id})")
        return True
    
    def test_proposal_approved_event(self) -> bool:
        """Proposal 승인 시 이벤트 수신 테스트"""
        self.print_test("Proposal 승인 이벤트 수신 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 설정 및 멤버십 승인
        self.setup_complete_event(start_event=True)
        
        # Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "테스트 전제",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        
        # 잠시 대기 후 Proposal 승인
        time.sleep(1)
        
        # Proposal 승인 (관리자 권한 필요)
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers={**self.admin_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"status": "ACCEPTED"}
        )
        
        if response.status_code != 200:
            self.print_result(False, f"Proposal 승인 실패: {response.status_code}")
            return False
        
        # 트랜잭션 커밋 및 SSE 폴링을 위한 충분한 대기 시간
        time.sleep(2.5)
        
        # SSE 스트림 읽기 완료 대기
        thread.join(timeout=12)
        
        # 이벤트 확인
        approved_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.approved.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        if not approved_events:
            self.print_result(False, "proposal.approved.v1 이벤트를 받지 못함")
            return False
        
        event = approved_events[0]
        assert event["payload"]["proposal_type"] == "assumption", "proposal_type이 assumption이어야 함"
        assert "approved_by" in event["payload"], "approved_by가 있어야 함"
        
        self.print_result(True, f"proposal.approved.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_last_event_id_reconnect(self) -> bool:
        """Last-Event-ID로 재연결 테스트"""
        self.print_test("Last-Event-ID 재연결 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 설정 및 멤버십 승인
        self.setup_complete_event(start_event=True)
        
        # 첫 번째 Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "첫 번째 전제",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"첫 번째 Proposal 생성 실패: {response.status_code}")
            return False
        
        first_proposal_id = response.json()["id"]
        
        # 첫 번째 SSE 연결 (3초 동안)
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 3)
        )
        thread.start()
        thread.join(timeout=5)
        
        # 첫 번째 이벤트 ID 저장
        first_event_id = self.last_event_id
        first_events_count = len(self.received_events)
        
        if not first_event_id:
            self.print_result(False, "첫 번째 연결에서 이벤트 ID를 받지 못함")
            return False
        
        # 첫 번째 Proposal을 거절하여 중복 제안 방지
        # (같은 사용자가 같은 assumption_id=None에 대해 PENDING 제안이 있으면 중복으로 판단됨)
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{first_proposal_id}/status",
            headers={**self.admin_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"status": "REJECTED"}
        )
        
        if response.status_code != 200:
            self.print_result(False, f"첫 번째 Proposal 거절 실패: {response.status_code}")
            return False
        
        # 거절 이벤트가 생성되고 커밋될 시간 대기
        time.sleep(1)
        
        # 두 번째 Proposal 생성 (이제 중복 체크를 통과할 수 있음)
        proposal_data2 = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "두 번째 전제",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data2
        )
        
        if response.status_code != 201:
            self.print_result(False, f"두 번째 Proposal 생성 실패: {response.status_code}")
            return False
        
        second_proposal_id = response.json()["id"]
        
        # 트랜잭션 커밋 및 SSE 폴링을 위한 충분한 대기 시간
        time.sleep(2.5)
        
        # Last-Event-ID로 재연결
        url_with_last_id = f"{self.base_url}/v1/events/{self.event_id}/stream?last_event_id={first_event_id}"
        thread2 = threading.Thread(
            target=self._read_sse_stream,
            args=(url_with_last_id, self.user_headers, 5)
        )
        thread2.start()
        thread2.join(timeout=7)
        
        # 두 번째 Proposal 이벤트만 받았는지 확인
        second_proposal_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.created.v1"
            and e.get("payload", {}).get("proposal_id") == second_proposal_id
        ]
        
        first_proposal_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.created.v1"
            and e.get("payload", {}).get("proposal_id") == first_proposal_id
        ]
        
        if first_proposal_events:
            self.print_result(False, "재연결 시 첫 번째 이벤트를 중복으로 받음")
            return False
        
        if not second_proposal_events:
            self.print_result(False, "재연결 시 두 번째 이벤트를 받지 못함")
            return False
        
        self.print_result(True, f"Last-Event-ID 재연결 성공 (첫 번째 이벤트 제외, 두 번째 이벤트만 수신)")
        return True
    
    def test_heartbeat(self) -> bool:
        """Heartbeat 수신 테스트"""
        self.print_test("Heartbeat 수신 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 설정 및 멤버십 승인
        self.setup_complete_event(start_event=True)
        
        # SSE 연결 (35초 동안 - heartbeat는 30초마다 전송)
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 35)
        )
        thread.start()
        thread.join(timeout=40)
        
        if not self.heartbeat_received:
            self.print_result(False, "Heartbeat를 받지 못함 (35초 대기)")
            return False
        
        self.print_result(True, "Heartbeat 수신 확인")
        return True
    
    def test_membership_required(self) -> bool:
        """멤버십 검증 테스트 (ACCEPTED 멤버십만 접근 가능)"""
        self.print_test("멤버십 검증 테스트")
        
        # 이전 테스트 데이터 초기화
        self.event_id = None
        
        # 이벤트 생성 (멤버십 없이) - 고유한 entrance_code 사용 (6자리)
        entrance_code = self.generate_entrance_code()  # 6자리 랜덤 코드 생성
        event_data = {
            "decision_subject": "SSE 멤버십 테스트",
            "entrance_code": entrance_code,
            "assumption_is_auto_approved_by_votes": False,
            "criteria_is_auto_approved_by_votes": False,
            "membership_is_auto_approved": False,
            "conclusion_is_auto_approved_by_votes": False,
            "max_membership": 10,
            "options": [{"content": "옵션1"}],
            "assumptions": [{"content": "전제1"}],
            "criteria": [{"content": "기준1"}]
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events",
            headers=self.admin_headers,
            json=event_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"이벤트 생성 실패: {response.status_code}")
            return False
        
        test_event_id = response.json()["id"]
        
        # 멤버십 없이 SSE 연결 시도
        url = f"{self.base_url}/v1/events/{test_event_id}/stream"
        response = requests.get(
            url,
            headers=self.user_headers,
            stream=True,
            timeout=3
        )
        
        if response.status_code != 403:
            self.print_result(False, f"멤버십 없이 접근 시 403이어야 하는데 {response.status_code} 반환")
            return False
        
        self.print_result(True, "멤버십 검증 확인 (ACCEPTED 멤버십만 접근 가능)")
        return True
