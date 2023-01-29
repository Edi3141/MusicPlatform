import requests
from bs4 import BeautifulSoup
import csv


def get_html(url):
    response = requests.get(url)
    return response.text


def get_total_pages(html):
    soup = BeautifulSoup(html, 'lxml')
    pages_nav = soup.find('nav', class_="navigation pagination").find('div')
    last_page = pages_nav.find_all('a')[-3]
    total_pages = last_page.find_next('a').get('href').split('/')[-2]
    return int(total_pages)


def write_to_csv(data):
    with open('starmedia1.csv', 'a') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows((
            data['Название'],
            data['Ссылка'],
        ))


def prepare_csv(data):
    with open('starmedia1.csv', 'w') as file:
        writer = csv.writer(file)
        writer.writerow(('Название', 'Ссылку на фото'))


def get_page_data(html):
    soup = BeautifulSoup(html, 'lxml')
    track_list = soup.find_all('div', class_="audio-wrapper")
    for track in track_list:
        try:
            title = track.find('div', class_="muz-title").find('a').text
        except:
            title = 'Нет название!'
        try:
            link = track.find('div', class_="muz-title").find('a').get('href')
            # links = 'https://starmedia.kg/' + link
        except:
            link = 'Нет ссылки на музыку'

        data = {'Название': title, 'Ссылка': link}
        write_to_csv(data)


def main():
    sounds_url = 'https://starmedia.kg/category/hit-yrlar/'
    pages = 'page/'

    total_pages = get_total_pages(get_html(sounds_url))

    for page in range(1, total_pages + 1):
        url_with_page = sounds_url + pages + str(page)
        html = get_html(url_with_page)
        get_page_data(html)


main()
