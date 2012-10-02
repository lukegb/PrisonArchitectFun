from paparse import parse_tree
import json
from pprint import pprint
import PIL.Image

SPRITE_W = 32
SPRITE_H = 32

MATERIAL_W = 64
MATERIAL_H = 64

ROTATETYPE_ALL_ORIENTATIONS = 1
ROTATETYPE_IDENTICAL_HORIZONTAL = 2
ROTATETYPE_ALL_ORIENTATIONS_SAME_DIMS = 3
ROTATETYPE_NO_ROTATION = 4

LINK_CHOOSER = [
  (0, 0, 0, 1, 1, 0, 0, 0, 0),
  (0, 1, 0, 0, 1, 0, 0, 0, 0),
  (0, 0, 0, 0, 1, 1, 0, 0, 0),
  (0, 0, 0, 0, 1, 0, 0, 1, 0),
  (9, 9, 9, 9, 9, 9, 9, 9, 9), #### INVESTIGATE MORE
  (0, 1, 0, 0, 1, 1, 0, 0, 0),
  (0, 0, 0, 0, 1, 1, 0, 1, 0),
  (0, 0, 0, 1, 1, 0, 0, 1, 0),
  (0, 1, 0, 1, 1, 0, 0, 0, 0),
  (0, 1, 0, 0, 1, 0, 0, 1, 0),
  (9, 9, 9, 9, 9, 9, 9, 9, 9), #### INVESTIGATE MORE
  (0, 0, 0, 1, 1, 1, 0, 0, 0),
  (9, 9, 9, 9, 9, 9, 9, 9, 9), #### INVESTIGATE MORE
  (0, 1, 0, 0, 1, 1, 0, 1, 0),
  (0, 0, 0, 1, 1, 1, 0, 1, 0),
  (0, 1, 0, 1, 1, 0, 0, 1, 0),
  (0, 1, 0, 1, 1, 1, 0, 0, 0),
  (0, 1, 0, 1, 1, 1, 0, 1, 0)]

def reorganise_raw_tree(tree, in_plurals):
    new_tree = {}
    for kk, kv in tree.iteritems():
        new_tree[kk] = dict()
        if not in_plurals:
            for v in kv:
                new_tree[kk][v["Name"]] = v
        else:
            no = new_tree[kk]["Objects"] = dict()
            for vk, vv in kv.iteritems():
                if type(vv) is dict and "Name" in vv:
                    vv["_key"] = vk
                    no[vv["Name"]] = vv
                else:
                    new_tree[kk][vk] = vv
    return new_tree

def load_resources(f, reorganise=True, in_plurals=False):
    cache_filename = f.replace("resources/", "resource_cache/")
    # check to see if we have a .json file there already...
    try:
        with open(cache_filename, 'r') as v:
            return json.load(v)
    except:
        pass

    # now load file
    with open(f, 'r') as v:
        tree = parse_tree(v.read())

    # organise tree into a nice dictionary
    if reorganise:
        tree = reorganise_raw_tree(tree, in_plurals)

    # and now save a cache
    try:
        with open(cache_filename, 'w') as v:
            json.dump(tree, v)
    except:
        pass

    return tree

_materials = None
def load_materials():
    global _materials
    if _materials is None:
        _materials = load_resources("resources/materials.txt")
        _materialsb = load_resources("resources/materials-new.txt")
        for k in _materials.keys():
            if k in _materialsb:
                _materials[k].update(_materialsb[k])
    return _materials

_sprite_names = None
def load_sprite_names():
    global _sprite_names
    if _sprite_names is None:
        _sprite_names = load_resources("resources/objects.spritebank", True, True)
    return _sprite_names

def _fetch_sprite_for_object(name, sheet, spritebank):
    # check that we have sprites...
    if spritebank is None or "Sprites" not in spritebank or "Objects" not in spritebank["Sprites"]:
        raise Exception("spritebank has no Sprites!")
    # and now the actual sprite...
    if name not in spritebank["Sprites"]["Objects"]:
        raise Exception("Sprites section has no %s!" % (name,))

    # RotateType notes:
    # 1: Facing towards, Facing away, Facing left, all snapped to BOTTOM EDGE of height-boxthing
    # 2: Facing towards, Facing left - only two available orientations
    # 3: Appears same as 1?
    # 4: No rotation.
    sd = spritebank["Sprites"]["Objects"][name] # Sprite Data
    if "RotateType" not in sd:
        sd["RotateType"] = 4 # no rotation assumed
    if "x" not in sd:
        sd["x"] = 0
    if "y" not in sd:
        sd["y"] = 0
    if "h" not in sd:
        sd["h"] = 1
    if "w" not in sd:
        sd["w"] = 1

    sd["RotateType"], sd["x"], sd["y"], sd["h"], sd["w"] = int(sd["RotateType"]), int(sd["x"]), int(sd["y"]), int(sd["h"]), int(sd["w"])

    # here goes
    # return: u, d, l, r
    x_pos = int(sd["x"]) * SPRITE_W
    y_pos = int(sd["y"]) * SPRITE_H
    sprite_w = int(sd["w"]) * SPRITE_W
    sprite_h = int(sd["h"]) * SPRITE_H
    if sd["RotateType"] == ROTATETYPE_ALL_ORIENTATIONS or sd["RotateType"] == ROTATETYPE_ALL_ORIENTATIONS_SAME_DIMS:
        # get first:
        up = sheet.crop((x_pos, y_pos, sprite_w + x_pos, sprite_h + y_pos))

        x_pos += sprite_w
        down = sheet.crop((x_pos, y_pos, sprite_w + x_pos, sprite_h + y_pos))

        # now the tricky one
        x_pos += sprite_w
        if sd["RotateType"] == ROTATETYPE_ALL_ORIENTATIONS:
            y_pos += sprite_h
            sprite_w, sprite_h = sprite_h, sprite_w
            y_pos -= sprite_h
        left = sheet.crop((x_pos, y_pos, sprite_w + x_pos, sprite_h + y_pos))

        right = left.transpose(PIL.Image.FLIP_LEFT_RIGHT)
    elif sd["RotateType"] == ROTATETYPE_IDENTICAL_HORIZONTAL:
        # get first:
        up = sheet.crop((x_pos, y_pos, sprite_w + x_pos, sprite_h + y_pos))
        down = up

        # now the tricky one
        x_pos += sprite_w
        y_pos += sprite_h
        sprite_w, sprite_h = sprite_h, sprite_w
        y_pos -= sprite_h
        left = sheet.crop((x_pos, y_pos, sprite_w + x_pos, sprite_h + y_pos))

        right = left.transpose(PIL.Image.FLIP_LEFT_RIGHT)
    elif sd["RotateType"] == ROTATETYPE_NO_ROTATION:
        up = sheet.crop((x_pos, y_pos, sprite_w + x_pos, sprite_h + y_pos))
        down = left = right = up
    else:
        raise Exception("Unknown RotateType %s!" % (sd["RotateType"],))
        
    return up, down, left, right

def _fetch_sprite_for_material(name, sheet, mat):
    # returns n squares where n is the area for the material
    if "SpriteType" not in mat:
        mat["SpriteType"] = "Single"
    OK_ST = ("Linked", "RandomArea", "AlignedArea", "Single")
    if mat["SpriteType"] not in OK_ST:
        raise Exception("material %s has unknown SpriteType: %s!" % (name, mat["SpriteType"]))

    # TODO: figure out why this is silly
    if mat["Name"] == "Road":
        mat["SpriteType"] = "Single"

    if mat["SpriteType"] == "RandomArea" or mat["SpriteType"] == "AlignedArea":
        # Sprite0 is coords
        # Sprite1 is width
        base_x = x = int(mat["Sprite0"]["x"])
        base_y = y = int(mat["Sprite0"]["y"])
        final_x = base_x + int(mat["Sprite1"]["x"])
        final_y = base_y + int(mat["Sprite1"]["y"])
        returns = []
        for x in xrange(base_x, final_x):
            for y in xrange(base_y, final_y):
                pixel_x = x * MATERIAL_W
                pixel_y = y * MATERIAL_H
                returns.append(sheet.crop((pixel_x, pixel_y, pixel_x + MATERIAL_W, pixel_y + MATERIAL_H)))
        return returns, mat["SpriteType"]
    elif mat["SpriteType"] == "Linked":
        returns = []
        for n in range(0, 18):
            s = mat["Sprite%d" % (n,)]
            pixel_x = int(s["x"]) * MATERIAL_W
            pixel_y = int(s["y"]) * MATERIAL_H
            returns.append(sheet.crop((pixel_x, pixel_y, pixel_x + MATERIAL_W, pixel_y + MATERIAL_H)))
        return returns, mat["SpriteType"]
    elif mat["SpriteType"] == "Single":
        pixel_x = int(mat["Sprite0"]["x"]) * MATERIAL_W
        pixel_y = int(mat["Sprite0"]["y"]) * MATERIAL_H
        return [sheet.crop((pixel_x, pixel_y, pixel_x + MATERIAL_W, pixel_y + MATERIAL_H))], "Single"
    else:
        raise Exception("material has (2ndc) unknown SpriteType: %s!" % (mat["SpriteType"],))

def select_tile_for_linked(mat):
    # mat is MATRIX
    # LIST of surrounding data
    # 1 = same, 0 = different materials
    # list(0, 1, 0,
    #      0, 1, 1,
    #      0, 0, 0) indicates L shape
    for x in xrange(len(LINK_CHOOSER)):
        xmat = LINK_CHOOSER[x]
        correct = True
        for y in xrange(9):
            if mat[y] != xmat[y]:
                correct = False
                break
        if correct:
            return x
    raise Exception("Bad matrix %s passed to tile selection" % (str(mat),))
    
    

_tileset_sheet = None
_objects_sheet = None
def fetch_sprite(material_type, material_name):
    global _tileset_sheet, _objects_sheet
    mats = load_materials()
    snames = load_sprite_names()
    if _tileset_sheet is None:
        _tileset_sheet = PIL.Image.open("resources/tileset.png", 'r')
    if _objects_sheet is None:
        _objects_sheet = PIL.Image.open("resources/objects.png", 'r')

    # materials are in tileset
    # others are in objects
    if material_type not in _materials:
        raise Exception("Material type %s not found!" % (material_type,))

    mat = mats[material_type]

    # sprite?
    # objects have straight-sprite names
    # materials are trickier
    if material_type == "Object":
        return _fetch_sprite_for_object(mat[material_name]["Sprite"], _objects_sheet, snames)
    elif material_type == "Material":
        return _fetch_sprite_for_material(material_name, _tileset_sheet, mat[material_name])
    else:
        raise Exception("Unsupported material type %s!" % (material_type,))
    
if __name__ == '__main__':
    pprint(load_resources())
