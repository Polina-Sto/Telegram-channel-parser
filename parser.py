# Этап 1. Подготовка к работе, импорт библиотек.
# импорт библиотек
from telethon.sync import TelegramClient
from telethon import events, types
import pandas as pd
import asyncio
import nest_asyncio
import logging 

# настройка логирования. Для последующего вывода информации об ошибках
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# запуск асинхронной работы программы
nest_asyncio.apply()

#запись переменных для работы
api_id = ''
api_hash = ''
channel_username = '' 
phone = '' 

# создание телеграм клиента для получения данных о канале
client = TelegramClient(phone, api_id, api_hash)

# Этап 2. Создание основной функции для сбора, сортировки и записи данных.
# Асинхронная функция для получения постов и реакций
async def main():
    try:
        # async with client: для корректного закрытия соединения
        async with client:
            await client.start()
            logger.info(" Авторизация успешна. Подключено к Telegram.")

            posts_data = []
            # Проверяем, существует ли канал и доступен ли он
            try:
                entity = await client.get_entity(channel_username)
                logger.info(f" Парсим канал: {entity.title} (ID: {entity.id})")
            except Exception as e:
                logger.error(f" Не удалось получить информацию о канале '{channel_username}': {e}")
                logger.error("Убедитесь, что юзернейм канала указан верно, канал публичный или вы состоите в нём.")
                return 

            processed_count = 0
            async for message in client.iter_messages(entity):
                processed_count += 1
                if processed_count % 10 == 0: # Оповещение каждые 10 сообщений
                    logger.info(f"Обработано {processed_count} сообщений...")

                reactions_summary = {}
                total_reactions = 0

                # Обработка реакций
                if message.reactions and message.reactions.results:
                    for r in message.reactions.results:
                        reaction_key = ""
                        if isinstance(r.reaction, types.ReactionEmoji):
                            # Стандартные эмодзи
                            reaction_key = r.reaction.emoticon
                        elif isinstance(r.reaction, types.ReactionCustomEmoji):
                            # Кастомные эмодзи (Telegram Premium)
                            # поэтому используем их document_id как идентификатор
                            reaction_key = f"custom_emoji_{r.reaction.document_id}"
                        else:
                            # Если появится новый тип реакции
                            reaction_key = str(r.reaction)

                        reactions_summary[reaction_key] = r.count
                        total_reactions += r.count
          
                vi = message.views if hasattr(message, 'views') else 0
                # Добавление данных о посте
                posts_data.append({
                    'id': message.id,
                    'date': message.date.replace(tzinfo=None) if message.date else None, # Убираем timezone для Excel
                    'text': (message.text[:500] + '...') if message.text and len(message.text) > 500 else (message.text if message.text else ''),
                    'reactions_detail': str(reactions_summary), # Детальный список реакций
                    'total_reactions': total_reactions,
                    'views': vi,
                    'act': message.action_entities
            })

        if not posts_data:
            logger.warning(" Не найдено сообщений в канале или не удалось их обработать.")
            return

	 # Вывод информации и сортировка
        df = pd.DataFrame(posts_data)
        df_sorted = df.sort_values(by='total_reactions', ascending=False)

        logger.info("\n ТОП-5 постов по соотношению реакций и просмотров:")
        print(df_sorted[['id', 'date', 'text', 'total_reactions', 'views', 'act']].head().to_string())

	 # Запись информации в файл  xlsx и его сохранение на компьютер
        output_filename = 'telegram_channel_analysis.xlsx'
        df.to_excel(output_filename, index=False)
        logger.info(f"\n Все данные сохранены в файл {output_filename}")

    except Exception as e:
        logger.exception(f"❌ Произошла ошибка в процессе парсинга: {e}")

# Этап 3. Запуск работы основной функции.
if __name__ == "__main__":
    logger.info("Запуск парсера Telegram-канала...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Парсер остановлен пользователем.")
    except Exception as e:
        logger.exception(f"Критическая ошибка при запуске: {e}")
