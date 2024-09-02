from .places_routes import places_bp

def init_routes(app):
    """애플리케이션에 라우트를 등록하는 함수."""
    app.register_blueprint(places_bp, url_prefix='/api/places')
    # 다른 블루프린트도 여기에 등록합니다.
