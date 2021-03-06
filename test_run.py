#!/usr/bin/python
#!/usr/bin/python
#
# libtcod python tutorial
#
 
import libtcodpy as libtcod
import math
import textwrap
import shelve
import random
 
#actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
 
#size of the map portion shown on-screen
CAMERA_WIDTH = 80
CAMERA_HEIGHT = 43
 
#size of the map
MAP_WIDTH = 100
MAP_HEIGHT = 100
 
#sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
 
#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 50
MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2
 
#spell values
HEAL_AMOUNT = 4
LIGHTNING_DAMAGE = 20
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 10
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 12
 
 
FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 20

LIMIT_FPS = 20  #20 frames-per-second maximum
 
spaceColours = {
                    'space'                     :   libtcod.Color( 8,8,8 ), 
                    'space_hidden'              :   libtcod.black,
                    'space_hidden_planet'       :   libtcod.Color( 2,2,2 ),
                    'asteroid'                  :   libtcod.lightest_sepia,
                    'asteroid_bg'               :   libtcod.darker_sepia,
                    'asteroid_hidden'           :   libtcod.dark_sepia,
                    'asteroid_hidden_bg'        :   libtcod.darkest_sepia,
                    'asteroid_floor'            :   libtcod.sepia,
                    'asteroid_floor_bg'         :   libtcod.dark_sepia,
                    'asteroid_floor_bg_hidden'  :   libtcod.black
}

ship = {
            'geometry'                  :   [   
                                                [205, 187, ' ', 218 ,205 , 191, ' ', ' ', ' ', ' ', ' ', ' '], 
                                                [' ', 195, 196, 217, '#', 192, 196, 196, 196, 196, 191, ' '], 
                                                [' ', 180, '#', '#', '#', '#', '#', 10, '#', '#', 192, 191], 
                                                [205, 180, '#', '#', '#', '#', '#', '#', '#', 192, '#', 179], 
                                                [' ', 180, '#', '#', '#', '#', '#', '#', '#', '#', 218, 217], 
                                                [' ', 195, 196, 191, '#', 218, 196, 196, 196, 196, 217, ' '], 
                                                [205, 188, ' ', 192, 205 , 217, ' ', ' ', ' ', ' ', ' ', ' ']
                                            ],

            'colour_map'                :   [
                                                ['engine',  'hull', ' ',        'hull',     'door',    'hull',    ' ',    ' ',    ' ',    ' ',    ' ',    ' '], 
                                                [' ',       'hull', 'hull',     'hull',     'floor',   'hull',    'hull',    'hull',    'hull',    'hull',    'hull',    ' '], 
                                                [' ',       'hull', 'floor',     'floor',    'floor',   'floor',   'floor',  'computer','floor',   'floor',   'window',    'window'], 
                                                ['engine',  'hull', 'floor',    'floor',    'floor',   'floor',   'floor',   'floor',   'floor',   'floor',   'floor',     'window'], 
                                                [' ',       'hull', 'floor',    'floor',    'floor',   'floor',   'floor',   'floor',   'floor',   'floor',   'window',    'window'], 
                                                [' ',       'hull', 'hull',     'hull',     'floor',   'hull',    'hull',    'hull',    'hull',    'hull',    'hull',    ' '], 
                                                ['engine',  'hull', ' ',        'hull',     'door',    'hull',    ' ',    ' ',    ' ',    ' ',    ' ',    ' ']            
                                            ],   

            'colours'                   :   {
                                                'engine'
                                                            :   {
                                                                'colour'    :   libtcod.blue,
                                                                'colour_bg' :   libtcod.light_blue
                                                            },
                                                'hull' 
                                                            :   {
                                                                'colour'    :   libtcod.grey,
                                                                'colour_bg' :   libtcod.darkest_grey
                                                            },
                                                'floor'                                                   
                                                            :   {
                                                                'colour'    :   libtcod.grey,
                                                                'colour_bg' :   libtcod.darker_grey
                                                            },
                                                'computer'                                                   
                                                            :   {
                                                                'colour'    :   libtcod.lightest_green,
                                                                'colour_bg' :   libtcod.white
                                                            },
                                                'window'
                                                            :   {
                                                                'colour'    :   libtcod.dark_cyan,
                                                                'colour_bg' :   libtcod.darkest_cyan
                                                            },
                                                'door'
                                                            :   {
                                                                'colour'    :   libtcod.darkest_red,
                                                                'colour_bg' :   libtcod.dark_red
                                                            }
                                            }
}

class Tile( ):
    #A tile of the map and its properties
    def __init__( self, blocked, name = None, space = False, planet = False, x = 0, y = 0,
                    char = ' ', colour = spaceColours['space'], colour_bg = spaceColours['space'], 
                    colour_hidden = libtcod.dark_grey, colour_hidden_bg = spaceColours['space_hidden'],
                    block_sight = None, tile_behaviour = None ):

        self.name = name
        self.blocked = blocked
        self.char = char
        self.explored = False
        # self.x = x
        # self.y = y
        self.space = space
        self.planet = planet
        self.colour = colour
        self.colour_bg = colour_bg
        self.colour_hidden = colour_hidden
        self.colour_hidden_bg = colour_hidden_bg

        if self.colour_hidden == 'normal_darken':
            self.colour_hidden = colour
            libtcod.color_scale_HSV(self.colour_hidden, 1, 1)

        self.tile_behaviour = tile_behaviour
        if self.tile_behaviour != None:
            self.tile_behaviour.owner = self

        #By default, if a tile is blocked, it also blocks sight:
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight


######################################################
#                  TILE BEHAVIOUR
######################################################

class Door(  ):
    def __init__( self, doorRange = 2, alwaysVisible = True ):  #Door 'AI'
        self.doorRange = doorRange
        self.alwaysVisible = alwaysVisible

    #Door tile_behaviour component for a tile
    def take_turn( self ):
        global map, fov_recompute

        object_map_pos = to_camera_coordinates(self.owner.x, self.owner.y)

        #Update the tile when needed
        if ( self.owner.distance_to( player ) <= self.doorRange):
            self.owner.char = '-'
            self.owner.blocks = False
            fov_recompute = True

        else:
            self.owner.char = 205
            self.owner.blocks = True
            fov_recompute = True

class Rect( ):
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = int(x)
        self.y1 = int(y)
        self.x2 = int(x + w)
        self.y2 = int(y + h)
 
    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)
 
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Circle( Rect ):
    def __init__( self, x, y, radius ):
        self.x = x
        self.y = y
        self.radius = radius
        Rect.__init__( self, self.x, self.y, self.radius * 2, self.radius * 2)

    def inCircle( self, x, y ):
        centreX, centreY = self.center()
        if  math.sqrt( (x - centreX) ** 2 + ( y - centreY ) ** 2 ) < self.radius:
            return True

    def distanceFromCentre( self, x, y ):
        centreX, centreY = self.center()
        return  math.sqrt( (x - centreX) ** 2 + ( y - centreY ) ** 2 )
            
class Ellipse( ):
    def __init__( self, mx, my, rh, rv ):
                #midX midY, radius Horizonal, radius Vertical

        self.mx = mx
        self.my = my
        self.rh = rh
        self.rv = rv

    def pointFromAngle( self, a ):
        c = math.cos(a)
        s = math.sin(a)
        ta = s / c
        tt = ta * self.rh / self.rv
        d = 1. / math.sqrt(1. + tt * tt)
        x = self.mx + math.copysign(self.rh * d, c)
        y = self.my + math.copysign(self.rv * tt * d, s)
        return int(x), int(y) 

    def pointInEllipse( self, xp, yp, angle = 0 ):
        #tests if a point[xp,yp] is within
        #boundaries defined by the ellipse
        #of center[x,y], diameter d D, and tilted at angle

        x = self.mx
        y = self.my
        d = self.rh
        D = self.rv

        cosa=math.cos(angle)
        sina=math.sin(angle)
        dd=d/2*d/2
        DD=D/2*D/2

        a =math.pow(cosa*(xp-x)+sina*(yp-y),2)
        b =math.pow(sina*(xp-x)-cosa*(yp-y),2)
        ellipse=(a/dd)+(b/DD)

        if ellipse <= 1:
            return True
        else:
            return False

class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__( self, x, y, char, name, colour, colour_bg = None, blocks = False, fighter = None, ai = None, item = None ):
        self.x = int(x)
        self.y = int(y)
        self.char = char
        self.name = name
        self.colour = colour
        self.colour_bg = colour_bg
        self.blocks = blocks
        self.fighter = fighter

        if self.fighter:  #let the fighter component know who owns it
            self.fighter.owner = self
 
        self.ai = ai
        if self.ai:  #let the AI component know who owns it
            self.ai.owner = self
 
        self.item = item
        if self.item:  #let the Item component know who owns it
            self.item.owner = self
 
    def move( self, dx, dy ):
        #Collision Check
        if not is_blocked( int(self.x + dx),  int(self.y + dy)):
            self.x += dx
            self.y += dy
 
    def move_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
 
        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)
 
    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
 
    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
 
    def send_to_back( self ):
        #Make this object be drawn first, so all others appear above it if they're in the same tile
        global objects
        objects.remove( self )
        objects.insert( 0, self )
 
    def draw( self ):
        #only show if it's visible to the player
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            (x, y) = to_camera_coordinates( self.x, self.y)

            if x is not None:   #Only draw if it's on screen
                #Set the colour and then draw the character that represents this object at its position
                libtcod.console_set_char_foreground( con, int(x), int(y), self.colour )
                libtcod.console_put_char( con, int(x), int(y), self.char, libtcod.BKGND_NONE )

                if self.colour_bg != None:
                    libtcod.console_set_char_background( con, int(x), int(y), self.colour_bg, libtcod.BKGND_SET )
                else:
                    libtcod.console_set_char_background( con, int(x), int(y), libtcod.black, libtcod.BKGND_SET )
        elif self.ai.alwaysVisible:
            (x, y) = to_camera_coordinates( self.x, self.y)
            if x is not None:
                libtcod.console_put_char_ex(con, int(x), int(y), self.char, self.colour, libtcod.BKGND_NONE)

    def clear(self):
        #erase the character that represents this object
        (x, y) = to_camera_coordinates(self.x, self.y)
        if x is not None:
            libtcod.console_put_char(con, int(x), int(y), ' ', libtcod.BKGND_NONE)
 
class Fighter:
    #combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, defense, power, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function
 
    def attack(self, target):
        #a simple formula for attack damage
        damage = self.power - target.fighter.defense
 
        if damage > 0:
            #make the target take some damage
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')
 
    def take_damage(self, damage):
        #apply damage if possible
        if damage > 0:
            self.hp -= damage
 
            #check for death. if there's a death function, call it
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner)
 
    def heal(self, amount):
        #heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
 
class BasicMonster:
    #AI for a basic monster.
    def take_turn(self):
        #a basic monster takes its turn. if you can see it, it can see you
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
 
            #move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
 
            #close enough, attack! (if the player is still alive.)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)
 
class ConfusedMonster:
    #AI for a temporarily confused monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns
 
    def take_turn(self):
        if self.num_turns > 0:  #still confused...
            #move in a random direction, and decrease the number of turns confused
            self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
 
        else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)
 
class Item:
    #an item that can be picked up and used.
    def __init__(self, use_function=None):
        self.use_function = use_function
 
    def pick_up(self):
        #add to the player's inventory and remove from the map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)
 
    def drop(self):
        #add to the map and remove from the player's inventory. also, place it at the player's coordinates
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)
 
    def use(self):
        #just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner)  #destroy after use, unless it was cancelled for some reason

def make_ship( pos_x, pos_y ):
    global map, tiles

    for y in range(len(ship['geometry'])):
        for x in range(len(ship['geometry'][y])):
            if ship['geometry'][y][x] != ' ':           #If it's not a blank tile

                map_x = pos_x + x
                map_y = pos_y + y

                map[map_x][map_y].char = ship['geometry'][y][x] #Change the map tile to the ship object

                #Set tile type
                map[map_x][map_y].type = ship['colour_map'][y][x]
                map[map_x][map_y].explored = True #We already know our ship
                # map[map_x][map_y].space = False

                if map[map_x][map_y].type == 'hull':
                    #Set up the base hull
                    map[map_x][map_y].blocked = True
                    map[map_x][map_y].block_sight = True

                elif map[map_x][map_y].type == 'window':
                    #Set up Windows
                    map[map_x][map_y].blocked = True

                elif map[map_x][map_y].type == 'door':
                    #Set up Doors
                    ship_door = Object( map_x, map_y, map[map_x][map_y].char, 'Door', colour = libtcod.light_grey, ai = Door( ) )
                    objects.append( ship_door )

                #Set tile colours
                map[map_x][map_y].colour = ( ship['colours'][map[map_x][map_y].type]['colour'] )

def is_blocked( x, y ):
    #first test the map tile
    if map[x][y].blocked:
        return True

    #now check for any objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False
 
def create_room(room):
    global map
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False

def create_asteroid( asteroid, numImpacts = None, impactRadius = None, monster_nest = True ):
    #Create an asteroid shape from a circle
    #Take the input circle, and cut out other circles from it (impact craters)

    global map

    monster_nest_locations = []

    #Setup asteroid base data
    for x in range( asteroid.x1, asteroid.x2 ):
        for y in range( asteroid.y1, asteroid.y2 ):
            if asteroid.inCircle( x, y ):
                if x < MAP_WIDTH and y < MAP_HEIGHT:
                    map[x][y].name = 'Asteroid rock'
                    map[x][y].space = False
                    map[x][y].blocked = True
                    map[x][y].block_sight = True
                    map[x][y].char = '#'
                    map[x][y].colour = spaceColours['asteroid']
                    map[x][y].colour_hidden = spaceColours['asteroid_hidden']
                    map[x][y].colour_bg = spaceColours['asteroid_bg']
                    map[x][y].colour_hidden_bg = spaceColours['asteroid_hidden_bg']

    #setup 'impacts'
    if numImpacts == None:
        #If no impacts are specified, work out a value based off the size of the asteroid
        numImpacts = int(asteroid.radius * 1.4)

    i = 0
    while i < numImpacts:
        #Get random map position in circle and check it's at the edge
        cX = libtcod.random_get_int( 0, asteroid.x1, asteroid.x2 )
        cY = libtcod.random_get_int( 0, asteroid.y1, asteroid.y2 )

        if asteroid.inCircle( cX, cY ) and (asteroid.distanceFromCentre( cX, cY ) < (asteroid.radius + 1)) and (asteroid.distanceFromCentre( cX, cY ) > (asteroid.radius - 1)):
            #Valid position found

            #If no impact radius specified, generate a random size per impact
            if impactRadius == None:
                thisImpactRadius = int(libtcod.random_get_int( 0, int(asteroid.radius * 0.1), int(asteroid.radius * 0.5)))
            else:
                thisImpactRadius = impactRadius

            #Create a circle 'impact' and subtract it from the map
            impact = Circle( cX, cY, thisImpactRadius )
            for x in range(impact.x1, impact.x2):
                for y in range(impact.y1, impact.y2):
                    if impact.inCircle( x, y ):
                        if x < MAP_WIDTH and y < MAP_HEIGHT:
                            map[x][y].name = 'Asteroid rock floor'
                            map[x][y].char = random.choice( [';', ',', '.'] )
                            map[x][y].colour_bg = spaceColours['asteroid_floor_bg']
                            map[x][y].blocked = False
                            map[x][y].block_sight = False

                            if asteroid.inCircle(x, y):
                                #Add the point of the impact to the monster_nest_locations
                                monster_nest_locations.append((x, y))
            i += 1

    if monster_nest and len(monster_nest_locations) > 0:
        monster_nest_point = random.choice(monster_nest_locations)
        create_monster_nest( monster_nest_point[0], monster_nest_point[1] )

def create_monster_nest( x, y, growLength = 5 ):
    global map

    map[x][y].colour_bg = libtcod.light_green
    map[x][y].name = 'Creature Nest'

    stopChance = 0
    growTiles = getAdjacentTiles(map, x, y)

    while random.random() > stopChance:
        newGrowTiles = []

        for t in growTiles:
            if random.random() < 0.5:
                map[t[0]][t[1]].colour += libtcod.green
                map[t[0]][t[1]].colour_bg += libtcod.darkest_green
                map[t[0]][t[1]].name = 'Creature Nest'
                for nT in getAdjacentTiles(map, t[0], t[1]):
                    if nT != (x, y):
                        newGrowTiles.append(nT)

        growTiles = newGrowTiles

        stopChance += 0.2


def create_h_tunnel(x1, x2, y):
    global map
    #horizontal tunnel. min() and max() are used in case x1>x2
    for x in range( int(min(x1, x2)), int(max(x1, x2) + 1)):
        map[x][int(y)].blocked = False
        map[x][int(y)].block_sight = False
 
def create_v_tunnel(y1, y2, x):
    global map
    #vertical tunnel
    for y in range( int(min(y1, y2)),  int(max(y1, y2) + 1)):
        map[int(x)][y].blocked = False
        map[int(x)][y].block_sight = False

def getAdjacentTiles( map, x, y, notChar = ' ' ):
    tiles = []
    for grid in [ (x+1, y+0), (x+1, y+1), (x+0, y+1), (x-1, y+1), (x-1, y+0), (x-1, y-1), (x+0, y-1), (x+1, y-1) ]:
        if map[grid[0]][grid[1]].char != notChar:
            tiles.append( grid )

    return tiles

def randomColourRange( inColourMin = [0,0,0], inColourMax = [255,255,255] ):
    return libtcod.Color(   random.randint( inColourMin[0], inColourMax[0] ),
                            random.randint( inColourMin[1], inColourMax[1] ),
                            random.randint( inColourMin[2], inColourMax[2] )
                        )

def make_starfield():
    global map_bg, tiles

    star_chars = [' '] * 30
    star_chars.append( '*' )
    star_chars.append( '.' )
    star_colours = [ libtcod.light_grey, libtcod.dark_grey, libtcod.grey ] * 50
    star_colours.append( libtcod.light_cyan )
    star_colours.append( libtcod.lightest_cyan )
    star_colours.append( libtcod.darkest_cyan )
    star_colours.append( libtcod.Color(20,10,10) )

    map_bg = [[Tile(False, char = random.choice(star_chars), colour = random.choice(star_colours), colour_bg = spaceColours['space'], colour_hidden = libtcod.darker_grey, colour_hidden_bg = spaceColours['space_hidden'] )
                for y in range(CAMERA_HEIGHT) ]
                    for x in range(CAMERA_WIDTH) ]

def planet_colours( planetType = 'moon' ):
    #Create the colours for the planet / moon

    pCX = 0
    pCY = 0
    pCZ = 0
    #Get base colour and derive everything from there

    if planetType == 'moon':
        #we're going for greyscale.  We don't differentiate between actual planets/moons just colours.  A moon like IO would be a planet, it's coloured
        colour = random.choice( [ (120,120,120), (70,70,70), (100,100,100) ] )
    else:
        colour = random.choice( [ (255,0,0), (0,255,0), (0,0,255) ] )

    colour_bg = (int(colour[0] * 0.5), int(colour[1] * 0.5), int(colour[2] * 0.5))
    return (
            libtcod.Color(colour[0], colour[1], colour[2]), 
            libtcod.Color(colour_bg[0], colour_bg[1], colour_bg[2])
            )

def setMapColours( map, x, y, colour ):
    map[x][y].colour = colour
    map[x][y].colour_bg = colour
    map[x][y].colour_hidden = colour
    map[x][y].colour_hidden_bg = colour

def dot(vA, vB):
    return vA[0]*vB[0]+vA[1]*vB[1]

def ang(lineA, lineB):
    # Get nicer vector form
    vA = [(lineA[0][0]-lineA[1][0]), (lineA[0][1]-lineA[1][1])]
    vB = [(lineB[0][0]-lineB[1][0]), (lineB[0][1]-lineB[1][1])]
    # Get dot prod
    dot_prod = dot(vA, vB)
    # Get magnitudes
    magA = dot(vA, vA)**0.5
    magB = dot(vB, vB)**0.5
    # Get cosine value
    cos_ = dot_prod/magA/magB
    # Get angle in radians and then convert to degrees
    angle = math.acos(dot_prod/magB/magA)
    # Basically doing angle <- angle mod 360
    ang_deg = math.degrees(angle)%360

    if ang_deg-180>=0:
        # As in if statement
        return 360 - ang_deg
    else: 

        return ang_deg

def make_planet( ):
    global map_planet, ship

    map_planet = [[Tile(False, char = ' ', colour = libtcod.Color(40,40,50), colour_bg = libtcod.Color(12,12,20), colour_hidden = libtcod.Color(30,30,40), colour_hidden_bg = libtcod.Color(12,12,12) )
                for y in range(int(MAP_HEIGHT * 2)) ]
                    for x in range(int(MAP_WIDTH * 2)) ]

    planet = Circle(10, 10, random.randrange(10,40))

    planet_colour, planet_colour_bg = planet_colours( random.choice(['moon', 'planet']) )
    planet_centre = planet.center()

    planet_shadow_side = random.choice([0,1,2,3,4])

    if planet_shadow_side != 4:
        #If the planet is lit front on we dont need the ellipse calcs
        planet_shadow_ellipse = Ellipse(planet_centre[0], planet_centre[1], (planet.radius * random.uniform(1, 1.9)), planet.radius * 2)
        planet_shadow_ellipse_points = []

        for a in range(360):
            planet_shadow_ellipse_points.append(planet_shadow_ellipse.pointFromAngle(a))

    for x in range( planet.x1, planet.x2 ):
        for y in range( planet.y1, planet.y2 ):
            if planet.inCircle(x, y):
                if x < MAP_WIDTH and x > 0 and y < MAP_HEIGHT and y > 0:
                    map_planet[x][y].block_sight = False
                    map_planet[x][y].blocked = False
                    map_planet[x][y].char = random.choice(['#', '&', '%'])

                    #Gradient coef for shading the planet
                    gradient_coef = clamp((planet.distanceFromCentre(x, y) / planet.radius), 0, 0.9)

                    #Colour in the planet
                    map_planet[x][y].colour = libtcod.color_lerp( planet_colour, spaceColours['space'], gradient_coef )
                    map_planet[x][y].colour_bg = libtcod.color_lerp( planet_colour_bg, spaceColours['space'], gradient_coef )
                    map_planet[x][y].colour_hidden = libtcod.color_lerp( map_planet[x][y].colour_hidden, spaceColours['space'], gradient_coef )
                    map_planet[x][y].colour_hidden_bg = libtcod.color_lerp( map_planet[x][y].colour_hidden_bg, spaceColours['space'], gradient_coef )

                    #If it's in the shadow of the sun, make it dark, or it's full lit
                    if planet_shadow_side <= 1:
                        #Most of the planet is in light
                        if planet_shadow_side == 0:
                            if not planet_shadow_ellipse.pointInEllipse(x, y) and x >= planet_centre[0]:
                                setMapColours(map_planet, x, y, spaceColours['space_hidden_planet'])
                        elif planet_shadow_side == 1:
                            if not planet_shadow_ellipse.pointInEllipse(x, y) and x <= planet_centre[0]:
                                setMapColours(map_planet, x, y, spaceColours['space_hidden_planet'])
                    elif planet_shadow_side <= 3:
                        #Most of it is in shadow, making a crescent
                        if planet_shadow_side == 2:
                            if planet_shadow_ellipse.pointInEllipse(x, y) or x >= planet_centre[0]:
                                setMapColours(map_planet, x, y, spaceColours['space_hidden_planet'])
                        elif planet_shadow_side == 3:
                            if planet_shadow_ellipse.pointInEllipse(x, y) or x <= planet_centre[0]:
                                setMapColours(map_planet, x, y, spaceColours['space_hidden_planet'])
                    
def clamp(inV, inMin, inMax):
    return max(inMin, min(inV, inMax))

def make_dust():

    global map

    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            if random.random() < 0.01:
                
                # if map_planet[x][y].char != ' ':
                #     map[x][y].colour_bg = map_planet[x][y].colour_bg

                map[x][y].char = '.'
                map[x][y].colour = libtcod.Color( random.randint(50,80), random.randint(50,80), random.randint(50,80) )
                map[x][y].name = 'dust'

def make_map():
    global map, objects, tiles
    
    #the list of objects with just the player
    objects = [player]
    tiles = []
 
    #fill map with "blocked" tiles
    map = [[ Tile(False)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]

    make_starfield()
    make_planet()
    make_dust()

    asteroids = []
    num_asteroids = 0

    MAX_ASTEROIDS = 5   

    for a in range( MAX_ASTEROIDS ):
        #Random radius
        radius = libtcod.random_get_int( 0, 2, 10 )
        x = libtcod.random_get_int( 0, 0, MAP_WIDTH - radius * 3 )
        y = libtcod.random_get_int( 0, 0, MAP_HEIGHT - radius * 3 )
        new_asteroid = Circle( x, y, radius )

        asteroids.append(create_asteroid(new_asteroid))

    player_ship = Rect( player.x + 10, player.y, 10, 10)

    ship_x, ship_y = 15, 15
    make_ship( ship_x, ship_y )

    player.x = ship_x + 9
    player.y = ship_y + 3
 
def place_objects(room):
    #choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)
 
    for i in range(num_monsters):
        #choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not is_blocked(x, y):
            if libtcod.random_get_int(0, 0, 100) < 80:  #80% chance of getting an orc
                #create an orc
                fighter_component = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
                ai_component = BasicMonster()
 
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green,
                    blocks=True, fighter=fighter_component, ai=ai_component)
            else:
                #create a troll
                fighter_component = Fighter(hp=16, defense=1, power=4, death_function=monster_death)
                ai_component = BasicMonster()
 
                monster = Object(x, y, 'T', 'troll', libtcod.darker_green,
                    blocks=True, fighter=fighter_component, ai=ai_component)
 
            objects.append(monster)
 
    #choose random number of items
    num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)
 
    for i in range(num_items):
        #choose random spot for this item
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not is_blocked(x, y):
            dice = libtcod.random_get_int(0, 0, 100)
            if dice < 70:
                #create a healing potion (70% chance)
                item_component = Item(use_function=cast_heal)
 
                item = Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)
            elif dice < 70+10:
                #create a lightning bolt scroll (10% chance)
                item_component = Item(use_function=cast_lightning)
 
                item = Object(x, y, '#', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)
            elif dice < 70+10+10:
                #create a fireball scroll (10% chance)
                item_component = Item(use_function=cast_fireball)
 
                item = Object(x, y, '#', 'scroll of fireball', libtcod.light_yellow, item=item_component)
            else:
                #create a confuse scroll (10% chance)
                item_component = Item(use_function=cast_confuse)
 
                item = Object(x, y, '#', 'scroll of confusion', libtcod.light_yellow, item=item_component)
 
            objects.append(item)
            item.send_to_back()  #items appear below other objects
 
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)
 
    #render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
 
    #now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
 
    #finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, int(x + total_width / 2), y, libtcod.BKGND_NONE, libtcod.CENTER,
        name + ': ' + str(value) + '/' + str(maximum))
 
def get_names_under_mouse():
    global mouse
 
    #return a string with the names of all objects under the mouse
    (x, y) = (mouse.cx, mouse.cy)
    (x, y) = (int(camera_x + x), int(camera_y + y))  #from screen to map coordinates
 
    #create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, int(obj.x), int(obj.y))]
 
    #Check if the tile under the mouse has a name and add it if it's valid
    for map_x in range(MAP_WIDTH):
        for map_y in range(MAP_HEIGHT):
            if map[x][y].name != None and libtcod.map_is_in_fov( fov_map, x, y ) and map[x][y].name not in names:
                names.append( map[x][y].name )

    names = ', '.join(names)  #join the names, separated by commas
    return names.capitalize()
 
def move_camera(target_x, target_y):
    global camera_x, camera_y, fov_recompute
 
    #new camera coordinates (top-left corner of the screen relative to the map)
    x = int(target_x - CAMERA_WIDTH / 2)  #coordinates so that the target is at the center of the screen
    y = int(target_y - CAMERA_HEIGHT / 2)
 
    #make sure the camera doesn't see outside the map
    if x < 0: x = 0
    if y < 0: y = 0
    if x > MAP_WIDTH - CAMERA_WIDTH - 1: x = MAP_WIDTH - CAMERA_WIDTH - 1
    if y > MAP_HEIGHT - CAMERA_HEIGHT - 1: y = MAP_HEIGHT - CAMERA_HEIGHT - 1
 
    if x != camera_x or y != camera_y: fov_recompute = True
 
    (camera_x, camera_y) = (x, y)
 
def to_camera_coordinates(x, y):
    #convert coordinates on the map to coordinates on the screen
    (x, y) = (x - camera_x, y - camera_y)
 
    if (x < 0 or y < 0 or x >= CAMERA_WIDTH or y >= CAMERA_HEIGHT):
        return (None, None)  #if it's outside the view, return nothing
 
    return (x, y)

def render_all():
    global fov_map, fov_recompute, dungeon_level
  
    move_camera(player.x, player.y)

    if fov_recompute:

        #recompute FOV if needed (the player moved or something)
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, int(player.x), int(player.y), TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        libtcod.console_clear(con)

        # libtcod.console_set_default_background(con, libtcod.black)
        # libtcod.console_set_char_foreground(con, x, y, col)
        
        #Render star field
        for y in range(CAMERA_HEIGHT):
            for x in range(CAMERA_WIDTH):
                (map_x, map_y) = (int(camera_x + x), int(camera_y + y))
                visible = libtcod.map_is_in_fov(fov_map, map_x, map_y)

                if visible:
                    libtcod.console_put_char_ex(con, x, y, map_bg[x][y].char, map_bg[x][y].colour, map_bg[x][y].colour_bg)
                else:
                    libtcod.console_put_char_ex(con, x, y, map_bg[x][y].char, map_bg[x][y].colour_hidden, map_bg[x][y].colour_hidden_bg)
        
        #Render planet
        for y in range(CAMERA_HEIGHT):
            for x in range(CAMERA_WIDTH):
                # (map_x, map_y) = (int(camera_x + x), int(camera_y + y)) #Map-Space
                (map_x, map_y) = (int(camera_x + x - player.x * 0.2), int(camera_y + y - player.y * 0.2)) #Offset

                visible = libtcod.map_is_in_fov(fov_map, int(camera_x + x), int(camera_y + y))

                if map_planet[map_x][map_y].char != ' ':
                    if visible:
                        libtcod.console_put_char_ex(con, x, y, map_planet[map_x][map_y].char, map_planet[map_x][map_y].colour, map_planet[map_x][map_y].colour_bg)
                    else:
                        libtcod.console_put_char_ex(con, x, y, map_planet[map_x][map_y].char, map_planet[map_x][map_y].colour_hidden, map_planet[map_x][map_y].colour_hidden_bg)
        
        #go through all tiles, and set their background color according to the FOV
        for y in range(CAMERA_HEIGHT):
            for x in range(CAMERA_WIDTH):
                (map_x, map_y) = (int(camera_x + x), int(camera_y + y))
                visible = libtcod.map_is_in_fov(fov_map, map_x, map_y)
 
                if not visible:
                    #if it's not visible right now, the player can only see it if it's explored
                    if map[map_x][map_y].explored:
                        if map[map_x][map_y].char != ' ':
                            libtcod.console_put_char_ex(con, x, y, map[map_x][map_y].char, map[map_x][map_y].colour_hidden, map[map_x][map_y].colour_hidden_bg )
                else:
                    #it's visible
                    if map[map_x][map_y].char != ' ':
                        libtcod.console_put_char_ex(con, x, y, map[map_x][map_y].char, map[map_x][map_y].colour, map[map_x][map_y].colour_bg )
                    #since it's visible, explore it
                    map[map_x][map_y].explored = True

    #draw all objects in the list, except the player. we want it to
    #always appear over all other objects! so it's drawn later.
    for object in objects:
        if object != player:
            object.draw()
    player.draw()
 
    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
 
    #prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
 
    #print the game messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1
 
    #show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)
 
    #display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
 
    #blit the contents of "panel" to the root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

 
def message(new_msg, color = libtcod.white):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
 
        #add the new line as a tuple, with the text and the color
        game_msgs.append( (line, color) )
        
def player_move_or_attack( dx, dy ):
    global fov_recompute

    #Coordinates the player is moving to, or attacking
    x = player.x + dx
    y = player.y + dy

    #Try to find an atttackable object there
    target = None
    for object in objects:
        #Check if object has a fighter component, and if it's where we want to move to
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    #attack the target found, move otherwise
    if target is not None:
        #Attack
        player.fighter.attack(target)
    elif x >= MAP_WIDTH - 1 or x < 0 or y >= MAP_HEIGHT - 1 or y < 0:
        #Edge of world, display message
        message( 'Nothing but billions of lightyears of space in this direction...', libtcod.yellow )
    else:
        player.move(dx, dy)
        fov_recompute = True

def menu( header, options, width, yOffset = 0 ):

    if len(options) > 26: raise ValueError('Menu cannot have more than 26 options.')

    #Calculate total height for the header ( after, auto-wrap )
    header_height = libtcod.console_get_height_rect( con, 0, 0, width, SCREEN_HEIGHT, header )
    if header == '':
        header_height = 0
    height = len(options) + header_height

    #Create an off screen console that represents the menu's window
    window = libtcod.console_new( width, height )

    #print the header, with auto-wrap
    libtcod.console_set_default_foreground( window, libtcod.white )
    libtcod.console_print_rect_ex( window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header )

    #print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '({letter_index}) {option_text}'.format( letter_index = chr(letter_index), option_text = option_text )
        libtcod.console_print_ex( window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text )
        y += 1
        letter_index += 1

    #blit the contenst of the "window" to the root console
    x = int(SCREEN_WIDTH / 2 - width / 2)
    y = int(SCREEN_HEIGHT / 2 - height / 2)
    libtcod.console_blit( window, 0, 0, width, height, 0, x, y + yOffset, 1.0, 0.7 )

    #present the root console to the player and wait for a key press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)

    #Waiting for key press.
    #Convert the ASCII code to an index; if it corresponds to an item, return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index

def inventory_menu(header):
    #show a menu with each item of the inventory as an option
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in inventory]
 
    index = menu(header, options, INVENTORY_WIDTH)
 
    #if an item was chosen, return it
    if index is None or len(inventory) == 0: return None
    return inventory[index].item
 
def msgbox(text, width=50):
    menu(text, [], width)  #use menu() as a sort of "message box"
 
######################################################
#                       INPUT
######################################################

def handle_keys():
    global fov_recompute, game_state, key

    if key.vk == libtcod.KEY_ESCAPE:
        return 'exit' #Exit

    if game_state == 'playing':
        #Movement Keys
        if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
            player_move_or_attack( 0, -1 )
            fov_recompute = True
        elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
            player_move_or_attack( 0, 1 )
            fov_recompute = True
        elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
            player_move_or_attack( -1, 0 )
            fov_recompute = True
        elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
            player_move_or_attack( 1, 0 )
            fov_recompute = True
        elif key.vk ==  libtcod.KEY_KP7:
            player_move_or_attack( -1, -1 )
            fov_recompute = True
        elif key.vk ==  libtcod.KEY_KP9:
            player_move_or_attack( 1, -1 )
            fov_recompute = True
        elif key.vk ==  libtcod.KEY_KP3:
            player_move_or_attack( 1, 1 )
            fov_recompute = True
        elif key.vk ==  libtcod.KEY_KP1:
            player_move_or_attack( -1, 1 )
            fov_recompute = True
        else:
            #check for other keys
            key_char = chr( key.c )

            if key_char == 'g':
                #pick up an item
                for object in objects:  #look for an item under the player
                    if object.x == player.x and object.y == player.y and object.item:
                        object.item.pick_up()
                        break
            elif key_char == 'i':
                #show the inventory
                chosen_item = inventory_menu( 'Press the key next to an item to use it, or any other to cancel.\n' )
                if chosen_item is not None:
                    chosen_item.use()
            elif key_char == 'd':
                #Drop an item from your inventory
                chosen_item = inventory_menu( 'Press the key next to an item to drop it, or any other to cancel.\n' )
                if chosen_item is not None:
                    chosen_item.drop()
            elif key_char == '<':
                #Go down stairs
                if stairs.x == player.x and stairs.y == player.y:
                    next_level()

            return 'no_turn'
 
def player_death(player):
    #the game ended!
    global game_state
    message('You died!', libtcod.red)
    game_state = 'dead'
 
    #for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red
 
def monster_death(monster):
    #transform it into a nasty corpse! it doesn't block, can't be
    #attacked and doesn't move
    message(monster.name.capitalize() + ' is dead!', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()
 
def target_tile(max_range=None):
    #return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
    global key, mouse
    while True:
        #render the screen. this erases the inventory and shows the names of objects under the mouse.
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse) 
        render_all()
        (x, y) = (mouse.cx, mouse.cy)
        (x, y) = (camera_x + x, camera_y + y)  #from screen to map coordinates
 
        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)  #cancel if the player right-clicked or pressed Escape
 
        #accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
            (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)
 
def target_monster(max_range=None):
    #returns a clicked monster inside FOV up to a range, or None if right-clicked
    while True:
        (x, y) = target_tile(max_range)
        if x is None:  #player cancelled
            return None
 
        #return the first clicked monster, otherwise continue looping
        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj
 
def closest_monster(max_range):
    #find closest enemy, up to a maximum range, and in the player's FOV
    closest_enemy = None
    closest_dist = max_range + 1  #start with (slightly more than) maximum range
 
    for object in objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
            #calculate distance between this object and the player
            dist = player.distance_to(object)
            if dist < closest_dist:  #it's closer, so remember it
                closest_enemy = object
                closest_dist = dist
    return closest_enemy
 
def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health.', libtcod.red)
        return 'cancelled'
 
    message('Your wounds start to feel better!', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)
 
def cast_lightning():
    #find closest enemy (inside a maximum range) and damage it
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:  #no enemy found within maximum range
        message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'
 
    #zap it!
    message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
        + str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)
 
def cast_fireball():
    #ask the player for a target tile to throw a fireball at
    message('Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)
 
    for obj in objects:  #damage every fighter in range, including the player
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
            obj.fighter.take_damage(FIREBALL_DAMAGE)
 
def cast_confuse():
    #ask the player for a target to confuse
    message('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None: return 'cancelled'
 
    #replace the monster's AI with a "confused" one; after some turns it will restore the old AI
    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster  #tell the new component who owns it
    message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', libtcod.light_green)
 
 
def save_game():
    #open a new empty shelve (possibly overwriting an old one) to write the game data
    file = shelve.open('savegame', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)  #index of player in objects list
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file.close()
 
def load_game():
    #open the previously saved shelve and load the game data
    global map, objects, player, stairs, inventory, game_msgs, game_state
 
    file = shelve.open('savegame', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']]  #get index of player in objects list and access it
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    file.close()
 
    initalise_FOV()
 
def new_game():
    global player, inventory, game_msgs, game_state
 
    #create object representing the player
    fighter_component = Fighter(hp=30, defense=2, power=5, death_function=player_death)
    player = Object(0, 0, '@', 'player', colour = libtcod.white, colour_bg = None, blocks=True, fighter=fighter_component)
 
    #generate map (at this point it's not drawn to the screen)
    make_map()
    initalise_FOV()
 
    game_state = 'playing'
    inventory = []
 
    #create the list of game messages and their colors, starts empty
    game_msgs = []
 
    #a warm welcoming message!
    message('Don\'t forget to breathe', libtcod.red)
 
def initalise_FOV():
    global fov_recompute, fov_map
    fov_recompute = True

    #Create a field of view map according to the generated map
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
 
def play_game():
    global key, mouse, camera_x, camera_y, fov_recompute

    player_action = None

    (camera_x, camera_y) = ( 0, 0 )

    while not libtcod.console_is_window_closed():
        #Render the screen
        libtcod.sys_check_for_event( libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse )
        render_all()

        libtcod.console_flush()

        #erase all objects at their old locations, before they move
        for object in objects:
            object.clear()

        #Handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break

        #let monsters take their turn and update tile behaviours
        if game_state == 'playing' and player_action != 'no_turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()
            for tile in tiles:
                if tile.tile_behaviour:
                    tile.tile_behaviour.update()

def main_menu():
    img = libtcod.image_load( b'menu_background.png' )

    while not libtcod.console_is_window_closed():
        #show the background image, at twice regular console resolution
        libtcod.image_blit_2x(img, 0, 0, 0)

        #Show the game title and some credits!
        libtcod.console_set_default_foreground( 0, libtcod.light_yellow )
        libtcod.console_print_ex(   0, int(SCREEN_WIDTH / 2), int(SCREEN_HEIGHT / 2 + 12), libtcod.BKGND_NONE, libtcod.CENTER,
                                    b'SALVAGE' )
        libtcod.console_print_ex(   0, int(SCREEN_WIDTH / 2), int(SCREEN_HEIGHT - 2), libtcod.BKGND_NONE, libtcod.CENTER,
                                    b'gibbonofdoom'  )

        #show options and wait for player's choice
        choice = menu( '', ['Play a new game', 'Continue last game', 'Quit'], 24, yOffset = 16 )

        if choice == 0:     #new game
            new_game()
            play_game()
        elif choice == 1:   #load game
            try:
                load_game()
                play_game()
            except:
                msg_box('\n No saved game to load.\n', 24)
                continue
        elif choice == 2:   #quit
            break

#############################################
#############################################

#Screen Data
libtcod.console_set_custom_font( b'arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD )
libtcod.console_init_root( SCREEN_WIDTH, SCREEN_HEIGHT, title = b'Salvage', fullscreen =False )

#Consoles
con = libtcod.console_new( SCREEN_WIDTH, SCREEN_HEIGHT )
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

#Mouse input
mouse = libtcod.Mouse()
key = libtcod.Key()

#Set frame limit
libtcod.sys_set_fps( LIMIT_FPS )

main_menu()

#############################################
#############################################