# The exact render commands, regenerated from the live builders.

from slidecast import render

TITLE_COMMAND = [
    'ffmpeg',
    '-y',
    '-f',
    'lavfi',
    '-i',
    'color=c=0x10202B:s=1920x1080',
    '-vframes',
    '1',
    '-vf',
    "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='T':fontcolor=0x2BD9A4:fontsize=88:x=(w-text_w)/2:y=(h-text_h)/2-70,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='S':fontcolor=0xE8EDF2:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2+60",
]

def test_the_title_command_is_exact():
    assert render.draw_title('T', 'S') == TITLE_COMMAND
