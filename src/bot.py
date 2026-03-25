import telebot
import time
import threading
from datetime import datetime
from config import TELEGRAM_TOKEN, CHAT_ID
from notion_service import create_task, get_tasks, mark_task_done, delete_task

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    print(f"Chat ID: {chat_id}")

    bot.reply_to(
        message,
        "👋 Hola, soy tu bot de tareas.\nUsa /add para agregar una tarea"
    )

@bot.message_handler(commands=['add'])
def add_task(message):
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Uso:\n/add tarea | YYYY-MM-DD")
        return

    content = parts[1]

    # Separar tarea y fecha
    if "|" in content:
        task_text, date_text = content.split("|", 1)
        task_text = task_text.strip()
        date_text = date_text.strip()

        try:
            due_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except:
            bot.reply_to(message, "⚠️ Fecha inválida. Usa formato YYYY-MM-DD")
            return
    else:
        task_text = content.strip()
        due_date = None

    if task_text == "":
        bot.reply_to(message, "⚠️ Escribe una tarea válida")
        return

    status, response = create_task(task_text, due_date)

    if status == 200:
        bot.reply_to(message, f"✅ Tarea guardada:\n📝 {task_text}")
    else:
        bot.reply_to(message, "❌ Error al guardar")
        print(response)

@bot.message_handler(commands=['list'])
def list_tasks(message):
    tasks, error = get_tasks()

    if error:
        bot.reply_to(message, "❌ Error al obtener tareas")
        print(error)
        return

    if not tasks:
        bot.reply_to(message, "📭 No hay tareas registradas")
        return

    response_text = "📋 *Tareas pendientes:*\n\n"

    for i, task in enumerate(tasks, start=1):
        status = "✅" if task["done"] else "⬜"
        response_text += f"{i}. {status} {task['name']}\n"

    bot.reply_to(message, response_text, parse_mode="Markdown")

@bot.message_handler(commands=['done'])
def done_task(message):
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(
            message,
            "⚠️ Usa el número de la tarea.\nEjemplo:\n/done 1"
        )
        return

    task_index = int(parts[1]) - 1

    tasks, error = get_tasks()

    if error:
        bot.reply_to(message, "❌ Error al obtener tareas")
        return

    if task_index < 0 or task_index >= len(tasks):
        bot.reply_to(message, "⚠️ Número de tarea inválido")
        return

    task = tasks[task_index]

    status, response = mark_task_done(task["id"])

    if status == 200:
        bot.reply_to(message, f"✅ Tarea completada:\n📝 {task['name']}")
    else:
        bot.reply_to(message, "❌ Error al actualizar la tarea")
        print(response)

@bot.message_handler(commands=['delete'])
def delete_task_command(message):
    parts = message.text.split(maxsplit=1)

    # Validación
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(
            message,
            "⚠️ Usa el número de la tarea.\nEjemplo:\n/delete 1"
        )
        return

    task_index = int(parts[1]) - 1

    tasks, error = get_tasks()

    if error:
        bot.reply_to(message, "❌ Error al obtener tareas")
        return

    if task_index < 0 or task_index >= len(tasks):
        bot.reply_to(message, "⚠️ Número de tarea inválido")
        return

    task = tasks[task_index]

    status, response = delete_task(task["id"])

    if status == 200:
        bot.reply_to(message, f"🗑️ Tarea eliminada:\n📝 {task['name']}")
    else:
        bot.reply_to(message, "❌ Error al eliminar la tarea")
        print(response)

from datetime import datetime, date

def reminder_loop():
    while True:
        print("⏰ Revisando tareas con fecha...")

        tasks, error = get_tasks()

        if not error and tasks:
            today = date.today()
            message = "⏰ Recordatorios:\n\n"

            has_tasks = False

            for task in tasks:
                if task["done"]:
                    continue

                if task["due"]:
                    due_date = datetime.strptime(task["due"], "%Y-%m-%d").date()

                    # Si es hoy o ya venció
                    if due_date <= today:
                        message += f"⚠️ {task['name']} (HOY o ATRASADA)\n"
                        has_tasks = True

                    # Si es mañana
                    elif (due_date - today).days == 1:
                        message += f"⏳ {task['name']} (mañana)\n"
                        has_tasks = True

            if has_tasks:
                bot.send_message(CHAT_ID, message)

        time.sleep(60)

print("Bot corriendo...")
threading.Thread(target=reminder_loop).start()
bot.polling()