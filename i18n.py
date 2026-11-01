"""Translations for Volume Booster PC.

Nine languages, English as the fallback. Every table must expose the exact same
set of keys (enforced by test_i18n.py) so a missing translation can never leak
a raw key into the UI.
"""

from __future__ import annotations

import ctypes
import os

FALLBACK = "en"

# code -> native name shown in the language menu
LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português (BR)",
    "ru": "Русский",
    "zh": "简体中文",
    "ja": "日本語",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "subtitle": "System-wide volume boost",
        "report": "Report a bug",
        "check_update": "Check for updates",
        "checking_update": "Checking for updates\u2026",
        "update_title": "Updates",
        "update_current": "You have the latest version ({version}).",
        "update_available": "Version {version} is available. Open the download page?",
        "update_failed": "Could not check for updates.",
        "updates_section": "Updates",
        "check_updates": "Check for updates at startup",
        "change": "Change",
        "download": "Download",
        "open_sound": "Open Sound",
        "hotkey_hint": "Click a shortcut and press the new combination. Esc cancels.",
        "confirm_title": "High level",
        "dont_ask_again": "Don't ask again",
        "cancel": "Cancel",
        "test": "Test",
        "sound_section": "Sound",
        "preview_sound": "Play a tone while moving the slider",
        "warn_loud": "Warn before very high levels",
        "windows_section": "Windows setup",
        "req_engine": "Equalizer APO installed",
        "req_engine_body": "Windows caps every device at 100 %. Equalizer APO is the component that goes past it.",
        "req_attached": "Attached to a playback device",
        "req_attached_body": "Open the Configurator and tick the device you want to boost.",
        "req_enhancements": "Enhancements are disabled on {device}",
        "req_enhancements_body": "Equalizer APO will not process that device. In Sound, open its properties and untick \u00abDisable all enhancements\u00bb.",
        "action_failed": "Could not open it automatically. Open Equalizer APO from the Start menu.",
        "req_reboot": "Reboot after installing Equalizer APO",
        "req_reboot_body": "The APO only loads at startup. If it was just installed, restart Windows.",
        "open": "Open",
        "hotkeys_section": "Global hotkeys",
        "hotkey_up": "Louder",
        "hotkey_down": "Quieter",
        "hotkey_press": "Press the combination\u2026",
        "hotkey_none": "Not set",
        "hotkey_invalid": "That is not a valid shortcut: hold Ctrl, Alt, Shift or Win and press a key.",
        "hotkey_taken": "Windows did not accept {combo}: another program already uses it.",
        "hotkey_saved": "Shortcut saved.",
        "start_section": "Startup",
        "start_hidden": "Start in the notification area",
        "close_to_tray": "Close to the notification area",
        "close": "Close",
        "tray_open": "Open",
        "tray_exit": "Quit",
        "exact": "Exact value",
        "apply": "Apply",
        "setup": "Setup",
        "muted": "muted",
        "applied": "Applied: {gain} · {engine}",
        "not_available": "Boost engine not found - click Setup.",
        "detached": "Equalizer APO is not attached to any device. Re-run its installer and tick the playback device you want to boost.",
        "confirm_loud": "That level is very loud and can hurt your hearing. Apply {gain} anyway?",
        "drift": "The config was changed outside the app. Press Apply to restore the boost.",
        "bad_number": "Enter a number between 0 and 500.",
        "write_failed": "Could not apply: {error}",
        "warning": "Above +6 dB, loud material clips. {gain} is a lot.",
        "autostart": "Start at login",
        "autostart_question": "Let this app start when you sign in, so the selector is ready?",
        "autostart_failed": "Could not change the startup setting: {error}",
        "help_windows": (
            "Windows caps every device at 100 %, so the gain is applied by Equalizer APO.\n\n"
            "1. Download it: sourceforge.net/projects/equalizerapo/\n"
            "2. Install it and tick ONLY the playback device you want to boost.\n"
            "3. Reboot.\n"
            "4. Sound > your device > Enhancements: leave "
            "'Disable all enhancements' unticked.\n\n"
            "Expected config file:\n{location}"
        ),
        "help_linux": (
            "PipeWire or PulseAudio applies system volume above 100 % natively, so no "
            "extra component is needed.\n\n"
            "If the engine is missing, install it:\n"
            "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
            "  Fedora: sudo dnf install pulseaudio-utils\n"
            "  Arch: sudo pacman -S libpulse\n\n"
            "Check which sink is used:\n  pactl get-default-sink\n\n"
            "Detected engine:\n{location}"
        ),
        "help_macos": (
            "macOS has no system-wide gain above 100 % without a virtual audio device, "
            "and that kind of device adds latency.\n\n"
            "This version supports Windows and Linux only. On macOS the selector opens "
            "but the boost stays disabled."
        ),
    },
    "es": {
        "subtitle": "Amplificación de volumen del sistema",
        "report": "Informar de un fallo",
        "check_update": "Buscar actualización",
        "checking_update": "Buscando actualizaciones\u2026",
        "update_title": "Actualizaciones",
        "update_current": "Tienes la última versión ({version}).",
        "update_available": "Hay una versión nueva: {version}. ¿Abrir la página de descarga?",
        "update_failed": "No se pudo comprobar si hay actualizaciones.",
        "updates_section": "Actualizaciones",
        "check_updates": "Buscar actualizaciones al iniciar",
        "change": "Cambiar",
        "download": "Descargar",
        "open_sound": "Abrir Sonido",
        "hotkey_hint": "Haz clic en un atajo y pulsa la combinación nueva. Esc cancela.",
        "confirm_title": "Nivel alto",
        "dont_ask_again": "No volver a preguntar",
        "cancel": "Cancelar",
        "test": "Probar",
        "sound_section": "Sonido",
        "preview_sound": "Sonar al mover el deslizador",
        "warn_loud": "Avisar antes de niveles muy altos",
        "windows_section": "Configuración de Windows",
        "req_engine": "Equalizer APO instalado",
        "req_engine_body": "Windows limita cada dispositivo al 100 %. Equalizer APO es el componente que permite superarlo.",
        "req_attached": "Asociado a un dispositivo de reproducción",
        "req_attached_body": "Abre el Configurator y marca el dispositivo que quieras amplificar.",
        "req_enhancements": "Las mejoras están desactivadas en {device}",
        "req_enhancements_body": "Equalizer APO no procesará ese dispositivo. En Sonido, abre sus propiedades y desmarca \u00abDeshabilitar todas las mejoras\u00bb.",
        "action_failed": "No pude abrirlo automáticamente. Abre Equalizer APO desde el menú Inicio.",
        "req_reboot": "Reiniciar tras instalar Equalizer APO",
        "req_reboot_body": "El APO solo se carga al arrancar. Si acabas de instalarlo, reinicia Windows.",
        "open": "Abrir",
        "hotkeys_section": "Atajos globales",
        "hotkey_up": "Subir",
        "hotkey_down": "Bajar",
        "hotkey_press": "Pulsa la combinación\u2026",
        "hotkey_none": "Sin asignar",
        "hotkey_invalid": "Esa combinación no vale: mantén Ctrl, Alt, Mayús o Win y pulsa una tecla.",
        "hotkey_taken": "Windows no acepta {combo}: otro programa ya la usa.",
        "hotkey_saved": "Atajo guardado.",
        "start_section": "Inicio",
        "start_hidden": "Empezar en el área de notificación",
        "close_to_tray": "Cerrar al área de notificación",
        "close": "Cerrar",
        "tray_open": "Abrir",
        "tray_exit": "Salir",
        "exact": "Valor exacto",
        "apply": "Aplicar",
        "setup": "Configuración",
        "muted": "silenciado",
        "applied": "Aplicado: {gain} · {engine}",
        "not_available": "No encuentro el motor - pulsa Configuración.",
        "detached": "Equalizer APO no está enganchado a ningún dispositivo. Vuelve a ejecutar su instalador y marca el dispositivo que quieras amplificar.",
        "confirm_loud": "Ese nivel es muy alto y puede dañar tu oído. ¿Aplicar {gain} igualmente?",
        "drift": "La configuración cambió fuera de la app. Pulsa Aplicar para restaurar el boost.",
        "bad_number": "Escribe un número entre 0 y 500.",
        "write_failed": "No se pudo aplicar: {error}",
        "warning": "Por encima de +6 dB, lo que ya suena fuerte satura. {gain} es mucho.",
        "autostart": "Iniciar al entrar",
        "autostart_question": "¿Dejar que la app arranque al iniciar sesión para tener el selector listo?",
        "autostart_failed": "No se pudo cambiar el inicio automático: {error}",
        "help_windows": (
            "Windows limita cada dispositivo al 100 %, así que el boost lo aplica "
            "Equalizer APO.\n\n"
            "1. Descárgalo: sourceforge.net/projects/equalizerapo/\n"
            "2. Instálalo marcando SOLO el dispositivo que quieras amplificar.\n"
            "3. Reinicia.\n"
            "4. Sonido > tu dispositivo > Mejoras: deja «Deshabilitar todas las "
            "mejoras» sin marcar.\n\n"
            "Fichero de configuración esperado:\n{location}"
        ),
        "help_linux": (
            "PipeWire o PulseAudio aplican volumen de sistema por encima del 100 % de "
            "forma nativa, así que no hace falta nada más.\n\n"
            "Si falta el motor, instálalo:\n"
            "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
            "  Fedora: sudo dnf install pulseaudio-utils\n"
            "  Arch: sudo pacman -S libpulse\n\n"
            "Comprueba qué salida se usa:\n  pactl get-default-sink\n\n"
            "Motor detectado:\n{location}"
        ),
        "help_macos": (
            "macOS no permite superar el 100 % en todo el sistema sin un dispositivo de "
            "audio virtual, y ese dispositivo añade latencia.\n\n"
            "Esta versión soporta solo Windows y Linux. En macOS el selector se abre, "
            "pero el boost queda desactivado."
        ),
    },
    "fr": {
        "subtitle": "Amplification du volume système",
        "report": "Signaler un bug",
        "check_update": "Rechercher des mises à jour",
        "checking_update": "Recherche de mises à jour\u2026",
        "update_title": "Mises à jour",
        "update_current": "Vous avez la dernière version ({version}).",
        "update_available": "La version {version} est disponible. Ouvrir la page de téléchargement ?",
        "update_failed": "Impossible de vérifier les mises à jour.",
        "updates_section": "Mises à jour",
        "check_updates": "Vérifier les mises à jour au démarrage",
        "change": "Modifier",
        "download": "Télécharger",
        "open_sound": "Ouvrir Son",
        "hotkey_hint": "Cliquez sur un raccourci et appuyez sur la nouvelle combinaison. Échap annule.",
        "confirm_title": "Niveau élevé",
        "dont_ask_again": "Ne plus demander",
        "cancel": "Annuler",
        "test": "Tester",
        "sound_section": "Son",
        "preview_sound": "Jouer un son en déplaçant le curseur",
        "warn_loud": "Avertir avant les niveaux très élevés",
        "windows_section": "Configuration de Windows",
        "req_engine": "Equalizer APO installé",
        "req_engine_body": "Windows limite chaque appareil à 100 %. Equalizer APO est le composant qui permet de dépasser.",
        "req_attached": "Associé à un périphérique de lecture",
        "req_attached_body": "Ouvrez le Configurator et cochez le périphérique à amplifier.",
        "req_enhancements": "Les améliorations sont désactivées sur {device}",
        "req_enhancements_body": "Equalizer APO ne traitera pas ce périphérique. Dans Son, ouvrez ses propriétés et décochez \u00ab Désactiver toutes les améliorations \u00bb.",
        "action_failed": "Impossible de l'ouvrir automatiquement. Ouvrez Equalizer APO depuis le menu Démarrer.",
        "req_reboot": "Redémarrer après l'installation d'Equalizer APO",
        "req_reboot_body": "L'APO ne se charge qu'au démarrage. S'il vient d'être installé, redémarrez Windows.",
        "open": "Ouvrir",
        "hotkeys_section": "Raccourcis globaux",
        "hotkey_up": "Plus fort",
        "hotkey_down": "Moins fort",
        "hotkey_press": "Appuyez sur la combinaison\u2026",
        "hotkey_none": "Non défini",
        "hotkey_invalid": "Raccourci invalide : maintenez Ctrl, Alt, Maj ou Win et appuyez sur une touche.",
        "hotkey_taken": "Windows refuse {combo} : un autre programme l'utilise déjà.",
        "hotkey_saved": "Raccourci enregistré.",
        "start_section": "Démarrage",
        "start_hidden": "Démarrer dans la zone de notification",
        "close_to_tray": "Fermer vers la zone de notification",
        "close": "Fermer",
        "tray_open": "Ouvrir",
        "tray_exit": "Quitter",
        "exact": "Valeur exacte",
        "apply": "Appliquer",
        "setup": "Configuration",
        "muted": "coupé",
        "applied": "Appliqué : {gain} · {engine}",
        "not_available": "Moteur introuvable - cliquez sur Configuration.",
        "detached": "Equalizer APO n'est attaché à aucun périphérique. Relancez son installeur et cochez le périphérique à amplifier.",
        "confirm_loud": "Ce niveau est très fort et peut abîmer votre audition. Appliquer {gain} quand même ?",
        "drift": "La configuration a changé en dehors de l'app. Cliquez sur Appliquer pour restaurer le gain.",
        "bad_number": "Saisissez un nombre entre 0 et 500.",
        "write_failed": "Impossible d'appliquer : {error}",
        "warning": "Au-delà de +6 dB, un signal fort sature. {gain}, c'est beaucoup.",
        "autostart": "Lancer à la connexion",
        "autostart_question": "Autoriser l'app à démarrer à la connexion pour avoir le sélecteur prêt ?",
        "autostart_failed": "Impossible de modifier le démarrage : {error}",
        "help_windows": (
            "Windows limite chaque périphérique à 100 %, le gain est donc appliqué par "
            "Equalizer APO.\n\n"
            "1. Téléchargez-le : sourceforge.net/projects/equalizerapo/\n"
            "2. Installez-le en cochant UNIQUEMENT le périphérique à amplifier.\n"
            "3. Redémarrez.\n"
            "4. Son > votre périphérique > Améliorations : laissez « Désactiver toutes "
            "les améliorations » décoché.\n\n"
            "Fichier de configuration attendu :\n{location}"
        ),
        "help_linux": (
            "PipeWire ou PulseAudio applique nativement un volume système au-delà de "
            "100 %, aucun composant supplémentaire n'est nécessaire.\n\n"
            "Si le moteur manque, installez-le :\n"
            "  Debian/Ubuntu : sudo apt install pulseaudio-utils\n"
            "  Fedora : sudo dnf install pulseaudio-utils\n"
            "  Arch : sudo pacman -S libpulse\n\n"
            "Vérifiez la sortie utilisée :\n  pactl get-default-sink\n\n"
            "Moteur détecté :\n{location}"
        ),
        "help_macos": (
            "macOS ne permet pas de dépasser 100 % sur tout le système sans un "
            "périphérique audio virtuel, et ce type de périphérique ajoute de la "
            "latence.\n\n"
            "Cette version ne prend en charge que Windows et Linux. Sur macOS le "
            "sélecteur s'ouvre mais l'amplification reste désactivée."
        ),
    },
    "de": {
        "subtitle": "Systemweite Lautstärkeverstärkung",
        "report": "Fehler melden",
        "check_update": "Nach Updates suchen",
        "checking_update": "Suche nach Updates\u2026",
        "update_title": "Updates",
        "update_current": "Sie haben die neueste Version ({version}).",
        "update_available": "Version {version} ist verfügbar. Downloadseite öffnen?",
        "update_failed": "Updates konnten nicht geprüft werden.",
        "updates_section": "Updates",
        "check_updates": "Beim Start nach Updates suchen",
        "change": "Ändern",
        "download": "Herunterladen",
        "open_sound": "Sound öffnen",
        "hotkey_hint": "Klicken Sie auf ein Kürzel und drücken Sie die neue Kombination. Esc bricht ab.",
        "confirm_title": "Hoher Pegel",
        "dont_ask_again": "Nicht mehr fragen",
        "cancel": "Abbrechen",
        "test": "Testen",
        "sound_section": "Ton",
        "preview_sound": "Ton beim Bewegen des Reglers abspielen",
        "warn_loud": "Vor sehr hohen Pegeln warnen",
        "windows_section": "Windows einrichten",
        "req_engine": "Equalizer APO installiert",
        "req_engine_body": "Windows begrenzt jedes Gerät auf 100 %. Equalizer APO ist die Komponente, die darüber hinausgeht.",
        "req_attached": "Einem Wiedergabegerät zugeordnet",
        "req_attached_body": "Öffnen Sie den Configurator und kreuzen Sie das zu verstärkende Gerät an.",
        "req_enhancements": "Verbesserungen sind auf {device} deaktiviert",
        "req_enhancements_body": "Equalizer APO verarbeitet dieses Gerät nicht. Öffnen Sie unter Sound die Eigenschaften und entfernen Sie das Häkchen bei \u201eAlle Verbesserungen deaktivieren\u201c.",
        "action_failed": "Konnte nicht automatisch geöffnet werden. Öffnen Sie Equalizer APO über das Startmenü.",
        "req_reboot": "Nach der Installation von Equalizer APO neu starten",
        "req_reboot_body": "Der APO wird nur beim Start geladen. Wenn er gerade installiert wurde, starten Sie Windows neu.",
        "open": "Öffnen",
        "hotkeys_section": "Globale Tastenkürzel",
        "hotkey_up": "Lauter",
        "hotkey_down": "Leiser",
        "hotkey_press": "Tastenkombination drücken\u2026",
        "hotkey_none": "Nicht belegt",
        "hotkey_invalid": "Ungültiges Kürzel: Halten Sie Strg, Alt, Umschalt oder Win gedrückt und drücken Sie eine Taste.",
        "hotkey_taken": "Windows akzeptiert {combo} nicht: ein anderes Programm nutzt sie bereits.",
        "hotkey_saved": "Kürzel gespeichert.",
        "start_section": "Start",
        "start_hidden": "Im Infobereich starten",
        "close_to_tray": "In den Infobereich schließen",
        "close": "Schließen",
        "tray_open": "Öffnen",
        "tray_exit": "Beenden",
        "exact": "Genauer Wert",
        "apply": "Übernehmen",
        "setup": "Einrichtung",
        "muted": "stumm",
        "applied": "Übernommen: {gain} · {engine}",
        "not_available": "Verstärker nicht gefunden - klicken Sie auf Einrichtung.",
        "detached": "Equalizer APO ist keinem Gerät zugeordnet. Starten Sie das Installationsprogramm neu und wählen Sie das zu verstärkende Gerät.",
        "confirm_loud": "Diese Lautstärke ist sehr hoch und kann Ihr Gehör schädigen. {gain} trotzdem übernehmen?",
        "drift": "Die Konfiguration wurde außerhalb der App geändert. Klicken Sie auf Übernehmen.",
        "bad_number": "Bitte eine Zahl zwischen 0 und 500 eingeben.",
        "write_failed": "Konnte nicht übernehmen: {error}",
        "warning": "Über +6 dB übersteuert lautes Material. {gain} ist viel.",
        "autostart": "Bei Anmeldung starten",
        "autostart_question": "Darf die App bei der Anmeldung starten, damit der Regler bereit ist?",
        "autostart_failed": "Starteinstellung konnte nicht geändert werden: {error}",
        "help_windows": (
            "Windows begrenzt jedes Gerät auf 100 %, daher übernimmt Equalizer APO die "
            "Verstärkung.\n\n"
            "1. Herunterladen: sourceforge.net/projects/equalizerapo/\n"
            "2. Installieren und NUR das zu verstärkende Gerät ankreuzen.\n"
            "3. Neu starten.\n"
            "4. Sound > Ihr Gerät > Verbesserungen: „Alle Verbesserungen deaktivieren“ "
            "nicht ankreuzen.\n\n"
            "Erwartete Konfigurationsdatei:\n{location}"
        ),
        "help_linux": (
            "PipeWire oder PulseAudio kann die Systemlautstärke von Haus aus über 100 % "
            "setzen, eine weitere Komponente ist also nicht nötig.\n\n"
            "Falls die Engine fehlt, installieren Sie sie:\n"
            "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
            "  Fedora: sudo dnf install pulseaudio-utils\n"
            "  Arch: sudo pacman -S libpulse\n\n"
            "Verwendete Ausgabe prüfen:\n  pactl get-default-sink\n\n"
            "Erkannte Engine:\n{location}"
        ),
        "help_macos": (
            "macOS erlaubt systemweit keine Verstärkung über 100 % ohne ein virtuelles "
            "Audiogerät, und solche Geräte erzeugen Latenz.\n\n"
            "Diese Version unterstützt nur Windows und Linux. Unter macOS öffnet sich "
            "der Regler, die Verstärkung bleibt aber deaktiviert."
        ),
    },
    "it": {
        "subtitle": "Amplificazione del volume di sistema",
        "report": "Segnala un bug",
        "check_update": "Cerca aggiornamenti",
        "checking_update": "Ricerca aggiornamenti\u2026",
        "update_title": "Aggiornamenti",
        "update_current": "Hai l'ultima versione ({version}).",
        "update_available": "La versione {version} è disponibile. Aprire la pagina di download?",
        "update_failed": "Impossibile verificare gli aggiornamenti.",
        "updates_section": "Aggiornamenti",
        "check_updates": "Cerca aggiornamenti all'avvio",
        "change": "Cambia",
        "download": "Scarica",
        "open_sound": "Apri Audio",
        "hotkey_hint": "Fai clic su una scorciatoia e premi la nuova combinazione. Esc annulla.",
        "confirm_title": "Livello alto",
        "dont_ask_again": "Non chiedere più",
        "cancel": "Annulla",
        "test": "Prova",
        "sound_section": "Audio",
        "preview_sound": "Riproduci un tono mentre muovi il cursore",
        "warn_loud": "Avvisa prima di livelli molto alti",
        "windows_section": "Configurazione di Windows",
        "req_engine": "Equalizer APO installato",
        "req_engine_body": "Windows limita ogni dispositivo al 100 %. Equalizer APO è il componente che permette di superarlo.",
        "req_attached": "Associato a un dispositivo di riproduzione",
        "req_attached_body": "Apri il Configurator e seleziona il dispositivo da amplificare.",
        "req_enhancements": "I miglioramenti sono disattivati su {device}",
        "req_enhancements_body": "Equalizer APO non elaborerà quel dispositivo. In Audio, apri le proprietà e deseleziona \u00abDisattiva tutti i miglioramenti\u00bb.",
        "action_failed": "Impossibile aprirlo automaticamente. Apri Equalizer APO dal menu Start.",
        "req_reboot": "Riavvia dopo aver installato Equalizer APO",
        "req_reboot_body": "L'APO si carica solo all'avvio. Se l'hai appena installato, riavvia Windows.",
        "open": "Apri",
        "hotkeys_section": "Scorciatoie globali",
        "hotkey_up": "Alza",
        "hotkey_down": "Abbassa",
        "hotkey_press": "Premi la combinazione\u2026",
        "hotkey_none": "Non assegnata",
        "hotkey_invalid": "Scorciatoia non valida: tieni premuto Ctrl, Alt, Maiusc o Win e premi un tasto.",
        "hotkey_taken": "Windows non accetta {combo}: un altro programma la usa già.",
        "hotkey_saved": "Scorciatoia salvata.",
        "start_section": "Avvio",
        "start_hidden": "Avvia nell'area di notifica",
        "close_to_tray": "Chiudi nell'area di notifica",
        "close": "Chiudi",
        "tray_open": "Apri",
        "tray_exit": "Esci",
        "exact": "Valore esatto",
        "apply": "Applica",
        "setup": "Configurazione",
        "muted": "muto",
        "applied": "Applicato: {gain} · {engine}",
        "not_available": "Motore non trovato - premi Configurazione.",
        "detached": "Equalizer APO non è associato a nessun dispositivo. Riesegui il suo installer e seleziona il dispositivo da amplificare.",
        "confirm_loud": "Questo livello è molto alto e può danneggiare l'udito. Applicare {gain} comunque?",
        "drift": "La configurazione è cambiata fuori dall'app. Premi Applica per ripristinare il guadagno.",
        "bad_number": "Inserisci un numero tra 0 e 500.",
        "write_failed": "Impossibile applicare: {error}",
        "warning": "Oltre +6 dB il materiale forte satura. {gain} è molto.",
        "autostart": "Avvia all'accesso",
        "autostart_question": "Consentire all'app di avviarsi all'accesso, così il selettore è pronto?",
        "autostart_failed": "Impossibile modificare l'avvio automatico: {error}",
        "help_windows": (
            "Windows limita ogni dispositivo al 100 %, quindi il guadagno lo applica "
            "Equalizer APO.\n\n"
            "1. Scaricalo: sourceforge.net/projects/equalizerapo/\n"
            "2. Installalo selezionando SOLO il dispositivo da amplificare.\n"
            "3. Riavvia.\n"
            "4. Audio > il tuo dispositivo > Miglioramenti: lascia deselezionato "
            "«Disattiva tutti i miglioramenti».\n\n"
            "File di configurazione atteso:\n{location}"
        ),
        "help_linux": (
            "PipeWire o PulseAudio applicano nativamente un volume di sistema oltre il "
            "100 %, quindi non serve altro.\n\n"
            "Se il motore manca, installalo:\n"
            "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
            "  Fedora: sudo dnf install pulseaudio-utils\n"
            "  Arch: sudo pacman -S libpulse\n\n"
            "Controlla l'uscita in uso:\n  pactl get-default-sink\n\n"
            "Motore rilevato:\n{location}"
        ),
        "help_macos": (
            "macOS non consente di superare il 100 % su tutto il sistema senza un "
            "dispositivo audio virtuale, e quel tipo di dispositivo aggiunge latenza.\n\n"
            "Questa versione supporta solo Windows e Linux. Su macOS il selettore si "
            "apre ma il boost resta disattivato."
        ),
    },
    "pt": {
        "subtitle": "Amplificação do volume do sistema",
        "report": "Relatar um bug",
        "check_update": "Verificar atualizações",
        "checking_update": "Verificando atualizações\u2026",
        "update_title": "Atualizações",
        "update_current": "Você tem a versão mais recente ({version}).",
        "update_available": "A versão {version} está disponível. Abrir a página de download?",
        "update_failed": "Não foi possível verificar atualizações.",
        "updates_section": "Atualizações",
        "check_updates": "Verificar atualizações ao iniciar",
        "change": "Alterar",
        "download": "Baixar",
        "open_sound": "Abrir Som",
        "hotkey_hint": "Clique em um atalho e pressione a nova combinação. Esc cancela.",
        "confirm_title": "Nível alto",
        "dont_ask_again": "Não perguntar novamente",
        "cancel": "Cancelar",
        "test": "Testar",
        "sound_section": "Som",
        "preview_sound": "Tocar um tom ao mover o controle",
        "warn_loud": "Avisar antes de níveis muito altos",
        "windows_section": "Configuração do Windows",
        "req_engine": "Equalizer APO instalado",
        "req_engine_body": "O Windows limita cada dispositivo a 100 %. O Equalizer APO é o componente que permite ultrapassar.",
        "req_attached": "Associado a um dispositivo de reprodução",
        "req_attached_body": "Abra o Configurator e marque o dispositivo que deseja amplificar.",
        "req_enhancements": "Os aprimoramentos estão desativados em {device}",
        "req_enhancements_body": "O Equalizer APO não vai processar esse dispositivo. Em Som, abra as propriedades e desmarque \u00abDesativar todos os aprimoramentos\u00bb.",
        "action_failed": "Não foi possível abrir automaticamente. Abra o Equalizer APO pelo menu Iniciar.",
        "req_reboot": "Reiniciar após instalar o Equalizer APO",
        "req_reboot_body": "O APO só carrega na inicialização. Se acabou de instalar, reinicie o Windows.",
        "open": "Abrir",
        "hotkeys_section": "Atalhos globais",
        "hotkey_up": "Aumentar",
        "hotkey_down": "Diminuir",
        "hotkey_press": "Pressione a combinação\u2026",
        "hotkey_none": "Não definido",
        "hotkey_invalid": "Atalho inválido: mantenha Ctrl, Alt, Shift ou Win e pressione uma tecla.",
        "hotkey_taken": "O Windows não aceita {combo}: outro programa já a usa.",
        "hotkey_saved": "Atalho salvo.",
        "start_section": "Inicialização",
        "start_hidden": "Iniciar na área de notificação",
        "close_to_tray": "Fechar para a área de notificação",
        "close": "Fechar",
        "tray_open": "Abrir",
        "tray_exit": "Sair",
        "exact": "Valor exato",
        "apply": "Aplicar",
        "setup": "Configuração",
        "muted": "mudo",
        "applied": "Aplicado: {gain} · {engine}",
        "not_available": "Motor não encontrado - clique em Configuração.",
        "detached": "O Equalizer APO não está associado a nenhum dispositivo. Execute o instalador de novo e marque o dispositivo que deseja amplificar.",
        "confirm_loud": "Esse nível é muito alto e pode prejudicar sua audição. Aplicar {gain} mesmo assim?",
        "drift": "A configuração mudou fora do app. Clique em Aplicar para restaurar o ganho.",
        "bad_number": "Digite um número entre 0 e 500.",
        "write_failed": "Não foi possível aplicar: {error}",
        "warning": "Acima de +6 dB o áudio forte satura. {gain} é muito.",
        "autostart": "Iniciar ao entrar",
        "autostart_question": "Permitir que o app inicie ao entrar, para o seletor ficar pronto?",
        "autostart_failed": "Não foi possível alterar a inicialização: {error}",
        "help_windows": (
            "O Windows limita cada dispositivo a 100 %, então o ganho é aplicado pelo "
            "Equalizer APO.\n\n"
            "1. Baixe: sourceforge.net/projects/equalizerapo/\n"
            "2. Instale marcando SOMENTE o dispositivo que deseja amplificar.\n"
            "3. Reinicie.\n"
            "4. Som > seu dispositivo > Aprimoramentos: deixe «Desativar todos os "
            "aprimoramentos» desmarcado.\n\n"
            "Arquivo de configuração esperado:\n{location}"
        ),
        "help_linux": (
            "O PipeWire ou o PulseAudio aplicam volume de sistema acima de 100 % "
            "nativamente, então nenhum componente extra é necessário.\n\n"
            "Se o motor estiver faltando, instale:\n"
            "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
            "  Fedora: sudo dnf install pulseaudio-utils\n"
            "  Arch: sudo pacman -S libpulse\n\n"
            "Veja qual saída está em uso:\n  pactl get-default-sink\n\n"
            "Motor detectado:\n{location}"
        ),
        "help_macos": (
            "O macOS não permite passar de 100 % em todo o sistema sem um dispositivo "
            "de áudio virtual, e esse tipo de dispositivo adiciona latência.\n\n"
            "Esta versão suporta apenas Windows e Linux. No macOS o seletor abre, mas o "
            "boost fica desativado."
        ),
    },
    "ru": {
        "subtitle": "Усиление системной громкости",
        "report": "Сообщить об ошибке",
        "check_update": "Проверить обновления",
        "checking_update": "Проверка обновлений\u2026",
        "update_title": "Обновления",
        "update_current": "У вас последняя версия ({version}).",
        "update_available": "Доступна версия {version}. Открыть страницу загрузки?",
        "update_failed": "Не удалось проверить обновления.",
        "updates_section": "Обновления",
        "check_updates": "Проверять обновления при запуске",
        "change": "Изменить",
        "download": "Скачать",
        "open_sound": "Открыть Звук",
        "hotkey_hint": "Нажмите на сочетание и введите новое. Esc отменяет.",
        "confirm_title": "Высокий уровень",
        "dont_ask_again": "Больше не спрашивать",
        "cancel": "Отмена",
        "test": "Проверить",
        "sound_section": "Звук",
        "preview_sound": "Играть тон при движении ползунка",
        "warn_loud": "Предупреждать о высоких уровнях",
        "windows_section": "Настройка Windows",
        "req_engine": "Equalizer APO установлен",
        "req_engine_body": "Windows ограничивает каждое устройство до 100 %. Equalizer APO — компонент, который позволяет это обойти.",
        "req_attached": "Привязан к устройству воспроизведения",
        "req_attached_body": "Откройте Configurator и отметьте устройство, которое нужно усилить.",
        "req_enhancements": "Улучшения отключены для {device}",
        "req_enhancements_body": "Equalizer APO не будет обрабатывать это устройство. В разделе «Звук» откройте свойства и снимите «Отключить все улучшения».",
        "action_failed": "Не удалось открыть автоматически. Откройте Equalizer APO из меню «Пуск».",
        "req_reboot": "Перезагрузка после установки Equalizer APO",
        "req_reboot_body": "APO загружается только при старте. Если вы только что его установили, перезагрузите Windows.",
        "open": "Открыть",
        "hotkeys_section": "Глобальные сочетания",
        "hotkey_up": "Громче",
        "hotkey_down": "Тише",
        "hotkey_press": "Нажмите сочетание\u2026",
        "hotkey_none": "Не задано",
        "hotkey_invalid": "Недопустимое сочетание: удерживайте Ctrl, Alt, Shift или Win и нажмите клавишу.",
        "hotkey_taken": "Windows не принимает {combo}: её уже использует другая программа.",
        "hotkey_saved": "Сочетание сохранено.",
        "start_section": "Запуск",
        "start_hidden": "Запускать в области уведомлений",
        "close_to_tray": "Закрывать в область уведомлений",
        "close": "Закрыть",
        "tray_open": "Открыть",
        "tray_exit": "Выход",
        "exact": "Точное значение",
        "apply": "Применить",
        "setup": "Настройка",
        "muted": "без звука",
        "applied": "Применено: {gain} · {engine}",
        "not_available": "Движок не найден - нажмите «Настройка».",
        "detached": "Equalizer APO не привязан ни к одному устройству. Запустите установщик снова и отметьте устройство, которое нужно усилить.",
        "confirm_loud": "Такой уровень очень громкий и может повредить слух. Всё равно применить {gain}?",
        "drift": "Конфигурация изменена вне приложения. Нажмите «Применить».",
        "bad_number": "Введите число от 0 до 500.",
        "write_failed": "Не удалось применить: {error}",
        "warning": "Выше +6 дБ громкий материал искажается. {gain} - это много.",
        "autostart": "Запускать при входе",
        "autostart_question": "Разрешить приложению запускаться при входе, чтобы регулятор был готов?",
        "autostart_failed": "Не удалось изменить автозапуск: {error}",
        "help_windows": (
            "Windows ограничивает каждое устройство до 100 %, поэтому усиление "
            "применяет Equalizer APO.\n\n"
            "1. Скачайте: sourceforge.net/projects/equalizerapo/\n"
            "2. Установите, отметив ТОЛЬКО устройство, которое нужно усилить.\n"
            "3. Перезагрузите компьютер.\n"
            "4. Звук > ваше устройство > Улучшения: не отмечайте «Отключить все "
            "улучшения».\n\n"
            "Ожидаемый файл конфигурации:\n{location}"
        ),
        "help_linux": (
            "PipeWire или PulseAudio умеют поднимать системную громкость выше 100 % "
            "из коробки, поэтому ничего дополнительно ставить не нужно.\n\n"
            "Если движка нет, установите его:\n"
            "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
            "  Fedora: sudo dnf install pulseaudio-utils\n"
            "  Arch: sudo pacman -S libpulse\n\n"
            "Проверьте используемый выход:\n  pactl get-default-sink\n\n"
            "Обнаруженный движок:\n{location}"
        ),
        "help_macos": (
            "macOS не позволяет превысить 100 % для всей системы без виртуального "
            "аудиоустройства, а такие устройства добавляют задержку.\n\n"
            "Эта версия поддерживает только Windows и Linux. На macOS регулятор "
            "открывается, но усиление отключено."
        ),
    },
    "zh": {
        "subtitle": "系统音量增强",
        "report": "报告问题",
        "check_update": "检查更新",
        "checking_update": "正在检查更新\u2026",
        "update_title": "更新",
        "update_current": "已是最新版本（{version}）。",
        "update_available": "有新版本 {version}。是否打开下载页面？",
        "update_failed": "无法检查更新。",
        "updates_section": "更新",
        "check_updates": "启动时检查更新",
        "change": "更改",
        "download": "下载",
        "open_sound": "打开声音设置",
        "hotkey_hint": "点击快捷键并按下新的组合键。Esc 取消。",
        "confirm_title": "音量过高",
        "dont_ask_again": "不再询问",
        "cancel": "取消",
        "test": "试听",
        "sound_section": "声音",
        "preview_sound": "移动滑块时播放提示音",
        "warn_loud": "高音量前提醒",
        "windows_section": "Windows 设置",
        "req_engine": "已安装 Equalizer APO",
        "req_engine_body": "Windows 将每个设备的音量限制在 100 %。Equalizer APO 是突破这一限制的组件。",
        "req_attached": "已关联播放设备",
        "req_attached_body": "打开 Configurator，勾选要增强的设备。",
        "req_enhancements": "{device} 已禁用增强功能",
        "req_enhancements_body": "Equalizer APO 不会处理该设备。在“声音”中打开其属性，取消勾选“禁用所有增强功能”。",
        "action_failed": "无法自动打开。请从开始菜单打开 Equalizer APO。",
        "req_reboot": "安装 Equalizer APO 后重启",
        "req_reboot_body": "APO 只在系统启动时加载。如果刚刚安装，请重启 Windows。",
        "open": "打开",
        "hotkeys_section": "全局快捷键",
        "hotkey_up": "增大",
        "hotkey_down": "减小",
        "hotkey_press": "请按下组合键\u2026",
        "hotkey_none": "未设置",
        "hotkey_invalid": "无效的快捷键：按住 Ctrl、Alt、Shift 或 Win 再按一个键。",
        "hotkey_taken": "Windows 不接受 {combo}：其他程序已占用。",
        "hotkey_saved": "快捷键已保存。",
        "start_section": "启动",
        "start_hidden": "在通知区域启动",
        "close_to_tray": "关闭到通知区域",
        "close": "关闭",
        "tray_open": "打开",
        "tray_exit": "退出",
        "exact": "精确数值",
        "apply": "应用",
        "setup": "设置",
        "muted": "静音",
        "applied": "已应用：{gain} · {engine}",
        "not_available": "未找到增强引擎 - 请点击“设置”。",
        "detached": "Equalizer APO 未关联任何设备。请重新运行安装程序并勾选要增强的设备。",
        "confirm_loud": "这个音量非常高，可能损伤听力。仍要应用 {gain} 吗？",
        "drift": "配置已被外部更改。点击“应用”恢复增益。",
        "bad_number": "请输入 0 到 500 之间的数字。",
        "write_failed": "应用失败：{error}",
        "warning": "超过 +6 dB 时，较大的信号会削波。{gain} 已经很高。",
        "autostart": "登录时启动",
        "autostart_question": "允许应用在登录时启动，以便随时使用滑块？",
        "autostart_failed": "无法更改启动设置：{error}",
        "help_windows": (
            "Windows 将每个设备的音量限制在 100 %，因此增益由 Equalizer APO 应用。\n\n"
            "1. 下载：sourceforge.net/projects/equalizerapo/\n"
            "2. 安装时只勾选要增强的设备。\n"
            "3. 重启电脑。\n"
            "4. 声音 > 你的设备 > 增强：不要勾选“禁用所有增强功能”。\n\n"
            "预期的配置文件：\n{location}"
        ),
        "help_linux": (
            "PipeWire 或 PulseAudio 原生支持把系统音量设为 100 % 以上，因此不需要"
            "额外组件。\n\n"
            "如果缺少引擎，请安装：\n"
            "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
            "  Fedora: sudo dnf install pulseaudio-utils\n"
            "  Arch: sudo pacman -S libpulse\n\n"
            "查看当前使用的输出：\n  pactl get-default-sink\n\n"
            "检测到的引擎：\n{location}"
        ),
        "help_macos": (
            "macOS 在没有虚拟音频设备的情况下无法对全系统超过 100 % 增益，而这类"
            "设备会增加延迟。\n\n"
            "此版本仅支持 Windows 和 Linux。在 macOS 上滑块可以打开，但增益保持"
            "禁用。"
        ),
    },
    "ja": {
        "subtitle": "システム全体の音量ブースト",
        "report": "不具合を報告",
        "check_update": "更新を確認",
        "checking_update": "更新を確認しています\u2026",
        "update_title": "更新",
        "update_current": "最新バージョン（{version}）です。",
        "update_available": "バージョン {version} があります。ダウンロードページを開きますか？",
        "update_failed": "更新を確認できませんでした。",
        "updates_section": "更新",
        "check_updates": "起動時に更新を確認する",
        "change": "変更",
        "download": "ダウンロード",
        "open_sound": "サウンドを開く",
        "hotkey_hint": "ショートカットをクリックして新しい組み合わせを押してください。Esc でキャンセル。",
        "confirm_title": "音量が大きすぎます",
        "dont_ask_again": "次回から表示しない",
        "cancel": "キャンセル",
        "test": "試聴",
        "sound_section": "サウンド",
        "preview_sound": "スライダーを動かすと音を鳴らす",
        "warn_loud": "大きすぎる音量の前に警告する",
        "windows_section": "Windows の設定",
        "req_engine": "Equalizer APO がインストール済み",
        "req_engine_body": "Windows はすべてのデバイスを 100 % に制限します。Equalizer APO がそれを超えるためのコンポーネントです。",
        "req_attached": "再生デバイスに関連付け済み",
        "req_attached_body": "Configurator を開き、ブーストしたいデバイスを選択してください。",
        "req_enhancements": "{device} で拡張機能が無効になっています",
        "req_enhancements_body": "Equalizer APO はそのデバイスを処理しません。サウンドでプロパティを開き、「すべての拡張機能を無効にする」をオフにしてください。",
        "action_failed": "自動で開けませんでした。スタートメニューから Equalizer APO を開いてください。",
        "req_reboot": "Equalizer APO のインストール後に再起動",
        "req_reboot_body": "APO は起動時にのみ読み込まれます。インストールしたばかりなら Windows を再起動してください。",
        "open": "開く",
        "hotkeys_section": "グローバルショートカット",
        "hotkey_up": "音量を上げる",
        "hotkey_down": "音量を下げる",
        "hotkey_press": "キーの組み合わせを押してください\u2026",
        "hotkey_none": "未設定",
        "hotkey_invalid": "無効なショートカットです: Ctrl、Alt、Shift、Win のいずれかを押しながらキーを押してください。",
        "hotkey_taken": "Windows が {combo} を受け付けません: 別のプログラムが使用中です。",
        "hotkey_saved": "ショートカットを保存しました。",
        "start_section": "起動",
        "start_hidden": "通知領域で起動",
        "close_to_tray": "通知領域に閉じる",
        "close": "閉じる",
        "tray_open": "開く",
        "tray_exit": "終了",
        "exact": "正確な値",
        "apply": "適用",
        "setup": "セットアップ",
        "muted": "ミュート",
        "applied": "適用しました: {gain} · {engine}",
        "not_available": "エンジンが見つかりません - 「セットアップ」をクリックしてください。",
        "detached": "Equalizer APO がどのデバイスにも関連付けられていません。インストーラーを再実行し、ブーストしたいデバイスを選択してください。",
        "confirm_loud": "この音量は非常に大きく、聴覚を損なう恐れがあります。{gain} を適用しますか？",
        "drift": "設定がアプリ外で変更されました。「適用」を押して元に戻してください。",
        "bad_number": "0 から 500 の数値を入力してください。",
        "write_failed": "適用できませんでした: {error}",
        "warning": "+6 dB を超えると大きな音はクリップします。{gain} は大きすぎます。",
        "autostart": "ログイン時に起動",
        "autostart_question": "ログイン時に起動して、すぐにスライダーを使えるようにしますか？",
        "autostart_failed": "スタートアップ設定を変更できませんでした: {error}",
        "help_windows": (
            "Windows はすべてのデバイスを 100 % に制限するため、ブーストは "
            "Equalizer APO が適用します。\n\n"
            "1. ダウンロード: sourceforge.net/projects/equalizerapo/\n"
            "2. インストール時にブーストしたいデバイスだけを選択します。\n"
            "3. 再起動します。\n"
            "4. サウンド > デバイス > 拡張機能:「すべての拡張機能を無効にする」を"
            "オフのままにします。\n\n"
            "想定される設定ファイル:\n{location}"
        ),
        "help_linux": (
            "PipeWire または PulseAudio は 100 % を超えるシステム音量を標準で扱える"
            "ため、追加のコンポーネントは不要です。\n\n"
            "エンジンがない場合はインストールします:\n"
            "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
            "  Fedora: sudo dnf install pulseaudio-utils\n"
            "  Arch: sudo pacman -S libpulse\n\n"
            "使用中の出力を確認:\n  pactl get-default-sink\n\n"
            "検出したエンジン:\n{location}"
        ),
        "help_macos": (
            "macOS では仮想オーディオデバイスなしにシステム全体で 100 % を超える"
            "ゲインをかけられず、その種のデバイスは遅延を追加します。\n\n"
            "このバージョンは Windows と Linux のみ対応です。macOS ではスライダーは"
            "開きますが、ブーストは無効のままです。"
        ),
    },
}

# Primary language IDs (LANGID & 0x3FF) -> translation code.
_LANGID_TO_CODE: dict[int, str] = {
    0x09: "en",
    0x0A: "es",
    0x0C: "fr",
    0x07: "de",
    0x10: "it",
    0x16: "pt",
    0x19: "ru",
    0x04: "zh",
    0x11: "ja",
}


def translate(language: str, key: str, **values: object) -> str:
    """Never raises: unknown language or key falls back to English, then to the key."""
    table = TRANSLATIONS.get(language) or TRANSLATIONS[FALLBACK]
    template = table.get(key) or TRANSLATIONS[FALLBACK].get(key, key)
    try:
        return template.format(**values)
    except (KeyError, IndexError, ValueError):
        return template


def language_from_langid(langid: int) -> str:
    return _LANGID_TO_CODE.get(int(langid) & 0x3FF, FALLBACK)


def system_language() -> str:
    """The desktop's UI language when it is one we ship, English otherwise."""
    try:
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return language_from_langid(langid)
    except (AttributeError, OSError):
        pass
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        raw = os.environ.get(variable)
        if not raw:
            continue
        code = raw.split(":")[0].split("_")[0].split(".")[0].lower()
        if code in TRANSLATIONS:
            return code
    return FALLBACK
