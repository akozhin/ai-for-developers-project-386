# Документация

## Концепт
- [idea.md](concept/idea.md) — суть продукта
- [vision.md](concept/vision.md) — техническое видение
- [architecture.md](concept/architecture.md) — компоненты и потоки
- [data-model.md](concept/data-model.md) — схема данных
- [api-contracts.md](concept/api-contracts.md) — обзор REST-контракта (источник правды — TypeSpec в `api/`)
- `integrations.md` — **пропущен**: внешних сервисов и интеграций (календари, почта) в проекте нет по замыслу

## Решения
- [001-tech-stack.md](decisions/001-tech-stack.md) — стек и организация репозитория
- [002-api-contract-typespec.md](decisions/002-api-contract-typespec.md) — контракт в TypeSpec (Design First)
- [003-ai-agent-langchain.md](decisions/003-ai-agent-langchain.md) — AI-подбор слотов на LangChain-агенте
- [004-docker-render-deploy.md](decisions/004-docker-render-deploy.md) — один Docker-образ, один процесс на `PORT`, деплой на Render

## Макеты
- [mockups/](mockups/) — экран записи, режим AI, аватар владельца по умолчанию

## План
- [roadmap.md](roadmap.md)
- [sprint-01-scaffold-ci](sprints/sprint-01-scaffold-ci/README.md)
- [sprint-02-landing](sprints/sprint-02-landing/README.md) — историческая запись; лендинг заменён экраном записи
