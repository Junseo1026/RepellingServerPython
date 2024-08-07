from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import bcrypt
import logging
from collections import defaultdict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# import pymysql
import pymysql

#DB는 Mac미니 사용
server_db = pymysql.connect( 
    user='root',
    passwd='',
    host='127.0.0.1',
    db='repellerDB', 
    charset='utf8'
)

# Prepared statement 사용 sql
# sql = "SELECT * FROM member WHERE id = %s"
# id_value = '1'  # id 값 설정

# cursor = server_db.cursor(pymysql.cursors.DictCursor)
# cursor.execute(sql, (id_value,))
# result = cursor.fetchone()

# if result:
#     print(result['email'])
# else:
#     print("No result found")

# cursor.close()
# server_db.close()

# server_db.commit() # DB를 업데이트, 수정, 추가 삭제등 할경우 db commit이 필요.
# 단순히 fetch하는 경우는 필요 없음.
# fetchone()은 한개만 fetch, fetchall()은 List형태로 fetch


# http://222.116.135.70
#  /api/v1/repellent-data/detail/group-farm/farm/1


# 데이터베이스 설정
#DATABASE_URL = "mysql+mysqlconnector://kku:kkukku415@localhost/repellerDB" #대학원실 mysql
DATABASE_URL = "mysql+pymysql://root:@127.0.0.1/repellerDB"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 데이터베이스 모델
class Farm(Base):
    __tablename__ = 'farm'
    
    id = Column(Integer, primary_key=True, index=True)
    gateway_id = Column(Integer, ForeignKey('gateway.id'), nullable=False)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False)
    address = Column(String, nullable=False)
    farm_type = Column(String, nullable=False)
    name = Column(String, nullable=False)

class Gateway(Base):
    __tablename__ = 'gateway'
    
    id = Column(Integer, primary_key=True, index=True)
    is_activated = Column(Boolean, default=False)
    ipv4 = Column(String, nullable=False)
    serial_id = Column(String, nullable=False, unique=True)

class Member(Base):
    __tablename__ = 'member'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    login_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)

class RefreshToken(Base):
    __tablename__ = 'refresh_token'
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False)
    refresh_token = Column(String, nullable=False)

class RepellentData(Base):
    __tablename__ = 'repellent_data'
    
    detection_date = Column(DateTime, nullable=False)
    detection_num = Column(Integer, nullable=False)
    detection_time = Column(String, nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    re_detection_minutes = Column(Integer, nullable=True)
    repellent_device_id = Column(Integer, ForeignKey('repellent_device.id'), nullable=False)
    repellent_sound_id = Column(Integer, ForeignKey('repellent_sound.id'), nullable=False)
    detection_type = Column(String, nullable=False)

class RepellentDevice(Base):
    __tablename__ = 'repellent_device'
    
    id = Column(Integer, primary_key=True, index=True)
    is_activated = Column(Boolean, default=False)
    is_working = Column(Boolean, default=True)
    farm_id = Column(Integer, ForeignKey('farm.id'), nullable=False)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    name = Column(String, nullable=False)
    serial_id = Column(String, nullable=False, unique=True)

class RepellentSound(Base):
    __tablename__ = 'repellent_sound'
    
    id = Column(Integer, primary_key=True, index=True)
    sound_name = Column(String, nullable=False)
    sound_level = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)

# Pydantic 모델
class FarmResponse(BaseModel):
    farmId: int
    farmName: str
    deviceCount: int
    farmAddress: str

class RepellentDataRequest(BaseModel):
    gatewayId: str
    nodeId: str
    message: str
    soundType: str
    soundLevel: int
    timestamp: str
    detectionType: str
    detectedCount: int

class LoginRequest(BaseModel):
    loginId: str
    password: str

class RegisterRequest(BaseModel):
    loginId: str
    password: str
    name: str
    email: str

class MainPageDataResponse(BaseModel):
    data: List[RepellentDataRequest]

class DayByDetectionListResponse(BaseModel):
    detectedAt: str
    detectionType: str
    count: int

class HourByDetectionListResponse(BaseModel):
    detectedAt: str
    detectionType: str
    count: int

class DailyDetectionListResponse(BaseModel):
    detectedAt: str
    detectionType: str
    count: int

class ReDetectionMinutesAndRepellentSoundResponse(BaseModel):
    detectionTime: str
    reDetectionMinutes: int
    repellentSound: str

class SerialIdCheckResponse(BaseModel):
    isSerialIdExists: bool

class CertificationResponse(BaseModel):
    certificationNumber: str

class LoginResponse(BaseModel):
    name: str

class FindIdResponse(BaseModel):
    loginId: str

# FastAPI 애플리케이션 설정
app = FastAPI()

# Swagger 설정
swagger_ui_parameters={
    "deepLinking": True,
    "displayRequestDuration": True,
    "docExpansion": "none",
    "operationsSorter": "method",
    "filter": True,
    "tagsSorter": "alpha",
    "syntaxHighlight.theme": "tomorrow-night",
}

# 데이터베이스 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 비밀번호 확인 함수
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# 라우터 설정
@app.get("/api/v1/farm/setting/list")
async def get_farm_setting_list(authorization: str = Header(None), db: Session = Depends(get_db)):
    try:
        farms = db.query(
            Farm.id.label("farmId"),
            Farm.name.label("farmName"),
            Farm.address.label("farmAddress")
        ).all()

        farm_responses = []
        for farm in farms:
            device_count = db.query(RepellentDevice).filter(RepellentDevice.farm_id == farm.farmId).count()
            farm_response = FarmResponse(
                farmId=farm.farmId,
                farmName=farm.farmName,
                deviceCount=device_count,
                farmAddress=farm.farmAddress
            )
            farm_responses.append(farm_response)

        return farm_responses
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/v1/repellent-data")
async def repellent_data(request: RepellentDataRequest, db: Session = Depends(get_db)):
    try:
        
        gateway = db.query(Gateway).filter_by(serial_id=request.gatewayId).first()
        if not gateway:
            raise HTTPException(status_code=404, detail="Gateway not found")
        # print(request)
        date_part, time_part = request.timestamp.split(',')
        # 날짜 부분만 파싱
        detection_date = datetime.strptime(date_part, '%Y-%m-%d').date()
        detection_datetime = datetime.strptime(f"{date_part} {time_part.strip()}", '%Y-%m-%d %H:%M:%S')
    
        detection_time = datetime.strptime(time_part.strip(), '%H:%M:%S').time()
        db_data = RepellentData(
            detection_date=detection_datetime.date(),
            detection_num = request.detectedCount,
            detection_time=detection_datetime,  # `datetime` 객체로 저장
            id=None,  # gateway ID를 사용
            re_detection_minutes=5,  # 필요 시 계산
            repellent_device_id=1,  # 필요 시 실제 데이터 사용
            repellent_sound_id=1,  # 필요 시 실제 데이터 사용
            detection_type=request.detectionType
        )
        db.add(db_data)
        db.commit()
        db.refresh(db_data)
        return JSONResponse(status_code=200, content={"message": "Data created successfully"})
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 로그인 / 토큰 같이 넘겨줘야함 수정필요
@app.post("/api/v1/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        # 요청 데이터 로그 출력
        logger.info(f"Login request data: {request.model_dump()}")

        # 데이터베이스 쿼리 시도
        user = db.query(Member).filter_by(login_id=request.loginId).first()
        if not user or not verify_password(request.password, user.password):
            logger.warning("Invalid credentials")
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # 성공적으로 로그인
        logger.info(f"User {user.name} logged in successfully")
        return JSONResponse(content={"name": user.name}, headers={
            "Authorization": "accessToken",
            "Set-Cookie": "refreshToken=refreshToken; Max-Age=1209600; Expires=Sun, 02 Jun 2024 08:33:53 GMT; HttpOnly"
        })
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@app.post("/api/v1/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        db_user = Member(
            login_id=request.loginId,
            password=request.password,
            name=request.name,
            email=request.email
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"message": "Registration successful"}
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/certification")
async def send_certification(email: str):
    return CertificationResponse(certificationNumber="123456")

@app.get("/api/v1/find/id")
async def find_id(name: str, email: str, db: Session = Depends(get_db)):
    try:
        user = db.query(Member).filter_by(name=name, email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return FindIdResponse(loginId=user.login_id)
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/farm/list")
async def get_farm_list(authorization: str = Header(None), db: Session = Depends(get_db)):
    try:
        # 모든 farm 데이터를 조인하여 쿼리
        result = db.query(
            Farm.id.label("farm_id"),
            Farm.name.label("farm_name"),
            Farm.address.label("farm_address"),
            Farm.farm_type.label("farm_type"),
            Gateway.id.label("gateway_id"),
            Gateway.serial_id.label("gateway_serialId"),
            Gateway.ipv4.label("gateway_ipv4"),
            Gateway.is_activated.label("gateway_isActivated"),
            RepellentDevice.id.label("repellentDevice_id"),
            RepellentDevice.serial_id.label("repellentDevice_serialId"),
            RepellentDevice.name.label("repellentDevice_name"),
            RepellentDevice.latitude.label("repellentDevice_latitude"),
            RepellentDevice.longitude.label("repellentDevice_longitude"),
            RepellentDevice.is_working.label("repellentDevice_isWorking"),
            RepellentData.id.label("repellentData_id"),
            RepellentData.detection_type.label("repellentData_detectionType"),
            RepellentData.detection_num.label("repellentData_detectionNum"),
            RepellentData.detection_time.label("repellentData_detectionTime"),
            RepellentData.detection_date.label("repellentData_detectionDate"),
            RepellentData.re_detection_minutes.label("repellentData_reDetectionMinutes"),
            RepellentSound.id.label("repellentSound_id"),
            RepellentSound.sound_name.label("repellentSound_soundName"),
            RepellentSound.sound_level.label("repellentSound_soundLevel")
        ).join(
            Gateway, Farm.gateway_id == Gateway.id
        ).outerjoin(
            RepellentDevice, Farm.id == RepellentDevice.farm_id
        ).outerjoin(
            RepellentData, RepellentDevice.id == RepellentData.repellent_device_id
        ).outerjoin(
            RepellentSound, RepellentData.repellent_sound_id == RepellentSound.id
        ).all()

        farms_dict = defaultdict(lambda: {
            "id": None,
            "name": None,
            "address": None,
            "farmType": None,
            "gateway": None,
            "repellentDevice": defaultdict(lambda: {
                "id": None,
                "serialId": None,
                "name": None,
                "latitude": None,
                "longitude": None,
                "isWorking": None,
                "repellentData": []
            })
        })

        for row in result:
            farm = farms_dict[row.farm_id]
            if not farm["id"]:
                farm["id"] = row.farm_id
                farm["name"] = row.farm_name
                farm["address"] = row.farm_address
                farm["farmType"] = row.farm_type
                farm["gateway"] = {
                    "id": row.gateway_id,
                    "serialId": row.gateway_serialId,
                    "ipv4": row.gateway_ipv4,
                    "isActivated": row.gateway_isActivated,
                }

            if row.repellentDevice_id:
                device = farm["repellentDevice"][row.repellentDevice_id]
                if not device["id"]:
                    device["id"] = row.repellentDevice_id
                    device["serialId"] = row.repellentDevice_serialId
                    device["name"] = row.repellentDevice_name
                    device["latitude"] = row.repellentDevice_latitude
                    device["longitude"] = row.repellentDevice_longitude
                    device["isWorking"] = row.repellentDevice_isWorking

                if row.repellentData_id:
                    device["repellentData"].append({
                        "id": row.repellentData_id,
                        "detectionType": row.repellentData_detectionType,
                        "detectionNum": row.repellentData_detectionNum,
                        "detectionTime": row.repellentData_detectionTime,
                        "detectionDate": row.repellentData_detectionDate,
                        "reDetectionMinutes": row.repellentData_reDetectionMinutes,
                        "repellentSound": {
                            "id": row.repellentSound_id,
                            "soundName": row.repellentSound_soundName,
                            "soundLevel": row.repellentSound_soundLevel,
                        }
                    })

        response_data = list(farms_dict.values())
        for farm in response_data:
            farm["repellentDevice"] = sorted(
                list(farm["repellentDevice"].values()), key=lambda x: x['id']
            )
            for device in farm["repellentDevice"]:
                device["repellentData"] = sorted(
                    device["repellentData"], key=lambda x: x['id']
                )

        return response_data

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@app.get("/api/v1/gateway/valid/serial-id")
async def check_gateway_serial_id(serialId: str, db: Session = Depends(get_db)):
    try:
        exists = db.query(Gateway).filter_by(serial_id=serialId).first() is not None
        return SerialIdCheckResponse(isSerialIdExists=exists)
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/repellent-device/valid/serial-id")
async def check_device_serial_id(serialId: str, farmId: int, db: Session = Depends(get_db)):
    try:
        exists = db.query(RepellentDevice).filter_by(serial_id=serialId, farm_id=farmId).first() is not None
        return SerialIdCheckResponse(isSerialIdExists=exists)
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/repellent-data/main")
async def get_repellent_data_main(farmId: int, db: Session = Depends(get_db)):
    try:
        day_by_detection_list = db.query(
            RepellentData.detection_date.label("detectedAt"),
            RepellentData.detection_type.label("detectionType"),
            func.count(RepellentData.id).label("count")
        ).filter(
            RepellentData.farm_id == farmId
        ).group_by(
            RepellentData.detection_date,
            RepellentData.detection_type
        ).all()

        response = {
            "dayByDetectionList": [
                {
                    "detectedAt": data.detectedAt,
                    "detectionType": data.detectionType,
                    "count": data.count,
                }
                for data in day_by_detection_list
            ],
            "reDetectionTimeAvg": 13,  # 예제 값 사용
            "repellentSoundName": "소리명"  # 예제 값 사용
        }

        return response
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/repellent-data/detail/group-farm/farm/{farmId}")
# FIXME: RepellentData 테이블 에는 farmid가 없음 따리서 repellent_device 테이블에서 데이터 비교 후 farm_id를 가져와야 함.

async def get_group_farm_data(farmId: int, db: Session = Depends(get_db)):
    try:
        # repellent_device 테이블과 조인
        data = db.query(
            RepellentData.detection_date.label("detectedAt"),
            RepellentData.detection_type.label("detectionType"),
            func.count(RepellentData.id).label("count")
        ).join(
            RepellentDevice, RepellentDevice.id == RepellentData.repellent_device_id
        ).filter(
            RepellentDevice.farm_id == farmId
        ).group_by(
            RepellentData.detection_date,
            RepellentData.detection_type
        ).all()

        return [
            DayByDetectionListResponse(
                detectedAt=item.detectedAt.strftime("%Y-%m-%d"),  # 날짜를 문자열로 변환
                detectionType=item.detectionType,
                count=item.count
            )
            for item in data
        ]
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/repellent-data/detail/group-time/farm/{farmId}")
async def get_group_time_data(farmId: int, db: Session = Depends(get_db)):
    try:
        data = db.query(
            RepellentData.detection_time.label("detectedAt"),
            RepellentData.detection_type.label("detectionType"),
            func.count(RepellentData.id).label("count")
        ).filter(
            RepellentData.farm_id == farmId
        ).group_by(
            RepellentData.detection_time,
            RepellentData.detection_type
        ).all()

        return [
            HourByDetectionListResponse(detectedAt=item.detectedAt, detectionType=item.detectionType, count=item.count)
            for item in data
        ]
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/repellent-data/detail/group-detection-device/farm/{farmId}")
async def get_group_detection_device_data(farmId: int, db: Session = Depends(get_db)):
    try:
        data = db.query(
            RepellentDevice.name.label("repellentDeviceName"),
            RepellentData.detection_type.label("detectionType"),
            func.sum(RepellentData.detection_num).label("detectionNumSum")
        ).filter(
            RepellentData.farm_id == farmId
        ).group_by(
            RepellentDevice.name,
            RepellentData.detection_type
        ).all()

        return [
            {
                "repellentDeviceName": item.repellentDeviceName,
                "detectionType": item.detectionType,
                "detectionNumSum": item.detectionNumSum
            }
            for item in data
        ]
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/repellent-data/detail/detection-device-id/{detectionDeviceId}")
async def get_detection_device_data(detectionDeviceId: int, db: Session = Depends(get_db)):
    try:
        data = db.query(
            RepellentData.detection_date.label("detectedAt"),
            RepellentData.detection_type.label("detectionType"),
            func.count(RepellentData.id).label("count")
        ).filter(
            RepellentData.repellent_device_id == detectionDeviceId
        ).group_by(
            RepellentData.detection_date,
            RepellentData.detection_type
        ).all()

        return [
            DailyDetectionListResponse(detectedAt=item.detectedAt, detectionType=item.detectionType, count=item.count)
            for item in data
        ]
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/repellent-data/detail/detection/detection-device-id/{detectionDeviceId}")
async def get_recent_sounds_data(detectionDeviceId: int, db: Session = Depends(get_db)):
    try:
        data = db.query(
            RepellentData.detection_time.label("detectionTime"),
            RepellentData.re_detection_minutes.label("reDetectionMinutes"),
            RepellentSound.sound_name.label("repellentSound")
        ).join(
            RepellentSound, RepellentData.repellent_sound_id == RepellentSound.id
        ).filter(
            RepellentData.repellent_device_id == detectionDeviceId
        ).order_by(
            RepellentData.detection_time.desc()
        ).limit(4).all()

        return [
            ReDetectionMinutesAndRepellentSoundResponse(detectionTime=item.detectionTime, reDetectionMinutes=item.reDetectionMinutes, repellentSound=item.repellentSound)
            for item in data
        ]
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/")
def read_root():
    return {"Hello": "World"}

# FastAPI 테스트 클라이언트 설정 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="222.116.135.70", port=8081, reload=True)

