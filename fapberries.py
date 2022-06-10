import requests, os, random, sys
from rich import print
from nsfw_detector import predict
from pathlib import Path

model = predict.load_model('.\mobilenet_v2_140_224\saved_model.h5') # https://github.com/GantMan/nsfw_model/releases/download/1.2.0/mobilenet_v2_140_224.1.zip
headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
            'authority': 'public-feedbacks.wildberries.ru'}
pornMin = 0.80
sexyMin = 0.80

page = 1
mainCategory = 'women_underwear1' # 'women_underwear2'
r = requests.get(f'https://catalog.wb.ru/catalog/{mainCategory}/catalog?kind=2&locale=ru&page={page}&sort=popular', headers=headers).json()
for product in r['data']['products']:
    with open('archive.txt', 'r') as archive:
        archive = archive.read().splitlines()

    product = requests.get(f'https://wbx-content-v2.wbstatic.net/ru/{product["id"]}.json', headers=headers).json()
    itemId = product['imt_id']
    if itemId not in archive:
        i = 0
        print(f'Товар: {product["imt_name"]} | imtId: {itemId}')
        payload = {'imtId': itemId, 'skip': 0, 'take': 20}
        product = requests.post('https://public-feedbacks.wildberries.ru/api/v1/summary/full', headers=headers, json=payload).json()
        feedbackCountWithPhoto = product['feedbackCountWithPhoto']

        print(f'Количество отзывов с фотографиями: {feedbackCountWithPhoto}')
        for offset in range(0, product['feedbackCountWithPhoto'], 20):
            payload = { 'imtId': itemId,
                        'skip': offset,
                        'take': 20,
                        'order': 'dateDesc',
                        'hasPhoto': True}

            product = requests.post('https://public-feedbacks.wildberries.ru/api/v1/feedbacks/site', headers=headers, json=payload).json()
            if len(product['feedbacks']) > 0:
                for feedback in product['feedbacks']:
                    Path(f'Downloads/{itemId}').mkdir(parents=True, exist_ok=True)
                    userId = feedback['wbUserId']
                    username = feedback['wbUserDetails']['name']
                    i += 1
                    print(f"\n{'-'*99}\n[{i}/{feedbackCountWithPhoto}] {username}:\n{feedback['text']}")
                    for photo in feedback['photos']:
                        photoUrl = f"https://feedbackphotos.wbstatic.net/{photo['fullSizeUri']}"
                        with open(f"Downloads/{itemId}/{itemId}_{username}_{userId}_{photo['fullSizeUri'].split('/')[-1]}", 'wb') as f:
                            f.write(requests.get(photoUrl).content)
                        print(f'{photoUrl}')
            else:
                with open('archive.txt', 'a') as archive:
                    archive.write(f'{itemId}\n')
                break

        if len(os.listdir(f'Downloads/{itemId}')) > 0:
            print(f'[green]Скачали {len(os.listdir(f"Downloads/{itemId}"))} пикч[/green]')
            pred = predict.classify(model, f'Downloads/{itemId}')
            for result in pred:
                porn, sexy = round(pred[result]['porn'], 2), round(pred[result]['sexy'], 2)
                if porn >= pornMin <= 1.00 or sexy >= sexyMin <= 1.00:
                    print(f'\n[green]{os.path.basename(result)}:\nОставляем пикчу.. | porn: {porn}, sexy: {sexy}[/green]')
                else:
                    print(f'\n[red]{os.path.basename(result)}:\nУдаляем пикчу.. | porn: {porn}, sexy: {sexy}[/red]')
                    os.remove(result)

        else:
            Path.rmdir(f'Downloads/{itemId}', ignore_errors=True)

        with open('archive.txt', 'a') as archive:
                archive.write(f'{itemId}\n')

    else:
        print(f'Товар уже в архиве')