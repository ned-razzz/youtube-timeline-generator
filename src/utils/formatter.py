
class Fommatter:
    """초 단위 데이터 문자열 변환 모듈"""

    @staticmethod
    def format_time_to_str(seconds):
        """초 단위 시간을 HH:MM:SS 형식의 문자열로 변환합니다."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def format_time_to_int(time_str):
        """HH:MM:SS 형식의 시간 문자열을 초 단위로 변환합니다."""
        parts = time_str.split(':')
        
        if len(parts) == 3:  # HH:MM:SS 형식
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS 형식
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            raise ValueError("시간 형식은 'HH:MM:SS' 또는 'MM:SS' 형식이어야 합니다.")