from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import re

WIDTH, HEIGHT = 1920, 1080
IMAGE_DIR = Path("output/images")

THEMES = {
    "forest": ((105,190,230),(30,105,72),(35,130,75),(25,105,60)),
    "village": ((255,190,120),(145,80,65),(190,130,75),(125,75,45)),
    "river": ((115,205,235),(20,105,155),(45,150,130),(25,105,125)),
    "mountain": ((145,195,245),(75,95,135),(105,135,120),(65,90,100)),
    "night": ((35,45,100),(15,20,55),(45,75,80),(25,45,65)),
    "garden": ((255,205,150),(65,145,100),(80,165,75),(45,120,65)),
}

def find_font(size):
    for f in ("C:/Windows/Fonts/mangal.ttf","C:/Windows/Fonts/Nirmala.ttf",
              "C:/Windows/Fonts/arial.ttf",
              "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"):
        if Path(f).exists():
            try: return ImageFont.truetype(f,size)
            except OSError: pass
    return ImageFont.load_default()

def scene_text_value(scene):
    if isinstance(scene, dict):
        return str(scene.get("description") or scene.get("visual") or scene.get("text") or scene)
    return str(scene)

def choose_theme(text, index):
    t = text.lower()
    tests = [
        ("night",("रात","चाँद","चांद","तारा","अंधेरा","night","moon")),
        ("river",("नदी","तालाब","झरना","पानी","समुद्र","river","water","पी रहा","पी रही")),
        ("mountain",("पहाड़","पहाड़","पर्वत","बर्फ","mountain","snow")),
        ("village",("गाँव","गांव","घर","किसान","बाजार","village","house")),
        ("garden",("फूल","बगीचा","बाग","garden","flower")),
        ("forest",("जंगल","पेड़","पेड़","वन","forest","rabbit","खरगोश","deer","हिरण")),
    ]
    for theme, words in tests:
        if any(w in t for w in words): return theme
    return list(THEMES)[index % len(THEMES)]

def detect_animals(text):
    t = text.lower()
    found = []
    terms = [
        ("rabbit",("rabbit","खरगोश","खरगोशी")),
        ("deer",("deer","हिरण","मृग")),
        ("bird",("bird","birds","चिड़िया","चिड़िया","पक्षी","तोता","कबूतर","मोर")),
        ("elephant",("elephant","हाथी")),
        ("monkey",("monkey","बंदर","बन्दर")),
        ("fox",("fox","लोमड़ी","लोमड़ी","सियार")),
        ("lion",("lion","शेर","सिंह")),
        ("turtle",("turtle","कछुआ")),
        ("squirrel",("squirrel","गिलहरी")),
        ("bear",("bear","भालू")),
        ("cow",("cow","गाय")),
        ("dog",("dog","कुत्ता","कुत्ते")),
        ("cat",("cat","बिल्ली")),
        ("mouse",("mouse","चूहा","चूहे")),
        ("frog",("frog","मेंढक")),
    ]
    for animal, words in terms:
        if any(w in t for w in words):
            found.append(animal)
    if not found:
        found = ["rabbit"]
    return found[:3]

def draw_rabbit(d,cx,cy,s,pose,seed):
    fur=(248,239,220,255); outline=(105,82,65,255)
    shirts=[(55,135,220,255),(235,95,90,255),(70,170,115,255),(155,100,205,255)]
    d.ellipse((cx-100*s,cy-5*s,cx+100*s,cy+205*s),fill=fur,outline=outline,width=max(3,int(5*s)))
    d.rounded_rectangle((cx-88*s,cy+65*s,cx+88*s,cy+180*s),radius=int(35*s),fill=shirts[seed%4])
    tilt=[-18,0,18][pose%3]
    d.ellipse((cx-78*s+tilt*s,cy-230*s,cx-18*s+tilt*s,cy-35*s),fill=fur,outline=outline,width=max(3,int(5*s)))
    d.ellipse((cx+18*s-tilt*s,cy-240*s,cx+78*s-tilt*s,cy-35*s),fill=fur,outline=outline,width=max(3,int(5*s)))
    d.ellipse((cx-110*s,cy-125*s,cx+110*s,cy+65*s),fill=fur,outline=outline,width=max(3,int(5*s)))
    d.ellipse((cx-58*s,cy-45*s,cx-34*s,cy-10*s),fill=(30,30,35,255))
    d.ellipse((cx+34*s,cy-45*s,cx+58*s,cy-10*s),fill=(30,30,35,255))
    d.ellipse((cx-13*s,cy+2*s,cx+13*s,cy+20*s),fill=(225,110,130,255))
    d.arc((cx-30*s,cy+15*s,cx+30*s,cy+65*s),10,170,fill=outline,width=max(3,int(5*s)))

def draw_deer(d,cx,cy,s,pose,seed):
    coat=(177,112,65,255); dark=(92,55,35,255); cream=(245,220,185,255)
    # legs, body, neck, head
    for lx in (-55,35):
        d.rounded_rectangle((cx+lx*s,cy+85*s,cx+(lx+22)*s,cy+260*s),radius=int(8*s),fill=dark)
    d.ellipse((cx-105*s,cy-15*s,cx+105*s,cy+145*s),fill=coat,outline=dark,width=max(3,int(5*s)))
    d.polygon([(cx+35*s,cy+40*s),(cx+95*s,cy-125*s),(cx+150*s,cy-145*s),(cx+130*s,cy+75*s)],fill=coat)
    d.ellipse((cx+75*s,cy-190*s,cx+220*s,cy-45*s),fill=coat,outline=dark,width=max(3,int(5*s)))
    # ears
    d.ellipse((cx+80*s,cy-220*s,cx+150*s,cy-160*s),fill=coat)
    d.ellipse((cx+170*s,cy-215*s,cx+240*s,cy-155*s),fill=coat)
    # antlers
    for ax in (cx+115*s,cx+185*s):
        d.line((ax,cy-180*s,ax-12*s,cy-275*s),fill=dark,width=max(4,int(10*s)))
        d.line((ax-8*s,cy-235*s,ax-55*s,cy-270*s),fill=dark,width=max(3,int(8*s)))
        d.line((ax-10*s,cy-245*s,ax+30*s,cy-285*s),fill=dark,width=max(3,int(8*s)))
    d.ellipse((cx+125*s,cy-145*s,cx+145*s,cy-115*s),fill=(25,25,30,255))
    d.ellipse((cx+178*s,cy-95*s,cx+208*s,cy-70*s),fill=(35,25,25,255))
    for sx,sy in [(-35,30),(0,45),(40,15)]:
        d.ellipse((cx+sx*s,cy+sy*s,cx+(sx+12)*s,cy+(sy+12)*s),fill=cream)

def draw_bird(d,cx,cy,s,pose,seed):
    colors=[(70,155,220,255),(235,175,55,255),(90,175,110,255),(190,100,170,255)]
    body=colors[seed%len(colors)]
    d.ellipse((cx-95*s,cy-55*s,cx+95*s,cy+75*s),fill=body,outline=(45,55,65,255),width=max(3,int(4*s)))
    # wing changes direction with pose
    if pose%2==0:
        d.ellipse((cx-60*s,cy-70*s,cx+35*s,cy+40*s),fill=(245,225,190,255))
    else:
        d.polygon([(cx-35*s,cy-20*s),(cx-170*s,cy-125*s),(cx-100*s,cy+55*s)],fill=(245,225,190,255))
    d.ellipse((cx+35*s,cy-105*s,cx+125*s,cy-15*s),fill=body)
    d.ellipse((cx+85*s,cy-80*s,cx+100*s,cy-60*s),fill=(20,20,25,255))
    d.polygon([(cx+115*s,cy-65*s),(cx+175*s,cy-45*s),(cx+115*s,cy-25*s)],fill=(245,155,40,255))
    d.line((cx-20*s,cy+65*s,cx-30*s,cy+110*s),fill=(210,135,45,255),width=max(3,int(6*s)))
    d.line((cx+25*s,cy+65*s,cx+20*s,cy+110*s),fill=(210,135,45,255),width=max(3,int(6*s)))

def draw_other(d,animal,cx,cy,s,seed):
    # Simple distinct silhouettes for additional story animals.
    palette={"elephant":(135,145,160,255),"monkey":(145,90,55,255),"fox":(220,115,55,255),
             "lion":(205,160,65,255),"turtle":(65,145,85,255),"squirrel":(175,105,60,255),
             "bear":(130,85,55,255),"cow":(235,235,220,255),"dog":(180,135,90,255),
             "cat":(180,170,160,255),"mouse":(160,155,165,255),"frog":(85,175,80,255)}
    col=palette.get(animal,(150,150,150,255)); outline=(65,55,50,255)
    d.ellipse((cx-100*s,cy-5*s,cx+105*s,cy+175*s),fill=col,outline=outline,width=max(3,int(5*s)))
    d.ellipse((cx-85*s,cy-145*s,cx+85*s,cy+20*s),fill=col,outline=outline,width=max(3,int(5*s)))
    d.ellipse((cx-48*s,cy-95*s,cx-25*s,cy-65*s),fill=(25,25,30,255))
    d.ellipse((cx+25*s,cy-95*s,cx+48*s,cy-65*s),fill=(25,25,30,255))
    if animal=="elephant":
        d.arc((cx+30*s,cy-10*s,cx+130*s,cy+155*s),270,90,fill=col,width=max(12,int(30*s)))
        d.ellipse((cx-115*s,cy-155*s,cx-35*s,cy-65*s),fill=(165,175,185,255))
    elif animal=="lion":
        d.ellipse((cx-120*s,cy-175*s,cx+120*s,cy+65*s),fill=(175,105,35,255))
        d.ellipse((cx-80*s,cy-135*s,cx+80*s,cy+25*s),fill=col)
    elif animal=="fox":
        d.polygon([(cx-75*s,cy-125*s),(cx-70*s,cy-235*s),(cx-5*s,cy-145*s)],fill=col)
        d.polygon([(cx+20*s,cy-145*s),(cx+85*s,cy-235*s),(cx+85*s,cy-120*s)],fill=col)
    elif animal=="turtle":
        d.ellipse((cx-115*s,cy-35*s,cx+115*s,cy+120*s),fill=(65,105,55,255),outline=outline,width=max(3,int(5*s)))
    else:
        d.ellipse((cx-110*s,cy-170*s,cx-35*s,cy-90*s),fill=col)
        d.ellipse((cx+35*s,cy-170*s,cx+110*s,cy-90*s),fill=col)

def draw_animal(d,animal,cx,cy,s,index):
    if animal=="rabbit": draw_rabbit(d,cx,cy,s,index,index)
    elif animal=="deer": draw_deer(d,cx,cy,s,index,index)
    elif animal=="bird": draw_bird(d,cx,cy,s,index,index)
    else: draw_other(d,animal,cx,cy,s,index)


def draw_bal_hanuman(d, cx, cy, s, pose=0):
    """Draw a friendly childlike Bal Hanuman character in every scene."""
    outline = (105, 55, 35, 255)
    skin = (205, 112, 65, 255)
    light_skin = (245, 185, 135, 255)
    saffron = (238, 125, 35, 255)
    gold = (250, 205, 75, 255)
    dark = (55, 35, 30, 255)

    def box(values):
        return tuple(int(v) for v in values)

    # Tail, with a curled tip; alternate side slightly between scenes.
    side = -1 if pose % 2 == 0 else 1
    d.arc(box((cx + side*45*s, cy+35*s, cx + side*230*s, cy+260*s)),
          180 if side == -1 else 0, 330 if side == -1 else 150,
          fill=skin, width=max(9, int(22*s)))
    d.ellipse(box((cx + side*190*s-10*s, cy+100*s,
                   cx + side*190*s+20*s, cy+130*s)), fill=gold)

    # Legs and saffron dhoti.
    d.rounded_rectangle(box((cx-75*s, cy+125*s, cx-25*s, cy+245*s)),
                        radius=max(5, int(15*s)), fill=skin, outline=outline,
                        width=max(2, int(4*s)))
    d.rounded_rectangle(box((cx+25*s, cy+125*s, cx+75*s, cy+245*s)),
                        radius=max(5, int(15*s)), fill=skin, outline=outline,
                        width=max(2, int(4*s)))
    d.polygon([box((cx-100*s,cy+55*s)), box((cx+100*s,cy+55*s)),
               box((cx+80*s,cy+175*s)), box((cx,cy+145*s)),
               box((cx-80*s,cy+175*s))], fill=saffron, outline=outline)
    d.line(box((cx-85*s,cy+105*s,cx+85*s,cy+105*s)),
           fill=gold, width=max(3,int(8*s)))

    # Body and arms. Pose 1 = blessing, pose 2 = holding gada, pose 3 = prayer.
    d.rounded_rectangle(box((cx-95*s,cy-65*s,cx+95*s,cy+105*s)),
                        radius=max(10,int(38*s)), fill=skin, outline=outline,
                        width=max(3,int(5*s)))
    if pose % 4 == 3:
        d.line(box((cx-70*s,cy-20*s,cx-8*s,cy+55*s)), fill=skin,
               width=max(16,int(34*s)))
        d.line(box((cx+70*s,cy-20*s,cx+8*s,cy+55*s)), fill=skin,
               width=max(16,int(34*s)))
        d.ellipse(box((cx-17*s,cy+38*s,cx+17*s,cy+72*s)), fill=light_skin)
    else:
        d.line(box((cx-75*s,cy-20*s,cx-145*s,cy+65*s)), fill=skin,
               width=max(16,int(34*s)))
        if pose % 4 == 1:
            d.line(box((cx+75*s,cy-20*s,cx+140*s,cy-100*s)), fill=skin,
                   width=max(16,int(34*s)))
            d.ellipse(box((cx+120*s,cy-125*s,cx+165*s,cy-80*s)), fill=light_skin)
        else:
            d.line(box((cx+75*s,cy-20*s,cx+145*s,cy+55*s)), fill=skin,
                   width=max(16,int(34*s)))

    # Monkey-like friendly face, ears and muzzle.
    d.ellipse(box((cx-125*s,cy-235*s,cx-65*s,cy-155*s)),
              fill=skin, outline=outline, width=max(2,int(4*s)))
    d.ellipse(box((cx+65*s,cy-235*s,cx+125*s,cy-155*s)),
              fill=skin, outline=outline, width=max(2,int(4*s)))
    d.ellipse(box((cx-105*s,cy-270*s,cx+105*s,cy-80*s)),
              fill=skin, outline=outline, width=max(3,int(5*s)))
    d.ellipse(box((cx-68*s,cy-190*s,cx+68*s,cy-105*s)), fill=light_skin)
    d.ellipse(box((cx-55*s,cy-210*s,cx-28*s,cy-175*s)), fill=dark)
    d.ellipse(box((cx+28*s,cy-210*s,cx+55*s,cy-175*s)), fill=dark)
    d.ellipse(box((cx-12*s,cy-165*s,cx+12*s,cy-145*s)), fill=dark)
    d.arc(box((cx-35*s,cy-155*s,cx+35*s,cy-112*s)), 10, 170,
          fill=outline, width=max(2,int(4*s)))
    # Tilak.
    d.line(box((cx,cy-250*s,cx,cy-218*s)), fill=(235,235,220,255),
           width=max(4,int(9*s)))
    d.ellipse(box((cx-8*s,cy-230*s,cx+8*s,cy-214*s)), fill=(190,45,35,255))

    # Small golden crown.
    d.polygon([box((cx-75*s,cy-250*s)), box((cx-60*s,cy-315*s)),
               box((cx-20*s,cy-280*s)), box((cx,cy-330*s)),
               box((cx+25*s,cy-280*s)), box((cx+65*s,cy-315*s)),
               box((cx+78*s,cy-250*s))], fill=gold, outline=outline)
    d.rectangle(box((cx-75*s,cy-255*s,cx+78*s,cy-238*s)),
                fill=(220,155,35,255), outline=outline)

    # Gada held beside him in selected scenes.
    if pose % 4 == 2:
        gx = cx + 165*s
        d.line(box((gx,cy-85*s,gx+5*s,cy+190*s)), fill=(150,90,45,255),
               width=max(7,int(15*s)))
        d.ellipse(box((gx-42*s,cy-145*s,gx+48*s,cy-55*s)),
                  fill=gold, outline=outline, width=max(3,int(5*s)))
        d.ellipse(box((gx-18*s,cy-125*s,gx+20*s,cy-85*s)),
                  fill=(255,230,130,255))

def draw_scene(story,scene_text,index):
    IMAGE_DIR.mkdir(parents=True,exist_ok=True)
    rng=random.Random(index+sum(ord(c) for c in str(scene_text)[:50]))
    theme=choose_theme(scene_text,index); top,bottom,ground,foliage=THEMES[theme]
    im=Image.new("RGB",(WIDTH,HEIGHT)); pix=im.load()
    for y in range(HEIGHT):
        f=y/(HEIGHT-1); col=tuple(int(top[k]*(1-f)+bottom[k]*f) for k in range(3))
        for x in range(WIDTH): pix[x,y]=col
    im=im.convert("RGBA"); d=ImageDraw.Draw(im,"RGBA")
    if theme=="night":
        d.ellipse((1450,80,1630,260),fill=(255,245,190,255))
        for _ in range(55):
            x,y=rng.randint(30,1890),rng.randint(20,520); d.ellipse((x,y,x+5,y+5),fill=(255,255,220,230))
    else:
        sx=220+(index*317)%1400; d.ellipse((sx,80,sx+190,270),fill=(255,220,130,235))
    if theme in ("forest","garden"):
        for x in (80,350,1510,1810):
            d.rounded_rectangle((x-20,560,x+20,880),radius=12,fill=(105,65,42,255))
            for dx,dy,r in [(-50,570,100),(45,520,115),(0,440,105)]:
                d.ellipse((x+dx-r,dy-r,x+dx+r,dy+r),fill=foliage+(255,))
    elif theme=="village":
        for x in (100,520,1330,1640):
            w=240; y=480
            d.rectangle((x,y,x+w,850),fill=(235,190,135,255),outline=(105,70,50,255),width=8)
            d.polygon([(x-25,y+10),(x+w//2,y-130),(x+w+25,y+10)],fill=(160,65,55,255))
            d.rectangle((x+100,650,x+145,850),fill=(100,65,45,255))
    elif theme=="river":
        d.polygon([(0,620),(500,570),(1000,680),(1500,590),(1920,650),(1920,1080),(0,1080)],fill=(45,155,195,255))
        for y in range(710,1000,75): d.arc((100,y,1800,y+100),5,170,fill=(190,240,245,180),width=8)
    elif theme=="mountain":
        for x,peak in [(-100,430),(350,330),(900,460),(1450,300),(1850,430)]:
            d.polygon([(x-450,850),(x,peak),(x+450,850)],fill=(105,125,145,255))
            d.polygon([(x-110,peak+125),(x,peak),(x+110,peak+125)],fill=(245,245,240,255))
    d.rectangle((0,850,WIDTH,HEIGHT),fill=ground+(255,))
    # Scene props
    for j in range(8):
        x=90+j*250+rng.randint(-30,30); y=rng.randint(850,1000)
        if index%3==0:
            d.line((x,y,x,y-55),fill=(40,100,45,255),width=8)
            d.ellipse((x-18,y-85,x+18,y-50),fill=(255,120+(j*13)%100,170,255))
        elif index%3==1:
            d.rectangle((x-8,y-45,x+8,y),fill=(245,225,190,255))
            d.ellipse((x-35,y-70,x+35,y-30),fill=(210,70,70,255))
        else: d.ellipse((x-40,y-25,x+40,y+20),fill=foliage+(255,))

    animals=detect_animals(scene_text)
    positions = [(620,690),(1170,700),(1550,670)]
    scales = [0.78,0.62,0.48]
    # If several animals are mentioned, show them together in the same scene.
    for n,animal in enumerate(animals):
        x,y=positions[n]; draw_animal(d,animal,x,y,scales[n],index+n)

    # Keep Bal Hanuman Ji clearly visible in every video scene.
    draw_bal_hanuman(d, 960, 675, 0.92, index % 4)

    overlay=Image.new("RGBA",(WIDTH,HEIGHT),(0,0,0,0)); od=ImageDraw.Draw(overlay)
    title=str(story.get("title","आज की प्यारी कहानी"))
    od.rounded_rectangle((55,45,WIDTH-55,165),radius=30,fill=(8,25,40,155))
    od.text((90,72),title[:48],font=find_font(54),fill=(255,255,255,255),stroke_width=2,stroke_fill=(20,30,40,255))
    caption=re.sub(r"\s+"," ",str(scene_text))[:100]
    od.rounded_rectangle((70,900,WIDTH-70,1035),radius=28,fill=(5,20,30,155))
    od.text((110,940),caption,font=find_font(34),fill=(255,255,255,255))
    im=Image.alpha_composite(im,overlay).convert("RGB")
    path=IMAGE_DIR/f"scene_{index+1:02d}.jpg"; im.save(path,quality=94,optimize=True)
    return path

def create_scene_images(story):
    paths=[]
    for i,scene in enumerate(story["scenes"]):
        paths.append(draw_scene(story,scene_text_value(scene),i))
    return paths
