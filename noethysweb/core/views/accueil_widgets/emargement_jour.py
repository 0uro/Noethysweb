# -*- coding: utf-8 -*-

import datetime

from core.models import Activite, Consommation, Ouverture
from core.views import accueil_widget


class Widget(accueil_widget.Widget):
    code = "emargement_jour"
    label = "Émargement du jour (liste)"

    def init_context_data(self):
        date_jour = datetime.date.today()
        structures = self.request.user.structures.all()

        ids_activites = list(
            Ouverture.objects.filter(
                date=date_jour,
                activite__structure__in=structures,
            ).values_list("activite_id", flat=True).distinct()
        )

        activites = list(
            Activite.objects.filter(pk__in=ids_activites)
            .order_by("nom")
        )

        consommations = (
            Consommation.objects
            .filter(date=date_jour, activite_id__in=ids_activites)
            .select_related("individu", "activite")
            .order_by("individu__nom", "individu__prenom", "activite__nom")
        )

        priorite = {
            "present": 50,
            "absentj": 40,
            "absenti": 40,
            "reservation": 30,
            "attente": 20,
            "demande": 10,
            "refus": 5,
        }

        individus = {}
        for conso in consommations:
            if not conso.individu_id or not conso.activite_id:
                continue

            ligne = individus.setdefault(conso.individu_id, {
                "individu": conso.individu,
                "etats": {},
            })

            ancien = ligne["etats"].get(conso.activite_id)
            if not ancien or priorite.get(conso.etat, 0) > priorite.get(ancien, 0):
                ligne["etats"][conso.activite_id] = conso.etat

        lignes = sorted(
            individus.values(),
            key=lambda item: (
                (item["individu"].nom or "").lower(),
                (item["individu"].prenom or "").lower(),
            ),
        )

        self.context["emargement_widget_date"] = date_jour
        self.context["emargement_widget_activites"] = activites
        self.context["emargement_widget_lignes"] = lignes
