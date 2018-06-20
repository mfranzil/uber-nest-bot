# -*- coding: utf-8 -*-

import datetime
import secrets
from inline import persone_keyboard, next_day


# TODO: Aggiungere tutti i try-catch

class ReplyStatus:
    response_mode = 0

    def __init__(self):
        pass

    @staticmethod
    def allfalse():
        ReplyStatus.response_mode = 0


def text_filter(bot, update):
    if ReplyStatus.response_mode == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Digita /help per avere informazioni sui comandi.")
    elif ReplyStatus.response_mode == 1:
        response_registra(bot, update)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Benvenuto nel bot di UberNEST. Per iniziare,"
                          " digita /help per visualizzare i comandi.")


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Comandi disponibili:")
    bot.send_message(chat_id=update.message.chat_id,
                     text="/status - Visualizza le prenotazioni correnti.\n"
                          "/prenota - Effettua una prenotazione.\n"
                          "/registra - Aggiungi il tuo nome al database.")


def status(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Lista delle prenotazioni per domani: ")

    groups = secrets.groups_morning[next_day()]
    if len(groups) > 0:
        message = "Persone in salita: \n\n"
        for i in groups:
            people = []
            for k in groups[i]:
                people.append(secrets.users[k])
            bot.send_message(chat_id=update.message.chat_id,
                             text=message + secrets.users[i] + ":\n" + ", ".join(people))

    groups = secrets.groups_evening[next_day()]
    if len(groups) > 0:
        message = "Persone in discesa: \n\n"
        for i in groups:
            people = []
            for k in groups[i]:
                people.append(secrets.users[k])
            bot.send_message(chat_id=update.message.chat_id,
                             text=message + secrets.users[i] + ":\n" + ", ".join(people))


def prenota(bot, update):
    time = (datetime.datetime.now() + datetime.timedelta(hours=1)).time()
    if datetime.time(6, 0) <= time <= datetime.time(20, 0):  # TODO FIX DST
        bot.send_message(chat_id=update.message.chat_id,
                         text="Scegli una persona:",
                         reply_markup=persone_keyboard())
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Mi dispiace, è possibile effettuare prenotazioni"
                              " tramite il bot solo dalle 6:00 alle 20:00 del giorno"
                              " prima.")


def registra(bot, update):
    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Questo utente risulta già iscritto a sistema!")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Disclaimer sul regolamento etc...")  # TODO Expand
        bot.send_message(chat_id=update.message.chat_id,
                         text="Inserire nome e cognome, che verranno mostrati"
                              " sia agli autisti sia ai passeggeri. Ogni violazione di"
                              " queste regole verrà punita con la rimozione dal"
                              " sistema.")
        ReplyStatus.response_mode = 1


def response_registra(bot, update):
    user = update.message.text
    secrets.users[str(update.message.chat_id)] = str(user)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Il tuo username è stato aggiunto con successo"
                          " al Database. Contatta un membro del Direttivo"
                          " se desideri diventare un autista di UberNest.")
    ReplyStatus.response_mode = 0
