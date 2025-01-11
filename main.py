#######
# ALL OF THIS IS REALLY CRUDE AND REALLY REALLY SHIT
# PLEASE FOR THE LOVE OF ALL THAT IS HOLY, DONT PUSH TO PROD
#######

#######
# KNOWN ISSUE(S):
# ---
# wall order inner-outer-inner and an odd number of walls causes the bricking to be applied to the 2 outer-most inner walls 
#
# some settings will likely break this, but I can't check every single settings,
# so please send error / unexpected behavior reports to Divide#4615 on discord or add an issue in github
######

import os

### debug
DEBUG = False

def namestr(obj, namespace):
    return [name for name in namespace if namespace[name] is obj]

def debug(st:str) -> None:
    if DEBUG:
        print(f"{namestr(st, globals())} || {st}", end="\n")

def soft_debug(st) -> None:
    if DEBUG:
        print(st, end="\n")
### debug end

cur_loc = os.path.dirname(os.path.abspath(__file__))
os.chdir(cur_loc)
debug(cur_loc)

stuff = os.listdir()

for thing in stuff:
    if thing.endswith(".gcode"):
        my_file = f"{cur_loc}\\{thing}"
        debug(my_file)
        break

# find variables
# this is easier if we read the whole file to memory
with open(my_file, "r") as f:
    all_gcode = f.read().split("\n")
    debug(len(all_gcode))


# read the file in reverse to find the config block first and not go through the whole file
n = len(all_gcode)
while True:
    n -= 1
    line = all_gcode[n]
    # init layer height
    if line.startswith("; initial_layer_print_height = "):
        INITIAL_LAYER_HEIGHT = float(line.split(" = ")[1])

    # find layer height
    if line.startswith("; first_layer_height = "):
        LAYER_HEIGHT = float(line.split(" = ")[1])

    # find wall line count
    if line.startswith("; wall_loops = "):
        WALL_COUNT = int(line.split(" = ")[1])

    # top surfaces
    if line.startswith("; top_shell_layers = "):
        TOP_SURFACE_COUNT = int(line.split(" = ")[1])

    # top surfaces
    if line.startswith("; bottom_shell_layers = "):
        BOTTOM_SURFACE_COUNT = int(line.split(" = ")[1])

    # find wall print sequence
    if line.startswith("; wall_sequence"):
        WALL_SEQUENCE = str(line.split(" = ")[1]) 

    # find incompatible settings
    if line == "; spiral_mode = 1" or line == "; alternate_extra_wall = 1" or line == "; enable_arc_fitting = 1":
        print("ERROR: unsupported settings detected")
        exit(1)

    # all info should be listed by now
    if line == "; filament end gcode " or n <= 0:
        if INITIAL_LAYER_HEIGHT == LAYER_HEIGHT:
            break # all is good and saved
        else:
            print("Initial layer height != normal layer height")

            exit(1)

# read it the normal direction to find max_z_height
n=-1
while True:
    n+=1
    line = all_gcode[n]
    # find total object height
    if line.startswith("; max_z_height:"):
        TOTAL_MODEL_HEIGHT = float(line.split(": ")[1])
        break
    
try:
    print("initial layer height:", INITIAL_LAYER_HEIGHT)
    print("layer height:", LAYER_HEIGHT)
    print("wall count:", WALL_COUNT)
    print("wall sequence:", WALL_SEQUENCE)
    print("top surface count:", TOP_SURFACE_COUNT)
    print("bottom surface count:", BOTTOM_SURFACE_COUNT)
    print("total model height:", TOTAL_MODEL_HEIGHT)
except NameError as e:
    print("\n---\n", e, "\n---\n")
    exit(1)


LAYER_HEIGHT_TO_START = LAYER_HEIGHT * BOTTOM_SURFACE_COUNT + LAYER_HEIGHT
LAYER_HEIGHT_TO_STOP = TOTAL_MODEL_HEIGHT - LAYER_HEIGHT * TOP_SURFACE_COUNT


print("start height:", LAYER_HEIGHT_TO_START)
print("stop height:", LAYER_HEIGHT_TO_STOP)

# correct for wall print sequence and wall count
#-if WALL_SEQUENCE == "inner-outer-inner":
#-    flag_alt_wall = WALL_COUNT % 2 == 0
#-elif WALL_SEQUENCE == "outer-inner":
#-    flag_alt_wall = True # outer walls are never given a chance to be raised
#-elif WALL_SEQUENCE == "inner wall/outer wall":
#-    flag_alt_wall = True

# define flags
flag_alt_wall = False 
flag_start = False
flag_stop = False
#-flag_is_elevated = False
flag_first_time = True
flag_start_found = False
flag_stop_found = False




# (this is just a code optimization, it would work with jsut one while loop
# but makes less conditional checks every iteration)
n = 0
cur_type_is_inner_wall = False
while n < len(all_gcode):
    line = all_gcode[n]

    # find start point
    if line.startswith(f";LAYER_CHANGE"):
        if LAYER_HEIGHT_TO_START.is_integer():
            if not flag_start_found and f";Z:{int(LAYER_HEIGHT_TO_START)}" in all_gcode[n+1]:
                START_POINT = n
                flag_start_found = True
        else:
            if not flag_start_found and f";Z:{LAYER_HEIGHT_TO_START}" in all_gcode[n+1]:
                flag_start_found = True
                START_POINT = n

    # verbose comments are added by this script, this is what this reads
    if line.startswith(";TYPE:Inner wall"):
        cur_type_is_inner_wall = True
    elif line.startswith(";TYPE:") and "Inner wall" not in line:
        cur_type_is_inner_wall = False

    # Find travel moves absed on extruder movement rate rather than m204 command (i was dumb)
    # this is still gross though - lol
    if line.startswith("G1") and cur_type_is_inner_wall:
        # check extrusion rate
        if "E" in line.upper():
            # get position of E attribute
            extrusion_rate = None
            e_rate_start = None
            e_rate_stop = None
            for temp_n, char in enumerate(line):
                if char.upper() == "E":
                    e_rate_start = temp_n
                if e_rate_start and char == " " or e_rate_start and temp_n == len(line)-1:
                    e_rate_stop = temp_n
                    break
            try:
                extrusion_rate = float(line[e_rate_start+1:e_rate_stop+1])
            except ValueError as e:
                print(e)
                print("something weird happened - (please report this issue)")
                print(temp_n)
                print(len(line))
                print(n)
                print(all_gcode[n])
                exit(1)
        else: extrusion_rate = 0

        # forcefully comment each time we go between inner wall loops
        if extrusion_rate == 0: # G1 line is travel move, negative E would be retraction
            if all_gcode[n+1].startswith("G1") and ("X" in all_gcode[n+1] or "Y" in all_gcode[n+1]):
                # make sure ;TYPE:Inner wall isn't already set 1 or 2 lines above
                if ";TYPE:Inner" not in all_gcode[n-1] and ";TYPE:Inner" not in all_gcode[n-2]:
                    #-print(n)
                    #-print(all_gcode[n])
                    #-print(all_gcode[n+1])     
                    all_gcode.insert(n+1, ";TYPE:Inner wall")
                    n+=1

    if line.startswith(f";LAYER_CHANGE"):
        if LAYER_HEIGHT_TO_STOP.is_integer():
            if f";Z:{int(LAYER_HEIGHT_TO_STOP)}" in all_gcode[n+1]:
                STOP_POINT = n
                break
        else:
            if f";Z:{int(LAYER_HEIGHT_TO_STOP)}" in all_gcode[n+1]:
                STOP_POINT = n
                break
    n+=1


# read through the file
n = START_POINT
adaptive_stop_point = STOP_POINT
#--next_wall_should_be_brick = not flag_alt_wall
while n < adaptive_stop_point:
    line = all_gcode[n]
    if ";LAYER_CHANGE" in line:
        current_layer_height = float(all_gcode[n+1].split(":")[1])

    # figure out what walls should be changed
    if ";TYPE:Inner wall" in line:
        #--if next_wall_should_be_brick:
        #--    flag_alt_wall = True
        #--    next_wall_should_be_brick = False
        if flag_alt_wall:
            print("!", end="")
            all_gcode.insert(n, f"G1 Z{round(current_layer_height + LAYER_HEIGHT*0.5, 3)} ; BRICK_WALL_ON")
            adaptive_stop_point+=1
            #-flag_is_elevated = True
            flag_alt_wall = False
            n+=1
        else:
            print("?", end="")
            #if flag_is_elevated:
            all_gcode.insert(n, f"G1 Z{current_layer_height} ; BRICK_WALL_OFF")
            adaptive_stop_point+=1
            flag_alt_wall = True
            #-flag_is_elevated = False
            n+=1

    # never brick outer walls
    elif ";TYPE:Outer wall" in line:
        #-if flag_alt_wall: #flag_is_elevated:
            #--next_wall_should_be_brick = True
        print("/", end="")
        all_gcode.insert(n, f"G1 Z{current_layer_height} ; BRICK_WALL_OFF")
        adaptive_stop_point+=1
        flag_alt_wall = not flag_alt_wall
        n+=1
            #-flag_is_elevated = False

    # dont stop bricking because of infill
    # this leads to less weird gcode previews
    # and likely doesn't effect strength much at all
    elif ";TYPE:" in line and "Sparse infill" not in line:
        if flag_is_elevated:
            print("/", end="")
            all_gcode.insert(n, f"G1 Z{current_layer_height} ; BRICK_WALL_OFF")
            adaptive_stop_point+=1
            flag_alt_wall = not flag_alt_wall
            n+=1
            flag_is_elevated = False

    n+=1

# sort all layers by height, ensuring nozzle doesn't hit raised wall when printing non-raised wall

# each "layer" should be from the first time that a layer that's evenly
# divisible by the layer height is mentioned, to the line before the first time
# that the next layer that's evenly divisible by the layer height is mentioned


print("\nDone!")



with open ("./edited.gcode", 'w') as f:
    for line in all_gcode:
        f.write(line)
        f.write("\n")

        
# move all inner walls that are an odd number up by LAYER_HEIGHT*0.5
# maybe increase extrusion by 1.5x for the first time, to prevent gap forming at bottom
# maybe not on the final layer of walls?? (to prevent buldging on top surface)
# this thus-far does not account for anything with more than 1 top surface layer, so basically only primatives
# it's worth noting it likely won't ever, unless I figure out some clever way of fixing that
# probably by going through the gcode in sliding window and doing a lot of re-reading wasting computing time lol
# definetly possible tho, also thankyou to whoever decided that gcode should come with comments all over the place
