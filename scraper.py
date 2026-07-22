import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 찾아내신 진짜 공지사항 게시판 URL
URL = "https://home.knu.ac.kr/HOME/aic/sub.htm?nav_code=aic1635293208"

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"👉 텔레그램 전송 결과: {res.status_code} (200이면 메시지 발송 성공!)")

def check_new_notice():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = soup.select('table tbody tr a, .board_list a, .list_td a, tr td.title a, .post-title a')
    
    if not posts:
        all_links = soup.select('a')
        posts = [a for a in all_links if len(a.text.strip()) > 5 and ('mno=' in a.get('href', '') or 'board' in a.get('href', '') or 'view' in a.get('href', ''))]

    if not posts:
        print("🚨 에러: 게시글을 찾지 못했습니다.")
        return
        
    # ★ 핵심 수정: 고정 공지 건너뛰기!
    # 방법 A) 무조건 고정 공지 1개를 건너뛰고 2번째 글 가져오기
    # latest_post = posts[1] 
    
    # 방법 B) 더 똑똑한 방법: 위에서부터 글을 순서대로 보면서 '공지'나 '필독'이 없는 첫 번째 일반 글을 찾기!
    latest_post = posts[0] # 기본값은 0번으로 설정
    for post in posts:
        title_text = post.text.strip()
        # 제목에 [공지], [필독], 공지, 필독 등의 단어가 포함되어 있으면 건너뜀 (사이트 맞춤 설정)
        if "[공지]" in title_text or "[필독]" in title_text or " [안내] " in title_text:
            continue
        # 고정 공지가 아닌 일반 글을 발견하면 그걸 최신 글로 확정하고 반복문 종료!
        latest_post = post
        break

    latest_title = latest_post.text.strip()
    latest_link = urljoin(URL, latest_post.get('href', ''))

    print(f"✅ 드디어 찾아낸 진짜 일반 최신글 제목: {latest_title}")
    print(f"✅ 완벽하게 조립된 최신글 링크: {latest_link}")

    message = f"[경북대 AIC 새 공지사항]\n제목: {latest_title}\n링크: {latest_link}"
    send_telegram_message(message)
    
    with open("latest_notice.txt", "w", encoding="utf-8") as f:
        f.write(latest_title)
    print("✅ latest_notice.txt 파일 생성 및 알림 발송 완벽 성공!")

if __name__ == "__main__":
    check_new_notice()
