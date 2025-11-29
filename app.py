from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import base64

app = Flask(__name__)

def init_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def scrape_coupang(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_name = ""
        name_tag = soup.select_one('h1.prod-buy-header__title') or soup.select_one('.prod-buy-header__title')
        if name_tag:
            product_name = name_tag.get_text(strip=True)
        price = ""
        price_tag = soup.select_one('.total-price strong') or soup.select_one('span.total-price')
        if price_tag:
            price = price_tag.get_text(strip=True)
        description_texts = []
        for elem in soup.select('.prod-description, .prod-buy-header__sub-title, .prod-option-item, .prod-attr-item'):
            text = elem.get_text(strip=True)
            if text and len(text) > 5:
                description_texts.append(text)
        images = []
        for img in soup.select('.prod-image__item img, .prod-image img')[:5]:
            src = img.get('src') or img.get('data-src')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                images.append(src)
        return {'success': True, 'product_name': product_name, 'price': price, 'descriptions': list(set(description_texts))[:20], 'images': images}
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
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'URL을 입력해주세요.'})
    if 'coupang.com' not in url:
        return jsonify({'success': False, 'error': '쿠팡 URL만 지원합니다.'})
    product_data = scrape_coupang(url)
    if not product_data['success']:
        return jsonify({'success': False, 'error': f'크롤링 실패: {product_data["error"]}'})
    if not product_data['product_name']:
        return jsonify({'success': False, 'error': '상품 정보를 찾을 수 없습니다.'})
    analysis = analyze_with_gemini(product_data)
    if not analysis['success']:
        return jsonify({'success': False, 'error': f'AI 분석 실패: {analysis["error"]}'})
    return jsonify({'success': True, 'product_name': product_data['product_name'], 'price': product_data['price'], 'image_count': len(product_data.get('images', [])), 'result': analysis['result']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
