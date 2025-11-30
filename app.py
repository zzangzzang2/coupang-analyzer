from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import base64

app = Flask(__name__)

def init_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def analyze_coupang(image_list=None, html_content=None):
    model = init_gemini()
    
    if image_list and html_content:
        prompt = """이 이미지들과 HTML은 같은 쿠팡 상품 페이지입니다.

중요: 
- HTML에서 정확한 상품명과 가격을 찾으세요
- 이미지에서 상세 특징, 스펙, 장점을 찾으세요
- 첫 번째 이미지 상단에 있는 메인 상품만 분석하세요
- "상품정보 접기" 버튼이 보이면 그 위쪽 내용만 분석하세요
- 하단의 "추천 상품", "함께 본 상품" 등은 무시하세요

요청:
1. 상품명을 정확히 찾아주세요
2. 가격을 찾아주세요 (원 단위)
3. 상품의 주요 특징을 7~15개로 정리해주세요
4. 이미지에서 보이는 모든 텍스트를 추출해주세요
5. HTML에서 상품 관련 텍스트를 추출해주세요

특징 작성 형식 (반드시 이 형식으로):
- 키워드 - 상세 설명
예시:
- 대용량 배터리 - 5000mAh 배터리로 하루 종일 사용 가능
- 빠른 충전 - 30분 만에 50% 충전되는 고속충전 지원

출력 형식:
[상품명] (찾은 상품명)
[가격] (찾은 가격)

[특징]
- 키워드 - 상세 설명
- 키워드 - 상세 설명
...

[이미지 텍스트]
(상품 이미지에서 읽은 모든 텍스트 - 광고문구, 스펙, 설명 등)

[HTML 텍스트]
(HTML에서 추출한 상품 관련 주요 텍스트)

HTML:
""" + html_content[:30000]
        
        content = [prompt]
        for img_data in image_list:
            content.append({'mime_type': 'image/png', 'data': img_data})
    
    elif image_list:
        prompt = """이 이미지들은 쿠팡 상품 페이지를 위에서 아래로 순서대로 캡처한 것입니다.

중요: 
- 첫 번째 이미지 상단에 있는 메인 상품만 분석하세요
- 첫 번째 이미지에서 상품명과 가격을 찾으세요
- "상품정보 접기" 버튼이 보이면 그 위쪽 내용만 분석하세요
- 하단의 "추천 상품", "함께 본 상품" 등은 무시하세요
- 리뷰, 상품평 섹션도 무시하세요

요청:
1. 첫 번째 이미지 상단에서 메인 상품명을 정확히 찾아주세요
2. 가격을 찾아주세요 (원 단위)
3. 상품의 주요 특징을 7~15개로 정리해주세요
4. 이미지에서 보이는 모든 텍스트를 추출해주세요

특징 작성 형식 (반드시 이 형식으로):
- 키워드 - 상세 설명
예시:
- 대용량 배터리 - 5000mAh 배터리로 하루 종일 사용 가능
- 빠른 충전 - 30분 만에 50% 충전되는 고속충전 지원

출력 형식:
[상품명] (이미지에서 찾은 정확한 상품명)
[가격] (이미지에서 찾은 가격)

[특징]
- 키워드 - 상세 설명
- 키워드 - 상세 설명
...

[이미지 텍스트]
(상품 이미지에서 읽은 모든 텍스트 - 광고문구, 스펙, 설명 등)
"""
        content = [prompt]
        for img_data in image_list:
            content.append({'mime_type': 'image/png', 'data': img_data})
    
    else:
        prompt = """다음은 쿠팡 상품 페이지의 HTML 소스입니다.

이 HTML에서 상품 정보를 찾아서 블로그 작성용 특징을 정리해주세요.

요청:
1. 상품명을 정확히 찾아주세요
2. 가격을 찾아주세요 (원 단위)
3. 상품의 주요 특징을 7~15개로 정리해주세요

특징 작성 형식 (반드시 이 형식으로):
- 키워드 - 상세 설명
예시:
- 대용량 배터리 - 5000mAh 배터리로 하루 종일 사용 가능
- 빠른 충전 - 30분 만에 50% 충전되는 고속충전 지원

출력 형식:
[상품명] (찾은 상품명)
[가격] (찾은 가격)

[특징]
- 키워드 - 상세 설명
- 키워드 - 상세 설명
...

HTML:
""" + html_content[:50000]
        content = [prompt]
    
    try:
        response = model.generate_content(content)
        return {'success': True, 'result': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def analyze_naver_place(image_list):
    model = init_gemini()
    
    prompt = """이 이미지들은 네이버 플레이스(가게/업체) 페이지를 캡처한 것입니다.

중요: 
- 첫 번째 이미지 상단에 있는 메인 업체만 분석하세요
- 하단의 "주변 추천", "다른 업체" 등은 무시하세요

요청:
1. 업체명을 정확히 찾아주세요
2. 주소, 전화번호, 영업시간을 찾아주세요
3. 업체의 주요 특징을 7~15개로 정리해주세요
4. 메뉴/서비스 정보가 있으면 포함해주세요
5. 이미지에서 보이는 모든 텍스트를 추출해주세요

특징 작성 형식 (반드시 이 형식으로):
- 키워드 - 상세 설명
예시:
- 파일럿 전문성 - 항공촬영 자격증 보유, 수백회 이상 현장 경험
- 촬영 장비 - 최신 드론 장비 사용, 4K 고화질 촬영
- 가격 경쟁력 - 합리적인 가격, 패키지 할인 제공

출력 형식:
[업체명] (찾은 업체명)
[주소] (찾은 주소)
[전화번호] (찾은 전화번호)
[영업시간] (찾은 영업시간)

[특징]
- 키워드 - 상세 설명
- 키워드 - 상세 설명
...

[메뉴/서비스]
(메뉴나 서비스 정보가 있으면 정리)

[이미지 텍스트]
(이미지에서 읽은 모든 텍스트)
"""
    
    content = [prompt]
    for img_data in image_list:
        content.append({'mime_type': 'image/png', 'data': img_data})
    
    try:
        response = model.generate_content(content)
        return {'success': True, 'result': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    image_list = []
    html_content = None
    analyze_type = request.form.get('type', 'coupang')
    
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file.filename:
                image_list.append(base64.b64encode(file.read()).decode('utf-8'))
    
    html_content = request.form.get('html', '').strip()
    
    if not image_list and not html_content:
        return jsonify({'success': False, 'error': '이미지 또는 HTML을 입력해주세요.'})
    
    if html_content and len(html_content) < 500:
        html_content = None
    
    if analyze_type == 'naver':
        if not image_list:
            return jsonify({'success': False, 'error': '네이버 플레이스는 이미지를 업로드해주세요.'})
        analysis = analyze_naver_place(image_list)
    else:
        analysis = analyze_coupang(image_list if image_list else None, html_content if html_content else None)
    
    if not analysis['success']:
        return jsonify({'success': False, 'error': f'AI 분석 실패: {analysis["error"]}'})
    
    return jsonify({'success': True, 'result': analysis['result']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
