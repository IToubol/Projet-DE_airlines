from json import dumps
from requests import get
from prox import proxies
from math import sqrt

def distance(latOrig, lonOrig, latDest, lonDest):
  return 111.319 * sqrt( (latDest-latOrig)**2 + (lonDest-lonOrig)**2 )

proxies = tuple(proxies)

pro,num = 0,0

with open("iata_icao.txt","r") as source, open("docMongo.txt","a") as cible:
  for line in source.readlines():
    print(num, end = ": ")
    num += 1
    if not num % 60: pro += 1
    prox = {'http': proxies[pro], 'https': proxies[pro]}
    dep,arr,ndep,narr = line.strip('\n').split()
    resp = get(f"https://api.flightplandatabase.com/search/plans?fromICAO={ndep}&toICAO={narr}&limit=1", proxies = prox)
    if resp.ok:
      resp = resp.json()
      if resp:
        plan = resp[0]
        res = get(f"https://api.flightplandatabase.com/plan/{plan['id']}?Units=AVIATION").json()
        nodes = res['route']['nodes']
        route = [(round(node['lat'],4), round(node['lon'],4)) for node in nodes]
        dist = 0
        for i in range(len(route)-1):
          prec, suiv = route[i], route[i+1]
          dist += distance(prec[0],prec[1],suiv[0],suiv[1])
        try:
          dic = {"_id":f"{dep} {arr}", "icao": f"{ndep} {narr}", "distance":round(dist, 4), "nbWaypoints": plan['waypoints'],
              "planId":plan['id'], "route":route}
          doc = dumps(dic)
          print(doc)
          cible.write(doc+'\n')
        except: print("Absent: ", resp)
      else: print("vide")
    else: print(resp.text)