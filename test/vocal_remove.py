from src.remove_vocals import remove_vocals_chunked
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]

try:
    print(f"'{input_file}' 로드 중...")
    with open(input_file, 'rb') as f:
        audio_bytes = f.read()
    
    result_bytes = remove_vocals_chunked(audio_bytes, 120)
    
    with open(output_file, 'wb') as f:
        f.write(result_bytes)
        
    print(f"보컬 제거 완료! 결과가 '{output_file}'에 저장되었습니다.")

except Exception as e:
    print(f"오류 발생: {str(e)}")
    import traceback
    traceback.print_exc()