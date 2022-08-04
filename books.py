import os
import requests
import json
from random import randint, random
import time
from bs4 import BeautifulSoup
import datetime
import logging

# Рейтинг книги в коде страницы задан текстом, поэтому создаем словарь для приведения его к числу
RAITINGS = {
    'One': 1,
    'Two': 2,
    'Three': 3,
    'Four': 4,
    'Five': 5,
}

# Имена файлов для обложек формируем по имени книги. Поэтому сделаем словарь символов, недопустимых в именах файлов
INVALID_SYMBOLS = ['"', '*', ':', '/', '\\', '?', '<', '>', '|']


def main():

    headers = {
        'accept': 'text/html,application/xhtml+xml,'
                  'application/xml;q=0.9,image/avif,image/webp,'
                  'image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                      ' AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/103.0.0.0 Safari/537.36',

    }

    # Проверяем наличие каталога для хранения картинок с обложками и, при необходимости, создаем
    if not os.path.exists('books_data'):
        os.mkdir('books_data')

    if not os.path.exists('books_data/book_images'):
        os.mkdir('books_data/book_images')

    # Создаем пустой .json файл, в который будем складывать данные о книгах. К имени файла добавим дату запуска парсера
    books_data = []
    filename = f'books_data/books_data_{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.json'
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(books_data, file)

    logfile = f'{filename.split(".")[0]}.log'
    logging.basicConfig(filename=logfile, level=logging.INFO, encoding='utf-8')

    # Запускаем цикл перебора страниц. При просмотре главной определено, что их всего 50.
    # При желании можно бы было предварительно распарсить данные главной
    # и извлечь из пагинатора фактическое количество страницу
    logging.info(f'{datetime.datetime.now().strftime("%H:%M:%S")}: Парсинг начать')
    for page_number in range(1, 51):

        # При каждом проходе цикла открываем файл с уже сохраненными данными,
        # т.к. будем из записывать постранично, чтобы не потерять то, что уже собрано
        # А способа "дописывать" в .json файл я не нашел
        with open(filename, 'r', encoding='utf-8') as file:
            books_data = json.load(file)

        # Выводим данные о том, какая страница сейчас парсится
        print(f'Loading data from page {page_number} out of 50')
        # и рисуем Progress bar
        print(f'[{"|" * page_number}{"." * (50 - page_number)}]')

        # получаем данные с текущей страницы
        logging.info(f'{datetime.datetime.now().strftime("%H:%M:%S")}: Получаю данные со страницы {page_number}')
        url = f'https://books.toscrape.com/catalogue/page-{page_number}.html'
        res = requests.get(url, headers=headers,)

        # Если данные получены успешно, начинаем парсить
        if res.status_code == 200:
            logging.info(f'{datetime.datetime.now().strftime("%H:%M:%S")}: данные со страницы {page_number} '
                         f'успешно получены')

            try:
                # Данные о каждой книге содержатся в элементе с одинаковым классом,
                # так что получаем список с ними
                soup = BeautifulSoup(res.text, 'lxml')
                cards = soup.find_all('article')
            except:
                logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                              f'На странице {page_number} не найдены данные о книгах')
                continue

            # Проходимся по элементам списка и получаем данные по каждой книге
            for book_number, card in enumerate(cards):

                # Получаем имя книги, которое содержится в единственном в карточке элементе h3
                # по атрибуту title т.к. текст в заголовке сокращается при длинном названии
                try:
                    name = card.find('h3').find('a').get('title')
                except:
                    name = f'{page_number} - {book_number}'
                    logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                                  f'Не удалось получить название книги. Присвоено имя {name}')
                # Выводим в консоль, с какой книгой сейчас работаем
                print(f'Загружаю данные о книге {name}')
                logging.info(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                             f'Загружаем данные о книге {name}')

                # Получаем адрес ссылки на изображение книги, формируем полный адрес к картинке,
                # загружаем и сохраняем картинку. При этом, при формировании имени фала берем название книги,
                # Но ограничиваем его длину и заменяем символы, недопустимые в именах файлов.
                try:
                    img_link = f'https://books.toscrape.com/{card.find("img").get("src")}'
                except:
                    logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                                  f'Не удалось получить ссылку на файл изображения книги {name}')
                else:
                    image = requests.get(img_link, headers=headers)
                    if image.status_code == 200:
                        image_filename = name[:128]
                        for symbol in INVALID_SYMBOLS:
                            image_filename = image_filename.replace(symbol, '_')
                        try:
                            with open(f'books_data/book_images/{image_filename}.jpg', 'wb') as file:
                                file.write(image.content)
                        except:
                            logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                                          f'Возникла ошибка при сохранении файла изображения книги {name}')
                    else:
                        logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                                      f'Не удалось загрузить файл изображения книги {name}')
                    time.sleep(random())

                # получаем остальные данные книги, формируем из них словарь и складываем в список всех книг
                try:
                    rating = RAITINGS[card.find('p', class_='star-rating').get('class')[-1]]
                except:
                    logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                                  f'Не удалось получить рейтинг книги {name}')
                    rating = None

                try:
                    in_stock = True if card.find(class_='instock').find('i').get('class')[0] == 'icon-ok' else False
                except:
                    logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                                  f'Не удалось получить наличие книги {name}')
                    in_stock = None

                try:
                    price = float(card.find('p', class_='price_color').text.split('£')[-1])
                except:
                    logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                                  f'Не удалось получить цену книги {name}')
                    price = None

                book_data = {
                    'name': name,
                    'rating': rating,
                    'in_stock': in_stock,
                    'price': price,
                }
                logging.info(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                             f'Данные по книге {name} собраны')

                books_data.append(book_data)

            # После завершения прохода по странице, сохраняем данные в итоговый файл
            logging.info(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                         f'Данные со страницы {page_number} собраны')
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    json.dump(books_data, file, indent=4, ensure_ascii=False)
            except:
                logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                              f'Произошла ошибка при записи файл данных со страницы {page_number}')

        # если страницу не удалось загрузить, формируем сообщение о том, на какой странице возникли проблемы
        else:
            print(f'Произошла ошибка {res.status_code} при попытке загрузки страницы {page_number}')
            logging.error(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                          f'Ошибка {res.status_code} при попытке загрузки страницы {page_number}')

        # Даем серверу немножко "отдохнуть" от нашего настойчивого внимания
        time.sleep(randint(1, 4))

    logging.info(f'{datetime.datetime.now().strftime("%H-%M-%S")}: '
                 f'Все данные собраны')


if __name__ == '__main__':
    main()
