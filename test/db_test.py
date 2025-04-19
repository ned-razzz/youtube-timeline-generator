import sys
import numpy as np
from src.db_manager import DatabaseManager
import ast


db_manager = DatabaseManager()

# id=1인 노래의 지문 가져오기
results = db_manager.load_changpops_by_worldcup(sys.argv[1])
if not results:
    raise ValueError("노래를 데이터베이스에서 찾을 수 없습니다.")

np.set_printoptions(threshold=sys.maxsize)
print(results[1]['fingerprint'])
# slist = {}
# for result in results:
#     slist[result['name']] = result['dtype']
# print(slist)
