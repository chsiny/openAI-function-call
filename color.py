def rgb_to_color_code(rgb: tuple[int]):
    """
    transfer rgb to desygner's color code

    @test
    rgb = (255, 240, 240) -> color_code = 15790335
    """
    r, g, b = rgb
    return b * 65536 + g * 256 + r

def rgb_to_hex(rgb: tuple):
    return "#%02x%02x%02x" % rgb
