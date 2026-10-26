# NikitaVenediktov.github.io

Личный сайт Никиты Венедиктова: https://nikitavenediktov.github.io

Статичный сайт на Jekyll, собирается GitHub Pages из ветки `main`.

- `index.md` — «Обо мне»
- `portfolio.md` — «Портфолио»
- `blog.html` — список записей; записи кладутся в `_posts/ГГГГ-ММ-ДД-slug.md` с `layout: post`, `title` и `description` (краткое описание для списка, RSS и превью ссылок); для постов из LinkedIn и Telegram — ещё `source` (`LinkedIn` или `Telegram`) и `source_url` (ссылка на оригинал)
- `contacts.md` — «Контакты»
- `_layouts/`, `_includes/`, `assets/css/` — общий шаблон, навигация и стили
- `favicon.svg`, `favicon.ico`, `apple-touch-icon.png` — иконки сайта; `assets/og-image.png` — картинка для превью ссылок
- SEO-теги, `sitemap.xml` и RSS блога (`/blog/feed.xml`) генерируют плагины `jekyll-seo-tag`, `jekyll-sitemap`, `jekyll-feed`
