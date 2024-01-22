"""
3. Сценарий Foursquare (kinopoisk)
- Напишите сценарий на языке Python, который предложит пользователю ввести интересующую его категорию 
(например, кофейни, музеи, парки и т.д.).
- Используйте API Foursquare для поиска заведений в указанной категории.
- Получите название заведения, его адрес и рейтинг для каждого из них.
- Скрипт должен вывести название и адрес и рейтинг  каждого заведения в консоль.
"""

import requests
import urllib
import json
import os
from dotenv import dotenv_values

def get_headers():
    headers = {
        'accept': 'application/json', 
        }
    headers['X-API-KEY'] = dotenv_values('.\l1_s1\.env')['TOKEN']
    return headers


def request_movies(url:str, params: dict, headers:dict)-> requests.Response:
    resp = requests.get(url, params=params, headers=headers)
    return resp    


def request_movies_type(url:str, params: dict, headers:dict) -> dict:
    result = {}
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code == 200:
        result = json.loads(resp.text)
    return result


def user_choice_number(prompts_list: list) -> int:
    """"
    Реализует отображение меню из списка опций и цифр. Выбор пользователя - цифра.
    """
    result = -1 # возвращает индекс в массиве prompts_list -1 если пользователь прервал работу.
    prompt = '\n'.join([f'{i}. {item}' for i, item in enumerate(prompts_list, start=1)])
    prompt += f'\n{len(prompts_list) + 1}. Выход'
    print(prompt)
    while True:
        choice_str = input("Укажите число, обозначающее выбор : ")
        try:
            choice_num = int(choice_str)
        except:
            continue
        if not (1 <= choice_num <= len(prompts_list) + 1):
            continue
        elif choice_num != len(prompts_list) + 1:
            result = choice_num - 1
        break
    return result

def user_choice_str(prompt: str, check_input):
    while True:
        user_choice_str = input(f'{prompt} (q - выход) : ').strip()
        if user_choice_str == 'q':
            break
        if check_input(user_choice_str):
            return user_choice_str


def main():
    url = 'https://api.kinopoisk.dev'
    search_movies_uri = '/v1.4/movie'
    possible_values_uri = '/v1/movie/possible-values-by-field' 
    search_movies_param_basic = {'selectFields':['id', 'name', 'description', 'genres', 'rating', 'enName'],
                    #    'type': 'animated-series',
                       'status': 'completed',
                    #    'year': ['2022', '2021'],                 
                    #    'rating.imdb': '9-10',
                        }
    action = 0
    movies_type = []
    headers = get_headers()
    movies_type = request_movies_type(urllib.parse.urljoin(url, possible_values_uri),\
                                                         {'field': 'type'},\
                                                         headers)
    movies_type = [item["name"] for item in movies_type]
    while True:
        chioce_num = user_choice_number(movies_type)
        if chioce_num == -1:
            break
        movie_type = movies_type[chioce_num]
        chioce_str = user_choice_str('Укажите года фильмов через запятую', lambda x: True)
        if chioce_str == 'q':
            break
        else:
            years = []
            for el in chioce_str.split(','):
                try:
                    year = int(el.strip())
                except:
                    continue
                if year > 1900:
                    years.append(str(year))
        chioce_str_raiting = user_choice_str('Укажите диапазон рейтинга фильмов через дефис', lambda x: True)
        if chioce_str == 'q':
            break
        search_movies_param = search_movies_param_basic
        search_movies_param['type'] = movie_type
        search_movies_param['year'] = years
        search_movies_param['rating.imdb'] = chioce_str_raiting
        resp = request_movies(urllib.parse.urljoin(url, search_movies_uri),\
                                                         search_movies_param,\
                                                         headers)
        if resp.status_code == 200:
            movies = json.loads(resp.text)['docs']
            print(f'Найдено фильмов : {json.loads(resp.text)["total"]}')
            print(f'Первые 10:')
            for movie in json.loads(resp.text)['docs']:
                print(f"{movie['id']}, {movie['name']}, {movie.get('enName')}, {movie.get('genre')}, {movie.get('rating')}")                 
        else:
            print(f'Oшибка выполнения запроса. http код : {resp.status_code}')



if __name__ == '__main__':
    main()