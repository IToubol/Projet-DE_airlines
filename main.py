import pandas as pd
import mysql.connector

from pymongo import MongoClient
from requests import get
from time import sleep
from datetime import datetime, timedelta

from constants import *
from last import lastlog
from valider import token


# lancement du programme


# Connexion à la bdd MongoDB
client = MongoClient(host = "localhost", port = 27017)
db = client.flights
routes = db.routes
yesterdayDataAPI = db.yesterday
todayDataAPI = db.today

# date présent
today = datetime.utcnow()
Y,M,D = today.year, today.month, today.day
now = Y*10*10*10*10 + M*10*10 + D

if lastlog != now:

    # enregistrement de la date de la dernière requête sur l'API de lufthansa.
    with open('last.py', 'w') as l:
        l.write(f"lastlog = {now}")


    # vidange des collections (MongoDB) yesterdayDataAPI et todayDataAPI
    yesterdayDataAPI.drop()
    todayDataAPI.drop()


    # Préprations à l'acquisition des nouvelles données sur les vols (grâce à l'API de lufthansa):

    # todayData = [] # données des vols d'aujourd'hui
    # yesterdayData = [] # données des vols d'hier

    missing = [] # listes des compagnie pour lesquelles la requête a échoué

    # Date de la veille
    yesterday = today - timedelta(1)
    yY, yM, yD = yesterday.year, yesterday.month, yesterday.day

    # Dates des deux jours couverts par les requêtes (syntaxe API)
    first = f"{yD:02}{MONTHS[yM-1]}{yY-2000}"
    second = f"{D:02}{MONTHS[M-1]}{Y-2000}"

    # fonction qui effectue la requête en fonction des compagnies et des dates.
    def lufthansa_request(comp, date):
        return get(f"""
                    {REQUEST_BASE}flight-schedules/flightschedules/passenger?
                    airlines={comp}
                    &startDate={date}
                    &endDate={date}
                    &daysOfOperation=1234567
                    &timeMode=UTC
                    """,
                   headers = token)


    # Acquisition des données (requête sur l'API)
    for company in ('LH', 'OS', 'LX', 'EN', 'WK'):

        # sleep(0.6)

        response = lufthansa_request(company, first)

        attempt = 1
        while attempt < 5 and not response.ok:
            sleep(1); attempt += 1
            response = lufthansa_request(company, first)

        # if response.ok: yesterdayData.append(response)
        if response.ok: yesterdayDataAPI.insert_one({"_id": company, "data": response.json()})
        else: missing.append(COMPANIE_DICT[company])
        
        # sleep(0.6)

        response = lufthansa_request(company, second)

        attempt = 1
        while attempt < 5 and not response.ok:
            sleep(1); attempt += 1
            response = lufthansa_request(company, second)

        # if response.ok: todayData.append(response)
        if response.ok: todayDataAPI.insert_one({"_id": company, "data": response.json()})
        else: missing.append(COMPANIE_DICT[company])



# Boucle infinie de mise à jour des donées

"""
Quelles infos voulons-nous présenter (en compément de l'affichage graphique)?
  Possibilités:
    - compagnie (nom)
    - lieu de départ (pays, ville, aeroport (noms, codes, localisation gps))
    - lieu d'arrivée (pays,ville, aeroport (noms, codes, localisation gps))
    - heure de départ (local, utc)
    - heure d'arrivée (local, utc)
    - distance totale du vol
    (- distance en ligne droite ? )
    - durée totale du vol
    - vitesse moyenne
    - trajet parcouru (en temps réel), en pourcentage ou valeur absolue
    - durée de vol (en temps réel), en pourcentage ou valeur absolue
"""

while True:

    to_print = []

    with mysql.connector.connect(**PARAMS) as db:
        with db.cursor() as c:

            # Acquisition des données temporelles
            today = datetime.utcnow()
            hr, mn = today.hour, today.minute
            reqTime = hr*60 + mn

            # tant = 0

            # for response in todayData:
            for response in todayDataAPI.find():

                # response = response.json()

                for flight in response:

                    deparTime = flight['legs'][0]['aircraftDepartureTimeUTC']
                    arrivTime = flight['legs'][0]['aircraftArrivalTimeUTC']
                    cpArrivTime = arrivTime

                    if deparTime <= reqTime:
            
                        if arrivTime <= deparTime:
                            
                            cpArrivTime += 1440
            
                        if cpArrivTime > reqTime:
                            
                            origCode = flight['legs'][0]['origin']
                            
                            try: c.execute(f"select pays, ville, nom, latitude, longitude, fuseauhoraire, decalageutc \
from aeroports join (select code, nom pays from pays) p on p.code = codepays join (select code, nom ville from villes) v \
on v.code = codeville where aeroports.code = '{origCode}';"); origData = c.fetchall()[0]
                            except: origData = None  #; tant += 1
                            
                            if origData:

                                destCode = flight['legs'][0]['destination']
                            
                                try:
                                    c.execute(f"select pays, ville, nom, latitude, longitude, fuseauhoraire, decalageutc \
from aeroports join (select code, nom pays from pays) p on p.code = codepays join (select code, nom ville from villes) v \
on v.code = codeville where aeroports.code = '{destCode}';"); destData = c.fetchall()[0]
                                except: destData = None

                                if destData:

                                    countD, cityD, airportD, latD, lonD, fusD, offsetD = origData

                                    countA, cityA, airportA, latA, lonA, fusA, offsetA = destData

                                    try:
                                        distance, route = routes.find_one({"_id": f"{origCode} {destCode}"},{"_id": 0, "distance": 1, "route": 1})
                                    except Exception as e:
                                        route = ((latD,lonD), (latA,lonA))
                                        distance = distanceCalcul(route)
                                        print("Echec requête Mongo routes:\n", e)

                                    # actualPos = positionGps((latD, lonD), (latA, lonA), deparTime, cpArrivTime)
                                    latitude, longitude, meanSpeed, travelled, totalTime, sinceTakeoff = dataCalcul()

                                    to_print.append([flight['flightNumber'], COMPANIE_DICT[flight['airline']],
                                    countD, cityD, airportD, fusD, offsetD, f"{deparTime//60:02}:{deparTime%60:02} (UTC)",
                                    countA, cityA, airportA, fusA, offsetA, f"{arrivTime//60:02}:{arrivTime%60:02} (UTC)", actualPos])

            
            # today = datetime.utcnow()
            # hr, mn = today.hour, today.minute
            # reqTime = hr*60 + mn

            for response in yesterdayDataAPI:

                response = response.json()

                for flight in response:

                    deparTime = flight['legs'][0]['aircraftDepartureTimeUTC']
                    arrivTime = flight['legs'][0]['aircraftArrivalTimeUTC']
                    cpArrivTime = arrivTime

                    if reqTime < arrivTime < deparTime:
                        
                        cpArrivTime += 1440
                            
                        origCode = flight['legs'][0]['origin']
                                
                        try: c.execute(f"select pays, ville, nom, latitude, longitude, fuseauhoraire, decalageutc \
from aeroports join (select code, nom pays from pays) p on p.code = codepays join (select code, nom ville from villes) v \
on v.code = codeville where aeroports.code = '{origCode}';"); origData = c.fetchall()[0]
                        except: origData = None  #; tant += 1
                        
                        if origData:
                        
                            destCode = flight['legs'][0]['destination']
                        
                            try: c.execute(f"select pays, ville, nom, latitude, longitude, fuseauhoraire, decalageutc \
from aeroports join (select code, nom pays from pays) p on p.code = codepays join (select code, nom ville from villes) v \
on v.code = codeville where aeroports.code = '{destCode}';"); destData = c.fetchall()[0]
                            except: destData = None; print('yesterday destData:',destData)

                            if destData:

                                countD, cityD, airportD, latD, lonD, fusD, offsetD = origData
                                
                                countA, cityA, airportA, latA, lonA, fusA, offsetA = destData

                                actualPos = dataCalcul((latD, lonD), (latA, lonA), deparTime, cpArrivTime)

                                to_print.append([flight['flightNumber'], COMPANIE_DICT[flight['airline']],
                                countD, cityD, airportD, fusD, offsetD, f"{deparTime//60:02}:{deparTime%60:02} (UTC)",
                                countA, cityA, airportA, fusA, offsetA, f"{arrivTime//60:02}:{arrivTime%60:02} (UTC)", actualPos])



    df = pd.DataFrame(to_print, columns = ["Numéro de vol", "Compagnie",
                                           "PaysOrigine", "VilleOrigine", "AeroportOrigine", "FuseauHoraire", "DecalageUTC", "Heure de départ",
                                           "PaysDestination", "VilleDestination", "AeroportDestination", "FuseauHoraire", "DecalageUTC", "Heure d'arrivée",
                                           "Position Actuelle (lat/lon)"]) #.set_index('Numéro de vol')

    if missing: print(f"résultats manquants pour la/les compagnie/s {[COMPANIE_DICT[company] for company in missing]}.")

    # print(f"\n{tant} trajets en cours obtenus en réponses ne sont pas ceux d'avions?!\n")

    print(df[["Numéro de vol","Heure de départ","VilleOrigine","Heure d'arrivée","VilleDestination"]])

    sleep(20)