"""
Скрипт загрузки документации в RAG-базу знаний ассистента.

Загружает:
1. Документацию проекта (base-agent.md, Passport.md, README.md, status04082026.md)
2. Шпаргалки по Python 3.13, TypeScript, React 19, Node.js 22
3. Ключевые страницы документации FastAPI, ChromaDB, LangChain

Использование:
    python -m scripts.load_docs
    python -m scripts.load_docs --project-only   # только документация проекта
    python -m scripts.load_docs --cheatsheets    # только шпаргалки
    python -m scripts.load_docs --libraries      # только документация библиотек
"""

import os
import sys
import argparse
import textwrap

# Добавляем backend в путь для импорта app.*
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_ROOT)

from app.rag.engine import get_rag_engine

COLLECTION = "assistant_main"

# ============================================================
# 1. Документация проекта
# ============================================================

PROJECT_DOCS = [
    ("base-agent.md", "project_doc", "Спецификация базового агента: архитектура, инструменты, промпт-шаблон"),
    ("Passport.md", "project_doc", "Паспорт проекта: назначение, возможности, архитектура, стек технологий"),
    ("README.md", "project_doc", "README проекта"),
    ("status04082026.md", "project_doc", "Статус проекта AI-smolagents"),
]


def load_project_docs(rag) -> int:
    """Загружает документацию проекта в RAG."""
    project_root = os.path.dirname(_BACKEND_ROOT)
    total_chunks = 0

    for filename, source, description in PROJECT_DOCS:
        path = os.path.join(project_root, filename)
        if not os.path.exists(path):
            print(f"  [SKIP] {filename} — файл не найден")
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            print(f"  [SKIP] {filename} — пустой файл")
            continue

        doc_text = f"# {filename}\n\n{description}\n\n{content}"
        chunks = rag.add_document(doc_text, {"source": source, "filename": filename})
        total_chunks += chunks
        print(f"  [OK] {filename} — {chunks} чанков")

    return total_chunks


# ============================================================
# 2. Шпаргалки
# ============================================================

CHEATSHEETS = {
    "python_313": textwrap.dedent("""
        # PYTHON 3.13 — ШПАРГАЛКА (актуальные возможности)

        ## Новое в Python 3.13
        - Улучшенный интерактивный интерпретатор (цветной вывод, многострочное редактирование)
        - Экспериментальная свободная потоковая сборка мусора (free-threaded build, без GIL)
        - JIT-компилятор (экспериментальный, ускоряет некоторые нагрузки)
        - Улучшенная ошибка отладки: traceback с цветной подсветкой
        - Новый синтаксис: type parameter syntax (PEP 695), улучшенные generics

        ## Синтаксис generics (PEP 695, Python 3.12+)
        ```python
        def first[T](items: list[T]) -> T:
            return items[0]

        class Stack[T]:
            def __init__(self) -> None:
                self.items: list[T] = []
            def push(self, item: T) -> None:
                self.items.append(item)
            def pop(self) -> T:
                return self.items.pop()
        ```

        ## Type aliases (PEP 695)
        ```python
        type Vector = list[float]
        type Matrix = list[Vector]
        type Callback = Callable[[int], str]
        ```

        ## Pattern Matching (match/case, Python 3.10+)
        ```python
        def process(command: str) -> str:
            match command.split():
                case ["go", direction]:
                    return f"Идём на {direction}"
                case ["stop"]:
                    return "Стоп"
                case [action, *rest] if action == "help":
                    return f"Помощь: {rest}"
                case _:
                    return "Неизвестная команда"
        ```

        ## Структурное сопоставление с классами
        ```python
        from dataclasses import dataclass

        @dataclass
        class Point:
            x: int
            y: int

        def describe(p):
            match p:
                case Point(x=0, y=0):
                    return "Начало координат"
                case Point(x, y):
                    return f"Точка ({x}, {y})"
        ```

        ## f-строки (Python 3.12+)
        ```python
        # Вложенные кавычки и многострочные f-строки
        name = "мир"
        msg = f"Привет, {name.upper()!r}!"
        # Многострочная f-строка (в реальном коде используйте f\"\"\")
        text = f\"\"\"
        Имя: {name}
        Длина: {len(name)}
        \"\"\"
        ```

        ## asyncio (современный подход)
        ```python
        import asyncio

        async def fetch(url: str) -> str:
            # ... асинхронный запрос
            return f"Данные из {url}"

        async def main():
            results = await asyncio.gather(
                fetch("https://api1.example.com"),
                fetch("https://api2.example.com"),
            )
            print(results)

        asyncio.run(main())
        ```

        ## Типизация (typing)
        ```python
        from typing import TypedDict, NotRequired, Literal, assert_never

        class User(TypedDict):
            id: int
            name: str
            email: NotRequired[str]

        def get_user() -> User:
            return {"id": 1, "name": "Alice"}

        def handle_status(status: Literal["ok", "error"]) -> None:
            if status == "ok":
                print("Всё хорошо")
            elif status == "error":
                print("Ошибка")
            else:
                assert_never(status)  # type checker поймёт
        ```

        ## dataclasses
        ```python
        from dataclasses import dataclass, field

        @dataclass(slots=True)
        class Product:
            name: str
            price: float
            tags: list[str] = field(default_factory=list)

            @property
            def discounted(self) -> float:
                return self.price * 0.9
        ```

        ## Полезные встроенные функции
        - `zip(strict=True)` — проверка равной длины (Python 3.10+)
        - `itertools.batched(iterable, n)` — разбиение на батчи (Python 3.12+)
        - `tomllib` — чтение TOML (Python 3.11+)
        - `ExceptionGroup` / `except*` — групповые исключения (Python 3.11+)
        - `Path.walk()` — обход директорий (Python 3.12+)
        - `str.removeprefix()`, `str.removesuffix()` — удаление префикса/суффикса
        - `functools.cache` — мемоизация
        - `typing.Self` — возврат self из метода
    """),
    "typescript": textwrap.dedent("""
        # TYPESCRIPT — ШПАРГАЛКА (актуальные возможности)

        ## Базовые типы
        ```typescript
        let name: string = "Alice";
        let age: number = 30;
        let isActive: boolean = true;
        let ids: number[] = [1, 2, 3];
        let tuple: [string, number] = ["key", 42];
        let anything: unknown = "может быть чем угодно";
        let nothing: void = undefined;
        ```

        ## Union и Intersection типы
        ```typescript
        type Status = "pending" | "in_progress" | "completed";
        type ID = string | number;

        type HasName = { name: string };
        type HasAge = { age: number };
        type Person = HasName & HasAge;  // intersection
        ```

        ## Generics
        ```typescript
        function identity<T>(value: T): T {
            return value;
        }

        interface Repository<T> {
            get(id: string): Promise<T>;
            save(item: T): Promise<void>;
        }

        class UserRepository implements Repository<User> {
            async get(id: string): Promise<User> { /* ... */ }
            async save(item: User): Promise<void> { /* ... */ }
        }
        ```

        ## Utility Types
        ```typescript
        interface User {
            id: number;
            name: string;
            email: string;
            password: string;
        }

        type PublicUser = Omit<User, "password">;
        type PartialUser = Partial<User>;
        type ReadonlyUser = Readonly<User>;
        type UserId = Pick<User, "id">;
        type UserOrNull = User | null;
        type UserRecord = Record<string, User>;
        ```

        ## Type Narrowing
        ```typescript
        function process(value: string | number | null) {
            if (value === null) {
                console.log("null");
            } else if (typeof value === "string") {
                console.log(value.toUpperCase());
            } else {
                console.log(value.toFixed(2));
            }
        }
        ```

        ## Discriminated Unions
        ```typescript
        type Result<T> =
            | { status: "success"; data: T }
            | { status: "error"; error: string };

        function handleResult<T>(result: Result<T>) {
            switch (result.status) {
                case "success":
                    console.log(result.data);
                    break;
                case "error":
                    console.error(result.error);
                    break;
            }
        }
        ```

        ## Type Guards
        ```typescript
        function isString(value: unknown): value is string {
            return typeof value === "string";
        }

        function isUser(obj: unknown): obj is User {
            return (
                typeof obj === "object" &&
                obj !== null &&
                "id" in obj &&
                "name" in obj
            );
        }
        ```

        ## Декораторы (экспериментальные)
        ```typescript
        function log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
            const original = descriptor.value;
            descriptor.value = function (...args: any[]) {
                console.log(`Calling ${propertyKey} with`, args);
                return original.apply(this, args);
            };
        }

        class Service {
            @log
            doWork(x: number) {
                return x * 2;
            }
        }
        ```

        ## Модули
        ```typescript
        // export.ts
        export interface Config { debug: boolean; }
        export const DEFAULT_CONFIG: Config = { debug: false };
        export function setup(config: Config): void { /* ... */ }
        export default class App { /* ... */ }

        // import.ts
        import App, { Config, DEFAULT_CONFIG, setup } from "./export";
        import * as Utils from "./utils";
        import type { SomeType } from "./types";
        ```

        ## Современные фичи
        - `satisfies` оператор (TS 4.9+): проверка типа без изменения вывода
        - `const` type parameters (TS 5.0+)
        - `using` declarations (TS 5.2+): ресурсы с деструктором
        - `import type` — только импорт типов
        - `as const` — литеральные типы
        - Nullish coalescing: `??`
        - Optional chaining: `?.`
    """),
    "react_19": textwrap.dedent("""
        # REACT 19 — ШПАРГАЛКА (актуальные возможности)

        ## Новое в React 19
        - Actions: асинхронные переходы для форм и обновлений
        - useActionState: управление состоянием действий
        - useOptimistic: оптимистичные обновления UI
        - useFormStatus: статус отправки формы
        - use: чтение ресурсов (promises, context) в компонентах
        - ref как prop: больше не нужен forwardRef
        - Компилятор React: автоматическая мемоизация
        - Улучшенные Server Components

        ## Функциональные компоненты
        ```tsx
        interface Props {
            title: string;
            onClose: () => void;
            children?: React.ReactNode;
        }

        function Modal({ title, onClose, children }: Props) {
            return (
                <div className="modal">
                    <h2>{title}</h2>
                    {children}
                    <button onClick={onClose}>Закрыть</button>
                </div>
            );
        }
        ```

        ## Хуки: useState, useEffect
        ```tsx
        function Counter() {
            const [count, setCount] = useState(0);

            useEffect(() => {
                document.title = `Счёт: ${count}`;
                return () => {
                    // cleanup
                };
            }, [count]);

            return (
                <button onClick={() => setCount(c => c + 1)}>
                    Счёт: {count}
                </button>
            );
        }
        ```

        ## useMemo, useCallback
        ```tsx
        function ExpensiveList({ items, filter }: Props) {
            const filtered = useMemo(
                () => items.filter(i => i.includes(filter)),
                [items, filter]
            );

            const handleClick = useCallback((id: number) => {
                console.log("Clicked", id);
            }, []);

            return filtered.map(item => (
                <Item key={item} onClick={handleClick} />
            ));
        }
        ```

        ## useReducer
        ```tsx
        type State = { count: number };
        type Action = { type: "increment" } | { type: "decrement" };

        function reducer(state: State, action: Action): State {
            switch (action.type) {
                case "increment":
                    return { count: state.count + 1 };
                case "decrement":
                    return { count: state.count - 1 };
            }
        }

        function Counter() {
            const [state, dispatch] = useReducer(reducer, { count: 0 });
            return (
                <>
                    <button onClick={() => dispatch({ type: "decrement" })}>-</button>
                    <span>{state.count}</span>
                    <button onClick={() => dispatch({ type: "increment" })}>+</button>
                </>
            );
        }
        ```

        ## Context API
        ```tsx
        const ThemeContext = createContext<"light" | "dark">("light");

        function App() {
            return (
                <ThemeContext.Provider value="dark">
                    <Toolbar />
                </ThemeContext.Provider>
            );
        }

        function Toolbar() {
            const theme = useContext(ThemeContext);
            return <div className={theme}>Тулбар</div>;
        }
        ```

        ## React 19: Actions и useActionState
        ```tsx
        function UpdateName() {
            const [state, formAction, isPending] = useActionState(
                async (prevState, formData) => {
                    const name = formData.get("name");
                    // асинхронная операция
                    await updateName(name);
                    return { success: true, name };
                },
                { success: false, name: "" }
            );

            return (
                <form action={formAction}>
                    <input name="name" />
                    <button disabled={isPending}>
                        {isPending ? "Сохранение..." : "Сохранить"}
                    </button>
                </form>
            );
        }
        ```

        ## React 19: useOptimistic
        ```tsx
        function MessageList({ messages, sendMessage }) {
            const [optimisticMessages, addOptimistic] = useOptimistic(
                messages,
                (current, newMessage) => [...current, newMessage]
            );

            async function handleSubmit(formData) {
                const message = formData.get("message");
                addOptimistic({ text: message, pending: true });
                await sendMessage(message);
            }

            return (
                <form action={handleSubmit}>
                    <input name="message" />
                    <button type="submit">Отправить</button>
                </form>
            );
        }
        ```

        ## React 19: ref как prop
        ```tsx
        // React 19 — forwardRef больше не нужен
        function Input({ ref, ...props }: Props & { ref?: React.Ref<HTMLInputElement> }) {
            return <input ref={ref} {...props} />;
        }

        function Parent() {
            const inputRef = useRef<HTMLInputElement>(null);
            return <Input ref={inputRef} placeholder="Введите текст" />;
        }
        ```

        ## React 19: use() хук
        ```tsx
        function Comments({ commentsPromise }) {
            const comments = use(commentsPromise);
            return comments.map(c => <Comment key={c.id} {...c} />);
        }
        ```

        ## Лучшие практики
        - Компоненты — чистые функции
        - Состояние поднимается вверх
        - Ключи в списках: стабильные, уникальные
        - Мемоизация только при реальной проблеме производительности
        - Обработка ошибок: Error Boundaries
        - Строгая типизация пропсов
    """),
    "nodejs_22": textwrap.dedent("""
        # NODE.JS 22 — ШПАРГАЛКА (актуальные возможности)

        ## Новое в Node.js 22
        - require() ESM модулей (синхронный require для ESM)
        - V8 12.4: улучшенная производительность
        - WebSocket клиент (стабильный)
        - --env-file: загрузка .env файлов
        - Улучшенный test runner
        - watch mode: --watch для перезапуска
        - Строгий режим по умолчанию для ESM

        ## ESM модули
        ```javascript
        // file.mjs или "type": "module" в package.json
        import { readFile } from "node:fs/promises";
        import path from "node:path";
        import { fileURLToPath } from "node:url";

        const __filename = fileURLToPath(import.meta.url);
        const __dirname = path.dirname(__filename);

        export function helper() {
            return "helper";
        }

        export default class App {
            constructor() {
                this.name = "App";
            }
        }
        ```

        ## Асинхронное программирование
        ```javascript
        // Промисы
        const data = await fetch("https://api.example.com/data");
        const json = await data.json();

        // Параллельное выполнение
        const [users, posts] = await Promise.all([
            fetch("/api/users").then(r => r.json()),
            fetch("/api/posts").then(r => r.json()),
        ]);

        // Гонка
        const result = await Promise.race([
            fetch("/api/fast").then(r => r.json()),
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error("Timeout")), 5000)
            ),
        ]);
        ```

        ## Файловая система (fs/promises)
        ```javascript
        import { readFile, writeFile, mkdir, readdir } from "node:fs/promises";

        const content = await readFile("config.json", "utf-8");
        await writeFile("output.txt", "данные", "utf-8");
        await mkdir("dist", { recursive: true });
        const files = await readdir("src");
        ```

        ## HTTP сервер
        ```javascript
        import { createServer } from "node:http";

        const server = createServer((req, res) => {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ status: "ok" }));
        });

        server.listen(3000, () => {
            console.log("Сервер запущен на http://localhost:3000");
        });
        ```

        ## Тестирование (node:test)
        ```javascript
        import { test, describe, it, beforeEach } from "node:test";
        import assert from "node:assert/strict";

        describe("Math operations", () => {
            it("should add numbers", () => {
                assert.equal(1 + 1, 2);
            });

            it("should handle async", async () => {
                const result = await Promise.resolve(42);
                assert.equal(result, 42);
            });
        });

        // Запуск: node --test
        ```

        ## Обработка ошибок
        ```javascript
        try {
            const data = await riskyOperation();
        } catch (error) {
            if (error.code === "ENOENT") {
                console.error("Файл не найден");
            } else if (error instanceof SyntaxError) {
                console.error("Синтаксическая ошибка");
            } else {
                console.error("Неизвестная ошибка:", error);
            }
        } finally {
            console.log("Выполнено всегда");
        }
        ```

        ## Полезные модули
        - `node:path` — работа с путями
        - `node:url` — URL парсинг
        - `node:events` — EventEmitter
        - `node:stream` — потоки
        - `node:worker_threads` — многопоточность
        - `node:child_process` — запуск процессов
        - `node:crypto` — криптография
        - `node:util` — утилиты (promisify, inspect)
    """),
}


def load_cheatsheets(rag) -> int:
    """Загружает шпаргалки по языкам программирования в RAG."""
    total_chunks = 0

    for name, content in CHEATSHEETS.items():
        doc_text = content.strip()
        chunks = rag.add_document(doc_text, {"source": "cheatsheet", "topic": name})
        total_chunks += chunks
        print(f"  [OK] Шпаргалка: {name} — {chunks} чанков")

    return total_chunks


# ============================================================
# 3. Документация библиотек (скачивание с официальных сайтов)
# ============================================================

LIBRARY_PAGES = {
    "fastapi": {
        "base_url": "https://fastapi.tiangolo.com",
        "description": "FastAPI — современный веб-фреймворк для Python",
        "pages": [
            "/",
            "/tutorial/first-steps/",
            "/tutorial/path-params/",
            "/tutorial/query-params/",
            "/tutorial/body/",
            "/tutorial/request-forms/",
            "/tutorial/dependencies/",
            "/tutorial/security/",
            "/tutorial/sql-databases/",
            "/tutorial/testing/",
            "/tutorial/static-files/",
            "/tutorial/middleware/",
            "/tutorial/cors/",
            "/tutorial/websockets/",
            "/tutorial/background-tasks/",
            "/advanced/async-sql-databases/",
            "/advanced/websockets/",
            "/advanced/testing-websockets/",
            "/advanced/events/",
            "/advanced/settings/",
            "/advanced/response-directly/",
            "/advanced/custom-response/",
            "/advanced/using-request-directly/",
            "/advanced/websockets/",
        ],
    },
    "chromadb": {
        "base_url": "https://docs.trychroma.com",
        "description": "ChromaDB — векторная база данных для RAG",
        "pages": [
            "/",
            "/docs/overview/getting-started",
            "/docs/overview/usage-guide",
            "/docs/guides/creating-embeddings",
            "/docs/guides/adding-data",
            "/docs/guides/querying-data",
            "/docs/guides/updating-data",
            "/docs/guides/deleting-data",
            "/docs/guides/metadata-filtering",
            "/docs/guides/integrations",
            "/docs/api-reference",
            "/docs/api-reference/collection",
            "/docs/api-reference/client",
            "/docs/api-reference/embeddings",
            "/docs/api-reference/query",
            "/docs/api-reference/telemetry",
        ],
    },
    "langchain": {
        "base_url": "https://python.langchain.com",
        "description": "LangChain — фреймворк для LLM-приложений",
        "pages": [
            "/",
            "/docs/introduction/",
            "/docs/concepts/",
            "/docs/tutorials/llm_chain/",
            "/docs/tutorials/chatbot/",
            "/docs/tutorials/qa_chat_history/",
            "/docs/tutorials/agents/",
            "/docs/tutorials/rag/",
            "/docs/how_to/",
            "/docs/integrations/text_embedding/",
            "/docs/integrations/vectorstores/",
            "/docs/concepts/rag/",
            "/docs/concepts/agents/",
            "/docs/concepts/tools/",
            "/docs/concepts/memory/",
        ],
    },
}


def fetch_page(url: str, timeout: int = 10) -> str:
    """Скачивает страницу и извлекает основной текстовый контент."""
    import requests
    from bs4 import BeautifulSoup
    import urllib3

    # Отключаем предупреждения SSL (некоторые сайты имеют проблемы с сертификатами)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()
    except Exception as e:
        print(f"    [ERROR] Не удалось скачать {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    # Удаляем скрипты, стили, навигацию
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Основной контент
    main = soup.find("main") or soup.find("article") or soup.find("body")
    if not main:
        return ""

    text = main.get_text(separator="\n", strip=True)
    # Ограничиваем размер страницы
    return text[:20000]


def load_library_docs(rag) -> int:
    """Скачивает и загружает документацию библиотек в RAG."""
    import requests

    total_chunks = 0

    for lib_name, lib_info in LIBRARY_PAGES.items():
        print(f"\n  [{lib_name}] Загрузка документации...")
        for page in lib_info["pages"]:
            url = lib_info["base_url"] + page
            print(f"    Скачивание: {url}")
            text = fetch_page(url)
            if not text:
                continue

            doc_text = f"# {lib_name} — {lib_info['description']}\nИсточник: {url}\n\n{text}"
            chunks = rag.add_document(doc_text, {"source": "library_docs", "library": lib_name, "url": url})
            total_chunks += chunks
            print(f"    [OK] {chunks} чанков")

    return total_chunks


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Загрузка документации в RAG")
    parser.add_argument("--project-only", action="store_true", help="Только документация проекта")
    parser.add_argument("--cheatsheets", action="store_true", help="Только шпаргалки")
    parser.add_argument("--libraries", action="store_true", help="Только документация библиотек")
    parser.add_argument("--collection", default=COLLECTION, help="Имя RAG-коллекции")
    args = parser.parse_args()

    # Если ничего не указано — загружаем всё
    do_project = args.project_only or not (args.cheatsheets or args.libraries)
    do_cheatsheets = args.cheatsheets or not (args.project_only or args.libraries)
    do_libraries = args.libraries or not (args.project_only or args.cheatsheets)

    print("=" * 60)
    print("Загрузка документации в RAG")
    print(f"Коллекция: {args.collection}")
    print("=" * 60)

    rag = get_rag_engine(collection_name=args.collection)
    if not rag.available:
        print("[ERROR] RAG-движок недоступен. Проверьте установку chromadb и sentence-transformers.")
        sys.exit(1)

    total = 0

    if do_project:
        print("\n[1/3] Документация проекта...")
        total += load_project_docs(rag)

    if do_cheatsheets:
        print("\n[2/3] Шпаргалки по языкам...")
        total += load_cheatsheets(rag)

    if do_libraries:
        print("\n[3/3] Документация библиотек...")
        total += load_library_docs(rag)

    print("\n" + "=" * 60)
    print(f"Готово! Загружено чанков: {total}")
    print("=" * 60)


if __name__ == "__main__":
    main()