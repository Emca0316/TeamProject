from django.shortcuts import render
import requests
import sys
from subprocess import run, PIPE
from bs4 import BeautifulSoup
import urllib.request as req
import re

from krwordrank.word import KRWordRank
from krwordrank.hangle import normalize
import krwordrank

import datetime
from datetime import timedelta

from wordcloud import WordCloud

import matplotlib.pyplot as plt

def basic(request):

    return render(request, 'home.html')

def result(request):
    subject = request.POST.get("subject")
    st_year = request.POST.get("year")
    st_month = request.POST.get("month")
    st_day = request.POST.get("day")
    top5_final_keywords, top5_final_keywordss_headlines_and_links = key_words_extraction(subject, st_year, st_month, st_day)
    st_date = datetime.datetime(int(st_year), int(st_month), int(st_day))
    ed_date = st_date + timedelta(days=6)
    ed_year = ed_date.year
    ed_month = ed_date.month
    ed_day = ed_date.day
    if subject == "1":
        subject = "정치"
    elif subject == "2":
        subject = "경제"
    elif subject == "3":
        subject = "사회"
    elif subject == "4":
        subject = "생활/문화"
    elif subject == "5":
        subject = "세계"
    elif subject == "6":
        subject = "IT/과학"
    else:
        subject = "오류"


    return render(request, 'home.html', {'top5_final_keywords': top5_final_keywords, 'top5_final_keywordss_headlines_and_links': top5_final_keywordss_headlines_and_links, 'st_year': st_year, 'st_month': st_month, 'st_day': st_day, 'ed_year': ed_year, 'ed_month': ed_month, 'ed_day': ed_day, 'subject': subject})

def key_words_extraction(subject, year, month, day):
    base_url_1 = 'https://news.naver.com'
    base_url_2 = '/main/ranking/popularDay.nhn?rankingType=popular_day&sectionId='
    while True:
        news_type_num = subject
        if news_type_num == "1":
            news_type = "100"
            break
        elif news_type_num == "2":
            news_type = "101"
            break
        elif news_type_num == "3":
            news_type = "102"
            break
        elif news_type_num == "4":
            news_type = "103"
            break
        elif news_type_num == "5":
            news_type = "104"
            break
        elif news_type_num == "6":
            news_type = "105"
            break
        else:
            print("잘못된 입력입니다.")
            print("\n")
            continue
    base_url_3 = '&date='

    y = year
    m = month
    d = day
    y = int(y)
    m = int(m)
    d = int(d)

    news_dates_sets = []
    for i in range(0, 3):
        start_news_date = datetime.datetime(y - i, m, d)
        news_dates_set = []
        for j in range(0, 7):
            news_date = start_news_date + timedelta(days=j)
            news_date_y_i = news_date.year * 10000
            news_date_m_i = news_date.month * 100
            news_date_d_i = news_date.day
            news_date_s = str(news_date_y_i + news_date_m_i + news_date_d_i)
            news_dates_set.append(news_date_s)
        news_dates_sets.append(news_dates_set)

    hangul = re.compile('[^ ㄱ-ㅣ가-힣]+')

    paragraphs_sets = []
    paragraphs_link_sets = []
    headline_sets = []
    for news_dates in news_dates_sets:
        paragraphs = []
        headline_set = []
        paragraphs_link_set = []
        for news_date in news_dates:
            page_for_headlines = req.urlopen(base_url_1 + base_url_2 + news_type + base_url_3 + news_date)
            page_for_headlines_html_v = BeautifulSoup(page_for_headlines, 'html.parser')
            headlines_with_tag = page_for_headlines_html_v.find_all('div', class_="ranking_headline")
            paragraphs_link = []
            for each in headlines_with_tag:
                headline_string = each.get_text().replace("\n", "")
                headline_set.append(headline_string)
                headline_string = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', headline_string)
                headline_string = hangul.sub(' ', headline_string)
                headline_string = headline_string.split(' ')
                headline_string = [i for i in headline_string if len(i) > 0]
                headline_string = " ".join(headline_string)
                paragraphs.append(headline_string)
                paragraphs_link.append(each.find('a')['href'])
                paragraphs_link_set.append(each.find('a')['href'])
            for each in paragraphs_link:
                page_for_each_article = req.urlopen(base_url_1 + each)
                page_for_each_article_html_v = BeautifulSoup(page_for_each_article, 'html.parser')
                # 본문을 담고 있는 html 코드
                paragraph_html = page_for_each_article_html_v.find('div', class_="_article_body_contents")
                if paragraph_html == None:
                    continue
                # paragraph 가져오기
                paragraph_string = paragraph_html.get_text()
                # 엔터키 제거
                paragraph_string = paragraph_string.replace("\n", "")
                paragraph_string = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', paragraph_string)
                paragraph_string = hangul.sub(' ', paragraph_string)
                paragraph_string = paragraph_string.split(' ')
                paragraph_string = [i for i in paragraph_string if len(i) > 0]
                paragraph_string = " ".join(paragraph_string)
                paragraphs.append(paragraph_string)
        paragraphs_link_sets.append(paragraphs_link_set)
        headline_sets.append(headline_set)
        paragraphs_sets.append(paragraphs)

    wordrank_extractor = KRWordRank(min_count=5, max_length=10, verbose=False)
    beta = 0.85  # PageRank의 decaying factor beta
    max_iter = 20

    top_keywords = []

    for paragraphs_set in paragraphs_sets:
        wordrank_extractor = KRWordRank(min_count=5, max_length=10, verbose=False)
        keywords, rank, graph = wordrank_extractor.extract(paragraphs_set, beta, max_iter)
        top_keywords.append(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:200])

    keyword_counter = {}
    for keywords in top_keywords:
        words, ranks = zip(*keywords)
        for word in words:
            keyword_counter[word] = keyword_counter.get(word, 0) + 1

    common_keywords = {word for word, count in keyword_counter.items() if count == 3}

    wordrank_extractor = KRWordRank(min_count=5, max_length=10, verbose=True)
    keywordss, rank, graph = wordrank_extractor.extract(paragraphs_sets[0], beta, max_iter)
    passwords = {word: score for word, score in sorted(keywordss.items(), key=lambda x: -x[1])[:300] if
                 not (word in common_keywords)}
    '''
    # Set your font path
    font_path = 'NanumSquare_acB.ttf'

    krwordrank_cloud = WordCloud(font_path=font_path, width=800, height=800, background_color="white")
    krwordrank_cloud = krwordrank_cloud.generate_from_frequencies(passwords)

    fig = plt.figure(figsize=(10, 10))
    plt.imshow(krwordrank_cloud, interpolation="bilinear")
    plt.show()

    fig.savefig('crawling.png')
    '''
    base_keywords = []
    for word, r in sorted(keywordss.items(), key=lambda x: x[1], reverse=True)[:150]:
        base_keywords.append(word)

    final_keywords = []
    for each in base_keywords:
        if each in common_keywords:
            continue
        else:
            final_keywords.append(each)

    top5_final_keywords = []
    for i in range(0, 5):
        top5_final_keywords.append(final_keywords[i])

    top5_final_keywordss_headlines = []
    top5_final_keywordss_links = []
    list1 = []
    list2 = []
    i = 0
    for keyword in top5_final_keywords:
        for headline in headline_sets[0]:
            if keyword in headline:
                index = headline_sets[0].index(headline)
                list1.append(headline)
                list2.append(paragraphs_link_sets[0][index])
                #top5_final_keywordss_headlines[i].append(headline)
                #top5_final_keywordss_links[i].append(paragraphs_link_sets[0][index])
            else:
                continue
        top5_final_keywordss_headlines.append(list1)
        top5_final_keywordss_links.append(list2)
        list1 = []
        list2 = []
        i = i + 1

    top5_final_keywordss_headlines_and_links = []
    for i in range(0, 5):
        top5_final_keywordss_headlines_and_links.append(list(zip(top5_final_keywordss_headlines[i], top5_final_keywordss_links[i])))

    return top5_final_keywords, top5_final_keywordss_headlines_and_links