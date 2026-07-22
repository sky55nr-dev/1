import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 깃허브 금고(Secrets)에서 안전하게 비밀번호를 가져옵니다.
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://home.knu.ac.kr/HOME/aic/sub.htm?nav_code=aic1635293208"

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"👉 텔레그램 전송 결과: {res.status_code} (200이면 성공!)")

def check_new_notice():
    # 1. 브라우저 위장 접속
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 2. 확인하신 2번째 줄(일반 최신 공지) 가져오기
    latest_post = soup.select_one('.board_list table tr:nth-of-type(2) td.subject a')
    
    if not latest_post:
        posts = soup.select('.board_list td.subject a')
        if len(posts) >= 2:
            latest_post = posts[1]
        elif len(posts) == 1:
            latest_post = posts[0]
            
    if not latest_post:
        print("🚨 에러: 웹페이지에서 공지사항 글을 찾지 못했습니다.")
        return
        
    latest_title = latest_post.text.strip()
    latest_link = urljoin("https://home.knu.ac.kr", latest_post.get('href', ''))
    print(f"✅ 웹사이트에서 확인한 최신글 제목: {latest_title}")

    # 3. ★ 핵심: 이전에 저장된 최신글 제목(latest_notice.txt) 읽어오기
    last_title = ""
    if os.path.exists("latest_notice.txt"):
        with open("latest_notice.txt", "r", encoding="utf-8") as f:
            last_title = f.read().strip()
            
    print(f"📁 파일에 저장되어 있던 이전 글 제목: {last_title}")

    # 4. ★ 비교 판단: 지금 웹사이트 글 제목이 이전 글 제목과 '다를 때만' 알림 전송!
    if latest_title != last_title:
        print("🚨 새로운 공지사항 발견! 텔레그램으로 알림을 전송합니다.")
        message = f"[경북대 AIC 새 공지사항]\n제목: {latest_title}\n링크: {latest_link}"
        send_telegram_message(message)
        
        # 새 글 제목을 최신으로 덮어써서 다음 시간엔 또 안 오도록 저장
        with open("latest_notice.txt", "w", encoding="utf-8") as f:
            f.write(latest_title)
        print("✅ latest_notice.txt 파일 업데이트 완료!")
    else:
        # 제목이 똑같다면 메시지 전송 없이 조용히 종료!
        print("💤 새로 올라온 공지사항이 없습니다. (메시지 전송 안 함)")

if __name__ == "__main__":
    check_new_notice()
