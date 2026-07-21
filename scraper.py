import os
import requests
from bs4 import BeautifulSoup

# 텔레그램 설정값 가져오기 (GitHub Secrets 활용)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 공지사항 웹사이트 주소
URL = "https://aic.knu.ac.kr/" # 실제 공지사항 게시판 목록 URL로 변경 필요

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})

def check_new_notice():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 공지사항 목록에서 가장 최신 글 제목 추출 (HTML 구조에 맞게 태그 수정 필요)
    # 예시: 최신 글이 <td class="title"><a href="...">제목</a></td> 형태일 경우
    latest_post = soup.select_one('#body_content > div > div.board_list > table > tbody > tr:nth-child(2) > td.subject > a') # 웹페이지 구조에 맞춰 변경
    
    if not latest_post:
        return
        
    latest_title = latest_post.text.strip()
    latest_link = "https://aic.knu.ac.kr/" + latest_post.get('href', '')

    # 이전에 저장된 최신 글 제목 읽기
    last_title = ""
    if os.path.exists("latest_notice.txt"):
        with open("latest_notice.txt", "r", encoding="utf-8") as f:
            last_title = f.read().strip()

    # 새 글이 등록되었는지 비교
    if latest_title != last_title:
        message = f"[새 공지사항 알림]\n제목: {latest_title}\n링크: {latest_link}"
        send_telegram_message(message)
        
        # 최신 글 제목을 파일에 덮어쓰기
        with open("latest_notice.txt", "w", encoding="utf-8") as f:
            f.write(latest_title)

if __name__ == "__main__":
    check_new_notice()