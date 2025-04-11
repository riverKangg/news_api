from datetime import datetime
import time
from bs4 import BeautifulSoup

from urllib.parse import quote

import json
import re
from summary.summarizer import NewsSummarizer  # GPT 요약기 클래스

def parse_response(response):
    try:
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            print("No JSON found in the response.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

def process_content_with_prompt(content, prompt):
    try:
        summarizer = NewsSummarizer()
        sentdict_raw = summarizer.summarize_with_gpt(content, prompt)
        sentdict = parse_response(sentdict_raw)

        if sentdict is None:
            raise ValueError("Parsed dictionary is None.")

        sentiment_label = sentdict.get('sentiment')
        summary_sentence = sentdict.get('sentence')

        if not sentiment_label or not summary_sentence:
            raise ValueError("Sentiment or sentence is missing from the response.")

        return sentiment_label, summary_sentence

    except Exception as e:
        print(f"Error processing content: {e}")
        return None, None


import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys

def fetch_article_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(response.text, 'html.parser')

    if 'sports' in url:
        content = soup.find('div', class_='_article_content')
    else:
        content = soup.find('div', id='newsct_article')

    content_text = content.get_text(strip=True) if content else ''
    return content_text, soup

def extract_journalist_info(soup):
    jour = soup.find('div', class_='media_end_head_journalist')
    if jour:
        jour_link_tag = jour.find('a')
        jour_name_tag = jour.find('em', class_='media_end_head_journalist_name')
        jour_link = jour_link_tag.get('href') if jour_link_tag else None
        jour_name = jour_name_tag.get_text(strip=True) if jour_name_tag else None
    else:
        jour_link = jour_name = None

    return jour_link, jour_name

def process_link(link):
    content_text, soup = fetch_article_content(link)
    jour_link, jour_name = extract_journalist_info(soup)
    return content_text, jour_link, jour_name

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("test url")
        url = "https://n.news.naver.com/mnews/article/020/0003627641?sid=103"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    content, jour_link, jour_name = process_link(url)
    print("본문:", content)
    print("기자 링크:", jour_link)
    print("기자 이름:", jour_name)

def build_naver_news_url(query: str, date: str) -> str:
    encoded_query = quote(query)
    option_date = f"ds={str(int(date[:4]))}.{date[4:6]}.{date[-2:]}&de={date[:4]}.{date[4:6]}.{date[-2:]}"
    url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}&sm=tab_opt&sort=1&photo=0&field=0&pd=3&{option_date}"
    return url

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def web_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--remote-debugging-port=9222')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def collect_and_summarize_news(query, category):
    date = datetime.now().strftime('%Y%m%d')
    url = build_naver_news_url(query, date)
    driver = web_driver()
    results = []

    try:
        driver.get(url)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news_items = soup.select(".news_area")

        for item in news_items:
            title_elem = item.select_one(".news_tit")
            if not title_elem:
                continue

            title = title_elem.text.strip()
            link = title_elem["href"]
            press_elem = item.select_one(".info.press")
            press = press_elem.text.strip() if press_elem else "언론사 정보 없음"
            desc_elem = item.select_one(".dsc_txt_wrap")
            description = desc_elem.text.strip() if desc_elem else "요약 정보 없음"

            test = item.find("div", class_="info_group")
            if not test:
                continue

            time_elem = test.find('span', class_='info').text.strip()
            a_tags = test.find_all('a')
            if not a_tags or 'naver' not in a_tags[-1].get('href', ''):
                continue

            naver_link = a_tags[-1].get('href')

            try:
                content, jour_link, jour_name = process_link(naver_link)
            except Exception as e:
                print(f"링크 파싱 오류: {e}")
                continue

            prompt = """
너는 삼성생명 홍보팀 직원이야.
기사에 대한 긍부정을 판단하고,
회사에 보고할 수 있게 기사를 한 줄로 정리해줘.

1. Classify the sentiment as one of the following: Positive, Negative, or Neutral.
2. 회사에 보고할 수 있게 한 문장으로 작성해줘. 한글로 작성해. 
3. Return the result in a strict JSON format using the keys: 'sentiment' and 'sentence'.

Expected return format:
{
    "sentiment": "Positive" | "Negative" | "Neutral",
    "sentence": "One-sentence summary that reflects the sentiment."
}
""" 
            sentiment_label, summary_sentence = process_content_with_prompt(content, prompt)

            result_item = {
                "category": category,
                "keyword": query,
                "title": title,
                "press": press,
                "summary": summary_sentence,
                "sentiment": sentiment_label,
                "description": description,
                "url": link,
                "naver_link": naver_link,
                "time": time_elem,
                "jour_name": jour_name,
            }

            results.append(result_item)

    finally:
        driver.quit()

    return results

if __name__ == '__main__':
    query = '윤석열'
    category = 'test'
    print(collect_and_summarize_news(query, category))
