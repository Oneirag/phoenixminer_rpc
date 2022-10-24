import pandas as pd
import holidays


def peak_price(dt=None) -> bool:
    """Returns true if given datetime (or now() if None) is peak"""
    tz = "Europe/Madrid"
    if dt is None:
        dt = pd.Timestamp.now(tz)
    if dt.dst() is None:
        dt = dt.tz_localize(tz)
    horario = {"summer": (13, 23),
               "winter": (12, 22)}
    horario = {"summer": (8, 24),
               "winter": (8, 24)}
    is_summer = dt.dst().total_seconds() > 0
    limits = horario.get("summer" if is_summer else "winter")
    hour = dt.hour
    hols = holidays.Spain(years=dt.year)
    working_day = dt.weekday() <= 4 and dt not in hols
    return (limits[0] <= hour < limits[1]) and working_day


if __name__ == '__main__':
    test_dates = {pd.Timestamp.now(): "Now",
                  pd.Timestamp(2020, 7, 1): "Un summer ",
                  pd.Timestamp(2020, 1, 1): "Un winter (festivo)",
                  pd.Timestamp(2020, 1, 2): "Un winter (no festivo)",
                  pd.Timestamp(2020, 7, 1, 13): "Un summer ",
                  pd.Timestamp(2020, 1, 1, 12): "Un winter (festivo)",
                  pd.Timestamp(2020, 1, 2, 12): "Un winter (no festivo)",
                  pd.Timestamp(2020, 1, 2, 8): "Un winter (no festivo)",
                  pd.Timestamp(2020, 1, 2, 9): "Un winter (no festivo)",
                  pd.Timestamp(2020, 1, 2, 7, 59): "Un winter (no festivo)",
                  pd.Timestamp(2020, 1, 2, 23, 59): "Un winter (no festivo)",
                  }
    for time, desc in test_dates.items():
        print(f"## {desc} ##")
        print("Fecha {}: es punta {}".format(time.isoformat(), peak_price(time)))
