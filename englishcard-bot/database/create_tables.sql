-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы общего пула слов
CREATE TABLE IF NOT EXISTS word_pool (
    word_id SERIAL PRIMARY KEY,
    english_word VARCHAR(100) UNIQUE NOT NULL,
    russian_translation VARCHAR(100) NOT NULL,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by BIGINT DEFAULT NULL
);

-- Создание таблицы связей пользователей и слов
CREATE TABLE IF NOT EXISTS user_words (
    user_word_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    word_id INTEGER REFERENCES word_pool(word_id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, word_id)
);

-- Создание таблицы статистики
CREATE TABLE IF NOT EXISTS statistics (
    stat_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    word_id INTEGER REFERENCES word_pool(word_id) ON DELETE CASCADE,
    is_correct BOOLEAN NOT NULL,
    answer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reaction_time INTERVAL
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_user_words_user ON user_words(user_id);
CREATE INDEX IF NOT EXISTS idx_user_words_active ON user_words(is_active);
CREATE INDEX IF NOT EXISTS idx_statistics_user_date ON statistics(user_id, answer_date);
CREATE INDEX IF NOT EXISTS idx_statistics_word ON statistics(word_id);
CREATE INDEX IF NOT EXISTS idx_word_pool_english ON word_pool(english_word);
CREATE INDEX IF NOT EXISTS idx_word_pool_russian ON word_pool(russian_translation);

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Таблица пользователей Telegram бота';
COMMENT ON TABLE word_pool IS 'Общий пул английских слов с переводом';
COMMENT ON TABLE statistics IS 'Статистика ответов пользователей';