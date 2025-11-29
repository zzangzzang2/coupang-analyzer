from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import google.generativeai as genai
import os

app = Flask(__name__)

def init_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def parse_html(html_content):
    try:
        import json
        import re
        soup = BeautifulSoup(html_content, 'html.parser')
        
        product_name = ""
        price = ""
        description_texts = []
        
        # JSON-LD에서 상품 정보 찾기
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if data.get('@type') == 'Product':
                    product_name = data.get('name', '')
                    if 'offers' in data:
                        price = str(data['offers'].get('price', '')) + '원'
                    if 'description' in data:
                        description_texts.append(data['description'])
            except:
                pass
        
        # 기존 방식도 시도
        if not product_name:
            name_tag = soup.select_one('h1.prod-buy-header__title') or soup.select_one('.prod-buy-header__title')
            if name_tag:
                product_name = name_tag.get_text(strip=True)
        
        if not price:
            price_tag = soup.select_one('.total-price strong') or soup.select_one('span.total-price')
            if price_tag:
                price = price_tag.get_text(strip=True)
        
        for elem in soup.select('.prod-description, .prod-buy-header__sub-title, .prod-option-item, .prod-attr-item'):
            text = elem.get_text(strip=True)
            if text and len(text) > 3:
                description_texts.append(text)
        
        return {'success': True, 'product_name': product_name, 'price': price, 'descriptions': list(set(description_texts))[:30]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def analyze_with_gemini(product_data):
    model = init_gemini()
    prompt = f"""다음 쿠팡 상품 정보를 분석해서 블로그용 특징을 한 줄씩 정리해줘.

상품명: {product_data['product_name']}
가격: {product_data['price']}
설명: {chr(10).join(product_data['descriptions'])}

요청: 7~15개 특징을 - 로 시작하는 리스트로 출력"""
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
    data = request.json
    html_content = data.get('html', '').strip()
    if not html_content:
        return jsonify({'success': False, 'error': 'HTML을 붙여넣어주세요.'})
    if len(html_content) < 1000:
        return jsonify({'success': False, 'error': '내용이 너무 짧습니다. 페이지 전체를 복사해주세요.'})
    product_data = parse_html(html_content)
    if not product_data['success']:
        return jsonify({'success': False, 'error': f'파싱 실패: {product_data["error"]}'})
    if not product_data['product_name']:
        return jsonify({'success': False, 'error': '상품 정보를 찾을 수 없습니다.'})
    analysis = analyze_with_gemini(product_data)
    if not analysis['success']:
        return jsonify({'success': False, 'error': f'AI 분석 실패: {analysis["error"]}'})
    return jsonify({'success': True, 'product_name': product_data['product_name'], 'price': product_data['price'], 'result': analysis['result']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
