from pprint import pprint
import requests
import urllib.parse as urp
import datetime
from tqdm import tqdm
import os
from dotenv import load_dotenv


class VK:
    def __init__(self, access_token, version='5.131'):
        self.params = {'access_token': access_token, 'v': version}

    def get_photos(self, user_id=None):
        url_photos = 'https://api.vk.com/method/photos.get'
        params_vk = {'owner_id': user_id,
                     'album_id': 'profile',
                     'extended': 1,
                     'photo_sizes': 1}
        query = requests.get(url_photos, params={**self.params, **params_vk}).json()
        return query


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {'Content-Type': 'application/json',
                'Authorization': f'OAuth {self.token}'}

    def create_folder(self, folder_name):
        url_upload = 'https://cloud-api.yandex.net:443/v1/disk/resources'
        params = {'path': folder_name}
        return requests.put(url_upload, params=params, headers=self.get_headers())

    def upload_file(self, file_path_on_yandex: str, file_name: str):
        """Метод загружает файл на яндекс диск"""
        url_upload = 'https://cloud-api.yandex.net:443/v1/disk/resources/upload'
        params = {'path': file_path_on_yandex, 'overwrite': 'true'}
        response = requests.get(url_upload, params=params, headers=self.get_headers())
        pprint(response)
        href = response.json()['href']
        return requests.put(url=href, data=file_name)

    def upload_by_url(self, file_path_on_yandex: str, url_resource: str):
        """Метод загружает файл на яндекс диск"""
        url_upload = 'https://cloud-api.yandex.net:443/v1/disk/resources/upload'
        params = {'url': url_resource,
                  'path': file_path_on_yandex,
                  'disable_redirects': 'false'}
        return requests.post(url_upload, params=params, headers=self.get_headers())


class PhotoBackuper:
    def __init__(self, vk_access_token, vk_api_version='5.131'):
        self.vk = VK(vk_access_token, vk_api_version)

    def backup(self, *, vk_user_id=None, yandex_token, count=5):

        ya = YaUploader(yandex_token)
        photos_info = []
        for photo in self.vk.get_photos(vk_user_id)['response']['items']:
            photos_info.append({'likes': photo['likes']['count'],
                                'url': photo['sizes'][-1]['url'],
                                'ext': photo['sizes'][-1]['url'].partition('?')[0].split('.')[-1],
                                'size': photo['sizes'][-1]['type']})
        result = []
        folder_name = str(datetime.datetime.now()).replace(':', '-')
        ya.create_folder(urp.quote(f'/{folder_name}'))
        files_uploaded_count = 0
        #with progressbar.ProgressBar(max_value=count) as bar:
        with tqdm(total=count) as bar:
            for photo in photos_info:
                file_name = f'''{photo['likes']}.{photo['ext']}'''
                addition = 0
                file_name_temp = file_name
                while file_name_temp in list(map(lambda x: x['file_name'], result)):
                    addition += 1
                    file_name_temp = f'{file_name}_{addition}'
                file_name = file_name_temp
                response = ya.upload_by_url(urp.quote(f'/{folder_name}/{file_name}'), photo['url'])
                if 200 < response.status_code < 300:
                    result.append({'file_name': file_name,
                                   'size': photo['size']})
                    files_uploaded_count += 1
                    bar.update(files_uploaded_count)
                if len(result) == count:
                    break
        return result


if __name__ == '__main__':
    load_dotenv()
    access_token_vk = os.getenv('ACCESS_TOKEN_VK')
    backuper = PhotoBackuper(access_token_vk)
    token_ya = os.getenv('TOKEN_YA')
    pprint(backuper.backup(vk_user_id='1', yandex_token=token_ya))
