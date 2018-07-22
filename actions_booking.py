# -*- coding: utf-8 -*-

import datetime
import logging as log
import common
import secrets
import inline

from common import tomorrow, get_partenza
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup


# Comando iniziale che viene chiamato dall'utente
def prenota(bot, update):
    if str(update.message.chat_id) in secrets.users:
        keyboard = [[InlineKeyboardButton("Prenotare una-tantum (solo per il giorno dopo)",
                                          callback_data=inline.create_callback_data("BOOKING", ["Temporary"]))],
                    [InlineKeyboardButton("Prenotare in maniera permanente",
                                          callback_data=inline.create_callback_data("BOOKING", ["Permanent"]))],
                    [InlineKeyboardButton("Visualizza e disdici una prenotazione",
                                          callback_data=inline.create_callback_data("DELETEBOOKING", []))],
                    [InlineKeyboardButton("Esci dal menu",
                                          callback_data=inline.create_callback_data("CANCEL", []))]]
        bot.send_message(chat_id=update.message.chat_id,
                         text="Cosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Per effettuare una prenotazione, registrati con /registra.")


# Funzione chiamata in seguito alla risposta dell'utente
def booking_handler(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    data = inline.separate_callback_data(update.callback_query.data)
    mode = data[1]

    log.info("Mode:" + str(mode) + ", length: " + str(len(data)))

    if len(data) == 2 and mode == "Temporary":
        if common.booking_time():
            bot.send_message(chat_id=chat_id,
                             text="Scegli una persona:",
                             reply_markup=booking_keyboard(mode, tomorrow()))
        else:
            bot.send_message(chat_id=chat_id,
                             text="Mi dispiace, è possibile effettuare prenotazioni"
                                  " tramite il bot solo dalle 6:00 alle 20:00 del giorno"
                                  " prima. Inoltre, UberNEST è attivo dal Lunedì al Venerdì.")
    elif len(data) == 2 and mode == "Permanent":
        bot.send_message(chat_id=chat_id, text="Funzionalità non ancora implementata")
    elif mode == "Permanent" or mode == "Temporary":
        person, direction = data[2:]

        person = str(person).decode('utf-8')
        booker = str(chat_id).decode('utf-8')

        trips = secrets.groups[direction][tomorrow()][person]

        if len(trips["Permanent"]) + len(trips["Temporary"]) < 4:
            if booker == person:
                bot.send_message(chat_id=chat_id, text="Sei tu l'autista!")
            elif booker not in trips["Temporary"] and booker not in trips["Permanent"]:
                trips[mode].append(booker)
                bot.send_message(chat_id=chat_id, text="Prenotato con "
                                                       + secrets.users[person] + " per domani con successo.")
            else:
                bot.send_message(chat_id=chat_id, text="Ti sei già prenotato per domani con questa persona!")
        else:
            bot.send_message(chat_id=chat_id, text="Posti per domani esauriti.")


def deletebooking_handler(bot, update):
    chat_id = update.callback_query.from_user.id
    data = inline.separate_callback_data(update.callback_query.data)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    log.info("Length: " + str(len(data)))

    if len(data) == 1:
        bookings = common.search_by_booking(str(chat_id))
        if len(bookings) > 0:
            keyboard = []
            for i in bookings:
                direction, day, driver, mode = i

                keyboard.append(
                    [InlineKeyboardButton(common.localize_direction(mode) + " il " + day
                                          + " con " + secrets.users[driver] + " - " +
                                          get_partenza(driver, day, direction),
                                          callback_data=inline.create_callback_data("DELETEBOOKING", i))])
            keyboard.append(
                [InlineKeyboardButton("Annulla",
                                      callback_data=inline.create_callback_data("DELETEBOOKING", ["CANCEL"]))])
            bot.send_message(chat_id=chat_id, text="Clicca su una prenotazione per cancellarla.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non hai prenotazioni all'attivo.")
    elif len(data) == 5:
        keyboard = []
        data[0] = "CONFIRM"

        keyboard.append(InlineKeyboardButton(
            "Sì", callback_data=inline.create_callback_data("DELETEBOOKING", data)))
        keyboard.append(InlineKeyboardButton(
            "No", callback_data=inline.create_callback_data("CANCEL", [])))

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif len(data) == 6:
        direction, day, driver, mode = data[2:]
        secrets.groups[direction][day][driver][mode].remove(str(chat_id))
        bot.send_message(chat_id=chat_id, text="Prenotazione cancellata con successo.")


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
# Day è un oggetto di tipo stringa
def booking_keyboard(mode, day):
    keyboard = []

    for direction in secrets.groups:
        for driver in secrets.groups[direction][day]:
            try:
                keyboard.append(
                    [InlineKeyboardButton(secrets.users[driver] + " - " + get_partenza(driver, day, direction),
                                          callback_data=inline.create_callback_data("BOOKING",
                                                                                    [mode, driver, direction]))])
            except TypeError:
                log.info("No bookings found")

    keyboard.append([InlineKeyboardButton("Annulla", callback_data=inline.create_callback_data("CANCEL", []))])
    return InlineKeyboardMarkup(keyboard)
