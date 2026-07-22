import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google import genai  # ★ 구글 AI 최신 라이브러리 추가

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
URL = "https://home.knu.ac.kr/HOME/aic/sub.htm?nav_code=aic1635293208"

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"👉 텔레그램 전송 결과: {res.status_code} (200이면 메시지 발송 성공!)")

# ★ 본문을 AI에게 넘겨 깔끔하게 요약 정리받는 함수!
def summarize_with_ai(content_text):
    if not GEMINI_API_KEY:
        return "⚠️ 구글 AI 키가 설정되지 않아 원본 앞부분만 표시합니다:\n" + content_text[:200]
        
    try:
        # 구글의 가장 빠르고 똑똑한 최신 모델(gemini-2.5-flash) 사용
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = (
            "너는 대학생을 위한 친절하고 똑똑한 AI 비서야. "
            "아래의 대학교 공지사항 본문 내용을 읽고, 학생이 알아야 할 핵심 내용(신청 기간, 대상, 혜택, 장소 등 중요한 정보)을 "
            "가장 깔끔하고 읽기 쉽게 '개조식(• 기호 사용) 3줄 요약 정리' 형태로 작성해 줘. "
            "인사말이나 불필요한 서론은 빼고 오직 요약된 내용만 답해.\n\n"
            f"[공지사항 본문]\n{content_text[:3000]}"
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"AI 요약 중 에러 발생: {e}")
        return "⚠️ AI 요약 중 오류가 발생하여 본문 일부를 표시합니다:\n" + content_text[:200]

def get_notice_content(notice_url, headers):
    try:
        res = requests.get(notice_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        content_area = soup.select_one('.board_view_con, .view_con, .board_view_content, td.content, .view_cont, #board_view, #body_content, .sub_cont')
            
        if content_area:
            for script in content_area(["script", "style"]):
                script.decompose()
            text = content_area.text.strip()
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(lines)
        return "본문 내용을 불러오지 못했습니다."
    except Exception as e:
        return "본문 로딩 중 문제가 발생했습니다."

def check_new_notice():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 2번째 줄(일반 최신 공지) 가져오기
    latest_post = soup.select_one('.board_list table tr:nth-of-type(2) td.subject a')
    if not latest_post:
        posts = soup.select('.board_list td.subject a')
        if len(posts) >= 2:
            latest_post = posts[1]
        elif len(posts) == 1:
            latest_post = posts[0]
            
    if not latest_post:
        print("🚨 에러: 게시글을 찾지 못했습니다.")
        return
        
    latest_title = latest_post.text.strip()
    latest_link = urljoin("https://home.knu.ac.kr", latest_post.get('href', ''))
    print(f"✅ 웹사이트에서 확인한 최신글 제목: {latest_title}")

    # ★ [현재 테스트 모드] AI가 정리한 본문을 즉시 확인하기 위해 무조건 알림을 보냅니다!
    print("🤖 AI 비서가 본문을 열심히 읽고 핵심 요약 정리를 하는 중입니다...")
    
    raw_content = get_notice_content(latest_link, headers)
    ai_summary = summarize_with_ai(raw_content)
    
    message = (
        f"🔔 [경북대 AIC 공지사항 핵심 정리]\n\n"
        f"📌 제목: {latest_title}\n\n"
        f"🤖 AI 3줄 요약 정리:\n{ai_summary}\n\n"
        f"🔗 원문 바로가기:\n{latest_link}"
    )
    send_telegram_message(message)
    
    with open("latest_notice.txt", "w", encoding="utf-8") as f:
        f.write(latest_title)
    print("✅ AI 요약 정리 알림 발송 완료!")

if __name__ == "__main__":
    check_new_notice()
