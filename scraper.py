import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://aic.knu.ac.kr/"

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"텔레그램 전송 결과: {res.status_code} (200이면 성공!)")

def check_new_notice():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # ★ 이 아래 따옴표 안에 아까 복사하신 선택자를 넣으세요!
    latest_post = soup.select_one('#body_content > div > div.board_list > table > tbody > tr:nth-child(2) > td.subject > a')
    
    if not latest_post:
        print("🚨 에러: 웹페이지에서 공지사항 글을 전혀 찾지 못했습니다! 선택자를 다시 확인해주세요.")
        return
        
    latest_title = latest_post.text.strip()
    link_path = latest_post.get('href', '')
    latest_link = link_path if link_path.startswith('http') else "https://aic.knu.ac.kr" + link_path

    print(f"✅ 웹사이트에서 읽어온 최신글 제목: {latest_title}")

    # 처음 테스트할 때는 무조건 메시지를 보내도록 강제 실행!
    message = f"[새 공지사항 테스트 알림]\n제목: {latest_title}\n링크: {latest_link}"
    send_telegram_message(message)
    
    # 이제 성공했으니 latest_notice.txt 파일도 강제로 만듭니다!
    with open("latest_notice.txt", "w", encoding="utf-8") as f:
        f.write(latest_title)
    print("✅ latest_notice.txt 파일 생성 완료!")

if __name__ == "__main__":
    check_new_notice()
