# -*- coding: utf-8 -*-
import datetime

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup

import logging as log
import common
import secrets
from common import today, tomorrow, get_partenza
from inline import separate_callback_data, create_callback_data


# Comando iniziale che viene chiamato dall'utente
def prenota(bot, update):
    keyboard = []
    keyboard.append([InlineKeyboardButton("Prenotare una-tantum",
                                          callback_data=create_callback_data("BOOKING", ["Temporary"]))])
    keyboard.append([InlineKeyboardButton("Prenotare in maniera permanente",
                                          callback_data=create_callback_data("BOOKING", ["Permanent"]))])
    keyboard.append([InlineKeyboardButton("Visualizza e disdici una prenotazione",
                                          callback_data=create_callback_data("DELETEBOOKING", []))])
    bot.send_message(chat_id=update.message.chat_id,
                     text="Cosa vuoi fare?",
                     reply_markup=InlineKeyboardMarkup(keyboard))


# Funzione per prelevare le prenotazioni da secrets
def fetch_bookings(bot, update, date):
    if (date == today() and common.is_today_weekday()) or (date == tomorrow() and common.is_tomorrow_weekday()):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Lista delle prenotazioni per "
                              + date.lower() + ": ")

        groups = secrets.groups_morning[date]
        if len(groups) > 0:
            message = "Persone in salita: \n\n"
            for day in groups:
                people = [secrets.users[user] for day in groups for mode in groups[day] for user in groups[day][mode]]
                bot.send_message(chat_id=update.message.chat_id,
                                 text=message + secrets.users[day] + ":\n" + ", ".join(people))

        groups = secrets.groups_evening[date]
        if len(groups) > 0:
            message = "Persone in discesa: \n\n"
            for day in groups:
                people = [secrets.users[user] for day in groups for k in groups[day] for user in groups[day][k]]
                bot.send_message(chat_id=update.message.chat_id,
                                 text=message + secrets.users[day] + ":\n" + ", ".join(people))

    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=date + " UberNEST non sarà attivo.")


# Funzione chiamata in seguito alla risposta dell'utente
def booking_handler(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    data = separate_callback_data(update.callback_query.data)
    mode = data[1]

    log.info("Mode:" + str(mode) + ", length: " + str(len(data)))

    if len(data) == 2 and (mode == "Permanent" or mode == "Temporary"):
        time = (datetime.datetime.now() + datetime.timedelta(hours=1 + common.is_dst())).time()
        if datetime.time(6, 0) <= time <= datetime.time(20, 0) and common.is_tomorrow_weekday():
            bot.send_message(chat_id=chat_id,
                             text="Scegli una persona:",
                             reply_markup=persone_keyboard(mode, tomorrow()))
        else:
            bot.send_message(chat_id=chat_id,
                             text="Mi dispiace, è possibile effettuare prenotazioni"
                                  " tramite il bot solo dalle 6:00 alle 20:00 del giorno"
                                  " prima. Inoltre, UberNEST è attivo dal Lunedì al Venerdì.")
    elif (mode == "Permanent" or mode == "Temporary"):
        person, direction = data[2:]
        person = str(person).decode('utf-8')

        try:
            if direction == "Salita":
                groups = secrets.groups_morning[tomorrow()]
            elif direction == "Discesa":
                groups = secrets.groups_evening[tomorrow()]
            else:
                groups = None
        except KeyError as ex:
            groups = None

        booker = str(chat_id).decode('utf-8')
        if len(groups[person]["Permanent"]) + len(groups[person]["Temporary"]) < 4:
            if booker == person:
                bot.send_message(chat_id=chat_id, text="Sei tu l'autista!")
            elif booker not in groups[person]["Temporary"] and \
                    booker not in groups[person]["Permanent"]:
                bot.send_message(chat_id=chat_id, text="Prenotato con "
                                                       + secrets.users[person] + " per domani con successo.")
                groups[person][mode].append(booker)
            else:
                bot.send_message(chat_id=chat_id, text="Ti sei già prenotato per domani con questa persona!")
        else:
            bot.send_message(chat_id=chat_id, text="Posti per domani esauriti.")


def deletebooking_handler(bot, update):
    chat_id = update.callback_query.from_user.id
    data = separate_callback_data(update.callback_query.data)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if len(data) == 1:
        bookings = common.search_by_booking(chat_id)
        if len(bookings) > 0:
            keyboard = []
            for i in bookings:
                direction, day, driver, mode = i
                if mode == "Temporary":
                    keyboard.append([InlineKeyboardButton("Temporanea con " + secrets.users[driver] + " - " +
                                                          get_partenza(driver, day, direction),
                                                          callback_data=create_callback_data("DELETEBOOKING", [i]))])
                else:
                    keyboard.append([InlineKeyboardButton("Permanente con " + secrets.users[driver] + " - " +
                                                          get_partenza(driver, day, direction),
                                                          callback_data=create_callback_data("DELETEBOOKING", [i]))])
            keyboard.append([InlineKeyboardButton("Annulla", callback_data=create_callback_data("DELETEBOOKING", ["CANCEL"]))])
            bot.send_message(chat_id=chat_id, text="Clicca su una prenotazione per cancellarla.",
                             reply_markup=InlineKeyboardMarkup([keyboard]))
        else:
            bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non hai prenotazioni all'attivo.")
    elif len(data) == 3:
        if data[1] == "CANCEL":
            bot.send_message(chat_id=chat_id, text="Operazione annullata")
        else:
            keyboard = []
            keyboard.append(InlineKeyboardButton(
                "Sì", callback_data=create_callback_data("DELETEBOOKING", ["CONFIRM", data[1]])))
            keyboard.append(InlineKeyboardButton(
                "No", callback_data=create_callback_data("DELETEBOOKING", ["CANCEL"])))
            bot.send_message(chat_id=chat_id,
                             text="Sei sicuro di voler cancellare questo viaggio?",
                             reply_markup=InlineKeyboardMarkup([keyboard]))
    elif len(data) == 4:
        direction, day, driver, mode = data[2]
        if direction == "Salita":
            secrets.groups_morning[day][driver][mode].remove(chat_id)
        elif direction == "Discesa":
            secrets.groups_evening[day][driver][mode].remove(chat_id)
        bot.send_message(chat_id=chat_id, text="Prenotazione cancellata con successo.")


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
# Day è un oggetto di tipo stringa
def persone_keyboard(mode, day):
    keyboard = []
    for i in secrets.groups_morning[day]:
        try:
            keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, day, "Salita"),
                                                  callback_data=create_callback_data("BOOKING", [mode, i, "Salita"]))])
        except TypeError as ex:
            log.info("No bookings found")
    for i in secrets.groups_evening[day]:
        try:
            keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, day, "Discesa"),
                                                  callback_data=create_callback_data("BOOKING", [mode, i, "Discesa"]))])
        except TypeError as ex:
            log.info("No bookings found")
    return InlineKeyboardMarkup(keyboard)
