from paparse import parse_save_from_file
import random
import math
import resources
import PIL.Image

DO_NOT_DRAW = ("Stack", "Light", "Prisoner", "FoodTray", "FoodTrayDirty", "Meal", "Garbage", "Rubble")

CELL_WIDTH = 64
CELL_HEIGHT = 64

def build_xy_material_matrix(cells, myx, myy):
    #output = [0, 0, 0, 0, 1, 0, 0, 0, 0]
    output = list()
    mymat = cells["%s %s" % (myx, myy)]["Mat"]
    for y in xrange(myy - 1, myy + 2):
        for x in xrange(myx - 1, myx + 2):
            c = cells["%s %s" % (x, y)]
            if "Mat" not in c:
                output.append(0)
            else:
                # TODO: correct rendering code so that it acts like game - i.e. fences link to walls
                # fetch material
                #_, t = resources.fetch_sprite("Material", c["Mat"])
                #output.append(1 if (t == "Linked") else 0)
                output.append(1 if c["Mat"] == mymat else 0)
    # disregard diagonals:
    output[0] = output[2] = output[-3] = output[-1] = 0
    return output

def xy_to_orientation(x, y):
    # decide which orientation we're in!
    # x = 0, y = 1, DOWN
    # x = 0, y = -1, UP
    # x = 1, y = 0, RIGHT
    # x = -1, y = 0, LEFT
    angle = math.atan2(y, x)
    if y == 0 or x == 0:
        return 0
    quadrant = round(angle/math.pi, 1)
    if quadrant >= -0.25 and quadrant < 0.25:
        return 3
    elif quadrant >= 0.25 and quadrant < 0.75:
        return 0
    elif quadrant >= 0.75 or quadrant < -0.75:
        return 2
    else:
        return 1

def get_z_for_object(object_name):
    # TODO: implement! :)
    return resources.renderdepth_for_object(object_name)

def rescale_image(pilimage, scale_factor):
    return pilimage.resize((pilimage.size[0] * scale_factor, pilimage.size[1] * scale_factor))

def rescale_coordinates(xy, scale_factor):
    return (xy[0] * scale_factor, xy[1] * scale_factor)

def draw_snapshot(prison, max_size=0):
    """ Draw a .prison file represented as Python dictionaries.

    prison parameters is the .prison file Python dictionary representation parameter.

    max_size allows you to specify the maximum number of pixels the image can be along a single axis (if integer).
        If it is an tuple, (width, height), then draw_snapshot will rescale the image to fit within the two parameters """
    # how big is this?
    cells_wide = int(prison["NumCellsX"])
    cells_high = int(prison["NumCellsY"])

    width = CELL_WIDTH * cells_wide
    height = CELL_HEIGHT * cells_high

    scale_factor = 1

    if max_size != 0:
        if type(max_size) is int:
            largest_dimension = max(width, height)
            if largest_dimension == width:
                scale_factor = max_size / width
            else:
                scale_factor = max_size / height
        else:
            max_width, max_height = max_size
            width_sf = max_width / width
            height_sf = max_height / height
            scale_factor = min(width_sf, height_sf)

    width, height = width * scale_factor, height * scale_factor

    im = PIL.Image.new("RGBA", (width, height))

    wall_map = {}

    # draw the background-wall tiles
    background = resources.fetch_sprite("Material", "Dirt")
    cells = prison["Cells"]
    objects_to_draw = dict()
    objects_to_draw[-5] = dict()
    for x in xrange(cells_wide):
        for y in xrange(cells_high):
            cell_name = "%d %d" % (x, y)
            if cell_name not in cells:
                print "Cell missing: %s" % (cell_name,)
                continue
            c = cells[cell_name]
            if "Mat" not in c:
                m, t = background
            else:
                m, t = resources.fetch_sprite("Material", c["Mat"])
            d = None
            if t == "Linked":
                # build x-y matrix of positions
                xy_mat = build_xy_material_matrix(cells, x, y)
                sel_tile = resources.select_tile_for_linked(xy_mat)
                d = m[sel_tile]
                wall_map[cell_name] = dict(sprite=d, coords=(x * CELL_WIDTH, y * CELL_HEIGHT))
            else:
                d = m[random.randint(0, len(m) - 1)]

            #im.paste(d, (x * CELL_WIDTH, y * CELL_HEIGHT))
            if y not in objects_to_draw[-5]:
                objects_to_draw[-5][y] = list()
            objects_to_draw[-5][y].append((d, (x * CELL_WIDTH, y * CELL_HEIGHT), d))

    # now overlay objects
    objects = prison["Objects"]
    for i, obj in objects.iteritems():
        if not i.startswith("[i") or not i.endswith("]"):
            continue

        if obj["Type"] in DO_NOT_DRAW:
            continue

        pos_y = float(obj["Pos.y"])
        pos_z = get_z_for_object(obj["Type"])

        if pos_z not in objects_to_draw:
            objects_to_draw[pos_z] = dict()

        if pos_y not in objects_to_draw[pos_z]:
            objects_to_draw[pos_z][pos_y] = list()
        
        objects_to_draw[pos_z][pos_y].append(obj)

    for k in sorted(objects_to_draw.keys()):
        objs_y = objects_to_draw[k]

        for ky in sorted(objs_y.keys()):
            for obj in objs_y[ky]:
                if k != -5:
                    coords = float(obj["Pos.x"]), float(obj["Pos.y"])
                    # fetch object sprite
                    object_sprites = resources.fetch_sprite("Object", obj["Type"])
                    if "Or.x" not in obj:
                        obj["Or.x"] = 0
                    if "Or.y" not in obj:
                        obj["Or.y"] = 0
                    
                    obj["Or.x"], obj["Or.y"] = float(obj["Or.x"]), float(obj["Or.y"])
                    orient = xy_to_orientation(obj["Or.x"], obj["Or.y"])
                    s = object_sprites[orient]
                    sprite_w, sprite_h = s.size
                    pixel_pos = (int(coords[0] * CELL_WIDTH - sprite_w / 2), int(coords[1] * CELL_HEIGHT - sprite_h / 2))
                    im.paste(rescale_image(s, scale_factor), rescale_coordinates(pixel_pos, scale_factor), rescale_image(s, scale_factor))

                    # is this sprite going to draw atop a wall?
                    # if so, NO! BAD SPRITE.
                    #top_cell_y = int(math.floor(coords[1]))
                    bottom_cell_y = int(math.ceil((pixel_pos[1] + sprite_h) / CELL_HEIGHT))
                    left_cell_x = int(math.floor(pixel_pos[0] / CELL_HEIGHT))
                    right_cell_x = int(left_cell_x + math.ceil(sprite_w / CELL_WIDTH))
                    c_y = bottom_cell_y
                    for c_x in xrange(left_cell_x, right_cell_x + 1):
                        # is this cell a wall?
                        c_n = "%d %d" % (c_x, c_y)
                        if c_n in wall_map: # yes
                            # redraw the wall!
                            im.paste(rescale_image(wall_map[c_n]["sprite"], scale_factor), rescale_coordinates(wall_map[c_n]["coords"], scale_factor))
                else:
                    im.paste(rescale_image(obj[0], scale_factor), rescale_coordinates(obj[1], scale_factor), rescale_image(obj[1], scale_factor))
    return im

if __name__ == '__main__':
    i = draw_snapshot(parse_save_from_file("start01.prison"))
    SF = 2
    #i = i.resize((i.size[0] / 2, i.size[1] / 2))
    i.save("start01.png")
