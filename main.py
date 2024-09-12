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
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError

# baseurl = "http://222.116.135.70:8080/"

# JWT 설정
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# import pymysql
import pymysql

server_db = pymysql.connect(
    user='kku', 
    passwd='kkukku415', 
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
DATABASE_URL = "mysql+mysqlconnector://kku:kkukku415@localhost/repellerDB"
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
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gateway_id = Column(Integer, primary_key=True, index=True)
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

#테이블이 이미 생성되어있다면 작동하지 X
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

class UpdateNameRequest(BaseModel):
    name: str

class UpdateFarmNameRequest(BaseModel):
    name: str

class UpdateFarmAddressRequest(BaseModel):
    address: str

class CreateFarmRequest(BaseModel):
    gateway_id: int # 나중에  DB수정하면 gateway_serial_id로 바꿀것
    address: str
    member_id: int
    farm_type: str
    name: str
    #farm_id는 자동 증가

class CreateGatewayRequest(BaseModel):
    is_activated: bool
    ipv4: str
    serial_id: str
    #gateway_id 자동 증가

class CreateRepellentDeviceRequest(BaseModel):
    farm_id: int
    serial_id: str
    name: str
    latitude: str
    longitude: str
    is_activated: bool = False
    is_working: bool = True

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

# JWT 토큰 생성 함수
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 현재 사용자 가져오기
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    user = db.query(Member).filter(Member.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/api/v1/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Member).filter(Member.login_id == request.loginId).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# 로그인 유저의 회원정보 불러오기
@app.get("/api/v1/members/me")
async def get_member_me(current_user: Member = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        member = db.query(Member).filter(Member.id == current_user.id).first()

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return {
            "member_id": member.id,
            "name": member.name,
            "login_id": member.login_id,
            "email": member.email
        }
    
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 로그인 유저의 기기정보 불러오기
@app.get("/api/v1/repellent_device/me")
async def get_my_device(current_user: Member = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        repellent_device = db.query(
            RepellentDevice.id,
            RepellentDevice.name,
            RepellentDevice.is_activated,
            RepellentDevice.is_working,
            RepellentDevice.latitude,
            RepellentDevice.longitude
        ).join(Farm).filter(Farm.member_id == current_user.id).all()
        
        if not repellent_device:
            raise HTTPException(status_code=404, detail="No device for this user")
        return [
            {
                "device_id": device.id,
                "name": device.name,
                "is_activated": device.is_activated,
                "is_working": device.is_working,
                "latitude": device.latitude,
                "longitude": device.longitude
            }
            for device in repellent_device
        ]
    
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



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
            id=None,  # ID
            gateway_id=gateway.serial_id,  # gateway ID를 사용하여 gateway_id 필드에 저장
            re_detection_minutes=5,  # 필요 시 계산
            repellent_device_id=request.nodeId,  # 필요 시 실제 데이터 사용
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
'''
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
'''
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
    
@app.put("/api/v1/farmname/{farm_id}")
async def update_farm_name(farm_id: int, request: UpdateFarmNameRequest, db: Session = Depends(get_db)):
    try:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()

        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")

        farm.name = request.name
        db.commit()
        db.refresh(farm)

        return {"message": "Farm name updated successfully", "farm_id": farm.id, "name": farm.name}
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.put("/api/v1/farmaddress/{farm_id}")
async def update_farm_address(farm_id: int, request: UpdateFarmAddressRequest, db: Session = Depends(get_db)):
    try:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()

        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")

        farm.address = request.address
        db.commit()  
        db.refresh(farm)

        return {"message": "Farm address updated successfully", "farm_id": farm.id, "address": farm.address}
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

@app.post("/api/v1/farmcreate")
async def create_farm(request: CreateFarmRequest, db: Session = Depends(get_db)):
    try:
        print(f"Received request: {request}")

        new_farm = Farm(
            gateway_id=request.gateway_id,
            address=request.address,
            member_id=request.member_id,
            farm_type=request.farm_type,
            name=request.name
        )
        
        db.add(new_farm)
        db.commit()
        db.refresh(new_farm)
        
        return {"message": "Farm created successfully", "farm_id": new_farm.id, "name": new_farm.name}
    
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/api/v1/farm/{farm_id}")
async def delete_farm(farm_id: int, db: Session = Depends(get_db)):
    try:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()

        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")

        db.delete(farm)
        db.commit()

        return {"message": "Farm deleted successfully", "farm_id": farm_id}
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/api/v1/farm/list")
async def get_farm_list(authorization: str = Header(None), db: Session = Depends(get_db)):
    try:
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

#게이트웨이 추가
@app.post("/api/v1/gatewaycreate")
async def create_gateway(request: CreateGatewayRequest, db: Session = Depends(get_db)):
    try:
        existing_gateway = db.query(Gateway).filter(Gateway.serial_id == request.serial_id).first()
        if existing_gateway:
            raise HTTPException(status_code=400, detail="Gateway with this serial_id already exists")

        new_gateway = Gateway(
            is_activated=request.is_activated,
            ipv4=request.ipv4,
            serial_id=request.serial_id
        )
        
        db.add(new_gateway)
        db.commit()
        db.refresh(new_gateway) 
        
        return {"message": "Gateway created successfully", "gateway_id": new_gateway.id}
    
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
    
@app.post("/api/v1/repellent-devicecreate")
async def create_device(request: CreateRepellentDeviceRequest, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == request.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    existing_device = db.query(RepellentDevice).filter(RepellentDevice.serial_id == request.serial_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Device with this serial_id already exists")

    new_RepellentDevice = RepellentDevice(
        farm_id=request.farm_id,
        serial_id=request.serial_id,
        name=request.name,
        latitude=request.latitude,
        longitude=request.longitude,
        is_activated=request.is_activated,
        is_working=request.is_working
    )

    db.add(new_RepellentDevice)
    db.commit()
    db.refresh(new_RepellentDevice)

    return {"message": "Device created successfully", "device_id": new_RepellentDevice.id}

@app.delete("/api/v1/device/{device_id}")
async def delete_repellentdevice(device_id: int, db: Session = Depends(get_db)):
    try:
        repellentdevice = db.query(RepellentDevice).filter(RepellentDevice.id == device_id).first()

        if not repellentdevice:
            raise HTTPException(status_code=404, detail="Worng device number")

        db.delete(repellentdevice)
        db.commit()

        return {"message": "Your Device deleted successfully", "device_id": device_id}
    
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
async def get_group_farm_data(farmId: int, db: Session = Depends(get_db)):
    try:
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


@app.get("/api/v1/members")
async def get_members(db: Session = Depends(get_db)):
    try:
        members = db.query(Member).all()
        return members
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/api/v1/members/{member_id}")
async def get_member_by_id(member_id: int, db: Session = Depends(get_db)):
    try:
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return member
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.put("/api/v1/membername/{member_id}")
async def update_member_name(member_id: int, request: UpdateNameRequest, db: Session = Depends(get_db)):
    try:
        member = db.query(Member).filter(Member.id == member_id).first()

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        member.name = request.name
        db.commit()
        db.refresh(member)

        return {"message": "Name updated successfully", "member": {"id": member.id, "name": member.name}}
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/v1/member/{member_id}/farms")
async def get_farms_by_member_id(member_id: int, db: Session = Depends(get_db)):
    try:
        farms_with_gateway = db.query(Farm, Gateway.id.label("gateway_id")).join(Gateway, Farm.gateway_id == Gateway.id).filter(Farm.member_id == member_id).all()
        if not farms_with_gateway:
            raise HTTPException(status_code=404, detail="No farms found for this member")

        return [
            {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "address": farm.address,
                "farm_type": farm.farm_type,
                "gateway_id": gateway_id
            } for farm, gateway_id in farms_with_gateway
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
    uvicorn.run("main:app", host="222.116.135.70", port=8080, reload=True)
