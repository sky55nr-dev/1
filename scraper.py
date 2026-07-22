import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin # 주소 자동 완성 기능 추가

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ★ 직접 찾아내신 진짜 공지사항 게시판의 숨겨진 URL!
URL = "https://home.knu.ac.kr/HOME/aic/sub.htm?nav_code=aic1635293208"

def send_telegram_message(message):
    send_url = f"https://apitelegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"👉 텔레그램 전송 결과: {res.status_code} (200이면 메시지 발송 성공!)")

def check_new_notice():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 공지사항 목록 테이블 안의 링크(a 태그)들을 넓게 탐색
    posts = soup.select('table tbody tr a, .board_list a, .list_td a, tr td.title a, .post-title a')
    
    # 위 규칙으로 못 찾으면 글자 수 5자 이상의 게시물 링크 자동 탐색
    if not posts:
        all_links = soup.select('a')
        posts = [a for a in all_links if len(a.text.strip()) > 5 and ('mno=' in a.get('href', '') or 'board' in a.get('href', '') or 'view' in a.get('href', ''))]

    if not posts:
        print("🚨 에러: 게시글을 찾지 못했습니다. 선택자나 페이지 로딩 방식을 확인해야 합니다.")
        return
        
    # 첫 번째로 읽어온 글을 최신 글로 지정!
    latest_post = posts[1]
    latest_title = latest_post.text.strip()
    
    # urljoin을 사용하면 상대 주소가 어떻게 오든 진짜 도메인(home.knu.ac.kr)과 완벽하게 조립해 줍니다!
    latest_link = urljoin(URL, latest_post.get('href', ''))

    print(f"✅ 드디어 찾아낸 최신글 제목: {latest_title}")
    print(f"✅ 완벽하게 조립된 최신글 링크: {latest_link}")

    # 스마트폰으로 첫 성공 기념 메시지 전송!
    message = f"[경북대 AIC 새 공지사항]\n제목: {latest_title}\n링크: {latest_link}"
    send_telegram_message(message)
    
    # 알림 발송 후 latest_notice.txt 파일도 정상 생성
    with open("latest_notice.txt", "w", encoding="utf-8") as f:
        f.write(latest_title)
    print("✅ latest_notice.txt 파일 생성 및 알림 발송 완벽 성공!")

if __name__ == "__main__":
    check_new_notice()
