from math import sqrt
# from time import perf_counter as pc

# Paramètres ce connexion à la BDD Mysql
params = {'user':'root', 'host':'localhost', 'password':'$Tefilin&41!', 'database':'iata'}

# ditcionnaire des code des compagnies
cpnDic = {'LH':'Lufthansa', 'OS':'Austrian Airlines', 'LX':'Swiss', 'EN':'Air Dolomiti', 'WK':'Edelweiss Air'}

# Base de l'url des requêtes
reqBase = "https://api.lufthansa.com/v1/"


"""
fonction qui calcule (approximativement) les coordonnees (au sol) d'un avion en cours de vol
en fonction de ses points de depart et d'arivée (coordonnées gps)
et de ses heures de depart et d'arrivée (en nb de minutes depuis minuit UTC).
Le résultat de cette fonction n'est valable que pour les cas où
moins de 24 heures ne sont passées depuis le départ
et où l'arrivée n'a pas encore eu lieu.
"""


def dataCalcul(distance, route, deparTime, arrivTime, reqTime):

    totalTime = arrivTime - deparTime

    sinceTakeoff = reqTime - deparTime

    meanSpeed = distance / totalTime

    travelled = sinceTakeoff * meanSpeed

    index, cumul = 0, 0

    first, second = route[index],route[index+1]

    while cumul < travelled:
        index += 1
        oldCumul = cumul
        first, second = route[index],route[index+1]
        cumul += 111.319 * sqrt((second[0]-first[0])**2 + (second[1]-first[1])**2)
    
    percent = (travelled - oldCumul) / (cumul - oldCumul)

    # latitude = first[0] + (second[0]-first[0])*percent
    # longitude = first[1] + (second[1]-first[1])*percent

    return first[0] + (second[0]-first[0])*percent, first[1] + (second[1]-first[1])*percent, meanSpeed, travelled, totalTime, sinceTakeoff


# nodes = ((0,0), (3,4), (6,8), (9,12))
# debut = pc()

def distanceCalcul(nodes):
    
    return 111.319 * sum(sqrt((nodes[i+1][0]-nodes[i][0])**2 + (nodes[i+1][1]-nodes[i][1])**2) for i in range(len(nodes)-1))

# fin = pc()
# print(distanceCalcul(nodes))
# print(fin - debut)