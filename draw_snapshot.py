from paparse import parse_save_from_file
import random
import resources
import PIL.Image

CELL_WIDTH = 64
CELL_HEIGHT = 64

def draw_snapshot(paf, outf):
    prison = parse_save_from_file(paf)

    # how big is this?
    cells_wide = int(prison["NumCellsX"])
    cells_high = int(prison["NumCellsY"])

    width = CELL_WIDTH * cells_wide
    height = CELL_HEIGHT * cells_high

    im = PIL.Image.new("RGBA", (width, height))
    background = resources.fetch_sprite("Material", "Dirt")
    cells = prison["Cells"]
    for x in xrange(cells_wide):
        for y in xrange(cells_high):
            if "%d %d" % (x, y) not in cells:
                print "Cell missing: %d %d" % (x, y)
                continue
            c = cells["%d %d" % (x, y)]
            if "Mat" not in c:
                m, t = background
            else:
                m, t = resources.fetch_sprite("Material", c["Mat"])
            d = None
            if t == "Linked":
                d = m[0]
            else:
                d = m[random.randint(0, len(m) - 1)]
            im.paste(d, (x * CELL_WIDTH, y * CELL_HEIGHT))

    im.save(outf)

if __name__ == '__main__':
    draw_snapshot("start01.prison", "start01.png")
