import re

EVENT_PATTERNS = {
    "NEXT_STEP": [
        r"(след(ующий|ующую|лежащую команду|шаг))",
        r"(давай следующий шаг)",
        r"(какой следующий шаг)",
        r"(переходи к следующему этапу)",
    ],
    "PREV_STEP": [
        r"(пред(ыдущий|ущий шаг))",
        r"(вернись к предыдущему шагу)",
    ],
    "STOP_TIMER": [
        r"(останови|выключи)\s+(таймер|отсчет)",
    ],
    "CONTINUE_TIMER": [
        r"(продолжи|включи)\s+(таймер|отсчет)",
    ],
    "ADD_TIME": [
        r"(добавь|прибавь|увеличь)(таймер|время)\s+(\d+)\s?(минут|секунд|часов)",
    ],
}


def parse_event(text):
    text = text.lower()

    for event_name, patterns in EVENT_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if event_name == "ADD_TIME":
                    try:
                        time_value = int(match.group(2))
                        time_unit = match.group(3)
                        return event_name, {"value": time_value,
                                            "unit": time_unit}
                    except (IndexError, ValueError):
                        pass
                return event_name, None
    return None, None
