# Как выложить демо «Эхо» на Streamlit Cloud

Занимает около 10 минут. Нужны аккаунты GitHub и OpenRouter.

## 1. Отдельный ключ OpenRouter с лимитом

1. Откройте https://openrouter.ai/settings/keys и нажмите Create Key.
2. Название: `echo-demo`. В поле Credit limit поставьте 2 ($2 хватит примерно на 600 разборов).
3. Скопируйте ключ. Он показывается один раз.

Отдельный ключ нужен, потому что демо открыто всем, у кого есть ссылка. Если ключ утечёт или кто-то устроит поток
запросов, потеря ограничена этими $2. Основной ключ останется нетронутым.

## 2. Репозиторий на GitHub

Локальный репозиторий уже собран: код, база знаний и готовый индекс в `index/`. Секретов в нём нет.

```powershell
cd C:\Users\Mi\Other\echo-assistant
gh repo create echo-assistant --public --source . --push
```

Без `gh`: создайте пустой публичный репозиторий `echo-assistant` на github.com и выполните две команды,
которые GitHub покажет в блоке «push an existing repository».

## 3. Приложение на Streamlit Cloud

1. Откройте https://share.streamlit.io, нажмите Create app → Deploy a public app from GitHub.
2. Repository: `<ваш логин>/echo-assistant`, Branch: `main`, Main file path: `app.py`.
3. App URL: например `echo-lavka`. Адрес будет `https://echo-lavka.streamlit.app`.
4. Advanced settings → Python 3.12. В Secrets вставьте:

```toml
OPENROUTER_API_KEY = "ключ из шага 1"
REPO_URL = "https://github.com/<ваш логин>/echo-assistant/blob/main"
```

5. Нажмите Deploy. Первая сборка идёт 2–4 минуты.

## 4. Проверка

1. Нажмите пример «брак» и кнопку «Разобрать». Ответ должен прийти за 3–10 секунд.
2. В блоке «Источники» нажмите ссылку на документ: откроется страница «База знаний» с выделенным разделом.
3. Нажмите пример «вне базы: доставка в Казахстан»: в черновике должна стоять метка [уточнить у отдела].

Если вместо ответа видно «Нет ключа OPENROUTER_API_KEY», проверьте Secrets (App settings → Secrets) и перезапустите
приложение (Reboot app).

## Обновление базы знаний

После правки файлов в `kb/` пересоберите индекс локально и отправьте изменения:

```powershell
uv run python ingest.py
git add kb index
git commit -m "Update knowledge base"
git push
```

Streamlit Cloud подхватит изменения сам.
