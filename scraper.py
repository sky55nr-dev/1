import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google import genai

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
URL = "https://home.knu.ac.kr/HOME/aic/sub.htm?nav_code=aic1635293208"

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"👉 텔레그램 전송 결과: {res.status_code} (200이면 메시지 발송 성공!)")

def summarize_with_ai(content_text):
    if not GEMINI_API_KEY:
        return "⚠️ [에러 원인] 깃허브 Secrets에 GEMINI_API_KEY가 설정되지 않았습니다!"
        
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        safe_text = content_text[:1500]
        
        prompt = (
            "너는 대학생을 위한 친절하고 똑똑한 AI 비서야. "
            "아래의 대학교 공지사항 본문 내용을 읽고, 학생이 알아야 할 핵심 내용(신청 기간, 대상, 혜택, 장소 등 중요한 정보)을 "
            "가장 깔끔하고 읽기 쉽게 '개조식(• 기호 사용) 3줄 요약 정리' 형태로 작성해 줘. "
            "인사말이나 불필요한 서론은 빼고 오직 요약된 내용만 답해.\n\n"
            f"[공지사항 본문]\n{safe_text}"
        )
        
        # ★ 핵심 수정: 지원이 종료된 1.5 대신 작동하는 최신 'gemini-2.5-flash'로 수정했습니다!
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"AI 요약 중 에러 발생: {e}")
        return f"⚠️ [AI 에러 원인]: {str(e)[:100]}"

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

    # [테스트 모드] AI 요약 알림을 즉시 발송합니다!
    print("🤖 AI 비서가 본문을 요약하는 중...")
    
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
    print("✅ 테스트 알림 발송 완료!")

if __name__ == "__main__":
    check_new_notice()
