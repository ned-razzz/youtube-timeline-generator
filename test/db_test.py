from ast import List
import sys
import numpy as np
from src.utils.db_manager import ChangPopData, DatabaseManager


db_manager = DatabaseManager()

# id=1인 노래의 지문 가져오기
results: list = db_manager.load_changpops_by_worldcup(sys.argv[1])
if not results:
    raise ValueError("노래를 데이터베이스에서 찾을 수 없습니다.")

# np.set_printoptions(threshold=sys.maxsize)
for result in results:
    print(result.name)
