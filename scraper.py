import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://home.knu.ac.kr/HOME/aic/sub.htm?nav_code=aic1635293208"

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"👉 텔레그램 전송 결과: {res.status_code} (200이면 메시지 발송 성공!)")

def get_notice_content(notice_url, headers):
    try:
        res = requests.get(notice_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 경북대 게시판의 본문 영역을 찾기 위한 다양한 선택자
        content_area = soup.select_one('.board_view_con, .view_con, .board_view_content, td.content, .view_cont, #board_view')
        
        if not content_area:
            content_area = soup.select_one('#body_content, .sub_cont')
            
        if content_area:
            for script in content_area(["script", "style"]):
                script.decompose()
                
            text = content_area.text.strip()
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)
            
            # 본문이 너무 길면 350자에서 자르기
            if len(clean_text) > 350:
                return clean_text[:350] + "\n\n...(이하 생략. 전체 내용은 링크에서 확인하세요!)"
            return clean_text
        else:
            return "본문 요약을 불러오지 못했습니다. 링크를 클릭해 확인해주세요!"
    except Exception as e:
        return "본문 로딩 중 문제가 발생했습니다. 링크를 클릭해 확인해주세요!"

def check_new_notice():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 일반 최신 공지 (2번째 줄) 가져오기
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

    # ★ 테스트 모드: 이전 글 비교를 무시하고 무조건 본문을 읽어와서 발송!
    print("🚨 [테스트 모드 작동] 본문 내용을 읽어와서 강제로 메시지를 발송합니다...")
    
    content_summary = get_notice_content(latest_link, headers)
    
    message = (
        f"🔔 [본문 미리보기 기능 테스트 알림]\n\n"
        f"📌 제목: {latest_title}\n\n"
        f"📄 본문 미리보기:\n{content_summary}\n\n"
        f"🔗 바로가기 링크:\n{latest_link}"
    )
    send_telegram_message(message)
    
    with open("latest_notice.txt", "w", encoding="utf-8") as f:
        f.write(latest_title)
    print("✅ 테스트 알림 발송 완료!")

if __name__ == "__main__":
    check_new_notice()
