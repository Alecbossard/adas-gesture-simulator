import cv2
import mediapipe as mp

# ==============================
# Fonctions utilitaires
# ==============================

def calculer_mode_adas(chiffre_detecte):
    """
    Convertit le nombre de doigts détectés en mode ADAS.
    0 ou None -> MANUEL
    1 -> ACC
    2 -> LKA
    3 -> EMERGENCY
    >=4 -> MANUEL
    """
    if chiffre_detecte == 1:
        return "ACC"
    elif chiffre_detecte == 2:
        return "LKA"
    elif chiffre_detecte == 3:
        return "EMERGENCY"
    else:
        return "MANUEL"


def calculer_zone_adas(image):
    """
    Calcule les paramètres géométriques de la zone ADAS.
    Retourne :
      x1, x2, y1, y2, largeur_zone, hauteur_zone,
      centres_voies (3 valeurs),
      x_sep1, x_sep2 (lignes blanches entre voies)
    """
    hauteur, largeur, _ = image.shape
    x1 = int(largeur * 0.55)
    x2 = int(largeur * 0.95)
    y1 = int(hauteur * 0.1)
    y2 = int(hauteur * 0.9)

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


def dessiner_tableau_adas(
    image,
    mode_adas,
    position_relative_ego,
    position_relative_cible,
    distance_min_atteinte,
    x_centre_ego,
    indice_voie_cible,
    zone_params
):
    """
    Dessine le mini tableau de bord ADAS :
    - 3 voies
    - véhicule ego (x_centre_ego)
    - véhicule cible (dans la voie indice_voie_cible)
    - messages ACC / EMERGENCY
    """

    (x1, x2, y1, y2, largeur_zone,
     hauteur_zone, centres_voies, x_sep1, x_sep2) = zone_params

    # Cadre de la zone
    cv2.rectangle(image, (x1, y1), (x2, y2), (200, 200, 200), 2)

    # Lignes de séparation des voies (lignes blanches)
    cv2.line(image, (x_sep1, y1), (x_sep1, y2), (255, 255, 255), 2)
    cv2.line(image, (x_sep2, y1), (x_sep2, y2), (255, 255, 255), 2)

    # Borne les positions relatives
    position_relative_ego = max(0.0, min(1.0, position_relative_ego))
    position_relative_cible = max(0.0, min(1.0, position_relative_cible))

    marge = 40  # marge verticale pour ne pas coller aux bords

    # Paramètres des véhicules
    largeur_voiture = int(largeur_zone / 8.0)
    hauteur_voiture = int(hauteur_zone / 10.0)

    # ------------------------------
    # Véhicule cible (fixe)
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
    # Véhicule ego (toi)
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

    # Contour noir pour l'ego
    cv2.rectangle(
        image,
        (x_ego_g, y_haut_ego),
        (x_ego_d, y_bas_ego),
        (0, 0, 0),
        2
    )

    # Texte spécifique en mode EMERGENCY
    if mode_adas == "EMERGENCY":
        cv2.putText(
            image,
            "BRAKE!",
            (x1 + 10, y1 + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            3,
            cv2.LINE_AA
        )

    # Distance mini atteinte (ACC + meme voie)
    if distance_min_atteinte:
        cv2.putText(
            image,
            "Distance mini atteinte",
            (x1 + 10, y2 - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 165, 255),  # orange
            2,
            cv2.LINE_AA
        )


def dessiner_legende(image):
    """
    Affiche une petite légende des gestes et touches.
    """
    lignes = [
        "Gestes doigts :",
        "1 -> ACC, 2 -> LKA, 3 -> EMERGENCY",
        "0 / main retiree -> MANUEL",
        "",
        "Touches clavier :",
        "Q / Fleche gauche  -> voie gauche (si libre)",
        "D / Fleche droite -> voie droite (si libre)",
        "Si vehicule a cote -> derive puis retour",
        "ECHAP -> quitter",
    ]
    x0, y0 = 30, 140
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
# Initialisation MediaPipe
# ==============================

mp_mains = mp.solutions.hands
mp_dessin = mp.solutions.drawing_utils

detector_mains = mp_mains.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ==============================
# Ouverture de la webcam
# ==============================

cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
if not cap.isOpened():
    print("❌ Impossible d’ouvrir la webcam")
    exit()

# Etat initial
mode_adas = "MANUEL"

position_relative_ego = 0.8
vitesse_ego = -0.003  # vers le haut

position_relative_cible = 0.4
indice_voie_cible = 1  # centre

marge_distance_relative = 0.15

# seuil pour considérer que la voiture cible est "à côté" (longitudinalement)
seuil_blocage_lateral = 0.20

indice_voie_ego = 1      # 0=gauche, 1=centre, 2=droite
indice_voie_ego_cible = indice_voie_ego

x_centre_ego = None      # sera initialisé plus tard

# Changement de voie "classique" (hors LKA)
changement_voie_en_cours = False

# LKA + blocage latéral : dérive puis retour
lateral_phase = "idle"   # "idle" / "out" / "back"
lateral_direction = 0    # -1 gauche, +1 droite
lateral_boundary_x = 0.0
vitesse_laterale = 10.0  # vitesse latérale pour animations

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Impossible de lire une frame")
        break

    # Effet miroir
    frame = cv2.flip(frame, 1)
    image = frame.copy()

    # Paramètres de la zone ADAS
    zone_params = calculer_zone_adas(image)
    (x1, x2, y1, y2, largeur_zone,
     hauteur_zone, centres_voies, x_sep1, x_sep2) = zone_params

    # Initialisation du centre ego
    if x_centre_ego is None:
        x_centre_ego = float(centres_voies[indice_voie_ego])

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    resultats = detector_mains.process(image_rgb)

    chiffre_detecte = None

    # ==============================
    # Détection des doigts (modes ADAS)
    # ==============================
    if resultats.multi_hand_landmarks:
        for id_main, main_landmarks in enumerate(resultats.multi_hand_landmarks):

            mp_dessin.draw_landmarks(
                image,
                main_landmarks,
                mp_mains.HAND_CONNECTIONS
            )

            main_label = None
            if resultats.multi_handedness:
                main_label = resultats.multi_handedness[id_main].classification[0].label  # 'Left' ou 'Right'

            hauteur, largeur, _ = image.shape
            points = []
            for lm in main_landmarks.landmark:
                x = int(lm.x * largeur)
                y = int(lm.y * hauteur)
                points.append((x, y))

            doigts_leves = 0

            # Pouce
            if main_label is not None:
                if main_label == "Right":
                    if points[4][0] < points[3][0]:
                        doigts_leves += 1
                else:  # Left
                    if points[4][0] > points[3][0]:
                        doigts_leves += 1

            # Autres doigts
            doigts_tips = [8, 12, 16, 20]
            doigts_pip = [6, 10, 14, 18]

            for tip, pip in zip(doigts_tips, doigts_pip):
                if points[tip][1] < points[pip][1]:
                    doigts_leves += 1

            chiffre_detecte = doigts_leves

    # ==============================
    # Mode ADAS (MANUEL / ACC / LKA / EMERGENCY)
    # ==============================
    if chiffre_detecte is None or chiffre_detecte in [0, 1, 2, 3]:
        nouveau_mode = calculer_mode_adas(chiffre_detecte)
        if nouveau_mode != mode_adas:
            ancien_mode = mode_adas
            mode_adas = nouveau_mode
            print(f"➡ Nouveau mode ADAS : {mode_adas} (chiffre detecte = {chiffre_detecte})")

            # Si on entre en LKA, on annule un éventuel changement de voie
            if mode_adas == "LKA":
                changement_voie_en_cours = False
                indice_voie_ego_cible = indice_voie_ego
                x_centre_ego = float(centres_voies[indice_voie_ego])
                lateral_phase = "idle"

    # ==============================
    # Dynamique longitudinale (ACC / EMERGENCY)
    # ==============================
    distance_min_atteinte = False
    vitesse_courante = vitesse_ego

    if mode_adas == "EMERGENCY":
        vitesse_courante = 0.0

    elif mode_adas == "ACC":
        if indice_voie_ego == indice_voie_cible:
            # Ego derrière la cible ?
            if position_relative_ego > position_relative_cible:
                if position_relative_ego <= position_relative_cible + marge_distance_relative:
                    distance_min_atteinte = True
                    position_relative_ego = position_relative_cible + marge_distance_relative
                    vitesse_courante = 0.0
                else:
                    vitesse_courante = vitesse_ego
            else:
                vitesse_courante = vitesse_ego
        else:
            vitesse_courante = vitesse_ego

    else:
        vitesse_courante = vitesse_ego

    position_relative_ego += vitesse_courante
    if position_relative_ego < 0.0:
        position_relative_ego = 0.8

    # ==============================
    # Dynamique latérale (animation)
    # ==============================

    # 1) Phase "out": dérive vers une ligne blanche
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

    # 3) Changement de voie "classique" (si pas de dérive LKA / blocage en cours)
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

    # ==============================
    # Affichages texte
    # ==============================
    if chiffre_detecte is not None:
        texte_chiffre = f"Chiffre detecte : {chiffre_detecte}"
    else:
        texte_chiffre = "Chiffre detecte : -"

    cv2.putText(
        image,
        texte_chiffre,
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        image,
        f"Mode ADAS : {mode_adas}",
        (30, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 0),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        image,
        f"Voie ego : {indice_voie_ego + 1}",
        (30, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    dessiner_legende(image)

    # ==============================
    # Dessin du tableau de bord ADAS
    # ==============================
    dessiner_tableau_adas(
        image,
        mode_adas,
        position_relative_ego,
        position_relative_cible,
        distance_min_atteinte,
        x_centre_ego,
        indice_voie_cible,
        zone_params
    )

    # ==============================
    # Affichage + clavier
    # ==============================
    cv2.imshow("Mini simulation ADAS controlee par gestes", image)

    key = cv2.waitKey(1) & 0xFF

    # ECHAP pour quitter
    if key == 27:
        break

    # ------------------------------
    # Gestion des touches gauche/droite
    # ------------------------------
    # Fonction pour savoir si la voie cible est bloquée par la voiture
    def voie_bloquee(target_lane):
        return (
            target_lane == indice_voie_cible and
            abs(position_relative_ego - position_relative_cible) <= seuil_blocage_lateral
        )

    # Gauche : 'q' ou flèche gauche (code 81)
    if key == ord('q') or key == 81:
        if mode_adas == "LKA":
            # En LKA : dérive vers la ligne gauche puis retour
            if lateral_phase == "idle":
                if indice_voie_ego == 0:
                    boundary_gauche = x1
                elif indice_voie_ego == 1:
                    boundary_gauche = x_sep1
                else:  # voie 3
                    boundary_gauche = x_sep2
                if x_centre_ego > boundary_gauche:
                    lateral_direction = -1
                    lateral_boundary_x = boundary_gauche
                    lateral_phase = "out"
        else:
            # Hors LKA : tentative de changement de voie vers la gauche
            if lateral_phase == "idle" and not changement_voie_en_cours:
                target_lane = indice_voie_ego - 1
                if target_lane >= 0:
                    if voie_bloquee(target_lane):
                        # Bloqué -> dérive jusqu'à la ligne puis retour
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
                        # Changement de voie normal
                        indice_voie_ego_cible = target_lane
                        changement_voie_en_cours = True
                        print(f"➡ Changement de voie vers la gauche (voie {indice_voie_ego_cible + 1})")

    # Droite : 'd' ou flèche droite (code 83)
    if key == ord('d') or key == 83:
        if mode_adas == "LKA":
            # En LKA : dérive vers la ligne droite puis retour
            if lateral_phase == "idle":
                if indice_voie_ego == 0:
                    boundary_droite = x_sep1
                elif indice_voie_ego == 1:
                    boundary_droite = x_sep2
                else:  # voie 3
                    boundary_droite = x2
                if x_centre_ego < boundary_droite:
                    lateral_direction = 1
                    lateral_boundary_x = boundary_droite
                    lateral_phase = "out"
        else:
            # Hors LKA : tentative de changement de voie vers la droite
            if lateral_phase == "idle" and not changement_voie_en_cours:
                target_lane = indice_voie_ego + 1
                if target_lane <= 2:
                    if voie_bloquee(target_lane):
                        # Bloqué -> dérive jusqu'à la ligne puis retour
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
                        # Changement de voie normal
                        indice_voie_ego_cible = target_lane
                        changement_voie_en_cours = True
                        print(f"➡ Changement de voie vers la droite (voie {indice_voie_ego_cible + 1})")

cap.release()
cv2.destroyAllWindows()
