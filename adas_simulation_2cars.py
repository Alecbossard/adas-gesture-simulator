import cv2
import numpy as np

# ==============================
# Fonctions utilitaires
# ==============================

def calculer_mode_adas(touche):
    """
    Map clavier -> mode ADAS.
    0 -> MANUEL
    1 -> ACC
    2 -> LKA
    3 -> EMERGENCY
    """
    if touche == ord('1'):
        return "ACC"
    elif touche == ord('2'):
        return "LKA"
    elif touche == ord('3'):
        return "EMERGENCY"
    elif touche == ord('0'):
        return "MANUEL"
    return None


def calculer_zone_adas(largeur, hauteur):
    """
    Calcule les paramètres géométriques de la zone ADAS.
    Retourne :
      x1, x2, y1, y2, largeur_zone, hauteur_zone,
      centres_voies (3 valeurs),
      x_sep1, x_sep2 (lignes blanches entre voies)
    """
    x1 = int(largeur * 0.25)
    x2 = int(largeur * 0.75)
    y1 = int(hauteur * 0.05)
    y2 = int(hauteur * 0.95)

    largeur_zone = x2 - x1
    hauteur_zone = y2 - y1
    largeur_voie = largeur_zone / 3.0

    centres_voies = [
        int(x1 + largeur_voie * 0.5),   # voie 1 (gauche)
        int(x1 + largeur_voie * 1.5),   # voie 2 (centre)
        int(x1 + largeur_voie * 2.5)    # voie 3 (droite)
    ]

    x_sep1 = int(x1 + largeur_voie)      # ligne blanche entre voie 1 et 2
    x_sep2 = int(x1 + 2 * largeur_voie)  # ligne blanche entre voie 2 et 3

    return x1, x2, y1, y2, largeur_zone, hauteur_zone, centres_voies, x_sep1, x_sep2


def dessiner_scene(
    image,
    mode_adas,
    position_relative_ego,
    position_relative_cible,
    distance_min_atteinte,
    x_centre_ego,
    indice_voie_ego,
    indice_voie_cible,
    v_ego_base,
    v_cible,
    zone_params
):
    """
    Dessine la scène :
    - route à 3 voies
    - voiture ego
    - véhicule cible
    - HUD (mode, voie, messages, vitesses)
    """

    (x1, x2, y1, y2, largeur_zone,
     hauteur_zone, centres_voies, x_sep1, x_sep2) = zone_params

    hauteur, largeur, _ = image.shape

    # Fond
    image[:] = (30, 30, 30)

    # Route
    cv2.rectangle(image, (x1, y1), (x2, y2), (50, 50, 50), -1)

    # Lignes de séparation des voies
    cv2.line(image, (x_sep1, y1), (x_sep1, y2), (255, 255, 255), 2)
    cv2.line(image, (x_sep2, y1), (x_sep2, y2), (255, 255, 255), 2)

    # Borne les positions relatives
    position_relative_ego = max(0.0, min(1.0, position_relative_ego))
    position_relative_cible = max(0.0, min(1.0, position_relative_cible))

    marge = 40  # marge verticale

    # Paramètres des véhicules
    largeur_voiture = int(largeur_zone / 8.0)
    hauteur_voiture = int(hauteur_zone / 10.0)

    # ------------------------------
    # Véhicule cible (qui bouge)
    # ------------------------------
    y_bas_cible = int(y2 - 10 - position_relative_cible * (hauteur_zone - marge))
    y_haut_cible = y_bas_cible - hauteur_voiture

    x_centre_cible = centres_voies[indice_voie_cible]
    x_cible_g = x_centre_cible - largeur_voiture // 2
    x_cible_d = x_centre_cible + largeur_voiture // 2

    couleur_cible = (255, 0, 0)  # bleu
    cv2.rectangle(
        image,
        (x_cible_g, y_haut_cible),
        (x_cible_d, y_bas_cible),
        couleur_cible,
        -1
    )

    # ------------------------------
    # Véhicule ego
    # ------------------------------
    y_bas_ego = int(y2 - 10 - position_relative_ego * (hauteur_zone - marge))
    y_haut_ego = y_bas_ego - hauteur_voiture

    x_ego_g = int(x_centre_ego - largeur_voiture // 2)
    x_ego_d = int(x_centre_ego + largeur_voiture // 2)

    if mode_adas == "MANUEL":
        couleur_ego = (180, 180, 180)   # gris
    elif mode_adas == "ACC":
        couleur_ego = (0, 255, 0)       # vert
    elif mode_adas == "LKA":
        couleur_ego = (0, 255, 255)     # jaune
    elif mode_adas == "EMERGENCY":
        couleur_ego = (0, 0, 255)       # rouge
    else:
        couleur_ego = (255, 255, 255)

    cv2.rectangle(
        image,
        (x_ego_g, y_haut_ego),
        (x_ego_d, y_bas_ego),
        couleur_ego,
        -1
    )
    cv2.rectangle(
        image,
        (x_ego_g, y_haut_ego),
        (x_ego_d, y_bas_ego),
        (0, 0, 0),
        2
    )

    # Texte EMERGENCY
    if mode_adas == "EMERGENCY":
        cv2.putText(
            image,
            "BRAKE!",
            (x1 + 20, y1 + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            3,
            cv2.LINE_AA
        )

    # Distance mini atteinte
    if distance_min_atteinte:
        cv2.putText(
            image,
            "Distance mini atteinte",
            (x1 + 20, y2 - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 165, 255),
            2,
            cv2.LINE_AA
        )

    # HUD
    cv2.putText(
        image,
        f"Mode ADAS : {mode_adas}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )
    cv2.putText(
        image,
        f"Voie ego : {indice_voie_ego + 1}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # Affichage vitesses
    cv2.putText(
        image,
        f"v_ego: {abs(v_ego_base):.4f}  v_cible: {abs(v_cible):.4f}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (200, 200, 200),
        2,
        cv2.LINE_AA
    )

    # Légende
    lignes = [
        "Touches :",
        "0 -> MANUEL, 1 -> ACC, 2 -> LKA, 3 -> EMERGENCY",
        "Q / Fleche gauche  -> tourner a gauche",
        "D / Fleche droite -> tourner a droite",
        "Z -> accelerer ego, S -> ralentir ego",
        "Deux voitures avancent (ego + cible)",
        "Blocage lateral si vehicule a cote",
        "ECHAP -> quitter",
    ]
    x0, y0 = 20, hauteur - 180
    for i, texte in enumerate(lignes):
        cv2.putText(
            image,
            texte,
            (x0, y0 + i * 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )


# ==============================
# Programme principal
# ==============================

def main():
    # Fenetre
    largeur = 900
    hauteur = 600
    image = np.zeros((hauteur, largeur, 3), dtype=np.uint8)

    # Zone ADAS
    zone_params = calculer_zone_adas(largeur, hauteur)
    (x1, x2, y1, y2, largeur_zone,
     hauteur_zone, centres_voies, x_sep1, x_sep2) = zone_params

    # Etat initial
    mode_adas = "MANUEL"

    # 0 = haut, 1 = bas
    position_relative_ego = 0.8
    position_relative_cible = 0.3  # devant ego au début

    # vitesses (négatives = vers le haut)
    v_ego_base = -0.004   # réglable par z/s
    v_cible = -0.003      # fixe

    marge_distance_relative = 0.15
    seuil_blocage_lateral = 0.20

    indice_voie_cible = 1     # centre
    indice_voie_ego = 1       # centre
    indice_voie_ego_cible = indice_voie_ego

    x_centre_ego = float(centres_voies[indice_voie_ego])

    # Changement de voie "classique"
    changement_voie_en_cours = False

    # Dérive latérale (LKA ou blocage latéral)
    lateral_phase = "idle"   # "idle" / "out" / "back"
    lateral_direction = 0    # -1 gauche, +1 droite
    lateral_boundary_x = 0.0

    vitesse_laterale = 10.0  # px/frame

    while True:
        # ------------------------------
        # Màj longitudinales des deux voitures
        # ------------------------------
        # Voiture cible : avance toujours à v_cible
        position_relative_cible += v_cible
        if position_relative_cible < 0.0:
            # On la remet en bas
            position_relative_cible = 1.0

        # Ego : vitesse dépend du mode (ACC / EMERGENCY) à partir de v_ego_base
        distance_min_atteinte = False
        v_ego = v_ego_base

        if mode_adas == "EMERGENCY":
            v_ego = 0.0

        elif mode_adas == "ACC":
            if indice_voie_ego == indice_voie_cible:
                # Ego derrière la cible ?
                if position_relative_ego > position_relative_cible:
                    distance = position_relative_ego - position_relative_cible

                    if distance <= marge_distance_relative:
                        # Trop proche : on se cale à la vitesse de la cible
                        distance_min_atteinte = True
                        v_ego = v_cible
                    else:
                        # On garde la vitesse demandée par le conducteur
                        v_ego = v_ego_base
                else:
                    # Ego déjà devant -> on laisse la vitesse du conducteur
                    v_ego = v_ego_base
            else:
                # Pas dans la même voie -> ACC n'agit pas
                v_ego = v_ego_base

        else:
            v_ego = v_ego_base

        position_relative_ego += v_ego
        if position_relative_ego < 0.0:
            position_relative_ego = 1.0

        # ------------------------------
        # Dynamique latérale (dérive + retour / changement de voie)
        # ------------------------------
        # 1) Phase "out": dérive vers la ligne
        if lateral_phase == "out":
            if lateral_direction == -1:
                x_centre_ego -= vitesse_laterale
                if x_centre_ego <= lateral_boundary_x:
                    x_centre_ego = lateral_boundary_x
                    lateral_phase = "back"
            elif lateral_direction == 1:
                x_centre_ego += vitesse_laterale
                if x_centre_ego >= lateral_boundary_x:
                    x_centre_ego = lateral_boundary_x
                    lateral_phase = "back"

        # 2) Phase "back": retour au centre de la même voie
        elif lateral_phase == "back":
            x_centre_voie = float(centres_voies[indice_voie_ego])
            diff = x_centre_voie - x_centre_ego
            if abs(diff) <= vitesse_laterale:
                x_centre_ego = x_centre_voie
                lateral_phase = "idle"
            else:
                x_centre_ego += vitesse_laterale * (1.0 if diff > 0 else -1.0)

        # 3) Changement de voie "classique"
        if lateral_phase == "idle" and mode_adas != "LKA":
            if changement_voie_en_cours:
                cible_x = float(centres_voies[indice_voie_ego_cible])
                diff = cible_x - x_centre_ego
                if abs(diff) <= vitesse_laterale:
                    x_centre_ego = cible_x
                    indice_voie_ego = indice_voie_ego_cible
                    changement_voie_en_cours = False
                else:
                    x_centre_ego += vitesse_laterale * (1.0 if diff > 0 else -1.0)

        # ------------------------------
        # Dessin
        # ------------------------------
        dessiner_scene(
            image,
            mode_adas,
            position_relative_ego,
            position_relative_cible,
            distance_min_atteinte,
            x_centre_ego,
            indice_voie_ego,
            indice_voie_cible,
            v_ego_base,
            v_cible,
            zone_params
        )

        cv2.imshow("Simulation ADAS (2 voitures)", image)

        # ------------------------------
        # Clavier
        # ------------------------------
        key = cv2.waitKey(20) & 0xFF

        if key != 255:
            # Quitter
            if key == 27:
                break

            # Changer de mode ADAS
            nouveau_mode = calculer_mode_adas(key)
            if nouveau_mode is not None and nouveau_mode != mode_adas:
                ancien_mode = mode_adas
                mode_adas = nouveau_mode
                print(f"➡ Nouveau mode ADAS : {mode_adas}")

                if mode_adas == "LKA":
                    changement_voie_en_cours = False
                    indice_voie_ego_cible = indice_voie_ego
                    x_centre_ego = float(centres_voies[indice_voie_ego])
                    lateral_phase = "idle"

            # Ajuster la vitesse de l'ego (z/s)
            if key == ord('z'):
                v_ego_base -= 0.001
                v_ego_base = max(v_ego_base, -0.01)
                print(f"v_ego_base (accel) = {v_ego_base:.4f}")
            if key == ord('s'):
                v_ego_base += 0.001
                v_ego_base = min(v_ego_base, -0.0005)
                print(f"v_ego_base (ralenti) = {v_ego_base:.4f}")

            # Fonction utilitaire : voie bloquée latéralement ?
            def voie_bloquee(target_lane):
                return (
                    target_lane == indice_voie_cible and
                    abs(position_relative_ego - position_relative_cible) <= seuil_blocage_lateral
                )

            # Gauche : q ou flèche gauche (81)
            if key == ord('q') or key == 81:
                if mode_adas == "LKA":
                    # dérive vers la ligne puis retour
                    if lateral_phase == "idle":
                        if indice_voie_ego == 0:
                            boundary_gauche = x1
                        elif indice_voie_ego == 1:
                            boundary_gauche = x_sep1
                        else:
                            boundary_gauche = x_sep2
                        if x_centre_ego > boundary_gauche:
                            lateral_direction = -1
                            lateral_boundary_x = boundary_gauche
                            lateral_phase = "out"
                else:
                    if lateral_phase == "idle" and not changement_voie_en_cours:
                        target_lane = indice_voie_ego - 1
                        if target_lane >= 0:
                            if voie_bloquee(target_lane):
                                # sécurité latérale -> dérive + retour
                                if indice_voie_ego == 0:
                                    boundary_gauche = x1
                                elif indice_voie_ego == 1:
                                    boundary_gauche = x_sep1
                                else:
                                    boundary_gauche = x_sep2
                                if x_centre_ego > boundary_gauche:
                                    lateral_direction = -1
                                    lateral_boundary_x = boundary_gauche
                                    lateral_phase = "out"
                            else:
                                indice_voie_ego_cible = target_lane
                                changement_voie_en_cours = True
                                print(f"➡ Changement de voie vers la gauche (voie {indice_voie_ego_cible + 1})")

            # Droite : d ou flèche droite (83)
            if key == ord('d') or key == 83:
                if mode_adas == "LKA":
                    if lateral_phase == "idle":
                        if indice_voie_ego == 0:
                            boundary_droite = x_sep1
                        elif indice_voie_ego == 1:
                            boundary_droite = x_sep2
                        else:
                            boundary_droite = x2
                        if x_centre_ego < boundary_droite:
                            lateral_direction = 1
                            lateral_boundary_x = boundary_droite
                            lateral_phase = "out"
                else:
                    if lateral_phase == "idle" and not changement_voie_en_cours:
                        target_lane = indice_voie_ego + 1
                        if target_lane <= 2:
                            if voie_bloquee(target_lane):
                                if indice_voie_ego == 0:
                                    boundary_droite = x_sep1
                                elif indice_voie_ego == 1:
                                    boundary_droite = x_sep2
                                else:
                                    boundary_droite = x2
                                if x_centre_ego < boundary_droite:
                                    lateral_direction = 1
                                    lateral_boundary_x = boundary_droite
                                    lateral_phase = "out"
                            else:
                                indice_voie_ego_cible = target_lane
                                changement_voie_en_cours = True
                                print(f"➡ Changement de voie vers la droite (voie {indice_voie_ego_cible + 1})")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
