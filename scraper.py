import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google import genai

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
URL = "https://home.knu.ac.kr/HOME/aic/sub.htm?nav_code=aic1635293208"
HISTORY_FILE = "notice_history.txt" # ★ 수십 개의 글을 기억할 새로운 메모장

def send_telegram_message(message):
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": message})
    print(f"👉 텔레그램 전송 결과: {res.status_code} (200이면 메시지 발송 성공!)")

def summarize_with_ai(content_text):
    if not GEMINI_API_KEY:
        return "⚠️ 깃허브 Secrets에 GEMINI_API_KEY가 없습니다!"
        
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
            model='gemini-3.5-flash-lite',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"AI 요약 중 에러 발생: {e}")
        return f"⚠️ (현재 AI 요약 일시 지연으로 원문 일부를 표시합니다)\n\n{content_text[:400]}..."

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
    
    # ★ 1. 게시판 1페이지에 있는 "모든" 글을 스캔해서 가져옵니다. (위치 상관 없음!)
    posts = soup.select('.board_list td.subject a')
    if not posts:
        posts = soup.select('.board_list table tr a')
        
    if not posts:
        print("🚨 에러: 게시글을 찾지 못했습니다.")
        return

    current_posts = []
    for post in posts:
        title = post.text.strip()
        link = urljoin("https://home.knu.ac.kr", post.get('href', ''))
        current_posts.append({'title': title, 'link': link})

    # ★ 2. 파이썬이 이전에 봤던 글들의 '기억(History)'을 모두 불러옵니다.
    seen_titles = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            seen_titles = [line.strip() for line in f.readlines() if line.strip()]

    # ★ 3. 최초 실행 방어막 (처음 실행할 때 15개 글이 한꺼번에 날아오는 것을 방지)
    if not seen_titles:
        print("🚨 [초기 셋팅 완료] 현재 게시판의 모든 글을 머릿속에 기억했습니다! 다음부터 새 글만 알림을 보냅니다.")
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            for p in current_posts:
                f.write(p['title'] + "\n")
        return

    # ★ 4. 현재 게시판 글들을 스캔하며, '기억에 없는 진짜 새 글'만 골라냅니다.
    new_notices = []
    for p in current_posts:
        if p['title'] not in seen_titles:
            new_notices.append(p)

    if not new_notices:
        print("💤 새로운 공지사항이 없습니다. (모두 이미 본 글입니다)")
        return

    # ★ 5. 새 글이 발견되면 (여러 개여도 모두) 순서대로 AI 요약해서 문자를 쏩니다!
    print(f"🚨 {len(new_notices)}개의 진짜 새로운 공지사항 발견! 알림 전송 시작...")
    
    # 여러 개일 경우 예전 글부터 순서대로 보내기 위해 뒤집기
    for notice in reversed(new_notices):
        raw_content = get_notice_content(notice['link'], headers)
        ai_summary = summarize_with_ai(raw_content)
        
        message = (
            f"🔔 [경북대 AIC 새 공지사항]\n\n"
            f"📌 제목: {notice['title']}\n\n"
            f"🤖 AI 요약:\n{ai_summary}\n\n"
            f"🔗 원문 바로가기:\n{notice['link']}"
        )
        send_telegram_message(message)
        
        # 알림을 보낸 새 글은 바로 '기억'에 추가!
        seen_titles.append(notice['title'])

    # ★ 6. 메모장이 너무 커지지 않게 최근 50개의 제목만 압축해서 저장해 둡니다.
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for title in seen_titles[-50:]:
            f.write(title + "\n")
            
    print("✅ 새 글 알림 전송 및 기억장치 업데이트 완벽 성공!")

if __name__ == "__main__":
    check_new_notice()
