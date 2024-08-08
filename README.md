RepellingServerPython<br><br>
서버: ssh kku@222.116.135.70 -p 9922<br>
실행방법<br>
Conda activate base<br> 
uvicorn main:app --host 0.0.0.0 --port 8000<br><br>
Nohup uvicorn main:app --host 0.0.0.0 --port 8000(백그라운드 실행, kill 명령어로 종료)

새로운 쉘: ps -ef | grep uvicorn

실행결과 확인: code nohup.out

docs문서보기: http://127.0.0.1:8000/redoc<br>
스웨거 문서보기: http://127.0.0.1:8000/docs<br>
