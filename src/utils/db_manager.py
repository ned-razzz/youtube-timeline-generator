"""
데이터베이스 연결 및 작업을 위한 모듈
초기화 시점에 즉시 연결을 생성하는 단순화된 구현
"""
from dataclasses import dataclass
import json
import pickle
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from contextlib import contextmanager
import zlib

# WorldCup 데이터 타입 정의
@dataclass
class WorldcupData:
    title: str
    genre: str  
    series_number: int
    
# WorldCup 데이터 타입 정의
@dataclass
class ChangPopData:
    name: str
    fingerprint: Dict
    artist: Optional[str]
    worldcup_id: Optional[int]

class DatabaseManager:
    """ChangPop 및 WorldCup 데이터 관리를 위한 데이터베이스 관리자 클래스"""
    
    def __init__(self, db_path: Union[str, Path] = "db/fingerprints.db"):
        """
        데이터베이스 관리자 초기화 및 연결 생성
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    
    @contextmanager
    def transaction(self):
        """
        트랜잭션 컨텍스트 매니저
        
        트랜잭션 내에서 수행되는 모든 작업은 하나의 단위로 취급됩니다.
        예외가 발생하면 모든 변경사항이 롤백됩니다.
        
        Yields:
            sqlite3.Cursor: 데이터베이스 커서 객체
        """
        cursor = self.conn.cursor()
        
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
    
    def insert_changpop(self, data: ChangPopData) -> int:
        """
        ChangPop 데이터를 데이터베이스에 삽입
        
        Args:
            data: 삽입할 ChangPop 데이터
                - name: 곡 이름
                - artist: 아티스트 이름
                - worldcup_id: 관련 월드컵 ID
            
        Returns:
            int: 삽입된 레코드의 ID
        
        Raises:
            Exception: 데이터베이스 작업 실패 시
        """
        serialized = pickle.dumps(data.fingerprint)
        compressed = zlib.compress(serialized)
        
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO changpops
                (name, artist, worldcup_id, fingerprint)
                VALUES (?, ?, ?, ?)
                """,
                (data.name, data.artist, data.worldcup_id, compressed)
            )
            return cursor.lastrowid
    
    def insert_worldcup(self, data: WorldcupData) -> int:
        """
        WorldCup 데이터를 데이터베이스에 삽입
        
        Args:
            data: 삽입할 WorldCup 데이터
                - title: 월드컵 제목
                - genre: 장르
                - series_number: 시리즈 번호
            
        Returns:
            int: 삽입된 레코드의 ID
        
        Raises:
            Exception: 데이터베이스 작업 실패 시
        """
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO worldcups 
                (title, genre, series_number)
                VALUES (?, ?, ?)
                """,
                (data.title, data.genre, data.series_number)
            )
            return cursor.lastrowid
    
    def delete_changpop(self, changpop_id: int) -> bool:
        """
        ChangPop 데이터 삭제
        
        Args:
            changpop_id: 삭제할 ChangPop ID
            
        Returns:
            bool: 삭제 성공 여부
        
        Raises:
            Exception: 데이터베이스 작업 실패 시
        """
        with self.transaction() as cursor:
            cursor.execute(
                "DELETE FROM changpops WHERE id = ?",
                (changpop_id,)
            )
            return cursor.rowcount > 0
    
    def load_changpops_by_worldcup(self, worldcup_id: int):
        """
        특정 WorldCup ID에 속한 모든 ChangPop 데이터 로드
        
        Args:
            worldcup_id: 찾을 WorldCup ID
            
        Returns:
            List[ChangPopData]: ChangPop 데이터 목록
        
        Raises:
            Exception: 데이터베이스 작업 실패 시
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, name, artist, worldcup_id, fingerprint
            FROM changpops
            WHERE worldcup_id = ?
            ORDER BY id
            """,
            (worldcup_id,)
        )
        
        data_list = []
        for row in cursor.fetchall():
            data = dict(row)
            data_list.append(self._convert_changpop_data(data))
        return data_list
        
    
    def load_changpop_by_id(self, changpop_id: int) -> Optional[ChangPopData]:
        """
        ID로 특정 ChangPop 데이터 로드
        
        Args:
            changpop_id: 찾을 ChangPop ID
            
        Returns:
            Optional[ChangPopData]: ChangPop 데이터 또는 None(찾지 못한 경우)
        
        Raises:
            Exception: 데이터베이스 작업 실패 시
        """
        cursor = self.conn.cursor()
        fields = "name, fingerprint"
        cursor.execute(
            f"SELECT {fields} FROM changpops WHERE id = ?",
            (changpop_id,)
        )
        row = cursor.fetchone()
        data = dict(row) if row else None
        return self._convert_changpop_data(data)
    
    def _convert_changpop_data(self, data):        
        #데이터 압축 해제 및 역직렬화
        compressed_fg = data['fingerprint']
        serialized_fg = zlib.decompress(compressed_fg)
        fingerprint = pickle.loads(serialized_fg)

        # # key값이 str인 peek_pairs 해시 테이블을 tuple로 복원
        # pattern = re.compile(r'\((\d+),\s*(\d+)\)')
        # restored_fingerprint = {(int(m.group(1)), int(m.group(2))): v 
        #                 for k, v in fingerprint.items()
        #                 if (m := pattern.match(k))}
        
        return ChangPopData(data['name'], 
                            fingerprint, 
                            data['artist'] if 'artist' in data else None, 
                            data['worldcup_id'] if 'worldcup_id' in data else None)
    
    def get_worldcup_details(self, worldcup_id: int) -> Optional[Dict[str, Any]]:
        """
        특정 WorldCup의 상세 정보를 로드
        
        Args:
            worldcup_id: 찾을 WorldCup ID
            
        Returns:
            Optional[Dict[str, Any]]: WorldCup 정보 또는 None(찾지 못한 경우)
        """
        cursor = self.conn.cursor()
        
        cursor.execute(
            """
            SELECT id, title, genre, series_number
            FROM worldcups
            WHERE id = ?
            """,
            (worldcup_id,)
        )
        
        row = cursor.fetchone()
        data = dict(row) if row else None
        return WorldcupData(data['title'], data['genre'], data['series_number'])
    
    def get_all_worldcups(self) -> List[Dict[str, Any]]:
        """
        모든 WorldCup 데이터 로드
        
        Returns:
            List[Dict[str, Any]]: WorldCup 데이터 목록
        """
        cursor = self.conn.cursor()
        
        cursor.execute(
            """
            SELECT id, title, genre, series_number
            FROM worldcups
            ORDER BY id
            """
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        사용자 정의 쿼리 실행
        
        Args:
            query: 실행할 SQL 쿼리
            params: 쿼리에 바인딩할 매개변수
            
        Returns:
            List[Dict[str, Any]]: 쿼리 결과
        """
        cursor = self.conn.cursor()
        
        cursor.execute(query, params)
        
        # SELECT 쿼리인 경우 결과 반환
        if query.strip().upper().startswith("SELECT"):
            return [dict(row) for row in cursor.fetchall()]
        
        # INSERT, UPDATE, DELETE 등의 경우 영향받은 행 수 반환
        self.conn.commit()
        return [{"affected_rows": cursor.rowcount}]
    
    def close(self):
        """
        데이터베이스 연결을 명시적으로 닫습니다.
        """
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """컨텍스트 매니저 진입시 자신을 반환합니다."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료시 연결을 닫습니다."""
        self.close()