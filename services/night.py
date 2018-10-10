# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import webapp2
from telegram import Bot

import dumpable
import secret_data
from util import common

bot = Bot(secret_data.bot_token)


class NightHandler(webapp2.RequestHandler):
    def get(self):
        dumpable.get_data()
        process_day()
        dumpable.dump_data()
        self.response.write("See console for output.")


def process_day():
    """Questo comando verrà fatto partire alle 02:00 di ogni giorno.
    Questo comando scorre tutta la lista di utenti controllando i viaggi effettuati in giornata
    e addebitandogli il prezzo impostato in common.trip_price. Se il viaggio è temporaneo, vengono
    anche rimossi.
    """
    today = datetime.datetime.today()
    day = common.day_to_string(today.weekday() - 1)

    if 1 <= today.weekday() <= 5 and today.date() not in common.no_trip_days:
        for direction in secret_data.groups:
            trips = secret_data.groups[direction][day]
            for driver in trips:
                if trips[driver]["Suspended"]:
                    trips[driver]["Suspended"] = False  # Rimuovo la sospensione del viaggio
                    bot.send_message(chat_id=str(driver),
                                     text="Il tuo viaggio di " + day.lower() + " "
                                          + common.direction_to_name(direction) + " è stato ripristinato.")

                    for mode in trips[driver]:
                        if mode == "Temporary" or mode == "Permanent":
                            for user in trips[driver][mode]:
                                bot.send_message(chat_id=str(user),
                                                 text="Il viaggio di " + secret_data.users[driver]["Name"]
                                                      + " per " + day.lower() + common.direction_to_name(direction)
                                                      + " è di nuovo operativo. La tua prenotazione " +
                                                      + common.localize_mode(mode) + " è di nuovo valida.")
                else:
                    for mode in trips[driver]:
                        if mode == "Temporary" or mode == "Permanent":
                            for user in trips[driver][mode]:
                                try:
                                    secret_data.users[user]["Debit"][driver] += common.trip_price
                                except KeyError:
                                    secret_data.users[user]["Debit"][driver] = common.trip_price

                                bot.send_message(chat_id=str(user),
                                                 text="Ti sono stati addebitati " + str(common.trip_price)
                                                      + " EUR da " + str(secret_data.users[driver]["Name"]) + ".")
                                bot.send_message(chat_id=str(driver),
                                                 text="Hai ora un credito di " + str(common.trip_price)
                                                      + " EUR da parte di " + str(
                                                     secret_data.users[user]["Name"]) + ".")
                        elif mode == "SuspendedUsers":
                            for user in trips[driver][mode]:
                                occupied_slots = len(trips["Permanent"]) + len(trips["Temporary"])
                                total_slots = secret_data.drivers[driver]["Slots"]

                                if occupied_slots > total_slots:
                                    bot.send_message(chat_id=str(user),
                                                     text="ATTENZIONE: Non è stato possibile ripristinare"
                                                          + " la tua prenotazione di " + day.lower() + " con "
                                                          + secret_data.users[driver]["Name"] + " "
                                                          + common.direction_to_name(
                                                         direction) + "; qualcun'altro ha occupato il tuo"
                                                          + " posto. Contatta l'autista per risolvere il problema.")
                                else:
                                    trips[driver]["Permanent"].append(user)
                                    trips[driver]["SuspendedUsers"].remove(user)

                                    bot.send_message(chat_id=str(user),
                                                     text="La prenotazione per " + day.lower() + " con "
                                                          + secret_data.users[driver]["Name"] + " "
                                                          + common.direction_to_name(
                                                         direction) + " è di nuovo operativa.")
                                    bot.send_message(chat_id=str(driver),
                                                     text="La prenotazione di "
                                                          + secret_data.users[user][
                                                              "Name"] + " per " + day.lower() + " "
                                                          + common.direction_to_name(
                                                         direction) + " è stata ripristinata.")
                trips[driver]["Temporary"] = []

                # Cancello l'eventuale ritrovo del giorno
                try:
                    del trips[driver]["Location"]
                except KeyError:
                    continue


class WeeklyReportHandler(webapp2.RequestHandler):
    def get(self):
        dumpable.get_data()
        weekly_report()
        dumpable.dump_data()
        self.response.write("See console for output.")


def weekly_report():
    """Questo comando viene fatto partire ogni sabato alle 12.00. Scorre tutta la lista di utenti e gli invia
    un messaggio con il riepilogo di soldi che devono dare. Se l'utente è anche un autista, riceverà anche
    un messaggio con i crediti.
    """
    for user in secret_data.users:
        # Invio dei debiti per tutti gli utenti
        debits = common.get_debits(user)
        if debits:
            string = "Riepilogo settimanale dei debiti:\n"
            for name, value in debits:
                string = string + "\n" + secret_data.users[name]["Name"] + " - " + str(value) + " EUR"
            bot.send_message(chat_id=user, text=string)

        # Invio dei crediti per ogni singolo autista
        if user in secret_data.drivers:
            credits = common.get_credits(user)
            if credits:
                string = "Riepilogo settimanale dei crediti:\n"
                for name, value in credits:
                    string = string + "\n" + secret_data.users[name]["Name"] + " - " + str(value) + " EUR"
                bot.send_message(chat_id=user, text=string)
