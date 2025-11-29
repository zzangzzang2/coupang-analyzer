from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import base64

app = Flask(__name__)

def init_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def analyze_combined(image_list=None, html_content=None):
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

출력 형식:
[상품명] (찾은 상품명)
[가격] (찾은 가격)

[특징]
- 특징1
- 특징2
...

[이미지 텍스트]
(상품 이미지에서 읽은 모든 텍스트 - 광고문구, 스펙, 설명 등)

[HTML 텍스트]
(HTML에서 추출한 상품 관련 주요 텍스트)

HTML:
""" + html_content[:30000]

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

출력 형식:
[상품명] (이미지에서 찾은 정확한 상품명)
[가격] (이미지에서 찾은 가격)

[특징]
- 특징1
- 특징2
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
4. 각 특징은 - 로 시작하는 한 줄로 작성해주세요

출력 형식:
[상품명] (찾은 상품명)
[가격] (찾은 가격)

- 특징1
- 특징2
...

HTML:
""" + html_content[:50000]
        content = [prompt]
    
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
    
    # 이미지 처리
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file.filename:
                image_list.append(base64.b64encode(file.read()).decode('utf-8'))
    
    # HTML 처리
    html_content = request.form.get('html', '').strip()
    
    if not image_list and not html_content:
        return jsonify({'success': False, 'error': '이미지 또는 HTML을 입력해주세요.'})
    
    if html_content and len(html_content) < 500:
        html_content = None
    
    analysis = analyze_combined(image_list if image_list else None, html_content if html_content else None)
    
    if not analysis['success']:
        return jsonify({'success': False, 'error': f'AI 분석 실패: {analysis["error"]}'})
    
    return jsonify({'success': True, 'result': analysis['result']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
