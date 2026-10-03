def wind_chill(wind_velocity, temperature):
    return round((35.74 + 0.6215 * temperature - 35.75 * (wind_velocity ** 0.16) + 0.4275 * temperature * (wind_velocity ** 0.16)))