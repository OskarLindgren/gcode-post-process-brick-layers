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

cur_loc = os.path.dirname(os.path.abspath(__file__))
os.chdir(cur_loc)

stuff = os.listdir()

for thing in stuff:
    if thing.endswith(".gcode"):
        my_file = f"{cur_loc}\{thing}"
        break

# find variables
# this is easier if we read the whole file to memory
with open(my_file, "r") as f:
    all_gcode = f.read().split("\n")


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
        WALL_SEQUENCE = str(line.split(" = ")[1].split(" ")[0]) 

    # find incompatible settings
    if line == "; spiral_mode = 1" or line == "; alternate_extra_wall = 1":
        print("ERROR: cringe settings detected")
        exit(1)

    # all info should be listed by now
    if line == "; filament end gcode " or n <= 0:
        if INITIAL_LAYER_HEIGHT == LAYER_HEIGHT:
            break # all is good and saved
        else:
            print("Initial layer height != normal layer height")

            exit(1)

# read it the normal direction to find max_z_heaight
n=-1
while True:
    n+=1
    line = all_gcode[n]
    # find total object height
    if line.startswith("; max_z_height:"):
        # after model is done, z is increased by 2mm
        TOTAL_MODEL_HEIGHT = float(line.split(": ")[1])
        break

print("initial layer height:", INITIAL_LAYER_HEIGHT)
print("layer height:", LAYER_HEIGHT)
print("wall count:", WALL_COUNT)
print("wall sequence:", WALL_SEQUENCE)
print("top surface count:", TOP_SURFACE_COUNT)
print("bottom surface count:", BOTTOM_SURFACE_COUNT)
print("total model height:", TOTAL_MODEL_HEIGHT)


LAYER_HEIGHT_TO_START = LAYER_HEIGHT * BOTTOM_SURFACE_COUNT + LAYER_HEIGHT
LAYER_HEIGHT_TO_STOP = TOTAL_MODEL_HEIGHT - LAYER_HEIGHT * TOP_SURFACE_COUNT


print("start height:", LAYER_HEIGHT_TO_START)
print("stop height:", LAYER_HEIGHT_TO_STOP)

# do every other wall, correcting for wall print sequence and wall count
#-if WALL_SEQUENCE == "inner-outer-inner":
#-    flag_first_wall = WALL_COUNT % 2 == 0
#-elif WALL_SEQUENCE == "outer-inner":
#-    flag_first_wall = True # outer walls are never given a chance to be raised
#-elif WALL_SEQUENCE == "inner-outer":
#-    flag_first_wall = WALL_COUNT % 2 == 0

# define flags
flag_alt_wall = True #flag_first_wall 
flag_start = False
flag_stop = False
flag_is_elevated = False
flag_first_time = True




# find start point
# (this is just a code optimization, it does the same thing as earlier version
# but makes less conditional checks every iteration)
n = 0
cur_type_is_inner_wall = False
while n < len(all_gcode):
    line = all_gcode[n]

    if line.startswith(f";LAYER_CHANGE"):
        if LAYER_HEIGHT_TO_START.is_integer():
            if f";Z:{int(LAYER_HEIGHT_TO_START)}" in all_gcode[n+1]:
                START_POINT = n
        else:
            if f";Z:{LAYER_HEIGHT_TO_START}" in all_gcode[n+1]:
                START_POINT = n

    # forcefully comment each time we go between inner wall loops
    if line.startswith(";TYPE:Inner wall"):
        cur_type_is_inner_wall = True
    elif line.startswith(";TYPE:") and "Inner wall" not in line:
        cur_type_is_inner_wall = False

    # THIS IS SO GROSS AND DEPENDS ON THE TRAVEL PATH BETWEEN WALLS AND SLICER SETTINGS, EW
    if line.startswith("M204 ") and cur_type_is_inner_wall:
        #-print("!")
        if all_gcode[n-1].startswith("G1 ") and all_gcode[n-2].startswith("M204 "):
            if not all_gcode[n+1].startswith(";TYPE:"):
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
next_wall_should_be_brick = False
while n < adaptive_stop_point:
    #-print(n)
    line = all_gcode[n]
    if ";LAYER_CHANGE" in line:
        current_layer_height = float(all_gcode[n+1].split(":")[1])

    # figure out what walls should be changed
    if ";TYPE:Inner wall" in line:
        if next_wall_should_be_brick:
            flag_alt_wall = True
            next_wall_should_be_brick = False
        if flag_alt_wall:
            print("!", end="")
            all_gcode.insert(n, f"G1 Z{round(current_layer_height + LAYER_HEIGHT*0.5, 3)} ; BRICK_WALL_ON")
            adaptive_stop_point+=1
            flag_is_elevated = True
            flag_alt_wall = False
            n+=1
        else:
            print("?", end="")
            if flag_is_elevated:
                all_gcode.insert(n, f"G1 Z{current_layer_height} ; BRICK_WALL_OFF")
                adaptive_stop_point+=1
                flag_alt_wall = True
                flag_is_elevated = False
                n+=1

    # never brick outer walls
    elif ";TYPE:Outer wall" in line:
        if flag_is_elevated:
            next_wall_should_be_brick = True
            print("/", end="")
            all_gcode.insert(n, f"G1 Z{current_layer_height} ; BRICK_WALL_OFF")
            adaptive_stop_point+=1
            flag_alt_wall = not flag_alt_wall
            n+=1
            flag_is_elevated = False

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
