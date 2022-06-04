import telebot
from telebot import types
import pymysql.cursors

connection = pymysql.connect(host='127.0.0.1',
                             user='root',
                             password='Asdfgh123!',
                             db='schedule_bot',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

token = ''
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.send_message(message.chat.id, "Привіт, я бот який допоможе тобі тримати розклад завжді під рукою")
    bot.send_message(message.chat.id, "Щоб дізнатися розклад своєї групи треба просто написати мені номер групи")
    bot.send_message(message.chat.id, "Щоб дізнатися розклад для викладача просто напишіть мені: Викладач")

def get_connection():
    return pymysql.connect(host='0.0.0.0',
                           user='root',
                           password='Asdfgh123!',
                           db='schedule_bot',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)


def get_all_groups():
    sql = "SELECT name FROM `groups`;"
    groups = []
    with get_connection().cursor() as cursor:
        cursor.execute(sql)
        for row in cursor:
            groups.append(row['name'])
    return groups


@bot.message_handler(content_types=['text'])
def receive_message(message):
    if message.text in get_all_groups():
        get_group_schedule(message)
    if message.text == 'Викладач':
        get_teachers(message)


def get_teachers(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    sql = "SELECT * FROM teachers;"
    with get_connection().cursor() as cursor:
        cursor.execute(sql)
        for row in cursor:
            markup.row(row['last_name'] + " " + row['first_name'][0] + ". " + row['father_name'][0] + ".")
    msg = bot.send_message(message.chat.id, "Виберіть викладача", reply_markup=markup)
    bot.register_next_step_handler(msg, get_teacher_schedule)


def get_teacher_schedule(message):
    bot.send_message(message.chat.id,
                     "Викладач " + message.text + ". Вкажіть дату на яку ви хочете переглянути розклад")
    sql = "SELECT date FROM `schedules` JOIN `teachers` ON `teachers`.id = schedules.teacher_id WHERE " \
          "teachers.last_name = SUBSTRING_INDEX('{}', ' ', 1) and teachers.first_name like concat(substr(substring_index('{}',' ', -2), 1, 1), '%') " \
          "and teachers.father_name like concat(substr(substring_index('{}',' ', -1), 1, 1), '%') group by date;".format(
        message.text, message.text, message.text)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    with get_connection().cursor() as cursor:
        cursor.execute(sql)
        for row in cursor:
            markup.row(row['date'].strftime("%Y-%m-%d"))
    msg = bot.send_message(message.chat.id, "Виберіть день", reply_markup=markup)
    bot.register_next_step_handler(msg, get_schedule_by_teacher_for_concrete_day, message.text)


def get_schedule_by_teacher_for_concrete_day(message, teacherName):
    sql = "SELECT * FROM `schedules` JOIN `groups` ON `groups`.id = schedules.group_id JOIN `subjects` on `schedules`.subject_id = `subjects`.id JOIN `teachers` on `teachers`.id = `schedules`.id WHERE " \
          "teachers.last_name = SUBSTRING_INDEX('{}', ' ', 1) and teachers.first_name like concat(substr(substring_index('{}',' ', -2), 1, 1), '%') " \
          "and teachers.father_name like concat(substr(substring_index('{}',' ', -1), 1, 1), '%') and `date` = '{}';".format(
        teacherName, teacherName, teacherName, message.text)
    with get_connection().cursor() as cursor:
        cursor.execute(sql)
        for row in cursor:
            text = '\U0001f4da: ' + row['subjects.name'] + ", Группа: " + str(row['name']) + " Викладач: " + str(
                row['last_name']) + " " + str(row['first_name']) + " " + str(row['father_name'])
            bot.send_message(message.chat.id, text)
        sqlForReplacements = "SELECT * FROM replacements " \
                             "JOIN schedules on replacements.schedule_id = schedules.id " \
                             "JOIN `groups` ON schedules.group_id = `groups`.id " \
                             "join teachers t on replacements.teacher_id = t.id " \
                             "join teachers t2 on schedules.teacher_id = t2.id " \
                             "join subjects s on replacements.subject_id = s.id " \
                             "join subjects s2 on schedules.subject_id = s2.id " \
                             "WHERE (t.last_name = SUBSTRING_INDEX('{}', ' ', 1) and t.first_name like concat(substr(substring_index('{}',' ', -2), 1, 1), '%') " \
                             "and t.father_name like concat(substr(substring_index('{}',' ', -1), 1, 1), '%')) or " \
                             "(t2.last_name = SUBSTRING_INDEX('{}', ' ', 1) and t2.first_name like concat(substr(substring_index('{}',' ', -2), 1, 1), '%') " \
                             "and t2.father_name like concat(substr(substring_index('{}',' ', -1), 1, 1), '%')) " \
                             "and schedules.date = '{}';".format(teacherName, teacherName, teacherName, teacherName, teacherName, teacherName, message.text)
        if cursor.execute(sqlForReplacements) != 0:
            bot.send_message(message.chat.id, "Заміни: ")
            for sRow in cursor:
                bot.send_message(message.chat.id,
                                 "Замість {}ї пари({}) викладається {}, викладач {}".format(sRow['lesson'],
                                                                                            sRow['s2.name'],
                                                                                            sRow['s.name'],
                                                                                            sRow['last_name'] + " " +
                                                                                            sRow['first_name'] + " " +
                                                                                            sRow['father_name']))

    bot.register_for_reply(message, get_schedule_by_teacher_for_concrete_day)


def get_group_schedule(message):
    bot.send_message(message.chat.id,
                     "Добре, ваша группа " + message.text + ". Вкажіть дату на яку ви хочете переглянути розклад")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    sql = "SELECT date FROM `schedules` JOIN `groups` ON `groups`.id = schedules.group_id WHERE `groups`.name = '{}' group by date;".format(
        message.text)
    with get_connection().cursor() as cursor:
        cursor.execute(sql)
        for row in cursor:
            markup.row(row['date'].strftime("%Y-%m-%d"))
    msg = bot.send_message(message.chat.id, "Виберіть день", reply_markup=markup)
    bot.register_next_step_handler(msg, get_schedule_by_group_for_concrete_day, message.text)


def get_schedule_by_group_for_concrete_day(message, group):
    sql = "SELECT * FROM `schedules` JOIN `groups` ON `groups`.id = schedules.group_id JOIN `subjects` on `schedules`.subject_id = `subjects`.id JOIN `teachers` on `teachers`.id = `schedules`.id WHERE `groups`.name = '{}' and `date` = '{}';".format(
        group, message.text)
    with get_connection().cursor() as cursor:
        cursor.execute(sql)
        bot.send_message(message.chat.id, "Розклад на " + message.text)
        for row in cursor:
            text = '\U0001f4da: ' + row['subjects.name'] + ", Пара: " + str(row['lesson']) + ", Викладач: " + row[
                'last_name'] + " " + row['first_name'] + " " + row['father_name'] + ", Аудиторія: " + row['cabinet']
            bot.send_message(message.chat.id, text)
        sqlForReplacements = "SELECT * FROM replacements " \
                             "JOIN schedules on replacements.schedule_id = schedules.id " \
                             "JOIN `groups` ON schedules.group_id = `groups`.id " \
                             "join teachers t on replacements.teacher_id = t.id " \
                             "join teachers t2 on schedules.teacher_id = t2.id " \
                             "join subjects s on replacements.subject_id = s.id " \
                             "join subjects s2 on schedules.subject_id = s2.id " \
                             "WHERE `groups`.name = '{}' and schedules.date = '{}';".format(group, message.text)
        if cursor.execute(sqlForReplacements) != 0:
            bot.send_message(message.chat.id, "Заміни: ")
            for sRow in cursor:
                bot.send_message(message.chat.id,
                                 "Замість {}ї пари({}) викладається {}, викладач {}".format(sRow['lesson'],
                                                                                            sRow['s2.name'],
                                                                                            sRow['s.name'],
                                                                                            sRow['last_name'] + " " + sRow['first_name'] + " " + sRow['father_name']))

    bot.register_for_reply(message, get_schedule_by_group_for_concrete_day)


if __name__ == '__main__':
    bot.polling(none_stop=True)
