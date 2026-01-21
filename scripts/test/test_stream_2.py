"""
실시간 동기화 (SSE) API 추가 테스트

테스트 항목:
- Criteria Proposal 생성/투표/승인 이벤트 수신 확인
- Conclusion Proposal 생성/투표/승인 이벤트 수신 확인
- Proposal 거절 이벤트 수신 확인 (assumption, criteria, conclusion)
- 연속 이벤트 시나리오 테스트
"""

import time
import json
import uuid
import requests
import threading
from typing import List, Dict, Optional
from scripts.test.base import BaseAPITester


class StreamAPITester2(BaseAPITester):
    """실시간 동기화 (SSE) API 추가 테스트 클래스"""
    
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
            
            for line in response.iter_lines(decode_unicode=True):
                elapsed = time.time() - start_time
                if elapsed > duration:
                    break
                
                if not line:
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
                    line_content = line[1:].strip()
                    if 'ping' in line_content.lower():
                        self.heartbeat_received = True
                elif line.startswith('retry:'):
                    pass
            
            if current_event and current_event_id:
                current_event["id"] = current_event_id
                self.received_events.append(current_event)
            
            response.close()
        except requests.exceptions.ReadTimeout as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            if elapsed >= duration:
                pass
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            error_str = str(e)
            is_read_timeout = (
                "Read timed out" in error_str or
                "ReadTimeout" in error_str or
                isinstance(e, (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError))
            )
            if elapsed >= duration and is_read_timeout:
                pass
            else:
                print(f"  [에러] SSE 스트림 읽기 실패: {e}")
    
    # ========== Criteria Proposal 테스트 ==========
    
    def test_criteria_proposal_created_event(self) -> bool:
        """Criteria Proposal 생성 시 이벤트 수신 테스트"""
        self.print_test("Criteria Proposal 생성 이벤트 수신 테스트")
        
        self.event_id = None
        self.setup_complete_event(start_event=True)
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        time.sleep(1)
        
        # Criteria Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "criteria_id": None,
            "proposal_content": "테스트 기준",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Criteria Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        time.sleep(2.5)
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
        assert event["payload"]["proposal_type"] == "criteria", "proposal_type이 criteria여야 함"
        
        self.print_result(True, f"Criteria proposal.created.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_criteria_proposal_vote_created_event(self) -> bool:
        """Criteria Proposal 투표 생성 시 이벤트 수신 테스트"""
        self.print_test("Criteria Proposal 투표 생성 이벤트 수신 테스트")
        
        self.event_id = None
        self.setup_complete_event(start_event=True)
        
        # Criteria Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "criteria_id": None,
            "proposal_content": "테스트 기준",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Criteria Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        time.sleep(1)
        
        # Vote 생성
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Vote 생성 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
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
        assert event["payload"]["proposal_type"] == "criteria", "proposal_type이 criteria여야 함"
        
        self.print_result(True, f"Criteria proposal.vote.created.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_criteria_proposal_approved_event(self) -> bool:
        """Criteria Proposal 승인 시 이벤트 수신 테스트"""
        self.print_test("Criteria Proposal 승인 이벤트 수신 테스트")
        
        self.event_id = None
        self.setup_complete_event(start_event=True)
        
        # Criteria Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "criteria_id": None,
            "proposal_content": "테스트 기준",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Criteria Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        time.sleep(1)
        
        # Proposal 승인
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/status",
            headers={**self.admin_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"status": "ACCEPTED"}
        )
        
        if response.status_code != 200:
            self.print_result(False, f"Criteria Proposal 승인 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
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
        assert event["payload"]["proposal_type"] == "criteria", "proposal_type이 criteria여야 함"
        assert "approved_by" in event["payload"], "approved_by가 있어야 함"
        
        self.print_result(True, f"Criteria proposal.approved.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    # ========== Conclusion Proposal 테스트 ==========
    
    def test_conclusion_proposal_created_event(self) -> bool:
        """Conclusion Proposal 생성 시 이벤트 수신 테스트"""
        self.print_test("Conclusion Proposal 생성 이벤트 수신 테스트")
        
        self.event_id = None
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
        time.sleep(1)
        
        # Conclusion Proposal 생성
        proposal_data = {
            "proposal_content": "테스트 결론",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{criterion_id}/conclusion-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Conclusion Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        time.sleep(2.5)
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
        assert event["payload"]["proposal_type"] == "conclusion", "proposal_type이 conclusion이어야 함"
        
        self.print_result(True, f"Conclusion proposal.created.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_conclusion_proposal_vote_created_event(self) -> bool:
        """Conclusion Proposal 투표 생성 시 이벤트 수신 테스트"""
        self.print_test("Conclusion Proposal 투표 생성 이벤트 수신 테스트")
        
        self.event_id = None
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
        
        # Conclusion Proposal 생성
        proposal_data = {
            "proposal_content": "테스트 결론",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{criterion_id}/conclusion-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Conclusion Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        time.sleep(1)
        
        # Vote 생성
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Vote 생성 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
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
        assert event["payload"]["proposal_type"] == "conclusion", "proposal_type이 conclusion이어야 함"
        
        self.print_result(True, f"Conclusion proposal.vote.created.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_conclusion_proposal_approved_event(self) -> bool:
        """Conclusion Proposal 승인 시 이벤트 수신 테스트"""
        self.print_test("Conclusion Proposal 승인 이벤트 수신 테스트")
        
        self.event_id = None
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
        
        # Conclusion Proposal 생성
        proposal_data = {
            "proposal_content": "테스트 결론",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{criterion_id}/conclusion-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Conclusion Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        time.sleep(1)
        
        # Proposal 승인
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/status",
            headers={**self.admin_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"status": "ACCEPTED"}
        )
        
        if response.status_code != 200:
            self.print_result(False, f"Conclusion Proposal 승인 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
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
        assert event["payload"]["proposal_type"] == "conclusion", "proposal_type이 conclusion이어야 함"
        assert "approved_by" in event["payload"], "approved_by가 있어야 함"
        
        self.print_result(True, f"Conclusion proposal.approved.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    # ========== Proposal 거절 이벤트 테스트 ==========
    
    def test_assumption_proposal_rejected_event(self) -> bool:
        """Assumption Proposal 거절 시 이벤트 수신 테스트"""
        self.print_test("Assumption Proposal 거절 이벤트 수신 테스트")
        
        self.event_id = None
        self.setup_complete_event(start_event=True)
        
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
            self.print_result(False, f"Assumption Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        time.sleep(1)
        
        # Proposal 거절
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers={**self.admin_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"status": "REJECTED"}
        )
        
        if response.status_code != 200:
            self.print_result(False, f"Assumption Proposal 거절 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
        thread.join(timeout=12)
        
        # 이벤트 확인
        rejected_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.rejected.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        if not rejected_events:
            self.print_result(False, "proposal.rejected.v1 이벤트를 받지 못함")
            return False
        
        event = rejected_events[0]
        assert event["payload"]["proposal_type"] == "assumption", "proposal_type이 assumption이어야 함"
        assert "rejected_by" in event["payload"], "rejected_by가 있어야 함"
        
        self.print_result(True, f"Assumption proposal.rejected.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_criteria_proposal_rejected_event(self) -> bool:
        """Criteria Proposal 거절 시 이벤트 수신 테스트"""
        self.print_test("Criteria Proposal 거절 이벤트 수신 테스트")
        
        self.event_id = None
        self.setup_complete_event(start_event=True)
        
        # Criteria Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "criteria_id": None,
            "proposal_content": "테스트 기준",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Criteria Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        time.sleep(1)
        
        # Proposal 거절
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/criteria-proposals/{proposal_id}/status",
            headers={**self.admin_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"status": "REJECTED"}
        )
        
        if response.status_code != 200:
            self.print_result(False, f"Criteria Proposal 거절 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
        thread.join(timeout=12)
        
        # 이벤트 확인
        rejected_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.rejected.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        if not rejected_events:
            self.print_result(False, "proposal.rejected.v1 이벤트를 받지 못함")
            return False
        
        event = rejected_events[0]
        assert event["payload"]["proposal_type"] == "criteria", "proposal_type이 criteria여야 함"
        assert "rejected_by" in event["payload"], "rejected_by가 있어야 함"
        
        self.print_result(True, f"Criteria proposal.rejected.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    def test_conclusion_proposal_rejected_event(self) -> bool:
        """Conclusion Proposal 거절 시 이벤트 수신 테스트"""
        self.print_test("Conclusion Proposal 거절 이벤트 수신 테스트")
        
        self.event_id = None
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
        
        # Conclusion Proposal 생성
        proposal_data = {
            "proposal_content": "테스트 결론",
            "reason": "SSE 테스트용"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/criteria/{criterion_id}/conclusion-proposals",
            headers={**self.user_headers, "Idempotency-Key": str(uuid.uuid4())},
            json=proposal_data
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Conclusion Proposal 생성 실패: {response.status_code}")
            return False
        
        proposal_id = response.json()["id"]
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 10)
        )
        thread.start()
        time.sleep(1)
        
        # Proposal 거절
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/conclusion-proposals/{proposal_id}/status",
            headers={**self.admin_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"status": "REJECTED"}
        )
        
        if response.status_code != 200:
            self.print_result(False, f"Conclusion Proposal 거절 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
        thread.join(timeout=12)
        
        # 이벤트 확인
        rejected_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.rejected.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        if not rejected_events:
            self.print_result(False, "proposal.rejected.v1 이벤트를 받지 못함")
            return False
        
        event = rejected_events[0]
        assert event["payload"]["proposal_type"] == "conclusion", "proposal_type이 conclusion이어야 함"
        assert "rejected_by" in event["payload"], "rejected_by가 있어야 함"
        
        self.print_result(True, f"Conclusion proposal.rejected.v1 이벤트 수신 확인 (proposal_id: {proposal_id})")
        return True
    
    # ========== 연속 이벤트 시나리오 테스트 ==========
    
    def test_proposal_creation_to_approval_flow(self) -> bool:
        """Proposal 생성 → 투표 → 승인 연속 이벤트 시나리오 테스트"""
        self.print_test("Proposal 생성 → 투표 → 승인 연속 이벤트 시나리오 테스트")
        
        self.event_id = None
        self.setup_complete_event(start_event=True)
        
        # SSE 연결 시작
        url = f"{self.base_url}/v1/events/{self.event_id}/stream"
        thread = threading.Thread(
            target=self._read_sse_stream,
            args=(url, self.user_headers, 15)
        )
        thread.start()
        time.sleep(1)
        
        # 1. Proposal 생성
        proposal_data = {
            "proposal_category": "CREATION",
            "assumption_id": None,
            "proposal_content": "연속 이벤트 테스트 전제",
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
        time.sleep(2.5)
        
        # 2. Vote 생성
        response = requests.post(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/votes",
            headers=self.user_headers
        )
        
        if response.status_code != 201:
            self.print_result(False, f"Vote 생성 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
        
        # 3. Proposal 승인
        response = requests.patch(
            f"{self.base_url}/v1/events/{self.event_id}/assumption-proposals/{proposal_id}/status",
            headers={**self.admin_headers, "Idempotency-Key": str(uuid.uuid4())},
            json={"status": "ACCEPTED"}
        )
        
        if response.status_code != 200:
            self.print_result(False, f"Proposal 승인 실패: {response.status_code}")
            return False
        
        time.sleep(2.5)
        thread.join(timeout=18)
        
        # 이벤트 확인
        created_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.created.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        vote_created_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.vote.created.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        approved_events = [
            e for e in self.received_events
            if e.get("event_type") == "proposal.approved.v1"
            and e.get("payload", {}).get("proposal_id") == proposal_id
        ]
        
        if not created_events:
            self.print_result(False, "proposal.created.v1 이벤트를 받지 못함")
            return False
        
        if not vote_created_events:
            self.print_result(False, "proposal.vote.created.v1 이벤트를 받지 못함")
            return False
        
        if not approved_events:
            self.print_result(False, "proposal.approved.v1 이벤트를 받지 못함")
            return False
        
        # 이벤트 순서 확인 (created_at 기준)
        all_events = sorted(
            created_events + vote_created_events + approved_events,
            key=lambda e: e.get("created_at", "")
        )
        
        event_types = [e.get("event_type") for e in all_events]
        expected_order = ["proposal.created.v1", "proposal.vote.created.v1", "proposal.approved.v1"]
        
        if event_types != expected_order:
            self.print_result(False, f"이벤트 순서가 올바르지 않음. 예상: {expected_order}, 실제: {event_types}")
            return False
        
        self.print_result(True, f"연속 이벤트 시나리오 성공 (생성 → 투표 → 승인)")
        return True
