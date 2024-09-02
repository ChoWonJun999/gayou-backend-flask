# 프로젝트 이름

Flask와 React를 사용한 웹 애플리케이션 프로젝트

## 개요

이 프로젝트는 Python의 Flask를 사용하여 RESTful API를 제공하는 백엔드 애플리케이션입니다. Flask는 MySQL 데이터베이스와 통합되어 데이터 CRUD(Create, Read, Update, Delete) 기능을 지원합니다. 또한 `APScheduler`를 사용하여 주기적으로 공공 데이터 API에서 데이터를 수집하는 기능을 포함하고 있습니다.

## 주요 기능

- **REST API**: Flask를 사용하여 RESTful API 엔드포인트를 제공합니다.
- **데이터베이스**: MySQL 데이터베이스를 사용하여 데이터 관리.
- **백그라운드 스케줄러**: `APScheduler`를 사용하여 주기적으로 공공 데이터 API에서 데이터를 수집합니다.
- **CORS 설정**: 특정 도메인에서만 API에 접근할 수 있도록 CORS 설정을 관리합니다.
- **React 프론트엔드**: React를 사용하여 사용자 인터페이스를 제공합니다.

## 설치 및 실행

### 사전 요구 사항

- Python 3.8
- MySQL 데이터베이스

### 백엔드(Flask) 설정

**가상 환경 설정**

```bash
 python -m venv venv
 source venv/bin/activate  # Linux/MacOS
 venv\Scripts\activate     # Windows
```

**필요 패키지 설치**

```bash
 pip install -r requirements.txt
```

**환경 변수 설정**

```makefile
 FLASK_ENV=development
 SERVICE_KEY=YOUR_SERVICE_KEY
 DB_HOST=your_host
 DB_USER=your_name
 DB_PASSWORD=your_password
 DB_NAME=your_db_name
```

**데이터베이스 설정**

```sql
 CREATE DATABASE your_db_name;
```

**Flask 서버 실행**

```bash
 set FLASK_APP=run.py
 flask run
```
