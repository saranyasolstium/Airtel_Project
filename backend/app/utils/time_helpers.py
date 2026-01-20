def humanize_duration(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    m = seconds // 60
    h = m // 60
    m = m % 60
    if h > 0 and m > 0:
        return f"{h}h {m}m"
    if h > 0:
        return f"{h}h"
    return f"{m}m"
