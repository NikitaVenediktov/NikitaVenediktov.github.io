# NikitaVenediktov.github.io

Личный сайт Никиты Венедиктова: https://nikitavenediktov.github.io

Статичный сайт на Jekyll, собирается GitHub Pages из ветки `main`.

- `index.md` — «Обо мне»
- `portfolio.md` — «Портфолио»
- `blog.html` — список записей; записи кладутся в `_posts/ГГГГ-ММ-ДД-slug.md`
- `contacts.md` — «Контакты»
- `_layouts/`, `_includes/`, `assets/css/` — общий шаблон, навигация и стили
- `favicon.svg`, `favicon.ico`, `apple-touch-icon.png` — иконки сайта; `assets/og-image.png` — картинка для превью ссылок
- SEO-теги, `sitemap.xml` и RSS блога (`/blog/feed.xml`) генерируют плагины `jekyll-seo-tag`, `jekyll-sitemap`, `jekyll-feed`
- Счётчик посещений — GoatCounter (`_includes/analytics.html`), имя аккаунта задаётся ключом `goatcounter` в `_config.yml`, скрипт подключается только в production-сборке (на GitHub Pages); статистика: https://nikitavenediktov.goatcounter.com
