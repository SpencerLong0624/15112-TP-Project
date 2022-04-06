import string, copy, random, math, os, time
from dataclasses import make_dataclass
from cmu_112_graphics import *

###############################################################################
# Name: Spencer Long
# Andrew ID: syl2
# Section: G1
# Assigment: Shapes Tower Defense (TP)
###############################################################################


#variables for game
def appStarted(app):

    #display screen for each feature
    app.StartScreen = True
    app.EasyScreen = False
    app.HardScreen = False
    app.ReportScreen = False
    app.HelpScreen = False
    app.mode = None
    app.towerOnBoard = []

    #General game variables
    app.timerDelay = 50
    app.timerCount = 0
    app.isPaused = True
    app.gameOver = False
    app.upgrade = False
    app.upgradeSelect = None

    #player data
    app.score = 0
    app.level = 1
    app.lives = 100
    app.coins = 112
    app.selectedRow = -1
    
    #grid dimensions and left margin size
    app.EasyGridSize = 8
    app.HardGridSize = 10
    app.leftMargin = app.width/8

    #2D list of grid
    app.Easy2DL = make2dList(app, 'Easy')
    app.Hard2DL = make2dList(app, 'Hard')

    #path planning for balloons
    #dx and dy for steps that balloons take 
    app.Edx = ((app.width - app.leftMargin)/app.EasyGridSize)/6
    app.Edy = (app.height / app.EasyGridSize)/6
    app.Hdx = ((app.width - app.leftMargin)/app.HardGridSize)/6
    app.Hdy = (app.height / app.HardGridSize)/6
    app.Easypath = pathPlanning(app, 'Easy')
    app.Hardpath = pathPlanning(app, 'Hard')

    #balloon data
    app.numOfBalloons = 2
    app.balloonR = 30
    app.balloonSpeed = 10
    app.balloonList = None

    #tower data
    app.towers = [('Dart Tower', '50'), ('8-Way Tower', '75'), 
                  ('Ice Tower', '100'), ('Sniper Tower', '125'), 
                  ('Mine Tower', '150'), ('Bomb', '10')]


#Balloon class
class Balloon(object):

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.pathIndex = 0  #location on balloon path
        self.moving = True
        self.frozen = False
        if color == 'red':
            self.lives = 1
            self.invisible = False
        elif color == 'blue':
            self.lives = 2
            self.invisible = False
        elif color == 'green':
            self.lives = 3
            self.invisible = False
        elif color == 'white':
            self.lives = 1
            self.invisible = True
    
    def __repr__(self):
        return f'({self.name}, {self.color}, {self.moving}, {self.frozen})'

#tower class
class Tower(object):
    
    def __init__(self, name, row, col):
        self.name = name
        self.row = row
        self.col = col


#dart tower, a subclass of tower class
class Dart(Tower):
    
    def __init__(self, name, row, col):
        super().__init__(name, row, col)
        self.attackSpeed = 10
        self.range = 200
        self.target = []


#8-Way tower, a subclass of tower class
class EightWay(Tower):

    def __init__(self, name, row, col):
        super().__init__(name, row, col)
        self.attackSpeed = 10
        self.range = 150


#Ice tower, a subclass of tower class
class Ice(Tower):

    def __init__(self, name, row, col):
        super().__init__(name, row, col)
        self.attackSpeed = 7
        self.range = 100
        self.frozenNum = 5 #number of balloons the tower can freeze at a time
        self.target = []


#Sniper tower, a subclass of tower class
class Sniper(Tower):

    def __init__(self, name, row, col):
        super().__init__(name, row, col)
        self.attackSpeed = 15
        self.range = 1000
        self.target = []


#Mine tower, a subclass of tower class
class Mine(Tower):

    def __init__(self, name, row, col):
        super().__init__(name, row, col)
        self.attackSpeed = 10
        self.range = 1000


#bomb class, bombs that can be placed on balloon path to pop balloons
class Bomb(object):

    def __init__(self, name, row, col):
        self.name = name
        self.row = row
        self.col = col
        self.lives = 5 #how many ballons a bomb can pop 


#distance formula
def distance(x0, y0, x1, y1):
    return (((x1 - x0)**2) + ((y1-y0)**2))**0.5


#from https://www.cs.cmu.edu/~112/notes/notes-2d-lists.html
#creates 2D list that maps to grid
def make2dList(app, mode):
    if mode == 'Easy':
        n = app.EasyGridSize
    elif mode == 'Hard':
        n = app.HardGridSize
    
    L = [([None] * n) for _ in range(n)]
    path = makeRandomPath(mode)
    for cell in path:
        (row, col) = cell
        L[row][col] = 'Path'
    return L


#from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
#gets cell bounds for grid 
def getCellBounds(app, row, col, mode):
    gridWidth  = app.width - app.leftMargin
    gridHeight = app.height
    if mode == 'Easy':
        cellWidth = gridWidth / app.EasyGridSize
        cellHeight = gridHeight / app.EasyGridSize
    elif mode == 'Hard':
        cellWidth = gridWidth / app.HardGridSize
        cellHeight = gridHeight / app.HardGridSize
    
    x0 = app.leftMargin + col * cellWidth
    x1 = app.leftMargin+ (col+1) * cellWidth
    y0 = row * cellHeight
    y1 = (row+1) * cellHeight
    return (x0, y0, x1, y1)
    

#random path generator
#wrapper function to get random balloon path on grid
def makeRandomPath(mode):
    #number of path cells on grid
    if mode == 'Easy': 
        length = random.randint(18, 25) 
    elif mode == 'Hard':
        length = random.randint(28, 39)
    return randomPathHelper(mode, (0,0), length, [(0,0)]) #helper function


#checks to see if last path placement is reaching end of grid
def pathReachesEnd(mode, path):
    endRow = path[len(path)-1][0]
    endCol = path[len(path)-1][1]
    if endRow + endCol == 0: #make sure not start path cell
        return False
    #border cells for grids in both modes
    elif mode == 'Easy':
        return (endRow == 0 or endRow == 7) or (endCol == 7)
    elif mode == 'Hard':
        return (endRow == 0 or endRow == 9) or (endCol == 9)


#helpr function to make better looking paths
#path cells on each row/col are limited to 4 each 
#Note: smallest number for cells in each row/col before algorithm crashes
def isGood(row, col, path):
    rowCount = 0
    colCount = 0
    #finds cells in path that has the same row/col as next placement
    for cell in path:
        (pathRow, pathCol) = cell
        if pathRow == row:
            rowCount += 1
        if pathCol == col:
            colCount += 1
    
    #bad placement if path cells in row/col exceeds limit
    if rowCount < 4 and colCount < 4:
        return True
    return False


#checks if next path cell placement is legal and also calls isGood above
def isLegalAndGood(mode, current, direction, path):
    nextRow = current[0] + direction[0]
    nextCol = current[1] + direction[1]
    #upperbounds for row/col depending on mode
    if mode == 'Easy':
        top = 7
    else:
        top = 9
    
    #checks requirments
    if ((nextRow, nextCol) not in path) and (isGood(nextRow, nextCol, path)):
        if (0 <= nextRow <= top) and (0 <= nextCol <= top):
            return True
    return False


#helper function that uses recursive backtracking to create balloon path
#start of path is always most top-left cell
#function also accounts for randomly chosen path length
#concept inspired from https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking
def randomPathHelper(mode, current, length, path):
    #base case
    #length achieved and has an exit for balloons
    if (len(path) == length) and pathReachesEnd(mode, path):
        return path
    #length acheived but has no exit for balloons so end is in middle of grid
    elif (len(path) == length) and (not pathReachesEnd(mode, path)):
        return None
    
    #recursive case
    deltas = [(-1,0), (1,0), (0,1), (0,-1)] #directions that path can go
    random.shuffle(deltas) #shuffle directions for randomness of path
    for direction in deltas:
        if isLegalAndGood(mode, current, direction, path):
            nextRow = current[0] + direction[0]
            nextCol = current[1] + direction[1]
            path.append((nextRow, nextCol))
            final = randomPathHelper(mode, (nextRow,nextCol), length, path)
            if final != None:
                return path
            path.pop()
    return None


#helper function for findNeighbors
#checks if the new tuple is in range of the grid
def inRange(row, col, mode):
    if mode == 'Easy':
        top = 7
    else:
        top = 9
    
    if (0 <= row <= top) and (0 <= col <= top):
        return True
    return False


#finds the neighbor path cells of a current cell
def findNeighbors(app, current, path, mode):
    if mode == 'Easy':
        grid = app.Easy2DL 
    elif mode == 'Hard':
        grid = app.Hard2DL 

    result = []
    (row, col) = current
    directions = [(-1,0), (1,0), (0,1), (0,-1)]
    for direction in directions:
        newRow = row + direction[0]
        newCol = col + direction[1]
        if inRange(newRow, newCol, mode): # checks if new index is in range
            #checks that neighbor wasn't visited and that it is actually a path
            #cell
            if (newRow, newCol) not in path and grid[newRow][newCol] == 'Path':
                result.append((newRow, newCol))
    return result


#finds length of randomly generated path
def pathLength(app, mode):
    count = 0
    #based on which mode, path size is different
    if mode == 'Easy':
        grid = app.Easy2DL 
    elif mode == 'Hard':
        grid = app.Hard2DL 
    
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 'Path':
                count += 1
    return count


#finds path in terms of grid coordinates
def pathPlanningGrid(app, mode):
    #first find path length of randomly generated grid
    if mode == 'Easy':
        length = pathLength(app, mode)
    elif mode == 'Hard':
        length = pathLength(app, mode)
    return pathPlanningHelper(app, (0,0), length, [(0,0)], mode)


#BFS helper function using back tracking instead of while loop for efficiency
#Since I don't need the shortest path, I modified the general algorithm to find
#a path that visits all path cells and ends at the end path cell
#Note: used list instead of queues 
def pathPlanningHelper(app, current, length, path, mode):
    #base cases
    #finds a path that reachs end cell
    if (len(path) == length) and (pathReachesEnd(mode, path)):
        return path
    #path ends at a cell in the middle of the grid
    elif (len(path) == length) and (not pathReachesEnd(mode, path)):
        return None

    #recursive case
    #loop through the neighbor path cells of current cell
    for neighbor in findNeighbors(app, current, path, mode):
        path.append(neighbor)
        nextPath = pathPlanningHelper(app, neighbor, length, path, mode)
        if nextPath != None:
            return path
        path.pop()
    return None


#from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
#modified version of getCellBounds that gets midpoint of cell
def midPoint(app, row, col, mode):
    gridWidth  = app.width - app.leftMargin
    gridHeight = app.height
    if mode == 'Easy':
        cellWidth = gridWidth / app.EasyGridSize
        cellHeight = gridHeight / app.EasyGridSize
    elif mode == 'Hard':
        cellWidth = gridWidth / app.HardGridSize
        cellHeight = gridHeight / app.HardGridSize
    
    x0 = app.leftMargin + col * cellWidth
    y0 = row * cellHeight

    cx = x0 + cellWidth/2
    cy = y0 + cellHeight/2
    return (cx, cy)


#returns a list of midpoints of balloon path cells
def getMidPoints(app, gridPath, mode):
    result = []
    for (row, col) in gridPath:
        coordinate = midPoint(app, row, col, mode)
        result.append(coordinate)
    return result


#gets pixel coordinates between midpoints of balloon path cells
def getDirectionPoints(app, mode, x, y, direction):
    #different dx, dy depending on mode
    if mode == 'Easy': 
        (app.dx, app.dy) = (app.Edx, app.Edy)
    elif mode == 'Hard':
        (app.dx, app.dy) = (app.Hdx, app.Hdy)
    
    #initialize midpoint in list
    result = [(x,y)]

    #loop 5 times to get to next midpoint because dx/dy is 1/6 of a cell's 
    #height/width
    for _ in range(5):
        if direction == 'Right':
            result.append((result[-1][0] + app.dx, y))
        elif direction == 'Left':
            result.append((result[-1][0] - app.dx, y))
        elif direction == 'Up':
            result.append((x, result[-1][1] - app.dy))
        elif direction == 'Down':
            result.append((x, result[-1][1] + app.dy))
    return result


#gets pixel coordinates between last midpoint and disappearance location
def getEndPoints(app, mode, x, y, last):
    (row, col) = last #row and col of last balloon path cell
    if row == 0: #top horizontal border
        return getDirectionPoints(app, mode, x, y, 'Up')
    elif row == 7 or row == 9: #bottom horizontal border
        return getDirectionPoints(app, mode, x, y, 'Down')
    elif col == 7 or col == 9: #right vertical border
        return getDirectionPoints(app, mode, x, y, 'Right')
    elif col == 0: #left vertical border
        return getDirectionPoints(app, mode, x, y, 'Left')


# turns grid based path list into list of pixel coordinates
def pathPlanning(app, mode):
    result = []
    gridPath = pathPlanningGrid(app, mode)  #(row, col) coordinates for path
    midPoints = getMidPoints(app, gridPath, mode)  #midpoint of path cells
    last = gridPath[-1]  #last path cell
    lastMidx = midPoints[-1][0]  #last cell row 
    lastMidy = midPoints[-1][1]  #last cell col

    #loop over midpoints to basically create smaller paths between two midpoints
    for i in range(len(midPoints)):
        #path from spawn location to last midpoint
        if (i != len(midPoints) - 1):
            (x0, y0) = (midPoints[i][0], midPoints[i][1]) #current midpoint
            (x1, y1) = (midPoints[i+1][0], midPoints[i+1][1]) #next midpoint
            if (x1-x0 > 0 and y1-y0 == 0):  #moving right
                result += getDirectionPoints(app, mode, x0, y0, 'Right')
            elif (x1-x0 < 0 and y1-y0 == 0): #moving left
                result += getDirectionPoints(app, mode, x0, y0, 'Left')
            elif (x1-x0 == 0 and y1-y0 < 0): #moving up
                result += getDirectionPoints(app, mode, x0, y0, 'Up')
            elif (x1-x0 == 0 and y1-y0 > 0): #moving down
                result += getDirectionPoints(app, mode, x0, y0, 'Down')
         #path from last midpoint towards unspawn location
        elif (i == len(midPoints) - 1):
            result += getEndPoints(app, mode, lastMidx, lastMidy, last)
    return result


#create list of Balloon instances and returns them in a list
#number of green/blue/red balloons are randomly generated
def createBalloonList(app, n, red, blue, green, white):
    balloonList = []
    #only red balloons
    if (red == True) and (blue == green == False):
        for i in range(n):
            balloon = Balloon(i, 'red')
            balloonList.append(balloon)
    
    #red and blue balloons
    elif (red == blue == True) and (green == False):
        bBalloons = random.randint(int(n/2), n) #random number of green balloons
        for i in range(n):
            if i < bBalloons:
                balloon = Balloon(i, 'blue')
            else:
                balloon = Balloon(i, 'red')
            balloonList.append(balloon)
    
    #all types of balloons
    else:
        gBalloons = random.randint(int(n/4), n) #random num of green balloons
        bBalloons = random.randint(int(n/4), n) #random num of blue balloons
        wBalloons = random.randint(int(n/4), n) #random hum of invisible balloons
        rBalloons = n - gBalloons - bBalloons - wBalloons
        nums = sorted([rBalloons, bBalloons, gBalloons, wBalloons])
        for i in range(n):
            if i <= nums[0]:
                balloon = Balloon(i, 'red')
            elif i <= nums[0] + nums[1]:
                balloon = Balloon(i, 'blue')
            elif i <= nums[0] + nums[1] + nums[2]:
                balloon = Balloon(i, 'white')
            elif i <= sum(nums):
                balloon = Balloon(i, 'green')
            balloonList.append(balloon)
        random.shuffle(balloonList) #shuffle list for random order of appearance
    return balloonList


#decides number of balloons depending on level and calls balloon list maker
#Note: number of balloons increase as the level increases
def makeBalloons(app):
    if app.level <= 5: #early game
        app.numOfBalloons += app.level 
        L = createBalloonList(app, app.numOfBalloons, True, False, False, False)
    elif 5 < app.level <= 15: #mid game
        app.numOfBalloons += int(1.5 * app.level)
        L = createBalloonList(app, app.numOfBalloons, True, True, False, False)
    elif 15 < app.level: #late game
        app.numOfBalloons += (2 * app.level)
        L = createBalloonList(app, app.numOfBalloons, True, True, True, True)
    return L


#decreased health of player if balloon passes end zone and ends game when player
#health is 0
def decreaseHealth(app, i):
    balloonDamage = app.balloonList[i].lives #damage dealt by balloon to user
    if app.lives - balloonDamage >= 0:
        app.lives -= balloonDamage
    elif app.lives - balloonDamage < 0:
        app.isPaused = True
        app.gameOver = True


#increases balloon speed every 4 levels
def increaseBalloonSpeed(app):
    if (app.balloonSpeed != 1) and (app.level % 4 == 0):
        app.balloonSpeed -= 1
        

#moves balloons on the path and decreases health if balloon reaches end
def moveBalloon(app):
    if app.EasyScreen:
        pathLength = len(app.Easypath) - 1
    elif app.HardScreen:
        pathLength = len(app.Hardpath) - 1

    for i in range(len(app.balloonList)):
        #MOVING balloon reaches the end
        if (app.balloonList[i].pathIndex == pathLength) and \
            (app.balloonList[i].moving):

            app.balloonList[i].moving = False
            decreaseHealth(app, i)
        
        #moving balloon hasn't reached the end
        elif app.balloonList[i].pathIndex < pathLength and \
                (not app.balloonList[i].frozen) and (app.balloonList[i].moving):
            app.balloonList[i].pathIndex += 1


#start the new level by calling balloon list making function and unpausing game
def startLevel(app):
    if app.isPaused:
        app.balloonList = makeBalloons(app) #make new list of balloons for level
        increaseBalloonSpeed(app)
        app.isPaused = False


#checks if all balloons in balloon list stopped moving
def allBalloonsStopped(app):
    for balloon in app.balloonList:
        if balloon.moving:
            return False
    return True


#checks if balloon stopped moving and ends animations
def checkEndLevel(app):
    if allBalloonsStopped(app):
        app.isPaused = True
        app.balloonList = [] #reset balloon list

        #resets this so next level doesn't result in uneven movement speed
        app.timerCount = 0

        app.level += 1


#checks if click is in panel
def pointInPanel(app, x, y):
    if (0 <= x <= app.leftMargin) and ((app.height * (4.25/9)) <= y <= app.height):
        return True
    return False


# from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
# gets row and col for selection panel
def selection(app, y):
    gridHeight = app.height * (4.75/9)
    cellHeight = gridHeight/6
    row = int((y - (app.height * (4.25/9))) / cellHeight)
    app.selectedRow = row


#checks if click is on game board
def pointOnBoard(app, x, y):
    return (app.leftMargin < x < app.width)


# from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
# gets cell on board
def getCellOnBoard(app, x, y, mode):
    if mode == 'Easy': dimension = 8
    elif mode == 'Hard': dimension = 10

    gridWidth = app.width - app.leftMargin
    gridHeight = app.height
    cellWidth = gridWidth / dimension
    cellHeight = gridHeight / dimension
    row = int(y / cellHeight)
    col = int((x - app.leftMargin) / cellWidth)
    return (row, col)


#creates the tower object
def createTowerObject(app, row, col):
    if app.selectedRow == 0:
        tower = Dart('Dart', row, col)
    elif app.selectedRow == 1:
        tower = EightWay('EightWay', row, col)
    elif app.selectedRow == 2:
        tower = Ice('Ice', row, col)
    elif app.selectedRow == 3:
        tower = Sniper('Sniper', row, col)
    elif app.selectedRow == 4:
        tower = Mine('Mine', row, col)
    elif app.selectedRow == 5:
        tower = Bomb('Bomb', row, col)
    return tower


#places tower/bomb onto board
def placeTower(app, x, y, mode):
    (row, col) = getCellOnBoard(app, x, y, mode)
    if mode == 'Easy':
        grid = app.Easy2DL
    elif mode == 'Hard':
        grid = app.Hard2DL

    #places tower
    #checks if there is already a tower there
    if (app.selectedRow != 5) and (grid[row][col] == None):
            tower = createTowerObject(app, row, col)
            grid[row][col] = tower
            app.towerOnBoard.append(tower)
            app.coins -= int(app.towers[app.selectedRow][1])
    
    #places bombs
    #Note: can place as many bombs as desired on a single path cell
    elif (app.selectedRow == 5) and (grid[row][col] == 'Path'):
        tower = createTowerObject(app, row, col)
        app.towerOnBoard.append(tower)
        app.coins -= int(app.towers[app.selectedRow][1])


#attack for dart tower
def dartAttack(app, tower, mode):
    #get balloon path depending on mode
    if (mode == 'Easy'): 
        path = app.Easypath
    elif (mode == 'Hard'):
        path = app.Hardpath
    
    #attacking
    for balloon in app.balloonList:
        #balloon is invisible
        if balloon.invisible:
            continue
        elif balloon.moving: #only checks balloons that are still 'alive'
            (x0, y0, x1, y1) = getCellBounds(app,tower.row, tower.col, mode)
            cx = x0 + ((x1-x0)/2)
            cy = y0 + ((y1-y0)/2)
            index = balloon.pathIndex
            if (distance(cx,cy,path[index][0],path[index][1]) <= tower.range):
                if (app.timerCount % tower.attackSpeed == 0):
                    if balloon.lives != 1: #casing for blue/green balloons
                        balloon.lives -= 1
                    else: #popped a balloon
                        balloon.moving = False
                        app.score += 1
                        app.coins += 1
                    break


#attacks for eight way tower
def EightWayAttack(app, tower, mode):
    #get balloon path
    if (mode == 'Easy'): 
        path = app.Easypath
    elif (mode == 'Hard'):
        path = app.Hardpath
    
    #all neighbors of the cell like the tower is in
    range = [((tower.row)+1, (tower.col)-1), ((tower.row)+1, tower.col),
                ((tower.row)+1, (tower.col)+1), (tower.row, (tower.col)+1),
                ((tower.row)-1, (tower.col)+1), ((tower.row)-1, tower.col),
                ((tower.row)-1, (tower.col)-1), (tower.row, (tower.col)-1)]

    for balloon in app.balloonList:
        x = path[balloon.pathIndex][0]
        y = path[balloon.pathIndex][1]
        #if balloon in neighbor cells and moving
        if (getCellOnBoard(app, x, y, mode) in range) and (balloon.moving):
            #attack speed and the balloon isn't invisible
            if (app.timerCount % tower.attackSpeed == 0) and (not balloon.invisible):
                if balloon.lives != 1: #casing for blue/green balloons
                    balloon.lives -= 1
                else: #popped a balloon
                    balloon.moving = False
                    app.score += 1
                    app.coins += 1
                break


#attack for ice tower
def IceAttack(app, tower, mode):
    #get balloon path depending on mode
    if (mode == 'Easy'): 
        path = app.Easypath
    elif (mode == 'Hard'):
        path = app.Hardpath


    num = 0 #num of balloons frozen by current attack
    #attacking
    #checks attack speed
    for balloon in app.balloonList:
        if num == tower.frozenNum: #max num of balloons frozen in one attack
            break
        elif balloon.moving: #only checks balloons that are still 'alive'
            (x0,y0,x1,y1) = getCellBounds(app,tower.row,tower.col, mode)
            cx = x0 + ((x1-x0)/2)
            cy = y0 + ((y1-y0)/2)
            i = balloon.pathIndex
            if distance(cx,cy,path[i][0],path[i][1]) <= tower.range:
                if (app.timerCount % tower.attackSpeed==0):
                    balloon.frozen = True
                    num += 1


#attack for sniper tower
def SniperAttack(app, tower):
    #attack speed and checks if there are still unpopped balloons
    if (app.timerCount % tower.attackSpeed==0) and (not allBalloonsStopped(app)):
        for balloon in app.balloonList:
            if balloon.moving: #decreasing lives of blue/green balloons
                if balloon.lives != 1:
                    balloon.lives -= 1
                else: #popped a balloon
                    balloon.moving = False
                    app.score += 1
                    app.coins += 1
                break


#gets target cell for mine tower
def getTargetCell(app, tower, mode):
    if (mode == 'Easy'): 
        path = app.Easypath
    elif (mode == 'Hard'):
        path = app.Hardpath

    #get center pixel cooridnates of the tower location
    (x0, y0, x1, y1) = getCellBounds(app, tower.row, tower.col, mode)
    cx = x0 + ((x1-x0)/2)
    cy = y0 + ((y1-y0)/2)

    #find closest path cell from path list
    closest = None
    closestXY = None
    for (x,y) in path:
        howFar = distance(cx, cy, x, y) #distance from path to tower center
        if closest == None:
            closest = howFar
            closestXY = (x, y)
        elif closest > howFar:
            closest = howFar
            closestXY = (x, y)
    
    #get cell 
    (row, col) = getCellOnBoard(app, closestXY[0], closestXY[1], mode)
    return (row, col)


#attack for Mind tower
def MineAttack(app, tower, mode):
    #get balloon path depending on mode
    if (mode == 'Easy'): 
        path = app.Easypath
    elif (mode == 'Hard'):
        path = app.Hardpath
    
    (row, col) = getTargetCell(app, tower, mode) #find cell to place bombs
    if app.timerCount % tower.attackSpeed == 0:
        app.towerOnBoard.append(Bomb('Bomb', row, col)) #places bomb


#attack for bomb
def BombAttack(app, tower, mode):
    #get balloon path depending on mode
    if (mode == 'Easy'): 
        path = app.Easypath
    elif (mode == 'Hard'):
        path = app.Hardpath
    
    #attacking
    for balloon in app.balloonList:
        if balloon.moving: #only checks balloons that are still 'alive'
            (x0, y0, x1, y1) = getCellBounds(app,tower.row, tower.col, mode)
            cx = x0 + ((x1-x0)/2)
            cy = y0 + ((y1-y0)/2)
            i = balloon.pathIndex
            bombRange = min(((x1-x0)/2), ((x1-x0)/2))
            if distance(cx,cy,path[i][0],path[i][1]) <= bombRange:
                if tower.lives == 0: #bomb is all used up
                    app.towerOnBoard.remove(tower)
                    break
                elif balloon.lives != 1: #casing for blue/green balloons
                    balloon.lives -= 1
                    tower.lives -= 1
                else: #popped a balloon
                    balloon.moving = False
                    app.score += 1
                    app.coins += 1
                    tower.lives -= 1


#attacking main function that calls attacking function for each tower type
def attacking(app, mode):
    for tower in app.towerOnBoard:
        if tower.name == 'Dart':
            dartAttack(app, tower, mode)
        elif tower.name == 'EightWay':
            EightWayAttack(app, tower, mode)
        elif tower.name == 'Ice':
            IceAttack(app, tower, mode)
        elif tower.name == 'Sniper':
            SniperAttack(app, tower)
        elif tower.name == 'Mine':
            MineAttack(app, tower, mode)
        elif tower.name == 'Bomb':
            BombAttack(app, tower, mode)


#checks if cell on board is empty
def cellIsEmpty(app, x, y, mode):
    if mode == 'Easy':
        grid = app.Easy2DL
    elif mode == 'Hard':
        grid = app.Hard2DL

    (row, col) = getCellOnBoard(app, x, y, mode) #gets the cell
    if ((grid[row][col] == None) or (grid[row][col] == 'Path')):
        return True
    return False


#upgrades towers on board
def upgrade(app, tower):
    if (tower.attackSpeed > 1) and (app.coins - 50 >= 0):
        tower.attackSpeed -= 1
        app.coins -= 50
        app.upgrade = False
        app.upgradeSelect = None


#finds the tower that is being upgraded
def getUpgradeTower(app, x, y, mode):
    if mode == 'Easy':
        grid = app.Easy2DL
    elif mode == 'Hard':
        grid = app.Hard2DL
    
    (row, col) = getCellOnBoard(app, x, y, mode) #gets the cell
    tower = grid[row][col]
    return tower


#runs actions corresponding to mouse clicks at specific locations
def mousePressed(app, event):

    #start screen buttons to enter each feature
    if (app.StartScreen) and (app.width/5 < event.x < app.width * (4/5)):
        if (app.height * (1/2) < event.y < app.height * (9.5/16)):
            app.EasyScreen = True
            app.StartScreen = False
            app.mode = 'Easy'
        elif (app.height * (10/16) < event.y < app.height * (11.5/16)):
            app.HardScreen = True
            app.StartScreen = False
            app.mode = 'Hard'
        elif (app.height * (12/16) < event.y < app.height * (13.5/16)):
            app.ReportScreen = True
            app.StartScreen = False
        elif (app.height * (14/16) < event.y < app.height * (15.5/16)):
            app.HelpScreen = True
            app.StartScreen = False


    #click featues in game
    elif app.EasyScreen or app.HardScreen:
        #back button in game screens
        if (0 < event.x < app.leftMargin) and (0 < event.y < 50):
            app.EasyScreen = False
            app.HardScreen = False
            app.StartScreen = True
            appStarted(app)
        
        #selects tower on panel
        elif pointInPanel(app, event.x, event.y):
            selection(app, event.y)
        
        #placing tower on board
        #checks that there is actually a selection
        elif pointOnBoard(app, event.x, event.y) and \
                (cellIsEmpty(app, event.x, event.y, app.mode)) and \
                    (app.selectedRow != -1):
            #checks that player has enough money
            if app.coins - int(app.towers[app.selectedRow][1]) >= 0:
                placeTower(app, event.x, event.y, app.mode)
        
        #clicks tower to upgrade tower
        #checks that click is on board, cell is occupied, and there are towers 
        #on the board
        elif pointOnBoard(app, event.x, event.y) and \
                (not cellIsEmpty(app, event.x, event.y, app.mode)) and \
                    (app.towerOnBoard != []):
            app.upgrade = True
            #get tower that is being upgraded
            app.upgradeSelect = getUpgradeTower(app, event.x, event.y, app.mode)


    #back button in report screen
    elif app.ReportScreen:
        if (0 < event.x < app.width/6) and (0 < event.y < 50):
            app.ReportScreen = False
            app.StartScreen = True
            appStarted(app)


    #back button in help screen
    elif app.HelpScreen:
        if (0 < event.x < app.width/6) and (0 < event.y < 50):
            app.HelpScreen = False
            app.StartScreen = True
            appStarted(app)


#executes actions corresponding to specific keybaord events
def keyPressed(app, event):
    #in-game key commands
    if (app.EasyScreen or app.HardScreen) and (not app.gameOver):
        #start new level
        if event.key == 's':
            startLevel(app)
        #to upgrade a tower
        elif app.upgrade and event.key == 'u':
            upgrade(app, app.upgradeSelect)
        #hack to get coins
        elif event.key == 'c':
            app.coins += 1000
        #skip to level 20
        elif event.key == 'l':
            app.level = 20
            app.balloonSpeed = 1
    
    elif app.gameOver:
        if event.key == 'r':
            appStarted(app)


#executes actions based on time
def timerFired(app):
    #movement of balloons
    if not app.isPaused:
        app.timerCount += 1
        checkEndLevel(app) #check if level ends
        if app.timerCount % app.balloonSpeed == 0:
            moveBalloon(app) #moves balloon
        attacking(app, app.mode) #makes towers attack balloons


# draws the starting screen for game
def drawStartScreen(app, canvas):
    #background
    canvas.create_rectangle(0, 0, app.width, app.height, fill = 'black')
    
    #boxes for each button
    canvas.create_rectangle(app.width/5, app.height * (1/2), app.width * (4/5), 
                            app.height * (9.5/16), fill = 'light blue')
    canvas.create_rectangle(app.width/5, app.height * (10/16), 
                            app.width * (4/5), app.height * (11.5/16), 
                            fill = 'light blue')
    canvas.create_rectangle(app.width/5, app.height * (12/16), 
                            app.width * (4/5), app.height * (13.5/16), 
                            fill = 'light blue')
    canvas.create_rectangle(app.width/5, app.height * (14/16), 
                            app.width * (4/5), app.height * (15.5/16), 
                            fill = 'light blue')
    
    #names for each button
    canvas.create_text(app.width/2, app.height * (1/4), 
                       text = 'Shapes Tower Defense', font = 'Arial 40 bold', 
                       fill = 'white')
    canvas.create_text(app.width/2, app.height * (8.75/16), text = 'Easy',
                       font = 'Arial 20 bold')
    canvas.create_text(app.width/2, app.height * (10.75/16), text = 'Hard',
                       font = 'Arial 20 bold')
    canvas.create_text(app.width/2, app.height * (12.75/16), 
                       text = 'Shape Data', font = 'Arial 20 bold') 
    canvas.create_text(app.width/2, app.height * (14.75/16), text = 'Help',
                       font = 'Arial 20 bold')


#modified version of getCellBounds from
#https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
#gets cell bounds of side panel for towers
def getPanelCellBounds(app, row):
    gridHeight = app.height * (4.75/9)
    cellHeight = gridHeight/6
    x0 = 0
    x1 = app.leftMargin
    y0 = (app.height * (4.25/9)) + row * cellHeight
    y1 = y0 + cellHeight
    return (x0, y0, x1, y1)


#draws side panel for towers
def drawPanel(app, canvas):
    for row in range(6): #panel is only one column
        (x0, y0, x1, y1) = getPanelCellBounds(app, row)
        if row == app.selectedRow: color = 'grey'
        else: color = 'black'
        canvas.create_rectangle(x0, y0, x1, y1, fill = color, 
                                outline = 'white')
        canvas.create_text(x0 + (x1-x0)/2, y0 + (y1-y0)/2, 
                           text = app.towers[row][0], fill = 'red')
        canvas.create_text(x0 + ((x1-x0) * (8/9)), y0 + ((y1-y0)/7), 
                           text = app.towers[row][1], font = 'Arial 10 bold',
                           fill = 'red')


#draws game board for both modes
def drawBoard(app, canvas, mode):
    if mode == 'Easy':
        for row in range(app.EasyGridSize):
            for col in range(app.EasyGridSize):
                (x0, y0, x1, y1) = getCellBounds(app, row, col, mode)
                if app.Easy2DL[row][col] == 'Path':
                    color = 'seashell3'
                else:
                    color = 'green'
                canvas.create_rectangle(x0, y0, x1, y1, fill = color)
    elif mode == 'Hard':
        for row in range(app.HardGridSize):
            for col in range(app.HardGridSize):
                (x0, y0, x1, y1) = getCellBounds(app, row, col, mode)
                if app.Hard2DL[row][col] == 'Path':
                    color = 'seashell3'
                else:
                    color = 'green'
                canvas.create_rectangle(x0, y0, x1, y1, fill = color)


#draws line for the balloon path
def drawPathLine(app, canvas, mode):
    if mode == 'Easy':
        points = app.Easypath
    elif mode == 'Hard':
        points = app.Hardpath
    
    for i in range(len(points)):
        if i != len(points) - 1:
            (x0, y0) = (points[i][0], points[i][1])
            (x1, y1) = (points[i+1][0], points[i+1][1])
            canvas.create_line(x0, y0, x1, y1, width = 5, fill = 'grey')


#draws balloons
def drawBalloon(app, canvas, mode):
    if not app.isPaused:
        if (mode == 'Easy'): 
            path = app.Easypath
        elif (mode == 'Hard'):
            path = app.Hardpath
        
        for balloon in app.balloonList:
            if balloon.moving:
                (cx, cy) = path[balloon.pathIndex]
                canvas.create_oval(cx-app.balloonR, cy-app.balloonR, 
                                   cx+app.balloonR, cy+app.balloonR,
                                   fill = balloon.color, width = 0)
                canvas.create_text(cx, cy, text = balloon.lives)


#draws dart tower (bullseye)
def drawDart(app, canvas, tower, mode):
    (a0, b0, a1, b1) = getCellBounds(app, tower.row, tower.col, mode)
    cx = a0 + ((a1-a0)/2)
    cy = b0 + ((b1-b0)/2)

    canvas.create_oval(cx - 30, cy - 30, cx + 30, cy + 30,
                       fill = 'blue')
    canvas.create_oval(cx - 20, cy - 20, cx + 20, cy + 20,
                       fill = 'red')
    canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10,
                       fill = 'yellow')


#draws 8-Way Tower (diamond)
def drawEightWay(app, canvas, tower, mode):
    (a0, b0, a1, b1) = getCellBounds(app, tower.row, tower.col, mode)
    cx = a0 + ((a1-a0)/2)
    cy = b0 + ((b1-b0)/2)

    x0 = cx 
    y0 = cy - 30
    x1 = cx + 30
    y1 = cy
    x2 = cx
    y2 = cy + 30
    x3 = cx - 30
    y3 = cy
    canvas.create_polygon(x0, y0, x1, y1, x2, y2, x3, y3, fill = 'purple')


#draws ice tower (square)
def drawIce(app, canvas, tower, mode):
    (a0, b0, a1, b1) = getCellBounds(app, tower.row, tower.col, mode)
    cx = a0 + ((a1-a0)/2)
    cy = b0 + ((b1-b0)/2)

    x0 = cx - 30
    y0 = cy - 30
    x1 = cx + 30
    y1 = cy + 30
    canvas.create_rectangle(x0, y0, x1, y1, fill = 'light blue')


#draws sniper tower (triangle)
def drawSniper(app, canvas, tower, mode):
    (a0, b0, a1, b1) = getCellBounds(app, tower.row, tower.col, mode)
    cx = a0 + ((a1-a0)/2)
    cy = b0 + ((b1-b0)/2)

    x0 = cx
    y0 = cy - 30
    x1 = cx + 30
    y1 = cy + 30
    x2 = cx - 30
    y2 = cy + 30
    canvas.create_polygon(x0, y0, x1, y1, x2, y2, fill = 'brown')


#drawws mine tower (rectangle)
def drawMine(app, canvas, tower, mode):
    (a0, b0, a1, b1) = getCellBounds(app, tower.row, tower.col, mode)
    cx = a0 + ((a1-a0)/2)
    cy = b0 + ((b1-b0)/2)

    x0 = cx - 15
    y0 = cy - 30
    x1 = cx + 15
    y1 = cy + 30
    canvas.create_rectangle(x0, y0, x1, y1, fill = 'red')


#draws bomb (Nuclear Shape)
def drawBomb(app, canvas, tower, mode):
    (a0, b0, a1, b1) = getCellBounds(app, tower.row, tower.col, mode)
    cx = a0 + ((a1-a0)/2)
    cy = b0 + ((b1-b0)/2)

    x0 = cx - 30
    y0 = cy - 30
    x1 = cx + 30
    y1 = cy + 30
    canvas.create_arc(x0, y0, x1, y1, start=45, extent=90, fill = 'black')
    canvas.create_arc(x0, y0, x1, y1, start=225, extent=90, fill = 'black')


#draws towers and bombs
def drawTower(app, canvas, mode):
    for tower in app.towerOnBoard:
        if tower.name == 'Bomb':
            drawBomb(app, canvas, tower, mode)
        else:
            if tower.name == 'Dart':
                drawDart(app, canvas, tower, mode)
            elif tower.name == 'EightWay':
                drawEightWay(app, canvas, tower, mode)
            elif tower.name == 'Ice':
                drawIce(app, canvas, tower, mode)
            elif tower.name == 'Sniper':
                drawSniper(app, canvas, tower, mode)
            elif tower.name == 'Mine':
                drawMine(app, canvas, tower, mode)


#draws upgrade screen for 
def drawUpgrade(app, canvas):
    if app.upgrade and app.upgradeSelect != None:
        #upgrade attack speed
        if app.upgradeSelect.attackSpeed != 1:
            text = """
            Press u to upgrade 
            this tower's attack 
            speed for 50 coins!
            """
            canvas.create_text(app.width/16 - 15, app.height * (3.5/9), 
                               text = text, fill = 'red', 
                               font = 'Arial 10 bold')
        
        #attack speed is maxed out
        elif app.upgradeSelect.attackSpeed == 1:
            text = """
            This tower's attack 
            speed is maxed out!
            """
            canvas.create_text(app.width/16 - 15, app.height * (3.5/9), 
                               text = text, fill = 'red', 
                               font = 'Arial 10 bold')


#draws game over pop up when user loses
def drawGameOver(app, canvas):
    if app.gameOver:
        canvas.create_rectangle(app.width/5, app.height/5, app.width * (4/5),
                                app.height * (4/5), fill = 'grey')
        canvas.create_text(app.width/2, app.height/2 - 40, text = 'Game Over!',
                           font = 'Arial 40 bold')
        canvas.create_text(app.width/2, app.height/2 + 20, 
                           text = f'Score: {app.score}',
                           font = 'Arial 20 bold')
        canvas.create_text(app.width/2, app.height/2 + 60, 
                           text = 'Press r to go back to Home Screen.',
                           font = 'Arial 20 bold')               


#draws overall gaming screen for both modes
def drawGameScreen(app, canvas, mode):
    #background
    canvas.create_rectangle(0, 0, app.width, app.height, fill = 'black')

    #back button and text
    canvas.create_rectangle(0, 0, app.leftMargin, 50, fill = 'red')
    canvas.create_text(app.width * (0.5/8), 50/2, text = 'Back', 
                       font = 'Arial 20 bold')

    canvas.create_text(app.width * (0.5/8), app.height/9, 
                       text = f'Score: {app.score}', fill = 'white')
    canvas.create_text(app.width * (0.5/8), app.height * (1.5/9), 
                       text = f'Level: {app.level}', fill = 'white')
    canvas.create_text(app.width * (0.5/8), app.height * (2/9), 
                       text = f'Lives: {app.lives}', fill = 'white')
    canvas.create_text(app.width * (0.5/8), app.height * (2.5/9), 
                       text = f'Coins: {app.coins}', fill = 'white')
    
    #gaming grid
    drawBoard(app, canvas, mode)

    #draw tower selection panel
    drawPanel(app, canvas)

    #draws lines for balloon path
    drawPathLine(app, canvas, mode)

    #draws balloons
    drawBalloon(app, canvas, mode)

    #draws towers
    drawTower(app, canvas, mode)

    #upgrade panel
    drawUpgrade(app, canvas)

    #draws game over screen
    drawGameOver(app, canvas)


#draws report screen
def drawReportScreen(app, canvas):
    #back button and text
    canvas.create_rectangle(0, 0, app.width/6, 50, fill = 'red')
    canvas.create_text(app.width/12, 50/2, text = 'Back', 
                       font = 'Arial 20 bold')
    information = """
    Dart Tower (Circle): Regular Tower with medium range and medium 
    attack speed.

    8-Way Tower (Diamond): Pops ballons that enter the 8 neighbor 
    cells around it. It has a a medium attack speed and a limited 
    range.

    Ice Tower (Square): Freezed up to 5 balloons with a small range 
    and a slow attack speed. It can detect invisible balloons

    Sniper Tower (Triangle): A long range tower that has a range of 
    the whole map, but it has a very slow attack speed. It can detect 
    invisible balloons.

    Mine Tower (Rectangle): Places bombs at the closest path cell. 
    It has a medium bomb spawning rate. It is advised to place it at 
    back up locations.

    Bomb (Arcs): Contraption that can pop up to 5 balloons. They can 
    only be placed on the path of the balloon. Note that bombs can 
    stack on top of each other.
    """
    canvas.create_text(app.width/2, app.height/2, text = information,
                       font = 'Arial 20 bold')


# draws help screen when help screen is clicked
def drawHelpScreen(app, canvas):
    instructions = """\
    Shapes Tower Defense is a 1 player strategy game. Players will start the
    game with 112 coins, 100 lives, and access to all towers. The score is 
    based off of how many balloons that are popped until the player dies. Each 
    time a balloon passes through the end zone, a point of health is lost. 
    There are three different kinds of balloons: red, blue, and green. Red 
    balloons have 1 life, blue balloons have 2 lives, and so forth. Note 
    that balloons that reach the end zone will decrease the player's life 
    points based off of the color of the balloon. The game ends when the 
    player has no life points left. The map will be random. Easy is an 8x8 
    grid and hard is a 10x10 grid. Players are only permittied to place one 
    tower on cells that aren't part of the balloon path. Each tower has its 
    unique attack type. Towers are bought with coins and 1 coin is earned 
    for every balloon popped. For more information about the towers, please 
    refer to Shape Data. As level increase, the speed and amount of balloons 
    will also increase. Have fun!
    """

    #back button and text
    canvas.create_rectangle(0, 0, app.width/6, 50, fill = 'red')
    canvas.create_text(app.width/12, 50/2, text = 'Back', 
                       font = 'Arial 20 bold')
    
    #text for help screen
    canvas.create_rectangle(0, 50, app.width, app.height, fill = 'blue')
    canvas.create_text(app.width/2, app.height/2, text = instructions, 
                      font = 'Arial 27 bold', fill = 'yellow')
    canvas.create_text(app.width/2, 50/2, text = 'How to play the game!',
                       font = 'Arial 20 bold')


#main draw function that controls graphics for overall game
def redrawAll(app, canvas):
    if app.StartScreen:
        drawStartScreen(app, canvas)
    elif app.EasyScreen:
        drawGameScreen(app, canvas, 'Easy')
    elif app.HardScreen:
        drawGameScreen(app, canvas, 'Hard')
    elif app.ReportScreen:
        drawReportScreen(app, canvas)
    elif app.HelpScreen:
        drawHelpScreen(app, canvas)


def main():
    runApp(width=1000, height=650)

if __name__ == '__main__':
    main()