"""Translations for Volume Amplifier.

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
