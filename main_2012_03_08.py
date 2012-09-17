import pygame
import random
import math

##########################
# Line of Sight Test:    #
#   Except it turned out #
#   to look better as a  #
#   3d effect.           #
# \author Brian Shaginaw #
##########################

class Surface():
    def __init__(self, pt1, pt2):
        self.pt1 = pt1
        self.pt2 = pt2
        self.delta = (pt2[0]-pt1[0], pt2[1]-pt1[1])
        self.normal = (self.delta[1],-self.delta[0])
        normalize = math.sqrt((self.normal[0]**2)+(self.normal[1]**2))
        self.normal = (self.normal[0]/normalize, self.normal[1]/normalize)
        
    def __str__(self):
        return "SURF"+str((self.pt1, self.pt2))+"ACE "

class Wall():
    # Valid configurations:
    # (x,y) height
    # (x,y) bottom top
    # (x,y,height)
    # (x,y,bottom,top)
    # POINTS MUST BE SET CLOCKWISE :(
    def __init__(self,pt1,pt2,pt3,pt4,height1=None,height2=None):
        self.visible = True # assume drawn, just in case (gets reset pretty immediately anyway).
        if not (len(pt1) == len(pt2) == len(pt3) == len(pt4) or len(pt1) in (2,3,4)):
            raise ValueError("Point tuples must all be the same size (either 2, 3, or 4)")
        self.points = [pt1,pt2,pt3,pt4]
        if not self.check_clockwise(self.points):
            raise ValueError("Points must be clockwise.")
        if height2 == None:
            height2 = height1
            height1 = 1
        #print height1,height2
        if len(pt1)==2:
            if height2==None:
                raise ValueError("You must provide either a flat height or a height for each point.")
            self.points = [(x[0],x[1],height1,height2) for x in self.points]
        elif len(pt1)==3:
            if height1==None:
                raise ValueError("You must provide the correct values I guess. I'm losing track.")
            self.points = [(x[0],x[1],height1,x[2]) for x in self.points]
            #print self.points
        self.raised = height1>1 or (len(pt1)==4 and (pt1[2]>1 or pt2[2]>1 or pt3[2]>1 or pt4[2]>1))
        self.walls = [Surface(a[0], a[1]) for a in zip((pt1,pt2,pt3,pt4), (pt2,pt3,pt4,pt1))]
        
    def base_square(self,(px,py),(sizex,sizey)):
        return [(y[0]+px+sizex/2,y[1]+py+sizey/2) for y in self.points]  # screen location of base square
        
    # the projected tops of the squares: essentially we're projecting a ray from the player to the corners of the base square to a distance of the height of the walls.
    def cap_square(self,(px,py),(sizex,sizey),index=3):
        return [((y[0]-sizex/2)*self.points[i][index]+sizex/2, (y[1]-sizey/2)*self.points[i][index]+sizey/2) for i,y in enumerate(self.base_square((px,py),(sizex,sizey)))]
        
    def check_clockwise(self, pts):
        pts += [pts[0]]
        return sum([(pts[j+1][0]-pt[0])*(pts[j+1][1]+pt[1]) for j,pt in enumerate(pts[:-1])])>0
        
    def recheck_visible(self,(px,py),(sizex,sizey)):
        botsq = self.base_square((px,py),(sizex,sizey))
        result = [1,1,1,1]
        for z in ((y[0]<0, y[1]<0, y[0]>sizex, y[1]>sizey) for y in botsq):
            result = [w and z[i] for i,w in enumerate(result)]
        self.visible = True not in result  # if the object in question is deemed to be off the screen.
        return self.visible
        
    def __str__(self):
        s = []
        for p in zip(*self.points):
            ln = len(str(max(p)))
            s.append([str(i).rjust(ln) for i in p])
        return '\n'.join([', '.join(x) for x in zip(*s)])

pygame.init()

black = (0x00,0x00,0x00)
shade = (0x11,0x11,0x11)
white = (0xFF,0xFF,0xFF)
clear = (0xFF,0x00,0xFF)

size=(500,500)  # size of the screen
px,py = 0,0     # player location


#walls = [Wall((30,0),(30,50),(80,100),(80,0), 3)]
# Position of the walls, this just makes two rows of 5
walls = [Wall((-50+x*150,150-y*250),(-50+x*150,100-y*250),(-100+x*150,100-y*250),(-100+x*150,150-y*250),x+1.1) for x in xrange(5) for y in (0,1)]
walls.append(Wall((700,-300),(700,-350),(-300,-350),(-300,-300),2)) # top
walls.append(Wall((-300,300),(-300,350),(700,350),(700,300),2))     # bottom
# thingy
walls.append(Wall((-350,50,1,2),(-350,350,1,2),(-300,350,1,2),(-300,50,1,2)))
walls.append(Wall((-350,-50,1.5,2),(-350,50,1.5,2),(-300,50,1.5,2),(-300,-50,1.5,2))) # capstone
walls.append(Wall((-300,-350,1,2),(-350,-350,1,2),(-350,-50,1,2),(-300,-50,1,2)))
# endthingy
walls.append(Wall((700,-350),(700,350),(750,350),(750,-350),2))
#walls.append(Wall((700,-350,2,2),(700,350,2,3),(750,350,2,3),(750,-350,2,2)))
walls.append(Wall((-700,-50),(-610,25),(-590,25),(-500,-25),2))

screen=pygame.display.set_mode(size)
cap = pygame.Surface(size)
cap.set_colorkey(clear)

pygame.display.set_caption("Orez Pillars")

done=False
clock = pygame.time.Clock()
step = 3                        # move speed
diagstep = step/math.sqrt(2)    # move speed diagonally
moving = 0                      # direction you are moving
movekeys = {pygame.K_w:1,
            pygame.K_a:2,
            pygame.K_s:4,
            pygame.K_d:8}

# Call this to redraw the scene.
# Redrawing the scene is expensive: only do this when you move or something changes.
def redraw():
    screen.fill(white)
    cap.fill(clear)
    pygame.draw.circle(screen, black, (size[0]/2, size[1]/2), 10)   # Your character, always in the center of the screen.
    for x in walls: # Draw each wall and each wall's 'shadow'
        botsq = x.base_square((-px,-py),size)
        botsc = x.cap_square((-px,-py),size,2)
        
        if not x.recheck_visible((-px,-py),size):
            continue    # well it's not visible.
        
        topsq = x.cap_square((-px,-py),size)
        sx1 = (botsc[0],botsc[2],topsq[2],topsq[0]) # draw a 'plane' from the opposite corners of the base to the cooresponding corners of the top.
        sx2 = (botsc[1],botsc[3],topsq[3],topsq[1]) # same, except the other opposite corners.
        pygame.draw.polygon(screen, black, botsc)
        pygame.draw.polygon(screen, black, sx1  )
        pygame.draw.polygon(screen, black, sx2  )
        pygame.draw.polygon(cap,    shade, topsq)   # draw to the cap layer, so that the caps can all go on last.
    screen.blit(cap,(0,0))

def cross(v,w):
    return (v[0]*w[1])-(v[1]*w[0])
    
def dot(v,w):
    return (v[0]*w[0])+(v[1]*w[1])

# http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
def collision_detection(vector):
    global px,py
    ipts = []
    for x in walls:
        if not x.visible or x.raised:
            continue    # no need to check
        
        for w in x.walls:
            """
            p = w.pt1
            q = (px,py)
            r = w.delta
            s = [vector[0], vector[1]]
            rxs = cross(r,s)
            if not rxs: # parallel
                continue
            qp = (q[0]-p[0], q[1]-p[1])
            t = (cross(qp, s)-0.0)/rxs
            u = (cross(qp, r)-0.0)/rxs
            """
            u = [w.pt2[0]-w.pt1[0], w.pt2[1]-w.pt1[1]]
            t = dot([px-w.pt1[0], py-w.pt1[1]], u)/dot(u,u)
            t = max(0, min(1, t))
            closest = [w.pt1[0]+u[0]*t - px, w.pt1[1]+u[1]*t - py]
            closestv = closest[0]*closest[0] + closest[1]*closest[1]
            #closest = abs(w.normal[0]*(w.pt1[1]+py) - w.normal[1]*(w.pt1[0]+px))
            if 10*10 >= closestv:
                print "hitting",w,"at distance",t,"at offset",closest,"(you're at",px,py,")\n"
            
            #if 0<=t<=1 and 0<=u<=1: # INTERSECT :O
                #print "At",q,",\nstepping",s
                #print "would intersect",w.pt1,w.pt2
                #print "so i push back with force: ",-w.normal[0]*vector[0],-w.normal[1]*vector[1],"\n"
                normalize = math.sqrt(vector[0]*vector[0]+vector[1]*vector[1]);
                vector[0] += w.normal[0]*-normalize
                vector[1] += w.normal[1]*-normalize
                #intersected_loc = (-(p[0]+t*r[0]), -(p[1]+t*r[1]))
                
                #print intersected_loc
                #px,py = intersected_loc
                #print "RAMMED"
                #return
                #ipts.append((u,w.normal,intersected_loc))
    """
    closest = (None,(0,0))
    rest = step
    if ipts:
        closest = min(ipts)
        rest = (closest[0])*step
        px,py = closest[2]
        print "Collide (",px,py,")"
    else:
        print "Not"
    """
    px += vector[0]
    py += vector[1]
    #px += closest[1][0]*rest
    #py += closest[1][1]*rest

"""
def collisionDetection(revert):
    global px,py
    actual = (px,py)
    for x in walls:     # check each wall for collision (obviously)
        if not x.visible or x.raised:    # if the wall isn't even on the screen we don't need to worry about it
            continue    # (the on-the-screen calculation is done in redraw)
        
        hold = [(revert[0],actual[1]),(actual[0],revert[1]),revert] # check y, then x, then default to neither.
        while min(x.points[0][0],x.points[2][0])-5 < -px < max(x.points[0][0],x.points[2][0])+5 and min(x.points[0][1],x.points[2][1])-5 < -py < max(x.points[0][1],x.points[2][1])+5:  # if your projected position is in a wall
            px,py = hold[0] # try a different position
            del hold[0] # and not this position, again.
            if len(hold) == 0:  # if that's the last slot then you shouldn't move, you've been blocked on all sides.
                return
        actual = px,py  # don't check a direction that we know is no good.
"""

redraw()            # initial drawing
while not done:     # main loop
    clock.tick(60)  # 60 fps
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done=True
        elif event.type == pygame.KEYDOWN:
            if event.key in movekeys:
                moving |= movekeys[event.key]   # add your direction to the moving mess.
        elif event.type == pygame.KEYUP:
            if event.key in movekeys:
                moving &= ~movekeys[event.key]  # remove your direction from the moving mess
    
    if moving:
        tm = moving         # temp var: we alter it, but we dont want to alter the original (or we lose keypresses)
        if tm&1 and tm&4:   # moving in two opposite directions in once, take em out
            tm &= ~5        # I recognize this check is done by just adding and subtracting step,
        if tm&2 and tm&8:   # but you would get the wrong speed (the diagonal speed)
            tm &= ~10
            
        tstep = step
        if (tm&5) and (tm&10):   # if you're moving in two cardinal directions, you move slower in each
            tstep = diagstep
        if tm:  # the actual moving.
            vector = [0,0]
            for i,x in enumerate(((0,-tstep),(-tstep,0),(0,tstep),(tstep,0))):  # each direction
                if tm&(2**i):
                    vector[0] += x[0]
                    vector[1] += x[1]
            
            collision_detection(vector)
            redraw()
    
    pygame.display.flip()
