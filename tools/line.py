def getABfromPoints(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[float, float]:
    a = float(p2[1] - p1[1]) / float(p2[0] - p1[0])
    b = (p2[1] - (a * p2[0]))
    return a, b

def getLinEqPointsFromAB(p1: tuple[int, int], p2: tuple[int, int], a: float, b: float) -> list:
    pointList = []
    for x in range(min(p1[0], p2[0])*100, max(p1[0], p2[0])*100):
        x /= 100
        pointList.append((round(x),round(a*x+b)))

    return pointList

def getPointListFromCoordinates(p1: tuple[int, int], p2: tuple[int, int]) -> list:
    if p1[0] == p2[0]:
        pointList = [(p1[0], y) for y in range(min(p1[1],p2[1]), max(p1[1],p2[1]))]
    else:
        pointList = getLinEqPointsFromAB(p1, p2, *getABfromPoints(p1, p2))

    return pointList