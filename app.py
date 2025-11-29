from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import base64

app = Flask(__name__)

def init_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def analyze_with_gemini_images(image_list):
    model = init_gemini()
    prompt = """이 이미지들은 쿠팡 상품 페이지 캡처입니다.

이미지에서 상품 정보를 찾아서 블로그 작성용 특징을 정리해주세요.

요청:
1. 먼저 상품명과 가격을 찾아주세요
2. 상품의 주요 특징을 7~15개로 정리해주세요
3. 이미지에 보이는 스펙, 기능, 장점 위주로 작성해주세요
4. 각 특징은 - 로 시작하는 한 줄로 작성해주세요

출력 형식:
[상품명] (찾은 상품명)
[가격] (찾은 가격)

- 특징1
- 특징2
..."""
    
    try:
        content = [prompt]
        for img_data in image_list:
            content.append({
                'mime_type': 'image/png',
                'data': img_data
            })
        response = model.generate_content(content)
        return {'success': True, 'result': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def analyze_with_gemini_html(html_content):
    model = init_gemini()
    prompt = f"""다음은 쿠팡 상품 페이지의 HTML 소스입니다.

이 HTML에서 상품 정보를 찾아서 블로그 작성용 특징을 정리해주세요.

요청:
1. 먼저 상품명과 가격을 찾아주세요
2. 상품의 주요 특징을 7~15개로 정리해주세요
3. 각 특징은 - 로 시작하는 한 줄로 작성해주세요

출력 형식:
[상품명] (찾은 상품명)
[가격] (찾은 가격)

- 특징1
- 특징2
...

HTML:
{html_content[:50000]}
"""
    try:
        response = model.generate_content(prompt)
        return {'success': True, 'result': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 이미지 업로드 방식
    if 'images' in request.files or 'image' in request.files:
        files = request.files.getlist('images') or [request.files['image']]
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': '파일을 선택해주세요.'})
        image_list = []
        for file in files:
            if file.filename:
                image_list.append(base64.b64encode(file.read()).decode('utf-8'))
        analysis = analyze_with_gemini_images(image_list)
    # HTML 붙여넣기 방식
    elif request.is_json:
        data = request.json
        html_content = data.get('html', '').strip()
        if not html_content:
            return jsonify({'success': False, 'error': 'HTML을 붙여넣어주세요.'})
        if len(html_content) < 1000:
            return jsonify({'success': False, 'error': '내용이 너무 짧습니다.'})
        analysis = analyze_with_gemini_html(html_content)
    else:
        return jsonify({'success': False, 'error': '이미지 또는 HTML을 입력해주세요.'})
    
    if not analysis['success']:
        return jsonify({'success': False, 'error': f'AI 분석 실패: {analysis["error"]}'})
    
    return jsonify({'success': True, 'result': analysis['result']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
