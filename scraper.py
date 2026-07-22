import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin  # 링크 깨짐 방지를 위해 추가

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://home.knu.ac.kr/HOME/aic/sub.htm?nav_code=aic1635293208"

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"텔레그램 전송 결과: {res.status_code} (200이면 성공!)")

def check_new_notice():
    # ★ 1. 사람이 크롬 브라우저로 접속하는 것처럼 위장하는 헤더 추가 (필수!)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # ★ 2. > tbody > 를 지우고, 일반 공지(2번째 줄)를 가져오는 가장 안전한 선택자로 변경!
    # (고정 공지가 1개라고 가정할 때, 목록에서 2번째 글을 선택합니다)
    latest_post = soup.select_one('.board_list table tr:nth-of-type(2) td.subject a')
    
    # 만약 위 선택자로도 실패할 경우를 대비한 비상 플랜 (목록의 2번째 링크를 자동으로 잡음)
    if not latest_post:
        posts = soup.select('.board_list td.subject a')
        if len(posts) >= 2:
            latest_post = posts[1]  # 0번은 고정 공지, 1번이 두 번째(일반 최신) 공지!
        elif len(posts) == 1:
            latest_post = posts[0]
            
    if not latest_post:
        print("🚨 에러: 웹페이지에서 공지사항 글을 전혀 찾지 못했습니다! 선택자를 다시 확인해주세요.")
        return
        
    latest_title = latest_post.text.strip()
    
    # ★ 3. 링크 주소가 이상하게 붙어서 깨지는 현상 방지 (urljoin 사용)
    latest_link = urljoin("https://home.knu.ac.kr", latest_post.get('href', ''))

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
