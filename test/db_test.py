import sys
import numpy as np
from src.db_manager import DatabaseManager
import ast


db_manager = DatabaseManager()

# id=1인 노래의 지문 가져오기
result = db_manager.load_changpop_by_id(19)
if not result:
    raise ValueError("노래를 데이터베이스에서 찾을 수 없습니다.")

np.set_printoptions(threshold=sys.maxsize)
print(result['shape'])
print(type(result['shape']))
print(result['fingerprint'])
