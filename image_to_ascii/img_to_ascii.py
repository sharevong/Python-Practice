from PIL import Image
import argparse

"""
图片转字符画
运行方式：
transform.py wm.png -o output.txt --> 输出图片的字符画为文件
transform.py wm.png -o output.txt --width 80 --height 60  --> 指定输出字符画的宽度和高度
"""

# 输入参数解析
parser = argparse.ArgumentParser()
parser.add_argument('file')
parser.add_argument('-o', '--output', default='output.txt')
parser.add_argument('--width', type=int, default=80)
parser.add_argument('--height', type=int, default=80)

args = parser.parse_args()
IMG = args.file
OUTPUT = args.output
WIDTH = args.width
HEIGHT = args.height


# 字符画使用的字符集
ascii_char = list("$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. ")


# rgb值转灰度值，计算公式参考以下资料
# https://www.zhihu.com/question/22039410
# https://en.wikipedia.org/wiki/Grayscale
def get_char(r, g, b, alpha=256):
    if alpha == 0:  # 像素透明度为0时返回空格符
        return ' '
    length = len(ascii_char)
    gray = int(0.2126*r + 0.7152*g + 0.0722*b)
    # gray = int(0.299*r + 0.587*g + 0.114*b)
    unit = (256.0+1) / length
    return ascii_char[int(gray/unit)]


if __name__ == '__main__':
    # pillow文档：https://pillow.readthedocs.io/en/5.1.x/
    im = Image.open(IMG)
    print(im.mode)
    # Image.NEAREST表示图片缩放取样时取最近的像素点
    im = im.resize((WIDTH, HEIGHT), Image.NEAREST)
    
    text = ''
    for i in range(HEIGHT):
        for j in range(WIDTH):
            # getpixel返回值与图片格式有关，本例假设图片为RGBA编码，返回r g b 透明度四个值
            text += get_char(*im.getpixel((j, i)))
        text += '\n'

    with open(OUTPUT, 'w') as f:
        f.write(text)
