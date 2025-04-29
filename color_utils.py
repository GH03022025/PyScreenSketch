import re
from lxml import etree


def hex_pattern():
    return re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


def rgb_pattern():
    return re.compile(r"^rgb$\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$$")


def hex_to_rgb(hex_clr: str) -> tuple:
    hex_clr = hex_clr.lstrip("#")
    return tuple(int(hex_clr[i : i + 2], 16) for i in (0, 2, 4))


def parse(clr: str) -> tuple:
    if not clr:
        return None

    if hex_pattern().match(clr):
        return hex_to_rgb(clr)

    if rgb_pattern().match(clr):
        return tuple(map(int, rgb_pattern().match(clr).groups()))


def get_luminance(rgb: tuple) -> float:
    r, g, b = [x / 255.0 for x in rgb]
    return 0.299 * r + 0.587 * g + 0.114 * b


def adjust_luminance(rgb, luminance, luma_thresh=0):
    clr_luma = get_luminance(rgb)

    if clr_luma >= luma_thresh:
        ratio = luminance
        new_rgb = (int(max(0, min(255, rgb[i] * ratio))) for i in range(3))
    else:
        ratio = 1.0 - luminance
        new_rgb = (
            int(max(0, min(255, rgb[i] + (255 - rgb[i]) * ratio))) for i in range(3)
        )

    return new_rgb


def recolor_svg(svg_root, color):
    rgb = parse(color)
    if not rgb:
        raise ValueError("Invalid color format")

    luminance = get_luminance(rgb)  #
    print(f"Target color: {rgb}, Luminance: {luminance * 100:.1f}%")

    color_attrs = ["fill", "stroke", "stop-color", "flood-color", "lighting-color"]

    for element in svg_root.xpath(
        "//*[@fill or @stroke or @stop-color or @flood-color or @lighting-color]"
    ):
        for attr in color_attrs:
            if attr in element.attrib:
                original_rgb = parse(element.attrib[attr])

                if not original_rgb:
                    continue
                else:
                    original_luminance = get_luminance(original_rgb)

                new_rgb = adjust_luminance(rgb, original_luminance, 0.25)
                new_rgb = "rgb({},{},{})".format(*new_rgb)

                element.set(attr, new_rgb)


input_svg = "C:\\Users\\Lenovo\\Desktop\\input.svg"  # 输入SVG文件路径
output_svg = "C:\\Users\\Lenovo\\Desktop\\output.svg"  # 输出SVG文件路径
color = "#00ff00"  # 十六进制颜色

parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse(input_svg, parser)
root = tree.getroot()

recolor_svg(root, color)
tree.write(output_svg, pretty_print=True, encoding="utf-8", xml_declaration=True)
