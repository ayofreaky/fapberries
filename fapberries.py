import requests, os
from rich import print
from nsfw_detector import predict
from pathlib import Path

model = predict.load_model('.\mobilenet_v2_140_224\saved_model.h5') # https://github.com/GantMan/nsfw_model/releases/download/1.2.0/mobilenet_v2_140_224.1.zip
headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
            'authority': 'public-feedbacks.wildberries.ru'}
pornMin = 0.80
sexyMin = 0.80

with open('items.txt', 'r') as f:
    itemIds = f.read().split('\n')
    print(f'[~] Товаров:', len(itemIds))

for itemId in itemIds:
    print(f'Парсим imtId по nmId {itemId}')
    r = requests.get(f'https://wbx-content-v2.wbstatic.net/ru/{itemId}.json').json()
    itemId = r['imt_id']
    print(f'Получили itemId: {itemId}')

    payload = {'imtId': itemId, 'skip': 0, 'take': 20}
    r = requests.post('https://public-feedbacks.wildberries.ru/api/v1/summary/full', headers=headers, json=payload).json()

    print(f"Количество отзывов с фотографиями: {r['feedbackCountWithPhoto']}")
    for offset in range(0, r['feedbackCountWithPhoto'], 20):
        payload = { 'imtId': itemId,
                    'skip': offset,
                    'take': 20,
                    'order': 'dateDesc',
                    'hasPhoto': True}

        r = requests.post('https://public-feedbacks.wildberries.ru/api/v1/feedbacks/site', headers=headers, json=payload).json()
        if len(r['feedbacks']) > 0:
            for feedback in r['feedbacks']:
                Path(f'Downloads\\{itemId}').mkdir(parents=True, exist_ok=True)
                userId = feedback['wbUserId']
                username = feedback['wbUserDetails']['name']
                print(f"\n{'-'*99}\n{username}:\n{feedback['text']}\n{'-'*99}")
                for photo in feedback['photos']:
                    photoUrl = f"https://feedbackphotos.wbstatic.net/{photo['fullSizeUri']}"
                    filename = photoUrl
                    with open(f"Downloads\{itemId}\{itemId}_{username}_{userId}_{photo['fullSizeUri'].split('/')[-1]}", 'wb') as f:
                        f.write(requests.get(photoUrl).content)
                    print(f"{photoUrl}")
        else:
            break
        if len(os.listdir(f'Downloads\\{itemId}')) > 0:
            print(f'[green]Скачали {len(os.listdir(f"Downloads/{itemId}"))} пикч[/green]')
            pred = predict.classify(model, f'Downloads\\{itemId}')
            for result in pred:
                porn, sexy = round(pred[result]['porn'], 2), round(pred[result]['sexy'], 2)
                if porn >= pornMin <= 1.00 or sexy >= sexyMin <= 1.00:
                    print(f'\n[green]{os.path.basename(result)}:\nОставляем пикчу.. | porn: {porn}, sexy: {sexy}[/green]')
                else:
                    print(f'\n[red]{os.path.basename(result)}:\nУдаляем пикчу.. | porn: {porn}, sexy: {sexy}[/red]')
                    os.remove(result)
        else:
            Path.rmdir(f'Downloads\\{itemId}', ignore_errors=True)
            # os.rmdir(f'Downloads\\{itemId}')
