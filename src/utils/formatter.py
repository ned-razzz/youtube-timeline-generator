def format_time(seconds):
    """
    초 단위 시간을 HH:MM:SS 형식의 문자열로 변환합니다.
    
    Args:
        seconds_total (float): 변환할 총 초 수
    
    Returns:
        str: HH:MM:SS 형식의 시간 문자열
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def deformat_time(time_str):
    """
    HH:MM:SS 형식의 시간 문자열을 초 단위로 변환합니다.
    
    Args:
        time_str (str): 변환할 시간 문자열 (HH:MM:SS 형식)
    
    Returns:
        float: 총 초 수
    """
    parts = time_str.split(':')
    
    if len(parts) == 3:  # HH:MM:SS 형식
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:  # MM:SS 형식
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    else:
        raise ValueError("시간 형식은 'HH:MM:SS' 또는 'MM:SS' 형식이어야 합니다.")