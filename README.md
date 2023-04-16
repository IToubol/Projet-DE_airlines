# Projet fil rouge - DE - airlines

Application d'affichage d'avions en vol en temps réel.

Il s'agit de mettre en place une application qui affiche sur une carte du monde
la position (au sol) en temps réel des avions en vol du groupe Lufthansa,
un peu à la manière du site flightradar24.com .
Nous disposons, pour ce faire, de l'API de Lufthansa (https://developer.lufthansa.com/docs)
et d'une API (https://flightplandatabase.com/dev/api) qui fournit des plans de vols.

Nous avons déjà plusieurs fichiers contenant une quantité intéressante de données
(obtenues à l'aide de nombeuses requêtes répétées sur les API citées)
qui nous permettent de remplir des bdd locales (comme Mysql et MongoDB)
pour fournir les infos nécessaires à notre application.

- Fichier csv contenant des infos sur les aérorports (identifiés par leur code IATA):
le nom, les codes IATA des ville et pays où ils se situent,
le décalage horaire local par rapport à l'heure UTC et la position (latitude & longitude)
- Fichier csv contenant des infos similaire sur les villes (identifiées par leur code IATA)
- Fichier csv contenant la correspondance entre le code IATA des pays et leurs noms.
- Fichier json contenant des infos pour environ 2500 paires Origine-Destination, comme:
la distance, le plan de vol (liste de points géographiques appartenant à la trajectoire de l'avion),
l'ID du plan de vol et le nombres de points.

[Pour le moment ces fichiers ne sont pas complets...]
