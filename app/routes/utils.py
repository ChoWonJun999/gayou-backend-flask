def validate_request_data(data, required_fields):
    """
    요청 데이터를 유효성 검사하는 함수.
    필수 필드가 모두 존재하는지 확인합니다.
    """
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    return True, None
