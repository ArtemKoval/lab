# The bar, the elbow, and the whole slide, from the live builders.

from slidecast import scenes

HEADING_FILTER = "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='Queue':expansion=none:fontcolor=0x2BD9A4:fontsize=64:alpha='(t-0.0)/0.5':x='140+80*max(0\\,1-(t-0.0)/0.5)':y=170:enable='gte(t\\,0.0)'"

BOX_IN_SLIDE = "drawbox=x=260:y=333:w=270:h=100:color=0x2BD9A4:t=6:enable='gte(t\\,1.5)',drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='Queue':expansion=none:fontcolor=0xE8EDF2:fontsize=34:alpha='(t-1.65)/0.5':x='280+80*max(0\\,1-(t-1.65)/0.5)':y=363:enable='gte(t\\,1.65)'"

BULLET_IN_SLIDE = "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='- one':expansion=none:fontcolor=0xE8EDF2:fontsize=44:alpha='(t-2.7)/0.5':x='180+80*max(0\\,1-(t-2.7)/0.5)':y=330:enable='gte(t\\,2.7)'"

BAR_FILTER = "drawbox=x=120:y=732:w=520:h=46:color=0x1B3242:t=8:enable='gte(t\\,2.0)',drawbox=x=124:y=736:w=48:h=38:color=0x2BD9A4:t=fill:enable='gte(t\\,2.0 + 0.0)',drawbox=x=176:y=736:w=48:h=38:color=0x2BD9A4:t=fill:enable='gte(t\\,2.0 + 0.12)',drawbox=x=228:y=736:w=48:h=38:color=0x2BD9A4:t=fill:enable='gte(t\\,2.0 + 0.24)',drawbox=x=280:y=736:w=48:h=38:color=0x2BD9A4:t=fill:enable='gte(t\\,2.0 + 0.36)',drawbox=x=332:y=736:w=48:h=38:color=0x2BD9A4:t=fill:enable='gte(t\\,2.0 + 0.48)',drawbox=x=384:y=736:w=48:h=38:color=0x2BD9A4:t=fill:enable='gte(t\\,2.0 + 0.6)',drawbox=x=436:y=736:w=48:h=38:color=0x2BD9A4:t=fill:enable='gte(t\\,2.0 + 0.72)',drawbox=x=488:y=736:w=48:h=38:color=0x2BD9A4:t=fill:enable='gte(t\\,2.0 + 0.84)',drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='accuracy':expansion=none:fontcolor=0xE8EDF2:fontsize=34:alpha='(t-2.0)/0.5':x='120+80*max(0\\,1-(t-2.0)/0.5)':y=682:enable='gte(t\\,2.0)'"

ELBOW_FILTER = "drawbox=x=395:y=415:w=420:h=6:color=0xE8EDF2:t=fill:enable='gte(t\\,3.0)',drawbox=x=812:y=418:w=6:h=266:color=0xE8EDF2:t=fill:enable='gte(t\\,3.0)',drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='►':expansion=none:fontcolor=0xE8EDF2:fontsize=40:alpha='(t-3.1)/0.5':x='815+80*max(0\\,1-(t-3.1)/0.5)':y=684:enable='gte(t\\,3.1)'"

def test_the_bar_with_a_share_of_point_eight_is_exact():
    element = {"kind": "bar", "at": 2.0, "col": 1, "row": 5,
               "label": "accuracy", "share": 0.8}
    assert scenes.bar_filter(element) == BAR_FILTER


def test_the_elbow_arrow_is_exact():
    element = {"kind": "arrow", "at": 3.0, "from": [2, 2], "to": [5, 4]}
    assert scenes.arrow_filter(element) == ELBOW_FILTER



def test_the_whole_slide_composes_in_order():
    filters = scenes.slide_filters(
        "Queue", ["one"],
        [{"kind": "box", "at": 1.5, "col": 2, "row": 2, "label": "Queue"}],
    )
    assert filters == [HEADING_FILTER, BOX_IN_SLIDE, BULLET_IN_SLIDE]
