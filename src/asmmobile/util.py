def getTimeHourMinute(interval):
    intervalMinutes = (interval.days*86400 + interval.seconds)/60
    hours = intervalMinutes/60
    minutes = intervalMinutes%60
    timeList = []
    if hours > 0:
        timeList.append("%d h" % hours)
    if minutes > 0:
        timeList.append("%d min" % minutes)
    return " ".join(timeList)
