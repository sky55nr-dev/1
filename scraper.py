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
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
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

    # ★ 실전 모드: 이전에 저장된 최신글 제목(latest_notice.txt) 불러오기
    last_title = ""
    if os.path.exists("latest_notice.txt"):
        with open("latest_notice.txt", "r", encoding="utf-8") as f:
            last_title = f.read().strip()
            
    print(f"📁 파일에 기록되어 있던 이전 글 제목: {last_title}")

    # ★ 비교 판단: 웹사이트 최신글이 이전 글과 '다를 때만' 알림 전송!
    if latest_title != last_title:
        print("🚨 새로운 공지사항 발견! AI가 본문 요약 정리를 시작합니다...")
        
        raw_content = get_notice_content(latest_link, headers)
        ai_summary = summarize_with_ai(raw_content)
        
        message = (
            f"🔔 [경북대 AIC 공지사항 핵심 정리]\n\n"
            f"📌 제목: {latest_title}\n\n"
            f"🤖 AI 3줄 요약 정리:\n{ai_summary}\n\n"
            f"🔗 원문 바로가기:\n{latest_link}"
        )
        send_telegram_message(message)
        
        # 알림을 보낸 뒤에는 새 글 제목을 파일에 덮어써서 다음 시간엔 안 오도록 기억시킴
        with open("latest_notice.txt", "w", encoding="utf-8") as f:
            f.write(latest_title)
        print("✅ 최신글 업데이트 및 AI 요약 알림 전송 완벽 성공!")
    else:
        # 제목이 똑같다면 메시지 전송 없이 조용히 종료!
        print("💤 새로 올라온 공지사항이 없습니다. (알림 전송 안 함)")

if __name__ == "__main__":
    check_new_notice()
